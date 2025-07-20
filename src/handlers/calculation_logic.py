#!/usr/bin/env python3
"""
Модуль логики расчета курса с наценкой для Crypto Helper Bot
Содержит функции для расчета курса в банковском стиле (покупка/продажа)
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, Tuple, Optional
from dataclasses import dataclass


@dataclass
class BankingRates:
    """Курсы покупки и продажи в банковском стиле"""
    base_rate: Decimal
    buy_rate: Decimal  # Курс покупки (банк покупает у клиента)
    sell_rate: Decimal  # Курс продажи (банк продает клиенту)
    margin_percent: Decimal
    spread_percent: Decimal = Decimal('0.5')  # Спрэд по умолчанию 0.5%
    
    def get_client_buy_rate(self) -> Decimal:
        """Курс, по которому клиент может купить валюту у банка"""
        return self.sell_rate
    
    def get_client_sell_rate(self) -> Decimal:
        """Курс, по которому клиент может продать валюту банку"""
        return self.buy_rate


class MarginCalculator:
    """Класс для расчета курса в банковском стиле с покупкой/продажей"""
    
    @staticmethod
    def detect_pair_type(pair_info: Dict[str, Any]) -> str:
        """
        Определение типа валютной пары для правильного расчета наценки
        
        Args:
            pair_info: Информация о валютной паре
            
        Returns:
            str: Тип пары - 'rub_base' (RUB/X) или 'rub_quote' (X/RUB)
        """
        base_currency = pair_info['base']
        quote_currency = pair_info['quote']
        
        if base_currency == 'RUB':
            return 'rub_base'  # RUB/X
        elif quote_currency == 'RUB':
            return 'rub_quote'  # X/RUB
        else:
            # Для других пар используем стандартную логику
            return 'standard'
    
    @staticmethod
    def calculate_rub_base_margin(
        base_rate: Decimal, margin_percent: Decimal
    ) -> Decimal:
        """
        Расчет курса для пар RUB/X (рубль - базовая валюта)
        Применяется ПЛЮС процент: курс = базовый_курс * (1 + наценка/100)
        
        Args:
            base_rate: Базовый курс
            margin_percent: Процентная наценка
            
        Returns:
            Decimal: Итоговый курс с наценкой
        """
        # Формула: итоговый_курс = базовый_курс * (1 + наценка/100)
        margin_multiplier = Decimal('1') + (margin_percent / Decimal('100'))
        final_rate = base_rate * margin_multiplier
        
        # Округляем до 8 знаков после запятой
        return final_rate.quantize(
            Decimal('0.00000001'), rounding=ROUND_HALF_UP
        )
    
    @staticmethod
    def calculate_rub_quote_margin(
        base_rate: Decimal, margin_percent: Decimal
    ) -> Decimal:
        """
        Расчет курса для пар X/RUB (рубль - котируемая валюта)
        Применяется МИНУС процент: курс = базовый_курс * (1 - наценка/100)
        
        Args:
            base_rate: Базовый курс
            margin_percent: Процентная наценка
            
        Returns:
            Decimal: Итоговый курс с наценкой
        """
        # Формула: итоговый_курс = базовый_курс * (1 - наценка/100)
        # Для пар X/RUB наценка вычитается из базового курса
        margin_multiplier = Decimal('1') - (margin_percent / Decimal('100'))
        final_rate = base_rate * margin_multiplier
        
        # Округляем до 8 знаков после запятой
        return final_rate.quantize(
            Decimal('0.00000001'), rounding=ROUND_HALF_UP
        )
    
    @staticmethod
    def calculate_banking_rates(
        base_rate: Decimal, 
        margin_percent: Decimal, 
        pair_info: Optional[Dict[str, Any]] = None,
        spread_percent: Decimal = Decimal('0.5')
    ) -> BankingRates:
        """
        Расчет курсов покупки и продажи в банковском стиле с учетом типа пары
        
        Args:
            base_rate: Базовый рыночный курс
            margin_percent: Процентная наценка банка
            pair_info: Информация о валютной паре для определения типа
            spread_percent: Спрэд между покупкой и продажей (по умолчанию 0.5%)
            
        Returns:
            BankingRates: Курсы покупки и продажи
        """
        half_spread = spread_percent / Decimal('2')
        
        # Применяем наценку к базовому курсу с учетом типа пары
        if pair_info:
            adjusted_rate = MarginCalculator.calculate_final_rate(
                base_rate, margin_percent, pair_info
            )
        else:
            # Стандартная логика для обратной совместимости
            margin_multiplier = Decimal('1') + (
                margin_percent / Decimal('100')
            )
            adjusted_rate = base_rate * margin_multiplier
        
        # Рассчитываем курсы покупки и продажи с учетом спрэда
        buy_rate = adjusted_rate * (
            Decimal('1') - half_spread / Decimal('100')
        )
        sell_rate = adjusted_rate * (
            Decimal('1') + half_spread / Decimal('100')
        )
        
        # Округляем до 8 знаков после запятой
        buy_rate = buy_rate.quantize(
            Decimal('0.00000001'), rounding=ROUND_HALF_UP
        )
        sell_rate = sell_rate.quantize(
            Decimal('0.00000001'), rounding=ROUND_HALF_UP
        )
        
        return BankingRates(
            base_rate=base_rate,
            buy_rate=buy_rate,
            sell_rate=sell_rate,
            margin_percent=margin_percent,
            spread_percent=spread_percent
        )
    
    @staticmethod
    def calculate_final_rate(
        base_rate: Decimal,
        margin_percent: Decimal,
        pair_info: Optional[Dict[str, Any]] = None
    ) -> Decimal:
        """
        Расчет итогового курса с наценкой с автоматическим выбором логики
        
        Args:
            base_rate: Базовый курс
            margin_percent: Процентная наценка
            pair_info: Информация о валютной паре (опционально)
            
        Returns:
            Decimal: Итоговый курс с наценкой
        """
        # Если информация о паре предоставлена, используем специальную логику
        if pair_info:
            pair_type = MarginCalculator.detect_pair_type(pair_info)
            
            if pair_type == 'rub_base':
                # RUB/X - ПЛЮС наценка
                return MarginCalculator.calculate_rub_base_margin(
                    base_rate, margin_percent
                )
            elif pair_type == 'rub_quote':
                # X/RUB - МИНУС наценка
                return MarginCalculator.calculate_rub_quote_margin(
                    base_rate, margin_percent
                )
        
        # Стандартная логика для обратной совместимости
        # Формула: итоговый_курс = базовый_курс * (1 + наценка/100)
        margin_multiplier = Decimal('1') + (margin_percent / Decimal('100'))
        final_rate = base_rate * margin_multiplier
        
        # Округляем до 8 знаков после запятой (стандарт для криптовалют)
        return final_rate.quantize(
            Decimal('0.00000001'), rounding=ROUND_HALF_UP
        )
    
    @staticmethod
    def get_effective_margin_for_display(
        margin_percent: Decimal, pair_info: Dict[str, Any]
    ) -> Decimal:
        """
        Получение эффективной наценки для отображения пользователю
        Показывает реальное влияние на курс с точки зрения пользователя
        
        Args:
            margin_percent: Введенная пользователем наценка
            pair_info: Информация о валютной паре
            
        Returns:
            Decimal: Эффективная наценка для отображения
        """
        # После исправления логики все наценки отображаются как есть
        # независимо от типа валютной пары
        return margin_percent
    
    @staticmethod
    def calculate_banking_exchange_amounts(
        amount: Decimal, 
        banking_rates: BankingRates,
        operation_type: str = 'sell'  # 'buy' или 'sell' с точки зрения клиента
    ) -> Tuple[Decimal, Decimal, Decimal, Decimal]:
        """
        Расчет сумм обмена в банковском стиле
        
        Args:
            amount: Сумма для обмена
            banking_rates: Курсы покупки и продажи
            operation_type: Тип операции - 'buy' (клиент покупает) или
                          'sell' (клиент продает)
            
        Returns:
            Tuple[Decimal, Decimal, Decimal, Decimal]: (
                сумма_по_базовому_курсу, сумма_по_курсу_покупки,
                сумма_по_курсу_продажи, прибыль_банка
            )
        """
        amount_base_rate = amount * banking_rates.base_rate
        amount_buy_rate = amount * banking_rates.buy_rate
        amount_sell_rate = amount * banking_rates.sell_rate
        
        # Прибыль банка - разница между курсами продажи и покупки
        bank_profit = amount * (
            banking_rates.sell_rate - banking_rates.buy_rate
        )
        
        return amount_base_rate, amount_buy_rate, amount_sell_rate, bank_profit
    
    @staticmethod
    def calculate_exchange_amounts(
        amount: Decimal, 
        base_rate: Decimal, 
        final_rate: Decimal
    ) -> Tuple[Decimal, Decimal, Decimal]:
        """
        Расчет сумм обмена (старый метод для совместимости)
        
        Args:
            amount: Сумма для обмена
            base_rate: Базовый курс
            final_rate: Итоговый курс с наценкой
            
        Returns:
            Tuple[Decimal, Decimal, Decimal]: (
                сумма_по_базовому_курсу, сумма_по_итоговому_курсу, разница
            )
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
    """Класс для хранения результата расчета с банковской логикой"""
    
    def __init__(
        self,
        pair_info: Dict[str, Any],
        amount: Decimal,
        base_rate: Decimal,
        margin: Decimal,
        final_rate: Decimal,
        exchange_rate_data: Dict[str, Any],
        banking_rates: Optional[BankingRates] = None
    ):
        self.pair_info = pair_info
        self.amount = amount
        self.base_rate = base_rate
        self.margin = margin
        self.margin_percent = margin  # Дублируем для совместимости
        self.final_rate = final_rate
        self.exchange_rate_data = exchange_rate_data
        self.banking_rates = banking_rates
        
        # Получаем информацию о валютах
        self.base_currency = pair_info['base']
        self.quote_currency = pair_info['quote']
        
        # Рассчитываем дополнительные значения
        self.rate_change = final_rate - base_rate
        
        # Если есть банковские курсы, используем их
        if banking_rates:
            (
                self.amount_base_rate, self.amount_buy_rate,
                self.amount_sell_rate, self.bank_profit
            ) = MarginCalculator.calculate_banking_exchange_amounts(
                amount, banking_rates
            )
            
            # Для совместимости с существующим кодом
            # Курс продажи как итоговый
            self.amount_final_rate = self.amount_sell_rate
            self.amount_difference = (
                self.amount_sell_rate - self.amount_base_rate
            )
        else:
            # Старая логика для совместимости
            (
                self.amount_base_rate, self.amount_final_rate,
                self.amount_difference
            ) = MarginCalculator.calculate_exchange_amounts(
                amount, base_rate, final_rate
            )
            self.amount_buy_rate = self.amount_final_rate
            self.amount_sell_rate = self.amount_final_rate
            self.bank_profit = self.amount_difference
        
        # Дополнительные атрибуты для удобства
        self.final_amount = self.amount_final_rate
        self.profit = self.amount_difference
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Преобразование результата в словарь
        
        Returns:
            Dict[str, Any]: Результат в виде словаря
        """
        result = {
            'pair_info': self.pair_info,
            'amount': float(self.amount),
            'base_rate': float(self.base_rate),
            'margin': float(self.margin),
            'margin_percent': float(self.margin_percent),
            'final_rate': float(self.final_rate),
            'rate_change': float(self.rate_change),
            'amount_base_rate': float(self.amount_base_rate),
            'amount_final_rate': float(self.amount_final_rate),
            'amount_difference': float(self.amount_difference),
            'final_amount': float(self.final_amount),
            'profit': float(self.profit),
            'base_currency': self.base_currency,
            'quote_currency': self.quote_currency,
            'exchange_rate_data': self.exchange_rate_data
        }
        
        # Добавляем банковские данные если есть
        if self.banking_rates:
            result.update({
                'buy_rate': float(self.banking_rates.buy_rate),
                'sell_rate': float(self.banking_rates.sell_rate),
                'spread_percent': float(self.banking_rates.spread_percent),
                'amount_buy_rate': float(self.amount_buy_rate),
                'amount_sell_rate': float(self.amount_sell_rate),
                'bank_profit': float(self.bank_profit)
            })
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CalculationResult':
        """
        Создание результата из словаря
        
        Args:
            data: Данные в виде словаря
            
        Returns:
            CalculationResult: Экземпляр результата
        """
        banking_rates = None
        if 'buy_rate' in data and 'sell_rate' in data:
            banking_rates = BankingRates(
                base_rate=Decimal(str(data['base_rate'])),
                buy_rate=Decimal(str(data['buy_rate'])),
                sell_rate=Decimal(str(data['sell_rate'])),
                margin_percent=Decimal(str(data['margin'])),
                spread_percent=Decimal(str(data.get('spread_percent', '0.5')))
            )
        
        return cls(
            pair_info=data['pair_info'],
            amount=Decimal(str(data['amount'])),
            base_rate=Decimal(str(data['base_rate'])),
            margin=Decimal(str(data['margin'])),
            final_rate=Decimal(str(data['final_rate'])),
            exchange_rate_data=data['exchange_rate_data'],
            banking_rates=banking_rates
        )


def calculate_banking_rate(
    pair_info: Dict[str, Any],
    amount: Decimal,
    margin: Decimal,
    exchange_rate_data: Dict[str, Any],
    spread_percent: Decimal = Decimal('0')
) -> CalculationResult:
    """
    Расчет курса в банковском стиле с курсами покупки и продажи
    С учетом специальной логики для пар с рублем
    
    Args:
        pair_info: Информация о валютной паре
        amount: Сумма для расчета
        margin: Процентная наценка
        exchange_rate_data: Данные о курсе
        spread_percent: Спрэд между курсами покупки и продажи
        
    Returns:
        CalculationResult: Результат расчета
    """
    base_rate = Decimal(str(exchange_rate_data['rate']))
    
    # Определяем тип пары для правильного расчета наценки
    pair_type = MarginCalculator.detect_pair_type(pair_info)
    
    # Рассчитываем курс с учетом типа пары ОДИН РАЗ
    if pair_type == 'rub_base':
        # RUB/X - ПЛЮС наценка
        adjusted_rate = MarginCalculator.calculate_rub_base_margin(
            base_rate, margin
        )
    elif pair_type == 'rub_quote':
        # X/RUB - МИНУС наценка
        adjusted_rate = MarginCalculator.calculate_rub_quote_margin(
            base_rate, margin
        )
    else:
        # Стандартная логика
        adjusted_rate = MarginCalculator.calculate_rub_base_margin(
            base_rate, margin
        )
    
    # Создаем банковские курсы БЕЗ повторного применения наценки
    # Передаем уже рассчитанный курс как базовый и обнуляем наценку
    banking_rates = MarginCalculator.calculate_banking_rates(
        base_rate=adjusted_rate,  # Используем уже рассчитанный курс
        # Обнуляем наценку, чтобы избежать двойного применения
        margin_percent=Decimal('0'),
        # Не передаем pair_info, чтобы избежать повторного расчета
        pair_info=None,
        spread_percent=spread_percent
    )
    
    # Итоговый курс берем как курс продажи (банк продает клиенту)
    final_rate = banking_rates.sell_rate
    
    return CalculationResult(
        pair_info=pair_info,
        amount=amount,
        # Сохраняем оригинальный базовый курс для отображения
        base_rate=base_rate,
        margin=margin,
        final_rate=final_rate,
        exchange_rate_data=exchange_rate_data,
        banking_rates=banking_rates
    )


def calculate_margin_rate(
    pair_info: Dict[str, Any],
    amount: Decimal,
    margin: Decimal,
    exchange_rate_data: Dict[str, Any],
    use_banking_logic: bool = True,
    spread_percent: Decimal = Decimal('0.5')
) -> CalculationResult:
    """
    Основная функция расчета курса с наценкой в банковском стиле
    
    Args:
        pair_info: Информация о валютной паре
        amount: Сумма для расчета
        margin: Процентная наценка
        exchange_rate_data: Данные о курсе
        use_banking_logic: Использовать банковскую логику покупки/продажи
        spread_percent: Спрэд между курсами покупки и продажи
        
    Returns:
        CalculationResult: Результат расчета
    """
    if use_banking_logic:
        return calculate_banking_rate(
            pair_info, amount, margin, exchange_rate_data, spread_percent
        )
    else:
        # Старая логика для совместимости с новой логикой
        base_rate = Decimal(str(exchange_rate_data['rate']))
        final_rate = MarginCalculator.calculate_final_rate(
            base_rate, margin, pair_info
        )
        
        return CalculationResult(
            pair_info=pair_info,
            amount=amount,
            base_rate=base_rate,
            margin=margin,
            final_rate=final_rate,
            exchange_rate_data=exchange_rate_data
        )