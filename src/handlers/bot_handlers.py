#!/usr/bin/env python3
"""
Модуль основных обработчиков для Crypto Helper Bot (ЗАГЛУШКА)
Временная заглушка до реализации новой логики в Фазе 1
"""

from aiogram import Router
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

# Новые импорты для новой логики
from .fsm_states import ExchangeFlow
from .formatters import MessageFormatter

try:
    from ..utils.logger import get_bot_logger
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from utils.logger import get_bot_logger

# Initialize logger
logger = get_bot_logger()

# Create router for margin calculation handlers
margin_router = Router()


async def start_margin_calculation(
    callback_query: CallbackQuery, 
    pair_callback: str, 
    state: FSMContext
):
    """
    ЗАГЛУШКА: Обработчик начала расчета наценки
    Будет реализован в Фазе 1
    """
    user_id = callback_query.from_user.id
    
    logger.info(f"Запрос расчета: user_id={user_id}, pair={pair_callback}")
    
    # Временная заглушка
    await callback_query.answer("🚧 Функция в разработке")
    
    message_text = (
        "🚧 <b>Новая логика в разработке</b>\n\n"
        "Пошаговый флоу обмена будет реализован в Фазе 1.\n"
        "Пока используется заглушка."
    )
    
    await callback_query.message.edit_text(
        message_text,
        parse_mode='HTML'
    )
    
    # Устанавливаем начальное состояние
    await state.set_state(ExchangeFlow.WAITING_FOR_SOURCE_CURRENCY)