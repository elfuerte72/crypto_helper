# Crypto Helper Telegram Bot

Минималистичный MVP Telegram-бот для автоматизации получения курсов криптовалют с наценкой для менеджеров в каналах.

## 🎯 Описание

Бот предназначен для менеджеров в Telegram каналах, которые работают с криптовалютными сделками. Основная функция - быстрое получение актуальных курсов с возможностью добавления наценки.

## 🔧 Технологический стек

- **Python 3.11+**
- **Aiogram 3.x** - фреймворк для Telegram ботов
- **aiohttp** - HTTP клиент для API запросов
- **python-dotenv** - управление конфигурацией
- **Rapira API** - источник криптовалютных курсов
- **APILayer** - источник фиатных валютных курсов

## 🌐 API Интеграция

### Rapira API (Криптовалюты)
- Получение курсов криптовалют (BTC, ETH, TON, USDT и др.)
- Публичный API без необходимости ключа
- Поддержка пар с рублем и долларом

### APILayer (Фиатные валюты)
- **Exchange Rates Data API** - основные валютные курсы
- **Currency Data API** - дополнительные данные о валютах
- Профессиональная точность курсов
- Поддержка 170+ валют

## 📋 Поддерживаемые валютные пары

### Фиатные валюты (через APILayer):
- USD/RUB, EUR/RUB, USD/ZAR, USD/THB
- USD/AED, USD/IDR, EUR/ZAR
- Кросс-курсы: RUB/ZAR, RUB/THB, RUB/AED, RUB/IDR

### Криптовалюты (через Rapira API):
- BTC/USDT, ETH/USDT, TON/USDT, USDT/RUB
- BTC/RUB, ETH/RUB, TON/RUB (через расчет)

### Поддерживаемые валюты:
- **Фиат**: USD, EUR, RUB, ZAR, THB, AED, IDR, GBP, JPY, CAD, AUD, CHF, CNY
- **Крипто**: BTC, ETH, TON, USDT, USDC, LTC, TRX, BNB, DAI, DOGE, ETC, OP, XMR, SOL, NOT

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Конфигурация

Скопируйте `.env.example` в `.env` и заполните необходимые значения:

```bash
cp .env.example .env
```

Обязательные переменные:
```env
BOT_TOKEN=your_telegram_bot_token
API_LAYER_KEY=your_apilayer_api_key
RAPIRA_API_URL=https://api.rapira.net/open/market/rates
API_LAYER_URL=https://api.apilayer.com/exchangerates_data
```

### 3. Тестирование APILayer интеграции

**Быстрая проверка (30 секунд):**
```bash
python APILayer/quick_test.py
```

**Проверка статуса подписок:**
```bash
python APILayer/check_subscriptions.py
```

**Полная демонстрация:**
```bash
python APILayer/demo.py
```

**Полное тестирование:**
```bash
python APILayer/test_apilayer_full.py
```

📖 **Подробная документация**: [APILayer/README.md](APILayer/README.md)

### 4. Запуск бота

```bash
python src/main.py
```

## 🔑 Основные команды

- `/admin_bot` - Запуск процесса получения курса (только для админов канала)
- `/start` - Приветственное сообщение
- `/test` - Тест функциональности

## 📊 Система мониторинга

### Health Check
Бот включает систему мониторинга состояния API:

```bash
python src/health_check.py
```

Проверяет:
- ✅ Доступность Rapira API
- ✅ Доступность APILayer
- ✅ Скорость ответа
- ✅ Качество данных

### Автоматическое переключение
- **Фиатные пары** → APILayer
- **Криптовалютные пары** → Rapira API  
- **Смешанные пары** → Rapira API
- **Fallback механизмы** при недоступности API

## 📖 Workflow

1. Клиент пишет в канал о желании совершить сделку
2. Менеджер запускает команду `/admin_bot`
3. Бот проверяет права администратора в канале
4. Менеджер выбирает валютную пару
5. Бот автоматически определяет нужный API (Rapira/APILayer)
6. Получает актуальный курс с профессиональной точностью
7. Менеджер указывает процентную наценку
8. Бот рассчитывает итоговый курс и публикует в канал
9. Дальнейшая коммуникация происходит вручную

