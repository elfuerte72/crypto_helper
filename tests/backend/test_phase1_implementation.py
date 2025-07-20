#!/usr/bin/env python3
"""
Unit тесты для Фазы 1: Базовая архитектура FSM
Тестирование созданных модулей новой логики
"""

import pytest
from decimal import Decimal
from unittest.mock import Mock, AsyncMock

# Импорты тестируемых модулей
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from handlers.fsm_states import (
    ExchangeFlow, Currency, 
    get_available_targets, is_valid_pair,
    MIN_MARGIN, MAX_MARGIN, MIN_AMOUNT
)
from handlers.validators import (
    ExchangeValidator, ValidationResult,
    is_valid_margin, is_valid_amount,
    parse_margin, parse_amount
)
from handlers.keyboards import (
    create_source_currency_keyboard,
    create_target_currency_keyboard,
    create_margin_input_keyboard,
    create_amount_input_keyboard,
    create_result_keyboard
)
from handlers.formatters import MessageFormatter


class TestFSMStates:
    """Тестирование FSM состояний и энумов"""
    
    def test_currency_enum(self):
        """Тест enum валют"""
        assert Currency.RUB == "RUB"
        assert Currency.USDT == "USDT"
        assert Currency.USD == "USD"
        assert Currency.EUR == "EUR"
    
    def test_exchange_flow_states(self):
        """Тест FSM состояний"""
        # Проверяем, что все состояния определены
        assert hasattr(ExchangeFlow, 'WAITING_FOR_SOURCE_CURRENCY')
        assert hasattr(ExchangeFlow, 'WAITING_FOR_TARGET_CURRENCY')
        assert hasattr(ExchangeFlow, 'WAITING_FOR_MARGIN')
        assert hasattr(ExchangeFlow, 'WAITING_FOR_AMOUNT')
        assert hasattr(ExchangeFlow, 'SHOWING_RESULT')
    
    def test_get_available_targets(self):
        """Тест получения доступных целевых валют"""
        # Для RUB доступны USDT, USD, EUR
        rub_targets = get_available_targets(Currency.RUB)
        assert Currency.USDT in rub_targets
        assert Currency.USD in rub_targets
        assert Currency.EUR in rub_targets
        
        # Для USDT доступен только RUB
        usdt_targets = get_available_targets(Currency.USDT)
        assert Currency.RUB in usdt_targets
        assert len(usdt_targets) == 1
    
    def test_is_valid_pair(self):
        """Тест валидации валютных пар"""
        # Валидные пары
        assert is_valid_pair(Currency.RUB, Currency.USDT) == True
        assert is_valid_pair(Currency.RUB, Currency.USD) == True
        assert is_valid_pair(Currency.RUB, Currency.EUR) == True
        assert is_valid_pair(Currency.USDT, Currency.RUB) == True
        
        # Невалидные пары
        assert is_valid_pair(Currency.USDT, Currency.USD) == False
        assert is_valid_pair(Currency.USD, Currency.EUR) == False
        assert is_valid_pair(Currency.RUB, Currency.RUB) == False
    
    def test_constants(self):
        """Тест констант валидации"""
        assert MIN_MARGIN == 0.1
        assert MAX_MARGIN == 10.0
        assert MIN_AMOUNT == 1.0


