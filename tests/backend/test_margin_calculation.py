#!/usr/bin/env python3
"""
Unit tests for margin calculation functionality
Tests for MarginCalculator class and related functionality
"""

import pytest
import asyncio
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

# Обновленные импорты из новых модулей
from handlers.calculation_logic import MarginCalculator, CalculationResult
from handlers.validation import ValidationError
from handlers.formatters import MessageFormatter
from handlers.keyboards import create_margin_selection_keyboard, create_result_keyboard
from handlers.fsm_states import MarginCalculationError
from services.api_service import ExchangeRate


class TestMarginCalculator:
    """Test cases for MarginCalculator class"""
    
    def test_calculate_final_rate_positive_margin(self):
        """Test calculation with positive margin"""
        base_rate = Decimal("100")
        margin = Decimal("5")  # 5%
        
        result = MarginCalculator.calculate_final_rate(base_rate, margin)
        expected = Decimal("105")
        
        assert result == expected
    
    def test_calculate_final_rate_negative_margin(self):
        """Test calculation with negative margin (discount)"""
        base_rate = Decimal("100")
        margin = Decimal("-10")  # -10%
        
        result = MarginCalculator.calculate_final_rate(base_rate, margin)
        expected = Decimal("90")
        
        assert result == expected
    
    def test_calculate_final_rate_zero_margin(self):
        """Test calculation with zero margin"""
        base_rate = Decimal("100")
        margin = Decimal("0")
        
        result = MarginCalculator.calculate_final_rate(base_rate, margin)
        expected = Decimal("100")
        
        assert result == expected
    
    def test_calculate_final_rate_fractional_margin(self):
        """Test calculation with fractional margin"""
        base_rate = Decimal("100")
        margin = Decimal("2.5")  # 2.5%
        
        result = MarginCalculator.calculate_final_rate(base_rate, margin)
        expected = Decimal("102.5")
        
        assert result == expected
    
    def test_calculate_final_rate_precision(self):
        """Test calculation precision with complex numbers"""
        base_rate = Decimal("1.23456789")
        margin = Decimal("3.7")  # 3.7%
        
        result = MarginCalculator.calculate_final_rate(base_rate, margin)
        # 1.23456789 * 1.037 = 1.28024690093 (actual calculation)
        expected = Decimal("1.28024690")  # Rounded to 8 decimal places
        
        assert result == expected
    
    def test_format_currency_value_btc(self):
        """Test currency formatting for BTC"""
        value = Decimal("1.23456789")
        result = MarginCalculator.format_currency_value(value, "BTC")
        assert result == "1.23456789"
    
    def test_format_currency_value_usdt(self):
        """Test currency formatting for USDT"""
        value = Decimal("1234.56789")
        result = MarginCalculator.format_currency_value(value, "USDT")
        assert result == "1234.5679"
    
    def test_format_currency_value_rub(self):
        """Test currency formatting for RUB"""
        value = Decimal("1234.56789")
        result = MarginCalculator.format_currency_value(value, "RUB")
        assert result == "1234.57"
    
    def test_format_currency_value_small_value(self):
        """Test currency formatting for small values"""
        value = Decimal("0.00012345")
        result = MarginCalculator.format_currency_value(value, "OTHER")
        assert result == "0.00012345"
    
    def test_format_currency_value_large_value(self):
        """Test currency formatting for large values"""
        value = Decimal("12345.6789")
        result = MarginCalculator.format_currency_value(value, "OTHER")
        assert result == "12345.6789"
    
    def test_calculate_exchange_amounts(self):
        """Test calculation of exchange amounts"""
        amount = Decimal("1000")
        base_rate = Decimal("100")
        final_rate = Decimal("105")
        
        amount_base, amount_final, difference = MarginCalculator.calculate_exchange_amounts(
            amount, base_rate, final_rate
        )
        
        assert amount_base == Decimal("100000")
        assert amount_final == Decimal("105000")
        assert difference == Decimal("5000")


