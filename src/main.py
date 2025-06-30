#!/usr/bin/env python3
"""
Crypto Helper Telegram Bot - MVP
Minimal proof of concept for technology validation
"""

import asyncio
import logging
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Bot configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required")

# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(Command('start'))
async def start_handler(message: Message):
    """Handle /start command - Hello World test"""
    await message.reply(
        "🚀 Crypto Helper Bot is running!\n"
        "This is a technology validation test.\n"
        "Bot is working correctly with Aiogram 3.x"
    )


@dp.message(Command('test'))
async def test_handler(message: Message):
    """Handle /test command - Basic functionality test"""
    await message.reply(
        "✅ Test successful!\n"
        f"Chat ID: {message.chat.id}\n"
        f"User ID: {message.from_user.id}\n"
        f"Username: @{message.from_user.username or 'N/A'}"
    )


async def main():
    """Main function to start the bot"""
    logger.info("Starting Crypto Helper Bot...")
    
    try:
        # Start polling
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
    finally:
        await bot.session.close()


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