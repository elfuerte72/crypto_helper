#!/usr/bin/env python3
"""
Тест исправления фиатных валютных пар
Проверяет работу fallback механизма для проблемных пар
"""

import asyncio
import sys
import os

# Добавляем путь к src для импорта модулей
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.api_service import api_service
from services.fiat_rates_service import fiat_rates_service
from utils.logger import get_api_logger

logger = get_api_logger()

# Проблемные пары из логов
PROBLEMATIC_PAIRS = [
    'RUB/THB', 'THB/RUB',
    'RUB/AED', 'AED/RUB', 
    'RUB/IDR', 'IDR/RUB',
    'RUB/EUR', 'EUR/RUB',
    'RUB/USD', 'USD/RUB'
]

async def test_fiat_service_fallback():
    """Тестируем fallback механизм в fiat_rates_service"""
    print("🧪 Тестирование fallback механизма fiat_rates_service...")
    
    async with fiat_rates_service:
        for pair in PROBLEMATIC_PAIRS:
            try:
                print(f"\n📊 Тестирование пары: {pair}")
                
                # Разбираем пару
                from_currency, to_currency = pair.split('/')
                
                # Тестируем получение курса с fallback
                rate = await fiat_rates_service.get_fiat_rate(from_currency, to_currency, use_fallback=True)
                
                if rate:
                    print(f"✅ {pair}: {rate:.6f}")
                    
                    # Тестируем создание ExchangeRate объекта
                    exchange_rate = await fiat_rates_service.get_fiat_exchange_rate(pair)
                    if exchange_rate:
                        print(f"   📈 ExchangeRate: {exchange_rate.rate:.6f} (source: {exchange_rate.source})")
                    else:
                        print(f"❌ Не удалось создать ExchangeRate для {pair}")
                else:
                    print(f"❌ {pair}: Курс не найден")
                    
            except Exception as e:
                print(f"❌ Ошибка при тестировании {pair}: {e}")

async def test_api_service_integration():
    """Тестируем интеграцию с api_service"""
    print("\n🔗 Тестирование интеграции с api_service...")
    
    async with api_service:
        for pair in PROBLEMATIC_PAIRS:
            try:
                print(f"\n📊 API тест для пары: {pair}")
                
                # Тестируем получение курса через api_service
                exchange_rate = await api_service.get_exchange_rate(pair)
                
                if exchange_rate:
                    print(f"✅ {pair}: {exchange_rate.rate:.6f} (source: {exchange_rate.source})")
                else:
                    print(f"❌ {pair}: Курс не найден через API service")
                    
            except Exception as e:
                print(f"❌ Ошибка API service для {pair}: {e}")

async def test_fallback_rates_coverage():
    """Тестируем покрытие fallback курсов"""
    print("\n📋 Тестирование покрытия fallback курсов...")
    
    async with fiat_rates_service:
        # Тестируем основные валюты
        base_currencies = ['USD', 'EUR', 'RUB', 'ZAR', 'THB', 'AED', 'IDR']
        
        for base_currency in base_currencies:
            print(f"\n💱 Fallback курсы для {base_currency}:")
            
            fallback_rates = await fiat_rates_service._get_fallback_rates(base_currency)
            
            if fallback_rates:
                for target_currency, rate in fallback_rates.items():
                    print(f"   {base_currency}/{target_currency}: {rate:.6f}")
            else:
                print(f"   ❌ Нет fallback курсов для {base_currency}")

async def test_cache_functionality():
    """Тестируем функциональность кэша"""
    print("\n🗄️ Тестирование кэша...")
    
    async with fiat_rates_service:
        # Очищаем кэш
        if hasattr(fiat_rates_service, '_cache'):
            fiat_rates_service._cache.clear()
        
        print("📝 Тестируем кэширование USD курсов...")
        
        # Первый запрос - должен попасть в fallback и закэшироваться
        rates1 = await fiat_rates_service._get_fallback_rates('USD')
        await fiat_rates_service._cache_rates('USD', rates1)
        
        # Второй запрос - должен использовать кэш
        cached_rates = await fiat_rates_service._get_cached_rates('USD')
        
        if cached_rates:
            print("✅ Кэш работает корректно")
            print(f"   Закэшировано курсов: {len(cached_rates)}")
        else:
            print("❌ Кэш не работает")

async def main():
    """Основная функция тестирования"""
    print("🚀 Запуск тестов исправления фиатных пар...\n")
    
    try:
        # Тест 1: Fallback механизм
        await test_fiat_service_fallback()
        
        # Тест 2: Интеграция с API service
        await test_api_service_integration()
        
        # Тест 3: Покрытие fallback курсов
        await test_fallback_rates_coverage()
        
        # Тест 4: Кэш
        await test_cache_functionality()
        
        print("\n🎉 Все тесты завершены!")
        
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())