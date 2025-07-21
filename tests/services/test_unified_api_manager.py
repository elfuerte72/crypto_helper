#!/usr/bin/env python3
"""
Unit Tests for Unified API Manager
TASK-PERF-002: Оптимизация API Performance
"""

import pytest
import asyncio
import aiohttp
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from services.unified_api_manager import (
    UnifiedAPIManager, APIRouter, CircuitBreaker, RatePreloader,
    APIRoute, CircuitBreakerState
)
from services.models import ExchangeRate
from config import config


class TestAPIRouter:
    """Тесты для API Router"""
    
    def setup_method(self):
        """Настройка для каждого теста"""
        self.router = APIRouter()
    
    def test_determine_pair_type_crypto(self):
        """Тест определения типа криптовалютной пары"""
        assert self.router.determine_pair_type('BTC/USDT') == 'crypto'
        assert self.router.determine_pair_type('ETH/BTC') == 'crypto'
        assert self.router.determine_pair_type('SOL/USDC') == 'crypto'
    
    def test_determine_pair_type_fiat(self):
        """Тест определения типа фиатной пары"""
        assert self.router.determine_pair_type('USD/EUR') == 'fiat'
        assert self.router.determine_pair_type('RUB/ZAR') == 'fiat'
        assert self.router.determine_pair_type('GBP/JPY') == 'fiat'
    
    def test_determine_pair_type_mixed(self):
        """Тест определения смешанного типа пары"""
        assert self.router.determine_pair_type('BTC/USD') == 'mixed'
        assert self.router.determine_pair_type('USDT/RUB') == 'mixed'
        assert self.router.determine_pair_type('EUR/BTC') == 'mixed'
    
    def test_determine_pair_type_invalid(self):
        """Тест определения некорректной пары"""
        assert self.router.determine_pair_type('INVALID') == 'invalid'
        assert self.router.determine_pair_type('BTC') == 'invalid'
        assert self.router.determine_pair_type('') == 'invalid'
    
    def test_get_best_route_crypto(self):
        """Тест получения маршрута для криптовалют"""
        route = self.router.get_best_route('BTC/USDT')
        assert route is not None
        assert route.api_name == 'rapira'
        assert 'crypto' in route.currency_types
    
    def test_get_best_route_fiat(self):
        """Тест получения маршрута для фиатных валют"""
        route = self.router.get_best_route('USD/EUR')
        assert route is not None
        assert route.api_name == 'apilayer'
        assert 'fiat' in route.currency_types
    
    def test_get_best_route_mixed_uses_rapira(self):
        """Тест, что смешанные пары используют Rapira API"""
        route = self.router.get_best_route('BTC/USD')
        assert route is not None
        assert route.api_name == 'rapira'
    
    def test_get_best_route_invalid(self):
        """Тест получения маршрута для некорректной пары"""
        route = self.router.get_best_route('INVALID')
        assert route is None


class TestCircuitBreaker:
    """Тесты для Circuit Breaker"""
    
    def setup_method(self):
        """Настройка для каждого теста"""
        self.circuit_breaker = CircuitBreaker(failure_threshold=3, reset_timeout=60)
    
    def test_initial_state_closed(self):
        """Тест начального состояния (закрыт)"""
        assert not self.circuit_breaker.is_open('test_api')
    
    def test_record_success_resets_failures(self):
        """Тест сброса ошибок при успехе"""
        # Добавляем несколько ошибок
        for _ in range(2):
            self.circuit_breaker.record_failure('test_api')
        
        # Записываем успех
        self.circuit_breaker.record_success('test_api')
        
        state = self.circuit_breaker.get_state('test_api')
        assert state.failures == 0
        assert not state.is_open
    
    def test_circuit_opens_after_threshold(self):
        """Тест открытия Circuit Breaker при превышении порога"""
        # Добавляем ошибки до порога
        for _ in range(3):
            self.circuit_breaker.record_failure('test_api')
        
        assert self.circuit_breaker.is_open('test_api')
        
        state = self.circuit_breaker.get_state('test_api')
        assert state.is_open
        assert state.failures == 3
        assert state.next_attempt is not None
    
    def test_circuit_half_open_after_timeout(self):
        """Тест перехода в половину открытия после таймаута"""
        # Открываем Circuit Breaker
        for _ in range(3):
            self.circuit_breaker.record_failure('test_api')
        
        assert self.circuit_breaker.is_open('test_api')
        
        # Симулируем прошедшее время
        state = self.circuit_breaker.get_state('test_api')
        state.next_attempt = datetime.now() - timedelta(seconds=1)
        
        # Проверяем, что можно попробовать снова
        assert not self.circuit_breaker.is_open('test_api')