class TestCalculationResult:
    """Test cases for CalculationResult class"""
    
    def test_calculation_result_creation(self):
        """Test CalculationResult creation"""
        pair_info = {
            'name': 'USDT/RUB',
            'base': 'USDT',
            'quote': 'RUB',
            'description': 'Tether к Российскому рублю',
            'emoji': '🇷🇺'
        }
        
        amount = Decimal("1000")
        base_rate = Decimal("95.5")
        margin = Decimal("5")
        final_rate = Decimal("100.275")
        exchange_rate_data = {
            'rate': 95.5,
            'timestamp': '2023-12-01T12:00:00',
            'source': 'rapira'
        }
        
        result = CalculationResult(
            pair_info, amount, base_rate, margin, final_rate, exchange_rate_data
        )
        
        assert result.pair_info == pair_info
        assert result.amount == amount
        assert result.base_rate == base_rate
        assert result.margin == margin
        assert result.final_rate == final_rate
        assert result.rate_change == Decimal("4.775")  # 100.275 - 95.5
    
    def test_calculation_result_to_dict(self):
        """Test CalculationResult to_dict method"""
        pair_info = {'name': 'USDT/RUB'}
        result = CalculationResult(
            pair_info, Decimal("100"), Decimal("95"), Decimal("5"), Decimal("99.75"), {}
        )
        
        result_dict = result.to_dict()
        
        assert isinstance(result_dict, dict)
        assert result_dict['amount'] == 100.0
        assert result_dict['base_rate'] == 95.0
        assert result_dict['margin'] == 5.0
        assert result_dict['final_rate'] == 99.75


class TestKeyboardCreation:
    """Test cases for keyboard creation functions"""
    
    def test_create_margin_selection_keyboard(self):
        """Test creation of margin selection keyboard"""
        keyboard = create_margin_selection_keyboard()
        
        # Check that keyboard is created
        assert keyboard is not None
        assert hasattr(keyboard, 'inline_keyboard')
        assert len(keyboard.inline_keyboard) > 0
        
        # Check for control buttons
        cancel_found = False
        main_menu_found = False
        for row in keyboard.inline_keyboard:
            for button in row:
                if button.callback_data == 'cancel_margin':
                    cancel_found = True
                elif button.callback_data == 'back_to_main':
                    main_menu_found = True
        
        assert cancel_found, "Cancel button should be present"
        assert main_menu_found, "Main menu button should be present"
    
    def test_create_result_keyboard(self):
        """Test creation of result keyboard"""
        keyboard = create_result_keyboard()
        
        # Check that keyboard is created
        assert keyboard is not None
        assert hasattr(keyboard, 'inline_keyboard')
        assert len(keyboard.inline_keyboard) > 0
        
        # Check for expected buttons
        expected_callbacks = [
            'recalculate_margin',
            'back_to_main'
        ]
        
        found_callbacks = []
        for row in keyboard.inline_keyboard:
            for button in row:
                if button.callback_data in expected_callbacks:
                    found_callbacks.append(button.callback_data)
        
        for callback in expected_callbacks:
            assert callback in found_callbacks, f"Button with callback '{callback}' should be present"


class TestFormatCalculationResult:
    """Test cases for result formatting function"""
    
    def test_format_calculation_result_positive_margin(self):
        """Test formatting result with positive margin"""
        pair_info = {
            'name': 'USDT/RUB',
            'base': 'USDT',
            'quote': 'RUB',
            'description': 'Tether к Российскому рублю',
            'emoji': '🇷🇺'
        }
        
        amount = Decimal("1000")
        base_rate = Decimal("95.5")
        margin = Decimal("5")
        final_rate = Decimal("100.275")
        exchange_rate_data = {
            'timestamp': '2023-12-01T12:00:00',
            'source': 'rapira'
        }
        
        result = CalculationResult(
            pair_info, amount, base_rate, margin, final_rate, exchange_rate_data
        )
        
        formatted_result = MessageFormatter.format_calculation_result(result)
        
        # Check that result contains expected elements
        assert "Расчет курса завершен" in formatted_result
        assert "USDT/RUB" in formatted_result
        assert "🇷🇺" in formatted_result
        assert "95.50" in formatted_result  # Base rate
        assert "100.28" in formatted_result  # Final rate
        assert "+5%" in formatted_result    # Margin
        assert "📈" in formatted_result      # Positive change emoji
        assert "2023-12-01 12:00:00" in formatted_result  # Timestamp
        assert "rapira" in formatted_result  # Source
    
    def test_format_calculation_result_negative_margin(self):
        """Test formatting result with negative margin"""
        pair_info = {
            'name': 'USDT/THB',
            'base': 'USDT',
            'quote': 'THB',
            'description': 'Tether к Тайскому бату',
            'emoji': '🇹🇭'
        }
        
        amount = Decimal("500")
        base_rate = Decimal("35.0")
        margin = Decimal("-5")
        final_rate = Decimal("33.25")
        exchange_rate_data = {
            'timestamp': '2023-12-01T15:30:00',
            'source': 'mock'
        }
        
        result = CalculationResult(
            pair_info, amount, base_rate, margin, final_rate, exchange_rate_data
        )
        
        formatted_result = MessageFormatter.format_calculation_result(result)
        
        # Check that result contains expected elements
        assert "USDT/THB" in formatted_result
        assert "🇹🇭" in formatted_result
        assert "35.00" in formatted_result  # Base rate
        assert "33.25" in formatted_result  # Final rate
        assert "-5%" in formatted_result    # Margin
        assert "📉" in formatted_result     # Negative change emoji
        assert "2023-12-01 15:30:00" in formatted_result  # Timestamp
        assert "mock" in formatted_result   # Source


