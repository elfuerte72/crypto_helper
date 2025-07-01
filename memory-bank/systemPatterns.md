# SYSTEM PATTERNS - Crypto Helper Telegram Bot

## Архитектурные паттерны

### Минималистичная архитектура MVP
- **Основное приложение**: Python скрипт с Telegram ботом
- **Telegram Bot API**: Aiogram 3.x фреймворк
- **HTTP клиент**: aiohttp для запросов к Rapira API
- **Конфигурация**: .env файл с python-dotenv
- **Хранилище**: Не требуется (без сохранения истории)
- **Внешние API**: Rapira API для получения курсов

### Паттерны проектирования для MVP
- **Handler Pattern**: Обработчики команд и callback'ов
- **State Machine Pattern**: FSM (Finite State Machine) для управления диалогом
- **Strategy Pattern**: Различные стратегии для валютных пар
- **Template Method Pattern**: Общий шаблон для обработки всех валютных пар
- **Decorator Pattern**: Проверка прав администратора

### Технологические решения (Определено)
- **Язык**: Python 3.11
- **Bot Framework**: Aiogram 3.x
- **HTTP Client**: aiohttp
- **Конфигурация**: python-dotenv
- **Управление состоянием**: aiogram FSM
- **API клиент**: aiohttp.ClientSession
- **Обработка ошибок**: try/except с retry логикой

### Ключевые компоненты системы

#### 1. Bot Handler Layer
- **Командные обработчики**: /admin_bot
- **Callback обработчики**: Выбор валютных пар
- **Message обработчики**: Обработка ввода наценки
- **Мидлвары**: Проверка прав администратора

#### 2. State Management Layer
- **FSM States**: Состояния диалога (выбор пары, ввод наценки)
- **State Transitions**: Переходы между состояниями
- **State Data**: Хранение временных данных диалога

#### 3. API Integration Layer
- **Rapira API Client**: HTTP клиент для получения курсов
- **Rate Limiting**: Ограничение частоты запросов
- **Error Handling**: Обработка ошибок API
- **Retry Logic**: Повторные попытки при ошибках

#### 4. Business Logic Layer
- **Currency Pair Handler**: Обработка различных валютных пар
- **Markup Calculator**: Расчет курса с наценкой
- **Message Formatter**: Форматирование сообщений для канала
- **Validation Logic**: Проверка корректности ввода

### Поддерживаемые валютные пары
```python
SUPPORTED_PAIRS = {
    # RUB направления
    'RUB_ZAR': 'RUB/ZAR',
    'ZAR_RUB': 'ZAR/RUB',
    'RUB_THB': 'RUB/THB',
    'THB_RUB': 'THB/RUB',
    'RUB_AED': 'RUB/AED',
    'AED_RUB': 'AED/RUB',
    'RUB_IDR': 'RUB/IDR',
    'IDR_RUB': 'IDR/RUB',
    
    # USDT направления
    'USDT_ZAR': 'USDT/ZAR',
    'ZAR_USDT': 'ZAR/USDT',
    'USDT_THB': 'USDT/THB',
    'THB_USDT': 'THB/USDT',
    'USDT_AED': 'USDT/AED',
    'AED_USDT': 'AED/USDT',
    'USDT_IDR': 'USDT/IDR',
    'IDR_USDT': 'IDR/USDT'
}
```

### Интеграции
- **Telegram Bot API**: Основное взаимодействие с пользователями
- **Rapira API**: Получение актуальных курсов криптовалют
- **Канал Telegram**: Публикация результатов

### Ограничения архитектуры MVP
- **Нет базы данных**: Все данные временные, в памяти
- **Нет логирования**: Минимальное логирование только ошибок
- **Нет масштабирования**: Один процесс, один бот
- **Нет мониторинга**: Нет метрик и мониторинга
- **Нет аутентификации**: Простая проверка прав админа

### Принципы разработки MVP
- **KISS (Keep It Simple, Stupid)**: Максимальная простота
- **YAGNI (You Aren't Gonna Need It)**: Не реализовывать лишний функционал
- **DRY (Don't Repeat Yourself)**: Избегать дублирования кода
- **Fail Fast**: Быстро обнаруживать и обрабатывать ошибки
- **Single Responsibility**: Каждый компонент отвечает за одну задачу