## 🔧 Архитектура

```
API Service (Unified)
├── Rapira API Service    # Криптовалютные курсы
├── APILayer Service      # Фиатные валютные курсы
├── Cross-rate Calculator # Расчет кросс-курсов
├── Health Monitor        # Мониторинг состояния
└── Error Handler         # Обработка ошибок
```

### Ключевые особенности:
- **Единый интерфейс** для всех типов валют
- **Автоматическое определение** типа валютной пары
- **Retry логика** с экспоненциальным backoff
- **Connection pooling** для оптимизации производительности
- **Подробное логирование** для диагностики

## 📁 Структура проекта

```
crypto_helpler/
├── src/
│   ├── main.py                    # Основной файл бота
│   ├── config.py                  # Конфигурация
│   ├── services/
│   │   ├── api_service.py         # Объединенный API сервис
│   │   ├── fiat_rates_service.py  # APILayer сервис
│   │   └── models.py              # Модели данных
│   ├── handlers/                  # Обработчики команд
│   └── utils/                     # Утилиты
├── APILayer/                      # Файлы интеграции APILayer
│   ├── quick_test.py              # Быстрая проверка APILayer
│   ├── check_subscriptions.py     # Проверка подписок
│   ├── demo.py                    # Демонстрация работы
│   ├── test_apilayer_full.py      # Полное тестирование
│   ├── APILAYER_BOT_INTEGRATION_COMPLETE.md # Техническая документация
│   ├── FINAL_INTEGRATION_REPORT.md # Финальный отчет
│   └── README.md                  # Документация APILayer
├── tests/                         # Основные тесты
├── docs/                          # Документация
├── memory-bank/                   # Контекст проекта
├── requirements.txt               # Зависимости
└── README.md                     # Этот файл
```

## 🚨 Диагностика и решение проблем

### Типичные проблемы:

#### 🔒 "Требуется подписка" (APILayer)
**Решение**: Активируйте подписку на [APILayer Dashboard](https://apilayer.com/dashboard)

#### 🚫 "Неверный API ключ"
**Решение**: Проверьте `API_LAYER_KEY` в файле `.env`

#### ❌ "Курс не найден"
**Решение**: Убедитесь, что валютная пара поддерживается

#### ⏳ "Лимит запросов"
**Решение**: Подождите сброса лимита или увеличьте план

### Полезные команды:

```bash
# Проверка конфигурации
python -c "from src.config import config; print(config.API_LAYER_KEY)"

# Тест сетевых подключений
curl -H "apikey: your_api_key" \
  "https://api.apilayer.com/exchangerates_data/latest?base=USD&symbols=RUB"

# Включение debug логов
export LOG_LEVEL=DEBUG
```

## 📊 Статус разработки

- ✅ **Технологическая валидация** - завершена
- ✅ **APILayer интеграция** - завершена  
- ✅ **Rapira API интеграция** - завершена
- ✅ **Объединенный API сервис** - завершен
- ✅ **Система мониторинга** - завершена
- ✅ **Comprehensive тестирование** - завершено
- 🔄 **Telegram бот интерфейс** - в разработке
- ⏳ **Продакшн деплой** - планируется

## 🎯 Следующие этапы

1. **Завершение Telegram интерфейса**
2. **Интеграция с каналами**
3. **Добавление админ-панели**
4. **Docker контейнеризация**
5. **CI/CD настройка**

## 📞 Поддержка

Для вопросов по проекту:
- Проверьте [APILayer/README.md](APILayer/README.md)
- Запустите диагностику: `python APILayer/check_subscriptions.py`
- Проверьте статус APILayer: [https://status.apilayer.com/](https://status.apilayer.com/)

## 🏆 Преимущества

- **Профессиональная точность** курсов через APILayer
- **Высокая доступность** с fallback механизмами
- **Автоматическое переключение** между API
- **Comprehensive мониторинг** состояния
- **Готовность к продакшену** с первого дня