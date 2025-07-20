#!/usr/bin/env python3
"""
Unit тесты для новых валют: THB, AED, ZAR, IDR
Тестирование расширенной поддержки валют для RUB
"""

import pytest
from decimal import Decimal
from unittest.mock import Mock, AsyncMock, patch

# Импорты тестируемых модулей
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from handlers.fsm_states import (
    Currency, get_available_targets, is_valid_pair
)
from handlers.keyboards import create_target_currency_keyboard
from handlers.formatters import MessageFormatter


class TestNewCurrencies:
    """Тестирование новых валют THB, AED, ZAR, IDR"""
    
    def test_new_currency_enums(self):
        """Тест enum новых валют"""
        assert Currency.THB == "THB"
        assert Currency.AED == "AED" 
        assert Currency.ZAR == "ZAR"
        assert Currency.IDR == "IDR"
        
        # Проверяем, что они наследуются от str
        assert isinstance(Currency.THB, str)
        assert isinstance(Currency.AED, str)
        assert isinstance(Currency.ZAR, str)
        assert isinstance(Currency.IDR, str)
    
    def test_new_currencies_in_rub_targets(self):
        """Тест включения новых валют в TARGETS_FOR_RUB"""
        rub_targets = get_available_targets(Currency.RUB)
        
        # Старые валюты
        assert Currency.USDT in rub_targets
        assert Currency.USD in rub_targets
        assert Currency.EUR in rub_targets
        
        # Новые валюты
        assert Currency.THB in rub_targets
        assert Currency.AED in rub_targets
        assert Currency.ZAR in rub_targets
        assert Currency.IDR in rub_targets
        
        # Общее количество
        assert len(rub_targets) == 7
    
    def test_new_currency_pairs_validation(self):
        """Тест валидации пар с новыми валютами"""
        # RUB → новые валюты (должно быть валидно)
        assert is_valid_pair(Currency.RUB, Currency.THB) == True
        assert is_valid_pair(Currency.RUB, Currency.AED) == True
        assert is_valid_pair(Currency.RUB, Currency.ZAR) == True
        assert is_valid_pair(Currency.RUB, Currency.IDR) == True
        
        # Новые валюты → RUB (должно быть невалидно, так как новые валюты не могут быть исходными)
        assert is_valid_pair(Currency.THB, Currency.RUB) == False
        assert is_valid_pair(Currency.AED, Currency.RUB) == False
        assert is_valid_pair(Currency.ZAR, Currency.RUB) == False
        assert is_valid_pair(Currency.IDR, Currency.RUB) == False
        
        # Новые валюты между собой (должно быть невалидно)
        assert is_valid_pair(Currency.THB, Currency.AED) == False
        assert is_valid_pair(Currency.AED, Currency.ZAR) == False
        assert is_valid_pair(Currency.ZAR, Currency.IDR) == False
        
        # Новые валюты → старые фиатные (должно быть невалидно)
        assert is_valid_pair(Currency.THB, Currency.USD) == False
        assert is_valid_pair(Currency.AED, Currency.EUR) == False
        assert is_valid_pair(Currency.ZAR, Currency.USDT) == False
    
    def test_new_currencies_keyboard_display(self):
        """Тест отображения новых валют в клавиатуре"""
        keyboard = create_target_currency_keyboard(Currency.RUB)
        
        # Собираем весь текст кнопок
        buttons_text = []
        for row in keyboard.inline_keyboard:
            for button in row:
                buttons_text.append(button.text)
        
        # Проверяем наличие новых валют с правильными эмодзи и названиями
        assert any("🇹🇭 THB" in text and "Тайский бат" in text for text in buttons_text)
        assert any("🇦🇪 AED" in text and "Дирхам ОАЭ" in text for text in buttons_text)
        assert any("🇿🇦 ZAR" in text and "Рэнд ЮАР" in text for text in buttons_text)
        assert any("🇮🇩 IDR" in text and "Рупия" in text for text in buttons_text)
    
    def test_new_currencies_callback_data(self):
        """Тест callback данных для новых валют"""
        keyboard = create_target_currency_keyboard(Currency.RUB)
        
        # Собираем все callback_data
        callbacks = []
        for row in keyboard.inline_keyboard:
            for button in row:
                if button.callback_data and button.callback_data.startswith('target_'):
                    callbacks.append(button.callback_data)
        
        # Проверяем наличие callback данных для новых валют
        assert "target_THB" in callbacks
        assert "target_AED" in callbacks
        assert "target_ZAR" in callbacks
        assert "target_IDR" in callbacks


