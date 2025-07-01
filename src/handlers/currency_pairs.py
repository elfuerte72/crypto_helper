#!/usr/bin/env python3
"""
Модуль валютных пар и констант для Crypto Helper Bot
Содержит определения валютных пар и функции для работы с ними
"""

from typing import Dict, Any, Optional

# Константы валютных пар (упрощенные - только USDT пары)
CURRENCY_PAIRS = {
    # USDT пары
    'usdt_zar': {
        'name': 'USDT/ZAR',
        'base': 'USDT',
        'quote': 'ZAR',
        'emoji': '🇿🇦',
        'description': 'Tether к Южноафриканскому рэнду'
    },
    'usdt_thb': {
        'name': 'USDT/THB',
        'base': 'USDT',
        'quote': 'THB',
        'emoji': '🇹🇭',
        'description': 'Tether к Тайскому бату'
    },
    'usdt_aed': {
        'name': 'USDT/AED',
        'base': 'USDT',
        'quote': 'AED',
        'emoji': '🇦🇪',
        'description': 'Tether к Дирхаму ОАЭ'
    },
    'usdt_idr': {
        'name': 'USDT/IDR',
        'base': 'USDT',
        'quote': 'IDR',
        'emoji': '🇮🇩',
        'description': 'Tether к Индонезийской рупии'
    },
    'usdt_rub': {
        'name': 'USDT/RUB',
        'base': 'USDT',
        'quote': 'RUB',
        'emoji': '🇷🇺',
        'description': 'Tether к Российскому рублю'
    },
    
    # Обратные USDT пары
    'zar_usdt': {
        'name': 'ZAR/USDT',
        'base': 'ZAR',
        'quote': 'USDT',
        'emoji': '🇿🇦',
        'description': 'Южноафриканский рэнд к Tether'
    },
    'thb_usdt': {
        'name': 'THB/USDT',
        'base': 'THB',
        'quote': 'USDT',
        'emoji': '🇹🇭',
        'description': 'Тайский бат к Tether'
    },
    'aed_usdt': {
        'name': 'AED/USDT',
        'base': 'AED',
        'quote': 'USDT',
        'emoji': '🇦🇪',
        'description': 'Дирхам ОАЭ к Tether'
    },
    'idr_usdt': {
        'name': 'IDR/USDT',
        'base': 'IDR',
        'quote': 'USDT',
        'emoji': '🇮🇩',
        'description': 'Индонезийская рупия к Tether'
    },
    'rub_usdt': {
        'name': 'RUB/USDT',
        'base': 'RUB',
        'quote': 'USDT',
        'emoji': '🇷🇺',
        'description': 'Российский рубль к Tether'
    }
}


def get_currency_pair_info(pair_callback: str) -> Optional[Dict[str, Any]]:
    """
    Получение информации о валютной паре по callback данным
    
    Args:
        pair_callback: Callback данные валютной пары (например, 'usdt_zar')
        
    Returns:
        Dict[str, Any]: Информация о валютной паре или None если не найдена
    """
    return CURRENCY_PAIRS.get(pair_callback)


def is_valid_currency_pair(pair_callback: str) -> bool:
    """
    Проверка валидности валютной пары
    
    Args:
        pair_callback: Callback данные валютной пары
        
    Returns:
        bool: True если пара существует, False в противном случае
    """
    return pair_callback in CURRENCY_PAIRS


def get_all_currency_pairs() -> Dict[str, Dict[str, Any]]:
    """
    Получение всех доступных валютных пар
    
    Returns:
        Dict[str, Dict[str, Any]]: Словарь всех валютных пар
    """
    return CURRENCY_PAIRS.copy()


def get_currency_pairs_by_base(base_currency: str) -> Dict[str, Dict[str, Any]]:
    """
    Получение валютных пар по базовой валюте
    
    Args:
        base_currency: Базовая валюта (например, 'USDT')
        
    Returns:
        Dict[str, Dict[str, Any]]: Словарь валютных пар с указанной базовой валютой
    """
    return {
        key: value for key, value in CURRENCY_PAIRS.items()
        if value['base'] == base_currency
    }


def get_currency_pairs_by_quote(quote_currency: str) -> Dict[str, Dict[str, Any]]:
    """
    Получение валютных пар по котируемой валюте
    
    Args:
        quote_currency: Котируемая валюта (например, 'RUB')
        
    Returns:
        Dict[str, Dict[str, Any]]: Словарь валютных пар с указанной котируемой валютой
    """
    return {
        key: value for key, value in CURRENCY_PAIRS.items()
        if value['quote'] == quote_currency
    }