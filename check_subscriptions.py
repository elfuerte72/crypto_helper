#!/usr/bin/env python3
"""
Скрипт для проверки статуса подписок APILayer
"""

import asyncio
import aiohttp
import sys
import os

# Добавляем src в path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import config

async def check_subscriptions():
    """Проверка статуса подписок APILayer"""
    
    print("📊 ПРОВЕРКА СТАТУСА ПОДПИСОК APILAYER")
    print("=" * 50)
    print(f"API Key: {config.API_LAYER_KEY}")
    print("=" * 50)
    
    headers = {
        'apikey': config.API_LAYER_KEY,
        'User-Agent': 'CryptoHelper-Bot/1.0'
    }
    
    async with aiohttp.ClientSession(headers=headers) as session:
        
        # Проверка 1: Exchange Rates Data API
        print("\n1. 📈 Exchange Rates Data API")
        print("-" * 30)
        
        endpoints = [
            ("/latest", "Текущие курсы"),
            ("/symbols", "Поддерживаемые валюты"),
            ("/convert", "Конвертация валют"),
            ("/historical", "Исторические данные")
        ]
        
        for endpoint, description in endpoints:
            try:
                url = f"{config.API_LAYER_URL}{endpoint}"
                params = {}
                
                # Добавляем параметры для конкретных endpoint'ов
                if endpoint == "/latest":
                    params = {'base': 'USD', 'symbols': 'RUB'}
                elif endpoint == "/convert":
                    params = {'from': 'USD', 'to': 'RUB', 'amount': 1}
                elif endpoint == "/historical":
                    params = {'date': '2024-01-01', 'base': 'USD', 'symbols': 'RUB'}
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('success'):
                            print(f"   ✅ {description}: Доступен")
                        else:
                            error = data.get('error', {})
                            print(f"   ❌ {description}: {error.get('info', 'Ошибка API')}")
                    elif response.status == 403:
                        print(f"   🔒 {description}: Требуется подписка")
                    elif response.status == 401:
                        print(f"   🚫 {description}: Неверный API ключ")
                    else:
                        print(f"   ❌ {description}: HTTP {response.status}")
                        
            except Exception as e:
                print(f"   ❌ {description}: Ошибка - {e}")
        
        # Проверка 2: Currency Data API
        print("\n2. 💰 Currency Data API")
        print("-" * 30)
        
        endpoints = [
            ("/list", "Список валют"),
            ("/live", "Курсы в реальном времени"),
            ("/historical", "Исторические курсы"),
            ("/change", "Изменения курсов"),
            ("/timeframe", "Курсы за период")
        ]
        
        for endpoint, description in endpoints:
            try:
                url = f"https://api.apilayer.com/currency_data{endpoint}"
                params = {}
                
                # Добавляем параметры для конкретных endpoint'ов
                if endpoint == "/live":
                    params = {'source': 'USD', 'currencies': 'RUB'}
                elif endpoint == "/historical":
                    params = {'date': '2024-01-01', 'source': 'USD', 'currencies': 'RUB'}
                elif endpoint == "/change":
                    params = {'source': 'USD', 'currencies': 'RUB', 'start_date': '2024-01-01', 'end_date': '2024-01-02'}
                elif endpoint == "/timeframe":
                    params = {'source': 'USD', 'currencies': 'RUB', 'start_date': '2024-01-01', 'end_date': '2024-01-02'}
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('success'):
                            print(f"   ✅ {description}: Доступен")
                        else:
                            error = data.get('error', {})
                            print(f"   ❌ {description}: {error.get('info', 'Ошибка API')}")
                    elif response.status == 403:
                        print(f"   🔒 {description}: Требуется подписка")
                    elif response.status == 401:
                        print(f"   🚫 {description}: Неверный API ключ")
                    else:
                        print(f"   ❌ {description}: HTTP {response.status}")
                        
            except Exception as e:
                print(f"   ❌ {description}: Ошибка - {e}")
        
        # Проверка 3: Получение детальной информации о подписке
        print("\n3. 📋 Детальная информация о подписке")
        print("-" * 30)
        
        try:
            # Пытаемся получить детали через основной endpoint
            url = f"{config.API_LAYER_URL}/latest"
            params = {'base': 'USD', 'symbols': 'RUB,EUR,ZAR,THB,AED,IDR,GBP,JPY,CAD,AUD,CHF,CNY'}
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('success'):
                        print("   ✅ Полный доступ к Exchange Rates Data API")
                        print(f"   • Базовая валюта: {data.get('base', 'N/A')}")
                        print(f"   • Дата: {data.get('date', 'N/A')}")
                        print(f"   • Получено курсов: {len(data.get('rates', {}))}")
                        print(f"   • Timestamp: {data.get('timestamp', 'N/A')}")
                    else:
                        error = data.get('error', {})
                        print(f"   ❌ Ограниченный доступ: {error.get('info', 'Неизвестная ошибка')}")
                else:
                    print(f"   ❌ Проблема с доступом: HTTP {response.status}")
                    error_text = await response.text()
                    print(f"   • Подробности: {error_text[:200]}...")
        except Exception as e:
            print(f"   ❌ Ошибка при проверке подписки: {e}")
        
        # Проверка 4: Тестирование лимитов
        print("\n4. 📊 Тестирование лимитов запросов")
        print("-" * 30)
        
        try:
            # Делаем несколько быстрых запросов
            for i in range(5):
                url = f"{config.API_LAYER_URL}/latest"
                params = {'base': 'USD', 'symbols': 'RUB'}
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        print(f"   ✅ Запрос {i+1}/5: Успешно")
                    elif response.status == 429:
                        print(f"   ⏳ Запрос {i+1}/5: Лимит запросов достигнут")
                        break
                    else:
                        print(f"   ❌ Запрос {i+1}/5: HTTP {response.status}")
                
                # Небольшая задержка между запросами
                await asyncio.sleep(0.1)
        except Exception as e:
            print(f"   ❌ Ошибка при тестировании лимитов: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Проверка подписок завершена!")
    print("\n💡 Рекомендации:")
    print("• Если видите 🔒 'Требуется подписка' - нужно активировать конкретный план")
    print("• Если видите 🚫 'Неверный API ключ' - проверьте ключ в .env файле")
    print("• Если видите ✅ 'Доступен' - API работает корректно")

if __name__ == "__main__":
    try:
        asyncio.run(check_subscriptions())
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        sys.exit(1)