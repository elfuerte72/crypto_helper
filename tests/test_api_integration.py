#!/usr/bin/env python3
"""
Тестовый скрипт для проверки интеграции с Rapira API
Запускает базовые тесты API сервиса
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


async def test_health_check():
    """Тест проверки состояния API"""
    print("🔍 Тестируем health check...")
    
    async with APIService() as api:
        try:
            health = await api.health_check()
            print(f"✅ Health check: {health['status']}")
            print(f"   Время ответа: {health.get('response_time_ms', 'N/A')}ms")
            print(f"   Сообщение: {health.get('message', 'N/A')}")
            print(f"   Доступно курсов: {health.get('rates_available', 'N/A')}")
            return True
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return False


async def test_get_all_rates():
    """Тест получения всех курсов"""
    print("\n📊 Тестируем получение всех курсов...")
    
    async with APIService() as api:
        try:
            rates = await api.get_all_rates()
            if rates:
                print(f"✅ Получено {len(rates)} курсов")
                
                # Показываем первые 5 курсов
                for i, (symbol, rate) in enumerate(rates.items()):
                    if i >= 5:
                        break
                    print(f"   {symbol}: {rate.rate} (source: {rate.source})")
                
                if len(rates) > 5:
                    print(f"   ... и еще {len(rates) - 5} курсов")
                
                return True
            else:
                print("❌ Не удалось получить курсы")
                return False
        except Exception as e:
            print(f"❌ Ошибка получения курсов: {e}")
            return False


async def test_specific_pairs():
    """Тест получения конкретных валютных пар"""
    print("\n💱 Тестируем получение конкретных валютных пар...")
    
    test_pairs = ['USDT/RUB', 'BTC/USDT', 'ETH/USDT', 'RUB/ZAR', 'USDT/THB']
    
    async with APIService() as api:
        results = []
        for pair in test_pairs:
            try:
                rate = await api.get_exchange_rate(pair)
                if rate:
                    print(f"✅ {pair}: {rate.rate} (source: {rate.source})")
                    results.append(True)
                else:
                    print(f"❌ {pair}: не найден")
                    results.append(False)
            except RapiraAPIError as e:
                print(f"❌ {pair}: API ошибка - {e}")
                results.append(False)
            except Exception as e:
                print(f"❌ {pair}: неожиданная ошибка - {e}")
                results.append(False)
        
        success_count = sum(results)
        print(f"\n📈 Успешно получено {success_count}/{len(test_pairs)} курсов")
        return success_count > 0


async def test_multiple_rates():
    """Тест получения нескольких курсов одновременно"""
    print("\n🔄 Тестируем параллельное получение курсов...")
    
    test_pairs = ['USDT/RUB', 'BTC/USDT', 'ETH/USDT']
    
    async with APIService() as api:
        try:
            rates = await api.get_multiple_rates(test_pairs)
            
            success_count = sum(1 for rate in rates.values() if rate is not None)
            print(f"✅ Получено {success_count}/{len(test_pairs)} курсов параллельно")
            
            for pair, rate in rates.items():
                if rate:
                    print(f"   {pair}: {rate.rate}")
                else:
                    print(f"   {pair}: не получен")
            
            return success_count > 0
        except Exception as e:
            print(f"❌ Ошибка параллельного получения: {e}")
            return False


async def run_all_tests():
    """Запуск всех тестов"""
    print("🚀 Запуск тестов интеграции с Rapira API")
    print(f"🔧 Режим отладки: {config.DEBUG_MODE}")
    print(f"🌐 API URL: {config.RAPIRA_API_URL}")
    print("=" * 60)
    
    tests = [
        ("Health Check", test_health_check),
        ("Получение всех курсов", test_get_all_rates),
        ("Конкретные валютные пары", test_specific_pairs),
        ("Параллельное получение", test_multiple_rates),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Критическая ошибка в тесте '{test_name}': {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("📋 РЕЗУЛЬТАТЫ ТЕСТОВ:")
    
    for i, (test_name, _) in enumerate(tests):
        status = "✅ ПРОЙДЕН" if results[i] else "❌ ПРОВАЛЕН"
        print(f"   {test_name}: {status}")
    
    passed = sum(results)
    total = len(results)
    
    print(f"\n🎯 Итого: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 Все тесты успешно пройдены!")
        return True
    elif passed > 0:
        print("⚠️  Некоторые тесты провалены, но интеграция частично работает")
        return True
    else:
        print("💥 Все тесты провалены - интеграция не работает")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Тесты прерваны пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        sys.exit(1)