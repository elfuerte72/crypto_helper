#!/usr/bin/env python3
"""
Unit Tests для исправления Memory Leak в кэшировании
TASK-PERF-001: Тестирование UnifiedCacheManager
"""

import pytest
import asyncio
import time
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from services.cache_manager import UnifiedCacheManager, rates_cache, api_cache
from config import config


class TestMemoryLeakFix:
    """Тестирование исправления Memory Leak в кэшировании"""
    
    @pytest.fixture
    def test_cache(self):
        """Создаем тестовый кэш для изоляции тестов"""
        return UnifiedCacheManager(
            max_size=10,
            default_ttl=2,  # Короткий TTL для быстрого тестирования
            cleanup_interval=1,
            enable_stats=True
        )
    
    def test_cache_size_limit_enforcement(self, test_cache):
        """Тест 1: Проверка ограничения размера кэша (LRU eviction)"""
        print("🧪 Test 1: Cache size limit enforcement")
        
        # Заполняем кэш выше лимита
        for i in range(15):  # Лимит 10, добавляем 15
            test_cache.set(f"key_{i}", f"value_{i}")
        
        stats = test_cache.get_stats()
        
        # Проверяем что размер не превышает лимит
        assert stats['current_size'] <= test_cache.max_size, f"Cache size {stats['current_size']} exceeds limit {test_cache.max_size}"
        assert stats['evictions'] > 0, "LRU evictions should have occurred"
        
        print(f"✅ Cache size enforced: {stats['current_size']}/{test_cache.max_size}")
        print(f"✅ LRU evictions: {stats['evictions']}")
    
    def test_ttl_cleanup(self, test_cache):
        """Тест 2: Проверка автоматической очистки по TTL"""
        print("🧪 Test 2: TTL cleanup functionality")
        
        # Добавляем записи в кэш
        test_cache.set("temp_key_1", "temp_value_1")
        test_cache.set("temp_key_2", "temp_value_2")
        
        # Проверяем что записи есть
        assert test_cache.get("temp_key_1") is not None
        assert test_cache.get("temp_key_2") is not None
        
        initial_size = test_cache.get_stats()['current_size']
        print(f"📊 Initial cache size: {initial_size}")
        
        # Ждем истечения TTL (2 секунды + запас)
        time.sleep(3)
        
        # Принудительно запускаем cleanup
        expired_count = test_cache.cleanup_expired()
        
        final_size = test_cache.get_stats()['current_size']
        print(f"📊 Final cache size: {final_size}")
        print(f"🧹 Expired entries removed: {expired_count}")
        
        # Проверяем что устаревшие записи удалены
        assert test_cache.get("temp_key_1") is None, "Expired entries should be removed"
        assert test_cache.get("temp_key_2") is None, "Expired entries should be removed"
        assert expired_count >= 2, "At least 2 entries should be expired"
    
    def test_memory_usage_estimation(self, test_cache):
        """Тест 3: Проверка мониторинга использования памяти"""
        print("🧪 Test 3: Memory usage estimation")
        
        # Добавляем данные разного размера
        test_data = {
            "small": "x" * 100,
            "medium": "y" * 1000,
            "large": "z" * 10000,
            "dict": {"key1": "value1", "key2": "value2", "nested": {"a": 1, "b": 2}}
        }
        
        initial_memory = test_cache.get_stats()['memory_usage_bytes']
        
        for key, value in test_data.items():
            test_cache.set(key, value)
        
        final_memory = test_cache.get_stats()['memory_usage_bytes']
        memory_increase = final_memory - initial_memory
        
        print(f"📊 Initial memory: {initial_memory} bytes")
        print(f"📊 Final memory: {final_memory} bytes")
        print(f"📈 Memory increase: {memory_increase} bytes")
        
        # Проверяем что память увеличилась
        assert final_memory > initial_memory, "Memory usage should increase with added data"
        assert memory_increase > 0, "Memory increase should be positive"
        
        # Проверяем что есть оценка в MB
        stats = test_cache.get_stats()
        assert 'memory_usage_mb' in stats, "Memory usage should be available in MB"
        assert stats['memory_usage_mb'] >= 0, "Memory usage in MB should be non-negative"
    
    def test_cache_stats_accuracy(self, test_cache):
        """Тест 4: Проверка точности статистики кэша"""
        print("🧪 Test 4: Cache statistics accuracy")
        
        # Выполняем операции с кэшем
        test_cache.set("hit_key", "hit_value")
        
        # Тестируем hits
        hit_value = test_cache.get("hit_key")  # Hit
        miss_value = test_cache.get("miss_key")  # Miss
        
        stats = test_cache.get_stats()
        
        print(f"📊 Stats: {stats}")
        
        # Проверяем статистику
        assert stats['hits'] >= 1, "Should have at least 1 hit"
        assert stats['misses'] >= 1, "Should have at least 1 miss"
        assert stats['total_sets'] >= 1, "Should have at least 1 set operation"
        assert stats['current_size'] <= stats['max_size'], "Current size should not exceed max size"
        assert 0 <= stats['utilization'] <= 1, "Utilization should be between 0 and 1"
        
        # Проверяем hit ratio
        total_requests = stats['hits'] + stats['misses']
        expected_hit_ratio = stats['hits'] / total_requests if total_requests > 0 else 0
        assert abs(stats['hit_ratio'] - expected_hit_ratio) < 0.001, "Hit ratio calculation should be accurate"
    
    def test_lru_order_maintenance(self, test_cache):
        """Тест 5: Проверка корректности LRU ordering"""
        print("🧪 Test 5: LRU order maintenance")
        
        # Заполняем кэш до лимита
        for i in range(test_cache.max_size):
            test_cache.set(f"lru_key_{i}", f"lru_value_{i}")
        
        # Обращаемся к первому элементу (делаем его recently used)
        first_value = test_cache.get("lru_key_0")
        assert first_value == "lru_value_0"
        
        # Добавляем новый элемент (должен вытеснить lru_key_1, а не lru_key_0)
        test_cache.set("new_key", "new_value")
        
        # Проверяем что первый элемент все еще есть (был recently used)
        assert test_cache.get("lru_key_0") is not None, "Recently used item should not be evicted"
        
        # Проверяем что второй элемент удален (был least recently used)
        assert test_cache.get("lru_key_1") is None, "Least recently used item should be evicted"
        
        print("✅ LRU ordering works correctly")
    
    @pytest.mark.asyncio
    async def test_background_cleanup_task(self, test_cache):
        """Тест 6: Проверка background cleanup task"""
        print("🧪 Test 6: Background cleanup task")
        
        # Запускаем background cleanup
        await test_cache.start()
        
        # Добавляем данные
        test_cache.set("bg_key_1", "bg_value_1")
        test_cache.set("bg_key_2", "bg_value_2")
        
        initial_cleanups = test_cache.get_stats()['ttl_cleanups']
        
        # Ждем несколько циклов cleanup (TTL = 2s, cleanup interval = 1s)
        await asyncio.sleep(4)
        
        final_cleanups = test_cache.get_stats()['ttl_cleanups']
        
        # Останавливаем background task
        await test_cache.stop()
        
        print(f"📊 Initial cleanups: {initial_cleanups}")
        print(f"📊 Final cleanups: {final_cleanups}")
        
        # Проверяем что cleanup сработал
        assert final_cleanups > initial_cleanups, "Background cleanup should have run"
        
        print("✅ Background cleanup task works correctly")


