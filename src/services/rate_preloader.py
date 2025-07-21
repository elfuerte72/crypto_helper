#!/usr/bin/env python3
"""
Rate Preloader for Crypto Helper Bot
Предзагрузка популярных курсов валют для ускорения ответов
TASK-PERF-002: Оптимизация API Performance
"""

import asyncio
import time
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

try:
    from ..config import config
    from ..utils.logger import get_api_logger
    from .models import ExchangeRate
    from .cache_manager import rates_cache, api_cache
except ImportError:
    # Handle direct execution
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from config import config
    from utils.logger import get_api_logger
    from services.models import ExchangeRate
    from services.cache_manager import rates_cache, api_cache

logger = get_api_logger()


@dataclass
class PreloadConfig:
    """Конфигурация предзагрузки"""
    pairs: List[str]
    interval: int  # Интервал в секундах
    priority: int  # Приоритет (чем меньше, тем выше)
    enabled: bool = True


@dataclass
class PreloadStats:
    """Статистика предзагрузки"""
    total_attempts: int = 0
    successful_loads: int = 0
    failed_loads: int = 0
    last_run: Optional[datetime] = None
    average_duration: float = 0.0
    cache_hit_ratio: float = 0.0


class SmartRatePreloader:
    """
    Умный предзагрузчик курсов с адаптивными интервалами и приоритизацией
    """
    
    def __init__(self):
        # Конфигурации предзагрузки по категориям
        self.preload_configs = {
            'critical': PreloadConfig(
                pairs=['USDT/RUB', 'USD/RUB', 'EUR/RUB'],
                interval=60,  # Каждую минуту
                priority=1
            ),
            'popular': PreloadConfig(
                pairs=['BTC/USDT', 'ETH/USDT', 'BTC/RUB', 'ETH/RUB'],
                interval=120,  # Каждые 2 минуты
                priority=2
            ),
            'secondary': PreloadConfig(
                pairs=['TON/USDT', 'SOL/USDT', 'ADA/USDT', 'DOT/USDT'],
                interval=300,  # Каждые 5 минут
                priority=3
            ),
            'fiat_cross': PreloadConfig(
                pairs=['USD/EUR', 'EUR/USD', 'GBP/USD', 'JPY/USD'],
                interval=180,  # Каждые 3 минуты
                priority=2
            )
        }
        
        # Статистика по категориям
        self.stats: Dict[str, PreloadStats] = {
            category: PreloadStats() for category in self.preload_configs.keys()
        }
        
        # Состояние предзагрузчика
        self.running = False
        self.tasks: Dict[str, asyncio.Task] = {}
        self.unified_manager = None
        
        # Адаптивные настройки
        self.adaptive_intervals = True
        self.min_interval = 30  # Минимальный интервал
        self.max_interval = 600  # Максимальный интервал
        
        logger.info(
            f"🧠 Smart Rate Preloader initialized\n"
            f"   ├─ Categories: {len(self.preload_configs)}\n"
            f"   ├─ Total pairs: {sum(len(cfg.pairs) for cfg in self.preload_configs.values())}\n"
            f"   ├─ Adaptive intervals: {self.adaptive_intervals}\n"
            f"   └─ Interval range: {self.min_interval}-{self.max_interval}s"
        )
    
    async def start(self, unified_manager):
        """Запустить предзагрузчик"""
        if self.running:
            logger.warning("Smart Rate Preloader already running")
            return
        
        self.unified_manager = unified_manager
        self.running = True
        
        # Запускаем задачи для каждой категории
        for category, config in self.preload_configs.items():
            if config.enabled:
                task = asyncio.create_task(
                    self._preload_category_loop(category, config)
                )
                self.tasks[category] = task
        
        logger.info(f"✅ Smart Rate Preloader started with {len(self.tasks)} categories")
    
    async def stop(self):
        """Остановить предзагрузчик"""
        self.running = False
        
        # Отменяем все задачи
        for category, task in self.tasks.items():
            if not task.done():
                task.cancel()
        
        # Ждем завершения всех задач
        if self.tasks:
            await asyncio.gather(*self.tasks.values(), return_exceptions=True)
        
        self.tasks.clear()
        logger.info("⏹️ Smart Rate Preloader stopped")
    
    async def _preload_category_loop(self, category: str, config: PreloadConfig):
        """Цикл предзагрузки для категории"""
        logger.info(f"🔄 Starting preload loop for category '{category}' ({len(config.pairs)} pairs)")
        
        while self.running:
            try:
                start_time = time.time()
                
                # Выполняем предзагрузку
                success_count = await self._preload_category(category, config)
                
                # Обновляем статистику
                duration = time.time() - start_time
                stats = self.stats[category]
                stats.total_attempts += 1
                stats.successful_loads += success_count
                stats.failed_loads += (len(config.pairs) - success_count)
                stats.last_run = datetime.now()
                stats.average_duration = (
                    (stats.average_duration * (stats.total_attempts - 1) + duration) 
                    / stats.total_attempts
                )
                
                # Адаптивная настройка интервала
                next_interval = self._calculate_adaptive_interval(category, config, success_count)
                
                logger.debug(
                    f"📊 Category '{category}' completed\n"
                    f"   ├─ Success: {success_count}/{len(config.pairs)}\n"
                    f"   ├─ Duration: {duration:.2f}s\n"
                    f"   └─ Next run in: {next_interval}s"
                )
                
                # Ждем до следующего запуска
                await asyncio.sleep(next_interval)
                
            except asyncio.CancelledError:
                logger.info(f"Preload loop for '{category}' cancelled")
                break
            except Exception as e:
                logger.error(f"Error in preload loop for '{category}': {e}")
                await asyncio.sleep(30)  # Пауза при ошибке
    
    async def _preload_category(self, category: str, config: PreloadConfig) -> int:
        """Предзагрузить курсы для категории"""
        if not self.unified_manager:
            logger.error("Unified manager not available for preloading")
            return 0
        
        logger.debug(f"📦 Preloading category '{category}' ({len(config.pairs)} pairs)")
        
        # Создаем задачи для параллельной загрузки
        tasks = []
        for pair in config.pairs:
            task = asyncio.create_task(
                self._preload_single_pair(pair, category)
            )
            tasks.append((pair, task))
        
        # Ожидаем завершения с тайм-аутом
        successful_count = 0
        timeout_per_pair = 5.0  # 5 секунд на пару
        
        try:
            # Используем asyncio.gather с тайм-аутом
            results = await asyncio.wait_for(
                asyncio.gather(*[task for _, task in tasks], return_exceptions=True),
                timeout=timeout_per_pair * len(config.pairs)
            )
            
            for i, result in enumerate(results):
                pair = config.pairs[i]
                if isinstance(result, Exception):
                    logger.debug(f"❌ Failed to preload {pair}: {result}")
                elif result:
                    successful_count += 1
                    logger.debug(f"✅ Preloaded {pair}")
                else:
                    logger.debug(f"❌ Failed to preload {pair}: No data")
                    
        except asyncio.TimeoutError:
            logger.warning(f"⏰ Timeout preloading category '{category}'")
            # Отменяем незавершенные задачи
            for _, task in tasks:
                if not task.done():
                    task.cancel()
        
        return successful_count
    
    async def _preload_single_pair(self, pair: str, category: str) -> Optional[ExchangeRate]:
        """Предзагрузить курс для одной пары"""
        try:
            # Проверяем, есть ли уже свежий курс в кэше
            cache_key = f"unified_rate_{pair}"
            cached_rate = api_cache.get(cache_key)
            
            if cached_rate and self._is_rate_fresh(cached_rate, category):
                logger.debug(f"💾 Fresh cache hit for {pair} in category '{category}'")
                self.stats[category].cache_hit_ratio = (
                    self.stats[category].cache_hit_ratio * 0.9 + 0.1
                )
                return cached_rate
            
            # Загружаем новый курс с коротким тайм-аутом
            rate = await asyncio.wait_for(
                self.unified_manager.get_exchange_rate(pair, use_cache=False),
                timeout=3.0
            )
            
            if rate:
                # Обновляем статистику кэша
                self.stats[category].cache_hit_ratio = (
                    self.stats[category].cache_hit_ratio * 0.9
                )
                return rate
            
            return None
            
        except asyncio.TimeoutError:
            logger.debug(f"⏰ Preload timeout for {pair}")
            return None
        except Exception as e:
            logger.debug(f"❌ Preload error for {pair}: {e}")
            return None
    
    def _is_rate_fresh(self, rate: ExchangeRate, category: str) -> bool:
        """Проверить, является ли курс свежим для данной категории"""
        if not rate.timestamp:
            return False
        
        try:
            rate_time = datetime.fromisoformat(rate.timestamp.replace('Z', '+00:00'))
            age = (datetime.now() - rate_time.replace(tzinfo=None)).total_seconds()
            
            # Критические курсы должны быть свежее
            if category == 'critical':
                return age < 45  # 45 секунд
            elif category == 'popular':
                return age < 90  # 1.5 минуты
            else:
                return age < 180  # 3 минуты
                
        except Exception:
            return False
    
    def _calculate_adaptive_interval(
        self, 
        category: str, 
        config: PreloadConfig, 
        success_count: int
    ) -> int:
        """Рассчитать адаптивный интервал для следующего запуска"""
        if not self.adaptive_intervals:
            return config.interval
        
        base_interval = config.interval
        success_ratio = success_count / len(config.pairs) if config.pairs else 0
        
        # Адаптируем интервал на основе успешности
        if success_ratio >= 0.9:  # 90%+ успех
            # Сокращаем интервал для популярных курсов
            adaptive_interval = int(base_interval * 0.9)
        elif success_ratio >= 0.7:  # 70-90% успех
            # Оставляем базовый интервал
            adaptive_interval = base_interval
        elif success_ratio >= 0.5:  # 50-70% успех
            # Увеличиваем интервал
            adaptive_interval = int(base_interval * 1.2)
        else:  # <50% успех
            # Значительно увеличиваем интервал
            adaptive_interval = int(base_interval * 1.5)
        
        # Ограничиваем пределами
        adaptive_interval = max(self.min_interval, min(self.max_interval, adaptive_interval))
        
        return adaptive_interval
    
    def get_preload_status(self) -> Dict[str, any]:
        """Получить статус предзагрузки"""
        total_pairs = sum(len(cfg.pairs) for cfg in self.preload_configs.values())
        cached_pairs = 0
        
        # Подсчитываем кэшированные пары
        for config in self.preload_configs.values():
            for pair in config.pairs:
                cache_key = f"unified_rate_{pair}"
                if api_cache.get(cache_key):
                    cached_pairs += 1
        
        return {
            'timestamp': datetime.now().isoformat(),
            'running': self.running,
            'active_categories': len(self.tasks),
            'total_pairs': total_pairs,
            'cached_pairs': cached_pairs,
            'cache_coverage': cached_pairs / total_pairs if total_pairs > 0 else 0,
            'categories': {
                category: {
                    'enabled': config.enabled,
                    'pairs_count': len(config.pairs),
                    'interval': config.interval,
                    'priority': config.priority,
                    'stats': {
                        'total_attempts': self.stats[category].total_attempts,
                        'success_rate': (
                            self.stats[category].successful_loads / (self.stats[category].successful_loads + self.stats[category].failed_loads)
                            if (self.stats[category].successful_loads + self.stats[category].failed_loads) > 0 else 0
                        ),
                        'last_run': self.stats[category].last_run.isoformat() if self.stats[category].last_run else None,
                        'avg_duration': round(self.stats[category].average_duration, 2),
                        'cache_hit_ratio': round(self.stats[category].cache_hit_ratio, 2)
                    }
                }
                for category, config in self.preload_configs.items()
            }
        }
    
    async def force_preload_category(self, category: str) -> Dict[str, any]:
        """Принудительно запустить предзагрузку для категории"""
        if category not in self.preload_configs:
            return {
                'success': False,
                'error': f'Unknown category: {category}'
            }
        
        if not self.unified_manager:
            return {
                'success': False,
                'error': 'Unified manager not available'
            }
        
        config = self.preload_configs[category]
        start_time = time.time()
        
        logger.info(f"🚀 Force preloading category '{category}'")
        success_count = await self._preload_category(category, config)
        duration = time.time() - start_time
        
        return {
            'success': True,
            'category': category,
            'pairs_attempted': len(config.pairs),
            'pairs_successful': success_count,
            'duration': round(duration, 2),
            'success_rate': success_count / len(config.pairs) if config.pairs else 0
        }
    
    def update_config(self, category: str, **kwargs) -> bool:
        """Обновить конфигурацию категории"""
        if category not in self.preload_configs:
            return False
        
        config = self.preload_configs[category]
        
        # Обновляем разрешенные параметры
        if 'interval' in kwargs:
            config.interval = max(self.min_interval, min(self.max_interval, kwargs['interval']))
        if 'enabled' in kwargs:
            config.enabled = bool(kwargs['enabled'])
        if 'pairs' in kwargs and isinstance(kwargs['pairs'], list):
            config.pairs = kwargs['pairs']
        
        logger.info(f"📝 Updated config for category '{category}': {kwargs}")
        return True


# Глобальный экземпляр Smart Rate Preloader
smart_preloader = SmartRatePreloader()