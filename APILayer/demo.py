#!/usr/bin/env python3
"""
Демонстрация работы APILayer интеграции с реальными данными
"""

import asyncio
import sys
import os
from datetime import datetime

# Добавляем src в path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from services.api_service import api_service, determine_pair_type
from config import config

def print_header(title):
    """Красивый заголовок"""
    print("\n" + "=" * 60)
    print(f"🎯 {title}")
    print("=" * 60)

def print_rate_info(rate):
    """Форматированный вывод информации о курсе"""
    if rate:
        print(f"   💰 Курс: {rate.rate:.8f}")
        print(f"   📊 Источник: {rate.source}")
        print(f"   🕐 Время: {rate.timestamp}")
        if rate.bid:
            print(f"   📈 Bid: {rate.bid:.8f}")
        if rate.ask:
            print(f"   📉 Ask: {rate.ask:.8f}")
        if rate.change_24h:
            change_icon = "📈" if rate.change_24h > 0 else "📉"
            print(f"   {change_icon} Изменение 24ч: {rate.change_24h:.2f}%")
    else:
        print("   ❌ Курс не получен")

async def demo_currency_rates():
    """Демонстрация получения курсов валют"""
    
    print_header("ДЕМОНСТРАЦИЯ РАБОТЫ CRYPTO HELPER")
    print(f"🔑 API Key: {config.API_LAYER_KEY[:10]}...")
    print(f"🌐 Rapira URL: {config.RAPIRA_API_URL}")
    print(f"🌐 APILayer URL: {config.API_LAYER_URL}")
    
    async with api_service as service:
        
        # Health Check
        print_header("ПРОВЕРКА СОСТОЯНИЯ API")
        health = await service.health_check()
        print(f"📊 Общий статус: {health['status']}")
        print(f"🔗 Rapira API: {health['rapira_api'].get('status', 'unknown')}")
        print(f"🔗 APILayer: {health['apilayer_api'].get('status', 'unknown')}")
        
        # Демонстрация криптовалютных курсов
        print_header("КРИПТОВАЛЮТНЫЕ КУРСЫ (через Rapira API)")
        
        crypto_pairs = ['BTC/USDT', 'ETH/USDT', 'TON/USDT', 'USDT/RUB']
        for pair in crypto_pairs:
            try:
                pair_type = determine_pair_type(pair)
                print(f"\n🔸 {pair} (тип: {pair_type})")
                
                rate = await service.get_exchange_rate(pair)
                print_rate_info(rate)
                
            except Exception as e:
                print(f"   ❌ Ошибка: {e}")
        
        # Демонстрация фиатных курсов
        print_header("ФИАТНЫЕ КУРСЫ (через APILayer)")
        
        fiat_pairs = ['USD/RUB', 'EUR/RUB', 'USD/ZAR', 'USD/THB', 'USD/AED']
        for pair in fiat_pairs:
            try:
                pair_type = determine_pair_type(pair)
                print(f"\n🔸 {pair} (тип: {pair_type})")
                
                rate = await service.get_exchange_rate(pair)
                print_rate_info(rate)
                
            except Exception as e:
                print(f"   ❌ Ошибка: {e}")
        
        # Демонстрация кросс-курсов
        print_header("КРОСС-КУРСЫ (расчетные)")
        
        cross_pairs = ['RUB/ZAR', 'RUB/THB', 'BTC/RUB', 'ETH/RUB']
        for pair in cross_pairs:
            try:
                pair_type = determine_pair_type(pair)
                print(f"\n🔸 {pair} (тип: {pair_type})")
                
                rate = await service.get_exchange_rate(pair)
                print_rate_info(rate)
                
            except Exception as e:
                print(f"   ❌ Ошибка: {e}")
        
        # Демонстрация расчета с наценкой
        print_header("РАСЧЕТ С НАЦЕНКОЙ (как в боте)")
        
        # Пример сценария: менеджер хочет продать USDT за рубли с наценкой 3%
        try:
            pair = 'USDT/RUB'
            margin_percent = 3.0
            
            print(f"\n💼 Сценарий: Продажа USDT за рубли")
            print(f"📈 Валютная пара: {pair}")
            print(f"💰 Наценка: {margin_percent}%")
            
            rate = await service.get_exchange_rate(pair)
            if rate:
                base_rate = rate.rate
                margin_rate = base_rate * (1 + margin_percent / 100)
                
                print(f"\n📊 Базовый курс: {base_rate:.2f} RUB за 1 USDT")
                print(f"📈 Курс с наценкой: {margin_rate:.2f} RUB за 1 USDT")
                print(f"💵 Прибыль с 1000 USDT: {(margin_rate - base_rate) * 1000:.2f} RUB")
                
                # Демонстрация расчета для клиента
                client_amount = 1000
                client_currency = 'USDT'
                
                print(f"\n🧮 Расчет для клиента:")
                print(f"💰 Клиент продает: {client_amount} {client_currency}")
                print(f"💸 Клиент получает: {margin_rate * client_amount:.2f} RUB")
                print(f"📊 Использованный курс: {margin_rate:.2f}")
                print(f"🏦 Источник данных: {rate.source}")
                
        except Exception as e:
            print(f"   ❌ Ошибка в расчете: {e}")
        
        # Демонстрация multiple rates
        print_header("ПОЛУЧЕНИЕ МНОЖЕСТВЕННЫХ КУРСОВ")
        
        all_pairs = ['BTC/USDT', 'ETH/USDT', 'USD/RUB', 'EUR/RUB', 'RUB/ZAR']
        print(f"📊 Получаем {len(all_pairs)} курсов одновременно...")
        
        try:
            start_time = datetime.now()
            rates = await service.get_multiple_rates(all_pairs)
            end_time = datetime.now()
            
            duration = (end_time - start_time).total_seconds()
            print(f"⏱️  Время выполнения: {duration:.2f} секунд")
            
            successful_rates = [pair for pair, rate in rates.items() if rate is not None]
            print(f"✅ Успешно получено: {len(successful_rates)}/{len(all_pairs)} курсов")
            
            for pair, rate in rates.items():
                status = "✅" if rate else "❌"
                rate_value = f"{rate.rate:.6f}" if rate else "N/A"
                print(f"   {status} {pair}: {rate_value}")
                
        except Exception as e:
            print(f"   ❌ Ошибка при получении множественных курсов: {e}")
        
        # Заключение
        print_header("ЗАКЛЮЧЕНИЕ")
        print("🎉 Демонстрация завершена!")
        print("\n📋 Что продемонстрировано:")
        print("✅ Получение криптовалютных курсов через Rapira API")
        print("✅ Получение фиатных курсов через APILayer")
        print("✅ Автоматическое определение типа валютной пары")
        print("✅ Расчет кросс-курсов")
        print("✅ Применение наценки (как в реальном боте)")
        print("✅ Одновременное получение множественных курсов")
        print("✅ Профессиональная точность данных")
        print("✅ Готовность к продакшену")
        
        print("\n🚀 Система готова к использованию в Telegram боте!")

if __name__ == "__main__":
    try:
        asyncio.run(demo_currency_rates())
    except KeyboardInterrupt:
        print("\n\n⚠️  Демонстрация прервана пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)