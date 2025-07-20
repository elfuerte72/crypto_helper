#!/usr/bin/env python3
"""
Unit тесты для исправлений callback timeout (TASK-CRYPTO-002)
Тестирование утилит безопасного редактирования сообщений и callback обработки
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from aiogram.types import Message, CallbackQuery, User, Chat, InlineKeyboardMarkup
from aiogram.exceptions import TelegramBadRequest

from handlers.formatters import SafeMessageEditor, LoadingMessageFormatter
from handlers.admin_flow import get_exchange_rate_with_loading, safe_callback_answer_and_edit
from handlers.fsm_states import Currency
from config import config


class TestSafeMessageEditor:
    """Тесты для SafeMessageEditor - исправление ошибок редактирования сообщений"""
    
    @pytest.fixture
    def mock_message(self):
        """Создать mock Message объект"""
        message = MagicMock(spec=Message)
        message.text = "Test message"
        message.caption = None
        message.reply_markup = None
        message.edit_text = AsyncMock()
        return message
    
    @pytest.fixture
    def mock_callback_query(self):
        """Создать mock CallbackQuery объект"""
        callback = MagicMock(spec=CallbackQuery)
        callback.answer = AsyncMock()
        callback.from_user = MagicMock(spec=User)
        callback.from_user.id = 123456
        return callback
    
    @pytest.mark.asyncio
    async def test_safe_edit_message_success(self, mock_message):
        """Тест успешного редактирования сообщения"""
        new_text = "New message text"
        
        # Настраиваем mock для успешного редактирования
        mock_message.edit_text.return_value = None
        
        result = await SafeMessageEditor.safe_edit_message(
            mock_message, new_text
        )
        
        assert result is True
        mock_message.edit_text.assert_called_once_with(
            text=new_text,
            reply_markup=None,
            parse_mode='HTML'
        )
    
    @pytest.mark.asyncio
    async def test_safe_edit_message_not_modified(self, mock_message):
        """Тест обработки ошибки 'message is not modified'"""
        new_text = "New message text"
        
        # Настраиваем mock для ошибки "message is not modified"
        mock_message.edit_text.side_effect = TelegramBadRequest(
            method="editMessageText",
            message="Bad Request: message is not modified"
        )
        
        result = await SafeMessageEditor.safe_edit_message(
            mock_message, new_text
        )
        
        assert result is True  # Должно возвращать True для этой ошибки
        mock_message.edit_text.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_safe_edit_message_retries(self, mock_message):
        """Тест повторных попыток при временных ошибках"""
        new_text = "New message text"
        
        # Первая попытка - ошибка, вторая - успех
        mock_message.edit_text.side_effect = [
            TelegramBadRequest(method="editMessageText", message="Bad request"),
            None
        ]
        
        with patch('asyncio.sleep', new_callable=AsyncMock):
            result = await SafeMessageEditor.safe_edit_message(
                mock_message, new_text, max_attempts=2
            )
        
        assert result is True
        assert mock_message.edit_text.call_count == 2
    
    @pytest.mark.asyncio
    async def test_safe_edit_message_max_attempts_exceeded(self, mock_message):
        """Тест превышения максимального количества попыток"""
        new_text = "New message text"
        
        # Все попытки неудачны
        mock_message.edit_text.side_effect = TelegramBadRequest(
            method="editMessageText", 
            message="Bad request"
        )
        
        with patch('asyncio.sleep', new_callable=AsyncMock):
            result = await SafeMessageEditor.safe_edit_message(
                mock_message, new_text, max_attempts=2
            )
        
        assert result is False
        assert mock_message.edit_text.call_count == 2
    
    @pytest.mark.asyncio
    async def test_safe_answer_callback_success(self, mock_callback_query):
        """Тест успешного ответа на callback query"""
        text = "Success"
        
        # Настраиваем mock для успешного ответа
        mock_callback_query.answer.return_value = None
        
        result = await SafeMessageEditor.safe_answer_callback(
            mock_callback_query, text
        )
        
        assert result is True
        mock_callback_query.answer.assert_called_once_with(
            text=text, show_alert=False
        )
    
    @pytest.mark.asyncio
    async def test_safe_answer_callback_timeout(self, mock_callback_query):
        """Тест обработки таймаута при ответе на callback"""
        text = "Test message"
        
        # Настраиваем mock для таймаута
        mock_callback_query.answer.side_effect = asyncio.TimeoutError()
        
        with patch('asyncio.wait_for', side_effect=asyncio.TimeoutError()):
            result = await SafeMessageEditor.safe_answer_callback(
                mock_callback_query, text, timeout=1.0
            )
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_safe_answer_callback_old_query(self, mock_callback_query):
        """Тест обработки старого callback query"""
        text = "Test message"
        
        # Настраиваем mock для старого query
        mock_callback_query.answer.side_effect = TelegramBadRequest(
            method="answerCallbackQuery",
            message="Bad Request: query is too old and response timeout expired"
        )
        
        result = await SafeMessageEditor.safe_answer_callback(
            mock_callback_query, text
        )
        
        assert result is False


class TestLoadingMessageFormatter:
    """Тесты для LoadingMessageFormatter - форматирование загрузочных сообщений"""
    
    def test_format_loading_message(self):
        """Тест форматирования общего сообщения загрузки"""
        result = LoadingMessageFormatter.format_loading_message(
            "Тестовая операция", 2, 5
        )
        
        assert "⏳" in result
        assert "Тестовая операция" in result
        assert "2/5" in result
        assert "Пожалуйста, подождите" in result
    
    def test_format_api_loading_message(self):
        """Тест форматирования сообщения загрузки API"""
        result = LoadingMessageFormatter.format_api_loading_message("Rapira API")
        
        assert "🔄" in result
        assert "Rapira API" in result
        assert "запрос к серверу" in result
        assert "несколько секунд" in result
    
    def test_format_calculation_loading_message(self):
        """Тест форматирования сообщения расчета"""
        result = LoadingMessageFormatter.format_calculation_loading_message()
        
        assert "🧮" in result
        assert "Расчет курса" in result
        assert "наценки" in result
        assert "Секундочку" in result
    
    def test_format_error_with_retry(self):
        """Тест форматирования ошибки с повторными попытками"""
        result = LoadingMessageFormatter.format_error_with_retry(
            "Тестовая ошибка", 2, 3
        )
        
        assert "⚠️" in result
        assert "попытка 2/3" in result
        assert "Тестовая ошибка" in result
        assert "Повторная попытка" in result
    
    def test_create_progress_bar(self):
        """Тест создания прогресс-бара"""
        # Тестируем приватный метод через публичный
        result = LoadingMessageFormatter._create_progress_bar(3, 10, 10)
        
        assert "[" in result
        assert "]" in result
        assert "█" in result  # Заполненная часть
        assert "░" in result  # Незаполненная часть


class TestAsyncAPIHandlers:
    """Тесты для асинхронных обработчиков API запросов"""
    
    @pytest.fixture
    def mock_message(self):
        """Создать mock Message объект"""
        message = MagicMock(spec=Message)
        message.text = "Test message"
        message.edit_text = AsyncMock()
        return message
    
    @pytest.fixture
    def mock_callback_query(self, mock_message):
        """Создать mock CallbackQuery объект"""
        callback = MagicMock(spec=CallbackQuery)
        callback.answer = AsyncMock()
        callback.message = mock_message
        callback.from_user = MagicMock(spec=User)
        callback.from_user.id = 123456
        return callback
    
    @pytest.mark.asyncio
    async def test_get_exchange_rate_with_loading_success(self, mock_message):
        """Тест успешного получения курса с загрузкой"""
        source_currency = Currency.RUB
        target_currency = Currency.USDT
        expected_rate = Decimal('100.50')
        
        # Мокаем SafeMessageEditor.safe_edit_message
        with patch('handlers.admin_flow.SafeMessageEditor.safe_edit_message', new_callable=AsyncMock) as mock_edit:
            mock_edit.return_value = True
            
            # Мокаем ExchangeCalculator.get_base_rate_for_pair
            with patch('handlers.admin_flow.ExchangeCalculator.get_base_rate_for_pair', new_callable=AsyncMock) as mock_get_rate:
                mock_get_rate.return_value = expected_rate
                
                result = await get_exchange_rate_with_loading(
                    mock_message, source_currency, target_currency
                )
        
        assert result == expected_rate
        assert mock_edit.call_count >= 1  # Должно быть вызвано для показа загрузки
        mock_get_rate.assert_called_once_with(source_currency, target_currency)
    
    @pytest.mark.asyncio
    async def test_get_exchange_rate_with_loading_timeout(self, mock_message):
        """Тест обработки таймаута API"""
        source_currency = Currency.RUB
        target_currency = Currency.USD
        
        with patch('handlers.admin_flow.SafeMessageEditor.safe_edit_message', new_callable=AsyncMock) as mock_edit:
            mock_edit.return_value = True
            
            # Мокаем таймаут
            with patch('handlers.admin_flow.ExchangeCalculator.get_base_rate_for_pair', new_callable=AsyncMock) as mock_get_rate:
                mock_get_rate.side_effect = asyncio.TimeoutError()
                
                with patch('asyncio.wait_for', side_effect=asyncio.TimeoutError()):
                    result = await get_exchange_rate_with_loading(
                        mock_message, source_currency, target_currency
                    )
        
        assert result is None
        # Должно показать сообщение об ошибке таймаута
        error_calls = [call for call in mock_edit.call_args_list 
                      if "таймаута" in str(call)]
        assert len(error_calls) > 0
    
    @pytest.mark.asyncio
    async def test_safe_callback_answer_and_edit_success(self, mock_callback_query):
        """Тест успешного комбинированного ответа и редактирования"""
        new_text = "New message"
        answer_text = "Success"
        
        with patch('handlers.admin_flow.SafeMessageEditor.safe_answer_callback', new_callable=AsyncMock) as mock_answer:
            mock_answer.return_value = True
            
            with patch('handlers.admin_flow.SafeMessageEditor.safe_edit_message', new_callable=AsyncMock) as mock_edit:
                mock_edit.return_value = True
                
                result = await safe_callback_answer_and_edit(
                    mock_callback_query,
                    new_text,
                    answer_text=answer_text
                )
        
        assert result is True
        mock_answer.assert_called_once()
        mock_edit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_safe_callback_answer_and_edit_partial_failure(self, mock_callback_query):
        """Тест частичной неудачи (ответ успешен, редактирование неудачно)"""
        new_text = "New message"
        
        with patch('handlers.admin_flow.SafeMessageEditor.safe_answer_callback', new_callable=AsyncMock) as mock_answer:
            mock_answer.return_value = True
            
            with patch('handlers.admin_flow.SafeMessageEditor.safe_edit_message', new_callable=AsyncMock) as mock_edit:
                mock_edit.return_value = False
                
                result = await safe_callback_answer_and_edit(
                    mock_callback_query,
                    new_text
                )
        
        assert result is False  # Общий результат неудачен
        mock_answer.assert_called_once()
        mock_edit.assert_called_once()


class TestConfigurationSettings:
    """Тесты для новых настроек конфигурации"""
    
    def test_callback_timeout_settings(self):
        """Тест наличия новых настроек таймаута"""
        # Проверяем что новые настройки присутствуют
        assert hasattr(config, 'CALLBACK_API_TIMEOUT')
        assert hasattr(config, 'CALLBACK_ANSWER_TIMEOUT')
        assert hasattr(config, 'MAX_MESSAGE_EDIT_ATTEMPTS')
        
        # Проверяем разумные значения по умолчанию
        assert config.CALLBACK_API_TIMEOUT <= 5  # Не больше 5 секунд
        assert config.CALLBACK_ANSWER_TIMEOUT <= 3  # Не больше 3 секунд
        assert config.MAX_MESSAGE_EDIT_ATTEMPTS >= 1  # Минимум 1 попытка
    
    def test_callback_timeout_values(self):
        """Тест корректности значений таймаутов"""
        # Callback API timeout должен быть меньше обычного API timeout
        assert config.CALLBACK_API_TIMEOUT < config.API_TIMEOUT
        
        # Callback answer timeout должен быть меньше callback API timeout
        assert config.CALLBACK_ANSWER_TIMEOUT <= config.CALLBACK_API_TIMEOUT


if __name__ == '__main__':
    # Запуск тестов напрямую для отладки
    pytest.main([__file__, '-v', '--tb=short'])