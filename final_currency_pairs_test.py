#!/usr/bin/env python3
"""
Финальный тест исправления валютных пар
Проверяет все исправления и fallback механизм
"""

import asyncio
import sys
import os
from decimal import Decimal

# Добавляем путь к src для импорта модулей
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.api_service import api_service
from handlers.currency_pairs import get_currency_pair_info
from handlers.calculation_logic import calculate_margin_rate
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

async def test_complete_flow():
    """Тестируем полный поток работы с исправлениями"""
    print("🚀 Тестирование полного потока с исправлениями...")
    
    results = {}
    
    async with api_service:
        for pair_callback in PROBLEMATIC_PAIRS:
            try:
                print(f"\n📊 Тестирование: {pair_callback}")
                
                # Шаг 1: Получаем информацию о паре (как в боте)
                pair_info = get_currency_pair_info(pair_callback)
                if not pair_info:
                    print(f"❌ Информация о паре не найдена")
                    results[pair_callback] = {'status': 'error', 'error': 'pair_info_not_found'}
                    continue
                
                print(f"   📋 Пара: {pair_info['name']} ({pair_info['base']}/{pair_info['quote']})")
                
                # Шаг 2: Формируем правильный формат для API (ИСПРАВЛЕНИЕ)
                pair_format = f"{pair_info['base']}/{pair_info['quote']}"
                
                # Шаг 3: Получаем курс через API
                exchange_rate = await api_service.get_exchange_rate(pair_format)
                
                if not exchange_rate:
                    print(f"❌ Курс не получен")
                    results[pair_callback] = {'status': 'error', 'error': 'no_exchange_rate'}
                    continue
                
                print(f"   💱 Курс: {exchange_rate.rate:.6f} (источник: {exchange_rate.source})")
                
                # Шаг 4: Тестируем расчет с наценкой
                test_amount = Decimal('100')
                test_margin = Decimal('5')
                
                result = calculate_margin_rate(
                    pair_info=pair_info,
                    amount=test_amount,
                    margin=test_margin,
                    exchange_rate_data=exchange_rate.to_dict()
                )
                
                print(f"   📈 Базовый курс: {result.base_rate:.6f}")
                print(f"   📊 Курс с наценкой 5%: {result.final_rate:.6f}")
                print(f"   💰 100 {pair_info['base']} = {result.amount_final_rate:.2f} {pair_info['quote']}")
                
                # Проверяем, что курс разумный
                if result.final_rate > 0 and result.amount_final_rate > 0:
                    print(f"   ✅ Расчет корректен")
                    results[pair_callback] = {
                        'status': 'success',
                        'pair_format': pair_format,
                        'rate': float(exchange_rate.rate),
                        'source': exchange_rate.source,
                        'final_rate': float(result.final_rate),
                        'calculation_result': float(result.amount_final_rate)
                    }
                else:
                    print(f"   ❌ Некорректный расчет")
                    results[pair_callback] = {'status': 'error', 'error': 'invalid_calculation'}
                
            except Exception as e:
                print(f"❌ Ошибка: {e}")
                results[pair_callback] = {'status': 'error', 'error': str(e)}
    
    return results

async def test_fallback_mechanism():
    """Тестируем fallback механизм при проблемах с API"""
    print("\n🔄 Тестирование fallback механизма...")
    
    # Временно отключаем API ключ для тестирования fallback
    original_api_key = None
    try:
        from config import config
        original_api_key = config.API_LAYER_KEY
        config.API_LAYER_KEY = ''  # Отключаем API ключ
        
        async with api_service:
            # Тестируем фиатную пару
            test_pair = 'RUB/USD'
            print(f"📊 Тестирование fallback для {test_pair}")
            
            exchange_rate = await api_service.get_exchange_rate(test_pair)
            
            if exchange_rate:
                print(f"✅ Fallback работает: {exchange_rate.rate:.6f} (источник: {exchange_rate.source})")
                
                # Проверяем, что источник указывает на fallback
                if 'fallback' in exchange_rate.source or 'apilayer_fallback' in exchange_rate.source:
                    print("   ✅ Источник корректно указывает на fallback")
                else:
                    print("   ⚠️ Источник не указывает на fallback")
                
                return True
            else:
                print("❌ Fallback не работает")
                return False
                
    finally:
        # Восстанавливаем API ключ
        if original_api_key:
            config.API_LAYER_KEY = original_api_key

async def generate_summary_report(results):
    """Генерируем итоговый отчет"""
    print("\n" + "="*60)
    print("📊 ИТОГОВЫЙ ОТЧЕТ ИСПРАВЛЕНИЙ")
    print("="*60)
    
    successful = sum(1 for r in results.values() if r['status'] == 'success')
    total = len(results)
    
    print(f"✅ Успешно обработано: {successful}/{total} пар")
    print(f"❌ Ошибок: {total - successful}/{total} пар")
    
    if successful > 0:
        print(f"\n📈 Успешные пары:")
        for pair_callback, result in results.items():
            if result['status'] == 'success':
                print(f"   {pair_callback}: {result['pair_format']} -> {result['rate']:.6f} ({result['source']})")
    
    if total - successful > 0:
        print(f"\n❌ Проблемные пары:")
        for pair_callback, result in results.items():
            if result['status'] == 'error':
                print(f"   {pair_callback}: {result['error']}")
    
    # Анализ источников данных
    sources = {}
    for result in results.values():
        if result['status'] == 'success':
            source = result['source']
            sources[source] = sources.get(source, 0) + 1
    
    if sources:
        print(f"\n📊 Источники данных:")
        for source, count in sources.items():
            print(f"   {source}: {count} пар")
    
    # Рекомендации
    print(f"\n💡 РЕКОМЕНДАЦИИ:")
    if successful == total:
        print("   ✅ Все пары работают корректно!")
        print("   ✅ Исправления успешно применены")
    else:
        print("   ⚠️ Некоторые пары требуют дополнительного внимания")
        
    fallback_count = sum(1 for r in results.values() 
                        if r['status'] == 'success' and 'fallback' in r['source'])
    
    if fallback_count > 0:
        print(f"   📋 {fallback_count} пар используют fallback данные")
        print("   💡 Рассмотрите возможность обновления API ключей")

async def main():
    """Основная функция тестирования"""
    print("🚀 Запуск финального теста исправлений валютных пар...\n")
    
    try:
        # Тест 1: Полный поток работы
        results = await test_complete_flow()
        
        # Тест 2: Fallback механизм
        fallback_works = await test_fallback_mechanism()
        
        # Тест 3: Итоговый отчет
        await generate_summary_report(results)
        
        print(f"\n🔄 Fallback механизм: {'✅ Работает' if fallback_works else '❌ Не работает'}")
        
        print("\n🎉 Финальный тест завершен!")
        
        # Проверяем общий результат
        successful = sum(1 for r in results.values() if r['status'] == 'success')
        total = len(results)
        
        if successful == total and fallback_works:
            print("\n🎊 ВСЕ ИСПРАВЛЕНИЯ РАБОТАЮТ КОРРЕКТНО!")
        elif successful > total * 0.8:
            print("\n✅ Большинство исправлений работают корректно")
        else:
            print("\n⚠️ Требуются дополнительные исправления")
        
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())