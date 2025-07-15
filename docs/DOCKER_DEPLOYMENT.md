# Docker Deployment Guide
## Crypto Helper Telegram Bot

Полное руководство по развертыванию Crypto Helper Bot с использованием Docker.

## 📋 Содержание
- [Быстрый старт](#быстрый-старт)
- [Требования](#требования)
- [Конфигурация](#конфигурация)
- [Развертывание](#развертывание)
- [Мониторинг](#мониторинг)
- [Обслуживание](#обслуживание)
- [Устранение неполадок](#устранение-неполадок)

## 🚀 Быстрый старт

### 1. Клонирование проекта
```bash
git clone <repository-url>
cd crypto_helpler
```

### 2. Настройка окружения
```bash
# Копируем шаблон конфигурации
cp .env.example .env

# Редактируем конфигурацию
nano .env
```

### 3. Запуск для разработки
```bash
# Сборка и запуск в режиме разработки
make dev-build
make dev-up

# Просмотр логов
make dev-logs
```

### 4. Запуск в продакшене
```bash
# Сборка и запуск в продакшене
make prod-build
make prod-up

# Проверка статуса
make prod-health
```

## 📦 Требования

### Системные требования
- **Docker**: 20.10.0+
- **Docker Compose**: 2.0.0+
- **RAM**: минимум 512MB, рекомендуется 1GB
- **CPU**: минимум 1 ядро, рекомендуется 2 ядра
- **Диск**: минимум 2GB свободного места

### Сетевые требования
- Доступ к интернету для API вызовов
- Доступ к Telegram API (api.telegram.org)
- Доступ к Rapira API
- Порт 8080 для health checks (опционально)

## ⚙️ Конфигурация

### Основные переменные окружения
```bash
# Обязательные
BOT_TOKEN=your_bot_token_here
RAPIRA_API_KEY=your_rapira_api_key_here

# Опциональные
LOG_LEVEL=INFO
API_TIMEOUT=30
API_RETRY_COUNT=3
```

### Файл .env
Скопируйте `.env.example` в `.env` и заполните все необходимые значения:

```bash
cp .env.example .env
```

**Важные переменные:**
- `BOT_TOKEN` - токен Telegram бота от @BotFather
- `RAPIRA_API_KEY` - ключ API от Rapira сервиса
- `LOG_LEVEL` - уровень логирования (DEBUG, INFO, WARNING, ERROR)

## 🐳 Развертывание

### Режим разработки

#### Сборка образа
```bash
# Автоматическая сборка
make dev-build

# Ручная сборка
docker build -f Dockerfile.dev -t crypto-helper-bot:dev .
```

#### Запуск сервисов
```bash
# Запуск основного бота
make dev-up

# Запуск с дополнительными сервисами
docker-compose -f docker-compose.dev.yml --profile redis --profile database up -d
```

#### Полезные команды
```bash
# Просмотр логов
make dev-logs

# Доступ к контейнеру
make dev-shell

# Запуск тестов
make dev-test

# Перезапуск
make dev-restart
```

### Режим продакшена

#### Сборка образа
```bash
# Автоматическая сборка
make prod-build

# Ручная сборка с тегом
docker build -t crypto-helper-bot:v1.0.0 .
```

#### Запуск сервисов
```bash
# Запуск основного бота
make prod-up

# Запуск с дополнительными сервисами
docker-compose --profile redis --profile database up -d
```

#### Проверка состояния
```bash
# Проверка здоровья
make prod-health

# Просмотр логов
make prod-logs

# Мониторинг ресурсов
make monitor
```

## 🔧 Архитектура контейнеров

### Основные сервисы

#### crypto-helper-bot
- **Образ**: `crypto-helper-bot:latest`
- **Порты**: 8080 (health check)
- **Volumes**: 
  - `./logs:/app/logs`
  - `./tmp:/app/tmp`
- **Ресурсы**: 
  - CPU: 0.5 cores limit
  - Memory: 512MB limit

#### redis (опционально)
- **Образ**: `redis:7-alpine`
- **Порты**: 6379
- **Использование**: кеширование, сессии
- **Профиль**: `redis`

#### postgres (опционально)
- **Образ**: `postgres:15-alpine`
- **Порты**: 5432
- **Использование**: база данных
- **Профиль**: `database`

### Сеть
- **Сеть**: `crypto-helper-network`
- **Драйвер**: bridge
- **Изоляция**: контейнеры изолированы от хоста

## 📊 Мониторинг

### Health Check Endpoints
```bash
# Общее состояние здоровья
curl http://localhost:8080/health

# Проверка жизнеспособности
curl http://localhost:8080/health/live

# Проверка готовности
curl http://localhost:8080/health/ready

# Метрики
curl http://localhost:8080/metrics
```

### Логи
```bash
# Просмотр логов в реальном времени
docker-compose logs -f crypto-helper-bot

# Логи за последние 100 строк
docker-compose logs --tail 100 crypto-helper-bot

# Логи с определенного времени
docker-compose logs --since "2024-01-01T00:00:00" crypto-helper-bot
```

### Мониторинг ресурсов
```bash
# Статистика контейнеров
docker stats

# Использование дискового пространства
docker system df

# Информация о контейнере
docker inspect crypto-helper-bot
```

## 🔧 Обслуживание

### Обновление приложения
```bash
# Остановка сервисов
make prod-down

# Сборка новой версии
make prod-build

# Запуск обновленной версии
make prod-up
```

### Бэкапы
```bash
# Создание бэкапа базы данных
make backup

# Восстановление из бэкапа
make restore BACKUP_FILE=postgres_backup_20240101_120000.tar.gz
```

### Очистка
```bash
# Удаление остановленных контейнеров
make clean

# Полная очистка (осторожно!)
make clean-all
```

### Обновление зависимостей
```bash
# Обновление образов
make update

# Пересборка с обновлениями
make prod-build --no-cache
```

## 🚨 Устранение неполадок

### Общие проблемы

#### Контейнер не запускается
```bash
# Проверка логов
docker-compose logs crypto-helper-bot

# Проверка конфигурации
docker-compose config

# Проверка переменных окружения
docker-compose exec crypto-helper-bot env
```

#### Проблемы с API
```bash
# Проверка connectivity
docker-compose exec crypto-helper-bot curl -v https://api.rapira.net/open/market/rates

# Проверка DNS
docker-compose exec crypto-helper-bot nslookup api.rapira.net
```

#### Проблемы с памятью
```bash
# Мониторинг использования памяти
docker stats --no-stream crypto-helper-bot

# Увеличение лимита памяти в docker-compose.yml
deploy:
  resources:
    limits:
      memory: 1024M
```

### Диагностика

#### Проверка состояния
```bash
# Статус всех сервисов
docker-compose ps

# Детальная информация о контейнере
docker inspect crypto-helper-bot

# Проверка health check
curl http://localhost:8080/health
```

#### Отладка
```bash
# Доступ к shell контейнера
docker-compose exec crypto-helper-bot bash

# Запуск в интерактивном режиме
docker run -it --rm crypto-helper-bot:latest bash

# Проверка файловой системы
docker-compose exec crypto-helper-bot ls -la /app/
```

### Логирование

#### Настройка уровня логов
```bash
# В .env файле
LOG_LEVEL=DEBUG

# Перезапуск для применения изменений
make prod-restart
```

#### Сохранение логов
```bash
# Экспорт логов в файл
docker-compose logs crypto-helper-bot > bot_logs.txt

# Сжатие логов
docker-compose logs crypto-helper-bot | gzip > bot_logs.gz
```

## 📞 Поддержка

### Контакты
- **GitHub Issues**: для багов и запросов функций
- **Email**: для критических проблем
- **Документация**: `/docs` директория

### Полезные ссылки
- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/)
- [Aiogram Documentation](https://docs.aiogram.dev/)

---

## 📝 Примечания

### Версионирование
- Используйте семантическое версионирование (v1.0.0)
- Тегируйте Docker образы соответствующими версиями
- Ведите changelog для отслеживания изменений

### Безопасность
- Не включайте `.env` файлы в git
- Используйте Docker secrets для продакшена
- Регулярно обновляйте базовые образы
- Запускайте контейнеры от непривилегированного пользователя

### Производительность
- Используйте multi-stage builds для уменьшения размера образов
- Настройте resource limits для контейнеров
- Мониторьте использование ресурсов в продакшене
- Используйте volumes для persistent data