class TestMarginCalculationIntegration:
    """Integration tests for margin calculation workflow"""
    
    @pytest.fixture
    def mock_exchange_rate(self):
        """Fixture providing mock exchange rate data"""
        return ExchangeRate(
            pair="USDT/RUB",
            rate=95.5,
            timestamp="2023-12-01T12:00:00",
            source="rapira",
            bid=95.3,
            ask=95.7,
            high_24h=96.0,
            low_24h=95.0,
            change_24h=1.5
        )
    
    def test_complete_calculation_workflow(self, mock_exchange_rate):
        """Test complete margin calculation workflow"""
        from handlers.calculation_logic import calculate_margin_rate
        
        # Setup test data
        pair_info = {
            'name': 'USDT/RUB',
            'base': 'USDT',
            'quote': 'RUB',
            'description': 'Tether к Российскому рублю',
            'emoji': '🇷🇺'
        }
        
        amount = Decimal("1000")
        margin = Decimal("5")
        exchange_rate_data = mock_exchange_rate.to_dict()
        
        # Perform calculation
        result = calculate_margin_rate(
            pair_info=pair_info,
            amount=amount,
            margin=margin,
            exchange_rate_data=exchange_rate_data
        )
        
        # Verify result
        assert result.amount == amount
        assert result.margin == margin
        assert result.base_rate == Decimal("95.5")
        assert result.final_rate == Decimal("100.275")  # 95.5 * 1.05
        assert result.rate_change == Decimal("4.775")   # 100.275 - 95.5
    
    def test_edge_case_very_small_rate(self):
        """Test calculation with very small exchange rate"""
        base_rate = Decimal("0.00000123")
        margin = Decimal("50")  # 50%
        
        final_rate = MarginCalculator.calculate_final_rate(base_rate, margin)
        expected = Decimal("0.00000185")  # 0.00000123 * 1.5, rounded to 8 decimals
        
        assert final_rate == expected
    
    def test_edge_case_very_large_rate(self):
        """Test calculation with very large exchange rate"""
        base_rate = Decimal("123456789.12345678")
        margin = Decimal("0.01")  # 0.01%
        
        final_rate = MarginCalculator.calculate_final_rate(base_rate, margin)
        # Actual calculation: 123456789.12345678 * 1.0001 = 123469134.80236913
        expected = Decimal("123469134.80236913")  # Calculated and rounded
        
        assert final_rate == expected
    
    def test_boundary_margin_values(self):
        """Test calculation with boundary margin values"""
        base_rate = Decimal("100")
        
        # Test -99.99% (almost -100%)
        margin = Decimal("-99.99")
        final_rate = MarginCalculator.calculate_final_rate(base_rate, margin)
        expected = Decimal("0.01")
        assert final_rate == expected
        
        # Test 999.99% (almost 1000%)
        margin = Decimal("999.99")
        final_rate = MarginCalculator.calculate_final_rate(base_rate, margin)
        expected = Decimal("1099.99")
        assert final_rate == expected


if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v'])