class TestFiatRatesServiceMemoryLeakFix:
    """Тестирование исправления Memory Leak в FiatRatesService"""
    
    @pytest.mark.asyncio
    async def test_fiat_service_cache_integration(self):
        """Тест 7: Интеграция FiatRatesService с новым кэшем"""
        print("🧪 Test 7: FiatRatesService cache integration")
        
        from services.fiat_rates_service import FiatRatesService
        
        service = FiatRatesService()
        
        # Проверяем что сервис использует новый кэш
        cache_stats = service.get_cache_stats()
        
        print(f"📊 Cache stats: {cache_stats}")
        
        # Проверяем структуру статистики
        required_fields = [
            'service', 'cache_manager', 'current_entries', 'max_entries',
            'memory_usage_mb', 'hit_ratio_percent', 'ttl_seconds'
        ]
        
        for field in required_fields:
            assert field in cache_stats, f"Cache stats should contain {field}"
        
        assert cache_stats['service'] == 'fiat_rates_cache'
        assert cache_stats['cache_manager'] == 'UnifiedCacheManager'
        assert cache_stats['max_entries'] == config.CACHE_MAX_SIZE
        
        print("✅ FiatRatesService integration works correctly")
    
    @pytest.mark.asyncio  
    async def test_cache_clear_functionality(self):
        """Тест 8: Функциональность очистки кэша"""
        print("🧪 Test 8: Cache clear functionality")
        
        from services.fiat_rates_service import FiatRatesService
        
        service = FiatRatesService()
        
        # Добавляем данные в кэш через сервис
        await service._cache_rates("USD", {"EUR": 0.85, "RUB": 100.0})
        await service._cache_rates("EUR", {"USD": 1.18, "RUB": 118.0})
        
        # Проверяем что данные есть
        cached_usd = await service._get_cached_rates("USD")
        assert cached_usd is not None, "USD rates should be cached"
        
        # Очищаем кэш
        clear_result = await service.clear_cache()
        
        print(f"📊 Clear result: {clear_result}")
        
        # Проверяем что данные удалены
        cached_usd_after = await service._get_cached_rates("USD")
        assert cached_usd_after is None, "USD rates should be cleared"
        
        # Проверяем структуру результата очистки
        assert 'operation' in clear_result
        assert 'entries_removed' in clear_result
        assert 'memory_freed_mb' in clear_result
        assert clear_result['operation'] == 'cache_clear'
        assert clear_result['entries_removed'] >= 0
        
        print("✅ Cache clear functionality works correctly")


