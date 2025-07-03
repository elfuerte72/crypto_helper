#!/usr/bin/env python3
"""
Тестовый скрипт для проверки обновленных валютных пар после изменений
"""

import asyncio
import sys
import os

# Добавляем путь для импорта модулей проекта
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from services.api_service import APIService
    from handlers.currency_pairs import CURRENCY_PAIRS, get_all_currency_pairs
    from config import config
    from utils.logger import get_api_logger
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    sys.exit(1)

logger = get_api_logger()


async def test_updated_pairs():
    """Тестирование обновленных валютных пар"""
    print("=" * 60)
    print("🚀 ТЕСТИРОВАНИЕ ОБНОВЛЕННЫХ ВАЛЮТНЫХ ПАР")
    print("=" * 60)
    
    # Проверяем новые валютные пары из handlers
    print("\n📋 Новые валютные пары из handlers/currency_pairs.py:")
    pairs = get_all_currency_pairs()
    for key, pair_info in pairs.items():
        print(f"  {key}: {pair_info['name']} {pair_info['emoji']} - {pair_info['description']}")
    
    # Проверяем конфигурацию
    print(f"\n📋 Поддерживаемые пары в config.py ({len(config.SUPPORTED_PAIRS)}):")
    for i, pair in enumerate(config.SUPPORTED_PAIRS, 1):
        print(f"  {i:2d}. {pair}")
    
    # Тестируем API сервис
    print("\n🔍 Тестирование API сервиса...")
    
    async with APIService() as api:
        # Получаем все курсы от Rapira
        all_rates = await api.get_all_rates()
        
        if not all_rates:
            print("❌ Не удалось получить курсы от Rapira API")
            return
        
        print(f"✅ Получено {len(all_rates)} курсов от Rapira API")
        
        # Тестируем каждую пару из конфигурации
        print("\n🧪 Тестирование каждой пары:")
        
        for pair in config.SUPPORTED_PAIRS:
            try:
                rate = await api.get_exchange_rate(pair)
                if rate:
                    if rate.rate > 1:
                        print(f"  ✅ {pair}: {rate.rate:.2f} (источник: {rate.source})")
                    else:
                        print(f"  ✅ {pair}: {rate.rate:.8f} (источник: {rate.source})")
                else:
                    print(f"  ❌ {pair}: курс не найден")
            except Exception as e:
                print(f"  ❌ {pair}: ошибка - {e}")
    
    print("\n✅ Тестирование завершено!")


if __name__ == "__main__":
    asyncio.run(test_updated_pairs())