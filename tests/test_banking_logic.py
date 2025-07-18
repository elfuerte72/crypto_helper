#!/usr/bin/env python3
"""
Тестовый файл для проверки новой банковской логики курсов
"""

import sys
import os
sys.path.insert(0, 'src')

from decimal import Decimal
from src.handlers.calculation_logic import calculate_banking_rate, MarginCalculator, BankingRates
from src.handlers.formatters import MessageFormatter
from src.handlers.currency_pairs import get_currency_pair_info

# Тестовые данные о курсах
test_exchange_rates = {
    'RUB/USD': {
        'rate': 0.01,
        'timestamp': '2024-01-15T10:00:00Z',
        'source': 'test'
    },
    'USD/RUB': {
        'rate': 100.0,
        'timestamp': '2024-01-15T10:00:00Z',
        'source': 'test'
    },
    'USDT/RUB': {
        'rate': 95.0,
        'timestamp': '2024-01-15T10:00:00Z',
        'source': 'test'
    },
    'EUR/RUB': {
        'rate': 110.0,
        'timestamp': '2024-01-15T10:00:00Z',
        'source': 'test'
    }
}

def test_rate_display():
    """Тест отображения курсов"""
    print("🧪 Тестирование отображения курсов...")
    
    test_pairs = [
        ('rubusd', 'RUB/USD'),
        ('usdrub', 'USD/RUB'),
        ('usdtrub', 'USDT/RUB'),
        ('eurrub', 'EUR/RUB')
    ]
    
    for pair_key, pair_name in test_pairs:
        pair_info = get_currency_pair_info(pair_key)
        if pair_info:
            rate = test_exchange_rates[pair_name]['rate']
            formatted = MessageFormatter._format_rate_display(pair_info, rate)
            print(f"  {pair_name}: {formatted}")
        else:
            print(f"  ❌ Пара {pair_key} не найдена")
    
    print()

def test_banking_rates():
    """Тест расчета банковских курсов"""
    print("🧪 Тестирование банковских курсов...")
    
    base_rate = Decimal('100.0')  # USD/RUB
    margin = Decimal('3.0')  # 3% наценка
    spread = Decimal('0.5')  # 0.5% спрэд
    
    banking_rates = MarginCalculator.calculate_banking_rates(
        base_rate, margin, spread
    )
    
    print(f"  Базовый курс: {banking_rates.base_rate}")
    print(f"  Курс покупки: {banking_rates.buy_rate}")
    print(f"  Курс продажи: {banking_rates.sell_rate}")
    print(f"  Наценка: {banking_rates.margin_percent}%")
    print(f"  Спрэд: {banking_rates.spread_percent}%")
    print()

def test_calculation_result():
    """Тест полного расчета"""
    print("🧪 Тестирование полного расчета...")
    
    # Тестируем USD/RUB
    pair_info = get_currency_pair_info('usdrub')
    amount = Decimal('100.0')  # 100 USD
    margin = Decimal('3.0')  # 3% наценка
    exchange_rate_data = test_exchange_rates['USD/RUB']
    
    result = calculate_banking_rate(
        pair_info, amount, margin, exchange_rate_data
    )
    
    print("  Результат расчета:")
    print(f"    Сумма: {result.amount} {result.base_currency}")
    print(f"    Базовый курс: {result.base_rate}")
    print(f"    Курс покупки: {result.banking_rates.buy_rate}")
    print(f"    Курс продажи: {result.banking_rates.sell_rate}")
    print(f"    По базовому курсу: {result.amount_base_rate} {result.quote_currency}")
    print(f"    По курсу покупки: {result.amount_buy_rate} {result.quote_currency}")
    print(f"    По курсу продажи: {result.amount_sell_rate} {result.quote_currency}")
    print(f"    Прибыль банка: {result.bank_profit} {result.quote_currency}")
    print()

def test_formatting():
    """Тест форматирования сообщений"""
    print("🧪 Тестирование форматирования...")
    
    # Тестируем RUB/USD - проблемная пара
    pair_info = get_currency_pair_info('rubusd')
    amount = Decimal('1000.0')  # 1000 RUB
    margin = Decimal('2.0')  # 2% наценка
    exchange_rate_data = test_exchange_rates['RUB/USD']
    
    result = calculate_banking_rate(
        pair_info, amount, margin, exchange_rate_data
    )
    
    formatted = MessageFormatter.format_banking_calculation_result(result)
    print("  Отформатированный результат:")
    print(formatted)
    print()

def test_all_pairs():
    """Тест всех валютных пар"""
    print("🧪 Тестирование всех валютных пар...")
    
    test_cases = [
        ('rubusd', 'RUB/USD', Decimal('1000.0')),
        ('usdrub', 'USD/RUB', Decimal('100.0')),
        ('usdtrub', 'USDT/RUB', Decimal('50.0')),
        ('eurrub', 'EUR/RUB', Decimal('100.0'))
    ]
    
    for pair_key, pair_name, amount in test_cases:
        print(f"\n  --- {pair_name} ---")
        pair_info = get_currency_pair_info(pair_key)
        if pair_info and pair_name in test_exchange_rates:
            exchange_rate_data = test_exchange_rates[pair_name]
            
            result = calculate_banking_rate(
                pair_info, amount, Decimal('2.5'), exchange_rate_data
            )
            
            # Форматируем курс
            base_rate_display = MessageFormatter._format_rate_display(
                pair_info, float(result.base_rate)
            )
            buy_rate_display = MessageFormatter._format_rate_display(
                pair_info, float(result.banking_rates.buy_rate)
            )
            sell_rate_display = MessageFormatter._format_rate_display(
                pair_info, float(result.banking_rates.sell_rate)
            )
            
            print(f"    Базовый курс: {base_rate_display}")
            print(f"    Курс покупки: {buy_rate_display}")
            print(f"    Курс продажи: {sell_rate_display}")
            print(f"    Сумма: {amount} {result.base_currency}")
            print(f"    Результат: {result.amount_sell_rate:.2f} {result.quote_currency}")
        else:
            print(f"    ❌ Пара {pair_key} не найдена")

if __name__ == "__main__":
    print("🚀 Тестирование банковской логики курсов валют\n")
    
    test_rate_display()
    test_banking_rates()
    test_calculation_result()
    test_formatting()
    test_all_pairs()
    
    print("\n✅ Тестирование завершено!")