#!/usr/bin/env python3
"""
Модуль FSM состояний для Crypto Helper Bot
Содержит определения состояний для управления диалогом
"""

from aiogram.fsm.state import State, StatesGroup


class MarginCalculationForm(StatesGroup):
    """FSM состояния для расчета курса с наценкой"""
    waiting_for_margin = State()
    showing_rate_comparison = State()
    waiting_for_amount = State()
    showing_result = State()


class MarginCalculationError(Exception):
    """Исключение для ошибок расчета наценки"""
    pass