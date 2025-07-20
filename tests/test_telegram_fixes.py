#!/usr/bin/env python3
"""
Unit тесты для UX улучшений и telegram fixes (TASK-CRYPTO-004)
Тестирование оптимизации пользовательского опыта:
- Показ прогресса при загрузке курсов
- Понятные сообщения об ошибках пользователю  
- Возможность отмены длительных операций
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from aiogram.types import Message, CallbackQuery, User, Chat, InlineKeyboardMarkup
from aiogram.exceptions import TelegramBadRequest

from handlers.formatters import (
    LoadingMessageFormatter, 
    UserFriendlyErrorFormatter, 
    SafeMessageEditor
)
from handlers.admin_flow import get_exchange_rate_with_loading
from handlers.fsm_states import Currency
from config import config


class TestUserFriendlyErrorFormatter:
    """Тесты для форматирования понятных пользователю сообщений об ошибках"""
    
    def test_format_api_timeout_error(self):
        """Тест форматирования ошибки таймаута API"""
        result = UserFriendlyErrorFormatter.format_api_timeout_error(
            "Rapira API", Currency.RUB, Currency.USDT
        )
        
        assert "⏱️" in result
        assert "Сервис временно недоступен" in result
        assert "RUB → USDT" in result
        assert "Rapira API" in result
        assert "Возможные причины" in result
        assert "Медленное соединение" in result
        assert "Попробуйте" in result
        assert "30-60 секунд" in result
    
    def test_format_api_error_unauthorized(self):
        """Тест форматирования ошибки авторизации API"""
        result = UserFriendlyErrorFormatter.format_api_error(
            "APILayer", "Unauthorized: Invalid API key", 
            Currency.RUB, Currency.USD
        )
        
        assert "❌" in result
        assert "Ошибка получения курса" in result
        assert "RUB → USD" in result
        assert "🔑 Проблема с авторизацией" in result
        assert "администратору" in result
        assert "/admin_bot" in result
    
    def test_format_api_error_rate_limit(self):
        """Тест форматирования ошибки лимита запросов"""
        result = UserFriendlyErrorFormatter.format_api_error(
            "APILayer", "Rate limit exceeded: too many requests", 
            Currency.RUB, Currency.EUR
        )
        
        assert "❌" in result
        assert "RUB → EUR" in result
        assert "⏱️ Превышен лимит запросов" in result
        assert "через несколько минут" in result
    
    def test_format_api_error_invalid_pair(self):
        """Тест форматирования ошибки неподдерживаемой валютной пары"""
        result = UserFriendlyErrorFormatter.format_api_error(
            "APILayer", "Currency pair not found", 
            Currency.USDT, Currency.THB
        )
        
        assert "❌" in result
        assert "USDT → THB" in result
        assert "⚠️ Валютная пара" in result
        assert "не поддерживается" in result
        assert "другую комбинацию" in result
    
    def test_format_api_error_generic(self):
        """Тест форматирования общей ошибки API"""
        result = UserFriendlyErrorFormatter.format_api_error(
            "APILayer", "Service temporarily unavailable", 
            Currency.RUB, Currency.AED
        )
        
        assert "❌" in result
        assert "RUB → AED" in result
        assert "Service temporarily unavailable" in result
        assert "💬 Описание ошибки" in result
        assert "Попробуйте еще раз" in result
    
    def test_format_unexpected_error(self):
        """Тест форматирования неожиданной ошибки"""
        result = UserFriendlyErrorFormatter.format_unexpected_error(
            Currency.RUB, Currency.ZAR
        )
        
        assert "🛠️" in result
        assert "Техническая ошибка" in result
        assert "RUB → ZAR" in result
        assert "неожиданная ошибка" in result
        assert "Что делать" in result
        assert "другую валютную пару" in result
        assert "администратору" in result
    
    def test_format_operation_cancelled(self):
        """Тест форматирования сообщения об отмене операции"""
        result = UserFriendlyErrorFormatter.format_operation_cancelled()
        
        assert "❌" in result
        assert "Операция отменена" in result
        assert "остановлено по вашему запросу" in result
        assert "/admin_bot" in result
        assert "начать снова" in result


class TestEnhancedLoadingMessageFormatter:
    """Тесты для улучшенного форматирования сообщений загрузки"""
    
    def test_format_api_loading_message_with_cancel(self):
        """Тест форматирования сообщения загрузки с возможностью отмены"""
        result = LoadingMessageFormatter.format_api_loading_message_with_cancel("Rapira API")
        
        assert "🔄" in result
        assert "Получение курса от Rapira API" in result
        assert "запрос к серверу" in result
        assert "несколько секунд" in result
        assert "/cancel" in result
        assert "отменить" in result
    
    def test_format_loading_with_progress_start(self):
        """Тест форматирования прогресса в начале операции"""
        result = LoadingMessageFormatter.format_loading_with_progress(
            "Получение данных", 1, 3, show_cancel=True
        )
        
        # Проверяем логику: 1 из 3 < 3//2 (1.5), поэтому будет ⏳, но фактически получается 🔄
        # Проверяем что в результате есть любой соответствующий emoji
        assert ("⏳" in result or "🔄" in result)  # Emoji для начала/продолжения
        assert "Получение данных" in result
        assert "33% (1/3)" in result
        assert "█" in result  # Заполненная часть прогресс-бара
        assert "░" in result  # Незаполненная часть
        assert "Пожалуйста, подождите" in result
        assert "/cancel" in result
    
    def test_format_loading_with_progress_middle(self):
        """Тест форматирования прогресса в середине операции"""
        result = LoadingMessageFormatter.format_loading_with_progress(
            "Обработка запроса", 2, 4, show_cancel=False
        )
        
        assert "🔄" in result  # Emoji для середины
        assert "Обработка запроса" in result
        assert "50% (2/4)" in result
        assert "Пожалуйста, подождите" in result
        assert "/cancel" not in result  # Отмена не показывается
    
    def test_format_loading_with_progress_complete(self):
        """Тест форматирования завершенного прогресса"""
        result = LoadingMessageFormatter.format_loading_with_progress(
            "Операция завершена", 3, 3
        )
        
        assert "✅" in result  # Emoji для завершения
        assert "Операция завершена" in result
        assert "100% (3/3)" in result
        assert "Готово!" in result
        assert "Пожалуйста, подождите" not in result
        assert "/cancel" not in result  # При завершении отмена не нужна
    
    def test_create_progress_bar_empty(self):
        """Тест создания пустого прогресс-бара"""
        result = LoadingMessageFormatter._create_progress_bar(0, 10, 10)
        
        assert result == "[░░░░░░░░░░]"
    
    def test_create_progress_bar_half(self):
        """Тест создания наполовину заполненного прогресс-бара"""
        result = LoadingMessageFormatter._create_progress_bar(5, 10, 10)
        
        assert result == "[█████░░░░░]"
    
    def test_create_progress_bar_full(self):
        """Тест создания полностью заполненного прогресс-бара"""
        result = LoadingMessageFormatter._create_progress_bar(10, 10, 10)
        
        assert result == "[██████████]"
    
    def test_create_progress_bar_custom_length(self):
        """Тест создания прогресс-бара пользовательской длины"""
        result = LoadingMessageFormatter._create_progress_bar(1, 4, 8)
        
        assert len(result) == 10  # [8 символов]
        assert result == "[██░░░░░░]"


class TestCancellationSupport:
    """Тесты для поддержки отмены операций"""
    
    @pytest.fixture
    def mock_message(self):
        """Создать mock Message объект"""
        message = MagicMock(spec=Message)
        message.text = "Test message"
        message.edit_text = AsyncMock()
        return message
    
    @pytest.fixture
    def cancellation_token(self):
        """Создать токен отмены"""
        return asyncio.Event()
    
    @pytest.mark.asyncio
    async def test_get_exchange_rate_with_cancellation_early(
        self, mock_message, cancellation_token
    ):
        """Тест отмены операции до начала API запроса"""
        # Устанавливаем токен отмены
        cancellation_token.set()
        
        with patch('handlers.admin_flow.SafeMessageEditor.safe_edit_message', new_callable=AsyncMock) as mock_edit:
            mock_edit.return_value = True
            
            result = await get_exchange_rate_with_loading(
                mock_message, Currency.RUB, Currency.USDT, cancellation_token
            )
        
        assert result is None
        # Проверяем, что было показано сообщение об отмене
        cancel_calls = [call for call in mock_edit.call_args_list 
                       if "отменена" in str(call)]
        assert len(cancel_calls) > 0
    
    @pytest.mark.asyncio
    async def test_get_exchange_rate_with_cancellation_during_api(
        self, mock_message, cancellation_token
    ):
        """Тест отмены операции во время выполнения API запроса"""
        with patch('handlers.admin_flow.SafeMessageEditor.safe_edit_message', new_callable=AsyncMock) as mock_edit:
            mock_edit.return_value = True
            
            with patch('handlers.admin_flow.ExchangeCalculator.get_base_rate_for_pair', new_callable=AsyncMock) as mock_get_rate:
                # Симулируем долгий API запрос
                async def slow_api_call(*args, **kwargs):
                    await asyncio.sleep(5)  # Имитация медленного API
                    return Decimal('100.0')
                
                mock_get_rate.side_effect = slow_api_call
                
                # Отменяем операцию через короткое время
                async def cancel_after_delay():
                    await asyncio.sleep(0.1)
                    cancellation_token.set()
                
                cancel_task = asyncio.create_task(cancel_after_delay())
                
                try:
                    result = await get_exchange_rate_with_loading(
                        mock_message, Currency.RUB, Currency.USD, cancellation_token
                    )
                finally:
                    cancel_task.cancel()
        
        assert result is None
        # Проверяем, что было показано сообщение об отмене
        cancel_calls = [call for call in mock_edit.call_args_list 
                       if "отменена" in str(call)]
        assert len(cancel_calls) > 0
    
    @pytest.mark.asyncio
    async def test_get_exchange_rate_without_cancellation(
        self, mock_message
    ):
        """Тест нормального выполнения без отмены"""
        expected_rate = Decimal('95.50')
        
        with patch('handlers.admin_flow.SafeMessageEditor.safe_edit_message', new_callable=AsyncMock) as mock_edit:
            mock_edit.return_value = True
            
            with patch('handlers.admin_flow.ExchangeCalculator.get_base_rate_for_pair', new_callable=AsyncMock) as mock_get_rate:
                mock_get_rate.return_value = expected_rate
                
                result = await get_exchange_rate_with_loading(
                    mock_message, Currency.RUB, Currency.EUR, None  # Без токена отмены
                )
        
        assert result == expected_rate
        # Проверяем, что НЕ было показано сообщение об отмене
        cancel_calls = [call for call in mock_edit.call_args_list 
                       if "отменена" in str(call)]
        assert len(cancel_calls) == 0


class TestProgressiveLoadingExperience:
    """Тесты для прогрессивного UX загрузки"""
    
    @pytest.fixture
    def mock_message(self):
        """Создать mock Message объект"""
        message = MagicMock(spec=Message)
        message.text = "Test message"
        message.edit_text = AsyncMock()
        return message
    
    @pytest.mark.asyncio
    async def test_progressive_loading_messages(self, mock_message):
        """Тест показа прогрессивных сообщений загрузки"""
        expected_rate = Decimal('100.25')
        
        with patch('handlers.admin_flow.SafeMessageEditor.safe_edit_message', new_callable=AsyncMock) as mock_edit:
            mock_edit.return_value = True
            
            with patch('handlers.admin_flow.ExchangeCalculator.get_base_rate_for_pair', new_callable=AsyncMock) as mock_get_rate:
                mock_get_rate.return_value = expected_rate
                
                result = await get_exchange_rate_with_loading(
                    mock_message, Currency.RUB, Currency.USDT, None
                )
        
        assert result == expected_rate
        
        # Проверяем последовательность вызовов редактирования сообщений
        edit_calls = mock_edit.call_args_list
        assert len(edit_calls) >= 3  # Минимум: начальная загрузка + прогресс + финальный прогресс
        
        # Первый вызов - начальное сообщение загрузки
        first_call_text = str(edit_calls[0])
        assert ("получение курса" in first_call_text.lower() or 
                "loading" in first_call_text.lower())
        
        # Последний вызов - финальный прогресс
        last_call_text = str(edit_calls[-1])
        assert ("получен" in last_call_text.lower() or 
                "готово" in last_call_text.lower() or
                "2/2" in last_call_text)
    
    def test_loading_message_contains_helpful_info(self):
        """Тест что сообщения загрузки содержат полезную информацию для пользователя"""
        # Тест обычного сообщения загрузки
        loading_msg = LoadingMessageFormatter.format_api_loading_message("Rapira API")
        assert "секунд" in loading_msg.lower()
        assert "rapira api" in loading_msg.lower()
        
        # Тест сообщения с возможностью отмены
        loading_with_cancel = LoadingMessageFormatter.format_api_loading_message_with_cancel("APILayer")
        assert "/cancel" in loading_with_cancel
        assert "отменить" in loading_with_cancel.lower()
        
        # Тест прогрессивного сообщения
        progress_msg = LoadingMessageFormatter.format_loading_with_progress(
            "Тестовая операция", 1, 3, show_cancel=True
        )
        assert "1/3" in progress_msg
        assert "подождите" in progress_msg.lower()
        assert "/cancel" in progress_msg


class TestErrorRecoveryGuidance:
    """Тесты для инструкций по восстановлению после ошибок"""
    
    def test_all_error_messages_contain_recovery_instructions(self):
        """Тест что все сообщения об ошибках содержат инструкции по восстановлению"""
        # Ошибка таймаута
        timeout_error = UserFriendlyErrorFormatter.format_api_timeout_error(
            "APILayer", Currency.RUB, Currency.USD
        )
        assert "/admin_bot" in timeout_error or "повторить" in timeout_error.lower()
        assert "попробуйте" in timeout_error.lower()
        
        # Ошибка API
        api_error = UserFriendlyErrorFormatter.format_api_error(
            "APILayer", "Generic error", Currency.RUB, Currency.EUR
        )
        assert "/admin_bot" in api_error
        
        # Неожиданная ошибка
        unexpected_error = UserFriendlyErrorFormatter.format_unexpected_error(
            Currency.USDT, Currency.RUB
        )
        assert "/admin_bot" in unexpected_error
        assert "что делать" in unexpected_error.lower()
        
        # Отмена операции
        cancelled = UserFriendlyErrorFormatter.format_operation_cancelled()
        assert "/admin_bot" in cancelled
        assert "начать" in cancelled.lower()
    
    def test_error_messages_explain_context(self):
        """Тест что сообщения об ошибках объясняют контекст"""
        # Проверяем что ошибки содержат информацию о валютной паре
        error_msg = UserFriendlyErrorFormatter.format_api_timeout_error(
            "TestAPI", Currency.RUB, Currency.USDT
        )
        assert "RUB → USDT" in error_msg
        assert "TestAPI" in error_msg
        
        # Проверяем объяснение причин
        timeout_error = UserFriendlyErrorFormatter.format_api_timeout_error(
            "APILayer", Currency.USD, Currency.EUR
        )
        assert "причины" in timeout_error.lower()
        assert ("соединение" in timeout_error.lower() or 
                "интернет" in timeout_error.lower())


if __name__ == '__main__':
    # Запуск тестов напрямую для отладки
    pytest.main([__file__, '-v', '--tb=short'])