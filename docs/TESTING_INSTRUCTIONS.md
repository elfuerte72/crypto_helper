# 🧪 Инструкция по тестированию APILayer интеграции

## Обзор

После подписки на APILayer сервисы, необходимо проверить корректность работы интеграции. Для этого созданы несколько тестовых скриптов.

## Ваши подписки APILayer

✅ **Exchange Rates Data API** - `ia4vDqQbnoqcYeKvYTXNdALCW24nsO1E`
✅ **Currency Data API** - `ia4vDqQbnoqcYeKvYTXNdALCW24nsO1E`

## 🚀 Быстрый старт

### 1. Быстрая проверка (30 секунд)
```bash
cd /Users/maximpenkin/Documents/crypto_helpler
python quick_test.py
```

Этот тест проверит:
- Доступность Exchange Rates Data API
- Доступность Currency Data API
- Работу интегрированного сервиса

### 2. Проверка статуса подписок (1 минута)
```bash
python check_subscriptions.py
```

Этот тест покажет:
- Какие endpoint'ы доступны
- Статус ваших подписок
- Лимиты запросов
- Детальную информацию о доступе

### 3. Полное тестирование (3-5 минут)
```bash
python test_apilayer_full.py
```

Комплексное тестирование:
- Все endpoint'ы Exchange Rates Data API
- Все endpoint'ы Currency Data API  
- Интегрированный fiat_rates_service
- Объединенный API сервис
- Автоматическое переключение между API

### 4. Базовое тестирование (1 минута)
```bash
python test_apilayer.py
```

Проверка основных функций:
- Health check APILayer
- Получение курсов валют
- Создание ExchangeRate объектов

### 5. Автоматический запуск всех тестов
```bash
python run_tests.py
```

## 📊 Интерпретация результатов

### ✅ Успешные результаты
- **Status: healthy** - API работает корректно
- **✅ USD/RUB: 75.123456** - Курс получен успешно
- **✅ Работает! Получено X курсов** - Данные получены

### ❌ Проблемы и их решения

#### 🔒 "Требуется подписка"
**Проблема**: API endpoint недоступен
**Решение**: 
1. Перейдите на [APILayer Dashboard](https://apilayer.com/dashboard)
2. Убедитесь, что подписка активна
3. Проверьте лимиты запросов

#### 🚫 "Неверный API ключ"
**Проблема**: Ключ не найден или неверен
**Решение**:
1. Проверьте файл `.env`
2. Убедитесь, что `API_LAYER_KEY=ia4vDqQbnoqcYeKvYTXNdALCW24nsO1E`
3. Перезапустите тест

#### ❌ "HTTP 403"
**Проблема**: Доступ запрещен
**Решение**:
1. Проверьте статус подписки на APILayer
2. Убедитесь, что подписались на правильные API:
   - Exchange Rates Data API
   - Currency Data API

#### ⏳ "Лимит запросов достигнут"
**Проблема**: Превышен лимит запросов
**Решение**:
1. Подождите сброса лимита (обычно ежедневно)
2. Проверьте лимиты на APILayer Dashboard

## 🎯 Что должно работать

### Фиатные валюты (через APILayer)
- USD/RUB, EUR/RUB, USD/ZAR, USD/THB
- USD/AED, USD/IDR, EUR/ZAR
- Кросс-курсы: RUB/ZAR, RUB/THB, RUB/AED, RUB/IDR

### Криптовалюты (через Rapira API)
- BTC/USDT, ETH/USDT, TON/USDT, USDT/RUB
- BTC/RUB, ETH/RUB, TON/RUB (через расчет)

### Объединенный сервис
- Автоматическое определение типа пары
- Переключение между Rapira и APILayer
- Unified health check

## 🔧 Структура тестов

```
crypto_helpler/
├── quick_test.py              # Быстрая проверка
├── check_subscriptions.py     # Статус подписок
├── test_apilayer.py          # Базовые тесты
├── test_apilayer_full.py     # Полное тестирование
├── run_tests.py              # Автоматический запуск
└── TESTING_INSTRUCTIONS.md   # Эта инструкция
```

## 🐛 Отладка

### Включение подробных логов
Отредактируйте `.env` файл:
```
LOG_LEVEL=DEBUG
```

### Проверка сетевых подключений
```bash
curl -H "apikey: ia4vDqQbnoqcYeKvYTXNdALCW24nsO1E" \
  "https://api.apilayer.com/exchangerates_data/latest?base=USD&symbols=RUB"
```

### Проверка переменных окружения
```bash
python -c "from src.config import config; print(f'API_LAYER_KEY: {config.API_LAYER_KEY}')"
```

## 📞 Поддержка

При возникновении проблем:

1. **Проверьте статус APILayer**: [https://status.apilayer.com/](https://status.apilayer.com/)
2. **Проверьте лимиты**: [APILayer Dashboard](https://apilayer.com/dashboard)
3. **Запустите диагностику**: `python check_subscriptions.py`

## 🏆 Ожидаемые результаты

После успешного тестирования вы должны увидеть:

```
🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! APILayer интеграция работает корректно!

📋 Что работает:
• Exchange Rates Data API - получение курсов валют
• Currency Data API - дополнительные данные о валютах
• Автоматическое переключение между Rapira (крипто) и APILayer (фиат)
• Расчет кросс-курсов
• Обработка ошибок и fallback механизмы
• Health check для мониторинга
```

Это означает, что ваша интеграция работает корректно и готова к использованию в продакшене!