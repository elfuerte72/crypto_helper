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

from handlers.admin_handlers import (
    CURRENCY_PAIRS,
    get_currency_pair_info,
    is_valid_currency_pair,
    handle_currency_pair_selection,
    handle_cancel_selection,
    handle_header_callbacks
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
        # Должно быть 16 пар: 4 RUB, 4 USDT, 4 обратных RUB, 4 обратных USDT
        assert len(CURRENCY_PAIRS) == 16, "Должно быть 16 валютных пар"
    
    def test_currency_pairs_naming(self):
        """Тест правильности именования валютных пар"""
        expected_pairs = {
            # RUB пары
            'rub_zar', 'rub_thb', 'rub_aed', 'rub_idr',
            # USDT пары
            'usdt_zar', 'usdt_thb', 'usdt_aed', 'usdt_idr',
            # Обратные RUB пары
            'zar_rub', 'thb_rub', 'aed_rub', 'idr_rub',
            # Обратные USDT пары
            'zar_usdt', 'thb_usdt', 'aed_usdt', 'idr_usdt'
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
        pair_info = get_currency_pair_info('rub_zar')
        
        assert pair_info is not None, "Должна быть возвращена информация о паре"
        assert pair_info['name'] == 'RUB/ZAR', "Неправильное имя пары"
        assert pair_info['base'] == 'RUB', "Неправильная базовая валюта"
        assert pair_info['quote'] == 'ZAR', "Неправильная котируемая валюта"
    
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
        valid_pairs = ['rub_zar', 'usdt_thb', 'zar_rub', 'aed_usdt']
        
        for pair in valid_pairs:
            assert is_valid_currency_pair(pair), f"Пара {pair} должна быть валидной"
    
    def test_is_valid_currency_pair_invalid(self):
        """Тест проверки валидности для невалидных пар"""
        invalid_pairs = ['invalid_pair', 'rub_usd', 'btc_eth', '']
        
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
    
    @pytest.mark.asyncio
    async def test_handle_currency_pair_selection_valid_pair(self):
        """Тест обработки выбора валидной валютной пары"""
        self.callback_query.data = 'rub_zar'
        
        await handle_currency_pair_selection(self.callback_query)
        
        # Проверяем, что сообщение было обновлено
        self.message.edit_text.assert_called_once()
        
        # Проверяем содержимое сообщения
        call_args = self.message.edit_text.call_args
        message_text = call_args[0][0]
        
        assert "RUB/ZAR" in message_text, "Сообщение должно содержать название пары"
        assert "🇷🇺➡️🇿🇦" in message_text, "Сообщение должно содержать emoji пары"
        assert "Российский рубль → Южноафриканский рэнд" in message_text, "Сообщение должно содержать описание"
        
        # Проверяем, что был отправлен ответ
        self.callback_query.answer.assert_called_once()
        answer_call = self.callback_query.answer.call_args
        assert "RUB/ZAR" in answer_call[0][0], "Ответ должен содержать название пары"
    
    @pytest.mark.asyncio
    async def test_handle_currency_pair_selection_invalid_pair(self):
        """Тест обработки выбора невалидной валютной пары"""
        self.callback_query.data = 'invalid_pair'
        
        await handle_currency_pair_selection(self.callback_query)
        
        # Проверяем, что сообщение не было обновлено
        self.message.edit_text.assert_not_called()
        
        # Проверяем, что был отправлен ответ об ошибке
        self.callback_query.answer.assert_called_once()
        answer_call = self.callback_query.answer.call_args
        assert "Неизвестная валютная пара" in answer_call[0][0], "Должно быть сообщение об ошибке"
        assert answer_call[1]['show_alert'] is True, "Должен быть показан alert"
    
    @pytest.mark.asyncio
    async def test_handle_currency_pair_selection_all_pairs(self):
        """Тест обработки всех валютных пар"""
        for pair_id in CURRENCY_PAIRS.keys():
            # Сбрасываем mock объекты
            self.message.edit_text.reset_mock()
            self.callback_query.answer.reset_mock()
            
            self.callback_query.data = pair_id
            
            await handle_currency_pair_selection(self.callback_query)
            
            # Проверяем, что сообщение было обновлено
            self.message.edit_text.assert_called_once(), f"Сообщение должно быть обновлено для пары {pair_id}"
            
            # Проверяем, что был отправлен ответ
            self.callback_query.answer.assert_called_once(), f"Должен быть отправлен ответ для пары {pair_id}"
    
    @pytest.mark.asyncio
    async def test_handle_currency_pair_selection_telegram_error(self):
        """Тест обработки ошибки Telegram API"""
        self.callback_query.data = 'rub_zar'
        self.message.edit_text.side_effect = TelegramBadRequest(method="editMessageText", message="Test error")
        
        await handle_currency_pair_selection(self.callback_query)
        
        # Проверяем, что был отправлен ответ об ошибке
        self.callback_query.answer.assert_called_once()
        answer_call = self.callback_query.answer.call_args
        assert "Произошла ошибка" in answer_call[0][0], "Должно быть сообщение об ошибке"
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
        
        assert "Операция отменена" in message_text, "Сообщение должно содержать информацию об отмене"
        
        # Проверяем, что был отправлен ответ
        self.callback_query.answer.assert_called_once()
        answer_call = self.callback_query.answer.call_args
        assert "Операция отменена" in answer_call[0][0], "Ответ должен содержать информацию об отмене"
    
    @pytest.mark.asyncio
    async def test_handle_header_callbacks(self):
        """Тест обработки callback'ов для заголовков"""
        header_callbacks = ['header_rub', 'header_usdt', 'header_reverse_rub', 'header_reverse_usdt']
        
        for header_callback in header_callbacks:
            # Сбрасываем mock объекты
            self.callback_query.answer.reset_mock()
            
            self.callback_query.data = header_callback
            
            await handle_header_callbacks(self.callback_query)
            
            # Проверяем, что был отправлен ответ
            self.callback_query.answer.assert_called_once()
            answer_call = self.callback_query.answer.call_args
            assert "Это заголовок" in answer_call[0][0], f"Должно быть сообщение о заголовке для {header_callback}"
            assert answer_call[1]['show_alert'] is False, "Не должен быть показан alert для заголовков"


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
        
        # Должны быть пары в обоих направлениях
        expected_currencies = {'RUB', 'USDT', 'ZAR', 'THB', 'AED', 'IDR'}
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
    
    def test_currency_pairs_emoji_consistency(self):
        """Тест консистентности emoji валютных пар"""
        # Проверяем, что emoji содержат правильные элементы
        for pair_id, pair_info in CURRENCY_PAIRS.items():
            emoji = pair_info['emoji']
            
            # Должно содержать стрелку
            assert '➡️' in emoji, f"Emoji для {pair_id} должно содержать стрелку"
            
            # Должно содержать соответствующие символы валют
            base = pair_info['base']
            quote = pair_info['quote']
            
            if base == 'RUB':
                assert '🇷🇺' in emoji, f"Emoji для {pair_id} должно содержать флаг России"
            elif base == 'USDT':
                assert '💰' in emoji, f"Emoji для {pair_id} должно содержать символ доллара"
            
            # Проверяем флаги для других валют
            flag_mapping = {
                'ZAR': '🇿🇦',
                'THB': '🇹🇭',
                'AED': '🇦🇪',
                'IDR': '🇮🇩'
            }
            
            if quote in flag_mapping:
                expected_flag = flag_mapping[quote]
                assert expected_flag in emoji, f"Emoji для {pair_id} должно содержать флаг {expected_flag}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])