class TestNewCurrencyFormatting:
    """Тестирование форматирования сообщений с новыми валютами"""
    
    def test_source_selected_message_formatting(self):
        """Тест форматирования сообщения выбора исходной валюты RUB"""
        message = MessageFormatter.format_source_selected_message(Currency.RUB)
        
        # Должно упоминать, что доступно больше валют
        assert "RUB" in message or "рубли" in message
        assert "получает" in message
    
    def test_target_selected_message_with_new_currencies(self):
        """Тест форматирования сообщения с новыми валютами"""
        # THB
        message_thb = MessageFormatter.format_target_selected_message(
            Currency.RUB, Currency.THB, Decimal("2.50")
        )
        assert "RUB → THB" in message_thb
        assert "1 THB = 2,50 RUB" in message_thb  # Новый формат курса
        
        # AED  
        message_aed = MessageFormatter.format_target_selected_message(
            Currency.RUB, Currency.AED, Decimal("27.20")
        )
        assert "RUB → AED" in message_aed
        assert "1 AED = 27,20 RUB" in message_aed  # Новый формат курса
        
        # ZAR
        message_zar = MessageFormatter.format_target_selected_message(
            Currency.RUB, Currency.ZAR, Decimal("5.41")
        )
        assert "RUB → ZAR" in message_zar
        assert "1 ZAR = 5,41 RUB" in message_zar  # Новый формат курса
        
        # IDR
        message_idr = MessageFormatter.format_target_selected_message(
            Currency.RUB, Currency.IDR, Decimal("156.50")
        )
        assert "RUB → IDR" in message_idr
        assert "1 IDR = 156,50 RUB" in message_idr  # Новый формат курса
    
    def test_final_result_with_new_currencies(self):
        """Тест форматирования финального результата с новыми валютами"""
        # RUB → THB
        message_thb = MessageFormatter.format_final_result(
            Currency.RUB, Currency.THB,
            Decimal("10000"), Decimal("2"), Decimal("2.55"), Decimal("3921.57")
        )
        assert "RUB → THB" in message_thb
        assert "10 000 RUB" in message_thb
        assert "3 921.57 THB" in message_thb
        
        # RUB → AED
        message_aed = MessageFormatter.format_final_result(
            Currency.RUB, Currency.AED,
            Decimal("5000"), Decimal("1.5"), Decimal("27.61"), Decimal("181.09")
        )
        assert "RUB → AED" in message_aed
        assert "5 000 RUB" in message_aed
        assert "181.09 AED" in message_aed
        
        # RUB → ZAR
        message_zar = MessageFormatter.format_final_result(
            Currency.RUB, Currency.ZAR,
            Decimal("15000"), Decimal("3"), Decimal("5.57"), Decimal("2693.36")
        )
        assert "RUB → ZAR" in message_zar
        assert "15 000 RUB" in message_zar
        assert "2 693.36 ZAR" in message_zar
        
        # RUB → IDR
        message_idr = MessageFormatter.format_final_result(
            Currency.RUB, Currency.IDR,
            Decimal("8000"), Decimal("2.5"), Decimal("160.41"), Decimal("49.87")
        )
        assert "RUB → IDR" in message_idr
        assert "8 000 RUB" in message_idr
        assert "49.87 IDR" in message_idr


