#!/usr/bin/env python3
"""
Модуль валидации входных данных для Crypto Helper Bot
Простая валидация для int/float значений
"""

from decimal import Decimal, InvalidOperation
from typing import Union


class ValidationError(Exception):
    """Исключение для ошибок валидации"""
    pass


class InputValidator:
    """Класс для валидации пользовательского ввода"""
    
    @staticmethod
    def validate_amount(amount_text: str) -> Decimal:
        """
        Упрощенная валидация суммы для расчета
        Принимает только чистые числовые значения
        
        Args:
            amount_text: Текст с суммой
            
        Returns:
            Decimal: Валидная сумма
            
        Raises:
            ValidationError: При некорректной сумме
        """
        try:
            # Простая обработка - только убираем пробелы
            clean_text = amount_text.strip()
            
            # Пытаемся преобразовать напрямую в Decimal
            amount = Decimal(clean_text)
            
            # Простые проверки диапазона
            if amount <= 0:
                raise ValidationError("Сумма должна быть больше нуля")
            
            if amount > Decimal('1000000000'):
                raise ValidationError("Сумма слишком большая")
            
            return amount
            
        except (InvalidOperation, ValueError):
            raise ValidationError(
                "Введите числовое значение (например: 1000 или 500.50)"
            )
    
    @staticmethod
    def validate_margin(margin_text: str) -> Decimal:
        """
        Упрощенная валидация процентной наценки
        Принимает только чистые числовые значения
        
        Args:
            margin_text: Текст с процентной наценкой
            
        Returns:
            Decimal: Валидная процентная наценка
            
        Raises:
            ValidationError: При некорректной наценке
        """
        try:
            # Простая обработка - убираем пробелы и знак %
            clean_text = margin_text.strip().replace('%', '')
            
            # Пытаемся преобразовать напрямую в Decimal
            margin = Decimal(clean_text)
            
            # Простые проверки диапазона
            if margin < -100:
                raise ValidationError("Наценка не может быть меньше -100%")
            
            if margin > 1000:
                raise ValidationError("Наценка не может быть больше 1000%")
            
            return margin
            
        except (InvalidOperation, ValueError):
            raise ValidationError(
                "Введите числовое значение (например: 5 или -1.2)"
            )


def validate_user_input(input_text: str, input_type: str) -> Union[Decimal, None]:
    """
    Универсальная функция валидации пользовательского ввода
    
    Args:
        input_text: Текст для валидации
        input_type: Тип данных ('amount' или 'margin')
        
    Returns:
        Decimal: Валидное значение или None при ошибке
        
    Raises:
        ValidationError: При некорректном вводе
    """
    if input_type == 'amount':
        return InputValidator.validate_amount(input_text)
    elif input_type == 'margin':
        return InputValidator.validate_margin(input_text)
    else:
        raise ValidationError(f"Неизвестный тип данных: {input_type}")