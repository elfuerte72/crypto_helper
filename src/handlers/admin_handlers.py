#!/usr/bin/env python3
"""
Обработчики административных команд для Crypto Helper Bot
Упрощенная версия - только команда /admin_bot и выбор валютных пар
"""

import logging
from typing import Optional

from aiogram import Router, Bot
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.fsm.context import FSMContext

# Импорты из новых модулей
from .currency_pairs import get_currency_pair_info, is_valid_currency_pair
from .keyboards import create_currency_pairs_keyboard
from .formatters import MessageFormatter

try:
    from ..config import config
    from ..utils.logger import get_bot_logger
except ImportError:
    # Handle direct execution
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from config import config
    from utils.logger import get_bot_logger

# Initialize logger
logger = get_bot_logger()

# Create router for admin handlers
admin_router = Router()


class AdminPermissionError(Exception):
    """Исключение для ошибок прав администратора"""
    pass


async def check_admin_permissions(bot: Bot, chat_id: int, user_id: int) -> bool:
    """
    Проверка прав администратора пользователя в канале
    
    Args:
        bot: Экземпляр бота
        chat_id: ID канала для проверки
        user_id: ID пользователя для проверки
        
    Returns:
        bool: True если пользователь является администратором
        
    Raises:
        AdminPermissionError: При ошибках проверки прав
    """
    try:
        # Получаем информацию о пользователе в канале
        chat_member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        
        # Проверяем статус пользователя
        admin_statuses = {
            ChatMemberStatus.CREATOR,
            ChatMemberStatus.ADMINISTRATOR
        }
        
        is_admin = chat_member.status in admin_statuses
        
        logger.info(
            f"Проверка прав администратора: "
            f"user_id={user_id}, chat_id={chat_id}, "
            f"status={chat_member.status}, is_admin={is_admin}"
        )
        
        return is_admin
        
    except TelegramBadRequest as e:
        logger.error(f"Ошибка Telegram API при проверке прав: {e}")
        raise AdminPermissionError(f"Не удалось проверить права доступа: {e}")
    
    except TelegramForbiddenError as e:
        logger.error(f"Доступ запрещен при проверке прав: {e}")
        raise AdminPermissionError("Бот не имеет доступа к информации о канале")
    
    except Exception as e:
        logger.error(f"Неожиданная ошибка при проверке прав: {e}")
        raise AdminPermissionError(f"Ошибка при проверке прав: {e}")


@admin_router.message(Command('admin_bot'))
async def admin_bot_command(message: Message, bot: Bot):
    """
    Обработчик команды /admin_bot
    Проверяет права администратора и показывает панель управления
    """
    user_id = message.from_user.id
    username = message.from_user.username or "N/A"
    
    logger.info(f"Команда /admin_bot от пользователя {user_id} (@{username})")
    
    # В режиме разработки пропускаем проверку прав
    if config.DEBUG_MODE:
        logger.info(f"Режим разработки: пропуск проверки прав для пользователя {user_id}")
    else:
        # Проверяем, указан ли канал для проверки прав
        if not config.ADMIN_CHANNEL_ID:
            await message.reply(
                "⚠️ <b>Ошибка конфигурации</b>\n\n"
                "Канал для проверки прав администратора не настроен.\n"
                "Обратитесь к разработчику.",
                parse_mode='HTML'
            )
            return
        
        try:
            # Проверяем права администратора
            is_admin = await check_admin_permissions(
                bot=bot,
                chat_id=config.ADMIN_CHANNEL_ID,
                user_id=user_id
            )
            
            if not is_admin:
                await message.reply(
                    "🚫 <b>Доступ запрещен</b>\n\n"
                    "Эта команда доступна только администраторам канала.\n"
                    "Для получения доступа обратитесь к администрации.",
                    parse_mode='HTML'
                )
                return
                
        except AdminPermissionError as e:
            await message.reply(
                f"❌ <b>Ошибка проверки прав</b>\n\n"
                f"{str(e)}\n\n"
                "Попробуйте позже или обратитесь к администратору.",
                parse_mode='HTML'
            )
            logger.error(f"Ошибка проверки прав для пользователя {user_id}: {e}")
            return
        
        except Exception as e:
            await message.reply(
                "❌ <b>Произошла ошибка</b>\n\n"
                "Не удалось обработать команду. Попробуйте позже.",
                parse_mode='HTML'
            )
            logger.error(f"Неожиданная ошибка в admin_bot_command: {e}")
            return
    
    try:
        # Создаем клавиатуру для выбора валютных пар
        keyboard = create_currency_pairs_keyboard()
        
        # Отправляем сообщение с панелью управления
        debug_status = "🔧 Режим разработки" if config.DEBUG_MODE else "🔒 Проверка прав пройдена"
        
        welcome_message = MessageFormatter.format_welcome_message()
        admin_message = f"{debug_status}\n\n{welcome_message}"
        
        await message.reply(
            admin_message,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
        logger.info(f"Административная панель отправлена пользователю {user_id} (DEBUG: {config.DEBUG_MODE})")
        
    except Exception as e:
        await message.reply(
            "❌ <b>Произошла ошибка</b>\n\n"
            "Не удалось отобразить панель управления. Попробуйте позже.",
            parse_mode='HTML'
        )
        logger.error(f"Неожиданная ошибка при отображении панели: {e}")


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