# SYSTEM PATTERNS - Crypto Helper Bot v2.0 Production + Optimization

## Реализованные архитектурные паттерны (v2.0 Production) ✅

### 1. Domain-Driven Design (DDD) - IMPLEMENTED ✅
```python
# PRODUCTION ENTITIES в src/handlers/fsm_states.py
class Currency(str, Enum):
    RUB = "RUB"
    USDT = "USDT"  
    USD = "USD"
    EUR = "EUR"
    THB = "THB"    # Thai Baht
    AED = "AED"    # UAE Dirham  
    ZAR = "ZAR"    # South African Rand
    IDR = "IDR"    # Indonesian Rupiah

# PRODUCTION DOMAIN LOGIC в src/services/models.py  
@dataclass
class ExchangeRate:
    pair: str
    rate: float
    timestamp: str
    source: str = "unknown"
    bid: Optional[float] = None
    ask: Optional[float] = None
    # ... additional market data fields

# BUSINESS LOGIC в src/handlers/admin_flow.py
class ExchangeCalculator:
    @staticmethod
    def calculate_final_rate(source: Currency, target: Currency, 
                           base_rate: Decimal, margin_percent: Decimal) -> Decimal:
        """PRODUCTION BUSINESS RULE IMPLEMENTATION"""
        if source == Currency.RUB:
            # Client gives RUB → increase rate
            return base_rate * (Decimal('1') + margin_percent / Decimal('100'))
        else:
            # Client gives USDT → decrease rate
            return base_rate * (Decimal('1') - margin_percent / Decimal('100'))
```

### 2. Finite State Machine (FSM) Pattern - PRODUCTION READY ✅
```python
# IMPLEMENTED в src/handlers/fsm_states.py
class ExchangeFlow(StatesGroup):
    WAITING_FOR_SOURCE_CURRENCY = State()  # RUB vs USDT selection
    WAITING_FOR_TARGET_CURRENCY = State()  # Target currency selection
    WAITING_FOR_MARGIN = State()           # Margin percentage input
    WAITING_FOR_AMOUNT = State()           # Transaction amount input  
    SHOWING_RESULT = State()               # Final calculation display

# PRODUCTION FSM FLOW в src/handlers/admin_flow.py (700+ lines)
# - Complete error handling
# - Callback timeout fixes (TASK-CRYPTO-002)
# - User-friendly error messages (TASK-CRYPTO-004)
# - Safe message editing (prevents "message not modified")
# - Loading progress indicators
# - Cancellation support
```

### 3. Repository Pattern - API Integration ✅ + OPTIMIZATION NEEDED 🔥
```python
# CURRENT IMPLEMENTATION (works but needs optimization)
# src/services/api_service.py - Rapira API Repository
class APIService:
    async def get_usdt_rub_rate(self) -> ExchangeRate:
        """Rapira API - crypto rates"""
        
    async def get_all_rates(self) -> Dict[str, ExchangeRate]:
        """Batch rate retrieval"""

# src/services/fiat_rates_service.py - APILayer Repository  
class FiatRatesService:
    async def get_fiat_exchange_rate(self, pair: str) -> ExchangeRate:
        """APILayer - fiat cross-rates"""
        
    # ❌ PROBLEM: Unbounded cache growth (memory leak)
    async def _cache_rates(self, base_currency: str, rates: Dict):
        if not hasattr(self, '_cache'):
            self._cache = {}  # Memory leak source!

# OPTIMIZATION TARGET: Unified Repository Pattern
# src/services/unified_api_manager.py - PLANNED
class UnifiedExchangeRateRepository:
    """Single interface for all rate sources"""
    async def get_rate(self, source: Currency, target: Currency) -> ExchangeRate:
        # Auto-route to appropriate API
        # Circuit breaker protection  
        # Unified caching strategy
```

### 4. Strategy Pattern - Rate Calculation ✅
```python
# PRODUCTION IMPLEMENTATION в src/handlers/admin_flow.py
class ExchangeCalculator:
    @staticmethod  
    def calculate_final_rate(source: Currency, target: Currency,
                           base_rate: Decimal, margin_percent: Decimal) -> Decimal:
        """
        STRATEGY PATTERN: Different margin calculation by direction
        
        Strategy 1 - RUB Source (client sells RUB):
        RUB → USDT/USD/EUR: increase rate (client gets less target currency)
        
        Strategy 2 - USDT Source (client sells USDT):  
        USDT → RUB/USD/EUR: decrease rate (client gets less target currency)
        """
        margin_factor = margin_percent / Decimal('100')
        
        if source == Currency.RUB:
            return base_rate * (Decimal('1') + margin_factor)
        else:
            return base_rate * (Decimal('1') - margin_factor)
    
    @staticmethod
    def calculate_result(source: Currency, target: Currency,
                        amount: Decimal, final_rate: Decimal) -> Decimal:
        """Result calculation strategy by currency direction"""
        if source == Currency.RUB:
            return amount / final_rate  # RUB amount / rate = target amount
        else:
            return amount * final_rate  # USDT amount * rate = target amount
```

