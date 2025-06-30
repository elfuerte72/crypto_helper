#!/usr/bin/env python3
"""
Обработчики административных команд для Crypto Helper Bot
Включает проверку прав администратора и управление валютными парами
"""

import logging
from typing import Optional

from aiogram import Router, Bot
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

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


def create_currency_pairs_keyboard() -> InlineKeyboardMarkup:
    """
    Создание inline клавиатуры для выбора валютных пар
    
    Returns:
        InlineKeyboardMarkup: Клавиатура с валютными парами
    """
    
    # Группируем валютные пары по базовой валюте
    rub_pairs = [
        ('RUB/ZAR', 'rub_zar'),
        ('RUB/THB', 'rub_thb'), 
        ('RUB/AED', 'rub_aed'),
        ('RUB/IDR', 'rub_idr')
    ]
    
    usdt_pairs = [
        ('USDT/ZAR', 'usdt_zar'),
        ('USDT/THB', 'usdt_thb'),
        ('USDT/AED', 'usdt_aed'), 
        ('USDT/IDR', 'usdt_idr')
    ]
    
    # Обратные пары
    reverse_rub_pairs = [
        ('ZAR/RUB', 'zar_rub'),
        ('THB/RUB', 'thb_rub'),
        ('AED/RUB', 'aed_rub'),
        ('IDR/RUB', 'idr_rub')
    ]
    
    reverse_usdt_pairs = [
        ('ZAR/USDT', 'zar_usdt'),
        ('THB/USDT', 'thb_usdt'),
        ('AED/USDT', 'aed_usdt'),
        ('IDR/USDT', 'idr_usdt')
    ]
    
    # Создаем кнопки
    keyboard = []
    
    # Добавляем заголовок для RUB пар
    keyboard.append([
        InlineKeyboardButton(text="🇷🇺 RUB → Другие валюты", callback_data="header_rub")
    ])
    
    # Добавляем RUB пары по 2 в ряд
    for i in range(0, len(rub_pairs), 2):
        row = []
        for j in range(2):
            if i + j < len(rub_pairs):
                pair_name, callback_data = rub_pairs[i + j]
                row.append(InlineKeyboardButton(text=pair_name, callback_data=callback_data))
        keyboard.append(row)
    
    # Добавляем заголовок для USDT пар
    keyboard.append([
        InlineKeyboardButton(text="💰 USDT → Другие валюты", callback_data="header_usdt")
    ])
    
    # Добавляем USDT пары по 2 в ряд
    for i in range(0, len(usdt_pairs), 2):
        row = []
        for j in range(2):
            if i + j < len(usdt_pairs):
                pair_name, callback_data = usdt_pairs[i + j]
                row.append(InlineKeyboardButton(text=pair_name, callback_data=callback_data))
        keyboard.append(row)
    
    # Добавляем заголовок для обратных RUB пар
    keyboard.append([
        InlineKeyboardButton(text="🔄 Другие валюты → RUB", callback_data="header_reverse_rub")
    ])
    
    # Добавляем обратные RUB пары по 2 в ряд
    for i in range(0, len(reverse_rub_pairs), 2):
        row = []
        for j in range(2):
            if i + j < len(reverse_rub_pairs):
                pair_name, callback_data = reverse_rub_pairs[i + j]
                row.append(InlineKeyboardButton(text=pair_name, callback_data=callback_data))
        keyboard.append(row)
    
    # Добавляем заголовок для обратных USDT пар
    keyboard.append([
        InlineKeyboardButton(text="🔄 Другие валюты → USDT", callback_data="header_reverse_usdt")
    ])
    
    # Добавляем обратные USDT пары по 2 в ряд
    for i in range(0, len(reverse_usdt_pairs), 2):
        row = []
        for j in range(2):
            if i + j < len(reverse_usdt_pairs):
                pair_name, callback_data = reverse_usdt_pairs[i + j]
                row.append(InlineKeyboardButton(text=pair_name, callback_data=callback_data))
        keyboard.append(row)
    
    # Добавляем кнопку отмены
    keyboard.append([
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_selection")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


@admin_router.message(Command('admin_bot'))
async def admin_bot_command(message: Message, bot: Bot):
    """
    Обработчик команды /admin_bot
    Проверяет права администратора и показывает панель управления
    """
    user_id = message.from_user.id
    username = message.from_user.username or "N/A"
    
    logger.info(f"Команда /admin_bot от пользователя {user_id} (@{username})")
    
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
        
        # Создаем клавиатуру для выбора валютных пар
        keyboard = create_currency_pairs_keyboard()
        
        # Отправляем сообщение с панелью управления
        admin_message = (
            "🔧 <b>Административная панель</b>\n\n"
            "Добро пожаловать в панель управления Crypto Helper Bot!\n\n"
            "📊 <b>Выберите валютную пару для получения курса:</b>\n\n"
            "• Выберите нужную валютную пару из списка ниже\n"
            "• Укажите процентную наценку\n"
            "• Получите актуальный курс с наценкой\n\n"
            "💡 <i>Курсы обновляются в реальном времени через Rapira API</i>"
        )
        
        await message.reply(
            admin_message,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
        logger.info(f"Административная панель отправлена пользователю {user_id}")
        
    except AdminPermissionError as e:
        await message.reply(
            f"❌ <b>Ошибка проверки прав</b>\n\n"
            f"{str(e)}\n\n"
            "Попробуйте позже или обратитесь к администратору.",
            parse_mode='HTML'
        )
        logger.error(f"Ошибка проверки прав для пользователя {user_id}: {e}")
    
    except Exception as e:
        await message.reply(
            "❌ <b>Произошла ошибка</b>\n\n"
            "Не удалось обработать команду. Попробуйте позже.",
            parse_mode='HTML'
        )
        logger.error(f"Неожиданная ошибка в admin_bot_command: {e}")


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
    await callback_query.message.edit_text(
        "❌ <b>Операция отменена</b>\n\n"
        "Выбор валютной пары отменен.\n"
        "Используйте /admin_bot для повторного вызова панели.",
        parse_mode='HTML'
    )
    
    await callback_query.answer("Операция отменена", show_alert=False)
    logger.info(f"Пользователь {callback_query.from_user.id} отменил выбор валютной пары")


@admin_router.callback_query(lambda c: c.data and '_' in c.data and not c.data.startswith('header_'))
async def handle_currency_pair_selection(callback_query: CallbackQuery):
    """
    Обработчик выбора валютной пары
    Пока что только показывает выбранную пару (полная реализация будет в следующих фазах)
    """
    pair_callback = callback_query.data
    user_id = callback_query.from_user.id
    
    # Маппинг callback_data на читаемые названия пар
    pair_names = {
        'rub_zar': 'RUB/ZAR',
        'rub_thb': 'RUB/THB',
        'rub_aed': 'RUB/AED', 
        'rub_idr': 'RUB/IDR',
        'usdt_zar': 'USDT/ZAR',
        'usdt_thb': 'USDT/THB',
        'usdt_aed': 'USDT/AED',
        'usdt_idr': 'USDT/IDR',
        'zar_rub': 'ZAR/RUB',
        'thb_rub': 'THB/RUB',
        'aed_rub': 'AED/RUB',
        'idr_rub': 'IDR/RUB',
        'zar_usdt': 'ZAR/USDT',
        'thb_usdt': 'THB/USDT',
        'aed_usdt': 'AED/USDT',
        'idr_usdt': 'IDR/USDT'
    }
    
    pair_name = pair_names.get(pair_callback, pair_callback.upper())
    
    logger.info(f"Пользователь {user_id} выбрал валютную пару: {pair_name}")
    
    # Временное сообщение для MVP (полная реализация в следующих фазах)
    response_message = (
        f"✅ <b>Валютная пара выбрана</b>\n\n"
        f"📊 <b>Пара:</b> {pair_name}\n\n"
        f"🚧 <b>В разработке</b>\n"
        f"Функциональность получения курса и расчета наценки "
        f"будет реализована в следующих фазах.\n\n"
        f"📝 <b>Следующие шаги:</b>\n"
        f"• Интеграция с Rapira API\n"
        f"• Запрос процентной наценки\n"
        f"• Расчет итогового курса\n"
        f"• Публикация в канал\n\n"
        f"Используйте /admin_bot для повторного вызова панели."
    )
    
    await callback_query.message.edit_text(
        response_message,
        parse_mode='HTML'
    )
    
    await callback_query.answer(f"Выбрана пара: {pair_name}", show_alert=False)