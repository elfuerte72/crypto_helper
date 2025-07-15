#!/usr/bin/env python3
"""
Handlers package for Crypto Helper Bot
Модульная архитектура обработчиков бота
"""

# Импорты основных компонентов
from .admin_handlers import admin_router
from .bot_handlers import margin_router, start_margin_calculation
from .currency_pairs import (
    get_currency_pair_info, 
    is_valid_currency_pair, 
    get_all_currency_pairs,
    CURRENCY_PAIRS
)
from .validation import InputValidator, ValidationError, validate_user_input
from .calculation_logic import (
    MarginCalculator, 
    CalculationResult, 
    calculate_margin_rate
)
from .formatters import MessageFormatter
from .keyboards import KeyboardBuilder, create_currency_pairs_keyboard
from .fsm_states import MarginCalculationForm, MarginCalculationError

__all__ = [
    # Роутеры
    'admin_router',
    'margin_router',
    
    # Основные функции
    'start_margin_calculation',
    
    # Валютные пары
    'get_currency_pair_info',
    'is_valid_currency_pair', 
    'get_all_currency_pairs',
    'CURRENCY_PAIRS',
    
    # Валидация
    'InputValidator',
    'ValidationError',
    'validate_user_input',
    
    # Расчеты
    'MarginCalculator',
    'CalculationResult',
    'calculate_margin_rate',
    
    # Форматирование
    'MessageFormatter',
    
    # Клавиатуры
    'KeyboardBuilder',
    'create_currency_pairs_keyboard',
    
    # FSM
    'MarginCalculationForm',
    'MarginCalculationError'
]