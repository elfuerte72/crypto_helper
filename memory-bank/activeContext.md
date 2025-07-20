# ACTIVE CONTEXT - Crypto Helper Bot (Новая логика)

## Текущая фаза: IMPLEMENT MODE
**Задача:** Реализация новой пошаговой логики обмена валют

## Статус проекта: ПОЛНАЯ ПЕРЕРАБОТКА
- [x] ✅ Создана новая ветка разработки
- [x] ✅ Удалена вся старая логика валютных пар и расчетов  
- [x] ✅ Очищена архитектура для новой разработки
- [ ] 🔄 **ТЕКУЩЕЕ:** Реализация новой логики (Фаза 1)

## Что было удалено (старая логика)
```
УДАЛЕННЫЕ ФАЙЛЫ:
- src/handlers/currency_pairs.py - жестко заданные валютные пары
- src/handlers/calculation_logic.py - старая логика расчета наценки  
- src/handlers/fsm_states.py - состояния для старого флоу
- src/handlers/keyboards.py - клавиатуры для валютных пар
- src/handlers/formatters.py - форматирование для старой логики
- src/handlers/validation.py - валидация для старой системы
- src/handlers/margin_calculation.py - дублированный функционал
```

## Новый бизнес-флоу (из промпта)

### Команда: `/admin_bot`
1. **Выбор исходной валюты:** RUB или USDT (что отдает клиент)
2. **Выбор целевой валюты:** 
   - Если RUB → USDT, USD, EUR
   - Если USDT → RUB
3. **Показ курса:** Унифицированный формат "1 USDT = X RUB"
4. **Ввод наценки:** Только число (2, 1.5, 0.75)
5. **Ввод суммы:** Число в отдаваемой валюте  
6. **Результат:** Расчет с правильной логикой наценки

## Приоритет IMPLEMENT (что делать сейчас)

### 🔥 КРИТИЧЕСКИЙ - Фаза 1: Базовая архитектура FSM
```python
# СОЗДАТЬ:
src/handlers/fsm_states.py      # 5 состояний FSM
src/handlers/admin_flow.py      # Основной флоу /admin_bot  
src/handlers/keyboards.py       # Клавиатуры для каждого шага
src/handlers/validators.py      # Валидация вводов
```

### FSM состояния для реализации:
```python
class ExchangeFlow(StatesGroup):
    WAITING_FOR_SOURCE_CURRENCY = State()  # RUB/USDT
    WAITING_FOR_TARGET_CURRENCY = State()  # Целевая валюта
    WAITING_FOR_MARGIN = State()           # Ввод наценки %
    WAITING_FOR_AMOUNT = State()           # Ввод суммы
    SHOWING_RESULT = State()               # Показ результата
```

## Ключевая логика наценки (ВАЖНО!)
```python
# RUB → USDT/USD/EUR: Итоговый = Базовый × (1 + наценка/100)
# USDT → RUB: Итоговый = Базовый × (1 - наценка/100)
```

## Технические детали для IMPLEMENT

### Domain модели:
```python
class Currency(Enum):
    RUB = "RUB"
    USDT = "USDT" 
    USD = "USD"
    EUR = "EUR"
```

### Конфигурация:
```python
SUPPORTED_SOURCES = [Currency.RUB, Currency.USDT]
TARGETS_FOR_RUB = [Currency.USDT, Currency.USD, Currency.EUR]
TARGETS_FOR_USDT = [Currency.RUB]
```

### Унифицированное отображение курса:
**Для ВСЕХ пар показывать:** `1 USDT = [число] RUB`

## Текущие рабочие файлы
- `src/handlers/admin_handlers.py` - команда /admin_bot (заглушка)
- `src/handlers/bot_handlers.py` - пустой роутер (заглушка)
- `src/bot.py` - основной файл (обновлен для новой логики)
- `src/config.py` - конфигурация (очищена)
- `src/services/api_service.py` - API клиенты (рабочие)

## Следующие шаги IMPLEMENT
1. **Создать fsm_states.py** - определить 5 состояний
2. **Создать admin_flow.py** - обработчик /admin_bot + FSM
3. **Создать keyboards.py** - кнопки для каждого шага
4. **Обновить admin_handlers.py** - интегрировать новый флоу
5. **Тестировать** - базовый переход между состояниями

## Критерии успеха Фазы 1
- [ ] Команда /admin_bot запускает FSM
- [ ] Показывает кнопки RUB/USDT
- [ ] Переходит в следующие состояния
- [ ] Динамические кнопки целевой валюты
- [ ] Базовая навигация работает

## API endpoints (уже работают)
- Rapira API: курсы USDT/RUB
- API Layer: кросс-курсы USD/USDT, EUR/USDT

## Примеры для тестирования
- RUB → USDT: курс 80, наценка 2% → 81.6, сумма 1000 → 12.25 USDT
- USDT → RUB: курс 80, наценка 2% → 78.4, сумма 10 → 784 RUB