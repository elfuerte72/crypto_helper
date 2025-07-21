#!/usr/bin/env python3
"""
Unified API Manager for Crypto Helper Bot
Объединяет Rapira API и APILayer в единый менеджер с автоматическим роутингом
TASK-PERF-002: Оптимизация API Performance
"""

import asyncio
import aiohttp
from typing import Dict, Optional, List, Tuple, Any, Set
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
import random
import time

try:
    from ..config import config
    from ..utils.logger import get_api_logger
    from .models import ExchangeRate, RapiraAPIError, APILayerError
    from .cache_manager import api_cache
    from .api_service import api_service
    from .fiat_rates_service import fiat_rates_service
except ImportError:
    # Handle direct execution
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from config import config
    from utils.logger import get_api_logger
    from services.models import ExchangeRate, RapiraAPIError, APILayerError
    from services.cache_manager import api_cache
    from services.api_service import api_service
    from services.fiat_rates_service import fiat_rates_service

logger = get_api_logger()


@dataclass
class APIRoute:
    """Маршрут для API запроса"""
    api_name: str
    service: Any
    currency_types: Set[str]
    priority: int  # Чем меньше, тем выше приоритет
    

@dataclass
class BatchRequest:
    """Batch запрос для нескольких валютных пар"""
    pairs: List[str]
    timestamp: datetime
    timeout: float = 10.0


@dataclass
class CircuitBreakerState:
    """Состояние Circuit Breaker для API"""
    failures: int = 0
    last_failure: Optional[datetime] = None
    is_open: bool = False
    next_attempt: Optional[datetime] = None


class APIRouter:
    """Роутер для автоматического выбора API по типу валютной пары"""
    
    def __init__(self):
        self.crypto_currencies = {
            'BTC', 'ETH', 'TON', 'USDT', 'USDC', 'LTC', 'TRX', 
            'BNB', 'DAI', 'DOGE', 'ETC', 'OP', 'XMR', 'SOL', 'NOT'
        }
        self.fiat_currencies = {
            'USD', 'EUR', 'RUB', 'ZAR', 'THB', 'AED', 'IDR', 
            'GBP', 'JPY', 'CAD', 'AUD', 'CHF', 'CNY'
        }
        
        # Настройка маршрутов API
        self.routes = [
            APIRoute(
                api_name='rapira',
                service=api_service,
                currency_types={'crypto'},
                priority=1  # Высший приоритет для криптовалют
            ),
            APIRoute(
                api_name='apilayer',
                service=fiat_rates_service,
                currency_types={'fiat'},
                priority=1  # Высший приоритет для фиатных валют
            )
        ]
        
        logger.info(
            f"🔀 API Router initialized\n"
            f"   ├─ Crypto currencies: {len(self.crypto_currencies)}\n"
            f"   ├─ Fiat currencies: {len(self.fiat_currencies)}\n"
            f"   └─ Routes configured: {len(self.routes)}"
        )
    
    def determine_pair_type(self, pair: str) -> str:
        """
        Определить тип валютной пары
        
        Args:
            pair: Валютная пара (например, 'BTC/USDT', 'USD/RUB')
            
        Returns:
            str: 'crypto', 'fiat', 'mixed', 'unknown'
        """
        try:
            base_currency, quote_currency = pair.split('/')
            
            base_is_crypto = base_currency in self.crypto_currencies
            quote_is_crypto = quote_currency in self.crypto_currencies
            base_is_fiat = base_currency in self.fiat_currencies
            quote_is_fiat = quote_currency in self.fiat_currencies
            
            if base_is_crypto and quote_is_crypto:
                return 'crypto'
            elif base_is_fiat and quote_is_fiat:
                return 'fiat'
            elif (base_is_crypto or quote_is_crypto) and (base_is_fiat or quote_is_fiat):
                return 'mixed'
            else:
                return 'unknown'
                
        except ValueError:
            return 'invalid'
    
    def get_best_route(self, pair: str) -> Optional[APIRoute]:
        """
        Получить лучший маршрут для валютной пары
        
        Args:
            pair: Валютная пара
            
        Returns:
            Optional[APIRoute]: Лучший маршрут или None
        """
        pair_type = self.determine_pair_type(pair)
        
        if pair_type == 'invalid':
            logger.error(f"Invalid pair format: {pair}")
            return None
        
        # Для mixed пар (крипто+фиат) используем Rapira API
        if pair_type == 'mixed':
            pair_type = 'crypto'
        
        # Находим подходящие маршруты
        suitable_routes = [
            route for route in self.routes
            if pair_type in route.currency_types
        ]
        
        if not suitable_routes:
            logger.warning(f"No suitable route found for pair: {pair} (type: {pair_type})")
            return None
        
        # Сортируем по приоритету
        best_route = min(suitable_routes, key=lambda r: r.priority)
        
        logger.debug(f"Selected {best_route.api_name} for {pair} (type: {pair_type})")
        return best_route


