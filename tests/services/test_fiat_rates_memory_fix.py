#!/usr/bin/env python3
"""
Интеграционные тесты для исправления Memory Leak в FiatRatesService
TASK-PERF-001: Проверка интеграции с UnifiedCacheManager
"""

import pytest
import asyncio
import time
import sys
import os
from unittest.mock import AsyncMock, patch

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from services.fiat_rates_service import FiatRatesService, fiat_rates_service
from services.cache_manager import rates_cache
from config import config


class TestFiatRatesMemoryLeakFix:
    """Интеграционные тесты для FiatRatesService с исправленным кэшированием"""
    
    @pytest.fixture
    async def service(self):
        """Создаем экземпляр сервиса для тестирования"""
        service = FiatRatesService()
        await service.start_session()
        yield service
        await service.close_session()
    
    @pytest.mark.asyncio
    async def test_cache_usage_in_get_rates_from_base(self, service):
        """Тест 1: Проверка использования нового кэша в get_rates_from_base"""
        print("🧪 Test 1: Cache usage in get_rates_from_base")
        
        # Очищаем кэш
        await service.clear_cache()
        
        # Мокаем API запрос для возврата тестовых данных
        test_rates = {"EUR": 0.85, "RUB": 100.0, "GBP": 0.75}
        
        with patch.object(service.session, 'get') as mock_get:
            # Мокаем успешный API ответ
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {
                'success': True,
                'rates': test_rates
            }
            mock_get.return_value.__aenter__.return_value = mock_response
            
            # Первый запрос - должен обратиться к API
            initial_stats = service.get_cache_stats()
            rates1 = await service.get_rates_from_base("USD")
            
            assert rates1 == test_rates, "Should return mocked rates"
            
            # Второй запрос - должен использовать кэш
            rates2 = await service.get_rates_from_base("USD")
            
            assert rates2 == test_rates, "Should return cached rates"
            
            # Проверяем статистику кэша
            final_stats = service.get_cache_stats()
            
            print(f"📊 Initial cache hits: {initial_stats['total_hits']}")
            print(f"📊 Final cache hits: {final_stats['total_hits']}")
            
            # Должен быть как минимум один cache hit
            assert final_stats['total_hits'] > initial_stats['total_hits'], \
                "Cache should have at least one hit from second request"
            
            # API должен быть вызван только один раз (первый запрос)
            assert mock_get.call_count == 1, "API should be called only once due to caching"
            
            print("✅ Cache is working correctly in get_rates_from_base")
    
    @pytest.mark.asyncio
    async def test_cache_ttl_expiration(self, service):
        """Тест 2: Проверка истечения TTL в кэше"""
        print("🧪 Test 2: Cache TTL expiration")
        
        # Очищаем кэш
        await service.clear_cache()
        
        # Сохраняем данные в кэш вручную с коротким TTL
        test_rates = {"EUR": 0.85, "RUB": 100.0}
        
        # Используем прямой доступ к кэшу для установки короткого TTL
        rates_cache.set("rates_USD", test_rates, ttl=1)  # 1 секунда TTL
        
        # Проверяем что данные есть
        cached_rates = await service._get_cached_rates("USD")
        assert cached_rates == test_rates, "Should return cached data immediately"
        
        # Ждем истечения TTL
        time.sleep(2)
        
        # Проверяем что данные удалены
        expired_rates = await service._get_cached_rates("USD")
        assert expired_rates is None, "Cached data should expire after TTL"
        
        print("✅ TTL expiration works correctly")
    
    @pytest.mark.asyncio
    async def test_cache_size_limit_with_real_service(self, service):
        """Тест 3: Проверка ограничения размера кэша в реальном сервисе"""
        print("🧪 Test 3: Cache size limit with real service")
        
        # Очищаем кэш
        await service.clear_cache()
        
        # Заполняем кэш множеством валютных пар
        currencies = ['USD', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD', 'CHF', 'CNY']
        test_data = {}
        
        for base_currency in currencies:
            rates = {target: 1.0 + ord(target[0]) * 0.01 for target in currencies if target != base_currency}
            test_data[base_currency] = rates
            await service._cache_rates(base_currency, rates)
        
        # Добавляем еще данных для превышения лимита кэша
        for i in range(config.CACHE_MAX_SIZE):
            extra_rates = {"EXTRA": float(i)}
            await service._cache_rates(f"EXTRA_{i}", extra_rates)
        
        # Проверяем что размер кэша не превышает лимит
        final_stats = service.get_cache_stats()
        
        print(f"📊 Cache entries: {final_stats['current_entries']}/{final_stats['max_entries']}")
        print(f"📊 Memory usage: {final_stats['memory_usage_mb']:.2f}MB")
        
        assert final_stats['current_entries'] <= final_stats['max_entries'], \
            f"Cache size {final_stats['current_entries']} exceeds limit {final_stats['max_entries']}"
        
        print("✅ Cache size limit enforced correctly")
    
    @pytest.mark.asyncio
    async def test_memory_monitoring_accuracy(self, service):
        """Тест 4: Проверка точности мониторинга памяти"""
        print("🧪 Test 4: Memory monitoring accuracy")
        
        # Очищаем кэш и получаем базовую статистику
        await service.clear_cache()
        empty_stats = service.get_cache_stats()
        
        # Добавляем данные известного размера
        large_data = {
            "EUR": 0.85,
            "RUB": 100.0,
            "GBP": 0.75,
            "JPY": 149.0,
            "large_string": "x" * 10000  # 10KB строка
        }
        
        await service._cache_rates("MEMORY_TEST", large_data)
        
        # Получаем статистику после добавления данных
        filled_stats = service.get_cache_stats()
        
        print(f"📊 Empty cache memory: {empty_stats['memory_usage_mb']:.4f}MB")
        print(f"📊 Filled cache memory: {filled_stats['memory_usage_mb']:.4f}MB")
        print(f"📊 Memory increase: {filled_stats['memory_usage_mb'] - empty_stats['memory_usage_mb']:.4f}MB")
        
        # Проверяем что память увеличилась
        assert filled_stats['memory_usage_mb'] > empty_stats['memory_usage_mb'], \
            "Memory usage should increase when adding data"
        
        # Проверяем что есть разумная оценка размера
        memory_increase_bytes = (filled_stats['memory_usage_mb'] - empty_stats['memory_usage_mb']) * 1024 * 1024
        assert memory_increase_bytes > 5000, "Memory increase should be at least 5KB for large data"  # Минимум для наших данных
        
        print("✅ Memory monitoring works accurately")
    
    @pytest.mark.asyncio
    async def test_concurrent_cache_access(self, service):
        """Тест 5: Проверка безопасности concurrent доступа к кэшу"""
        print("🧪 Test 5: Concurrent cache access safety")
        
        await service.clear_cache()
        
        async def cache_worker(worker_id: int):
            """Воркер для параллельного доступа к кэшу"""
            for i in range(10):
                # Попеременно читаем и пишем в кэш
                await service._cache_rates(f"worker_{worker_id}_key_{i}", {"rate": float(worker_id * 100 + i)})
                cached_data = await service._get_cached_rates(f"worker_{worker_id}_key_{i}")
                assert cached_data is not None, f"Worker {worker_id} should find its own data"
        
        # Запускаем несколько параллельных воркеров
        workers = [cache_worker(i) for i in range(5)]
        
        # Выполняем все задачи параллельно
        await asyncio.gather(*workers)
        
        # Проверяем финальную статистику
        final_stats = service.get_cache_stats()
        
        print(f"📊 Final cache entries: {final_stats['current_entries']}")
        print(f"📊 Total hits: {final_stats['total_hits']}")
        print(f"📊 Total misses: {final_stats['total_misses']}")
        
        # Кэш должен остаться в согласованном состоянии
        assert final_stats['current_entries'] >= 0, "Cache should remain in consistent state"
        assert final_stats['current_entries'] <= final_stats['max_entries'], "Cache size should not exceed limit"
        
        print("✅ Concurrent access handled safely")
    
    @pytest.mark.asyncio
    async def test_cache_stats_comprehensive(self, service):
        """Тест 6: Проверка полноты статистики кэша"""
        print("🧪 Test 6: Comprehensive cache statistics")
        
        await service.clear_cache()
        
        # Выполняем различные операции для генерации статистики
        await service._cache_rates("STATS_USD", {"EUR": 0.85})  # Set
        await service._get_cached_rates("STATS_USD")  # Hit
        await service._get_cached_rates("NONEXISTENT")  # Miss
        
        stats = service.get_cache_stats()
        
        # Проверяем наличие всех ожидаемых полей
        expected_fields = [
            'service', 'timestamp', 'cache_manager', 'current_entries', 'max_entries',
            'utilization_percent', 'hit_ratio_percent', 'total_hits', 'total_misses',
            'memory_usage_mb', 'memory_usage_bytes', 'ttl_cleanups', 'lru_evictions',
            'ttl_seconds', 'cleanup_interval_seconds', 'status'
        ]
        
        for field in expected_fields:
            assert field in stats, f"Stats should contain {field}"
        
        # Проверяем типы и диапазоны значений
        assert isinstance(stats['current_entries'], int), "current_entries should be int"
        assert isinstance(stats['max_entries'], int), "max_entries should be int"
        assert 0 <= stats['utilization_percent'] <= 100, "utilization_percent should be 0-100"
        assert 0 <= stats['hit_ratio_percent'] <= 100, "hit_ratio_percent should be 0-100"
        assert stats['memory_usage_mb'] >= 0, "memory_usage_mb should be non-negative"
        assert stats['status'] in ['healthy', 'warning'], "status should be healthy or warning"
        
        print(f"📊 Cache stats structure validation passed")
        print(f"📊 Service: {stats['service']}")
        print(f"📊 Cache manager: {stats['cache_manager']}")
        print(f"📊 Utilization: {stats['utilization_percent']:.1f}%")
        print(f"📊 Hit ratio: {stats['hit_ratio_percent']:.1f}%")
        
        print("✅ Cache statistics are comprehensive and accurate")


class TestMemoryLeakRegression:
    """Регрессионные тесты для предотвращения возврата Memory Leak"""
    
    @pytest.mark.asyncio
    async def test_no_unlimited_cache_growth(self):
        """Тест 7: Проверка отсутствия безграничного роста кэша"""
        print("🧪 Test 7: No unlimited cache growth regression test")
        
        service = FiatRatesService()
        await service.clear_cache()
        
        # Симулируем интенсивное использование как в production
        base_currencies = ['USD', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD', 'CHF', 'CNY', 'RUB', 'ZAR']
        
        initial_stats = service.get_cache_stats()
        print(f"📊 Initial memory: {initial_stats['memory_usage_mb']:.4f}MB")
        
        # Добавляем много данных (симулируем несколько часов работы)
        for cycle in range(20):  # 20 циклов обновления курсов
            for base in base_currencies:
                # Каждый цикл добавляем курсы для всех валют
                rates = {target: 1.0 + cycle * 0.1 + ord(target[0]) * 0.01 
                        for target in base_currencies if target != base}
                await service._cache_rates(f"{base}_cycle_{cycle}", rates)
        
        final_stats = service.get_cache_stats()
        print(f"📊 Final memory: {final_stats['memory_usage_mb']:.4f}MB")
        print(f"📊 Final entries: {final_stats['current_entries']}/{final_stats['max_entries']}")
        print(f"📊 LRU evictions: {final_stats['lru_evictions']}")
        
        # КРИТИЧЕСКАЯ ПРОВЕРКА: кэш НЕ должен расти бесконечно
        assert final_stats['current_entries'] <= config.CACHE_MAX_SIZE, \
            f"MEMORY LEAK DETECTED: Cache has {final_stats['current_entries']} entries, limit is {config.CACHE_MAX_SIZE}"
        
        # Должны происходить evictions при превышении лимита
        assert final_stats['lru_evictions'] > 0, \
            "LRU evictions should occur to prevent unlimited growth"
        
        # Память не должна расти линейно с количеством операций
        memory_growth = final_stats['memory_usage_mb'] - initial_stats['memory_usage_mb']
        assert memory_growth < 50, \
            f"Memory growth {memory_growth:.2f}MB is too high - possible memory leak"
        
        print("✅ No unlimited cache growth detected - Memory leak is FIXED!")
    
    def test_old_cache_attributes_removed(self):
        """Тест 8: Проверка что старые атрибуты кэша удалены"""
        print("🧪 Test 8: Old cache attributes removed")
        
        service = FiatRatesService()
        
        # Проверяем что старый self._cache НЕ используется
        assert not hasattr(service, '_cache') or not service._cache, \
            "Old self._cache attribute should not be used - this would cause memory leak"
        
        print("✅ Old cache attributes properly removed")
    
    @pytest.mark.asyncio
    async def test_cache_cleanup_on_service_destruction(self):
        """Тест 9: Проверка очистки кэша при завершении работы сервиса"""
        print("🧪 Test 9: Cache cleanup on service destruction")
        
        # Создаем временный сервис
        temp_service = FiatRatesService()
        
        # Добавляем данные
        await temp_service._cache_rates("TEMP_USD", {"EUR": 0.85})
        
        # Проверяем что данные есть
        cached_data = await temp_service._get_cached_rates("TEMP_USD")
        assert cached_data is not None, "Data should be cached"
        
        # Очищаем кэш сервиса
        clear_result = await temp_service.clear_cache()
        
        # Проверяем что данные удалены
        assert clear_result['entries_removed'] > 0, "Should remove cached entries"
        
        cleared_data = await temp_service._get_cached_rates("TEMP_USD")
        assert cleared_data is None, "Data should be cleared"
        
        print("✅ Cache cleanup works correctly")


if __name__ == "__main__":
    print("🧪 Running FiatRatesService Memory Leak Fix Integration Tests")
    print("=" * 70)
    
    # Запускаем тесты
    pytest.main([__file__, "-v", "-s"])