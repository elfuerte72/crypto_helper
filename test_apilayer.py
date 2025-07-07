#!/usr/bin/env python3
"""
Тестовый скрипт для проверки интеграции APILayer
"""

import asyncio
import sys
import os

# Добавляем src в path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.fiat_rates_service import fiat_rates_service
from config import config


async def test_apilayer_integration():
    """Тестирование интеграции APILayer"""
    
    print("🔍 Тестирование интеграции APILayer...")
    print(f"API Key: {config.API_LAYER_KEY[:10]}...")
    print(f"API URL: {config.API_LAYER_URL}")
    print("-" * 50)
    
    try:
        # Инициализируем сервис
        async with fiat_rates_service as service:
            
            # 1. Health check
            print("1. Проверка здоровья APILayer...")
            health = await service.health_check()
            print(f"   Status: {health['status']}")
            print(f"   Response time: {health.get('response_time_ms', 'N/A')}ms")
            if health['status'] != 'healthy':
                print(f"   Error: {health.get('message', 'Unknown error')}")
                return False
            
            # 2. Тестирование базовых курсов
            print("\n2. Тестирование базовых курсов...")
            test_pairs = [
                ('USD', 'RUB'),
                ('USD', 'ZAR'),
                ('USD', 'THB'),
                ('USD', 'AED'),
                ('USD', 'IDR'),
                ('RUB', 'ZAR'),
                ('USDT', 'RUB')  # Это должно не работать, так как USDT не фиатная валюта
            ]
            
            for from_curr, to_curr in test_pairs:
                rate = await service.get_fiat_rate(from_curr, to_curr)
                if rate is not None:
                    print(f"   ✅ {from_curr}/{to_curr}: {rate:.6f}")
                else:
                    print(f"   ❌ {from_curr}/{to_curr}: не удалось получить курс")
            
            # 3. Тестирование ExchangeRate объектов
            print("\n3. Тестирование ExchangeRate объектов...")
            exchange_rate = await service.get_fiat_exchange_rate('USD/RUB')
            if exchange_rate:
                print(f"   ✅ USD/RUB ExchangeRate:")
                print(f"      Pair: {exchange_rate.pair}")
                print(f"      Rate: {exchange_rate.rate}")
                print(f"      Source: {exchange_rate.source}")
                print(f"      Timestamp: {exchange_rate.timestamp}")
            else:
                print(f"   ❌ Не удалось создать ExchangeRate для USD/RUB")
            
            print("\n✅ Тестирование завершено успешно!")
            return True
            
    except Exception as e:
        print(f"\n❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_apilayer_integration())
    sys.exit(0 if success else 1)