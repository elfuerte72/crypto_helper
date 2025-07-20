#!/usr/bin/env python3
"""
Validators для Crypto Helper Bot (Новая логика)
Валидация вводов для пошагового флоу обмена валют
"""

import re
from decimal import Decimal, InvalidOperation
from typing import Optional, Tuple

from .fsm_states import Currency, MIN_MARGIN, MAX_MARGIN, MIN_AMOUNT


class ValidationResult:
    """Результат валидации"""
    
    def __init__(self, is_valid: bool, value: Optional[Decimal] = None, error: Optional[str] = None):
        self.is_valid = is_valid
        self.value = value
        self.error = error


class ExchangeValidator:
    """Валидатор для данных процесса обмена валют"""
    
    @staticmethod
    def validate_margin_input(text: str) -> ValidationResult:
        """
        Валидация ввода наценки в процентах
        
        Поддерживаемые форматы:
        - 2 -> 2.0%
        - 1.5 -> 1.5%
        - 2,5 -> 2.5%
        - 2% -> 2.0%
        
        Args:
            text: Пользовательский ввод
            
        Returns:
            ValidationResult: Результат валидации
        """
        if not text or not text.strip():
            return ValidationResult(False, error="Введите значение наценки")
        
        # Очищаем ввод
        clean_text = text.strip().lower()
        
        # Убираем знак процента если есть
        clean_text = clean_text.replace('%', '').strip()
        
        # Заменяем запятую на точку для русской локали
        clean_text = clean_text.replace(',', '.')
        
        # Проверяем формат числа
        if not re.match(r'^\d+(\.\d+)?$', clean_text):
            return ValidationResult(
                False, 
                error="Введите число в формате: 2 или 1.5 или 2,5"
            )
        
        try:
            margin = Decimal(clean_text)
            
            # Проверяем диапазон
            if margin < MIN_MARGIN:
                return ValidationResult(
                    False,
                    error=f"Наценка должна быть не меньше {MIN_MARGIN}%"
                )
            
            if margin > MAX_MARGIN:
                return ValidationResult(
                    False,
                    error=f"Наценка должна быть не больше {MAX_MARGIN}%"
                )
            
            return ValidationResult(True, value=margin)
            
        except (InvalidOperation, ValueError):
            return ValidationResult(
                False,
                error="Введите корректное числовое значение"
            )
    
    @staticmethod
    def validate_amount_input(text: str, currency: Currency) -> ValidationResult:
        """
        Валидация ввода суммы сделки
        
        Поддерживаемые форматы:
        - 1000 -> 1000
        - 1 000 -> 1000
        - 1000.50 -> 1000.50
        - 1 000,50 -> 1000.50
        
        Args:
            text: Пользовательский ввод
            currency: Валюта для контекстной валидации
            
        Returns:
            ValidationResult: Результат валидации
        """
        if not text or not text.strip():
            return ValidationResult(False, error="Введите сумму")
        
        # Очищаем ввод
        clean_text = text.strip()
        
        # Убираем пробелы (тысячные разделители)
        clean_text = clean_text.replace(' ', '')
        
        # Заменяем запятую на точку для десятичной части
        clean_text = clean_text.replace(',', '.')
        
        # Проверяем формат числа
        if not re.match(r'^\d+(\.\d{1,2})?$', clean_text):
            return ValidationResult(
                False,
                error="Введите число в формате: 1000 или 1000.50"
            )
        
        try:
            amount = Decimal(clean_text)
            
            # Общие проверки
            if amount <= 0:
                return ValidationResult(
                    False,
                    error="Сумма должна быть больше нуля"
                )
            
            if amount < MIN_AMOUNT:
                return ValidationResult(
                    False,
                    error=f"Минимальная сумма: {MIN_AMOUNT} {currency.value}"
                )
            
            # Валидация максимумов по валютам
            max_limits = {
                Currency.RUB: Decimal('10000000'),  # 10 млн рублей
                Currency.USDT: Decimal('100000'),   # 100 тыс USDT
                Currency.USD: Decimal('100000'),    # 100 тыс USD
                Currency.EUR: Decimal('100000')     # 100 тыс EUR
            }
            
            max_amount = max_limits.get(currency, Decimal('1000000'))
            
            if amount > max_amount:
                return ValidationResult(
                    False,
                    error=f"Максимальная сумма: {max_amount:,.0f} {currency.value}".replace(',', ' ')
                )
            
            return ValidationResult(True, value=amount)
            
        except (InvalidOperation, ValueError):
            return ValidationResult(
                False,
                error="Введите корректное числовое значение"
            )
    
    @staticmethod
    def validate_callback_data(data: str, expected_prefix: str) -> ValidationResult:
        """
        Валидация callback данных от inline кнопок
        
        Args:
            data: Callback данные
            expected_prefix: Ожидаемый префикс
            
        Returns:
            ValidationResult: Результат валидации
        """
        if not data or not data.startswith(expected_prefix):
            return ValidationResult(
                False,
                error=f"Неверный формат callback данных"
            )
        
        value_part = data.replace(expected_prefix, '', 1)
        
        if not value_part:
            return ValidationResult(
                False,
                error="Отсутствует значение в callback данных"
            )
        
        return ValidationResult(True, value=value_part)
    
    @staticmethod
    def validate_currency_pair(source: Currency, target: Currency) -> ValidationResult:
        """
        Валидация валютной пары
        
        Args:
            source: Исходная валюта
            target: Целевая валюта
            
        Returns:
            ValidationResult: Результат валидации
        """
        from .fsm_states import is_valid_pair
        
        if source == target:
            return ValidationResult(
                False,
                error="Исходная и целевая валюты не могут быть одинаковыми"
            )
        
        if not is_valid_pair(source, target):
            return ValidationResult(
                False,
                error=f"Направление обмена {source.value} → {target.value} не поддерживается"
            )
        
        return ValidationResult(True)


