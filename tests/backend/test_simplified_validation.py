#!/usr/bin/env python3
"""
Тесты для упрощенной валидации входных данных
Задача 12: Упрощение FSM и пользовательского потока
"""

import pytest
from decimal import Decimal

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from handlers.validation import InputValidator, ValidationError


class TestSimplifiedValidation:
    """Тесты упрощенной валидации"""
    
    def test_validate_amount_simple_integer(self):
        """Тест валидации простого целого числа"""
        result = InputValidator.validate_amount("1000")
        assert result == Decimal("1000")
    
    def test_validate_amount_simple_float(self):
        """Тест валидации простого десятичного числа"""
        result = InputValidator.validate_amount("500.50")
        assert result == Decimal("500.50")
    
    def test_validate_amount_with_spaces(self):
        """Тест валидации числа с пробелами"""
        result = InputValidator.validate_amount("  1000  ")
        assert result == Decimal("1000")
    
    def test_validate_amount_zero(self):
        """Тест валидации нуля - должен вызвать ошибку"""
        with pytest.raises(ValidationError) as exc_info:
            InputValidator.validate_amount("0")
        assert "больше нуля" in str(exc_info.value)
    
    def test_validate_amount_negative(self):
        """Тест валидации отрицательного числа - должен вызвать ошибку"""
        with pytest.raises(ValidationError) as exc_info:
            InputValidator.validate_amount("-100")
        assert "больше нуля" in str(exc_info.value)
    
    def test_validate_amount_too_large(self):
        """Тест валидации слишком большого числа"""
        with pytest.raises(ValidationError) as exc_info:
            InputValidator.validate_amount("2000000000")
        assert "слишком большая" in str(exc_info.value)
    
    def test_validate_amount_invalid_text(self):
        """Тест валидации некорректного текста"""
        with pytest.raises(ValidationError) as exc_info:
            InputValidator.validate_amount("abc")
        assert "числовое значение" in str(exc_info.value)
    
    def test_validate_amount_empty_string(self):
        """Тест валидации пустой строки"""
        with pytest.raises(ValidationError) as exc_info:
            InputValidator.validate_amount("")
        assert "числовое значение" in str(exc_info.value)
    
    def test_validate_margin_simple_positive(self):
        """Тест валидации положительной наценки"""
        result = InputValidator.validate_margin("5")
        assert result == Decimal("5")
    
    def test_validate_margin_simple_negative(self):
        """Тест валидации отрицательной наценки"""
        result = InputValidator.validate_margin("-1.2")
        assert result == Decimal("-1.2")
    
    def test_validate_margin_with_percent_sign(self):
        """Тест валидации наценки со знаком процента"""
        result = InputValidator.validate_margin("5%")
        assert result == Decimal("5")
    
    def test_validate_margin_with_spaces(self):
        """Тест валидации наценки с пробелами"""
        result = InputValidator.validate_margin("  2.5  ")
        assert result == Decimal("2.5")
    
    def test_validate_margin_zero(self):
        """Тест валидации нулевой наценки"""
        result = InputValidator.validate_margin("0")
        assert result == Decimal("0")
    
    def test_validate_margin_too_low(self):
        """Тест валидации слишком низкой наценки"""
        with pytest.raises(ValidationError) as exc_info:
            InputValidator.validate_margin("-150")
        assert "меньше -100%" in str(exc_info.value)
    
    def test_validate_margin_too_high(self):
        """Тест валидации слишком высокой наценки"""
        with pytest.raises(ValidationError) as exc_info:
            InputValidator.validate_margin("1500")
        assert "больше 1000%" in str(exc_info.value)
    
    def test_validate_margin_invalid_text(self):
        """Тест валидации некорректного текста для наценки"""
        with pytest.raises(ValidationError) as exc_info:
            InputValidator.validate_margin("abc")
        assert "числовое значение" in str(exc_info.value)
    
    def test_validate_margin_empty_string(self):
        """Тест валидации пустой строки для наценки"""
        with pytest.raises(ValidationError) as exc_info:
            InputValidator.validate_margin("")
        assert "числовое значение" in str(exc_info.value)