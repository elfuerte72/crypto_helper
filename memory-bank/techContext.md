# TECH CONTEXT - Crypto Helper Bot

## Технологический стек (сохранен после переработки)

### Core Framework
- **Python 3.11** - основной язык
- **Aiogram 3.10** - Telegram Bot framework
- **aiohttp 3.9.1** - асинхронный HTTP клиент
- **python-dotenv 1.0.0** - управление конфигурацией

### Дополнительные библиотеки
- **Decimal** - точные математические вычисления
- **Enum** - типизация валют и состояний
- **datetime** - работа с временными метками
- **asyncio** - асинхронное программирование

## Внешние API (работают)

### Rapira API
```python
# Основной источник курса USDT/RUB
URL: https://api.rapira.net/open/market/rates
Headers: X-API-KEY: {RAPIRA_API_KEY}
Response: {"USDT_RUB": 85.3456}
```

### API Layer (ExchangeRates Data)
```python
# Кросс-курсы для USD/EUR
URL: https://api.apilayer.com/exchangerates_data
Headers: apikey: {API_LAYER_KEY}
Endpoints:
- /latest?symbols=USD&base=USDT
- /latest?symbols=EUR&base=USDT
```

## Файловая структура (после очистки)

### Основные файлы
```
src/
├── bot.py                 # Главный файл бота (обновлен)
├── config.py              # Конфигурация (очищена)
├── main.py                # Entry point
└── start_app.py           # Альтернативный запуск
```

### Handlers (упрощены/удалены)
```
src/handlers/
├── __init__.py            # Упрощенные экспорты
├── admin_handlers.py      # Заглушка /admin_bot 
├── bot_handlers.py        # Пустой роутер
└── [УДАЛЕНО] currency_pairs.py
└── [УДАЛЕНО] calculation_logic.py
└── [УДАЛЕНО] fsm_states.py
└── [УДАЛЕНО] keyboards.py
└── [УДАЛЕНО] formatters.py
└── [УДАЛЕНО] validation.py
└── [УДАЛЕНО] margin_calculation.py
```

### Services (сохранены)
```
src/services/
├── __init__.py            
├── api_service.py         # Rapira + API Layer клиенты
├── fiat_rates_service.py  # Фиатные курсы
└── models.py              # Модели данных API
```

### Utils (сохранены)
```
src/utils/
├── __init__.py
└── logger.py              # Система логирования
```

## Новая архитектура для реализации

### Модули для создания
```
src/handlers/
├── fsm_states.py          # FSM состояния (создать)
├── admin_flow.py          # Основной флоу (создать)
├── currency_selection.py  # Выбор валют (создать)
├── margin_input.py        # Ввод наценки (создать)
├── amount_input.py        # Ввод суммы (создать)
├── calculation.py         # Расчеты (создать)
├── keyboards.py           # Клавиатуры (создать)
├── validators.py          # Валидация (создать)
└── formatters.py          # Форматирование (создать)
```

### Domain модели
```python
# src/domain/entities.py (планируется)
from enum import Enum
from decimal import Decimal
from dataclasses import dataclass
from datetime import datetime

class Currency(Enum):
    RUB = "RUB"
    USDT = "USDT"
    USD = "USD"
    EUR = "EUR"

@dataclass
class ExchangePair:
    source: Currency
    target: Currency
    
@dataclass 
class ExchangeRate:
    pair: ExchangePair
    rate: Decimal
    timestamp: datetime
    source: str

@dataclass
class Deal:
    pair: ExchangePair
    amount: Decimal
    margin_percent: Decimal
    base_rate: Decimal
    final_rate: Decimal
    result: Decimal
```

## FSM состояния (aiogram)

### Определение состояний
```python
from aiogram.fsm.state import State, StatesGroup

class ExchangeFlow(StatesGroup):
    WAITING_FOR_SOURCE_CURRENCY = State()  
    WAITING_FOR_TARGET_CURRENCY = State()  
    WAITING_FOR_MARGIN = State()          
    WAITING_FOR_AMOUNT = State()           
    SHOWING_RESULT = State()               
```

### Хранение данных FSM
```python
# В aiogram FSMContext
await state.update_data(
    source_currency='RUB',
    target_currency='USDT', 
    base_rate=Decimal('85.30'),
    margin_percent=Decimal('2.0'),
    amount=Decimal('1000')
)
```

## Математические вычисления

