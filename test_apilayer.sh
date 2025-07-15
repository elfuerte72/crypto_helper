#!/bin/bash
# Скрипт для быстрого запуска тестов APILayer

echo "🧪 APILayer Test Runner"
echo "======================"
echo ""

case "${1:-help}" in
    "quick")
        echo "🚀 Запуск быстрой проверки APILayer..."
        python APILayer/quick_test.py
        ;;
    "demo")
        echo "🎯 Запуск полной демонстрации..."
        python APILayer/demo.py
        ;;
    "full")
        echo "🔬 Запуск полного тестирования..."
        python APILayer/test_apilayer_full.py
        ;;
    "subs"|"subscriptions")
        echo "📋 Проверка подписок APILayer..."
        python APILayer/check_subscriptions.py
        ;;
    "help"|*)
        echo "Использование: $0 [команда]"
        echo ""
        echo "Доступные команды:"
        echo "  quick        - Быстрая проверка (30 сек)"
        echo "  demo         - Полная демонстрация (2-3 мин)"
        echo "  full         - Полное тестирование (3-5 мин)"
        echo "  subs         - Проверка подписок APILayer"
        echo "  help         - Показать эту справку"
        echo ""
        echo "Примеры:"
        echo "  $0 quick     # Быстрый тест"
        echo "  $0 demo      # Демонстрация"
        echo "  $0 full      # Полное тестирование"
        ;;
esac