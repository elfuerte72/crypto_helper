#!/usr/bin/env python3
"""
Модуль валютных пар и констант для Crypto Helper Bot
Содержит определения валютных пар для криптовалют с рублем
"""

from typing import Dict, Any, Optional

# Константы валютных пар (криптовалюты с рублем)
CURRENCY_PAIRS = {
    # RUB пары с криптовалютами
    'rub_btc': {
        'name': 'RUB/BTC',
        'base': 'RUB',
        'quote': 'BTC',
        'emoji': '₿',
        'description': 'Российский рубль к Bitcoin'
    },
    'rub_ton': {
        'name': 'RUB/TON',
        'base': 'RUB',
        'quote': 'TON',
        'emoji': '💎',
        'description': 'Российский рубль к Toncoin'
    },
    'rub_usdt': {
        'name': 'RUB/USDT',
        'base': 'RUB',
        'quote': 'USDT',
        'emoji': '🟢',
        'description': 'Российский рубль к Tether'
    },
    'rub_eth': {
        'name': 'RUB/ETH',
        'base': 'RUB',
        'quote': 'ETH',
        'emoji': '🔷',
        'description': 'Российский рубль к Ethereum'
    },
    
    # Обратные пары (криптовалюты к рублю)
    'btc_rub': {
        'name': 'BTC/RUB',
        'base': 'BTC',
        'quote': 'RUB',
        'emoji': '₿',
        'description': 'Bitcoin к Российскому рублю'
    },
    'ton_rub': {
        'name': 'TON/RUB',
        'base': 'TON',
        'quote': 'RUB',
        'emoji': '💎',
        'description': 'Toncoin к Российскому рублю'
    },
    'usdt_rub': {
        'name': 'USDT/RUB',
        'base': 'USDT',
        'quote': 'RUB',
        'emoji': '🟢',
        'description': 'Tether к Российскому рублю'
    },
    'eth_rub': {
        'name': 'ETH/RUB',
        'base': 'ETH',
        'quote': 'RUB',
        'emoji': '🔷',
        'description': 'Ethereum к Российскому рублю'
    }
}


def get_currency_pair_info(pair_callback: str) -> Optional[Dict[str, Any]]:
    """
    Получение информации о валютной паре по callback данным
    
    Args:
        pair_callback: Callback данные валютной пары (например, 'rub_btc')
        
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
        base_currency: Базовая валюта (например, 'RUB' или 'BTC')
        
    Returns:
        Dict[str, Dict[str, Any]]: Словарь валютных пар с базовой валютой
    """
    return {
        key: value for key, value in CURRENCY_PAIRS.items()
        if value['base'] == base_currency
    }


def get_currency_pairs_by_quote(quote_currency: str) -> Dict[str, Dict[str, Any]]:
    """
    Получение валютных пар по котируемой валюте
    
    Args:
        quote_currency: Котируемая валюта (например, 'RUB' или 'BTC')
        
    Returns:
        Dict[str, Dict[str, Any]]: Словарь валютных пар с котируемой валютой
    """
    return {
        key: value for key, value in CURRENCY_PAIRS.items()
        if value['quote'] == quote_currency
    }


def get_crypto_to_rub_pairs() -> Dict[str, Dict[str, Any]]:
    """
    Получение пар криптовалют к рублю (например, BTC/RUB)
    
    Returns:
        Dict[str, Dict[str, Any]]: Словарь пар криптовалют к рублю
    """
    return get_currency_pairs_by_quote('RUB')


def get_rub_to_crypto_pairs() -> Dict[str, Dict[str, Any]]:
    """
    Получение пар рубля к криптовалютам (например, RUB/BTC)
    
    Returns:
        Dict[str, Dict[str, Any]]: Словарь пар рубля к криптовалютам
    """
    return get_currency_pairs_by_base('RUB')


def format_currency_symbol(currency: str) -> str:
    """
    Форматирование символа валюты с эмодзи
    
    Args:
        currency: Код валюты (BTC, ETH, TON, USDT, RUB)
        
    Returns:
        str: Отформатированный символ валюты
    """
    emoji_map = {
        'BTC': '₿ BTC',
        'ETH': '🔷 ETH', 
        'TON': '💎 TON',
        'USDT': '🟢 USDT',
        'RUB': '🇷🇺 RUB'
    }
    return emoji_map.get(currency, currency)


def get_pair_display_name(pair_callback: str) -> str:
    """
    Получение отображаемого имени валютной пары
    
    Args:
        pair_callback: Callback данные пары (например, 'rub_btc')
        
    Returns:
        str: Отображаемое имя пары с эмодзи
    """
    pair_info = get_currency_pair_info(pair_callback)
    if not pair_info:
        return pair_callback.upper()
    
    base_formatted = format_currency_symbol(pair_info['base'])
    quote_formatted = format_currency_symbol(pair_info['quote'])
    
    return f"{base_formatted} → {quote_formatted}"