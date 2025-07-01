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
from aiogram.fsm.context import FSMContext

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
    
    # В режиме разработки пропускаем проверку администратора
    if config.DEBUG_MODE:
        logger.info(f"Режим разработки: пропускаем проверку прав для пользователя {user_id}")
        # Переходим сразу к показу панели управления
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
    
    # Создаем клавиатуру для выбора валютных пар
    keyboard = create_currency_pairs_keyboard()
    
    # Отправляем сообщение с панелью управления
    if config.DEBUG_MODE:
        admin_message = (
            "🔧 <b>Административная панель (Режим разработки)</b>\n\n"
            "Добро пожаловать в панель управления Crypto Helper Bot!\n\n"
            "🧪 <i>Режим разработки активен - проверка прав администратора отключена</i>\n\n"
            "📊 <b>Выберите валютную пару для получения курса:</b>\n\n"
            "• Выберите нужную валютную пару из списка ниже\n"
            "• Укажите процентную наценку\n"
            "• Получите актуальный курс с наценкой\n\n"
            "💡 <i>Курсы обновляются в реальном времени через Rapira API</i>"
        )
    else:
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


# Константы для валютных пар
CURRENCY_PAIRS = {
    # RUB пары
    'rub_zar': {
        'name': 'RUB/ZAR',
        'base': 'RUB',
        'quote': 'ZAR',
        'description': 'Российский рубль → Южноафриканский рэнд',
        'emoji': '🇷🇺➡️🇿🇦'
    },
    'rub_thb': {
        'name': 'RUB/THB',
        'base': 'RUB',
        'quote': 'THB',
        'description': 'Российский рубль → Тайский бат',
        'emoji': '🇷🇺➡️🇹🇭'
    },
    'rub_aed': {
        'name': 'RUB/AED',
        'base': 'RUB',
        'quote': 'AED',
        'description': 'Российский рубль → Дирхам ОАЭ',
        'emoji': '🇷🇺➡️🇦🇪'
    },
    'rub_idr': {
        'name': 'RUB/IDR',
        'base': 'RUB',
        'quote': 'IDR',
        'description': 'Российский рубль → Индонезийская рупия',
        'emoji': '🇷🇺➡️🇮🇩'
    },
    # USDT пары
    'usdt_zar': {
        'name': 'USDT/ZAR',
        'base': 'USDT',
        'quote': 'ZAR',
        'description': 'Tether USD → Южноафриканский рэнд',
        'emoji': '💰➡️🇿🇦'
    },
    'usdt_thb': {
        'name': 'USDT/THB',
        'base': 'USDT',
        'quote': 'THB',
        'description': 'Tether USD → Тайский бат',
        'emoji': '💰➡️🇹🇭'
    },
    'usdt_aed': {
        'name': 'USDT/AED',
        'base': 'USDT',
        'quote': 'AED',
        'description': 'Tether USD → Дирхам ОАЭ',
        'emoji': '💰➡️🇦🇪'
    },
    'usdt_idr': {
        'name': 'USDT/IDR',
        'base': 'USDT',
        'quote': 'IDR',
        'description': 'Tether USD → Индонезийская рупия',
        'emoji': '💰➡️🇮🇩'
    },
    # Обратные RUB пары
    'zar_rub': {
        'name': 'ZAR/RUB',
        'base': 'ZAR',
        'quote': 'RUB',
        'description': 'Южноафриканский рэнд → Российский рубль',
        'emoji': '🇿🇦➡️🇷🇺'
    },
    'thb_rub': {
        'name': 'THB/RUB',
        'base': 'THB',
        'quote': 'RUB',
        'description': 'Тайский бат → Российский рубль',
        'emoji': '🇹🇭➡️🇷🇺'
    },
    'aed_rub': {
        'name': 'AED/RUB',
        'base': 'AED',
        'quote': 'RUB',
        'description': 'Дирхам ОАЭ → Российский рубль',
        'emoji': '🇦🇪➡️🇷🇺'
    },
    'idr_rub': {
        'name': 'IDR/RUB',
        'base': 'IDR',
        'quote': 'RUB',
        'description': 'Индонезийская рупия → Российский рубль',
        'emoji': '🇮🇩➡️🇷🇺'
    },
    # Обратные USDT пары
    'zar_usdt': {
        'name': 'ZAR/USDT',
        'base': 'ZAR',
        'quote': 'USDT',
        'description': 'Южноафриканский рэнд → Tether USD',
        'emoji': '🇿🇦➡️💰'
    },
    'thb_usdt': {
        'name': 'THB/USDT',
        'base': 'THB',
        'quote': 'USDT',
        'description': 'Тайский бат → Tether USD',
        'emoji': '🇹🇭➡️💰'
    },
    'aed_usdt': {
        'name': 'AED/USDT',
        'base': 'AED',
        'quote': 'USDT',
        'description': 'Дирхам ОАЭ → Tether USD',
        'emoji': '🇦🇪➡️💰'
    },
    'idr_usdt': {
        'name': 'IDR/USDT',
        'base': 'IDR',
        'quote': 'USDT',
        'description': 'Индонезийская рупия → Tether USD',
        'emoji': '🇮🇩➡️💰'
    }
}


def get_currency_pair_info(pair_callback: str) -> Optional[dict]:
    """
    Получение информации о валютной паре по callback данным
    
    Args:
        pair_callback: Callback данные валютной пары
        
    Returns:
        dict: Информация о валютной паре или None если пара не найдена
    """
    return CURRENCY_PAIRS.get(pair_callback)


def is_valid_currency_pair(pair_callback: str) -> bool:
    """
    Проверка валидности валютной пары
    
    Args:
        pair_callback: Callback данные для проверки
        
    Returns:
        bool: True если пара валидна
    """
    return pair_callback in CURRENCY_PAIRS


@admin_router.callback_query(lambda c: c.data and '_' in c.data and not c.data.startswith('header_'))
async def handle_currency_pair_selection(callback_query: CallbackQuery, state: FSMContext):
    """
    Обработчик выбора валютной пары
    Обрабатывает все поддерживаемые валютные пары и запускает расчет наценки
    """
    from .margin_calculation import start_margin_calculation
    
    pair_callback = callback_query.data
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