### 5. Command Pattern - Message Handlers ✅
```python
# PRODUCTION HANDLERS в src/handlers/admin_flow.py
class CommandHandlers:
    
    @admin_flow_router.callback_query(ExchangeFlow.WAITING_FOR_SOURCE_CURRENCY)
    async def handle_source_currency_selection(callback_query, state):
        """Command: Process source currency selection"""
        
    @admin_flow_router.callback_query(ExchangeFlow.WAITING_FOR_TARGET_CURRENCY)  
    async def handle_target_currency_selection(callback_query, state):
        """Command: Process target currency + fetch rates"""
        
    @admin_flow_router.message(ExchangeFlow.WAITING_FOR_MARGIN)
    async def handle_margin_input(message, state):
        """Command: Process margin percentage input"""
        
    @admin_flow_router.message(ExchangeFlow.WAITING_FOR_AMOUNT)
    async def handle_amount_input(message, state):
        """Command: Process amount input + calculate final result"""
```

## OPTIMIZATION PATTERNS (Performance Issues) 🔥

### 1. Memory Management Anti-Pattern - CRITICAL ISSUE ❌
```python
# CURRENT PROBLEM в src/services/fiat_rates_service.py
class FiatRatesService:
    async def _cache_rates(self, base_currency: str, rates: Dict[str, float]):
        if not hasattr(self, '_cache'):
            self._cache = {}  # ❌ ANTI-PATTERN: Unbounded growth
        
        cache_key = f"rates_{base_currency}"
        self._cache[cache_key] = (rates, datetime.now().timestamp())
        # ❌ No TTL cleanup, no size limits, no eviction policy

# IMPACT: Memory leak → OOM crashes in production after 24-48h

# SOLUTION PATTERN: LRU Cache with TTL
# src/services/cache_manager.py - TO BE IMPLEMENTED
class LRUCacheWithTTL:
    """Proper cache pattern with bounded memory"""
    def __init__(self, max_size=100, ttl_seconds=300):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache = OrderedDict()  # LRU ordering
        self._timestamps = {}
    
    async def get(self, key: str) -> Optional[Any]:
        # Check TTL + move to end (LRU access)
        
    async def set(self, key: str, value: Any):
        # Add + evict oldest if over max_size
        
    async def cleanup_expired(self):
        # Background TTL cleanup task
```

### 2. Performance Anti-Pattern - API Bottlenecks ❌
```python
# CURRENT PROBLEM в src/services/api_service.py
connector = aiohttp.TCPConnector(
    limit=100,        # ❌ Too low for production
    limit_per_host=30 # ❌ Limits concurrent requests
)

# CURRENT PROBLEM в src/config.py
API_TIMEOUT = 30  # ❌ Too high for callback handling

# IMPACT: Slow responses (15+ sec), low concurrency (~10 users)

# SOLUTION PATTERN: Optimized Connection Pooling
connector = aiohttp.TCPConnector(
    limit=200,        # ↑ 2x increase
    limit_per_host=50, # ↑ 67% increase
    keepalive_timeout=60,
    enable_cleanup_closed=True
)

# SOLUTION PATTERN: Production Timeouts
CALLBACK_API_TIMEOUT = 3   # Quick callback response
API_TIMEOUT = 10          # Reasonable for production
```

### 3. Architecture Duplication Anti-Pattern ⚠️
```python
# CURRENT PROBLEM: Separate API services without unified interface
# fiat_rates_service.py - APILayer logic
# api_service.py - Rapira logic
# ❌ Duplicated error handling, retry logic, monitoring

# SOLUTION PATTERN: Unified API Manager
class UnifiedAPIManager:
    """Single entry point pattern"""
    def __init__(self):
        self.rapira_client = RapiraClient()
        self.apilayer_client = APILayerClient()
        self.circuit_breaker = CircuitBreaker()
    
    async def get_rate(self, source: Currency, target: Currency):
        # Auto-route based on currency types
        # Unified error handling
        # Single monitoring point
        # Consistent retry logic
```