class TestNewCurrencyAPIIntegration:
    """Тестирование интеграции с API для новых валют"""
    
    @pytest.mark.asyncio
    async def test_api_rate_methods_exist(self):
        """Тест существования методов получения курсов для новых валют"""
        # Импортируем ExchangeCalculator
        from handlers.admin_flow import ExchangeCalculator
        
        # Проверяем, что методы существуют
        assert hasattr(ExchangeCalculator, 'get_thb_rub_rate')
        assert hasattr(ExchangeCalculator, 'get_aed_rub_rate')
        assert hasattr(ExchangeCalculator, 'get_zar_rub_rate')
        assert hasattr(ExchangeCalculator, 'get_idr_rub_rate')
        
        # Проверяем, что это async методы
        import asyncio
        assert asyncio.iscoroutinefunction(ExchangeCalculator.get_thb_rub_rate)
        assert asyncio.iscoroutinefunction(ExchangeCalculator.get_aed_rub_rate)
        assert asyncio.iscoroutinefunction(ExchangeCalculator.get_zar_rub_rate)
        assert asyncio.iscoroutinefunction(ExchangeCalculator.get_idr_rub_rate)
    
    @pytest.mark.asyncio 
    @patch('handlers.admin_flow.fiat_rates_service')
    async def test_get_base_rate_for_new_currency_pairs(self, mock_fiat_service):
        """Тест получения базовых курсов для новых валютных пар"""
        from handlers.admin_flow import ExchangeCalculator
        
        # Настраиваем mock для разных валют
        mock_rate = Mock()
        mock_rate.rate = 2.50
        mock_rate.source = "apilayer"
        mock_fiat_service.get_fiat_exchange_rate = AsyncMock(return_value=mock_rate)
        
        # Тестируем получение курсов для новых валют
        
        # THB/RUB
        mock_fiat_service.get_fiat_exchange_rate.return_value.rate = 2.50
        rate_thb = await ExchangeCalculator.get_base_rate_for_pair(Currency.RUB, Currency.THB)
        assert rate_thb == Decimal("2.50")
        mock_fiat_service.get_fiat_exchange_rate.assert_called_with('THB/RUB')
        
        # AED/RUB
        mock_fiat_service.get_fiat_exchange_rate.return_value.rate = 27.20
        rate_aed = await ExchangeCalculator.get_base_rate_for_pair(Currency.RUB, Currency.AED)
        assert rate_aed == Decimal("27.20")
        mock_fiat_service.get_fiat_exchange_rate.assert_called_with('AED/RUB')
        
        # ZAR/RUB
        mock_fiat_service.get_fiat_exchange_rate.return_value.rate = 5.41
        rate_zar = await ExchangeCalculator.get_base_rate_for_pair(Currency.RUB, Currency.ZAR)
        assert rate_zar == Decimal("5.41")
        mock_fiat_service.get_fiat_exchange_rate.assert_called_with('ZAR/RUB')
        
        # IDR/RUB
        mock_fiat_service.get_fiat_exchange_rate.return_value.rate = 156.50
        rate_idr = await ExchangeCalculator.get_base_rate_for_pair(Currency.RUB, Currency.IDR)
        assert rate_idr == Decimal("156.50")
        mock_fiat_service.get_fiat_exchange_rate.assert_called_with('IDR/RUB')


