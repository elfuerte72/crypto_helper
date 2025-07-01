#!/usr/bin/env python3
"""
Crypto Helper Telegram Bot - Main Bot Module
Production-ready bot implementation with proper structure
"""

import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command

try:
    from .config import config
    from .utils.logger import get_bot_logger
    from .handlers.admin_handlers import admin_router
    from .handlers.bot_handlers import margin_router  # Обновленный импорт
except ImportError:
    # Handle direct execution
    import sys
    import os
    sys.path.insert(0, os.path.dirname(__file__))
    from config import config
    from utils.logger import get_bot_logger
    from handlers.admin_handlers import admin_router
    from handlers.bot_handlers import margin_router  # Обновленный импорт

# Initialize logger
logger = get_bot_logger()


class CryptoHelperBot:
    """Main bot class with proper initialization and error handling"""
    
    def __init__(self):
        """Initialize bot instance"""
        self.bot = Bot(token=config.BOT_TOKEN)
        self.dp = Dispatcher()
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup message handlers"""
        # Include admin router
        self.dp.include_router(admin_router)
        
        # Include margin calculation router
        self.dp.include_router(margin_router)
        
        # Basic command handlers
        self.dp.message(Command('start'))(self.start_handler)
        self.dp.message(Command('test'))(self.test_handler)
        self.dp.message(Command('help'))(self.help_handler)
    
    async def start_handler(self, message: Message):
        """Handle /start command"""
        logger.info(f"Start command from user {message.from_user.id}")
        
        welcome_text = (
            "🚀 <b>Crypto Helper Bot</b>\n\n"
            "Добро пожаловать в бота для автоматизации курсов криптовалют!\n\n"
            "📋 <b>Доступные команды:</b>\n"
            "/start - Показать это сообщение\n"
            "/help - Справка по командам\n"
            "/test - Тестовая команда\n"
            "/admin_bot - Панель администратора\n\n"
            "🔧 <b>Статус:</b> MVP версия в разработке"
        )
        
        await message.reply(welcome_text, parse_mode='HTML')
    
    async def test_handler(self, message: Message):
        """Handle /test command"""
        logger.info(f"Test command from user {message.from_user.id}")
        
        test_info = (
            "✅ <b>Тест успешен!</b>\n\n"
            f"🆔 Chat ID: <code>{message.chat.id}</code>\n"
            f"👤 User ID: <code>{message.from_user.id}</code>\n"
            f"📝 Username: @{message.from_user.username or 'N/A'}\n"
            f"🌐 Chat Type: {message.chat.type}\n"
            f"⚙️ Debug Mode: {'Включен' if config.DEBUG_MODE else 'Выключен'}"
        )
        
        await message.reply(test_info, parse_mode='HTML')
    
    async def help_handler(self, message: Message):
        """Handle /help command"""
        logger.info(f"Help command from user {message.from_user.id}")
        
        help_text = (
            "📚 <b>Справка по Crypto Helper Bot</b>\n\n"
            "🎯 <b>Назначение:</b>\n"
            "Бот для автоматизации получения курсов криптовалют "
            "и расчета наценки для менеджеров.\n\n"
            "💱 <b>Поддерживаемые пары:</b>\n"
            "• USDT/ZAR, ZAR/USDT\n"
            "• USDT/THB, THB/USDT\n"
            "• USDT/AED, AED/USDT\n"
            "• USDT/IDR, IDR/USDT\n"
            "• USDT/RUB, RUB/USDT\n\n"
            "⚡ <b>Команды:</b>\n"
            "/start - Начало работы\n"
            "/help - Эта справка\n"
            "/test - Тестовая информация\n"
            "/admin_bot - Административная панель\n\n"
            "🔧 <b>Статус:</b> MVP в разработке"
        )
        
        await message.reply(help_text, parse_mode='HTML')
    
    async def start(self):
        """Start the bot"""
        logger.info("🚀 Starting Crypto Helper Bot...")
        logger.info(f"Debug mode: {config.DEBUG_MODE}")
        logger.info(f"Supported pairs: {len(config.SUPPORTED_PAIRS)}")
        
        try:
            # Get bot info
            bot_info = await self.bot.get_me()
            logger.info(f"Bot info: @{bot_info.username} ({bot_info.first_name})")
            
            # Start polling
            logger.info("Starting polling...")
            await self.dp.start_polling(self.bot)
            
        except Exception as e:
            logger.error(f"Error starting bot: {e}")
            raise
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up bot resources...")
        await self.bot.session.close()


async def main():
    """Main function to run the bot"""
    try:
        # Validate configuration
        config.validate()
        
        # Create and start bot
        bot = CryptoHelperBot()
        await bot.start()
        
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        return 0
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == '__main__':
    print("🤖 Crypto Helper Bot - Production Version")
    print("=" * 50)
    
    try:
        exit_code = asyncio.run(main())
        exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
        exit(0)