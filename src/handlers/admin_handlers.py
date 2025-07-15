#!/usr/bin/env python3
"""
Обработчики команд для Crypto Helper Bot
Упрощенная версия - только команда /admin_bot и выбор валютных пар
"""

import logging

from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

# Импорты из новых модулей
from .currency_pairs import get_currency_pair_info, is_valid_currency_pair
from .keyboards import create_currency_pairs_keyboard
from .formatters import MessageFormatter

try:
    from ..utils.logger import get_bot_logger
except ImportError:
    # Handle direct execution
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from utils.logger import get_bot_logger

# Initialize logger
logger = get_bot_logger()

# Create router for admin handlers
admin_router = Router()


@admin_router.message(Command('admin_bot'))
async def admin_bot_command(message: Message):
    """
    Обработчик команды /admin_bot
    Показывает панель управления для всех пользователей
    """
    user_id = message.from_user.id
    username = message.from_user.username or "N/A"
    
    logger.info(f"Команда /admin_bot от пользователя {user_id} (@{username})")
    
    try:
        # Создаем клавиатуру для выбора валютных пар
        keyboard = create_currency_pairs_keyboard()
        
        # Отправляем сообщение с панелью управления
        welcome_message = MessageFormatter.format_welcome_message()
        
        await message.reply(
            welcome_message,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
        logger.info(f"Панель управления отправлена пользователю {user_id}")
        
    except Exception as e:
        await message.reply(
            "❌ <b>Произошла ошибка</b>\n\n"
            "Не удалось отобразить панель управления. Попробуйте позже.",
            parse_mode='HTML'
        )
        logger.error(f"Неожиданная ошибка при отображении панели: {e}")


@admin_router.callback_query(lambda c: c.data and c.data.startswith('header_'))
async def handle_header_callbacks(callback_query: CallbackQuery):
    """
    Обработчик для кнопок-заголовков (не выполняет действий, только уведомление)
    """
    await callback_query.answer("Это заголовок. Выберите валютную пару ниже.", show_alert=False)


@admin_router.callback_query(lambda c: c.data == 'cancel_selection')
async def handle_cancel_selection(callback_query: CallbackQuery):
    """
    Обработчик отмены выбора валютной пары
    """
    cancel_message = MessageFormatter.format_cancel_message("Операция")
    await callback_query.message.edit_text(cancel_message, parse_mode='HTML')
    
    await callback_query.answer("Операция отменена", show_alert=False)
    logger.info(f"Пользователь {callback_query.from_user.id} отменил выбор валютной пары")


@admin_router.callback_query(lambda c: c.data and c.data.startswith('pair_'))
async def handle_currency_pair_selection(callback_query: CallbackQuery, state: FSMContext):
    """
    Обработчик выбора валютной пары
    Обрабатывает все поддерживаемые валютные пары и запускает расчет наценки
    """
    # Импортируем функцию из нового модуля
    from .bot_handlers import start_margin_calculation
    
    # Извлекаем название пары из callback данных
    pair_callback = callback_query.data.replace('pair_', '')
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username or "N/A"
    
    logger.info(
        f"Обработка выбора валютной пары: "
        f"user_id={user_id}, username=@{username}, pair={pair_callback}"
    )
    
    # Проверяем валидность валютной пары
    if not is_valid_currency_pair(pair_callback):
        logger.warning(f"Неизвестная валютная пара: {pair_callback}")
        await callback_query.answer(
            "❌ Неизвестная валютная пара",
            show_alert=True
        )
        return
    
    # Получаем информацию о валютной паре
    pair_info = get_currency_pair_info(pair_callback)
    
    if not pair_info:
        logger.error(f"Не удалось получить информацию о паре: {pair_callback}")
        await callback_query.answer(
            "❌ Ошибка получения информации о валютной паре",
            show_alert=True
        )
        return
    
    # Запускаем процесс расчета наценки
    await start_margin_calculation(callback_query, pair_callback, state)
    
    logger.info(
        f"Запущен процесс расчета наценки для пары: "
        f"user_id={user_id}, pair={pair_info['name']}"
    )