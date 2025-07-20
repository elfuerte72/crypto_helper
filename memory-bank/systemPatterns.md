# SYSTEM PATTERNS - Crypto Helper Bot

## Архитектурные паттерны (версия 2.0)

### 1. Domain-Driven Design (DDD)
```python
# Основные сущности
class Currency(Enum):
    RUB = "RUB"
    USDT = "USDT"
    USD = "USD" 
    EUR = "EUR"

class ExchangePair:
    source: Currency      # Что отдает клиент
    target: Currency      # Что получает клиент

class ExchangeRate:
    pair: ExchangePair
    rate: Decimal         # Базовый курс
    timestamp: datetime
    source: str           # API источник

class Deal:
    pair: ExchangePair
    amount: Decimal       # Сумма в исходной валюте
    margin_percent: Decimal
    base_rate: Decimal
    final_rate: Decimal   # С учетом наценки
    result: Decimal       # Итоговая сумма
```

### 2. Finite State Machine (FSM) Pattern
```python
class ExchangeFlow(StatesGroup):
    WAITING_FOR_SOURCE_CURRENCY = State()  # RUB или USDT
    WAITING_FOR_TARGET_CURRENCY = State()  # Целевая валюта
    WAITING_FOR_MARGIN = State()           # Процент наценки
    WAITING_FOR_AMOUNT = State()           # Сумма сделки
    SHOWING_RESULT = State()               # Результат расчета
```

### 3. Strategy Pattern - Расчет наценки
```python
class MarginCalculator:
    @staticmethod
    def calculate_for_rub_source(base_rate: Decimal, margin: Decimal) -> Decimal:
        """RUB → USDT/USD/EUR: повышаем курс"""
        return base_rate * (1 + margin / 100)
    
    @staticmethod 
    def calculate_for_usdt_source(base_rate: Decimal, margin: Decimal) -> Decimal:
        """USDT → RUB: понижаем курс""" 
        return base_rate * (1 - margin / 100)
```

### 4. Repository Pattern - API интеграция
```python
class ExchangeRateRepository:
    async def get_usdt_rub_rate() -> ExchangeRate:
        """Rapira API - базовый курс"""
        
    async def get_usd_usdt_rate() -> ExchangeRate:
        """API Layer - для кросс-курса"""
        
    async def get_eur_usdt_rate() -> ExchangeRate:
        """API Layer - для кросс-курса"""
        
    async def calculate_cross_rate(source: Currency, target: Currency) -> ExchangeRate:
        """Расчет кросс-курсов через USDT"""
```

### 5. Command Pattern - Обработчики
```python
class HandleSourceCurrencySelection:
    async def execute(currency: Currency, state: FSMContext)
    
class HandleTargetCurrencySelection:
    async def execute(currency: Currency, state: FSMContext)
    
class HandleMarginInput:
    async def execute(margin: Decimal, state: FSMContext)
    
class HandleAmountInput:
    async def execute(amount: Decimal, state: FSMContext)
```

## Модульная архитектура

### Слои приложения
```
┌─────────────────────────────────────┐
│           Presentation Layer         │
│  (Telegram Handlers, Keyboards)     │
├─────────────────────────────────────┤
│          Application Layer           │
│     (Use Cases, FSM Flow)           │
├─────────────────────────────────────┤
│            Domain Layer              │
│  (Entities, Business Logic)         │
├─────────────────────────────────────┤
│         Infrastructure Layer         │
│    (API Clients, Config)            │
└─────────────────────────────────────┘
```

### Структура модулей
```
handlers/
├── admin_flow.py          # Presentation: основной флоу
├── currency_selection.py  # Application: логика выбора
├── margin_input.py        # Application: ввод наценки
├── amount_input.py        # Application: ввод суммы
├── calculation.py         # Domain: бизнес-логика расчетов
├── keyboards.py           # Presentation: UI элементы
├── validators.py          # Domain: валидация правил
├── formatters.py          # Presentation: форматирование
└── fsm_states.py          # Application: управление состоянием
```

## Паттерны обработки ошибок

