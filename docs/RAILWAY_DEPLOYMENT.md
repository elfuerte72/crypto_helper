# 🚀 Деплой Crypto Helper Bot на Railway

## 📋 Требования

1. **Railway CLI** ✅ (установлен)
2. **Docker** ✅ (проект упакован)
3. **Переменные окружения** (нужно настроить)

## 🔐 Обязательные переменные окружения для Railway

После создания проекта установите следующие переменные через Railway Dashboard или CLI:

### Основные переменные:
```bash
BOT_TOKEN=your_telegram_bot_token_here
RAPIRA_API_KEY=your_rapira_api_key_here
API_LAYER_KEY=your_api_layer_key_here
```

### Дополнительные настройки:
```bash
RAPIRA_API_URL=https://api.rapira.net/open/market/rates
API_LAYER_URL=https://api.apilayer.com/exchangerates_data
LOG_LEVEL=INFO
API_TIMEOUT=30
API_RETRY_COUNT=3
USE_MOCK_DATA=false
ENVIRONMENT=production
```

**⚠️ Важно:** PORT будет автоматически задан Railway. Не устанавливайте его вручную!

## 🚀 Команды для деплоя

```bash
# 1. Инициализация проекта ✅ (выполнено)
railway init -n crypto-helper-bot

# 2. Подключение к сервису
railway link
# Выберите: Maxim's Projects -> crypto-helper-bot -> crypto-helper-bot

# 3. Быстрая настройка базовых переменных
./setup_railway_vars.sh

# 4. Установка секретных ключей (ОБЯЗАТЕЛЬНО!)
railway variables --set "BOT_TOKEN=ваш_telegram_bot_token"
railway variables --set "RAPIRA_API_KEY=ваш_rapira_api_key"  
railway variables --set "API_LAYER_KEY=ваш_api_layer_key"

# 5. Повторный деплой с переменными
railway up --detach

# 6. Просмотр логов
railway logs --follow

# 7. Открыть в браузере
railway open
```

## 🔧 Конфигурация

Проект использует:
- **Dockerfile** для сборки
- **railway.json** для конфигурации
- **Переменные окружения** для настроек

## 📱 Особенности деплоя

1. **Порт**: Railway автоматически назначает PORT
2. **Health check**: Встроенная проверка здоровья на `/health/live`
3. **Логирование**: Настроено через LOG_LEVEL
4. **Безопасность**: Работа от non-root пользователя

## 📊 Текущий статус

✅ **Выполнено:**
- Railway CLI установлен
- Проект `crypto-helper-bot` создан  
- Docker образ собран и развернут
- railway.json конфигурация создана

⏳ **Нужно выполнить:**
1. Подключиться к сервису: `railway link`
2. Установить секретные ключи (BOT_TOKEN, API ключи)
3. Перезапустить деплой: `railway up --detach`

## 🆘 Помощь

**Основные команды:**
```bash
railway status              # Проверить статус
railway logs --follow       # Логи в реальном времени  
railway open                # Открыть в браузере
railway variables           # Посмотреть переменные
```

**Ссылки:**
- 📚 Документация Railway: https://docs.railway.app/
- 🌐 Ваш проект: https://railway.com/project/7a17ef86-d503-484c-b691-5f2cbc5724b9
- 🤖 Telegram Bot API: https://core.telegram.org/bots/api

## 📊 Текущий статус деплоя

✅ **Railway CLI установлен** (версия 4.5.4)  
✅ **Проект создан**: `crypto-helper-bot`  
✅ **Dockerfile готов** для Railway  
✅ **Первый деплой выполнен** (образ собран)  
⚠️ **Требуется**: установка переменных окружения и повторный деплой

## 🔄 Следующие шаги для завершения

1. **Подключитесь к сервису:**
   ```bash
   railway link
   # Выберите: Maxim's Projects -> crypto-helper-bot -> crypto-helper-bot
   ```

2. **Быстро установите базовые переменные:**
   ```bash
   ./setup_railway_vars.sh
   ```

3. **Добавьте секретные ключи:**
   ```bash
   railway variables --set "BOT_TOKEN=ваш_реальный_токен_бота"
   railway variables --set "RAPIRA_API_KEY=ваш_ключ_rapira"
   railway variables --set "API_LAYER_KEY=ваш_ключ_apilayer"
   ```

4. **Повторно разверните:**
   ```bash
   railway up --detach
   ```

**Устранение проблем:**
- Если `No service linked`: выполните `railway link`
- Если бот не отвечает: проверьте `railway logs`
- Если ошибки API: проверьте ключи в переменных окружения 