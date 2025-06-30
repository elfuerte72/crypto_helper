#!/usr/bin/env python3
"""
Тестовый скрипт для проверки реального API Rapira (без debug режима)
"""

import asyncio
import sys
import os
from pathlib import Path

# Добавляем src в путь
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

from services.api_service import APIService, RapiraAPIError
from config import config
from utils.logger import get_api_logger

logger = get_api_logger()


async def test_real_api():
    """Тест реального API"""
    print("🌐 Тестируем реальный Rapira API...")
    
    # Временно отключаем debug режим
    original_debug = config.DEBUG_MODE
    config.DEBUG_MODE = False
    
    try:
        async with APIService() as api:
            # Health check
            print("🔍 Проверяем health check...")
            health = await api.health_check()
            print(f"   Статус: {health['status']}")
            print(f"   Время ответа: {health.get('response_time_ms', 'N/A')}ms")
            print(f"   Доступно курсов: {health.get('rates_available', 'N/A')}")
            
            if health['status'] != 'healthy':
                print(f"   Сообщение: {health.get('message', 'N/A')}")
                return False
            
            # Получение всех курсов
            print("\n📊 Получаем все курсы...")
            rates = await api.get_all_rates()
            
            if rates:
                print(f"   Получено {len(rates)} курсов")
                
                # Показываем несколько курсов
                count = 0
                for symbol, rate in rates.items():
                    if count >= 5:
                        break
                    print(f"   {symbol}: {rate.rate} (bid: {rate.bid}, ask: {rate.ask})")
                    count += 1
                
                # Проверяем конкретные пары
                print("\n💱 Проверяем конкретные пары...")
                test_pairs = ['USDT/RUB', 'BTC/USDT', 'ETH/USDT']
                
                for pair in test_pairs:
                    try:
                        rate = await api.get_exchange_rate(pair)
                        if rate:
                            print(f"   ✅ {pair}: {rate.rate} (source: {rate.source})")
                        else:
                            print(f"   ❌ {pair}: не найден")
                    except Exception as e:
                        print(f"   ❌ {pair}: ошибка - {e}")
                
                return True
            else:
                print("   ❌ Не удалось получить курсы")
                return False
                
    except Exception as e:
        print(f"❌ Ошибка тестирования реального API: {e}")
        return False
    finally:
        # Восстанавливаем debug режим
        config.DEBUG_MODE = original_debug


if __name__ == "__main__":
    try:
        success = asyncio.run(test_real_api())
        if success:
            print("\n🎉 Реальный API работает корректно!")
        else:
            print("\n⚠️  Проблемы с реальным API")
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Тест прерван пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        sys.exit(1)