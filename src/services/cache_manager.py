#!/usr/bin/env python3
"""
Unified Cache Manager for Crypto Helper Bot
Решает проблему Memory Leak с TTL cleanup и ограничением размера кэша
"""

import asyncio
import time
from typing import Dict, Optional, Any, Tuple
from dataclasses import dataclass
from collections import OrderedDict
import threading
import logging

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Запись в кэше с метаданными"""
    data: Any
    timestamp: float
    access_count: int = 0
    last_access: float = None
    
    def __post_init__(self):
        if self.last_access is None:
            self.last_access = self.timestamp


class UnifiedCacheManager:
    """
    Унифицированный менеджер кэша с:
    - TTL (Time To Live) cleanup
    - LRU (Least Recently Used) eviction
    - Ограничение размера кэша
    - Мониторинг использования памяти
    """
    
    def __init__(
        self,
        max_size: int = 100,
        default_ttl: int = 300,  # 5 минут
        cleanup_interval: int = 60,  # Очистка каждую минуту
        enable_stats: bool = True
    ):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cleanup_interval = cleanup_interval
        self.enable_stats = enable_stats
        
        # LRU cache implementation
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        
        # Статистика кэша
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'ttl_cleanups': 0,
            'total_sets': 0,
            'memory_usage_bytes': 0
        }
        
        # Background cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False
        
        logger.info(
            f"🗄️ Cache Manager initialized\n"
            f"   ├─ Max size: {self.max_size} entries\n"
            f"   ├─ Default TTL: {self.default_ttl}s\n"
            f"   ├─ Cleanup interval: {self.cleanup_interval}s\n"
            f"   └─ Stats enabled: {self.enable_stats}"
        )
    
    async def start(self):
        """Запуск background cleanup task"""
        if not self._running:
            self._running = True
            self._cleanup_task = asyncio.create_task(self._background_cleanup())
            logger.info("✅ Cache Manager background cleanup started")
    
    async def stop(self):
        """Остановка background cleanup task"""
        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
        logger.info("⏹️ Cache Manager stopped")
    
    def get(self, key: str) -> Optional[Any]:
        """
        Получить значение из кэша
        
        Args:
            key: Ключ кэша
            
        Returns:
            Значение или None если не найдено/устарело
        """
        with self._lock:
            if key not in self._cache:
                self._stats['misses'] += 1
                return None
            
            entry = self._cache[key]
            current_time = time.time()
            
            # Проверяем TTL
            if current_time - entry.timestamp > self.default_ttl:
                logger.debug(f"Cache key '{key}' expired (TTL: {self.default_ttl}s)")
                del self._cache[key]
                self._stats['misses'] += 1
                self._stats['ttl_cleanups'] += 1
                return None
            
            # Обновляем LRU order и статистику доступа
            entry.access_count += 1
            entry.last_access = current_time
            self._cache.move_to_end(key)  # Перемещаем в конец (most recently used)
            
            self._stats['hits'] += 1
            logger.debug(f"Cache HIT for key '{key}' (access #{entry.access_count})")
            return entry.data
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Сохранить значение в кэш
        
        Args:
            key: Ключ кэша
            value: Значение для сохранения
            ttl: TTL для этого значения (по умолчанию использует default_ttl)
        """
        with self._lock:
            current_time = time.time()
            
            # Создаем новую запись
            entry = CacheEntry(
                data=value,
                timestamp=current_time
            )
            
            # Если ключ уже существует, обновляем
            if key in self._cache:
                old_entry = self._cache[key]
                entry.access_count = old_entry.access_count
                logger.debug(f"Cache UPDATE for key '{key}'")
            else:
                logger.debug(f"Cache SET for key '{key}'")
            
            self._cache[key] = entry
            self._cache.move_to_end(key)  # Новые записи в конец
            self._stats['total_sets'] += 1
            
            # Принудительная очистка при превышении размера
            self._enforce_size_limit()
    
    def delete(self, key: str) -> bool:
        """
        Удалить ключ из кэша
        
        Args:
            key: Ключ для удаления
            
        Returns:
            True если ключ был найден и удален
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"Cache DELETE for key '{key}'")
                return True
            return False
    
    def clear(self) -> None:
        """Очистить весь кэш"""
        with self._lock:
            old_size = len(self._cache)
            self._cache.clear()
            logger.info(f"Cache CLEARED: removed {old_size} entries")
    
    def _enforce_size_limit(self) -> None:
        """Принудительное ограничение размера кэша (LRU eviction)"""
        while len(self._cache) > self.max_size:
            # Удаляем самый старый (least recently used) элемент
            oldest_key = next(iter(self._cache))
            oldest_entry = self._cache[oldest_key]
            
            logger.debug(
                f"LRU EVICTION: removing '{oldest_key}' "
                f"(age: {time.time() - oldest_entry.timestamp:.1f}s, "
                f"accesses: {oldest_entry.access_count})"
            )
            
            del self._cache[oldest_key]
            self._stats['evictions'] += 1
    
    def cleanup_expired(self) -> int:
        """
        Ручная очистка устаревших записей
        
        Returns:
            Количество удаленных записей
        """
        with self._lock:
            current_time = time.time()
            expired_keys = []
            
            for key, entry in self._cache.items():
                if current_time - entry.timestamp > self.default_ttl:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._cache[key]
                self._stats['ttl_cleanups'] += 1
            
            if expired_keys:
                logger.info(f"TTL CLEANUP: removed {len(expired_keys)} expired entries")
            
            return len(expired_keys)
    
    async def _background_cleanup(self) -> None:
        """Background task для автоматической очистки"""
        logger.info(f"🔄 Background cleanup started (interval: {self.cleanup_interval}s)")
        
        while self._running:
            try:
                await asyncio.sleep(self.cleanup_interval)
                
                if not self._running:
                    break
                
                # Выполняем очистку
                expired_count = self.cleanup_expired()
                
                # Логируем статистику каждые 10 минут
                if int(time.time()) % 600 == 0:  # Каждые 10 минут
                    stats = self.get_stats()
                    logger.info(
                        f"📊 Cache Stats:\n"
                        f"   ├─ Entries: {stats['current_size']}/{self.max_size}\n"
                        f"   ├─ Hit ratio: {stats['hit_ratio']:.1%}\n"
                        f"   ├─ Total cleanups: {stats['ttl_cleanups']}\n"
                        f"   └─ Total evictions: {stats['evictions']}"
                    )
                
            except asyncio.CancelledError:
                logger.info("Background cleanup cancelled")
                break
            except Exception as e:
                logger.error(f"Background cleanup error: {e}")
                # Продолжаем работу даже при ошибках
                await asyncio.sleep(5)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Получить статистику кэша
        
        Returns:
            Словарь со статистикой
        """
        with self._lock:
            total_requests = self._stats['hits'] + self._stats['misses']
            hit_ratio = self._stats['hits'] / total_requests if total_requests > 0 else 0.0
            
            # Примерная оценка использования памяти
            memory_usage = self._estimate_memory_usage()
            
            return {
                'current_size': len(self._cache),
                'max_size': self.max_size,
                'hits': self._stats['hits'],
                'misses': self._stats['misses'],
                'hit_ratio': hit_ratio,
                'evictions': self._stats['evictions'],
                'ttl_cleanups': self._stats['ttl_cleanups'],
                'total_sets': self._stats['total_sets'],
                'memory_usage_bytes': memory_usage,
                'memory_usage_mb': memory_usage / (1024 * 1024),
                'utilization': len(self._cache) / self.max_size if self.max_size > 0 else 0.0
            }
    
    def _estimate_memory_usage(self) -> int:
        """
        Примерная оценка использования памяти кэшем
        
        Returns:
            Размер в байтах (приблизительно)
        """
        total_size = 0
        
        for key, entry in self._cache.items():
            # Размер ключа
            total_size += len(key.encode('utf-8'))
            
            # Размер данных (примерная оценка)
            if isinstance(entry.data, str):
                total_size += len(entry.data.encode('utf-8'))
            elif isinstance(entry.data, dict):
                # Для словарей используем приблизительную оценку
                total_size += len(str(entry.data).encode('utf-8'))
            elif isinstance(entry.data, (int, float)):
                total_size += 8  # Примерный размер числа
            else:
                total_size += 64  # Дефолтная оценка для других типов
            
            # Размер метаданных CacheEntry
            total_size += 64  # timestamp, access_count, last_access
        
        return total_size
    
    def has_key(self, key: str) -> bool:
        """Проверить существование ключа в кэше (без обновления LRU)"""
        with self._lock:
            if key not in self._cache:
                return False
            
            entry = self._cache[key]
            current_time = time.time()
            
            # Проверяем TTL без обновления статистики
            return (current_time - entry.timestamp) <= self.default_ttl


