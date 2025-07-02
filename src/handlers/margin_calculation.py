#!/usr/bin/env python3
"""
Упрощенный модуль расчета курса с наценкой для Crypto Helper Bot
Основной интерфейс для обратной совместимости
"""

# Импорты для обратной совместимости
from .fsm_states import MarginCalculationForm, MarginCalculationError
from .validation import InputValidator, ValidationError, validate_user_input
from .calculation_logic import (
    MarginCalculator, 
    CalculationResult, 
    calculate_margin_rate
)
from .formatters import MessageFormatter
from .keyboards import (
    KeyboardBuilder,
    create_currency_pairs_keyboard,
    create_amount_selection_keyboard,
    create_margin_selection_keyboard,
    create_result_keyboard
)
from .currency_pairs import (
    get_currency_pair_info,
    is_valid_currency_pair,
    get_all_currency_pairs
)
from .bot_handlers import (
    margin_router,
    start_margin_calculation
)

# Экспортируем основные компоненты для обратной совместимости
__all__ = [
    # FSM
    'MarginCalculationForm',
    'MarginCalculationError',
    
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
    'create_amount_selection_keyboard',
    'create_margin_selection_keyboard',
    'create_result_keyboard',
    
    # Валютные пары
    'get_currency_pair_info',
    'is_valid_currency_pair',
    'get_all_currency_pairs',
    
    # Обработчики
    'margin_router',
    'start_margin_calculation'
]

# Для обратной совместимости - псевдонимы старых классов
AmountValidator = InputValidator  # Старое название класса