class TestValidators:
    """Тестирование модуля валидации"""
    
    def test_validate_margin_input_valid(self):
        """Тест валидации корректной наценки"""
        # Целые числа
        result = ExchangeValidator.validate_margin_input("2")
        assert result.is_valid == True
        assert result.value == Decimal("2")
        
        # Десятичные числа
        result = ExchangeValidator.validate_margin_input("1.5")
        assert result.is_valid == True
        assert result.value == Decimal("1.5")
        
        # Русский формат (запятая)
        result = ExchangeValidator.validate_margin_input("2,5")
        assert result.is_valid == True
        assert result.value == Decimal("2.5")
        
        # С символом %
        result = ExchangeValidator.validate_margin_input("3%")
        assert result.is_valid == True
        assert result.value == Decimal("3")
    
    def test_validate_margin_input_invalid(self):
        """Тест валидации некорректной наценки"""
        # Пустая строка
        result = ExchangeValidator.validate_margin_input("")
        assert result.is_valid == False
        
        # Слишком малое значение
        result = ExchangeValidator.validate_margin_input("0.05")
        assert result.is_valid == False
        
        # Слишком большое значение
        result = ExchangeValidator.validate_margin_input("15")
        assert result.is_valid == False
        
        # Нечисловое значение
        result = ExchangeValidator.validate_margin_input("abc")
        assert result.is_valid == False
    
    def test_validate_amount_input_valid(self):
        """Тест валидации корректной суммы"""
        # Простое число
        result = ExchangeValidator.validate_amount_input("1000", Currency.RUB)
        assert result.is_valid == True
        assert result.value == Decimal("1000")
        
        # С пробелами (тысячные разделители)
        result = ExchangeValidator.validate_amount_input("1 000", Currency.RUB)
        assert result.is_valid == True
        assert result.value == Decimal("1000")
        
        # Десятичное число
        result = ExchangeValidator.validate_amount_input("1000.50", Currency.RUB)
        assert result.is_valid == True
        assert result.value == Decimal("1000.50")
        
        # Русский формат
        result = ExchangeValidator.validate_amount_input("1000,50", Currency.RUB)
        assert result.is_valid == True
        assert result.value == Decimal("1000.50")
    
    def test_validate_amount_input_invalid(self):
        """Тест валидации некорректной суммы"""
        # Пустая строка
        result = ExchangeValidator.validate_amount_input("", Currency.RUB)
        assert result.is_valid == False
        
        # Отрицательное число
        result = ExchangeValidator.validate_amount_input("-100", Currency.RUB)
        assert result.is_valid == False
        
        # Ноль
        result = ExchangeValidator.validate_amount_input("0", Currency.RUB)
        assert result.is_valid == False
        
        # Слишком малое значение
        result = ExchangeValidator.validate_amount_input("0.5", Currency.RUB)
        assert result.is_valid == False
    
    def test_validate_callback_data(self):
        """Тест валидации callback данных"""
        # Корректные данные
        result = ExchangeValidator.validate_callback_data("source_RUB", "source_")
        assert result.is_valid == True
        assert result.value == "RUB"
        
        # Некорректный префикс
        result = ExchangeValidator.validate_callback_data("target_USD", "source_")
        assert result.is_valid == False
        
        # Отсутствует значение
        result = ExchangeValidator.validate_callback_data("source_", "source_")
        assert result.is_valid == False
    
    def test_helper_functions(self):
        """Тест вспомогательных функций"""
        # is_valid_margin
        assert is_valid_margin("2.5") == True
        assert is_valid_margin("abc") == False
        
        # is_valid_amount
        assert is_valid_amount("1000", Currency.RUB) == True
        assert is_valid_amount("abc", Currency.RUB) == False
        
        # parse_margin
        assert parse_margin("2.5") == Decimal("2.5")
        assert parse_margin("abc") is None
        
        # parse_amount
        assert parse_amount("1000", Currency.RUB) == Decimal("1000")
        assert parse_amount("abc", Currency.RUB) is None


