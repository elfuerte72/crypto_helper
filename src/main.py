#!/usr/bin/env python3
"""
Crypto Helper Telegram Bot - MVP
Основной файл бота с интеграцией всех модулей
"""

import asyncio
import logging
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage

# Import configuration and handlers
from config import config
from utils.logger import get_bot_logger
from handlers.admin_handlers import admin_router
from handlers.margin_calculation import margin_router

# Initialize logger
logger = get_bot_logger()

# Initialize bot and dispatcher with FSM storage
bot = Bot(token=config.BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


# Include routers
dp.include_router(admin_router)
dp.include_router(margin_router)


@dp.message(Command('start'))
async def start_handler(message: Message):
    """Handle /start command - Welcome message"""
    await message.reply(
        "🚀 <b>Crypto Helper Bot</b>\n\n"
        "Добро пожаловать в бот для расчета курсов криптовалют!\n\n"
        "📊 <b>Доступные команды:</b>\n"
        "• /admin_bot - Панель управления (только для администраторов)\n"
        "• /start - Показать это сообщение\n"
        "• /help - Справка по использованию\n\n"
        "💡 <i>Для доступа к функциям бота используйте команду /admin_bot</i>",
        parse_mode='HTML'
    )


@dp.message(Command('help'))
async def help_handler(message: Message):
    """Handle /help command - Help information"""
    await message.reply(
        "📖 <b>Справка по использованию</b>\n\n"
        "🔧 <b>Административные функции:</b>\n"
        "• /admin_bot - Доступ к панели управления\n"
        "  (только для администраторов канала)\n\n"
        "💱 <b>Функциональность:</b>\n"
        "• Выбор валютных пар (RUB, USDT, криптовалюты)\n"
        "• Получение актуальных курсов через Rapira API\n"
        "• Расчет курса с процентной наценкой\n"
        "• Форматирование результатов для публикации\n\n"
        "🌐 <b>Поддерживаемые направления:</b>\n"
        "• RUB ↔ ZAR, THB, AED, IDR\n"
        "• USDT ↔ ZAR, THB, AED, IDR\n"
        "• Основные криптовалютные пары\n\n"
        "⚙️ <b>Технические детали:</b>\n"
        "• Курсы обновляются в реальном времени\n"
        "• Поддержка положительных и отрицательных наценок\n"
        "• Точные расчеты с округлением до 8 знаков\n\n"
        "❓ Если у вас есть вопросы, обратитесь к администратору.",
        parse_mode='HTML'
    )


async def main():
    """Main function to start the bot"""
    logger.info("🚀 Запуск Crypto Helper Bot...")
    logger.info(f"📊 Режим отладки: {config.DEBUG_MODE}")
    logger.info(f"🔗 Rapira API URL: {config.RAPIRA_API_URL}")
    logger.info(f"📋 Поддерживаемых пар: {len(config.SUPPORTED_PAIRS)}")
    
    try:
        # Start polling
        logger.info("🔄 Начало polling...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"❌ Ошибка запуска бота: {e}")
        raise
    finally:
        await bot.session.close()
        logger.info("🛑 Бот остановлен")


if __name__ == '__main__':
    print("🤖 Crypto Helper Bot - Technology Validation")
    print("=" * 50)
    print("Testing Aiogram 3.x integration...")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")