## PRODUCTION PATTERNS (Working Well) ✅

### 1. Safe Message Editing Pattern ✅
```python
# IMPLEMENTED в src/handlers/formatters.py
class SafeMessageEditor:
    """Prevents 'message is not modified' errors"""
    
    @staticmethod
    def _get_message_hash(text: str, markup_data: str = "") -> str:
        """Content hash for change detection"""
        content = f"{text}|{markup_data}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    @staticmethod
    async def safe_edit_message(message, new_text, reply_markup=None):
        """Edit only if content actually changed"""
        current_hash = SafeMessageEditor._get_message_hash(
            message.text or "", str(message.reply_markup)
        )
        new_hash = SafeMessageEditor._get_message_hash(
            new_text, str(reply_markup)
        )
        
        if current_hash == new_hash:
            return True  # Skip edit, content identical
        
        # Proceed with edit + retry logic
```

### 2. Async Loading Pattern ✅
```python
# IMPLEMENTED в src/handlers/admin_flow.py  
async def get_exchange_rate_with_loading(message, source_currency, target_currency):
    """Non-blocking rate fetching with progress indicators"""
    
    # Show immediate loading message
    loading_text = LoadingMessageFormatter.format_api_loading_message("Rapira API")
    await SafeMessageEditor.safe_edit_message(message, loading_text)
    
    # Parallel: API request + progress updates
    api_task = asyncio.create_task(ExchangeCalculator.get_base_rate_for_pair())
    
    # Update progress while waiting
    progress_text = LoadingMessageFormatter.format_loading_with_progress(
        "Getting rate", 1, 2
    )
    await SafeMessageEditor.safe_edit_message(message, progress_text)
    
    # Get result with timeout
    base_rate = await asyncio.wait_for(api_task, timeout=config.CALLBACK_API_TIMEOUT)
```

### 3. Input Validation Pattern ✅
```python
# IMPLEMENTED в src/handlers/validators.py
class ExchangeValidator:
    """Comprehensive input validation with detailed error messages"""
    
    @staticmethod
    def validate_margin_input(text: str) -> ValidationResult:
        """Supports: 2, 1.5, 2,5, 2% formats"""
        # Sanitization: remove %, normalize decimal separator
        clean_text = text.strip().replace('%', '').replace(',', '.')
        
        # Range validation: 0.1% - 10%
        margin = Decimal(clean_text)
        if not (Decimal('0.1') <= margin <= Decimal('10.0')):
            return ValidationResult(False, error="Naценка должна быть от 0.1% до 10%")
        
        return ValidationResult(True, value=margin)
    
    @staticmethod  
    def validate_currency_pair(source: Currency, target: Currency) -> ValidationResult:
        """Business rule validation for supported pairs"""
        if not is_valid_pair(source, target):
            return ValidationResult(
                False, 
                error=f"Направление {source.value} → {target.value} не поддерживается"
            )
```

### 4. Error Recovery Pattern ✅
```python
# IMPLEMENTED в src/handlers/formatters.py
class UserFriendlyErrorFormatter:
    """Convert technical errors to user-friendly messages"""
    
    @staticmethod
    def format_api_timeout_error(api_name: str, source: Currency, target: Currency):
        """Context-aware timeout error messaging"""
        return (
            f"⚠️ <b>Курс валют недоступен</b>\n\n"
            f"📊 <b>Валютная пара:</b> {source.value} → {target.value}\n"
            f"🔌 <b>Сервис:</b> {api_name}\n\n"
            f"❌ <b>Актуальный курс недоступен</b>\n\n"
            f"⏰ <b>Причина:</b> Сервер курсов не отвечает\n\n"
            f"⚡ <i>Мы НЕ показываем устаревшие курсы для вашей безопасности</i>"
        )
```

## PLANNED OPTIMIZATION PATTERNS

### 1. Circuit Breaker Pattern - WEEK 2 🔧
```python
# src/services/circuit_breaker.py - TO BE IMPLEMENTED
class CircuitBreaker:
    """Prevent cascade failures in API calls"""
    
    def __init__(self, failure_threshold=5, recovery_timeout=60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    async def call(self, func, *args, **kwargs):
        if self.state == 'OPEN':
            if self._should_attempt_reset():
                self.state = 'HALF_OPEN'
            else:
                raise CircuitBreakerOpenError()
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
```

