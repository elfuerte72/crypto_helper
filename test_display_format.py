#!/usr/bin/env python3
"""
Тест нового формата отображения курсов
Проверяет, что курсы отображаются в понятном формате
"""

import sys
import os
from decimal import Decimal

# Добавляем путь к src для импорта модулей
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from handlers.formatters import MessageFormatter
from handlers.currency_pairs import CURRENCY_PAIRS
from handlers.calculation_logic import calculate_margin_rate


def test_display_format():
    """Тест нового формата отображения курсов"""
    
    print("🎨 Тестирование нового формата отображения курсов")
    print("=" * 70)
    
    # Тестовые случаи
    test_cases = [
        {
            'pair_key': 'rubusd',
            'pair_name': 'RUB/USD',
            'api_rate': 0.01018,  # API возвращает: 1 RUB = 0.01018 USD
            'expected_display': '1 USD = 98.23 RUB',  # Показываем: 1 USD = 98.23 RUB
            'description': 'RUB/USD должен отображаться как USD/RUB'
        },
        {
            'pair_key': 'usdrub',
            'pair_name': 'USD/RUB',
            'api_rate': 98.25,  # API возвращает: 1 USD = 98.25 RUB
            'expected_display': '1 USD = 98.25 RUB',  # Показываем: 1 USD = 98.25 RUB
            'description': 'USD/RUB должен отображаться как есть'
        },
        {
            'pair_key': 'rubeur',
            'pair_name': 'RUB/EUR',
            'api_rate': 0.00935,  # API возвращает: 1 RUB = 0.00935 EUR
            'expected_display': '1 EUR = 107.00 RUB',  # Показываем: 1 EUR = 107.00 RUB
            'description': 'RUB/EUR должен отображаться как EUR/RUB'
        },
        {
            'pair_key': 'eurrub',
            'pair_name': 'EUR/RUB',
            'api_rate': 107.50,  # API возвращает: 1 EUR = 107.50 RUB
            'expected_display': '1 EUR = 107.50 RUB',  # Показываем: 1 EUR = 107.50 RUB
            'description': 'EUR/RUB должен отображаться как есть'
        },
        {
            'pair_key': 'rubusdt',
            'pair_name': 'RUB/USDT',
            'api_rate': 0.01045,  # API возвращает: 1 RUB = 0.01045 USDT
            'expected_display': '1 USDT = 95.69 RUB',  # Показываем: 1 USDT = 95.69 RUB
            'description': 'RUB/USDT должен отображаться как USDT/RUB'
        },
        {
            'pair_key': 'usdtrub',
            'pair_name': 'USDT/RUB',
            'api_rate': 95.50,  # API возвращает: 1 USDT = 95.50 RUB
            'expected_display': '1 USDT = 95.50 RUB',  # Показываем: 1 USDT = 95.50 RUB
            'description': 'USDT/RUB должен отображаться как есть'
        },
    ]
    
    print(f"📊 Тестирование {len(test_cases)} случаев отображения")
    print()
    
    success_count = 0
    
    for i, test_case in enumerate(test_cases, 1):
        pair_key = test_case['pair_key']
        pair_name = test_case['pair_name']
        api_rate = test_case['api_rate']
        expected_display = test_case['expected_display']
        description = test_case['description']
        
        print(f"🔍 Тест {i}: {pair_name}")
        print(f"   📝 {description}")
        print(f"   🔢 API курс: {api_rate}")
        
        # Получаем информацию о паре
        pair_info = CURRENCY_PAIRS.get(pair_key)
        if not pair_info:
            print(f"   ❌ Пара {pair_key} не найдена")
            continue
        
        try:
            # Форматируем курс
            formatted_rate = MessageFormatter._format_user_friendly_rate(pair_info, api_rate)
            
            print(f"   💰 Отформатированный курс: {formatted_rate}")
            print(f"   🎯 Ожидаемый формат: <code>{expected_display}</code>")
            
            # Проверяем соответствие (убираем HTML теги для сравнения)
            clean_formatted = formatted_rate.replace('<code>', '').replace('</code>', '')
            
            # Для числовых значений проверяем приблизительное равенство
            if 'RUB' in expected_display:
                # Извлекаем числовое значение из ожидаемого результата
                expected_value = float(expected_display.split('=')[1].strip().split()[0])
                actual_value = float(clean_formatted.split('=')[1].strip().split()[0])
                
                # Проверяем с точностью до 2 знаков после запятой
                if abs(expected_value - actual_value) < 0.01:
                    print(f"   ✅ Формат корректен!")
                    success_count += 1
                else:
                    print(f"   ❌ Неверное значение! Ожидалось: {expected_value}, получено: {actual_value}")
            else:
                # Для нерублевых пар проверяем точное соответствие
                if expected_display in clean_formatted:
                    print(f"   ✅ Формат корректен!")
                    success_count += 1
                else:
                    print(f"   ❌ Неверный формат!")
                    
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
        
        print()
    
    print("=" * 70)
    print(f"📊 Результаты тестирования формата отображения:")
    print(f"✅ Успешно: {success_count}/{len(test_cases)}")
    print(f"❌ Неудачно: {len(test_cases) - success_count}/{len(test_cases)}")
    print(f"📈 Процент успеха: {(success_count/len(test_cases))*100:.1f}%")
    
    return success_count == len(test_cases)