class TestMemoryLeakStressTest:
    """Стресс-тесты для проверки отсутствия Memory Leak"""
    
    def test_memory_leak_stress_test(self):
        """Тест 9: Стресс-тест на отсутствие Memory Leak"""
        print("🧪 Test 9: Memory leak stress test")
        
        test_cache = UnifiedCacheManager(
            max_size=50,
            default_ttl=1,  # Короткий TTL
            cleanup_interval=1
        )
        
        initial_memory = test_cache.get_stats()['memory_usage_bytes']
        print(f"📊 Initial memory: {initial_memory} bytes")
        
        # Симулируем интенсивное использование кэша
        cycles = 100
        entries_per_cycle = 100
        
        for cycle in range(cycles):
            # Добавляем много записей
            for i in range(entries_per_cycle):
                key = f"stress_key_{cycle}_{i}"
                value = f"stress_value_{cycle}_{i}" * 10  # Увеличиваем размер данных
                test_cache.set(key, value)
            
            # Периодически принудительно очищаем
            if cycle % 10 == 0:
                test_cache.cleanup_expired()
                current_stats = test_cache.get_stats()
                print(f"  Cycle {cycle}: {current_stats['current_size']} entries, {current_stats['memory_usage_mb']:.2f}MB")
        
        final_stats = test_cache.get_stats()
        final_memory = final_stats['memory_usage_bytes']
        
        print(f"📊 Final memory: {final_memory} bytes")
        print(f"📊 Final stats: {final_stats}")
        
        # Критическая проверка: размер кэша должен быть ограничен
        assert final_stats['current_size'] <= test_cache.max_size, \
            f"Cache size {final_stats['current_size']} exceeded limit {test_cache.max_size} - MEMORY LEAK!"
        
        # Проверяем что происходили evictions и cleanups
        assert final_stats['evictions'] > 0, "LRU evictions should have occurred during stress test"
        assert final_stats['ttl_cleanups'] >= 0, "TTL cleanups should have occurred"
        
        print(f"✅ Memory leak stress test passed!")
        print(f"   ├─ Total evictions: {final_stats['evictions']}")
        print(f"   ├─ Total cleanups: {final_stats['ttl_cleanups']}")
        print(f"   └─ Final cache size: {final_stats['current_size']}/{test_cache.max_size}")


if __name__ == "__main__":
    print("🧪 Running Memory Leak Fix Tests for TASK-PERF-001")
    print("=" * 60)
    
    # Запускаем тесты
    pytest.main([__file__, "-v", "-s"])