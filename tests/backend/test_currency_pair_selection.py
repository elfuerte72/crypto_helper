#!/usr/bin/env python3
"""
Unit тесты для функциональности выбора валютных пар
Тестирует обработчики валютных пар и вспомогательные функции
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import CallbackQuery, Message, User, Chat
from aiogram.exceptions import TelegramBadRequest

# Импортируем модули для тестирования
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

# Обновленные импорты из новых модулей
from handlers.currency_pairs import (
    CURRENCY_PAIRS,
    get_currency_pair_info,
    is_valid_currency_pair
)
from handlers.admin_handlers import (
    handle_currency_pair_selection,
    handle_cancel_selection
)


class TestCurrencyPairConstants:
    """Тесты для констант валютных пар"""
    
    def test_currency_pairs_structure(self):
        """Тест структуры констант валютных пар"""
        # Проверяем, что все пары имеют правильную структуру
        required_keys = {'name', 'base', 'quote', 'description', 'emoji'}
        
        for pair_id, pair_info in CURRENCY_PAIRS.items():
            assert isinstance(pair_info, dict), f"Пара {pair_id} должна быть словарем"
            assert required_keys.issubset(pair_info.keys()), \
                f"Пара {pair_id} должна содержать все необходимые ключи"
            
            # Проверяем типы данных
            assert isinstance(pair_info['name'], str), f"name должно быть строкой для {pair_id}"
            assert isinstance(pair_info['base'], str), f"base должно быть строкой для {pair_id}"
            assert isinstance(pair_info['quote'], str), f"quote должно быть строкой для {pair_id}"
            assert isinstance(pair_info['description'], str), f"description должно быть строкой для {pair_id}"
            assert isinstance(pair_info['emoji'], str), f"emoji должно быть строкой для {pair_id}"
    
    def test_currency_pairs_count(self):
        """Тест количества валютных пар"""
        # После упрощения должно быть 10 пар: только USDT пары
        assert len(CURRENCY_PAIRS) == 10, "Должно быть 10 валютных пар (только USDT)"
    
    def test_currency_pairs_naming(self):
        """Тест правильности именования валютных пар"""
        expected_pairs = {
            # USDT пары
            'usdt_zar', 'usdt_thb', 'usdt_aed', 'usdt_idr', 'usdt_rub',
            # Обратные USDT пары
            'zar_usdt', 'thb_usdt', 'aed_usdt', 'idr_usdt', 'rub_usdt'
        }
        
        actual_pairs = set(CURRENCY_PAIRS.keys())
        assert actual_pairs == expected_pairs, "Набор валютных пар не соответствует ожидаемому"
    
    def test_currency_pair_names_format(self):
        """Тест формата названий валютных пар"""
        for pair_id, pair_info in CURRENCY_PAIRS.items():
            name = pair_info['name']
            base = pair_info['base']
            quote = pair_info['quote']
            
            # Проверяем формат имени
            expected_name = f"{base}/{quote}"
            assert name == expected_name, f"Имя пары {pair_id} должно быть {expected_name}, получено {name}"


class TestCurrencyPairHelpers:
    """Тесты для вспомогательных функций валютных пар"""
    
    def test_get_currency_pair_info_valid(self):
        """Тест получения информации о валидной валютной паре"""
        pair_info = get_currency_pair_info('usdt_rub')
        
        assert pair_info is not None, "Должна быть возвращена информация о паре"
        assert pair_info['name'] == 'USDT/RUB', "Неправильное имя пары"
        assert pair_info['base'] == 'USDT', "Неправильная базовая валюта"
        assert pair_info['quote'] == 'RUB', "Неправильная котируемая валюта"
    
    def test_get_currency_pair_info_invalid(self):
        """Тест получения информации о невалидной валютной паре"""
        pair_info = get_currency_pair_info('invalid_pair')
        assert pair_info is None, "Должен быть возвращен None для невалидной пары"
    
    def test_get_currency_pair_info_empty(self):
        """Тест получения информации с пустым входом"""
        pair_info = get_currency_pair_info('')
        assert pair_info is None, "Должен быть возвращен None для пустой строки"
    
    def test_is_valid_currency_pair_valid(self):
        """Тест проверки валидности для валидных пар"""
        valid_pairs = ['usdt_zar', 'usdt_thb', 'zar_usdt', 'aed_usdt']
        
        for pair in valid_pairs:
            assert is_valid_currency_pair(pair), f"Пара {pair} должна быть валидной"
    
    def test_is_valid_currency_pair_invalid(self):
        """Тест проверки валидности для невалидных пар"""
        invalid_pairs = ['invalid_pair', 'rub_usd', 'btc_eth', '', 'rub_zar']  # rub_zar больше не поддерживается
        
        for pair in invalid_pairs:
            assert not is_valid_currency_pair(pair), f"Пара {pair} не должна быть валидной"
    
    def test_all_pairs_are_valid(self):
        """Тест что все пары из констант проходят валидацию"""
        for pair_id in CURRENCY_PAIRS.keys():
            assert is_valid_currency_pair(pair_id), f"Пара {pair_id} должна быть валидной"


class TestCurrencyPairCallbackHandlers:
    """Тесты для обработчиков callback queries валютных пар"""
    
    def setup_method(self):
        """Настройка для каждого теста"""
        # Создаем mock объекты
        self.user = User(
            id=123456789,
            is_bot=False,
            first_name="Test",
            username="testuser"
        )
        
        self.chat = Chat(
            id=-1001234567890,
            type="channel"
        )
        
        self.message = MagicMock(spec=Message)
        self.message.edit_text = AsyncMock()
        
        self.callback_query = MagicMock(spec=CallbackQuery)
        self.callback_query.from_user = self.user
        self.callback_query.message = self.message
        self.callback_query.answer = AsyncMock()
        
        # Mock FSMContext
        self.state = AsyncMock()
    
    @pytest.mark.asyncio
    async def test_handle_currency_pair_selection_valid_pair(self):
        """Тест обработки выбора валидной валютной пары"""
        with patch('handlers.bot_handlers.start_margin_calculation') as mock_start:
            self.callback_query.data = 'pair_usdt_rub'
            
            await handle_currency_pair_selection(self.callback_query, self.state)
            
            # Проверяем, что была вызвана функция начала расчета наценки
            mock_start.assert_called_once_with(
                self.callback_query, 'usdt_rub', self.state
            )
    
    @pytest.mark.asyncio
    async def test_handle_currency_pair_selection_invalid_pair(self):
        """Тест обработки выбора невалидной валютной пары"""
        self.callback_query.data = 'pair_invalid_pair'
        
        await handle_currency_pair_selection(self.callback_query, self.state)
        
        # Проверяем, что был отправлен ответ об ошибке
        self.callback_query.answer.assert_called_once()
        answer_call = self.callback_query.answer.call_args
        assert "Неизвестная валютная пара" in answer_call[0][0], "Должно быть сообщение об ошибке"
        assert answer_call[1]['show_alert'] is True, "Должен быть показан alert"
    
    @pytest.mark.asyncio
    async def test_handle_cancel_selection(self):
        """Тест обработки отмены выбора валютной пары"""
        await handle_cancel_selection(self.callback_query)
        
        # Проверяем, что сообщение было обновлено
        self.message.edit_text.assert_called_once()
        
        # Проверяем содержимое сообщения об отмене
        call_args = self.message.edit_text.call_args
        message_text = call_args[0][0]
        
        assert "отменен" in message_text, "Сообщение должно содержать информацию об отмене"
        
        # Проверяем, что был отправлен ответ
        self.callback_query.answer.assert_called_once()
        answer_call = self.callback_query.answer.call_args
        assert "Операция отменена" in answer_call[0][0], "Ответ должен содержать информацию об отмене"


class TestCurrencyPairIntegration:
    """Интеграционные тесты для валютных пар"""
    
    def test_currency_pairs_consistency(self):
        """Тест консистентности данных валютных пар"""
        # Проверяем, что для каждой пары есть обратная пара
        bases = set()
        quotes = set()
        
        for pair_info in CURRENCY_PAIRS.values():
            bases.add(pair_info['base'])
            quotes.add(pair_info['quote'])
        
        # Должны быть только USDT пары
        expected_currencies = {'USDT', 'ZAR', 'THB', 'AED', 'IDR', 'RUB'}
        assert bases == expected_currencies, "Базовые валюты должны соответствовать ожидаемым"
        assert quotes == expected_currencies, "Котируемые валюты должны соответствовать ожидаемым"
    
    def test_currency_pairs_bidirectional(self):
        """Тест двунаправленности валютных пар"""
        # Проверяем, что для каждой пары есть обратная
        for pair_id, pair_info in CURRENCY_PAIRS.items():
            base = pair_info['base']
            quote = pair_info['quote']
            
            # Ищем обратную пару
            reverse_pair_found = False
            for other_pair_id, other_pair_info in CURRENCY_PAIRS.items():
                if (other_pair_info['base'] == quote and 
                    other_pair_info['quote'] == base):
                    reverse_pair_found = True
                    break
            
            assert reverse_pair_found, f"Не найдена обратная пара для {pair_id} ({base}/{quote})"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])