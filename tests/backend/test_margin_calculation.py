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

from handlers.margin_calculation import (
    MarginCalculator,
    MarginCalculationError,
    format_calculation_result,
    create_margin_selection_keyboard,
    create_result_keyboard
)
from services.api_service import ExchangeRate


class TestMarginCalculator:
    """Test cases for MarginCalculator class"""
    
    def test_validate_margin_positive_integer(self):
        """Test validation of positive integer margin"""
        result = MarginCalculator.validate_margin("5")
        assert result == Decimal("5")
    
    def test_validate_margin_positive_float(self):
        """Test validation of positive float margin"""
        result = MarginCalculator.validate_margin("2.5")
        assert result == Decimal("2.5")
    
    def test_validate_margin_negative_integer(self):
        """Test validation of negative integer margin"""
        result = MarginCalculator.validate_margin("-3")
        assert result == Decimal("-3")
    
    def test_validate_margin_negative_float(self):
        """Test validation of negative float margin"""
        result = MarginCalculator.validate_margin("-1.5")
        assert result == Decimal("-1.5")
    
    def test_validate_margin_zero(self):
        """Test validation of zero margin"""
        result = MarginCalculator.validate_margin("0")
        assert result == Decimal("0")
    
    def test_validate_margin_with_percent_sign(self):
        """Test validation of margin with percent sign"""
        result = MarginCalculator.validate_margin("5%")
        assert result == Decimal("5")
    
    def test_validate_margin_with_spaces(self):
        """Test validation of margin with spaces"""
        result = MarginCalculator.validate_margin("  3.5  ")
        assert result == Decimal("3.5")
    
    def test_validate_margin_comma_as_decimal_separator(self):
        """Test validation of margin with comma as decimal separator"""
        result = MarginCalculator.validate_margin("2,5")
        assert result == Decimal("2.5")
    
    def test_validate_margin_too_low(self):
        """Test validation fails for margin below -100%"""
        with pytest.raises(MarginCalculationError) as exc_info:
            MarginCalculator.validate_margin("-150")
        
        assert "не может быть меньше -100%" in str(exc_info.value)
    
    def test_validate_margin_too_high(self):
        """Test validation fails for margin above 1000%"""
        with pytest.raises(MarginCalculationError) as exc_info:
            MarginCalculator.validate_margin("1500")
        
        assert "не может быть больше 1000%" in str(exc_info.value)
    
    def test_validate_margin_invalid_text(self):
        """Test validation fails for invalid text"""
        with pytest.raises(MarginCalculationError) as exc_info:
            MarginCalculator.validate_margin("abc")
        
        assert "Некорректный формат наценки" in str(exc_info.value)
    
    def test_validate_margin_empty_string(self):
        """Test validation fails for empty string"""
        with pytest.raises(MarginCalculationError):
            MarginCalculator.validate_margin("")
    
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