class InputSanitizer:
    """Санитизация пользовательского ввода"""
    
    @staticmethod
    def sanitize_text_input(text: str, max_length: int = 100) -> str:
        """
        Базовая санитизация текстового ввода
        
        Args:
            text: Исходный текст
            max_length: Максимальная длина
            
        Returns:
            str: Очищенный текст
        """
        if not text:
            return ""
        
        # Обрезаем до максимальной длины
        sanitized = text[:max_length]
        
        # Убираем лишние пробелы
        sanitized = ' '.join(sanitized.split())
        
        # Базовая фильтрация опасных символов
        dangerous_chars = ['<', '>', '"', "'", '&', '\n', '\r', '\t']
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        
        return sanitized
    
    @staticmethod
    def extract_numeric_value(text: str) -> Optional[str]:
        """
        Извлечение числового значения из текста
        
        Args:
            text: Исходный текст
            
        Returns:
            Optional[str]: Числовое значение или None
        """
        if not text:
            return None
        
        # Ищем числовое значение в тексте
        numeric_pattern = r'(\d+(?:[.,]\d+)?)'
        match = re.search(numeric_pattern, text.replace(' ', ''))
        
        if match:
            return match.group(1).replace(',', '.')
        
        return None


# Утилитарные функции для быстрой валидации
def is_valid_margin(text: str) -> bool:
    """Быстрая проверка валидности наценки"""
    result = ExchangeValidator.validate_margin_input(text)
    return result.is_valid


def is_valid_amount(text: str, currency: Currency) -> bool:
    """Быстрая проверка валидности суммы"""
    result = ExchangeValidator.validate_amount_input(text, currency)
    return result.is_valid


def parse_margin(text: str) -> Optional[Decimal]:
    """Быстрое извлечение значения наценки"""
    result = ExchangeValidator.validate_margin_input(text)
    return result.value if result.is_valid else None


def parse_amount(text: str, currency: Currency) -> Optional[Decimal]:
    """Быстрое извлечение значения суммы"""
    result = ExchangeValidator.validate_amount_input(text, currency)
    return result.value if result.is_valid else None