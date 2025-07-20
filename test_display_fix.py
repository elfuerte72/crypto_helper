#!/usr/bin/env python3
"""
Тест для проверки корректности отображения курса RUB/USDT
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from handlers.formatters import MessageFormatter
from handlers.currency_pairs import get_currency_pair_info

def test_rubusdt_display():
    """Тест отображения курса для RUB/USDT"""
    
    # Получаем информацию о паре RUB/USDT
    pair_info = get_currency_pair_info('rubusdt')
    print(f"Информация о паре: {pair_info}")
    
    # Тестируем с курсом 0.012 (1 RUB = 0.012 USDT)
    rate = 0.012
    
    print(f"\nИсходный курс: {rate} (1 RUB = {rate} USDT)")
    
    # Форматируем курс
    formatted_rate = MessageFormatter._format_user_friendly_rate(pair_info, rate)
    print(f"Отформатированный курс: {formatted_rate}")
    
    # Ожидаем увидеть: 1 USDT = ~83.33 RUB
    expected_display_rate = 1.0 / rate
    print(f"Ожидаемый курс в обратном виде: 1 USDT = {expected_display_rate:.2f} RUB")

def test_usdtrub_display():
    """Тест отображения курса для USDT/RUB (для сравнения)"""
    
    # Получаем информацию о паре USDT/RUB
    pair_info = get_currency_pair_info('usdtrub')
    print(f"\nИнформация о паре: {pair_info}")
    
    # Тестируем с курсом 83.33 (1 USDT = 83.33 RUB)
    rate = 83.33
    
    print(f"Исходный курс: {rate} (1 USDT = {rate} RUB)")
    
    # Форматируем курс
    formatted_rate = MessageFormatter._format_user_friendly_rate(pair_info, rate)
    print(f"Отформатированный курс: {formatted_rate}")

if __name__ == "__main__":
    print("=== Тест отображения курсов ===")
    
    try:
        test_rubusdt_display()
        test_usdtrub_display()
        print("\n✅ Тесты завершены успешно!")
        
    except Exception as e:
        print(f"\n❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc() 