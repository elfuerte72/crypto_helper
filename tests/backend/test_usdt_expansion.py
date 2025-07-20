#!/usr/bin/env python3
"""
Unit тесты для расширения поддержки USDT
Тестирование новых направлений USDT → (EUR, USD, THB, AED, ZAR, IDR)
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


class TestUSDTExpansion:
    """Тестирование расширенной поддержки USDT"""
    
    def test_usdt_targets_expanded(self):
        """Тест расширения целевых валют для USDT"""
        usdt_targets = get_available_targets(Currency.USDT)
        
        # Проверяем старую валюту
        assert Currency.RUB in usdt_targets
        
        # Проверяем новые валюты
        assert Currency.USD in usdt_targets
        assert Currency.EUR in usdt_targets
        assert Currency.THB in usdt_targets
        assert Currency.AED in usdt_targets
        assert Currency.ZAR in usdt_targets
        assert Currency.IDR in usdt_targets
        
        # Общее количество
        assert len(usdt_targets) == 7
        
        # Проверяем что RUB по-прежнему поддерживает те же 7 валют
        rub_targets = get_available_targets(Currency.RUB)
        assert len(rub_targets) == 7
    
    def test_usdt_pair_validation(self):
        """Тест валидации новых пар с USDT"""
        # USDT → новые валюты (должно быть валидно)
        assert is_valid_pair(Currency.USDT, Currency.USD) == True
        assert is_valid_pair(Currency.USDT, Currency.EUR) == True
        assert is_valid_pair(Currency.USDT, Currency.THB) == True
        assert is_valid_pair(Currency.USDT, Currency.AED) == True
        assert is_valid_pair(Currency.USDT, Currency.ZAR) == True
        assert is_valid_pair(Currency.USDT, Currency.IDR) == True
        
        # USDT → RUB (старая пара, должна остаться валидной)
        assert is_valid_pair(Currency.USDT, Currency.RUB) == True
        
        # Обратные направления не поддерживаются
        assert is_valid_pair(Currency.USD, Currency.USDT) == False
        assert is_valid_pair(Currency.EUR, Currency.USDT) == False
        assert is_valid_pair(Currency.THB, Currency.USDT) == False
    
    def test_usdt_keyboard_display(self):
        """Тест отображения новых валют в клавиатуре для USDT"""
        keyboard = create_target_currency_keyboard(Currency.USDT)
        
        # Собираем весь текст кнопок
        buttons_text = []
        for row in keyboard.inline_keyboard:
            for button in row:
                buttons_text.append(button.text)
        
        # Проверяем наличие всех валют
        assert any("RUB" in text and "Рубли" in text for text in buttons_text)
        assert any("USD" in text and "Доллары" in text for text in buttons_text)
        assert any("EUR" in text and "Евро" in text for text in buttons_text)
        assert any("THB" in text and "Тайский бат" in text for text in buttons_text)
        assert any("AED" in text and "Дирхам ОАЭ" in text for text in buttons_text)
        assert any("ZAR" in text and "Рэнд ЮАР" in text for text in buttons_text)
        assert any("IDR" in text and "Рупия" in text for text in buttons_text)
    
    def test_usdt_callback_data(self):
        """Тест callback данных для новых пар USDT"""
        keyboard = create_target_currency_keyboard(Currency.USDT)
        
        # Собираем все callback_data
        callbacks = []
        for row in keyboard.inline_keyboard:
            for button in row:
                if button.callback_data and button.callback_data.startswith('target_'):
                    callbacks.append(button.callback_data)
        
        # Проверяем наличие callback данных для всех валют
        assert "target_RUB" in callbacks
        assert "target_USD" in callbacks
        assert "target_EUR" in callbacks
        assert "target_THB" in callbacks
        assert "target_AED" in callbacks
        assert "target_ZAR" in callbacks
        assert "target_IDR" in callbacks


class TestUSDTFormatting:
    """Тестирование форматирования сообщений с USDT"""
    
    def test_usdt_rate_formatting(self):
        """Тест форматирования курсов USDT к новым валютам"""
        # USDT → USD
        rate_text = MessageFormatter._format_rate_for_pair(Currency.USDT, Currency.USD, Decimal("1.02"))
        assert rate_text == "<b>1 USDT = 1,02 USD</b>"
        
        # USDT → EUR
        rate_text = MessageFormatter._format_rate_for_pair(Currency.USDT, Currency.EUR, Decimal("0.95"))
        assert rate_text == "<b>1 USDT = 0,95 EUR</b>"
        
        # USDT → THB
        rate_text = MessageFormatter._format_rate_for_pair(Currency.USDT, Currency.THB, Decimal("35.50"))
        assert rate_text == "<b>1 USDT = 35,50 THB</b>"
        
        # USDT → AED
        rate_text = MessageFormatter._format_rate_for_pair(Currency.USDT, Currency.AED, Decimal("3.67"))
        assert rate_text == "<b>1 USDT = 3,67 AED</b>"
        
        # USDT → ZAR
        rate_text = MessageFormatter._format_rate_for_pair(Currency.USDT, Currency.ZAR, Decimal("18.50"))
        assert rate_text == "<b>1 USDT = 18,50 ZAR</b>"
        
        # USDT → IDR
        rate_text = MessageFormatter._format_rate_for_pair(Currency.USDT, Currency.IDR, Decimal("15650.00"))
        assert rate_text == "<b>1 USDT = 15650,00 IDR</b>"
        
        # USDT → RUB (старая пара, должна остаться такой же)
        rate_text = MessageFormatter._format_rate_for_pair(Currency.USDT, Currency.RUB, Decimal("100.15"))
        assert rate_text == "<b>1 USDT = 100,15 RUB</b>"
    
    def test_usdt_target_selected_messages(self):
        """Тест форматирования сообщений выбора целевой валюты с USDT"""
        # USDT → USD
        message = MessageFormatter.format_target_selected_message(
            Currency.USDT, Currency.USD, Decimal("1.02")
        )
        assert "USDT → USD" in message
        assert "1 USDT = 1,02 USD" in message
        
        # USDT → EUR
        message = MessageFormatter.format_target_selected_message(
            Currency.USDT, Currency.EUR, Decimal("0.95")
        )
        assert "USDT → EUR" in message
        assert "1 USDT = 0,95 EUR" in message
        
        # USDT → THB
        message = MessageFormatter.format_target_selected_message(
            Currency.USDT, Currency.THB, Decimal("35.50")
        )
        assert "USDT → THB" in message
        assert "1 USDT = 35,50 THB" in message
    
    def test_usdt_final_result_messages(self):
        """Тест форматирования финального результата с USDT"""
        # USDT → USD
        message = MessageFormatter.format_final_result(
            Currency.USDT, Currency.USD,
            Decimal("100"), Decimal("2"), Decimal("1.00"), Decimal("98.00")
        )
        assert "USDT → USD" in message
        assert "100 USDT" in message
        assert "98.00 USD" in message
        assert "1 USDT = 1,00 USD" in message
        
        # USDT → EUR
        message = MessageFormatter.format_final_result(
            Currency.USDT, Currency.EUR,
            Decimal("50"), Decimal("1.5"), Decimal("0.936"), Decimal("46.80")
        )
        assert "USDT → EUR" in message
        assert "50 USDT" in message
        assert "46.80 EUR" in message


class TestUSDTAPIIntegration:
    """Тестирование API интеграции для USDT"""
    
    @pytest.mark.asyncio
    async def test_usdt_cross_rate_calculation_methods_exist(self):
        """Тест существования методов кросс-конвертации для USDT"""
        from handlers.admin_flow import ExchangeCalculator
        
        # Проверяем, что новый метод существует
        assert hasattr(ExchangeCalculator, 'get_usdt_to_fiat_rate')
        
        # Проверяем, что это async метод
        import asyncio
        assert asyncio.iscoroutinefunction(ExchangeCalculator.get_usdt_to_fiat_rate)
    
    @pytest.mark.asyncio 
    @patch('handlers.admin_flow.ExchangeCalculator.get_usdt_rub_rate')
    @patch('handlers.admin_flow.ExchangeCalculator.get_usd_rub_rate')
    async def test_usdt_to_usd_cross_rate(self, mock_usd_rub, mock_usdt_rub):
        """Тест кросс-конвертации USDT → USD"""
        from handlers.admin_flow import ExchangeCalculator
        
        # Настраиваем mock'и: USDT/RUB = 100, USD/RUB = 98
        mock_usdt_rub.return_value = Decimal("100.00")
        mock_usd_rub.return_value = Decimal("98.00")
        
        # Тестируем кросс-курс
        cross_rate = await ExchangeCalculator.get_usdt_to_fiat_rate(Currency.USD)
        
        # USDT/USD = USDT/RUB ÷ USD/RUB = 100 ÷ 98 ≈ 1.0204
        expected = Decimal("100.00") / Decimal("98.00")
        assert cross_rate == expected.quantize(Decimal('0.000001'))
        
        # Проверяем, что методы были вызваны
        mock_usdt_rub.assert_called_once()
        mock_usd_rub.assert_called_once()
    
    @pytest.mark.asyncio 
    @patch('handlers.admin_flow.ExchangeCalculator.get_usdt_rub_rate')
    @patch('handlers.admin_flow.ExchangeCalculator.get_eur_rub_rate')
    async def test_usdt_to_eur_cross_rate(self, mock_eur_rub, mock_usdt_rub):
        """Тест кросс-конвертации USDT → EUR"""
        from handlers.admin_flow import ExchangeCalculator
        
        # Настраиваем mock'и: USDT/RUB = 100, EUR/RUB = 110
        mock_usdt_rub.return_value = Decimal("100.00")
        mock_eur_rub.return_value = Decimal("110.00")
        
        # Тестируем кросс-курс
        cross_rate = await ExchangeCalculator.get_usdt_to_fiat_rate(Currency.EUR)
        
        # USDT/EUR = USDT/RUB ÷ EUR/RUB = 100 ÷ 110 ≈ 0.909091
        expected = Decimal("100.00") / Decimal("110.00")
        assert cross_rate == expected.quantize(Decimal('0.000001'))
    
    @pytest.mark.asyncio 
    @patch('handlers.admin_flow.ExchangeCalculator.get_usdt_to_fiat_rate')
    async def test_get_base_rate_for_usdt_pairs(self, mock_cross_rate):
        """Тест получения базовых курсов для новых пар USDT"""
        from handlers.admin_flow import ExchangeCalculator
        
        # Настраиваем mock для кросс-курса
        mock_cross_rate.return_value = Decimal("1.02")
        
        # Тестируем получение курса для USDT → USD
        rate = await ExchangeCalculator.get_base_rate_for_pair(Currency.USDT, Currency.USD)
        
        assert rate == Decimal("1.02")
        mock_cross_rate.assert_called_once_with(Currency.USD)


class TestUSDTCalculations:
    """Тестирование расчетов с новыми парами USDT"""
    
    def test_usdt_margin_calculation(self):
        """Тест расчета наценки для новых пар USDT"""
        from handlers.admin_flow import ExchangeCalculator
        
        # USDT → USD с наценкой 2%
        base_rate = Decimal("1.00")
        margin = Decimal("2")
        final_rate = ExchangeCalculator.calculate_final_rate(
            Currency.USDT, Currency.USD, base_rate, margin
        )
        # Для USDT уменьшаем курс: 1.00 × (1 - 0.02) = 0.98
        expected = base_rate * Decimal("0.98")
        assert final_rate == expected.quantize(Decimal('0.01'))
        
        # USDT → EUR с наценкой 1.5%
        base_rate = Decimal("0.95")
        margin = Decimal("1.5")
        final_rate = ExchangeCalculator.calculate_final_rate(
            Currency.USDT, Currency.EUR, base_rate, margin
        )
        # 0.95 × (1 - 0.015) = 0.95 × 0.985 = 0.93575
        expected = base_rate * Decimal("0.985")
        assert final_rate == expected.quantize(Decimal('0.01'))
    
    def test_usdt_result_calculation(self):
        """Тест расчета результата для новых пар USDT"""
        from handlers.admin_flow import ExchangeCalculator
        
        # 100 USDT → USD по курсу 0.98
        amount = Decimal("100")
        final_rate = Decimal("0.98")
        result = ExchangeCalculator.calculate_result(
            Currency.USDT, Currency.USD, amount, final_rate
        )
        # Для USDT умножаем: 100 × 0.98 = 98.00
        expected = amount * final_rate
        assert result == expected.quantize(Decimal('0.01'))
        
        # 50 USDT → EUR по курсу 0.936
        amount = Decimal("50")
        final_rate = Decimal("0.936")
        result = ExchangeCalculator.calculate_result(
            Currency.USDT, Currency.EUR, amount, final_rate
        )
        # 50 × 0.936 = 46.80
        expected = amount * final_rate
        assert result == expected.quantize(Decimal('0.01'))


class TestUSDTErrorHandling:
    """Тестирование обработки ошибок для новых пар USDT"""
    
    @pytest.mark.asyncio
    async def test_unsupported_currency_error(self):
        """Тест ошибки для неподдерживаемой валюты в кросс-конвертации"""
        from handlers.admin_flow import ExchangeCalculator
        
        # Создаем несуществующую валюту
        class FakeCurrency:
            value = "XXX"
        
        fake_currency = FakeCurrency()
        
        with pytest.raises(ValueError) as exc_info:
            await ExchangeCalculator.get_usdt_to_fiat_rate(fake_currency)
        
        assert "Неподдерживаемая валюта для кросс-конвертации" in str(exc_info.value)
    
    @pytest.mark.asyncio 
    @patch('handlers.admin_flow.ExchangeCalculator.get_usdt_rub_rate')
    async def test_cross_rate_api_error_propagation(self, mock_usdt_rub):
        """Тест передачи ошибок API в кросс-конвертации"""
        from handlers.admin_flow import ExchangeCalculator
        from services.models import RapiraAPIError
        
        # Настраиваем mock для возврата ошибки
        mock_usdt_rub.side_effect = RapiraAPIError("Network error")
        
        # Проверяем, что ошибка передается
        with pytest.raises(RapiraAPIError):
            await ExchangeCalculator.get_usdt_to_fiat_rate(Currency.USD)


if __name__ == '__main__':
    # Запуск тестов
    pytest.main([__file__, '-v'])