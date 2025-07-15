#!/bin/bash

# Crypto Helper Bot - Simple Start Script
# One-click start for development and production

echo "🚀 Запуск Crypto Helper Bot..."
echo "================================"

# Проверка Docker
echo "1. Проверка Docker..."
if ! docker --version > /dev/null 2>&1; then
    echo "❌ Docker не найден или не запущен"
    echo "Запустите Docker Desktop и повторите попытку"
    exit 1
fi
echo "✅ Docker работает"

# Проверка файлов
echo "2. Проверка файлов проекта..."
if [ ! -f "Dockerfile" ]; then
    echo "❌ Dockerfile не найден"
    exit 1
fi
echo "✅ Файлы проекта найдены"

# Проверка .env
echo "3. Проверка конфигурации..."
if [ ! -f ".env" ]; then
    echo "⚠️ .env файл не найден, создаем из примера..."
    cp .env.example .env
    echo "📝 ВАЖНО: Отредактируйте .env файл:"
    echo "   - BOT_TOKEN=your_bot_token_here"
    echo "   - RAPIRA_API_KEY=your_rapira_api_key_here"
    echo ""
    echo "Затем запустите скрипт снова: ./start.sh"
    exit 1
fi

# Проверка токенов
if grep -q "your_bot_token_here" .env || grep -q "your_rapira_api_key_here" .env; then
    echo "⚠️ Обнаружены примеры токенов в .env файле"
    echo "📝 Пожалуйста, укажите реальные токены:"
    echo "   - BOT_TOKEN=your_real_bot_token"
    echo "   - RAPIRA_API_KEY=your_real_api_key"
    exit 1
fi
echo "✅ Конфигурация готова"

# Сборка
echo "4. Сборка образа..."
if docker-compose build; then
    echo "✅ Образ собран успешно"
else
    echo "❌ Ошибка сборки образа"
    exit 1
fi

# Запуск
echo "5. Запуск бота..."
if docker-compose up -d; then
    echo "✅ Бот запущен"
else
    echo "❌ Ошибка запуска бота"
    exit 1
fi

# Проверка статуса
echo "6. Проверка статуса..."
sleep 5
docker-compose ps

echo ""
echo "🎉 Бот успешно запущен!"
echo "================================"
echo "Полезные команды:"
echo "make logs     # Просмотр логов"
echo "make down     # Остановка"
echo "make restart  # Перезапуск"
echo "make status   # Статус"
echo ""
echo "Логи бота:"
docker-compose logs --tail 10 crypto-helper-bot