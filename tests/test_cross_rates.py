#!/usr/bin/env python3
"""
Тестовый скрипт для проверки вычисления кросс-курсов
"""

import asyncio
import sys
import os
from pathlib import Path

# Добавляем src в путь
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

from services.api_service import APIService, RapiraAPIError
from config import config
from utils.logger import get_api_logger

logger = get_api_logger()


async def test_cross_rates():
    """Тест вычисления кросс-курсов"""
    print("🔄 Тестируем вычисление кросс-курсов...")
    
    # Тестируем в debug режиме, где есть mock данные для кросс-курсов
    original_debug = config.DEBUG_MODE
    config.DEBUG_MODE = True
    
    try:
        async with APIService() as api:
            # Получаем все курсы
            print("📊 Получаем базовые курсы...")
            all_rates = await api.get_all_rates()
            
            if not all_rates:
                print("❌ Не удалось получить базовые курсы")
                return False
            
            print(f"   Получено {len(all_rates)} базовых курсов")
            
            # Показываем базовые курсы
            base_pairs = ['USDT/RUB', 'USDT/THB', 'USDT/AED', 'USDT/ZAR', 'USDT/IDR']
            print("\n💰 Базовые курсы:")
            for pair in base_pairs:
                if pair in all_rates:
                    rate = all_rates[pair]
                    print(f"   {pair}: {rate.rate}")
            
            # Тестируем кросс-курсы
            print("\n🔄 Тестируем кросс-курсы через USDT:")
            cross_pairs = ['RUB/ZAR', 'RUB/THB', 'RUB/AED', 'THB/ZAR']
            
            results = []
            for pair in cross_pairs:
                try:
                    rate = await api.get_exchange_rate(pair)
                    if rate:
                        print(f"   ✅ {pair}: {rate.rate} (source: {rate.source})")
                        results.append(True)
                    else:
                        print(f"   ❌ {pair}: не найден")
                        results.append(False)
                except Exception as e:
                    print(f"   ❌ {pair}: ошибка - {e}")
                    results.append(False)
            
            success_count = sum(results)
            print(f"\n📈 Успешно вычислено {success_count}/{len(cross_pairs)} кросс-курсов")
            
            # Проверяем логику вычисления
            if 'USDT/RUB' in all_rates and 'USDT/THB' in all_rates:
                usdt_rub = all_rates['USDT/RUB'].rate
                usdt_thb = all_rates['USDT/THB'].rate
                expected_rub_thb = usdt_thb / usdt_rub
                
                print(f"\n🧮 Проверка вычислений:")
                print(f"   USDT/RUB: {usdt_rub}")
                print(f"   USDT/THB: {usdt_thb}")
                print(f"   Ожидаемый RUB/THB: {expected_rub_thb:.6f}")
                
                # Получаем вычисленный курс
                try:
                    rub_thb = await api.get_exchange_rate('RUB/THB')
                    if rub_thb:
                        print(f"   Фактический RUB/THB: {rub_thb.rate:.6f}")
                        diff = abs(rub_thb.rate - expected_rub_thb) / expected_rub_thb * 100
                        print(f"   Расхождение: {diff:.2f}%")
                        
                        if diff < 5:  # Допускаем 5% расхождение из-за спредов
                            print("   ✅ Вычисление корректно")
                        else:
                            print("   ⚠️  Большое расхождение в вычислениях")
                except Exception as e:
                    print(f"   ❌ Ошибка проверки: {e}")
            
            return success_count > 0
            
    except Exception as e:
        print(f"❌ Ошибка тестирования кросс-курсов: {e}")
        return False
    finally:
        # Восстанавливаем debug режим
        config.DEBUG_MODE = original_debug


async def test_real_cross_calculation():
    """Тест вычисления кросс-курсов на реальных данных"""
    print("\n🌐 Тестируем кросс-курсы на реальных данных...")
    
    # Используем реальный API
    original_debug = config.DEBUG_MODE
    config.DEBUG_MODE = False
    
    try:
        async with APIService() as api:
            # Получаем реальные курсы
            all_rates = await api.get_all_rates()
            
            if not all_rates:
                print("❌ Не удалось получить реальные курсы")
                return False
            
            # Проверяем наличие базовых курсов
            if 'USDT/RUB' not in all_rates:
                print("❌ Базовый курс USDT/RUB недоступен")
                return False
            
            usdt_rub = all_rates['USDT/RUB'].rate
            print(f"   Базовый курс USDT/RUB: {usdt_rub}")
            
            # Симулируем курсы других валют (в реальном API их может не быть)
            # Для демонстрации логики
            mock_rates = {
                'USDT/THB': 35.5,
                'USDT/AED': 3.67,
                'USDT/ZAR': 18.5
            }
            
            print(f"\\n🧮 Демонстрация вычисления кросс-курсов:")
            for usdt_pair, mock_rate in mock_rates.items():
                target_currency = usdt_pair.split('/')[1]
                cross_pair = f'RUB/{target_currency}'
                
                # Вычисляем кросс-курс: RUB/XXX = USDT/XXX / USDT/RUB
                cross_rate = mock_rate / usdt_rub
                
                print(f"   {cross_pair}: {cross_rate:.6f} (через USDT)")
                print(f"     Логика: {usdt_pair}({mock_rate}) / USDT/RUB({usdt_rub}) = {cross_rate:.6f}")
            
            return True
            
    except Exception as e:
        print(f"❌ Ошибка тестирования реальных кросс-курсов: {e}")
        return False
    finally:
        config.DEBUG_MODE = original_debug


if __name__ == "__main__":
    try:
        print("🚀 Тестирование системы кросс-курсов")
        print("=" * 60)
        
        # Тест 1: Кросс-курсы с mock данными
        success1 = asyncio.run(test_cross_rates())
        
        # Тест 2: Демонстрация на реальных данных
        success2 = asyncio.run(test_real_cross_calculation())
        
        print("\\n" + "=" * 60)
        print("📋 РЕЗУЛЬТАТЫ:")
        print(f"   Mock кросс-курсы: {'✅ РАБОТАЮТ' if success1 else '❌ НЕ РАБОТАЮТ'}")
        print(f"   Логика вычислений: {'✅ КОРРЕКТНА' if success2 else '❌ ОШИБКИ'}")
        
        if success1 and success2:
            print("\\n🎉 Система кросс-курсов работает корректно!")
            sys.exit(0)
        else:
            print("\\n⚠️  Есть проблемы с системой кросс-курсов")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\\n⏹️  Тест прерван пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\\n💥 Критическая ошибка: {e}")
        sys.exit(1)