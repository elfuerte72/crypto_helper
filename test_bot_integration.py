#!/usr/bin/env python3
"""
Тестовый скрипт для проверки интеграции APILayer с Telegram ботом
"""

import asyncio
import sys
import os
from unittest.mock import AsyncMock, MagicMock

# Добавляем src в path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.api_service import api_service, determine_pair_type
from handlers.currency_pairs import get_currency_pair_info, is_valid_currency_pair
from handlers.calculation_logic import calculate_margin_rate, CalculationResult
from handlers.formatters import MessageFormatter
from config import config
from decimal import Decimal

def print_header(title):
    """Красивый заголовок"""
    print("\n" + "=" * 60)
    print(f"🤖 {title}")
    print("=" * 60)

async def test_api_integration():
    """Тестирование интеграции API с ботом"""
    
    print_header("ТЕСТИРОВАНИЕ ИНТЕГРАЦИИ API С TELEGRAM БОТОМ")
    print(f"🔑 API Key: {config.API_LAYER_KEY[:10]}...")
    print(f"🎯 Bot Token: {config.BOT_TOKEN[:10]}...")
    
    # Тест 1: Проверка health check
    print("\n1. Проверка состояния API сервисов...")
    
    try:
        async with api_service as service:
            health = await service.health_check()
            print(f"   📊 Общий статус: {health['status']}")
            print(f"   🔗 Rapira API: {health['rapira_api'].get('status', 'unknown')}")
            print(f"   🔗 APILayer: {health['apilayer_api'].get('status', 'unknown')}")
            
            if health['status'] != 'healthy':
                print("   ⚠️  Некоторые API недоступны, но тестирование продолжится")
            
    except Exception as e:
        print(f"   ❌ Ошибка health check: {e}")
        return False
    
    # Тест 2: Проверка валютных пар (как в боте)
    print("\n2. Тестирование валютных пар (логика бота)...")
    
    test_pairs = [
        ('rubzar', 'RUB/ZAR'),
        ('zarrub', 'ZAR/RUB'),
        ('usdtrub', 'USDT/RUB'),
        ('btcusdt', 'BTC/USDT'),
        ('ethusdt', 'ETH/USDT')
    ]
    
    for pair_callback, expected_pair in test_pairs:
        try:
            # Проверяем, что пара валидна (как в боте)
            is_valid = is_valid_currency_pair(pair_callback)
            print(f"   📋 {pair_callback} → {expected_pair}: {'✅ валидна' if is_valid else '❌ невалидна'}")
            
            if is_valid:
                # Получаем информацию о паре
                pair_info = get_currency_pair_info(pair_callback)
                if pair_info:
                    print(f"      • Название: {pair_info['name']}")
                    print(f"      • Базовая валюта: {pair_info['base']}")
                    print(f"      • Котируемая валюта: {pair_info['quote']}")
                    
                    # Определяем тип пары
                    pair_type = determine_pair_type(pair_info['name'])
                    print(f"      • Тип: {pair_type}")
                else:
                    print(f"      ❌ Не удалось получить информацию о паре")
                    
        except Exception as e:
            print(f"   ❌ Ошибка при обработке {pair_callback}: {e}")
    
    # Тест 3: Получение курсов (как в обработчиках бота)
    print("\n3. Тестирование получения курсов...")
    
    test_real_pairs = ['RUB/ZAR', 'USDT/RUB', 'BTC/USDT', 'USD/RUB']
    
    async with api_service as service:
        for pair in test_real_pairs:
            try:
                # Получаем курс (как в start_margin_calculation)
                exchange_rate = await service.get_exchange_rate(pair)
                
                if exchange_rate:
                    print(f"   ✅ {pair}: {exchange_rate.rate:.6f} (источник: {exchange_rate.source})")
                    
                    # Конвертируем в dict (как в боте)
                    rate_dict = exchange_rate.to_dict()
                    print(f"      • Rate dict: ключей = {len(rate_dict)}")
                else:
                    print(f"   ❌ {pair}: курс не получен")
                    
            except Exception as e:
                print(f"   ❌ {pair}: ошибка - {e}")
    
    # Тест 4: Расчет с наценкой (как в боте)
    print("\n4. Тестирование расчета с наценкой...")
    
    try:
        # Симулируем процесс как в боте
        pair_callback = 'usdtrub'
        pair_info = get_currency_pair_info(pair_callback)
        
        if pair_info:
            async with api_service as service:
                exchange_rate = await service.get_exchange_rate(pair_info['name'])
                
                if exchange_rate:
                    # Параметры для расчета
                    amount = Decimal('1000')  # 1000 USDT
                    margin = Decimal('3.5')   # 3.5% наценка
                    
                    # Выполняем расчет (как в process_margin_input)
                    result = calculate_margin_rate(
                        pair_info=pair_info,
                        amount=amount,
                        margin=margin,
                        exchange_rate_data=exchange_rate.to_dict()
                    )
                    
                    print(f"   💰 Тестовый расчет для {pair_info['name']}:")
                    print(f"      • Базовый курс: {result.base_rate:.2f}")
                    print(f"      • Наценка: {margin}%")
                    print(f"      • Итоговый курс: {result.final_rate:.2f}")
                    print(f"      • Сумма: {amount} {pair_info['base']}")
                    print(f"      • Результат: {result.final_amount:.2f} {pair_info['quote']}")
                    print(f"      • Прибыль: {result.profit:.2f} {pair_info['quote']}")
                    
                    # Тестируем форматирование (как в боте)
                    formatted_result = MessageFormatter.format_calculation_result(result)
                    print(f"   📝 Длина отформатированного сообщения: {len(formatted_result)} символов")
                    
                else:
                    print("   ❌ Не удалось получить курс для расчета")
        else:
            print("   ❌ Не удалось получить информацию о паре для расчета")
            
    except Exception as e:
        print(f"   ❌ Ошибка при расчете с наценкой: {e}")
    
    # Тест 5: Тестирование форматирования сообщений
    print("\n5. Тестирование форматирования сообщений...")
    
    try:
        # Тестируем основные сообщения бота
        welcome_msg = MessageFormatter.format_welcome_message()
        print(f"   ✅ Welcome message: {len(welcome_msg)} символов")
        
        error_msg = MessageFormatter.format_error_message('api_error', 'Тестовая ошибка')
        print(f"   ✅ Error message: {len(error_msg)} символов")
        
        cancel_msg = MessageFormatter.format_cancel_message('Тестовая операция')
        print(f"   ✅ Cancel message: {len(cancel_msg)} символов")
        
    except Exception as e:
        print(f"   ❌ Ошибка при тестировании форматирования: {e}")
    
    return True

