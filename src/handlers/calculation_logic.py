#!/usr/bin/env python3
"""
Модуль логики расчета курса с наценкой для Crypto Helper Bot
Содержит функции для расчета курса и форматирования валютных значений
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, Tuple


class MarginCalculator:
    """Класс для расчета курса с наценкой"""
    
    @staticmethod
    def calculate_final_rate(base_rate: Decimal, margin_percent: Decimal) -> Decimal:
        """
        Расчет итогового курса с наценкой
        
        Args:
            base_rate: Базовый курс
            margin_percent: Процентная наценка
            
        Returns:
            Decimal: Итоговый курс с наценкой
        """
        # Формула: итоговый_курс = базовый_курс * (1 + наценка/100)
        margin_multiplier = Decimal('1') + (margin_percent / Decimal('100'))
        final_rate = base_rate * margin_multiplier
        
        # Округляем до 8 знаков после запятой (стандарт для криптовалют)
        return final_rate.quantize(Decimal('0.00000001'), rounding=ROUND_HALF_UP)
    
    @staticmethod
    def calculate_exchange_amounts(
        amount: Decimal, 
        base_rate: Decimal, 
        final_rate: Decimal
    ) -> Tuple[Decimal, Decimal, Decimal]:
        """
        Расчет сумм обмена
        
        Args:
            amount: Сумма для обмена
            base_rate: Базовый курс
            final_rate: Итоговый курс с наценкой
            
        Returns:
            Tuple[Decimal, Decimal, Decimal]: (сумма_по_базовому_курсу, сумма_по_итоговому_курсу, разница)
        """
        amount_base_rate = amount * base_rate
        amount_final_rate = amount * final_rate
        amount_difference = amount_final_rate - amount_base_rate
        
        return amount_base_rate, amount_final_rate, amount_difference
    
    @staticmethod
    def format_currency_value(value: Decimal, currency: str) -> str:
        """
        Форматирование значения валюты для отображения
        
        Args:
            value: Значение для форматирования
            currency: Код валюты
            
        Returns:
            str: Отформатированное значение
        """
        # Определяем количество знаков после запятой в зависимости от валюты
        if currency in ['BTC', 'ETH']:
            # Для основных криптовалют - больше знаков
            return f"{value:.8f}"
        elif currency in ['USDT', 'USDC', 'DAI']:
            # Для стейблкоинов - меньше знаков
            return f"{value:.4f}"
        elif currency in ['RUB', 'USD', 'EUR']:
            # Для фиатных валют - 2 знака
            return f"{value:.2f}"
        else:
            # Для остальных - автоматическое определение
            if value >= 1:
                return f"{value:.4f}"
            else:
                return f"{value:.8f}"
    
    @staticmethod
    def format_amount_display(amount: Decimal, currency: str) -> str:
        """
        Форматирование суммы для отображения
        
        Args:
            amount: Сумма для форматирования
            currency: Код валюты
            
        Returns:
            str: Отформатированная сумма
        """
        # Определяем количество знаков после запятой в зависимости от валюты
        if currency in ['BTC', 'ETH']:
            # Для основных криптовалют - больше знаков
            return f"{amount:.8f}"
        elif currency in ['USDT', 'USDC', 'DAI']:
            # Для стейблкоинов - меньше знаков
            return f"{amount:.4f}"
        elif currency in ['RUB', 'USD', 'EUR']:
            # Для фиатных валют - 2 знака
            return f"{amount:.2f}"
        else:
            # Для остальных - автоматическое определение
            if amount >= 1:
                return f"{amount:.4f}"
            else:
                return f"{amount:.8f}"


class CalculationResult:
    """Класс для хранения результата расчета"""
    
    def __init__(
        self,
        pair_info: Dict[str, Any],
        amount: Decimal,
        base_rate: Decimal,
        margin: Decimal,
        final_rate: Decimal,
        exchange_rate_data: Dict[str, Any]
    ):
        self.pair_info = pair_info
        self.amount = amount
        self.base_rate = base_rate
        self.margin = margin
        self.final_rate = final_rate
        self.exchange_rate_data = exchange_rate_data
        
        # Рассчитываем дополнительные значения
        self.rate_change = final_rate - base_rate
        self.amount_base_rate, self.amount_final_rate, self.amount_difference = \
            MarginCalculator.calculate_exchange_amounts(amount, base_rate, final_rate)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Преобразование результата в словарь
        
        Returns:
            Dict[str, Any]: Результат в виде словаря
        """
        return {
            'pair_info': self.pair_info,
            'amount': float(self.amount),
            'base_rate': float(self.base_rate),
            'margin': float(self.margin),
            'final_rate': float(self.final_rate),
            'rate_change': float(self.rate_change),
            'amount_base_rate': float(self.amount_base_rate),
            'amount_final_rate': float(self.amount_final_rate),
            'amount_difference': float(self.amount_difference),
            'exchange_rate_data': self.exchange_rate_data
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CalculationResult':
        """
        Создание результата из словаря
        
        Args:
            data: Данные в виде словаря
            
        Returns:
            CalculationResult: Экземпляр результата
        """
        return cls(
            pair_info=data['pair_info'],
            amount=Decimal(str(data['amount'])),
            base_rate=Decimal(str(data['base_rate'])),
            margin=Decimal(str(data['margin'])),
            final_rate=Decimal(str(data['final_rate'])),
            exchange_rate_data=data['exchange_rate_data']
        )


def calculate_margin_rate(
    pair_info: Dict[str, Any],
    amount: Decimal,
    margin: Decimal,
    exchange_rate_data: Dict[str, Any]
) -> CalculationResult:
    """
    Основная функция расчета курса с наценкой
    
    Args:
        pair_info: Информация о валютной паре
        amount: Сумма для расчета
        margin: Процентная наценка
        exchange_rate_data: Данные о курсе
        
    Returns:
        CalculationResult: Результат расчета
    """
    base_rate = Decimal(str(exchange_rate_data['rate']))
    final_rate = MarginCalculator.calculate_final_rate(base_rate, margin)
    
    return CalculationResult(
        pair_info=pair_info,
        amount=amount,
        base_rate=base_rate,
        margin=margin,
        final_rate=final_rate,
        exchange_rate_data=exchange_rate_data
    )