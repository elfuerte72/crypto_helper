#!/usr/bin/env python3
"""
FSM States для Crypto Helper Bot (Новая логика)
Состояния для пошагового флоу обмена валют
"""

from aiogram.fsm.state import State, StatesGroup
from enum import Enum


class Currency(str, Enum):
    """Поддерживаемые валюты"""
    RUB = "RUB"
    USDT = "USDT"
    USD = "USD"
    EUR = "EUR"


class ExchangeFlow(StatesGroup):
    """FSM состояния для процесса обмена валют"""
    
    # Шаг 1: Выбор исходной валюты (что отдает клиент)
    WAITING_FOR_SOURCE_CURRENCY = State()
    
    # Шаг 2: Выбор целевой валюты (что получает клиент)
    WAITING_FOR_TARGET_CURRENCY = State()
    
    # Шаг 3: Ввод наценки в процентах
    WAITING_FOR_MARGIN = State()
    
    # Шаг 4: Ввод суммы сделки
    WAITING_FOR_AMOUNT = State()
    
    # Шаг 5: Показ результата
    SHOWING_RESULT = State()


# Конфигурация поддерживаемых направлений обмена
SUPPORTED_SOURCES = [Currency.RUB, Currency.USDT]

TARGETS_FOR_RUB = [Currency.USDT, Currency.USD, Currency.EUR]
TARGETS_FOR_USDT = [Currency.RUB]

# Валидационные правила
MIN_MARGIN = 0.1
MAX_MARGIN = 10.0
MIN_AMOUNT = 1.0


def get_available_targets(source_currency: Currency) -> list[Currency]:
    """Получить доступные целевые валюты для исходной валюты"""
    if source_currency == Currency.RUB:
        return TARGETS_FOR_RUB
    elif source_currency == Currency.USDT:
        return TARGETS_FOR_USDT
    else:
        return []


def is_valid_pair(source: Currency, target: Currency) -> bool:
    """Проверить валидность валютной пары"""
    available_targets = get_available_targets(source)
    return target in available_targets


# Для обратной совместимости (временно)
class MarginCalculationForm(StatesGroup):
    """DEPRECATED: Используйте ExchangeFlow"""
    pass


class MarginCalculationError(Exception):
    """DEPRECATED: Ошибка расчета наценки"""
    pass 