#!/usr/bin/env python3
"""
Быстрый тест основных функций после исправлений
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

async def quick_test():
    """Быстрый тест основных функций"""
    print("🚀 Быстрый тест исправлений...")
    
    # Тестируем одну проблемную пару
    test_pair = 'rubthb'
    
    try:
        # Получаем информацию о паре
        pair_info = get_currency_pair_info(test_pair)
        print(f"✅ Информация о паре: {pair_info['name']}")
        
        # Формируем правильный формат
        pair_format = f"{pair_info['base']}/{pair_info['quote']}"
        print(f"✅ Формат для API: {pair_format}")
        
        # Получаем курс
        async with api_service:
            exchange_rate = await api_service.get_exchange_rate(pair_format)
            
            if exchange_rate:
                print(f"✅ Курс получен: {exchange_rate.rate:.6f} ({exchange_rate.source})")
                
                # Тестируем расчет
                result = calculate_margin_rate(
                    pair_info=pair_info,
                    amount=Decimal('100'),
                    margin=Decimal('5'),
                    exchange_rate_data=exchange_rate.to_dict()
                )
                
                print(f"✅ Расчет: 100 {pair_info['base']} = {result.amount_final_rate:.2f} {pair_info['quote']}")
                print("🎉 Все исправления работают!")
                
            else:
                print("❌ Курс не получен")
                
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(quick_test())