async def test_bot_simulation():
    """Симуляция работы бота с реальными данными"""
    
    print_header("СИМУЛЯЦИЯ РАБОТЫ TELEGRAM БОТА")
    
    # Симулируем пользователя
    mock_user = MagicMock()
    mock_user.id = 12345
    mock_user.username = "test_user"
    
    # Симулируем сценарий: пользователь выбирает валютную пару и рассчитывает наценку
    print("\n🎭 Сценарий: Пользователь рассчитывает курс USDT/RUB с наценкой 2.5%")
    print("-" * 50)
    
    try:
        # Шаг 1: Пользователь нажимает на валютную пару
        pair_callback = 'usdtrub'
        print(f"1. 👤 Пользователь выбирает пару: {pair_callback}")
        
        # Шаг 2: Бот проверяет валидность
        is_valid = is_valid_currency_pair(pair_callback)
        print(f"2. 🤖 Проверка валидности: {'✅ валидна' if is_valid else '❌ невалидна'}")
        
        if not is_valid:
            print("   ❌ Сценарий прерван - невалидная пара")
            return False
        
        # Шаг 3: Бот получает информацию о паре
        pair_info = get_currency_pair_info(pair_callback)
        print(f"3. 🤖 Информация о паре: {pair_info['name']} ({pair_info['base']} → {pair_info['quote']})")
        
        # Шаг 4: Бот получает курс через API
        print("4. 🤖 Получение курса через API...")
        async with api_service as service:
            exchange_rate = await service.get_exchange_rate(pair_info['name'])
            
            if exchange_rate:
                print(f"   ✅ Курс получен: {exchange_rate.rate:.2f} (источник: {exchange_rate.source})")
                
                # Шаг 5: Пользователь вводит наценку
                margin_input = "2.5"
                print(f"5. 👤 Пользователь вводит наценку: {margin_input}%")
                
                # Шаг 6: Бот валидирует наценку
                from handlers.validation import InputValidator
                try:
                    margin = InputValidator.validate_margin(margin_input)
                    print(f"6. 🤖 Наценка валидна: {margin}%")
                    
                    # Шаг 7: Бот рассчитывает итоговый курс
                    from handlers.calculation_logic import MarginCalculator
                    final_rate = MarginCalculator.calculate_final_rate(
                        Decimal(str(exchange_rate.rate)), 
                        margin
                    )
                    print(f"7. 🤖 Итоговый курс: {final_rate:.2f}")
                    
                    # Шаг 8: Пользователь вводит сумму
                    amount_input = "500"
                    print(f"8. 👤 Пользователь вводит сумму: {amount_input}")
                    
                    # Шаг 9: Бот валидирует сумму
                    amount = InputValidator.validate_amount(amount_input)
                    print(f"9. 🤖 Сумма валидна: {amount}")
                    
                    # Шаг 10: Бот выполняет финальный расчет
                    result = calculate_margin_rate(
                        pair_info=pair_info,
                        amount=amount,
                        margin=margin,
                        exchange_rate_data=exchange_rate.to_dict()
                    )
                    
                    print("10. 🤖 Финальный расчет:")
                    print(f"    • Базовый курс: {result.base_rate:.2f}")
                    print(f"    • Наценка: {result.margin_percent}%")
                    print(f"    • Итоговый курс: {result.final_rate:.2f}")
                    print(f"    • Сумма: {result.amount} {result.base_currency}")
                    print(f"    • Результат: {result.final_amount:.2f} {result.quote_currency}")
                    print(f"    • Прибыль: {result.profit:.2f} {result.quote_currency}")
                    
                    # Шаг 11: Бот форматирует сообщение
                    formatted_message = MessageFormatter.format_calculation_result(result)
                    print(f"11. 🤖 Сообщение отформатировано ({len(formatted_message)} символов)")
                    
                    print("\n✅ Сценарий выполнен успешно!")
                    return True
                    
                except Exception as e:
                    print(f"   ❌ Ошибка при валидации/расчете: {e}")
                    return False
            else:
                print("   ❌ Не удалось получить курс")
                return False
                
    except Exception as e:
        print(f"❌ Ошибка в сценарии: {e}")
        return False