### 1. Circuit Breaker для API
```python
class APICircuitBreaker:
    async def call_with_fallback(api_call, fallback_action):
        try:
            return await api_call()
        except APIError:
            return await fallback_action()  # Кеш или резервный API
```

### 2. Graceful Degradation
```python
async def get_exchange_rate(pair: ExchangePair):
    try:
        # Основной API
        return await rapira_api.get_rate(pair)
    except APIError:
        # Резервный API
        return await api_layer.get_rate(pair)
    except Exception:
        # Кешированные данные
        return cache.get_last_rate(pair)
```

### 3. Validation Chain
```python
class ValidationChain:
    def __init__(self):
        self.validators = []
    
    def add_validator(self, validator):
        self.validators.append(validator)
        
    def validate(self, value):
        for validator in self.validators:
            if not validator.is_valid(value):
                raise ValidationError(validator.error_message)
```

## Паттерны конфигурации

### 1. Configuration Objects
```python
@dataclass
class ExchangeConfig:
    supported_sources: List[Currency] = field(default_factory=lambda: [Currency.RUB, Currency.USDT])
    targets_for_rub: List[Currency] = field(default_factory=lambda: [Currency.USDT, Currency.USD, Currency.EUR])
    targets_for_usdt: List[Currency] = field(default_factory=lambda: [Currency.RUB])
    min_margin: Decimal = Decimal('0.1')
    max_margin: Decimal = Decimal('10.0')
    rate_cache_ttl: int = 300  # 5 минут
```

### 2. Environment-based Configuration
```python
class Config:
    @classmethod
    def get_exchange_config(cls) -> ExchangeConfig:
        return ExchangeConfig(
            min_margin=Decimal(os.getenv('MIN_MARGIN', '0.1')),
            max_margin=Decimal(os.getenv('MAX_MARGIN', '10.0')),
        )
```

## Паттерны тестирования

### 1. Mock Objects для API
```python
class MockExchangeRateRepository:
    def __init__(self, mock_rates: Dict[str, Decimal]):
        self.mock_rates = mock_rates
        
    async def get_usdt_rub_rate(self) -> ExchangeRate:
        return ExchangeRate(rate=self.mock_rates['USDT/RUB'])
```

### 2. Test Fixtures
```python
@pytest.fixture
def sample_deal():
    return Deal(
        pair=ExchangePair(Currency.RUB, Currency.USDT),
        amount=Decimal('1000'),
        margin_percent=Decimal('2'),
        base_rate=Decimal('80'),
    )
```

### 3. State Machine Testing
```python
class TestFSMFlow:
    async def test_complete_flow(self):
        # Arrange: начальное состояние
        # Act: прохождение всех состояний
        # Assert: финальный результат
```

## Паттерны безопасности

### 1. Input Sanitization
```python
class SafeDecimalValidator:
    @staticmethod
    def validate(value: str) -> Decimal:
        # Очистка от опасных символов
        cleaned = re.sub(r'[^\d.,]', '', value)
        # Нормализация разделителей
        normalized = cleaned.replace(',', '.')
        return Decimal(normalized)
```

### 2. Rate Limiting
```python
class UserRateLimit:
    def __init__(self, max_requests: int, window_seconds: int):
        self.limits = {}
        
    def is_allowed(self, user_id: int) -> bool:
        # Проверка лимитов по пользователю
```

## Паттерны логирования

### 1. Structured Logging
```python
logger.info("Exchange calculation completed", extra={
    'user_id': user_id,
    'source_currency': deal.pair.source.value,
    'target_currency': deal.pair.target.value, 
    'amount': float(deal.amount),
    'margin': float(deal.margin_percent),
    'result': float(deal.result)
})
```

### 2. Context Logging
```python
class DealContext:
    def __init__(self, user_id: int, deal_id: str):
        self.user_id = user_id
        self.deal_id = deal_id
        
    def log(self, message: str, level: str = 'info'):
        logger.log(level, f"[{self.deal_id}] {message}", extra={'user_id': self.user_id})
```