### 2. Event-Driven Pattern - WEEK 3 📡
```python
# src/events/event_bus.py - TO BE IMPLEMENTED  
class EventBus:
    """Decoupled component communication"""
    
    def __init__(self):
        self._subscribers = defaultdict(list)
    
    def subscribe(self, event_type: str, handler: Callable):
        self._subscribers[event_type].append(handler)
    
    async def publish(self, event_type: str, data: Any):
        for handler in self._subscribers[event_type]:
            await handler(data)

# Usage:
# event_bus.subscribe('rate_updated', update_cache_handler)
# await event_bus.publish('rate_updated', {'pair': 'USDT/RUB', 'rate': 85.3})
```

### 3. Background Task Pattern - WEEK 1 ⏰
```python
# src/services/rate_preloader.py - TO BE IMPLEMENTED
class RatePreloader:
    """Proactive cache warming for popular pairs"""
    
    async def start_preloading(self):
        """Background task every 2 minutes"""
        while True:
            try:
                await self.preload_popular_pairs()
                await asyncio.sleep(120)  # 2 minutes
            except Exception as e:
                logger.error(f"Preload error: {e}")
                await asyncio.sleep(30)  # Retry in 30 seconds
    
    async def preload_popular_pairs(self):
        """Concurrent preloading of USDT/RUB, USD/RUB, EUR/RUB"""
        popular_pairs = [
            (Currency.USDT, Currency.RUB),
            (Currency.USD, Currency.RUB), 
            (Currency.EUR, Currency.RUB)
        ]
        
        tasks = [
            self.unified_api_manager.get_rate(source, target)
            for source, target in popular_pairs
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
```

## MONITORING PATTERNS (Planned) 📊

### 1. Metrics Collection Pattern - WEEK 4
```python
# src/monitoring/metrics_collector.py - TO BE IMPLEMENTED
class MetricsCollector:
    """Production monitoring and alerting"""
    
    async def collect_memory_metrics(self):
        """Track memory usage trends, detect leaks"""
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        
        await self.emit_metric('memory_usage_mb', memory_mb)
        
        if memory_mb > 150:  # Alert threshold
            await self.emit_alert('high_memory_usage', memory_mb)
    
    async def collect_api_metrics(self):
        """API performance monitoring"""
        # Response times, success rates, error types
        
    async def collect_cache_metrics(self):
        """Cache efficiency monitoring"""
        # Hit rates, eviction counts, memory usage
```

### 2. Health Check Pattern - PRODUCTION ✅ + ENHANCEMENT
```python
# src/health_check.py - CURRENT (basic) + ENHANCEMENTS PLANNED
class HealthChecker:
    """Multi-layer health validation"""
    
    async def comprehensive_health_check(self):
        """
        CURRENT: Basic API connectivity
        PLANNED: Memory usage, cache status, FSM state counts, error rates
        """
        health_data = {
            'timestamp': datetime.now().isoformat(),
            'memory_usage': self._get_memory_usage(),
            'cache_stats': await self.cache_manager.get_stats(),
            'api_status': await self._check_apis(),
            'fsm_sessions': await self._count_active_sessions(),
        }
        
        return health_data
```

## SUCCESS PATTERNS (Validation) ✅

### 1. Comprehensive Testing Pattern ✅
```python
# IMPLEMENTED: 37+ unit tests across critical components
tests/
├── handlers/test_callback_timeout_fixes.py    # 18 tests - FSM flow
├── services/test_logging_functional.py        # 14 tests - API integration  
├── services/test_improved_logging_simple.py   # Additional coverage
└── test_telegram_fixes.py                     # 22 tests - UX improvements

# PATTERN: Test doubles for external dependencies
class MockAPIService:
    def __init__(self, mock_rates):
        self.mock_rates = mock_rates
    
    async def get_usdt_rub_rate(self):
        return ExchangeRate(rate=self.mock_rates['USDT/RUB'])
```

### 2. Configuration Pattern ✅
```python
# IMPLEMENTED в src/config.py - Environment-driven configuration
class Config:
    # Production vs Development settings
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    IS_LOCAL_DEVELOPMENT = os.getenv('ENVIRONMENT', 'production') == 'development'
    
    # Business rules configuration
    MIN_MARGIN_PERCENT = 0.1
    MAX_MARGIN_PERCENT = 10.0
    SUPPORTED_SOURCE_CURRENCIES = ['RUB', 'USDT']
    
    # Performance tuning (optimization targets)
    API_TIMEOUT = int(os.getenv('API_TIMEOUT', '30'))         # → 10
    CALLBACK_API_TIMEOUT = int(os.getenv('CALLBACK_API_TIMEOUT', '3'))
```

**STATUS:** Production patterns working, optimization patterns ready for implementation 🚀