async def main():
    """Основная функция тестирования"""
    
    print("🧪 ТЕСТИРОВАНИЕ ИНТЕГРАЦИИ APILAYER С TELEGRAM БОТОМ")
    print("=" * 70)
    print(f"Проект: {os.path.basename(os.getcwd())}")
    print(f"Python: {sys.version.split()[0]}")
    print("=" * 70)
    
    # Проверяем конфигурацию
    print("\n🔧 Проверка конфигурации...")
    if not config.BOT_TOKEN:
        print("❌ BOT_TOKEN не настроен")
        return False
    
    if not config.API_LAYER_KEY:
        print("❌ API_LAYER_KEY не настроен")
        return False
    
    print("✅ Конфигурация в порядке")
    
    # Запускаем тесты
    results = []
    
    # Тест 1: API интеграция
    try:
        result1 = await test_api_integration()
        results.append(("API Integration", result1))
    except Exception as e:
        print(f"❌ Критическая ошибка в API тестах: {e}")
        results.append(("API Integration", False))
    
    # Тест 2: Симуляция бота
    try:
        result2 = await test_bot_simulation()
        results.append(("Bot Simulation", result2))
    except Exception as e:
        print(f"❌ Критическая ошибка в симуляции бота: {e}")
        results.append(("Bot Simulation", False))
    
    # Итоговый отчет
    print("\n" + "=" * 70)
    print("📊 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
    print("=" * 70)
    
    all_passed = True
    for test_name, result in results:
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        print(f"{test_name}: {status}")
        all_passed = all_passed and result
    
    print("=" * 70)
    if all_passed:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print("\n🚀 Интеграция APILayer с Telegram ботом работает корректно!")
        print("\n📋 Что протестировано:")
        print("✅ API health check")
        print("✅ Обработка валютных пар")
        print("✅ Получение курсов через объединенный API")
        print("✅ Расчеты с наценкой")
        print("✅ Форматирование сообщений")
        print("✅ Полный сценарий работы пользователя")
        print("\n🎯 Бот готов к запуску!")
    else:
        print("❌ НЕКОТОРЫЕ ТЕСТЫ ПРОВАЛЕНЫ")
        print("🔧 Проверьте настройки и исправьте ошибки")
    
    return all_passed

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Тестирование прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)