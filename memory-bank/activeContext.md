# ACTIVE CONTEXT - Crypto Helper Bot Performance Optimization 🔥

## Текущая фаза: PERFORMANCE OPTIMIZATION MODE
**Главная задача:** Устранение bottlenecks и масштабирование production-ready бота

## КОНТЕКСТ: ОТ WORKING BOT К OPTIMIZED BOT

### ✅ **ЧТО УЖЕ РАБОТАЕТ (Production v2.0):**
```
✅ Полностью функциональный бот с 14 валютными направлениями
✅ Пошаговый FSM флоу (/admin_bot → currency selection → rate → margin → amount → result)
✅ Двойная API интеграция (Rapira для crypto, APILayer для fiat)
✅ Продвинутая обработка ошибок и user-friendly messages
✅ Safety mechanisms (callback timeout fixes, message deduplication)
✅ Comprehensive testing (37+ unit tests passing)
✅ Production deployment на Railway
```

### 🔥 **ПРОБЛЕМЫ ПРОИЗВОДИТЕЛЬНОСТИ (обнаружены при анализе):**
```
❌ Memory Leak: fiat_rates_service._cache растет бесконечно
❌ Slow Response: 15+ секунд для некоторых операций
❌ API Bottlenecks: 30s timeouts, low connection pooling
❌ Logging Overhead: Debug logging в production
❌ Architecture Duplication: 2 API services, 3 formatters
❌ Scale Limitations: MemoryStorage ограничивает concurrent users до ~10
```

## CURRENT FOCUS: TASK-PERF-001 (Memory Leak Fix) 🚨

### **КРИТИЧЕСКАЯ ПРОБЛЕМА:**
```python
# В src/services/fiat_rates_service.py (строки ~380-390):
async def _cache_rates(self, base_currency: str, rates: Dict[str, float]):
    if not hasattr(self, '_cache'):
        self._cache = {}  # ❌ ПРОБЛЕМА: кэш растет без ограничений!
    
    cache_key = f"rates_{base_currency}"
    self._cache[cache_key] = (rates, datetime.now().timestamp())
    # ❌ Нет очистки устаревших записей
    # ❌ Нет ограничения размера кэша
```

### **IMPACT ANALYSIS:**
- **Memory Growth:** 1MB+ per hour в active usage
- **Production Risk:** OOM errors после 24-48 часов работы
- **User Impact:** Постепенное замедление ответов
- **Railway Impact:** Превышение memory limits, forced restarts

### **SOLUTION APPROACH:**
```python
# Реализовать в новом файле: src/services/cache_manager.py
class LRUCacheWithTTL:
    def __init__(self, max_size=100, ttl_seconds=300):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache = OrderedDict()  # LRU ordering
        self._timestamps = {}
    
    async def get(self, key):
        # Check TTL expiry + move to end (LRU)
    
    async def set(self, key, value):
        # Add with timestamp + evict oldest if over max_size
    
    async def cleanup_expired(self):
        # Background task для очистки просроченных записей
```

## IMMEDIATE TASKS FOR IMPLEMENT AGENT

### **TASK-PERF-001: Memory Leak Fix (Week 1, Critical)**

#### **Files to Create:**
```
src/services/cache_manager.py - NEW FILE
├── LRUCacheWithTTL class
├── CacheMetrics class (для мониторинга)
├── TTL cleanup background task
└── Memory usage tracking
```

#### **Files to Modify:**
```
src/services/fiat_rates_service.py
├── Replace self._cache with CacheManager instance
├── Remove manual cache management
├── Add cache metrics logging
└── Integrate TTL cleanup

src/config.py
├── Add CACHE_MAX_SIZE = 100
├── Add CACHE_TTL_SECONDS = 300 (5 minutes)
├── Add CACHE_CLEANUP_INTERVAL = 60 (1 minute)
└── Add CACHE_MONITORING_ENABLED = True
```

#### **Requirements:**
- [ ] Ограничить размер кэша до 100 записей (configurable)
- [ ] TTL = 5 минут для всех cache entries
- [ ] LRU eviction при превышении max_size
- [ ] Background cleanup task каждую минуту
- [ ] Memory usage monitoring и logging
- [ ] Graceful fallback если cache недоступен

### **TASK-PERF-002: API Performance (Week 1, High Priority)**

