# 🚀 Keep Alive Service для Heroku Bot

## Проблема
Heroku Eco план автоматически усыпляет приложения после 30 минут неактивности.

## Решения

### 🔧 Решение 1: Локальный пинг-сервис (Рекомендуемый)

#### Установка
```bash
pip install -r keep_alive_requirements.txt
```

#### Запуск
```bash
python keep_alive_service.py
```

#### Что делает:
- Пингует бота каждые 25 минут
- Отправляет GET запрос на `/health/live`
- Выводит статус в консоль
- Работает 24/7 пока запущен

#### Преимущества:
- ✅ Бесплатно
- ✅ Надежно
- ✅ Простая настройка
- ✅ Полный контроль

#### Недостатки:
- ❌ Нужен запущенный компьютер/сервер
- ❌ Ручной запуск после перезагрузки

### 🌐 Решение 2: Внешние пинг-сервисы

#### UptimeRobot (Рекомендуемый внешний)
1. Зарегистрируйтесь на https://uptimerobot.com
2. Создайте новый монитор:
   - Type: HTTP(s)
   - URL: `https://crypto-helper-testing-7c5ffa6d9fbf.herokuapp.com/health/live`
   - Monitoring Interval: 5 minutes (максимум для бесплатного)
3. Сохраните

#### Ping-Estate
1. Зайдите на https://ping-estate.com
2. Добавьте URL: `https://crypto-helper-testing-7c5ffa6d9fbf.herokuapp.com/health/live`
3. Установите интервал: 25 минут

#### Freshping
1. Зарегистрируйтесь на https://www.freshworks.com/website-monitoring/
2. Добавьте проверку здоровья
3. URL: `https://crypto-helper-testing-7c5ffa6d9fbf.herokuapp.com/health/live`

### 💰 Решение 3: Обновление Heroku плана

#### Basic Plan ($7/месяц)
- Приложение никогда не засыпает
- Больше ресурсов
- SSL сертификаты

```bash
heroku ps:type basic -a crypto-helper-testing
```

## 🎯 Рекомендация

**Для начала:** Используйте локальный пинг-сервис (`keep_alive_service.py`)
**Для продакшена:** UptimeRobot + Basic план Heroku

## 📊 Мониторинг

Проверить статус бота:
```bash
heroku ps -a crypto-helper-testing
curl https://crypto-helper-testing-7c5ffa6d9fbf.herokuapp.com/health/live
```

## 🚨 Если бот уснул

Быстрое пробуждение:
```bash
heroku restart -a crypto-helper-testing
``` 