#!/usr/bin/env python3
"""
Диагностика соединения с API Layer
Проверяет доступность API и правильность конфигурации
"""

import asyncio
import sys
import os
import json
import aiohttp
from datetime import datetime

# Добавляем путь к src для импорта модулей
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import config
from services.fiat_rates_service import fiat_rates_service
from utils.logger import get_api_logger

logger = get_api_logger()

async def test_api_layer_connection():
    """Тестируем прямое соединение с API Layer"""
    print("🔍 Тестирование прямого соединения с API Layer...")
    
    if not config.API_LAYER_KEY:
        print("❌ API_LAYER_KEY не настроен в конфигурации")
        return False
    
    print(f"🔗 URL: {config.API_LAYER_URL}")
    print(f"🔑 API Key: {config.API_LAYER_KEY[:10]}...")
    
    headers = {
        'apikey': config.API_LAYER_KEY,
        'Accept': 'application/json'
    }
    
    # Тестируем простой запрос
    test_url = f"{config.API_LAYER_URL}/latest"
    params = {
        'base': 'USD',
        'symbols': 'EUR,RUB,ZAR'
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            print(f"📡 Отправляем запрос: {test_url}")
            print(f"📋 Параметры: {params}")
            
            async with session.get(test_url, params=params, headers=headers) as response:
                print(f"📊 Статус ответа: {response.status}")
                print(f"📄 Заголовки ответа: {dict(response.headers)}")
                
                if response.status == 200:
                    data = await response.json()
                    print("✅ Успешный ответ от API Layer:")
                    print(json.dumps(data, indent=2, ensure_ascii=False))
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ Ошибка API Layer ({response.status}): {error_text}")
                    return False
                    
    except Exception as e:
        print(f"💥 Ошибка соединения: {e}")
        return False

async def test_fiat_service_health():
    """Тестируем health check fiat_rates_service"""
    print("\n🏥 Тестирование health check fiat_rates_service...")
    
    try:
        async with fiat_rates_service:
            health_data = await fiat_rates_service.health_check()
            
            print("📊 Результат health check:")
            print(json.dumps(health_data, indent=2, ensure_ascii=False))
            
            return health_data.get('status') == 'healthy'
            
    except Exception as e:
        print(f"💥 Ошибка health check: {e}")
        return False

async def test_problematic_pairs():
    """Тестируем проблемные пары"""
    print("\n🧪 Тестирование проблемных пар...")
    
    problematic_pairs = [
        'RUB/THB', 'THB/RUB',
        'RUB/AED', 'AED/RUB', 
        'RUB/IDR', 'IDR/RUB',
        'RUB/EUR', 'EUR/RUB',
        'RUB/USD', 'USD/RUB'
    ]
    
    results = {}
    
    async with fiat_rates_service:
        for pair in problematic_pairs:
            try:
                print(f"\n📊 Тестирование пары: {pair}")
                
                from_currency, to_currency = pair.split('/')
                
                # Пытаемся получить курс без fallback
                rate_no_fallback = await fiat_rates_service.get_fiat_rate(
                    from_currency, to_currency, use_fallback=False
                )
                
                # Пытаемся получить курс с fallback
                rate_with_fallback = await fiat_rates_service.get_fiat_rate(
                    from_currency, to_currency, use_fallback=True
                )
                
                results[pair] = {
                    'no_fallback': rate_no_fallback,
                    'with_fallback': rate_with_fallback
                }
                
                if rate_no_fallback:
                    print(f"✅ Реальный API: {rate_no_fallback:.6f}")
                else:
                    print("❌ Реальный API: не доступен")
                
                if rate_with_fallback:
                    print(f"✅ С fallback: {rate_with_fallback:.6f}")
                else:
                    print("❌ С fallback: не работает")
                    
            except Exception as e:
                print(f"💥 Ошибка для {pair}: {e}")
                results[pair] = {'error': str(e)}
    
    return results

async def test_fallback_data_integrity():
    """Проверяем целостность fallback данных"""
    print("\n🔍 Проверка целостности fallback данных...")
    
    async with fiat_rates_service:
        base_currencies = ['USD', 'EUR', 'RUB', 'ZAR', 'THB', 'AED', 'IDR']
        
        for base_currency in base_currencies:
            print(f"\n💱 Проверка fallback для {base_currency}:")
            
            fallback_rates = await fiat_rates_service._get_fallback_rates(base_currency)
            
            if not fallback_rates:
                print(f"❌ Нет fallback данных для {base_currency}")
                continue
            
            # Проверяем, что есть курсы для всех поддерживаемых валют
            supported_currencies = fiat_rates_service.supported_currencies
            missing_currencies = supported_currencies - set(fallback_rates.keys()) - {base_currency}
            
            if missing_currencies:
                print(f"⚠️  Отсутствуют курсы для: {missing_currencies}")
            else:
                print(f"✅ Все курсы присутствуют ({len(fallback_rates)} валют)")
            
            # Проверяем разумность курсов
            for currency, rate in fallback_rates.items():
                if rate <= 0:
                    print(f"❌ Неверный курс {base_currency}/{currency}: {rate}")
                elif rate > 1000000:  # Очень большой курс
                    print(f"⚠️  Подозрительно большой курс {base_currency}/{currency}: {rate}")

async def generate_config_recommendations():
    """Генерируем рекомендации по конфигурации"""
    print("\n📋 Рекомендации по конфигурации:")
    
    print(f"🔑 API_LAYER_KEY: {'✅ Настроен' if config.API_LAYER_KEY else '❌ Не настроен'}")
    print(f"🔗 API_LAYER_URL: {config.API_LAYER_URL}")
    print(f"⏱️  API_TIMEOUT: {config.API_TIMEOUT}s")
    print(f"🔄 API_RETRY_COUNT: {config.API_RETRY_COUNT}")
    print(f"🧪 USE_MOCK_DATA: {config.USE_MOCK_DATA}")
    
    if not config.API_LAYER_KEY:
        print("\n⚠️  ВАЖНО: Установите API_LAYER_KEY в .env файле")
        print("   Получить ключ можно на: https://apilayer.com/marketplace/exchangerates_data-api")
    
    if config.API_TIMEOUT < 30:
        print("\n⚠️  Рекомендуется увеличить API_TIMEOUT до 30 секунд")
    
    if config.API_RETRY_COUNT < 3:
        print("\n⚠️  Рекомендуется установить API_RETRY_COUNT = 3")

async def main():
    """Основная функция диагностики"""
    print("🚀 Запуск диагностики API Layer...\n")
    print(f"⏰ Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 1. Проверяем конфигурацию
        await generate_config_recommendations()
        
        # 2. Тестируем прямое соединение
        api_connection_ok = await test_api_layer_connection()
        
        # 3. Тестируем health check
        health_ok = await test_fiat_service_health()
        
        # 4. Тестируем проблемные пары
        pair_results = await test_problematic_pairs()
        
        # 5. Проверяем fallback данные
        await test_fallback_data_integrity()
        
        # Итоговый отчет
        print("\n" + "="*50)
        print("📊 ИТОГОВЫЙ ОТЧЕТ")
        print("="*50)
        print(f"🔗 API Layer соединение: {'✅ OK' if api_connection_ok else '❌ FAIL'}")
        print(f"🏥 Health check: {'✅ OK' if health_ok else '❌ FAIL'}")
        
        successful_pairs = sum(1 for result in pair_results.values() 
                             if result.get('with_fallback') is not None)
        total_pairs = len(pair_results)
        print(f"📊 Работающие пары: {successful_pairs}/{total_pairs}")
        
        if not api_connection_ok:
            print("\n⚠️  РЕКОМЕНДАЦИИ:")
            print("1. Проверьте API_LAYER_KEY в .env файле")
            print("2. Убедитесь в доступности интернета")
            print("3. Проверьте лимиты API Layer")
        
        if successful_pairs < total_pairs:
            print("\n⚠️  Некоторые пары не работают даже с fallback")
            print("   Это может указывать на проблемы в fallback данных")
        
        print("\n🎉 Диагностика завершена!")
        
    except Exception as e:
        print(f"\n💥 Критическая ошибка диагностики: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())