### Логика наценки (КРИТИЧНО)
```python
from decimal import Decimal, ROUND_HALF_UP

def calculate_margin_rate(base_rate: Decimal, margin: Decimal, direction: str) -> Decimal:
    """
    Расчет курса с наценкой
    direction: 'rub_to_crypto' или 'crypto_to_rub'
    """
    if direction == 'rub_to_crypto':
        # RUB → USDT/USD/EUR: увеличиваем курс
        result = base_rate * (Decimal('1') + margin / Decimal('100'))
    else:
        # USDT → RUB: уменьшаем курс  
        result = base_rate * (Decimal('1') - margin / Decimal('100'))
    
    return result.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
```

### Кросс-курсы
```python
async def calculate_cross_rate(source: Currency, target: Currency) -> Decimal:
    """
    Расчет кросс-курса через USDT
    Например: RUB → USD = (USDT/RUB) / (USDT/USD)
    """
    if source == Currency.RUB and target == Currency.USD:
        usdt_rub = await api_service.get_usdt_rub_rate()
        usdt_usd = await api_service.get_usd_usdt_rate()
        return usdt_rub / usdt_usd
```

## Клавиатуры (aiogram)

### Inline keyboards
```python
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def create_source_currency_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="RUB", callback_data="source_rub"),
            InlineKeyboardButton(text="USDT", callback_data="source_usdt")
        ]
    ])

def create_target_currency_keyboard(source: Currency) -> InlineKeyboardMarkup:
    buttons = []
    if source == Currency.RUB:
        buttons = [
            [InlineKeyboardButton(text="USDT", callback_data="target_usdt")],
            [InlineKeyboardButton(text="USD", callback_data="target_usd")],
            [InlineKeyboardButton(text="EUR", callback_data="target_eur")]
        ]
    elif source == Currency.USDT:
        buttons = [
            [InlineKeyboardButton(text="RUB", callback_data="target_rub")]
        ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)
```

## Валидация

### Числовые значения
```python
def validate_margin(value: str) -> Decimal:
    """Валидация наценки 0.1% - 10%"""
    try:
        # Поддержка 2,5 → 2.5
        normalized = value.replace(',', '.')
        margin = Decimal(normalized)
        
        if margin < Decimal('0.1') or margin > Decimal('10'):
            raise ValueError("Наценка должна быть от 0.1% до 10%")
            
        return margin
    except (ValueError, InvalidOperation):
        raise ValueError("Введите число от 0.1 до 10")

def validate_amount(value: str) -> Decimal:
    """Валидация суммы"""
    try:
        normalized = value.replace(',', '.')
        amount = Decimal(normalized)
        
        if amount <= 0:
            raise ValueError("Сумма должна быть больше 0")
            
        return amount
    except (ValueError, InvalidOperation):
        raise ValueError("Введите корректную сумму")
```

## Обработка ошибок

### API fallback
```python
async def get_exchange_rate_with_fallback(pair: str) -> Decimal:
    try:
        return await rapira_api.get_rate(pair)
    except APIError:
        logger.warning(f"Rapira API failed for {pair}, trying API Layer")
        return await api_layer.get_rate(pair)
    except Exception as e:
        logger.error(f"All APIs failed for {pair}: {e}")
        return get_cached_rate(pair)
```

### FSM error handling
```python
@router.message(ExchangeFlow.WAITING_FOR_MARGIN)
async def handle_margin_error(message: Message, state: FSMContext):
    try:
        margin = validate_margin(message.text)
        await process_margin(margin, state)
    except ValueError as e:
        await message.reply(f"❌ {str(e)}")
```

## Конфигурация

### Environment variables
```bash
# .env
BOT_TOKEN=your_bot_token
RAPIRA_API_KEY=your_rapira_key
API_LAYER_KEY=your_api_layer_key
LOG_LEVEL=INFO
```

### Config объект
```python
class Config:
    BOT_TOKEN: str = os.getenv('BOT_TOKEN')
    RAPIRA_API_KEY: str = os.getenv('RAPIRA_API_KEY')
    API_LAYER_KEY: str = os.getenv('API_LAYER_KEY')
    
    # Бизнес-настройки
    MIN_MARGIN = Decimal('0.1')
    MAX_MARGIN = Decimal('10.0')
    RATE_CACHE_TTL = 300  # 5 минут
```

## Логирование

### Structured logging
```python
import logging

logger = logging.getLogger(__name__)

# Логирование операций
logger.info("Exchange calculation started", extra={
    'user_id': user_id,
    'source': 'RUB',
    'target': 'USDT',
    'amount': '1000'
})
```

## Развертывание

### Railway (текущее)
```bash
# Установленные переменные
railway variables set BOT_TOKEN=xxx
railway variables set RAPIRA_API_KEY=xxx  
railway variables set API_LAYER_KEY=xxx

# Запуск
railway up
```

### Docker (альтернатива)
```dockerfile
FROM python:3.11-slim
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY src/ ./src/
CMD ["python", "-m", "src.main"]
```