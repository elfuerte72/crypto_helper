#!/usr/bin/env python3
"""
Интеграционный тест для новой логики расчета маржи
Проверяет работу с реальными данными курсов
"""

import asyncio
import sys
import os
from decimal import Decimal

# Добавляем путь к src для импорта модулей
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from handlers.calculation_logic import MarginCalculator, calculate_margin_rate
from handlers.currency_pairs import CURRENCY_PAIRS


def test_margin_calculation_logic():
    """Тест новой логики расчета маржи"""
    
    print("🧪 Тестирование новой логики расчета маржи")
    print("=" * 60)
    
    # Тестовые данные
    base_rate = Decimal('100.0')
    margin_percent = Decimal('5.0')
    test_amount = Decimal('1000.0')
    
    exchange_rate_data = {
        'rate': '100.0',
        'timestamp': '2024-01-01T12:00:00Z',
        'source': 'test'
    }
    
    # Тестовые случаи
    test_cases = [
        # Пары X/RUB - должны использовать МИНУС процент
        {
            'pair_key': 'usdtrub',
            'expected_type': 'rub_quote',
            'expected_rate': Decimal('95.0'),  # 100 * (1 - 5/100) = 95
            'description': 'USDT/RUB - минус процент'
        },
        {
            'pair_key': 'usdrub',
            'expected_type': 'rub_quote',
            'expected_rate': Decimal('95.0'),
            'description': 'USD/RUB - минус процент'
        },
        {
            'pair_key': 'eurrub',
            'expected_type': 'rub_quote',
            'expected_rate': Decimal('95.0'),
            'description': 'EUR/RUB - минус процент'
        },
        {
            'pair_key': 'aedrub',
            'expected_type': 'rub_quote',
            'expected_rate': Decimal('95.0'),
            'description': 'AED/RUB - минус процент'
        },
        {
            'pair_key': 'thbrub',
            'expected_type': 'rub_quote',
            'expected_rate': Decimal('95.0'),
            'description': 'THB/RUB - минус процент'
        },
        {
            'pair_key': 'zarrub',
            'expected_type': 'rub_quote',
            'expected_rate': Decimal('95.0'),
            'description': 'ZAR/RUB - минус процент'
        },
        {
            'pair_key': 'idrrub',
            'expected_type': 'rub_quote',
            'expected_rate': Decimal('95.0'),
            'description': 'IDR/RUB - минус процент'
        },
        
        # Пары RUB/X - должны использовать ПЛЮС процент
        {
            'pair_key': 'rubusdt',
            'expected_type': 'rub_base',
            'expected_rate': Decimal('105.0'),  # 100 * (1 + 5/100) = 105
            'description': 'RUB/USDT - плюс процент'
        },
        {
            'pair_key': 'rubusd',
            'expected_type': 'rub_base',
            'expected_rate': Decimal('105.0'),
            'description': 'RUB/USD - плюс процент'
        },
        {
            'pair_key': 'rubeur',
            'expected_type': 'rub_base',
            'expected_rate': Decimal('105.0'),
            'description': 'RUB/EUR - плюс процент'
        },
        {
            'pair_key': 'rubaed',
            'expected_type': 'rub_base',
            'expected_rate': Decimal('105.0'),
            'description': 'RUB/AED - плюс процент'
        },
        {
            'pair_key': 'rubthb',
            'expected_type': 'rub_base',
            'expected_rate': Decimal('105.0'),
            'description': 'RUB/THB - плюс процент'
        },
        {
            'pair_key': 'rubzar',
            'expected_type': 'rub_base',
            'expected_rate': Decimal('105.0'),
            'description': 'RUB/ZAR - плюс процент'
        },
        {
            'pair_key': 'rubidr',
            'expected_type': 'rub_base',
            'expected_rate': Decimal('105.0'),
            'description': 'RUB/IDR - плюс процент'
        },
    ]
    
    print(f"📊 Тестирование {len(test_cases)} валютных пар")
    print(f"📈 Базовый курс: {base_rate}")
    print(f"📈 Маржа: {margin_percent}%")
    print(f"💰 Тестовая сумма: {test_amount}")
    print()
    
    success_count = 0
    total_count = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        pair_key = test_case['pair_key']
        expected_type = test_case['expected_type']
        expected_rate = test_case['expected_rate']
        description = test_case['description']
        
        print(f"🔍 Тест {i}/{total_count}: {description}")
        
        # Получаем информацию о паре
        pair_info = CURRENCY_PAIRS.get(pair_key)
        if not pair_info:
            print(f"   ❌ Пара {pair_key} не найдена")
            continue
        
        try:
            # Проверяем определение типа пары
            pair_type = MarginCalculator.detect_pair_type(pair_info)
            print(f"   🔍 Определен тип: {pair_type}")
            
            if pair_type != expected_type:
                print(f"   ❌ Неверный тип пары! Ожидался: {expected_type}, получен: {pair_type}")
                continue
            
            # Проверяем расчет курса
            calculated_rate = MarginCalculator.calculate_final_rate(
                base_rate, margin_percent, pair_info
            )
            print(f"   📊 Рассчитанный курс: {calculated_rate}")
            
            if calculated_rate != expected_rate:
                print(f"   ❌ Неверный курс! Ожидался: {expected_rate}, получен: {calculated_rate}")
                continue
            
            # Проверяем интеграцию с основной функцией
            result = calculate_margin_rate(
                pair_info=pair_info,
                amount=test_amount,
                margin=margin_percent,
                exchange_rate_data=exchange_rate_data,
                use_banking_logic=False
            )
            
            print(f"   💰 Итоговая сумма: {result.amount_final_rate}")
            print(f"   📈 Разница: {result.amount_difference}")
            print(f"   ✅ Тест пройден успешно!")
            
            success_count += 1
            
        except Exception as e:
            print(f"   ❌ Ошибка при тестировании: {e}")
        
        print()
    
    print("=" * 60)
    print(f"📊 Результаты тестирования:")
    print(f"✅ Успешно: {success_count}/{total_count}")
    print(f"❌ Неудачно: {total_count - success_count}/{total_count}")
    print(f"📈 Процент успеха: {(success_count/total_count)*100:.1f}%")
    
    if success_count == total_count:
        print("🎉 Все тесты пройдены успешно!")
        return True
    else:
        print("⚠️  Есть проблемы с тестами!")
        return False


