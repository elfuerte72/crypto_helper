#!/usr/bin/env python3
"""
Простой тест для проверки функции format_calculation_result_simple
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from decimal import Decimal
from src.handlers.calculation_logic import CalculationResult, BankingRates
from src.handlers.formatters import MessageFormatter

def test_simple_formatter():
    """Тест функции format_calculation_result_simple"""
    
    # Данные теста
    pair_info = {
        'name': 'USDT/RUB',
        'base': 'USDT', 
        'quote': 'RUB',
        'description': 'Tether к Российскому рублю',
        'emoji': '🇷🇺'
    }
    
    amount = Decimal("1000")
    base_rate = Decimal("95.5")
    margin = Decimal("5")
    final_rate = Decimal("100.275")
    exchange_rate_data = {
        'timestamp': '2023-12-01T12:00:00',
        'source': 'rapira',
        'rate': 95.5
    }
    
    # Создаем банковские курсы
    banking_rates = BankingRates(
        base_rate=base_rate,
        buy_rate=Decimal("100.0"),
        sell_rate=Decimal("100.5"),
        margin_percent=margin,
        spread_percent=Decimal("0.5")
    )
    
    # Создаем результат с банковскими курсами
    result = CalculationResult(
        pair_info=pair_info,
        amount=amount,
        base_rate=base_rate,
        margin=margin,
        final_rate=final_rate,
        exchange_rate_data=exchange_rate_data,
        banking_rates=banking_rates
    )
    
    # Форматируем результат
    formatted_result = MessageFormatter.format_calculation_result_simple(result)
    
    print("=== РЕЗУЛЬТАТ ФОРМАТИРОВАНИЯ ===")
    print(formatted_result)
    print("=== КОНЕЦ РЕЗУЛЬТАТА ===")
    
    # Проверяем, что нужные элементы есть
    print("\n=== ПРОВЕРКИ ===")
    
    print(f"✅ Расчет завершен: {'✅' if 'Расчет завершен' in formatted_result else '❌'}")
    print(f"✅ Название пары: {'✅' if 'USDT/RUB' in formatted_result else '❌'}")
    print(f"✅ Эмодзи: {'✅' if '🇷🇺' in formatted_result else '❌'}")
    print(f"✅ Сумма: {'✅' if '1000.0000' in formatted_result else '❌'}")
    print(f"✅ Курс с процентом: {'✅' if 'Курс с' in formatted_result else '❌'}")
    print(f"✅ Итого к получению: {'✅' if 'Итого к получению' in formatted_result else '❌'}")
    
    # Проверяем, что НЕТ нежелательных элементов
    print(f"❌ Базовый курс: {'❌' if 'Базовый курс' in formatted_result else '✅'}")
    print(f"❌ Банковские курсы: {'❌' if 'Банковские курсы' in formatted_result else '✅'}")
    print(f"❌ Покупка: {'❌' if 'Покупка:' in formatted_result else '✅'}")
    print(f"❌ Продажа: {'❌' if 'Продажа:' in formatted_result else '✅'}")
    print(f"❌ Слово 'наценка': {'❌' if 'наценка' in formatted_result.lower() else '✅'}")
    
    print("\n=== ТЕСТ ЗАВЕРШЕН ===")

if __name__ == "__main__":
    test_simple_formatter()