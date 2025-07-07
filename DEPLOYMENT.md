# Docker & Heroku Deployment Guide

## Полноценный Docker контейнер готов! ✅

### Что было сделано:

1. **📦 Обновлен Dockerfile**
   - Оптимизирован для Heroku
   - Добавлены health checks
   - Поддержка переменной окружения PORT
   - Безопасность (non-root пользователь)

2. **🔧 Добавлена поддержка переменных окружения**
   - Создан `.env.example` с вашими переменными
   - Обновлен `health_check.py` для поддержки PORT
   - Добавлен `psutil` в requirements.txt

3. **🚀 Heroku готовность**
   - Создан `heroku.yml` для Container Registry
   - Создан `Procfile` 
   - Создан `deploy_heroku.sh` скрипт

4. **🐳 Docker Compose обновлен**
   - Добавлены все ваши переменные окружения
   - Настроен порт 8080
   - Обновлен health check

## Локальное тестирование

### 1. Создайте .env файл
```bash
cp .env.example .env
# Отредактируйте .env файл со своими токенами
```

### 2. Запустите через Docker Compose
```bash
# Запуск
make up
# или
docker-compose up --build

# Проверка здоровья
curl http://localhost:8080/health

# Логи
make logs
# или
docker-compose logs -f crypto-helper-bot
```

### 3. Остановка
```bash
make down
# или
docker-compose down
```

## Деплой на Heroku

### Шаг 1: Подготовка
```bash
# Установите Heroku CLI если нет
# https://devcenter.heroku.com/articles/heroku-cli

# Убедитесь что вы на ветке testing
git branch --show-current
```

### Шаг 2: Запуск деплоя
```bash
# Сделайте скрипт исполняемым
chmod +x deploy_heroku.sh

# Запустите деплой
./deploy_heroku.sh
```

### Шаг 3: Установка секретных переменных
```bash
# Установите ваши реальные токены
heroku config:set BOT_TOKEN=your_real_bot_token -a crypto-helper-testing
heroku config:set RAPIRA_API_KEY=your_real_api_key -a crypto-helper-testing  
heroku config:set API_LAYER_KEY=your_real_api_layer_key -a crypto-helper-testing
```

### Шаг 4: Проверка
```bash
# Проверка статуса
heroku ps -a crypto-helper-testing

# Логи
heroku logs --tail -a crypto-helper-testing

# Health check
curl https://crypto-helper-testing.herokuapp.com/health
```

## Альтернативный ручной деплой

Если автоматический скрипт не работает:

```bash
# 1. Логин в Heroku
heroku login
heroku container:login

# 2. Создание приложения
heroku apps:create crypto-helper-testing --region us
heroku stack:set container -a crypto-helper-testing

# 3. Переменные окружения
heroku config:set ENVIRONMENT=production -a crypto-helper-testing
heroku config:set LOG_LEVEL=INFO -a crypto-helper-testing
heroku config:set API_TIMEOUT=30 -a crypto-helper-testing
heroku config:set API_RETRY_COUNT=3 -a crypto-helper-testing
heroku config:set USE_MOCK_DATA=false -a crypto-helper-testing
heroku config:set RAPIRA_API_URL=https://api.rapira.net/open/market/rates -a crypto-helper-testing
heroku config:set API_LAYER_URL=https://api.apilayer.com/exchangerates_data -a crypto-helper-testing

# ВАЖНО: Установите секретные переменные
heroku config:set BOT_TOKEN=your_bot_token -a crypto-helper-testing
heroku config:set RAPIRA_API_KEY=your_api_key -a crypto-helper-testing
heroku config:set API_LAYER_KEY=your_api_layer_key -a crypto-helper-testing

# 4. Деплой
heroku container:push web -a crypto-helper-testing
heroku container:release web -a crypto-helper-testing
```

## Endpoints

После деплоя будут доступны:

- **Главная**: `https://crypto-helper-testing.herokuapp.com/`
- **Health Check**: `https://crypto-helper-testing.herokuapp.com/health`
- **Liveness**: `https://crypto-helper-testing.herokuapp.com/health/live`
- **Readiness**: `https://crypto-helper-testing.herokuapp.com/health/ready`
- **Metrics**: `https://crypto-helper-testing.herokuapp.com/metrics`

## Полезные команды

```bash
# Просмотр конфигурации
heroku config -a crypto-helper-testing

# Перезапуск
heroku restart -a crypto-helper-testing

# Изменение переменной
heroku config:set VARIABLE=value -a crypto-helper-testing

# Удаление приложения (если нужно)
heroku apps:destroy crypto-helper-testing
```

## Решение проблем

### Проблема: Контейнер не запускается
```bash
# Проверьте логи
heroku logs --tail -a crypto-helper-testing

# Проверьте переменные
heroku config -a crypto-helper-testing
```

### Проблема: Health check падает
```bash
# Проверьте что все переменные установлены
# Особенно BOT_TOKEN и API ключи
```

### Проблема: Бот не отвечает
```bash
# Проверьте что BOT_TOKEN правильный
# Проверьте что вебхук Telegram не установлен
```

---

🎉 **Ваш Docker контейнер и Heroku деплой готовы!**

Теперь можете запускать `./deploy_heroku.sh` для деплоя на Heroku или `make up` для локального тестирования. 