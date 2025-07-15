#!/bin/bash

# 🔍 Скрипт проверки статуса деплоя Railway

echo "🔍 Проверка статуса деплоя Crypto Helper Bot на Railway"
echo "=================================================="

# Проверка статуса проекта
echo "📊 Статус проекта:"
railway status
echo ""

# Проверка переменных окружения
echo "🔧 Переменные окружения:"
railway variables --kv
echo ""

# Проверка логов (последние 50 строк)
echo "📝 Последние логи (50 строк):"
railway logs --lines 50
echo ""

echo "✅ Проверка завершена!"
echo ""
echo "💡 Полезные команды:"
echo "   railway logs --follow    # Логи в реальном времени"
echo "   railway open            # Открыть в браузере"
echo "   railway up              # Повторный деплой" 