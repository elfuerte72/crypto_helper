# ⚡ Быстрая настройка Railway - ПАМЯТКА

## 🎯 Что уже сделано
✅ Railway CLI установлен  
✅ Проект `crypto-helper-bot` создан  
✅ Docker образ собран и развернут  

## 🚀 Что нужно сделать (3 минуты)

### 1. Подключиться к сервису
```bash
railway link
```
*Выберите: Maxim's Projects → crypto-helper-bot → crypto-helper-bot*

### 2. Установить переменные
```bash
# Базовые переменные (автоматически)
./setup_railway_vars.sh

# Ваши секретные ключи (вручную)
railway variables --set "BOT_TOKEN=ваш_токен"
railway variables --set "RAPIRA_API_KEY=ваш_ключ"
railway variables --set "API_LAYER_KEY=ваш_ключ"
```

### 3. Повторный деплой
```bash
railway up --detach
```

### 4. Проверить логи
```bash
railway logs --follow
```

## 🔗 Ссылки
- **Проект**: https://railway.com/project/7a17ef86-d503-484c-b691-5f2cbc5724b9
- **Документация**: [RAILWAY_DEPLOYMENT.md](./RAILWAY_DEPLOYMENT.md)

---
*После установки переменных бот будет работать автоматически!* 🤖 