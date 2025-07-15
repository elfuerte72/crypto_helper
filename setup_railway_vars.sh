#!/bin/bash

# 🔧 Скрипт настройки переменных окружения для Railway
# Запустите после подключения к сервису: railway link

echo "🚀 Настройка переменных окружения для Railway..."

# Базовые настройки
echo "📝 Устанавливаю базовые переменные..."
railway variables --set "ENVIRONMENT=production"
railway variables --set "LOG_LEVEL=INFO"
railway variables --set "API_TIMEOUT=30"
railway variables --set "API_RETRY_COUNT=3"
railway variables --set "USE_MOCK_DATA=false"

# API URL (значения по умолчанию)
echo "🌐 Устанавливаю API endpoints..."
railway variables --set "RAPIRA_API_URL=https://api.rapira.net/open/market/rates"
railway variables --set "API_LAYER_URL=https://api.apilayer.com/exchangerates_data"

echo "✅ Базовые переменные установлены!"
echo ""
echo "⚠️  ВНИМАНИЕ: Необходимо установить секретные ключи:"
echo "   railway variables --set 'BOT_TOKEN=ваш_telegram_bot_token'"
echo "   railway variables --set 'RAPIRA_API_KEY=ваш_rapira_api_key'"
echo "   railway variables --set 'API_LAYER_KEY=ваш_api_layer_key'"
echo ""
echo "После установки ключей запустите деплой:"
echo "   railway up --detach" 