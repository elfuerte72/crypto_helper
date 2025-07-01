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
        Валидация суммы для расчета
        Принимает только числовые значения (int или float)
        
        Args:
            amount_text: Текст с суммой
            
        Returns:
            Decimal: Валидная сумма
            
        Raises:
            ValidationError: При некорректной сумме
        """
        try:
            # Удаляем только пробелы и заменяем запятую на точку
            clean_text = amount_text.strip().replace(',', '.')
            
            # Проверяем, что строка содержит только цифры, точку и знак минуса
            if not clean_text.replace('.', '').replace('-', '').isdigit():
                raise ValidationError(
                    "Используйте только числа, например: 1000, 500.50, 1250"
                )
            
            # Проверяем, что есть хотя бы одна цифра
            if not any(char.isdigit() for char in clean_text):
                raise ValidationError(
                    "Введите числовое значение, например: 1000, 500.50, 1250"
                )
            
            # Проверяем количество точек (не больше одной)
            if clean_text.count('.') > 1:
                raise ValidationError(
                    "Неверный формат числа. Используйте только одну точку для десятичной дроби"
                )
            
            # Преобразуем в Decimal для точных вычислений
            amount = Decimal(clean_text)
            
            # Проверяем диапазон (от 0.01 до 1,000,000,000)
            if amount <= 0:
                raise ValidationError("Сумма должна быть больше нуля")
            
            if amount > Decimal('1000000000'):
                raise ValidationError("Сумма слишком большая (максимум: 1,000,000,000)")
            
            if amount < Decimal('0.01'):
                raise ValidationError("Минимальная сумма: 0.01")
            
            return amount
            
        except (InvalidOperation, ValueError):
            raise ValidationError(
                "Некорректный формат суммы. Используйте только числовые значения, например: 1000, 500.50, 1250"
            )
    
    @staticmethod
    def validate_margin(margin_text: str) -> Decimal:
        """
        Валидация процентной наценки
        Принимает только числовые значения (int или float)
        
        Args:
            margin_text: Текст с процентной наценкой
            
        Returns:
            Decimal: Валидная процентная наценка
            
        Raises:
            ValidationError: При некорректной наценке
        """
        try:
            # Удаляем пробелы и знак процента, заменяем запятую на точку
            clean_text = margin_text.strip().replace('%', '').replace(',', '.')
            
            # Проверяем, что строка содержит только цифры, точку и знаки
            if not clean_text.replace('.', '').replace('-', '').replace('+', '').isdigit():
                raise ValidationError(
                    "Используйте только числа, например: 5, 2.5, -1.2"
                )
            
            # Проверяем, что есть хотя бы одна цифра
            if not any(char.isdigit() for char in clean_text):
                raise ValidationError(
                    "Введите числовое значение, например: 5, 2.5, -1.2"
                )
            
            # Проверяем количество точек (не больше одной)
            if clean_text.count('.') > 1:
                raise ValidationError(
                    "Неверный формат числа. Используйте только одну точку для десятичной дроби"
                )
            
            # Проверяем знаки + и - (только в начале)
            if '+' in clean_text[1:] or '-' in clean_text[1:]:
                raise ValidationError(
                    "Знак '+' или '-' может быть только в начале числа"
                )
            
            # Преобразуем в Decimal для точных вычислений
            margin = Decimal(clean_text)
            
            # Проверяем диапазон (от -100% до +1000%)
            if margin < -100:
                raise ValidationError(
                    "Наценка не может быть меньше -100% (это означало бы отрицательную цену)"
                )
            
            if margin > 1000:
                raise ValidationError(
                    "Наценка не может быть больше 1000% (слишком высокая наценка)"
                )
            
            return margin
            
        except (InvalidOperation, ValueError):
            raise ValidationError(
                "Некорректный формат наценки. Используйте только числовые значения, например: 5, 2.5, -1.2"
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