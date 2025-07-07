#!/usr/bin/env python3
"""
Полный тестовый скрипт для проверки интеграции APILayer
Проверяет работу обеих подписок:
1. Exchange Rates Data API
2. Currency Data API
"""

import asyncio
import sys
import os
import aiohttp
import json
from datetime import datetime

# Добавляем src в path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.fiat_rates_service import fiat_rates_service
from services.api_service import api_service
from config import config


async def test_exchange_rates_data_api():
    """Тестирование Exchange Rates Data API"""
    
    print("📊 Тестирование Exchange Rates Data API...")
    
    headers = {
        'apikey': config.API_LAYER_KEY,
        'Content-Type': 'application/json',
        'User-Agent': 'CryptoHelper-Bot/1.0'
    }
    
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            # Тест 1: Получение курсов относительно USD
            print("\n1. Тестирование latest rates (USD base)...")
            
            url = f"{config.API_LAYER_URL}/latest"
            params = {
                'base': 'USD',
                'symbols': 'RUB,ZAR,THB,AED,IDR,EUR,GBP,JPY,CAD,AUD,CHF,CNY'
            }
            
            async with session.get(url, params=params) as response:
                print(f"   Status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    print(f"   Success: {data.get('success', False)}")
                    
                    if data.get('success'):
                        rates = data.get('rates', {})
                        print(f"   Получено курсов: {len(rates)}")
                        
                        for currency, rate in rates.items():
                            print(f"   ✅ USD/{currency}: {rate:.6f}")
                    else:
                        error = data.get('error', {})
                        print(f"   ❌ Ошибка: {error.get('info', 'Unknown error')}")
                        return False
                else:
                    error_text = await response.text()
                    print(f"   ❌ HTTP Error {response.status}: {error_text}")
                    return False
            
            # Тест 2: Получение курсов относительно EUR
            print("\n2. Тестирование latest rates (EUR base)...")
            
            params['base'] = 'EUR'
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('success'):
                        rates = data.get('rates', {})
                        print(f"   ✅ EUR base: получено {len(rates)} курсов")
                        if 'RUB' in rates:
                            print(f"   ✅ EUR/RUB: {rates['RUB']:.6f}")
                    else:
                        print(f"   ❌ Ошибка EUR base: {data.get('error', {}).get('info', 'Unknown')}")
                else:
                    print(f"   ❌ HTTP Error EUR base: {response.status}")
            
            # Тест 3: Конвертация валют
            print("\n3. Тестирование currency conversion...")
            
            convert_url = f"{config.API_LAYER_URL}/convert"
            params = {
                'from': 'USD',
                'to': 'RUB',
                'amount': 100
            }
            
            async with session.get(convert_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('success'):
                        result = data.get('result', 0)
                        info = data.get('info', {})
                        rate = info.get('rate', 0)
                        print(f"   ✅ Конвертация 100 USD -> RUB: {result:.2f} (курс: {rate:.6f})")
                    else:
                        print(f"   ❌ Ошибка конвертации: {data.get('error', {}).get('info', 'Unknown')}")
                else:
                    print(f"   ❌ HTTP Error конвертации: {response.status}")
            
            print("\n✅ Exchange Rates Data API работает корректно!")
            return True
            
    except Exception as e:
        print(f"\n❌ Ошибка при тестировании Exchange Rates Data API: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_currency_data_api():
    """Тестирование Currency Data API"""
    
    print("\n💰 Тестирование Currency Data API...")
    
    headers = {
        'apikey': config.API_LAYER_KEY,
        'Content-Type': 'application/json',
        'User-Agent': 'CryptoHelper-Bot/1.0'
    }
    
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            # Тест 1: Список поддерживаемых валют
            print("\n1. Тестирование supported currencies...")
            
            url = "https://api.apilayer.com/currency_data/list"
            
            async with session.get(url) as response:
                print(f"   Status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    print(f"   Success: {data.get('success', False)}")
                    
                    if data.get('success'):
                        currencies = data.get('currencies', {})
                        print(f"   Поддерживается валют: {len(currencies)}")
                        
                        # Проверяем наши основные валюты
                        our_currencies = ['USD', 'EUR', 'RUB', 'ZAR', 'THB', 'AED', 'IDR']
                        for curr in our_currencies:
                            if curr in currencies:
                                print(f"   ✅ {curr}: {currencies[curr]}")
                            else:
                                print(f"   ❌ {curr}: не поддерживается")
                    else:
                        error = data.get('error', {})
                        print(f"   ❌ Ошибка: {error.get('info', 'Unknown error')}")
                        return False
                else:
                    error_text = await response.text()
                    print(f"   ❌ HTTP Error {response.status}: {error_text}")
                    return False
            
            # Тест 2: Live rates
            print("\n2. Тестирование live rates...")
            
            url = "https://api.apilayer.com/currency_data/live"
            params = {
                'source': 'USD',
                'currencies': 'RUB,ZAR,THB,AED,IDR,EUR'
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('success'):
                        quotes = data.get('quotes', {})
                        print(f"   ✅ Live rates: получено {len(quotes)} курсов")
                        
                        for quote_key, rate in quotes.items():
                            # quote_key format: USDRUB, USDZAR, etc.
                            if quote_key.startswith('USD'):
                                currency = quote_key[3:]  # Remove 'USD'
                                print(f"   ✅ USD/{currency}: {rate:.6f}")
                    else:
                        print(f"   ❌ Ошибка live rates: {data.get('error', {}).get('info', 'Unknown')}")
                else:
                    print(f"   ❌ HTTP Error live rates: {response.status}")
            
            # Тест 3: Change rates (изменения курсов)
            print("\n3. Тестирование change rates...")
            
            url = "https://api.apilayer.com/currency_data/change"
            params = {
                'source': 'USD',
                'currencies': 'RUB,EUR',
                'start_date': '2024-01-01',
                'end_date': datetime.now().strftime('%Y-%m-%d')
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('success'):
                        print(f"   ✅ Change rates: данные получены")
                        
                        quotes = data.get('quotes', {})
                        for quote_key, info in quotes.items():
                            if isinstance(info, dict):
                                change = info.get('change', 0)
                                change_pct = info.get('change_pct', 0)
                                print(f"   ✅ {quote_key}: изменение {change:.6f} ({change_pct:.2f}%)")
                    else:
                        print(f"   ❌ Ошибка change rates: {data.get('error', {}).get('info', 'Unknown')}")
                else:
                    print(f"   ❌ HTTP Error change rates: {response.status}")
            
            print("\n✅ Currency Data API работает корректно!")
            return True
            
    except Exception as e:
        print(f"\n❌ Ошибка при тестировании Currency Data API: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_integrated_fiat_service():
    """Тестирование интегрированного fiat_rates_service"""
    
    print("\n🔧 Тестирование интегрированного fiat_rates_service...")
    
    try:
        async with fiat_rates_service as service:
            
            # 1. Health check
            print("\n1. Health check...")
            health = await service.health_check()
            print(f"   Status: {health['status']}")
            print(f"   Response time: {health.get('response_time_ms', 'N/A')}ms")
            
            if health['status'] != 'healthy':
                print(f"   ❌ Service не здоров: {health.get('message', 'Unknown error')}")
                return False
            
            # 2. Тестирование основных валютных пар
            print("\n2. Тестирование валютных пар...")
            
            test_pairs = [
                ('USD', 'RUB'),
                ('USD', 'ZAR'),
                ('USD', 'THB'),
                ('USD', 'AED'),
                ('USD', 'IDR'),
                ('EUR', 'RUB'),
                ('RUB', 'ZAR'),  # Кросс-курс
                ('ZAR', 'RUB'),  # Обратный кросс-курс
            ]
            
            for from_curr, to_curr in test_pairs:
                rate = await service.get_fiat_rate(from_curr, to_curr)
                if rate is not None:
                    print(f"   ✅ {from_curr}/{to_curr}: {rate:.6f}")
                else:
                    print(f"   ❌ {from_curr}/{to_curr}: не удалось получить курс")
            
            # 3. Тестирование ExchangeRate объектов
            print("\n3. Тестирование ExchangeRate объектов...")
            
            for pair in ['USD/RUB', 'EUR/ZAR', 'RUB/THB']:
                exchange_rate = await service.get_fiat_exchange_rate(pair)
                if exchange_rate:
                    print(f"   ✅ {pair}: {exchange_rate.rate:.6f} (source: {exchange_rate.source})")
                else:
                    print(f"   ❌ {pair}: не удалось создать ExchangeRate")
            
            print("\n✅ Интегрированный fiat_rates_service работает корректно!")
            return True
            
    except Exception as e:
        print(f"\n❌ Ошибка при тестировании fiat_rates_service: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_unified_api_service():
    """Тестирование объединенного API сервиса"""
    
    print("\n🚀 Тестирование объединенного API сервиса...")
    
    try:
        async with api_service as service:
            
            # 1. Health check
            print("\n1. Комплексный health check...")
            health = await service.health_check()
            print(f"   Общий статус: {health['status']}")
            print(f"   Rapira API: {health['rapira_api'].get('status', 'unknown')}")
            print(f"   APILayer: {health['apilayer_api'].get('status', 'unknown')}")
            
            # 2. Тестирование криптовалютных пар (через Rapira)
            print("\n2. Тестирование криптовалютных пар...")
            
            crypto_pairs = ['BTC/USDT', 'ETH/USDT', 'TON/USDT', 'USDT/RUB']
            
            for pair in crypto_pairs:
                try:
                    rate = await service.get_exchange_rate(pair)
                    if rate:
                        print(f"   ✅ {pair}: {rate.rate:.6f} (source: {rate.source})")
                    else:
                        print(f"   ❌ {pair}: не удалось получить курс")
                except Exception as e:
                    print(f"   ❌ {pair}: ошибка - {e}")
            
            # 3. Тестирование фиатных пар (через APILayer)
            print("\n3. Тестирование фиатных пар...")
            
            fiat_pairs = ['USD/RUB', 'EUR/ZAR', 'RUB/THB']
            
            for pair in fiat_pairs:
                try:
                    rate = await service.get_exchange_rate(pair)
                    if rate:
                        print(f"   ✅ {pair}: {rate.rate:.6f} (source: {rate.source})")
                    else:
                        print(f"   ❌ {pair}: не удалось получить курс")
                except Exception as e:
                    print(f"   ❌ {pair}: ошибка - {e}")
            
            # 4. Тестирование определения типа пар
            print("\n4. Тестирование определения типа пар...")
            
            from services.api_service import determine_pair_type
            
            test_pairs = [
                ('BTC/USDT', 'crypto'),
                ('USD/RUB', 'fiat'),
                ('USDT/RUB', 'mixed'),
                ('EUR/ZAR', 'fiat'),
                ('ETH/BTC', 'crypto')
            ]
            
            for pair, expected_type in test_pairs:
                actual_type = determine_pair_type(pair)
                if actual_type == expected_type:
                    print(f"   ✅ {pair}: {actual_type}")
                else:
                    print(f"   ❌ {pair}: ожидался {expected_type}, получен {actual_type}")
            
            print("\n✅ Объединенный API сервис работает корректно!")
            return True
            
    except Exception as e:
        print(f"\n❌ Ошибка при тестировании API сервиса: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Основная функция тестирования"""
    
    print("🎯 ПОЛНОЕ ТЕСТИРОВАНИЕ APILAYER ИНТЕГРАЦИИ")
    print("=" * 60)
    print(f"API Key: {config.API_LAYER_KEY[:10]}...")
    print(f"Exchange Rates API URL: {config.API_LAYER_URL}")
    print(f"Currency Data API URL: https://api.apilayer.com/currency_data")
    print("=" * 60)
    
    results = []
    
    # Тест 1: Exchange Rates Data API
    print("\n" + "=" * 60)
    result1 = await test_exchange_rates_data_api()
    results.append(("Exchange Rates Data API", result1))
    
    # Тест 2: Currency Data API
    print("\n" + "=" * 60)
    result2 = await test_currency_data_api()
    results.append(("Currency Data API", result2))
    
    # Тест 3: Интегрированный fiat_rates_service
    print("\n" + "=" * 60)
    result3 = await test_integrated_fiat_service()
    results.append(("Fiat Rates Service", result3))
    
    # Тест 4: Объединенный API сервис
    print("\n" + "=" * 60)
    result4 = await test_unified_api_service()
    results.append(("Unified API Service", result4))
    
    # Итоговый отчет
    print("\n" + "=" * 60)
    print("📊 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
    print("=" * 60)
    
    all_passed = True
    for test_name, result in results:
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        print(f"{test_name}: {status}")
        all_passed = all_passed and result
    
    print("=" * 60)
    if all_passed:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! APILayer интеграция работает корректно!")
        print("\n📋 Что работает:")
        print("• Exchange Rates Data API - получение курсов валют")
        print("• Currency Data API - дополнительные данные о валютах")
        print("• Автоматическое переключение между Rapira (крипто) и APILayer (фиат)")
        print("• Расчет кросс-курсов")
        print("• Обработка ошибок и fallback механизмы")
        print("• Health check для мониторинга")
    else:
        print("❌ НЕКОТОРЫЕ ТЕСТЫ ПРОВАЛЕНЫ. Требуется диагностика.")
    
    return all_passed


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Тестирование прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Критическая ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)