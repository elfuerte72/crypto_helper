#!/usr/bin/env python3
"""
Быстрая проверка работоспособности APILayer подписок
"""

import asyncio
import aiohttp
import sys
import os

# Добавляем src в path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import config

async def quick_test():
    """Быстрая проверка APILayer"""
    
    print("⚡ БЫСТРАЯ ПРОВЕРКА APILAYER")
    print("=" * 40)
    print(f"API Key: {config.API_LAYER_KEY[:10]}...")
    print("=" * 40)
    
    headers = {
        'apikey': config.API_LAYER_KEY,
        'User-Agent': 'CryptoHelper-Bot/1.0'
    }
    
    async with aiohttp.ClientSession(headers=headers) as session:
        
        # Тест 1: Exchange Rates Data API
        print("\n1. Exchange Rates Data API:")
        try:
            url = f"{config.API_LAYER_URL}/latest"
            params = {'base': 'USD', 'symbols': 'RUB,EUR,ZAR,THB,AED,IDR'}
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('success'):
                        rates = data.get('rates', {})
                        print(f"   ✅ Работает! Получено {len(rates)} курсов")
                        for curr, rate in list(rates.items())[:3]:
                            print(f"   • USD/{curr}: {rate:.6f}")
                    else:
                        error = data.get('error', {})
                        print(f"   ❌ Ошибка: {error.get('info', 'Unknown')}")
                else:
                    print(f"   ❌ HTTP Error: {response.status}")
                    error_text = await response.text()
                    print(f"   • {error_text}")
        except Exception as e:
            print(f"   ❌ Исключение: {e}")
        
        # Тест 2: Currency Data API
        print("\n2. Currency Data API:")
        try:
            url = "https://api.apilayer.com/currency_data/live"
            params = {'source': 'USD', 'currencies': 'RUB,EUR,ZAR'}
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('success'):
                        quotes = data.get('quotes', {})
                        print(f"   ✅ Работает! Получено {len(quotes)} курсов")
                        for quote, rate in list(quotes.items())[:3]:
                            print(f"   • {quote}: {rate:.6f}")
                    else:
                        error = data.get('error', {})
                        print(f"   ❌ Ошибка: {error.get('info', 'Unknown')}")
                else:
                    print(f"   ❌ HTTP Error: {response.status}")
                    error_text = await response.text()
                    print(f"   • {error_text}")
        except Exception as e:
            print(f"   ❌ Исключение: {e}")
        
        # Тест 3: Интегрированный сервис
        print("\n3. Интегрированный Fiat Service:")
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
            from services.fiat_rates_service import fiat_rates_service
            
            async with fiat_rates_service as service:
                rate = await service.get_fiat_rate('USD', 'RUB')
                if rate:
                    print(f"   ✅ Работает! USD/RUB: {rate:.6f}")
                else:
                    print(f"   ❌ Не удалось получить курс")
        except Exception as e:
            print(f"   ❌ Исключение: {e}")
    
    print("\n" + "=" * 40)
    print("✅ Быстрая проверка завершена!")

if __name__ == "__main__":
    try:
        asyncio.run(quick_test())
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        sys.exit(1)