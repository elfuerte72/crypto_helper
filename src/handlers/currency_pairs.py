#!/usr/bin/env python3
"""
Currency Pairs (DEPRECATED)
Заглушка для обратной совместимости со старой логикой
Новая логика использует пошаговый выбор в fsm_states.py
"""

# from .fsm_states import Currency, is_valid_pair  # Будет использовано позже


def get_currency_pair_info(pair_callback: str) -> dict:
    """DEPRECATED: Получить информацию о валютной паре"""
    # Заглушка для старых импортов
    return {
        "name": pair_callback,
        "base": "RUB",
        "quote": "USDT"
    }


def is_valid_currency_pair(pair_callback: str) -> bool:
    """DEPRECATED: Проверить валидность валютной пары"""
    # Заглушка для старых импортов
    return True  # Временно разрешаем все 