class TestUnifiedAPIManager:
    """Тесты для Unified API Manager"""
    
    def setup_method(self):
        """Настройка для каждого теста"""
        self.manager = UnifiedAPIManager()
    
    @pytest.mark.asyncio
    async def test_start_and_stop(self):
        """Тест запуска и остановки менеджера"""
        await self.manager.start()
        assert self.manager.session is not None
        assert not self.manager.session.closed
        
        await self.manager.stop()
        assert self.manager.session is None
    
    @pytest.mark.asyncio
    async def test_get_from_cache(self):
        """Тест получения из кэша"""
        # Тестовый курс
        test_rate = ExchangeRate(
            pair='BTC/USDT',
            rate=50000.0,
            timestamp=datetime.now().isoformat(),
            source='test'
        )
        
        # Сохраняем в кэш
        self.manager._store_in_cache('BTC/USDT', test_rate)
        
        # Получаем из кэша
        cached_rate = self.manager._get_from_cache('BTC/USDT')
        assert cached_rate is not None
        assert cached_rate.pair == 'BTC/USDT'
        assert cached_rate.rate == 50000.0
    
    @pytest.mark.asyncio 
    @patch('services.unified_api_manager.api_service')
    async def test_get_exchange_rate_success(self, mock_api_service):
        """Тест успешного получения курса"""
        # Настраиваем мок
        test_rate = ExchangeRate(
            pair='BTC/USDT',
            rate=50000.0,
            timestamp=datetime.now().isoformat(),
            source='rapira'
        )
        mock_api_service.get_exchange_rate = AsyncMock(return_value=test_rate)
        
        # Тестируем
        rate = await self.manager.get_exchange_rate('BTC/USDT', use_cache=False)
        
        assert rate is not None
        assert rate.pair == 'BTC/USDT'
        assert rate.rate == 50000.0
        assert self.manager.stats['total_requests'] == 1
    
    @pytest.mark.asyncio
    @patch('services.unified_api_manager.api_service')
    async def test_get_exchange_rate_circuit_breaker_open(self, mock_api_service):
        """Тест блокировки запросов при открытом Circuit Breaker"""
        # Открываем Circuit Breaker
        for _ in range(5):
            self.manager.circuit_breaker.record_failure('rapira')
        
        # Пытаемся получить курс
        rate = await self.manager.get_exchange_rate('BTC/USDT', use_cache=False)
        
        assert rate is None
        assert self.manager.stats['circuit_breaker_blocks'] == 1
    
    @pytest.mark.asyncio
    @patch('services.unified_api_manager.api_service')
    @patch('services.unified_api_manager.fiat_rates_service') 
    async def test_get_multiple_rates(self, mock_fiat_service, mock_api_service):
        """Тест получения нескольких курсов"""
        # Настраиваем моки
        crypto_rate = ExchangeRate(
            pair='BTC/USDT',
            rate=50000.0,
            timestamp=datetime.now().isoformat(),
            source='rapira'
        )
        fiat_rate = ExchangeRate(
            pair='USD/EUR',
            rate=0.85,
            timestamp=datetime.now().isoformat(),
            source='apilayer'
        )
        
        mock_api_service.get_exchange_rate = AsyncMock(return_value=crypto_rate)
        mock_fiat_service.get_fiat_exchange_rate = AsyncMock(return_value=fiat_rate)
        
        # Тестируем
        results = await self.manager.get_multiple_rates(
            ['BTC/USDT', 'USD/EUR'], 
            use_cache=False
        )
        
        assert len(results) == 2
        assert results['BTC/USDT'] is not None
        assert results['USD/EUR'] is not None
        assert self.manager.stats['batch_requests'] == 1
    
    @pytest.mark.asyncio
    async def test_get_performance_stats(self):
        """Тест получения статистики производительности"""
        # Добавляем немного статистики
        self.manager.stats['total_requests'] = 10
        self.manager.stats['cache_hits'] = 7
        self.manager.stats['cache_misses'] = 3
        
        stats = self.manager.get_performance_stats()
        
        assert 'timestamp' in stats
        assert 'api_requests' in stats
        assert 'cache_performance' in stats
        assert 'circuit_breaker_states' in stats
        assert stats['api_requests']['total_requests'] == 10
        assert stats['api_requests']['cache_hits'] == 7


class TestRatePreloader:
    """Тесты для Rate Preloader"""
    
    def setup_method(self):
        """Настройка для каждого теста"""
        self.preloader = RatePreloader(preload_interval=60)
    
    @pytest.mark.asyncio
    async def test_start_and_stop(self):
        """Тест запуска и остановки предзагрузчика"""
        mock_manager = Mock()
        
        await self.preloader.start_preloading(mock_manager)
        assert self.preloader.running
        assert self.preloader.preload_task is not None
        
        await self.preloader.stop_preloading()
        assert not self.preloader.running
        assert self.preloader.preload_task is None
    
    @pytest.mark.asyncio
    async def test_preload_single_pair_success(self, monkeypatch):
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
        
        # Тестируем предзагрузку
        result = await self.preloader._preload_single_pair(mock_manager, 'USDT/RUB')
        
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
        
        # Тестируем предзагрузку
        result = await self.preloader._preload_single_pair(mock_manager, 'USDT/RUB')
        
        assert result is None


@pytest.mark.asyncio
async def test_performance_optimization_integration():
    """Интеграционный тест оптимизации производительности"""
    manager = UnifiedAPIManager()
    
    try:
        await manager.start()
        
        # Проверяем оптимизированные настройки сессии
        assert manager.session is not None
        assert manager.session.connector.limit == config.CONNECTION_POOL_LIMIT
        assert manager.session.connector.limit_per_host == config.CONNECTION_POOL_LIMIT_PER_HOST
        # ИСПРАВЛЕНО: проверяем новый оптимизированный таймаут (10s вместо 30s)
        assert manager.session.timeout.total == 10
        
        # Проверяем работу Circuit Breaker
        assert not manager.circuit_breaker.is_open('rapira')
        assert not manager.circuit_breaker.is_open('apilayer')
        
    finally:
        await manager.stop()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])