class TestNewCurrencyCalculations:
    """Тестирование расчетов с новыми валютами"""
    
    def test_margin_calculation_with_new_currencies(self):
        """Тест расчета наценки с новыми валютами"""
        from handlers.admin_flow import ExchangeCalculator
        
        # RUB → THB с наценкой 2%
        base_rate = Decimal("2.50")
        margin = Decimal("2")
        final_rate = ExchangeCalculator.calculate_final_rate(
            Currency.RUB, Currency.THB, base_rate, margin
        )
        expected = base_rate * Decimal("1.02")  # 2.50 * 1.02 = 2.55
        assert final_rate == expected.quantize(Decimal('0.01'))
        
        # RUB → AED с наценкой 1.5%
        base_rate = Decimal("27.20")
        margin = Decimal("1.5")
        final_rate = ExchangeCalculator.calculate_final_rate(
            Currency.RUB, Currency.AED, base_rate, margin
        )
        expected = base_rate * Decimal("1.015")  # 27.20 * 1.015 = 27.608
        assert final_rate == expected.quantize(Decimal('0.01'))
    
    def test_result_calculation_with_new_currencies(self):
        """Тест расчета результата с новыми валютами"""
        from handlers.admin_flow import ExchangeCalculator
        
        # 10,000 RUB → THB по курсу 2.55
        amount = Decimal("10000")
        final_rate = Decimal("2.55")
        result = ExchangeCalculator.calculate_result(
            Currency.RUB, Currency.THB, amount, final_rate
        )
        expected = amount / final_rate  # 10000 / 2.55 ≈ 3921.57
        assert result == expected.quantize(Decimal('0.01'))
        
        # 5,000 RUB → AED по курсу 27.61
        amount = Decimal("5000")
        final_rate = Decimal("27.61")
        result = ExchangeCalculator.calculate_result(
            Currency.RUB, Currency.AED, amount, final_rate
        )
        expected = amount / final_rate  # 5000 / 27.61 ≈ 181.09
        assert result == expected.quantize(Decimal('0.01'))
        
        # 15,000 RUB → ZAR по курсу 5.57
        amount = Decimal("15000")
        final_rate = Decimal("5.57")
        result = ExchangeCalculator.calculate_result(
            Currency.RUB, Currency.ZAR, amount, final_rate
        )
        expected = amount / final_rate  # 15000 / 5.57 ≈ 2693.36
        assert result == expected.quantize(Decimal('0.01'))
        
        # 8,000 RUB → IDR по курсу 160.41
        amount = Decimal("8000")
        final_rate = Decimal("160.41")
        result = ExchangeCalculator.calculate_result(
            Currency.RUB, Currency.IDR, amount, final_rate
        )
        expected = amount / final_rate  # 8000 / 160.41 ≈ 49.87
        assert result == expected.quantize(Decimal('0.01'))


class TestNewCurrencyErrorHandling:
    """Тестирование обработки ошибок с новыми валютами"""
    
    @pytest.mark.asyncio
    @patch('handlers.admin_flow.fiat_rates_service')
    async def test_api_error_handling_for_new_currencies(self, mock_fiat_service):
        """Тест обработки ошибок API для новых валют"""
        from handlers.admin_flow import ExchangeCalculator
        from services.models import APILayerError
        
        # Настраиваем mock для возврата ошибки
        mock_fiat_service.get_fiat_exchange_rate = AsyncMock(side_effect=Exception("Network error"))
        
        # Проверяем, что ошибки правильно обрабатываются
        with pytest.raises(APILayerError):
            await ExchangeCalculator.get_thb_rub_rate()
        
        with pytest.raises(APILayerError):
            await ExchangeCalculator.get_aed_rub_rate()
        
        with pytest.raises(APILayerError):
            await ExchangeCalculator.get_zar_rub_rate()
        
        with pytest.raises(APILayerError):
            await ExchangeCalculator.get_idr_rub_rate()
    
    @pytest.mark.asyncio
    @patch('handlers.admin_flow.fiat_rates_service')
    async def test_invalid_rate_handling_for_new_currencies(self, mock_fiat_service):
        """Тест обработки невалидных курсов для новых валют"""
        from handlers.admin_flow import ExchangeCalculator
        from services.models import APILayerError
        
        # Настраиваем mock для возврата невалидного курса
        mock_rate = Mock()
        mock_rate.rate = 0  # Невалидный курс
        mock_fiat_service.get_fiat_exchange_rate = AsyncMock(return_value=mock_rate)
        
        # Проверяем, что невалидные курсы обрабатываются
        with pytest.raises(APILayerError):
            await ExchangeCalculator.get_thb_rub_rate()


if __name__ == '__main__':
    # Запуск тестов
    pytest.main([__file__, '-v'])