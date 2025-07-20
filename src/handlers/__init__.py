#!/usr/bin/env python3
"""
Handlers package for Crypto Helper Bot (НОВАЯ ЛОГИКА)
Модульная архитектура для пошагового флоу обмена валют
"""

# Импорты основных компонентов (новая логика)
from .admin_handlers import admin_router
from .admin_flow import admin_flow_router
from .bot_handlers import margin_router, start_margin_calculation
from .currency_pairs import get_currency_pair_info, is_valid_currency_pair
from .calculation_logic import calculate_margin_rate
from .formatters import MessageFormatter
from .keyboards import (
    create_source_currency_keyboard,
    create_target_currency_keyboard,
    create_margin_input_keyboard,
    create_amount_input_keyboard,
    create_result_keyboard
)
from .fsm_states import ExchangeFlow, Currency
from .validators import ExchangeValidator, ValidationResult

__all__ = [
    # Роутеры
    'admin_router',
    'admin_flow_router',
    'margin_router',
    
    # Основные функции
    'start_margin_calculation',
    
    # Валютные пары (обратная совместимость)
    'get_currency_pair_info',
    'is_valid_currency_pair',
    
    # Расчеты
    'calculate_margin_rate',
    
    # Форматирование
    'MessageFormatter',
    
    # Клавиатуры (новая логика)
    'create_source_currency_keyboard',
    'create_target_currency_keyboard', 
    'create_margin_input_keyboard',
    'create_amount_input_keyboard',
    'create_result_keyboard',
    
    # FSM (новая логика)
    'ExchangeFlow',
    'Currency',
    
    # Валидация
    'ExchangeValidator',
    'ValidationResult'
]