class TestKeyboards:
    """Тестирование модуля клавиатур"""
    
    def test_create_source_currency_keyboard(self):
        """Тест создания клавиатуры исходной валюты"""
        keyboard = create_source_currency_keyboard()
        assert keyboard is not None
        assert len(keyboard.inline_keyboard) > 0
        
        # Проверяем наличие кнопок RUB и USDT
        buttons_text = []
        for row in keyboard.inline_keyboard:
            for button in row:
                buttons_text.append(button.text)
        
        assert any("RUB" in text for text in buttons_text)
        assert any("USDT" in text for text in buttons_text)
        assert any("Отмена" in text for text in buttons_text)
    
    def test_create_target_currency_keyboard(self):
        """Тест создания клавиатуры целевой валюты"""
        # Для RUB
        keyboard = create_target_currency_keyboard(Currency.RUB)
        assert keyboard is not None
        
        buttons_text = []
        for row in keyboard.inline_keyboard:
            for button in row:
                buttons_text.append(button.text)
        
        assert any("USDT" in text for text in buttons_text)
        assert any("USD" in text for text in buttons_text)
        assert any("EUR" in text for text in buttons_text)
        assert any("Назад" in text for text in buttons_text)
        
        # Для USDT
        keyboard = create_target_currency_keyboard(Currency.USDT)
        assert keyboard is not None
        
        buttons_text = []
        for row in keyboard.inline_keyboard:
            for button in row:
                buttons_text.append(button.text)
        
        assert any("RUB" in text for text in buttons_text)
    
    def test_create_margin_input_keyboard(self):
        """Тест создания клавиатуры ввода наценки"""
        keyboard = create_margin_input_keyboard()
        assert keyboard is not None
        assert len(keyboard.inline_keyboard) > 0
        
        # Проверяем наличие предустановленных значений
        buttons_data = []
        for row in keyboard.inline_keyboard:
            for button in row:
                buttons_data.append(button.callback_data)
        
        assert any("margin_" in data for data in buttons_data)
    
    def test_create_amount_input_keyboard(self):
        """Тест создания клавиатуры ввода суммы"""
        keyboard = create_amount_input_keyboard()
        assert keyboard is not None
        assert len(keyboard.inline_keyboard) > 0
        
        # Проверяем наличие предустановленных значений
        buttons_data = []
        for row in keyboard.inline_keyboard:
            for button in row:
                buttons_data.append(button.callback_data)
        
        assert any("amount_" in data for data in buttons_data)
    
    def test_create_result_keyboard(self):
        """Тест создания клавиатуры результата"""
        keyboard = create_result_keyboard()
        assert keyboard is not None
        assert len(keyboard.inline_keyboard) > 0
        
        buttons_text = []
        for row in keyboard.inline_keyboard:
            for button in row:
                buttons_text.append(button.text)
        
        assert any("Новая сделка" in text for text in buttons_text)
        assert any("Главное меню" in text for text in buttons_text)


class TestFormatters:
    """Тестирование модуля форматеров"""
    
    def test_format_welcome_message(self):
        """Тест форматирования приветственного сообщения"""
        message = MessageFormatter.format_welcome_message()
        assert "Калькулятор обмена валют" in message
        assert "отдает клиент" in message
    
    def test_format_source_selected_message(self):
        """Тест форматирования сообщения после выбора исходной валюты"""
        message = MessageFormatter.format_source_selected_message(Currency.RUB)
        assert "рубли" in message
        assert "получает" in message
        
        message = MessageFormatter.format_source_selected_message(Currency.USDT)
        assert "USDT" in message
    
    def test_format_target_selected_message(self):
        """Тест форматирования сообщения после выбора целевой валюты"""
        message = MessageFormatter.format_target_selected_message(
            Currency.RUB, Currency.USDT, Decimal("80.00")
        )
        assert "RUB → USDT" in message
        assert "80" in message
        assert "наценку" in message
    
    def test_format_final_result(self):
        """Тест форматирования финального результата"""
        message = MessageFormatter.format_final_result(
            Currency.RUB, Currency.USDT,
            Decimal("1000"), Decimal("2"), Decimal("81.60"), Decimal("12.25")
        )
        assert "Сделка рассчитана" in message
        assert "RUB → USDT" in message
        assert "1 000 RUB" in message
        assert "12.25 USDT" in message
        assert "2%" in message
    
    def test_format_error_messages(self):
        """Тест форматирования сообщений об ошибках"""
        # Ошибка валидации наценки
        message = MessageFormatter.format_margin_validation_error()
        assert "Неверная наценка" in message
        assert "0.1 до 10" in message
        
        # Ошибка валидации суммы
        message = MessageFormatter.format_amount_validation_error()
        assert "Неверная сумма" in message
        assert "положительное число" in message
        
        # Общая ошибка
        message = MessageFormatter.format_error_message("Тестовая ошибка")
        assert "Ошибка:" in message
        assert "Тестовая ошибка" in message
        
        # Отмена операции
        message = MessageFormatter.format_cancel_message("Тест")
        assert "Тест отменена" in message
        assert "/admin_bot" in message


class TestValidationResult:
    """Тестирование класса ValidationResult"""
    
    def test_valid_result(self):
        """Тест успешного результата валидации"""
        result = ValidationResult(True, Decimal("2.5"))
        assert result.is_valid == True
        assert result.value == Decimal("2.5")
        assert result.error is None
    
    def test_invalid_result(self):
        """Тест неуспешного результата валидации"""
        result = ValidationResult(False, error="Тестовая ошибка")
        assert result.is_valid == False
        assert result.value is None
        assert result.error == "Тестовая ошибка"


if __name__ == '__main__':
    # Запуск тестов
    pytest.main([__file__, '-v'])