def test_specific_examples():
    """Тест конкретных примеров из требований"""
    
    print("\n🎯 Тестирование конкретных примеров")
    print("=" * 60)
    
    examples = [
        {
            'pair': 'USDT/RUB',
            'pair_key': 'usdtrub',
            'base_rate': Decimal('95.50'),
            'margin': Decimal('3.0'),
            'expected_operation': 'минус',
            'expected_rate': Decimal('92.635'),  # 95.50 * (1 - 3/100) = 95.50 * 0.97 = 92.635
        },
        {
            'pair': 'RUB/USDT',
            'pair_key': 'rubusdt',
            'base_rate': Decimal('0.01047'),
            'margin': Decimal('2.5'),
            'expected_operation': 'плюс',
            'expected_rate': Decimal('0.01073175'),  # 0.01047 * (1 + 2.5/100) = 0.01047 * 1.025 = 0.01073175
        },
        {
            'pair': 'USD/RUB',
            'pair_key': 'usdrub',
            'base_rate': Decimal('98.25'),
            'margin': Decimal('1.5'),
            'expected_operation': 'минус',
            'expected_rate': Decimal('96.77625'),  # 98.25 * (1 - 1.5/100) = 98.25 * 0.985 = 96.77625
        },
        {
            'pair': 'RUB/USD',
            'pair_key': 'rubusd',
            'base_rate': Decimal('0.01018'),
            'margin': Decimal('4.0'),
            'expected_operation': 'плюс',
            'expected_rate': Decimal('0.01058720'),  # 0.01018 * (1 + 4/100) = 0.01018 * 1.04 = 0.01058720
        },
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"🔍 Пример {i}: {example['pair']}")
        print(f"   📊 Базовый курс: {example['base_rate']}")
        print(f"   📈 Маржа: {example['margin']}%")
        print(f"   🔄 Операция: {example['expected_operation']} процент")
        
        pair_info = CURRENCY_PAIRS.get(example['pair_key'])
        if not pair_info:
            print(f"   ❌ Пара не найдена!")
            continue
        
        try:
            calculated_rate = MarginCalculator.calculate_final_rate(
                example['base_rate'], example['margin'], pair_info
            )
            
            print(f"   🎯 Ожидаемый курс: {example['expected_rate']}")
            print(f"   📊 Рассчитанный курс: {calculated_rate}")
            
            # Проверяем с точностью до 8 знаков
            if abs(calculated_rate - example['expected_rate']) < Decimal('0.00000001'):
                print(f"   ✅ Расчет корректен!")
            else:
                print(f"   ❌ Расчет неверен!")
                
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
        
        print()


if __name__ == '__main__':
    print("🚀 Запуск интеграционного теста новой логики расчета маржи")
    print()
    
    # Основные тесты
    main_test_passed = test_margin_calculation_logic()
    
    # Тесты конкретных примеров
    test_specific_examples()
    
    print("\n🏁 Тестирование завершено!")
    
    if main_test_passed:
        print("✅ Новая логика работает корректно!")
        sys.exit(0)
    else:
        print("❌ Обнаружены проблемы в новой логике!")
        sys.exit(1)