def test_margin_calculation_with_display():
    """Тест расчета маржи с новым форматом отображения"""
    
    print("\n🧮 Тестирование расчета маржи с новым форматом отображения")
    print("=" * 70)
    
    # Тестовые случаи
    test_cases = [
        {
            'pair_key': 'rubusd',
            'pair_name': 'RUB/USD',
            'api_rate': 0.01018,  # 1 RUB = 0.01018 USD
            'margin': 5.0,
            'expected_logic': 'плюс',
            'description': 'RUB/USD с маржой 5% (плюс процент)'
        },
        {
            'pair_key': 'usdrub',
            'pair_name': 'USD/RUB',
            'api_rate': 98.25,  # 1 USD = 98.25 RUB
            'margin': 5.0,
            'expected_logic': 'минус',
            'description': 'USD/RUB с маржой 5% (минус процент)'
        },
        {
            'pair_key': 'usdtrub',
            'pair_name': 'USDT/RUB',
            'api_rate': 95.50,  # 1 USDT = 95.50 RUB
            'margin': 3.0,
            'expected_logic': 'минус',
            'description': 'USDT/RUB с маржой 3% (минус процент)'
        },
        {
            'pair_key': 'rubusdt',
            'pair_name': 'RUB/USDT',
            'api_rate': 0.01045,  # 1 RUB = 0.01045 USDT
            'margin': 2.5,
            'expected_logic': 'плюс',
            'description': 'RUB/USDT с маржой 2.5% (плюс процент)'
        },
    ]
    
    print(f"📊 Тестирование {len(test_cases)} случаев расчета с отображением")
    print()
    
    success_count = 0
    
    for i, test_case in enumerate(test_cases, 1):
        pair_key = test_case['pair_key']
        pair_name = test_case['pair_name']
        api_rate = test_case['api_rate']
        margin = test_case['margin']
        expected_logic = test_case['expected_logic']
        description = test_case['description']
        
        print(f"🔍 Тест {i}: {pair_name}")
        print(f"   📝 {description}")
        print(f"   🔢 API курс: {api_rate}")
        print(f"   📈 Маржа: {margin}%")
        print(f"   🔄 Ожидаемая логика: {expected_logic} процент")
        
        # Получаем информацию о паре
        pair_info = CURRENCY_PAIRS.get(pair_key)
        if not pair_info:
            print(f"   ❌ Пара {pair_key} не найдена")
            continue
        
        try:
            # Данные для расчета
            exchange_rate_data = {
                'rate': str(api_rate),
                'timestamp': '2024-01-01T12:00:00Z',
                'source': 'test'
            }
            
            # Выполняем расчет
            result = calculate_margin_rate(
                pair_info=pair_info,
                amount=Decimal('1000.0'),
                margin=Decimal(str(margin)),
                exchange_rate_data=exchange_rate_data,
                use_banking_logic=False
            )
            
            # Проверяем логику расчета
            base_rate = Decimal(str(api_rate))
            if expected_logic == 'плюс':
                expected_final_rate = base_rate * (Decimal('1') + Decimal(str(margin)) / Decimal('100'))
            else:  # минус
                expected_final_rate = base_rate * (Decimal('1') - Decimal(str(margin)) / Decimal('100'))
            
            print(f"   💰 Базовый курс: {base_rate}")
            print(f"   💎 Итоговый курс: {result.final_rate}")
            print(f"   🎯 Ожидаемый курс: {expected_final_rate}")
            
            # Проверяем с точностью до 8 знаков
            if abs(result.final_rate - expected_final_rate) < Decimal('0.00000001'):
                print(f"   ✅ Логика расчета корректна!")
                
                # Проверяем формат отображения
                base_rate_display = MessageFormatter._format_user_friendly_rate(pair_info, float(base_rate))
                final_rate_display = MessageFormatter._format_user_friendly_rate(pair_info, float(result.final_rate))
                
                print(f"   📊 Базовый курс (отображение): {base_rate_display}")
                print(f"   💎 Итоговый курс (отображение): {final_rate_display}")
                
                success_count += 1
            else:
                print(f"   ❌ Неверная логика расчета!")
                
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
        
        print()
    
    print("=" * 70)
    print(f"📊 Результаты тестирования расчета с отображением:")
    print(f"✅ Успешно: {success_count}/{len(test_cases)}")
    print(f"❌ Неудачно: {len(test_cases) - success_count}/{len(test_cases)}")
    print(f"📈 Процент успеха: {(success_count/len(test_cases))*100:.1f}%")
    
    return success_count == len(test_cases)


if __name__ == '__main__':
    print("🚀 Запуск тестов нового формата отображения курсов")
    print()
    
    # Тест формата отображения
    display_test_passed = test_display_format()
    
    # Тест расчета с отображением
    calculation_test_passed = test_margin_calculation_with_display()
    
    print("\n🏁 Тестирование завершено!")
    
    if display_test_passed and calculation_test_passed:
        print("✅ Все тесты пройдены! Новый формат отображения работает корректно!")
        print("📋 Сводка изменений:")
        print("   • RUB/USD теперь отображается как USD/RUB")
        print("   • RUB/EUR теперь отображается как EUR/RUB")
        print("   • RUB/USDT теперь отображается как USDT/RUB")
        print("   • Логика расчета маржи сохранена (плюс/минус)")
        print("   • Формат всегда показывает 'сколько рублей за 1 единицу валюты'")
        sys.exit(0)
    else:
        print("❌ Обнаружены проблемы в новом формате отображения!")
        sys.exit(1)