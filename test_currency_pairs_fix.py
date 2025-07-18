#!/usr/bin/env python3
"""
Тест исправления валютных пар
Проверяет корректную работу с проблемными парами
"""

import asyncio
import sys
import os

# Добавляем путь к src для импорта модулей
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.api_service import api_service
from services.fiat_rates_service import fiat_rates_service
from handlers.currency_pairs import get_currency_pair_info, CURRENCY_PAIRS
from utils.logger import get_api_logger

logger = get_api_logger()

# Проблемные пары из вашего списка
PROBLEMATIC_PAIRS = [
    'rubthb', 'thbrub',
    'rubaed', 'aedrub', 
    'rubidr', 'idrrub',
    'rubeur', 'eurrub',
    'rubusd', 'usdrub'
]

async def test_currency_pairs_info():
    """Тестируем получение информации о валютных парах"""
    print("🔍 Тестирование получения информации о валютных парах...")
    
    for pair_callback in PROBLEMATIC_PAIRS:
        pair_info = get_currency_pair_info(pair_callback)
        if pair_info:
            print(f"✅ {pair_callback}: {pair_info['name']} ({pair_info['base']}/{pair_info['quote']})")
        else:
            print(f"❌ {pair_callback}: Информация не найдена")

async def test_api_service_with_correct_format():
    """Тестируем API service с правильным форматом пар"""
    print("\n🌐 Тестирование API service с правильным форматом...")
    
    async with api_service:
        for pair_callback in PROBLEMATIC_PAIRS:
            pair_info = get_currency_pair_info(pair_callback)
            if not pair_info:
                print(f"❌ {pair_callback}: Информация о паре не найдена")
                continue
            
            # Формируем правильный формат для API
            pair_format = f"{pair_info['base']}/{pair_info['quote']}"
            
            try:
                print(f"\n📊 Тестирование пары: {pair_callback} -> {pair_format}")
                
                exchange_rate = await api_service.get_exchange_rate(pair_format)
                
                if exchange_rate:
                    print(f"✅ {pair_format}: {exchange_rate.rate:.6f} (source: {exchange_rate.source})")
                else:
                    print(f"❌ {pair_format}: Курс не найден")
                    
            except Exception as e:
                print(f"❌ Ошибка для {pair_format}: {e}")

async def test_fiat_pairs_specifically():
    """Тестируем фиатные пары отдельно"""
    print("\n💱 Тестирование фиатных пар через fiat_rates_service...")
    
    fiat_pairs = [
        'RUB/THB', 'THB/RUB',
        'RUB/AED', 'AED/RUB', 
        'RUB/IDR', 'IDR/RUB',
        'RUB/EUR', 'EUR/RUB',
        'RUB/USD', 'USD/RUB'
    ]
    
    async with fiat_rates_service:
        for pair in fiat_pairs:
            try:
                print(f"\n📊 Тестирование фиатной пары: {pair}")
                
                exchange_rate = await fiat_rates_service.get_fiat_exchange_rate(pair)
                
                if exchange_rate:
                    print(f"✅ {pair}: {exchange_rate.rate:.6f} (source: {exchange_rate.source})")
                else:
                    print(f"❌ {pair}: Курс не найден")
                    
            except Exception as e:
                print(f"❌ Ошибка для {pair}: {e}")

async def test_integration_flow():
    """Тестируем полный поток как в боте"""
    print("\n🤖 Тестирование полного потока как в боте...")
    
    async with api_service:
        for pair_callback in PROBLEMATIC_PAIRS:
            try:
                print(f"\n🔄 Полный тест для: {pair_callback}")
                
                # Шаг 1: Получаем информацию о паре
                pair_info = get_currency_pair_info(pair_callback)
                if not pair_info:
                    print(f"❌ Информация о паре {pair_callback} не найдена")
                    continue
                
                print(f"   📋 Информация о паре: {pair_info['name']} ({pair_info['base']}/{pair_info['quote']})")
                
                # Шаг 2: Формируем правильный формат для API (как в исправленном коде)
                pair_format = f"{pair_info['base']}/{pair_info['quote']}"
                
                # Шаг 3: Получаем курс через API
                exchange_rate = await api_service.get_exchange_rate(pair_format)
                
                if exchange_rate:
                    print(f"   ✅ Курс получен: {exchange_rate.rate:.6f} (source: {exchange_rate.source})")
                    
                    # Шаг 4: Тестируем расчет с наценкой
                    from handlers.calculation_logic import calculate_margin_rate
                    from decimal import Decimal
                    
                    result = calculate_margin_rate(
                        pair_info=pair_info,
                        amount=Decimal('100'),
                        margin=Decimal('5'),
                        exchange_rate_data=exchange_rate.to_dict()
                    )
                    
                    print(f"   💰 Расчет с наценкой 5%: {result.final_rate:.6f}")
                    print(f"   📊 Сумма для 100 {pair_info['base']}: {result.amount_final_rate:.2f} {pair_info['quote']}")
                    
                else:
                    print(f"   ❌ Курс не получен для {pair_format}")
                    
            except Exception as e:
                print(f"❌ Ошибка в полном тесте для {pair_callback}: {e}")
                import traceback
                traceback.print_exc()

async def test_health_checks():
    """Тестируем health check'и сервисов"""
    print("\n🏥 Тестирование health check'ов...")
    
    # API service health check
    try:
        async with api_service:
            health_data = await api_service.health_check()
            print(f"API Service: {health_data.get('status', 'unknown')}")
            if health_data.get('rapira_api'):
                print(f"  Rapira API: {health_data['rapira_api'].get('status', 'unknown')}")
            if health_data.get('apilayer_api'):
                print(f"  APILayer: {health_data['apilayer_api'].get('status', 'unknown')}")
    except Exception as e:
        print(f"❌ Ошибка health check API service: {e}")
    
    # Fiat rates service health check
    try:
        async with fiat_rates_service:
            health_data = await fiat_rates_service.health_check()
            print(f"Fiat Rates Service: {health_data.get('status', 'unknown')}")
    except Exception as e:
        print(f"❌ Ошибка health check fiat rates service: {e}")

async def main():
    """Основная функция тестирования"""
    print("🚀 Запуск тестов исправления валютных пар...\n")
    
    try:
        # Тест 1: Информация о парах
        await test_currency_pairs_info()
        
        # Тест 2: API service с правильным форматом
        await test_api_service_with_correct_format()
        
        # Тест 3: Фиатные пары отдельно
        await test_fiat_pairs_specifically()
        
        # Тест 4: Полный поток
        await test_integration_flow()
        
        # Тест 5: Health check'и
        await test_health_checks()
        
        print("\n🎉 Все тесты завершены!")
        
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())