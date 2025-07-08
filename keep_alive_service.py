#!/usr/bin/env python3
"""
Keep Alive Service for Heroku Bot
Pings the bot every 25 minutes to prevent it from sleeping on Eco plan
"""

import time
import requests
import schedule
from datetime import datetime

# URL вашего бота
BOT_URL = "https://crypto-helper-testing-7c5ffa6d9fbf.herokuapp.com"


def ping_bot():
    """Пингует бот чтобы он не уснул"""
    try:
        response = requests.get(f"{BOT_URL}/health/live", timeout=10)
        if response.status_code == 200:
            status = response.json()['status']
            print(f"✅ {datetime.now()}: Bot is alive - {status}")
        else:
            status_code = response.status_code
            timestamp = datetime.now()
            print(f"⚠️  {timestamp}: Bot responded with status {status_code}")
    except Exception as e:
        print(f"❌ {datetime.now()}: Failed to ping bot: {e}")


def main():
    """Основная функция - запускает пинги каждые 25 минут"""
    print("🚀 Starting Keep Alive Service for Crypto Helper Bot")
    print(f"📍 Target URL: {BOT_URL}")
    print("⏰ Will ping every 25 minutes to prevent sleeping")
    
    # Запланировать пинг каждые 25 минут
    schedule.every(25).minutes.do(ping_bot)
    
    # Первый пинг сразу
    ping_bot()
    
    # Бесконечный цикл
    while True:
        schedule.run_pending()
        time.sleep(60)  # Проверять каждую минуту


if __name__ == "__main__":
    main() 