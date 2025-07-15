# 🚀 Crypto Helper Bot - Railway Deployment

![Railway](https://img.shields.io/badge/Railway-0B0D0E?style=for-the-badge&logo=railway&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)

## 📋 Статус деплоя

| Компонент | Статус | Описание |
|-----------|--------|----------|
| 🛠️ Railway CLI | ✅ Установлен | Версия 4.5.4 |
| 📦 Проект | ✅ Создан | `crypto-helper-bot` |
| 🐳 Docker образ | ✅ Собран | Python 3.11-slim |
| 🔗 Первый деплой | ✅ Выполнен | Требуются переменные |
| ⚙️ Переменные | ⚠️ Частично | Нужны секретные ключи |

## 🎯 Быстрый старт

### Вариант 1: Автоматическая настройка (рекомендуется)
```bash
# 1. Подключиться к сервису
railway link

# 2. Запустить автонастройку
./setup_railway_vars.sh

# 3. Добавить секретные ключи
railway variables --set "BOT_TOKEN=ваш_токен"
railway variables --set "RAPIRA_API_KEY=ваш_ключ"
railway variables --set "API_LAYER_KEY=ваш_ключ"

# 4. Деплой
railway up --detach
```

### Вариант 2: Ручная настройка
```bash
railway link
railway variables --set "ENVIRONMENT=production"
railway variables --set "LOG_LEVEL=INFO"
railway variables --set "API_TIMEOUT=30"
railway variables --set "API_RETRY_COUNT=3"
railway variables --set "USE_MOCK_DATA=false"
railway variables --set "RAPIRA_API_URL=https://api.rapira.net/open/market/rates"
railway variables --set "API_LAYER_URL=https://api.apilayer.com/exchangerates_data"
# + добавить секретные ключи
railway up --detach
```

## 🔧 Управление

### Мониторинг
```bash
./check_deployment.sh     # Полная проверка статуса
railway logs --follow     # Логи в реальном времени
railway status            # Статус проекта
```

### Управление переменными
```bash
railway variables         # Показать все переменные
railway variables --kv    # В формате ключ=значение
railway variables --set "KEY=value"  # Установить переменную
```

### Деплой и управление
```bash
railway up                # Деплой с логами
railway up --detach       # Деплой без логов
railway open              # Открыть в браузере
railway service           # Переключить сервис
```

## 📁 Структура проекта

```
crypto_helpler/
├── 🐳 Dockerfile                 # Конфигурация контейнера
├── ⚙️ railway.json              # Настройки Railway
├── 📋 requirements.txt          # Python зависимости
├── 🔧 setup_railway_vars.sh     # Автонастройка переменных
├── 🔍 check_deployment.sh       # Проверка статуса
├── 📖 RAILWAY_DEPLOYMENT.md     # Подробная документация
├── ⚡ QUICK_RAILWAY_SETUP.md    # Быстрая памятка
└── src/                         # Исходный код бота
    ├── start_app.py            # Точка входа
    ├── main.py                 # Основная логика
    ├── config.py               # Конфигурация
    └── ...
```

## 🔐 Переменные окружения

### Обязательные
- `BOT_TOKEN` - Токен Telegram бота
- `RAPIRA_API_KEY` - Ключ API Rapira
- `API_LAYER_KEY` - Ключ API Layer

### Дополнительные (с умолчаниями)
- `ENVIRONMENT=production`
- `LOG_LEVEL=INFO`
- `API_TIMEOUT=30`
- `API_RETRY_COUNT=3`
- `USE_MOCK_DATA=false`
- `RAPIRA_API_URL=https://api.rapira.net/open/market/rates`
- `API_LAYER_URL=https://api.apilayer.com/exchangerates_data`

## 🔗 Ссылки

- **🌐 Ваш проект**: https://railway.com/project/7a17ef86-d503-484c-b691-5f2cbc5724b9
- **📚 Документация Railway**: https://docs.railway.app/
- **🤖 Telegram Bot API**: https://core.telegram.org/bots/api
- **💰 API Rapira**: https://api.rapira.net/
- **🌍 API Layer**: https://apilayer.com/

## 🆘 Устранение проблем

| Проблема | Решение |
|----------|---------|
| `No service linked` | `railway link` |
| Бот не отвечает | `railway logs` → проверить ошибки |
| `Configuration Error` | Установить переменные окружения |
| `TokenValidationError` | Проверить `BOT_TOKEN` |
| `API errors` | Проверить API ключи |

---

**Готово к работе!** 🎉 После установки переменных окружения ваш бот будет автоматически работать на Railway. 