# Глобальные экземпляры кэш-менеджеров для разных типов данных

# Кэш для курсов валют (быстрое устаревание)
rates_cache = UnifiedCacheManager(
    max_size=100,
    default_ttl=300,  # 5 минут
    cleanup_interval=60,
    enable_stats=True
)

# Кэш для API ответов (среднее устаревание)
api_cache = UnifiedCacheManager(
    max_size=50,
    default_ttl=600,  # 10 минут
    cleanup_interval=120,
    enable_stats=True
)

# Кэш для статических данных (медленное устаревание)
static_cache = UnifiedCacheManager(
    max_size=20,
    default_ttl=3600,  # 1 час
    cleanup_interval=300,
    enable_stats=True
)


async def start_all_caches():
    """Запустить все кэш-менеджеры"""
    await rates_cache.start()
    await api_cache.start()
    await static_cache.start()
    logger.info("🚀 All cache managers started")


async def stop_all_caches():
    """Остановить все кэш-менеджеры"""
    await rates_cache.stop()
    await api_cache.stop()
    await static_cache.stop()
    logger.info("⏹️ All cache managers stopped")


def get_all_cache_stats() -> Dict[str, Any]:
    """Получить статистику всех кэшей"""
    return {
        'rates_cache': rates_cache.get_stats(),
        'api_cache': api_cache.get_stats(),
        'static_cache': static_cache.get_stats(),
        'total_memory_mb': sum([
            rates_cache.get_stats()['memory_usage_mb'],
            api_cache.get_stats()['memory_usage_mb'],
            static_cache.get_stats()['memory_usage_mb']
        ])
    }