#### **Files to Modify:**
```
src/services/api_service.py
├── Increase connection limits: limit=200, limit_per_host=50
├── Reduce API_TIMEOUT: 30s → 10s for production
├── Add batch request capability
└── Implement rate preloading for popular pairs

src/services/rate_preloader.py - NEW FILE
├── Background task для предзагрузки USDT/RUB, USD/RUB, EUR/RUB
├── Update every 2 minutes
├── Cache warm-up strategy
└── Error handling для preload failures

src/config.py
├── Update API_TIMEOUT = 10 (was 30)
├── Add CONNECTION_POOL_SIZE = 200
├── Add CONNECTION_PER_HOST = 50  
├── Add PRELOAD_POPULAR_PAIRS = True
└── Add PRELOAD_INTERVAL = 120 seconds
```

## PERFORMANCE OPTIMIZATION CONTEXT

### **Current Performance Baseline:**
```
Response Time: 5-15 seconds (API dependent)
Memory Usage: 50MB baseline → unbounded growth ❌
Concurrent Users: ~10 максимум
API Success Rate: 95%
Memory Leaks: Confirmed in production ❌
Connection Pool: 100 total, 30 per host (too low)
```

### **Target Performance (Post-Optimization):**
```
Response Time: 3-8 seconds (50%+ improvement)
Memory Usage: Stable 50-100MB (no growth)
Concurrent Users: 50+ users  
API Success Rate: 99%+
Memory Leaks: Zero leaks confirmed
Connection Pool: 200 total, 50 per host
```

## TECHNICAL IMPLEMENTATION PRIORITIES

### **🔥 Week 1 - Critical Infrastructure:**
1. **Memory Management:** Fix the cache leak (prevents OOM crashes)
2. **API Optimization:** Faster responses and higher throughput
3. **Connection Scaling:** Support more concurrent operations

### **⚡ Week 2 - Architecture Cleanup:**
1. **Unified API Manager:** Consolidate Rapira + APILayer logic
2. **Production Logging:** Remove debug overhead, add structured logs
3. **Error Recovery:** Better retry logic and circuit breakers

### **📈 Week 3-4 - Advanced Features:**
1. **Redis Integration:** Scalable storage for multi-instance deployment
2. **Event System:** Real-time rate updates and notifications
3. **Monitoring Dashboard:** Performance metrics and alerting

## TESTING & VALIDATION STRATEGY

### **Performance Testing Requirements:**
```python
# Test scenarios для validation:
1. Memory Leak Test: Run bot 24+ hours, measure stable memory
2. Load Test: 50+ concurrent users, measure response times  
3. API Stress Test: High-frequency rate requests, measure success rate
4. Cache Efficiency Test: Hit rate >80%, eviction working correctly
5. Failover Test: API unavailability scenarios, graceful degradation
```

### **Monitoring Integration:**
```python
# Add metrics collection:
- Memory usage over time
- Cache hit/miss ratios  
- API response times by endpoint
- Concurrent user count
- Error rates by type
- Resource utilization (CPU, network)
```

## DEPLOYMENT & ROLLBACK STRATEGY

### **Safe Rollout Plan:**
1. **Local Testing:** All optimizations tested in development
2. **Staging Deployment:** Railway staging environment validation
3. **Feature Flags:** Toggle optimizations without code changes
4. **Gradual Rollout:** Monitor metrics during deployment
5. **Rollback Ready:** Quick revert to stable v2.0 if issues

### **Success Validation:**
- [ ] Memory usage stable for 24+ hours
- [ ] Response times <10s for 95% requests
- [ ] Zero OOM errors in production
- [ ] Support 50+ concurrent users
- [ ] Maintain 99%+ API success rate

## FILES CURRENTLY WORKING (Do Not Break!)

### **Production-Critical Files:**
```
src/handlers/admin_flow.py ✅     # Main user flow (700+ lines, tested)
src/services/api_service.py ✅    # Rapira integration (working)  
src/services/fiat_rates_service.py ❌ # APILayer (HAS MEMORY LEAK)
src/handlers/formatters.py ✅     # Message formatting (working)
src/config.py ✅                  # Environment config (stable)
```

### **Integration Points:**
- Railway deployment configuration
- Environment variables (.env)
- API credentials (Rapira + APILayer)
- FSM state management (aiogram)

**CRITICAL:** Все оптимизации должны сохранить existing functionality при улучшении performance!

## IMMEDIATE NEXT STEPS

1. **START WITH:** `src/services/cache_manager.py` - создать LRU cache с TTL
2. **THEN MODIFY:** `src/services/fiat_rates_service.py` - интегрировать new cache
3. **TEST LOCALLY:** Verify memory leak fixed + performance improved  
4. **DEPLOY TO STAGING:** Validate in Railway staging environment
5. **MONITOR PRODUCTION:** Ensure stable memory usage over 24+ hours

**STATUS:** Ready for implementation of TASK-PERF-001 (Memory Leak Fix) 🚀