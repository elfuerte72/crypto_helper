#!/usr/bin/env python3
"""
Unit Tests for Smart Rate Preloader
TASK-PERF-002: Оптимизация API Performance
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from services.rate_preloader import SmartRatePreloader, PreloadConfig, PreloadStats
from services.models import ExchangeRate
from config import config


class TestPreloadConfig:
    """Тесты для PreloadConfig"""
    
    def test_preload_config_creation(self):
        """Тест создания конфигурации предзагрузки"""
        config = PreloadConfig(
            pairs=['USDT/RUB', 'BTC/USDT'],
            interval=60,
            priority=1
        )
        
        assert config.pairs == ['USDT/RUB', 'BTC/USDT']
        assert config.interval == 60
        assert config.priority == 1
        assert config.enabled is True
    
    def test_preload_config_disabled(self):
        """Тест отключенной конфигурации"""
        config = PreloadConfig(
            pairs=['USD/EUR'],
            interval=120,
            priority=2,
            enabled=False
        )
        
        assert config.enabled is False


class TestPreloadStats:
    """Тесты для PreloadStats"""
    
    def test_preload_stats_initial(self):
        """Тест начальных значений статистики"""
        stats = PreloadStats()
        
        assert stats.total_attempts == 0
        assert stats.successful_loads == 0
        assert stats.failed_loads == 0
        assert stats.last_run is None
        assert stats.average_duration == 0.0
        assert stats.cache_hit_ratio == 0.0


class TestSmartRatePreloader:
    """Тесты для Smart Rate Preloader"""
    
    def setup_method(self):
        """Настройка для каждого теста"""
        self.preloader = SmartRatePreloader()
    
    def test_initialization(self):
        """Тест инициализации предзагрузчика"""
        assert not self.preloader.running
        assert len(self.preloader.preload_configs) > 0
        assert 'critical' in self.preloader.preload_configs
        assert 'popular' in self.preloader.preload_configs
        assert 'secondary' in self.preloader.preload_configs
        assert 'fiat_cross' in self.preloader.preload_configs
    
    def test_critical_config(self):
        """Тест критической конфигурации"""
        critical_config = self.preloader.preload_configs['critical']
        
        assert 'USDT/RUB' in critical_config.pairs
        assert 'USD/RUB' in critical_config.pairs
        assert 'EUR/RUB' in critical_config.pairs
        assert critical_config.interval == 60  # 1 минута
        assert critical_config.priority == 1
        assert critical_config.enabled is True
    
    def test_popular_config(self):
        """Тест популярной конфигурации"""
        popular_config = self.preloader.preload_configs['popular']
        
        assert 'BTC/USDT' in popular_config.pairs
        assert 'ETH/USDT' in popular_config.pairs
        assert popular_config.interval == 120  # 2 минуты
        assert popular_config.priority == 2
    
    @pytest.mark.asyncio
    async def test_start_and_stop(self):
        """Тест запуска и остановки предзагрузчика"""
        mock_manager = Mock()
        
        await self.preloader.start(mock_manager)
        assert self.preloader.running
        assert self.preloader.unified_manager == mock_manager
        assert len(self.preloader.tasks) > 0
        
        await self.preloader.stop()
        assert not self.preloader.running
        assert len(self.preloader.tasks) == 0
    
    @pytest.mark.asyncio
    async def test_preload_single_pair_success(self):
        """Тест успешной предзагрузки одной пары"""
        # Создаем мок менеджера
        mock_manager = Mock()
        test_rate = ExchangeRate(
            pair='USDT/RUB',
            rate=100.0,
            timestamp=datetime.now().isoformat(),
            source='test'
        )
        mock_manager.get_exchange_rate = AsyncMock(return_value=test_rate)
        self.preloader.unified_manager = mock_manager
        
        # Тестируем предзагрузку
        result = await self.preloader._preload_single_pair('USDT/RUB', 'critical')
        
        assert result is not None
        assert result.pair == 'USDT/RUB'
        assert result.rate == 100.0
    
    @pytest.mark.asyncio
    async def test_preload_single_pair_timeout(self):
        """Тест таймаута при предзагрузке"""
        # Создаем мок менеджера с медленным ответом
        mock_manager = Mock()
        
        async def slow_response(*args, **kwargs):
            await asyncio.sleep(10)  # Превышаем таймаут в 3 секунды
            return None
        
        mock_manager.get_exchange_rate = slow_response
        self.preloader.unified_manager = mock_manager
        
        # Тестируем предзагрузку
        result = await self.preloader._preload_single_pair('USDT/RUB', 'critical')
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_preload_category(self):
        """Тест предзагрузки категории"""
        # Создаем мок менеджера
        mock_manager = Mock()
        test_rate = ExchangeRate(
            pair='USDT/RUB',
            rate=100.0,
            timestamp=datetime.now().isoformat(),
            source='test'
        )
        mock_manager.get_exchange_rate = AsyncMock(return_value=test_rate)
        self.preloader.unified_manager = mock_manager
        
        # Тестируем предзагрузку категории
        config = self.preloader.preload_configs['critical']
        success_count = await self.preloader._preload_category('critical', config)
        
        assert success_count > 0
        assert success_count <= len(config.pairs)
    
    def test_is_rate_fresh_critical(self):
        """Тест проверки свежести курса для критической категории"""
        # Свежий курс (10 секунд назад)
        fresh_rate = ExchangeRate(
            pair='USDT/RUB',
            rate=100.0,
            timestamp=(datetime.now() - timedelta(seconds=10)).isoformat(),
            source='test'
        )
        assert self.preloader._is_rate_fresh(fresh_rate, 'critical')
        
        # Устаревший курс (60 секунд назад)
        stale_rate = ExchangeRate(
            pair='USDT/RUB',
            rate=100.0,
            timestamp=(datetime.now() - timedelta(seconds=60)).isoformat(),
            source='test'
        )
        assert not self.preloader._is_rate_fresh(stale_rate, 'critical')
    
    def test_is_rate_fresh_popular(self):
        """Тест проверки свежести курса для популярной категории"""
        # Свежий курс (60 секунд назад)
        fresh_rate = ExchangeRate(
            pair='BTC/USDT',
            rate=50000.0,
            timestamp=(datetime.now() - timedelta(seconds=60)).isoformat(),
            source='test'
        )
        assert self.preloader._is_rate_fresh(fresh_rate, 'popular')
        
        # Устаревший курс (120 секунд назад)
        stale_rate = ExchangeRate(
            pair='BTC/USDT',
            rate=50000.0,
            timestamp=(datetime.now() - timedelta(seconds=120)).isoformat(),
            source='test'
        )
        assert not self.preloader._is_rate_fresh(stale_rate, 'popular')
    
    def test_calculate_adaptive_interval_high_success(self):
        """Тест адаптивного интервала при высокой успешности"""
        config = PreloadConfig(pairs=['A', 'B', 'C'], interval=120, priority=1)
        
        # 100% успех - интервал должен сократиться
        adaptive_interval = self.preloader._calculate_adaptive_interval(
            'test', config, 3  # 3 из 3 успешных
        )
        assert adaptive_interval < config.interval
    
    def test_calculate_adaptive_interval_low_success(self):
        """Тест адаптивного интервала при низкой успешности"""
        config = PreloadConfig(pairs=['A', 'B', 'C'], interval=120, priority=1)
        
        # 33% успех - интервал должен увеличиться
        adaptive_interval = self.preloader._calculate_adaptive_interval(
            'test', config, 1  # 1 из 3 успешных
        )
        assert adaptive_interval > config.interval
    
    def test_calculate_adaptive_interval_limits(self):
        """Тест ограничений адаптивного интервала"""
        config = PreloadConfig(pairs=['A'], interval=10, priority=1)
        
        # Интервал не должен быть меньше минимального
        adaptive_interval = self.preloader._calculate_adaptive_interval(
            'test', config, 1
        )
        assert adaptive_interval >= self.preloader.min_interval
        
        config.interval = 1000
        # Интервал не должен быть больше максимального
        adaptive_interval = self.preloader._calculate_adaptive_interval(
            'test', config, 0
        )
        assert adaptive_interval <= self.preloader.max_interval
    
    def test_get_preload_status(self):
        """Тест получения статуса предзагрузки"""
        status = self.preloader.get_preload_status()
        
        assert 'timestamp' in status
        assert 'running' in status
        assert 'active_categories' in status
        assert 'total_pairs' in status
        assert 'cached_pairs' in status
        assert 'cache_coverage' in status
        assert 'categories' in status
        
        assert status['running'] is False
        assert status['total_pairs'] > 0
        assert len(status['categories']) == len(self.preloader.preload_configs)
    
    @pytest.mark.asyncio
    async def test_force_preload_category_success(self):
        """Тест принудительной предзагрузки категории"""
        # Создаем мок менеджера
        mock_manager = Mock()
        test_rate = ExchangeRate(
            pair='USDT/RUB',
            rate=100.0,
            timestamp=datetime.now().isoformat(),
            source='test'
        )
        mock_manager.get_exchange_rate = AsyncMock(return_value=test_rate)
        self.preloader.unified_manager = mock_manager
        
        # Тестируем принудительную предзагрузку
        result = await self.preloader.force_preload_category('critical')
        
        assert result['success'] is True
        assert result['category'] == 'critical'
        assert result['pairs_attempted'] > 0
        assert result['pairs_successful'] >= 0
        assert 'duration' in result
        assert 'success_rate' in result
    
    @pytest.mark.asyncio
    async def test_force_preload_category_unknown(self):
        """Тест принудительной предзагрузки неизвестной категории"""
        result = await self.preloader.force_preload_category('unknown')
        
        assert result['success'] is False
        assert 'error' in result
        assert 'Unknown category' in result['error']
    
    def test_update_config_success(self):
        """Тест успешного обновления конфигурации"""
        original_interval = self.preloader.preload_configs['critical'].interval
        
        success = self.preloader.update_config('critical', interval=90)
        
        assert success is True
        assert self.preloader.preload_configs['critical'].interval == 90
        assert self.preloader.preload_configs['critical'].interval != original_interval
    
    def test_update_config_interval_limits(self):
        """Тест ограничений при обновлении интервала"""
        # Пытаемся установить слишком маленький интервал
        self.preloader.update_config('critical', interval=10)
        assert self.preloader.preload_configs['critical'].interval >= self.preloader.min_interval
        
        # Пытаемся установить слишком большой интервал
        self.preloader.update_config('critical', interval=1000)
        assert self.preloader.preload_configs['critical'].interval <= self.preloader.max_interval
    
    def test_update_config_unknown_category(self):
        """Тест обновления конфигурации неизвестной категории"""
        success = self.preloader.update_config('unknown', interval=120)
        assert success is False
    
    def test_update_config_enabled_flag(self):
        """Тест обновления флага включения"""
        self.preloader.update_config('critical', enabled=False)
        assert self.preloader.preload_configs['critical'].enabled is False
        
        self.preloader.update_config('critical', enabled=True)
        assert self.preloader.preload_configs['critical'].enabled is True
    
    def test_update_config_pairs_list(self):
        """Тест обновления списка пар"""
        new_pairs = ['TEST/PAIR1', 'TEST/PAIR2']
        self.preloader.update_config('critical', pairs=new_pairs)
        
        assert self.preloader.preload_configs['critical'].pairs == new_pairs


@pytest.mark.asyncio
async def test_preloader_integration_with_config():
    """Интеграционный тест предзагрузчика с конфигурацией"""
    preloader = SmartRatePreloader()
    
    # Проверяем, что все категории имеют корректные настройки
    for category, config in preloader.preload_configs.items():
        assert config.interval >= preloader.min_interval
        assert config.interval <= preloader.max_interval
        assert len(config.pairs) > 0
        assert config.priority > 0
        
        # Проверяем статистику
        stats = preloader.stats[category]
        assert isinstance(stats, PreloadStats)


@pytest.mark.asyncio 
async def test_cache_interaction():
    """Тест взаимодействия с кэшем"""
    preloader = SmartRatePreloader()
    
    # Создаем тестовый курс с меткой времени
    test_rate = ExchangeRate(
        pair='USDT/RUB',
        rate=100.0,
        timestamp=datetime.now().isoformat(),
        source='test'
    )
    
    # Проверяем определение свежести
    assert preloader._is_rate_fresh(test_rate, 'critical')
    
    # Проверяем старый курс
    old_rate = ExchangeRate(
        pair='USDT/RUB',
        rate=100.0,
        timestamp=(datetime.now() - timedelta(minutes=5)).isoformat(),
        source='test'
    )
    assert not preloader._is_rate_fresh(old_rate, 'critical')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])