class CircuitBreaker:
    """Circuit Breaker для защиты от каскадных ошибок API"""
    
    def __init__(self, failure_threshold: int = 5, reset_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.states: Dict[str, CircuitBreakerState] = {}
        
        logger.info(
            f"⚡ Circuit Breaker initialized\n"
            f"   ├─ Failure threshold: {failure_threshold}\n"
            f"   └─ Reset timeout: {reset_timeout}s"
        )
    
    def get_state(self, api_name: str) -> CircuitBreakerState:
        """Получить состояние Circuit Breaker для API"""
        if api_name not in self.states:
            self.states[api_name] = CircuitBreakerState()
        return self.states[api_name]
    
    def is_open(self, api_name: str) -> bool:
        """Проверить, открыт ли Circuit Breaker"""
        state = self.get_state(api_name)
        
        if not state.is_open:
            return False
        
        # Проверяем, можно ли попробовать снова
        if state.next_attempt and datetime.now() >= state.next_attempt:
            logger.info(f"🔄 Circuit Breaker for {api_name}: attempting reset")
            state.is_open = False
            state.next_attempt = None
            return False
        
        return True
    
    def record_success(self, api_name: str):
        """Зарегистрировать успешный вызов"""
        state = self.get_state(api_name)
        if state.failures > 0:
            logger.info(f"✅ Circuit Breaker for {api_name}: success recorded, resetting failures")
        
        state.failures = 0
        state.is_open = False
        state.next_attempt = None
    
    def record_failure(self, api_name: str):
        """Зарегистрировать неудачный вызов"""
        state = self.get_state(api_name)
        state.failures += 1
        state.last_failure = datetime.now()
        
        if state.failures >= self.failure_threshold and not state.is_open:
            state.is_open = True
            state.next_attempt = datetime.now() + timedelta(seconds=self.reset_timeout)
            
            logger.warning(
                f"🚨 Circuit Breaker for {api_name}: OPENED\n"
                f"   ├─ Failures: {state.failures}/{self.failure_threshold}\n"
                f"   └─ Reset attempt at: {state.next_attempt}"
            )
        else:
            logger.warning(f"⚠️ Circuit Breaker for {api_name}: failure {state.failures}/{self.failure_threshold}")


class RatePreloader:
    """Предзагрузчик популярных курсов валют"""
    
    def __init__(self, preload_interval: int = 120):  # 2 минуты
        self.preload_interval = preload_interval
        self.popular_pairs = [
            'USDT/RUB',  # Самая популярная крипто пара
            'USD/RUB',   # Популярная фиатная пара
            'EUR/RUB',   # Популярная фиатная пара
            'BTC/USDT',  # Популярная крипто пара
            'ETH/USDT',  # Популярная крипто пара
        ]
        self.preload_task: Optional[asyncio.Task] = None
        self.running = False
        
        logger.info(
            f"📦 Rate Preloader initialized\n"
            f"   ├─ Preload interval: {preload_interval}s\n"
            f"   └─ Popular pairs: {len(self.popular_pairs)}"
        )
    
    async def start_preloading(self, unified_manager):
        """Запустить предзагрузку курсов"""
        if self.running:
            logger.warning("Rate preloader already running")
            return
        
        self.running = True
        self.preload_task = asyncio.create_task(
            self._preload_loop(unified_manager)
        )
        logger.info("✅ Rate preloader started")
    
    async def stop_preloading(self):
        """Остановить предзагрузку курсов"""
        self.running = False
        if self.preload_task:
            self.preload_task.cancel()
            try:
                await self.preload_task
            except asyncio.CancelledError:
                pass
            self.preload_task = None
        logger.info("⏹️ Rate preloader stopped")
    
    async def _preload_loop(self, unified_manager):
        """Основной цикл предзагрузки"""
        logger.info(f"🔄 Starting preload loop for {len(self.popular_pairs)} pairs")
        
        while self.running:
            try:
                await self._preload_popular_rates(unified_manager)
                await asyncio.sleep(self.preload_interval)
            except asyncio.CancelledError:
                logger.info("Preload loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in preload loop: {e}")
                await asyncio.sleep(10)  # Короткая пауза при ошибке
    
    async def _preload_popular_rates(self, unified_manager):
        """Предзагрузить популярные курсы"""
        start_time = time.time()
        successful_preloads = 0
        
        logger.debug(f"📦 Preloading {len(self.popular_pairs)} popular pairs")
        
        # Создаем задачи для параллельной загрузки
        tasks = []
        for pair in self.popular_pairs:
            task = asyncio.create_task(
                self._preload_single_pair(unified_manager, pair)
            )
            tasks.append((pair, task))
        
        # Ожидаем завершения всех задач
        for pair, task in tasks:
            try:
                rate = await task
                if rate:
                    successful_preloads += 1
                    logger.debug(f"✅ Preloaded {pair}: {rate.rate}")
                else:
                    logger.debug(f"❌ Failed to preload {pair}")
            except Exception as e:
                logger.warning(f"Error preloading {pair}: {e}")
        
        duration = time.time() - start_time
        logger.info(
            f"📦 Preload completed\n"
            f"   ├─ Successful: {successful_preloads}/{len(self.popular_pairs)}\n"
            f"   ├─ Duration: {duration:.2f}s\n"
            f"   └─ Cache utilization: {api_cache.get_stats()['utilization']:.1%}"
        )
    
    async def _preload_single_pair(self, unified_manager, pair: str) -> Optional[ExchangeRate]:
        """Предзагрузить курс для одной пары"""
        try:
            # Используем короткий таймаут для предзагрузки
            rate = await asyncio.wait_for(
                unified_manager.get_exchange_rate(pair, use_cache=False),
                timeout=5.0
            )
            return rate
        except asyncio.TimeoutError:
            logger.debug(f"Preload timeout for {pair}")
            return None
        except Exception as e:
            logger.debug(f"Preload error for {pair}: {e}")
            return None


class UnifiedAPIManager:
    """Единый менеджер API с автоматическим роутингом и оптимизацией производительности"""
    
    def __init__(self):
        self.router = APIRouter()
        self.circuit_breaker = CircuitBreaker()
        self.preloader = RatePreloader()
        
        # Создаем оптимизированную HTTP сессию
        self.session: Optional[aiohttp.ClientSession] = None
        self._session_lock = asyncio.Lock()
        
        # Статистика производительности
        self.stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'circuit_breaker_blocks': 0,
            'batch_requests': 0,
            'preload_hits': 0
        }
        
        logger.info("🚀 Unified API Manager initialized")
    
    async def start(self):
        """Запустить менеджер API"""
        await self._ensure_session()
        await self.preloader.start_preloading(self)
        logger.info("✅ Unified API Manager started")
    
    async def stop(self):
        """Остановить менеджер API"""
        await self.preloader.stop_preloading()
        await self._close_session()
        logger.info("⏹️ Unified API Manager stopped")
    
    async def _ensure_session(self):
        """Убедиться, что HTTP сессия создана"""
        async with self._session_lock:
            if not self.session or self.session.closed:
                # Оптимизированные настройки connection pool
                connector = aiohttp.TCPConnector(
                    limit=200,              # УВЕЛИЧЕНО: общий лимит соединений
                    limit_per_host=50,      # УВЕЛИЧЕНО: лимит на хост
                    ttl_dns_cache=300,      # DNS кэш на 5 минут
                    use_dns_cache=True,
                    keepalive_timeout=60,   # УВЕЛИЧЕНО: keep-alive
                    enable_cleanup_closed=True,
                    timeout_ceil_threshold=5
                )
                
                # СОКРАЩЕННЫЕ таймауты для production
                timeout = aiohttp.ClientTimeout(
                    total=10,               # СОКРАЩЕНО: с 30s до 10s
                    connect=5,              # Таймаут подключения
                    sock_connect=3,         # Таймаут сокета
                    sock_read=5             # Таймаут чтения
                )
                
                headers = {
                    'User-Agent': 'CryptoHelper-UnifiedAPI/2.0',
                    'Accept': 'application/json',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive'
                }
                
                self.session = aiohttp.ClientSession(
                    connector=connector,
                    timeout=timeout,
                    headers=headers,
                    raise_for_status=False
                )
                
                logger.info(
                    f"🔗 Optimized HTTP session created\n"
                    f"   ├─ Connection limit: 200 (50 per host)\n"
                    f"   ├─ Keep-alive timeout: 60s\n"
                    f"   ├─ Total timeout: 10s\n"
                    f"   └─ DNS cache TTL: 300s"
                )
    
    async def _close_session(self):
        """Закрыть HTTP сессию"""
        async with self._session_lock:
            if self.session and not self.session.closed:
                await self.session.close()
                self.session = None
                logger.info("🔒 HTTP session closed")
    
    async def get_exchange_rate(
        self, 
        pair: str, 
        use_cache: bool = True,
        timeout: Optional[float] = None
    ) -> Optional[ExchangeRate]:
        """
        Получить курс обмена для валютной пары
        
        Args:
            pair: Валютная пара (например, 'BTC/USDT')
            use_cache: Использовать кэш
            timeout: Таймаут запроса
            
        Returns:
            Optional[ExchangeRate]: Курс обмена или None
        """
        self.stats['total_requests'] += 1
        
        # Проверяем кэш
        if use_cache:
            cached_rate = self._get_from_cache(pair)
            if cached_rate:
                self.stats['cache_hits'] += 1
                logger.debug(f"💾 Cache HIT for {pair}")
                return cached_rate
            else:
                self.stats['cache_misses'] += 1
        
        # Находим маршрут
        route = self.router.get_best_route(pair)
        if not route:
            logger.error(f"No route found for pair: {pair}")
            return None
        
        # Проверяем Circuit Breaker
        if self.circuit_breaker.is_open(route.api_name):
            self.stats['circuit_breaker_blocks'] += 1
            logger.warning(f"🚨 Circuit Breaker OPEN for {route.api_name}, blocking request for {pair}")
            return None
        
        # Выполняем запрос
        try:
            rate = await self._execute_api_request(route, pair, timeout)
            
            if rate:
                self.circuit_breaker.record_success(route.api_name)
                if use_cache:
                    self._store_in_cache(pair, rate)
                logger.debug(f"✅ Successfully fetched {pair} via {route.api_name}")
                return rate
            else:
                self.circuit_breaker.record_failure(route.api_name)
                logger.warning(f"❌ Failed to fetch {pair} via {route.api_name}")
                return None
                
        except Exception as e:
            self.circuit_breaker.record_failure(route.api_name)
            logger.error(f"❌ Error fetching {pair} via {route.api_name}: {e}")
            return None
    
    async def get_multiple_rates(
        self, 
        pairs: List[str], 
        use_cache: bool = True,
        timeout: Optional[float] = None
    ) -> Dict[str, Optional[ExchangeRate]]:
        """
        Получить курсы для нескольких валютных пар параллельно (batch request)
        
        Args:
            pairs: Список валютных пар
            use_cache: Использовать кэш
            timeout: Таймаут запроса
            
        Returns:
            Dict[str, Optional[ExchangeRate]]: Словарь курсов
        """
        self.stats['batch_requests'] += 1
        logger.info(f"📦 Batch request for {len(pairs)} pairs")
        
        start_time = time.time()
        
        # Создаем задачи для параллельного выполнения
        tasks = []
        for pair in pairs:
            task = asyncio.create_task(
                self.get_exchange_rate(pair, use_cache, timeout)
            )
            tasks.append((pair, task))
        
        # Ожидаем завершения всех задач
        results = {}
        successful_count = 0
        
        for pair, task in tasks:
            try:
                rate = await task
                results[pair] = rate
                if rate:
                    successful_count += 1
            except Exception as e:
                logger.error(f"Error in batch request for {pair}: {e}")
                results[pair] = None
        
        duration = time.time() - start_time
        logger.info(
            f"📦 Batch request completed\n"
            f"   ├─ Successful: {successful_count}/{len(pairs)}\n"
            f"   ├─ Duration: {duration:.2f}s\n"
            f"   └─ Avg per pair: {duration/len(pairs):.3f}s"
        )
        
        return results
    
    async def _execute_api_request(
        self, 
        route: APIRoute, 
        pair: str, 
        timeout: Optional[float]
    ) -> Optional[ExchangeRate]:
        """Выполнить API запрос через выбранный маршрут"""
        try:
            if route.api_name == 'rapira':
                # Для Rapira API используем api_service
                rate = await api_service.get_exchange_rate(pair)
                return rate
                
            elif route.api_name == 'apilayer':
                # Для APILayer используем fiat_rates_service
                rate = await fiat_rates_service.get_fiat_exchange_rate(pair)
                return rate
                
            else:
                logger.error(f"Unknown API route: {route.api_name}")
                return None
                
        except (RapiraAPIError, APILayerError) as e:
            logger.error(f"API error for {pair} via {route.api_name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error for {pair} via {route.api_name}: {e}")
            raise
    
    def _get_from_cache(self, pair: str) -> Optional[ExchangeRate]:
        """Получить курс из кэша"""
        cache_key = f"unified_rate_{pair}"
        return api_cache.get(cache_key)
    
    def _store_in_cache(self, pair: str, rate: ExchangeRate):
        """Сохранить курс в кэш"""
        cache_key = f"unified_rate_{pair}"
        api_cache.set(cache_key, rate, ttl=config.API_CACHE_TTL)
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Проверка здоровья всех API сервисов
        
        Returns:
            Dict[str, Any]: Результаты проверки
        """
        logger.info("🏥 Performing unified health check")
        
        health_data = {
            'timestamp': datetime.now().isoformat(),
            'service': 'unified_api_manager',
            'status': 'unknown',
            'apis': {},
            'circuit_breakers': {},
            'performance_stats': self.stats.copy(),
            'cache_stats': api_cache.get_stats()
        }
        
        # Проверяем состояние Circuit Breakers
        for api_name in ['rapira', 'apilayer']:
            state = self.circuit_breaker.get_state(api_name)
            health_data['circuit_breakers'][api_name] = {
                'is_open': state.is_open,
                'failures': state.failures,
                'last_failure': state.last_failure.isoformat() if state.last_failure else None
            }
        
        # Проверяем каждый API
        api_checks = []
        
        # Rapira API
        rapira_task = asyncio.create_task(api_service.health_check())
        api_checks.append(('rapira', rapira_task))
        
        # APILayer
        apilayer_task = asyncio.create_task(fiat_rates_service.health_check())
        api_checks.append(('apilayer', apilayer_task))
        
        # Собираем результаты
        healthy_apis = 0
        total_apis = len(api_checks)
        
        for api_name, task in api_checks:
            try:
                api_health = await task
                health_data['apis'][api_name] = api_health
                if api_health.get('status') == 'healthy':
                    healthy_apis += 1
            except Exception as e:
                health_data['apis'][api_name] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }
        
        # Определяем общий статус
        if healthy_apis == total_apis:
            health_data['status'] = 'healthy'
            health_data['message'] = 'All APIs operational'
        elif healthy_apis > 0:
            health_data['status'] = 'degraded'
            health_data['message'] = f'{healthy_apis}/{total_apis} APIs operational'
        else:
            health_data['status'] = 'unhealthy'
            health_data['message'] = 'No APIs operational'
        
        logger.info(f"🏥 Health check completed: {health_data['status']} ({healthy_apis}/{total_apis} APIs)")
        return health_data
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Получить статистику производительности"""
        cache_stats = api_cache.get_stats()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'api_requests': self.stats.copy(),
            'cache_performance': {
                'hit_ratio': cache_stats['hit_ratio'],
                'size': cache_stats['current_size'],
                'utilization': cache_stats['utilization']
            },
            'circuit_breaker_states': {
                api_name: {
                    'failures': state.failures,
                    'is_open': state.is_open
                }
                for api_name, state in self.circuit_breaker.states.items()
            },
            'popular_pairs_cached': len([
                pair for pair in self.preloader.popular_pairs
                if self._get_from_cache(pair) is not None
            ])
        }


# Глобальный экземпляр Unified API Manager
unified_api_manager = UnifiedAPIManager()