class TestKeyboardCreation:
    """Test cases for keyboard creation functions"""
    
    def test_create_margin_selection_keyboard(self):
        """Test creation of margin selection keyboard"""
        keyboard = create_margin_selection_keyboard()
        
        # Check that keyboard is created
        assert keyboard is not None
        assert hasattr(keyboard, 'inline_keyboard')
        assert len(keyboard.inline_keyboard) > 0
        
        # Check for header
        header_found = False
        for row in keyboard.inline_keyboard:
            for button in row:
                if "Быстрый выбор наценки" in button.text:
                    header_found = True
                    break
        
        assert header_found, "Header button should be present"
        
        # Check for margin buttons
        margin_buttons_found = 0
        for row in keyboard.inline_keyboard:
            for button in row:
                if button.callback_data and button.callback_data.startswith('margin_'):
                    margin_buttons_found += 1
        
        assert margin_buttons_found > 0, "Margin buttons should be present"
        
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
            'publish_result',
            'recalculate_margin',
            'copy_result',
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
            'name': 'RUB/ZAR',
            'base': 'RUB',
            'quote': 'ZAR',
            'description': 'Российский рубль → Южноафриканский рэнд',
            'emoji': '🇷🇺➡️🇿🇦'
        }
        
        base_rate = Decimal("5.5")
        margin = Decimal("10")
        final_rate = Decimal("6.05")
        rate_change = Decimal("0.55")
        exchange_rate_data = {
            'timestamp': '2023-12-01T12:00:00',
            'source': 'rapira'
        }
        
        result = format_calculation_result(
            pair_info, base_rate, margin, final_rate, rate_change, exchange_rate_data
        )
        
        # Check that result contains expected elements
        assert "Расчет курса завершен" in result
        assert "RUB/ZAR" in result
        assert "🇷🇺➡️🇿🇦" in result
        assert "5.5000" in result  # Base rate
        assert "6.0500" in result  # Final rate
        assert "+10%" in result    # Margin
        assert "📈" in result      # Positive change emoji
        assert "2023-12-01 12:00:00" in result  # Timestamp
        assert "rapira" in result  # Source
    
    def test_format_calculation_result_negative_margin(self):
        """Test formatting result with negative margin"""
        pair_info = {
            'name': 'USDT/THB',
            'base': 'USDT',
            'quote': 'THB',
            'description': 'Tether USD → Тайский бат',
            'emoji': '💰➡️🇹🇭'
        }
        
        base_rate = Decimal("35.0")
        margin = Decimal("-5")
        final_rate = Decimal("33.25")
        rate_change = Decimal("-1.75")
        exchange_rate_data = {
            'timestamp': '2023-12-01T15:30:00',
            'source': 'mock'
        }
        
        result = format_calculation_result(
            pair_info, base_rate, margin, final_rate, rate_change, exchange_rate_data
        )
        
        # Check that result contains expected elements
        assert "USDT/THB" in result
        assert "💰➡️🇹🇭" in result
        assert "35.0000" in result  # Base rate
        assert "33.2500" in result  # Final rate
        assert "-5%" in result      # Margin
        assert "📉" in result       # Negative change emoji
        assert "2023-12-01 15:30:00" in result  # Timestamp
        assert "mock" in result     # Source
    
    def test_format_calculation_result_zero_margin(self):
        """Test formatting result with zero margin"""
        pair_info = {
            'name': 'BTC/USDT',
            'base': 'BTC',
            'quote': 'USDT',
            'description': 'Bitcoin → Tether USD',
            'emoji': '₿➡️💰'
        }
        
        base_rate = Decimal("42000.12345678")
        margin = Decimal("0")
        final_rate = Decimal("42000.12345678")
        rate_change = Decimal("0")
        exchange_rate_data = {
            'timestamp': '2023-12-01T10:15:30',
            'source': 'rapira'
        }
        
        result = format_calculation_result(
            pair_info, base_rate, margin, final_rate, rate_change, exchange_rate_data
        )
        
        # Check that result contains expected elements
        assert "BTC/USDT" in result
        assert "42000.1235" in result      # Rate formatted to 4 decimals for USDT
        assert "+0%" in result             # Zero margin
        assert "+0.0000" in result         # Zero change formatted for USDT
        assert "2023-12-01 10:15:30" in result


class TestMarginCalculationIntegration:
    """Integration tests for margin calculation workflow"""
    
    @pytest.fixture
    def mock_exchange_rate(self):
        """Fixture providing mock exchange rate data"""
        return ExchangeRate(
            pair="RUB/ZAR",
            rate=5.5,
            timestamp="2023-12-01T12:00:00",
            source="rapira",
            bid=5.48,
            ask=5.52,
            high_24h=5.6,
            low_24h=5.4,
            change_24h=2.5
        )
    
    def test_complete_calculation_workflow(self, mock_exchange_rate):
        """Test complete margin calculation workflow"""
        # Step 1: Validate margin
        margin_text = "7.5"
        margin = MarginCalculator.validate_margin(margin_text)
        assert margin == Decimal("7.5")
        
        # Step 2: Calculate final rate
        base_rate = Decimal(str(mock_exchange_rate.rate))
        final_rate = MarginCalculator.calculate_final_rate(base_rate, margin)
        expected_final_rate = Decimal("5.9125")  # 5.5 * 1.075
        assert final_rate == expected_final_rate
        
        # Step 3: Calculate change
        rate_change = final_rate - base_rate
        expected_change = Decimal("0.4125")
        assert rate_change == expected_change
        
        # Step 4: Format result
        pair_info = {
            'name': 'RUB/ZAR',
            'base': 'RUB',
            'quote': 'ZAR',
            'description': 'Российский рубль → Южноафриканский рэнд',
            'emoji': '🇷🇺➡️🇿🇦'
        }
        
        result = format_calculation_result(
            pair_info=pair_info,
            base_rate=base_rate,
            margin=margin,
            final_rate=final_rate,
            rate_change=rate_change,
            exchange_rate_data=mock_exchange_rate.to_dict()
        )
        
        # Verify formatted result
        assert "5.5000" in result
        assert "5.9125" in result
        assert "+7.5%" in result
        assert "+0.4125" in result
    
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