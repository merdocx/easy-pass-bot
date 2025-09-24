# 🤖 Настройка двух ботов Easy Pass Bot

## 📋 Обзор

Проект разделен на два отдельных бота:

1. **Бот для жителей** (`7961301390:AAFz7gE__kiwT_B8GPleVvrsf-qxqXbd8X4`)
   - Регистрация жителей
   - Подача заявок на пропуски
   - Просмотр своих заявок
   - Отмена заявок

2. **Бот для охраны и админов** (`8069990519:AAHySjIKHlSgVcJpLaXlExZ5Se0juiKX4GQ`)
   - Поиск пропусков по номеру автомобиля
   - Отметка использования пропусков
   - Модерация заявок на регистрацию
   - Управление пользователями

## 🚀 Запуск ботов

### Вариант 1: Запуск по отдельности

**Бот для жителей:**
```bash
cd /root/easy-pass-bot
source venv/bin/activate
python start_resident_bot.py
```

**Бот для охраны и админов:**
```bash
cd /root/easy-pass-bot
source venv/bin/activate
python start_security_bot.py
```

### Вариант 2: Запуск обоих ботов одновременно

```bash
cd /root/easy-pass-bot
source venv/bin/activate
python start_both_bots.py
```

### Вариант 3: Запуск через systemd (рекомендуется для продакшена)

Создайте два сервиса:

**`/etc/systemd/system/easy-pass-resident-bot.service`:**
```ini
[Unit]
Description=Easy Pass Resident Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/easy-pass-bot
Environment=PATH=/root/easy-pass-bot/venv/bin
ExecStart=/root/easy-pass-bot/venv/bin/python start_resident_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**`/etc/systemd/system/easy-pass-security-bot.service`:**
```ini
[Unit]
Description=Easy Pass Security Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/easy-pass-bot
Environment=PATH=/root/easy-pass-bot/venv/bin
ExecStart=/root/easy-pass-bot/venv/bin/python start_security_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Команды управления:**
```bash
# Запуск
sudo systemctl start easy-pass-resident-bot
sudo systemctl start easy-pass-security-bot

# Остановка
sudo systemctl stop easy-pass-resident-bot
sudo systemctl stop easy-pass-security-bot

# Статус
sudo systemctl status easy-pass-resident-bot
sudo systemctl status easy-pass-security-bot

# Логи
sudo journalctl -u easy-pass-resident-bot -f
sudo journalctl -u easy-pass-security-bot -f
```

## 📁 Структура проекта

```
easy-pass-bot/
├── bots/
│   ├── config.py                    # Общая конфигурация
│   ├── resident_bot/                # Бот для жителей
│   │   ├── main.py                 # Точка входа
│   │   └── handlers.py             # Обработчики
│   └── security_bot/               # Бот для охраны и админов
│       ├── main.py                 # Точка входа
│       ├── handlers.py             # Обработчики охраны
│       └── admin_handlers.py       # Обработчики админов
├── src/easy_pass_bot/              # Общий код (база данных, сервисы)
├── start_resident_bot.py           # Скрипт запуска бота жителей
├── start_security_bot.py           # Скрипт запуска бота охраны
├── start_both_bots.py              # Скрипт запуска обоих ботов
└── database/                       # База данных SQLite
```

## 🔧 Конфигурация

Токены ботов настроены в файле `bots/config.py`:

```python
RESIDENT_BOT_TOKEN = "7961301390:AAFz7gE__kiwT_B8GPleVvrsf-qxqXbd8X4"
SECURITY_BOT_TOKEN = "8069990519:AAHySjIKHlSgVcJpLaXlExZ5Se0juiKX4GQ"
```

## 🎯 Функционал по ботам

### Бот для жителей (7961301390)
- ✅ Регистрация в системе
- ✅ Подача заявок на пропуски
- ✅ Просмотр своих заявок
- ✅ Отмена неиспользованных заявок
- ✅ Статус модерации

### Бот для охраны и админов (8069990519)
- ✅ Поиск пропусков по номеру автомобиля
- ✅ Отметка использования пропусков
- ✅ Просмотр списка активных пропусков
- ✅ Модерация заявок на регистрацию
- ✅ Управление пользователями (блокировка/разблокировка)
- ✅ Административные функции

## 🧪 Тестирование

**Тест бота жителей:**
```bash
cd /root/easy-pass-bot
source venv/bin/activate
timeout 10s python start_resident_bot.py
```

**Тест бота охраны:**
```bash
cd /root/easy-pass-bot
source venv/bin/activate
timeout 10s python start_security_bot.py
```

## 📊 Мониторинг

- **Логи**: Каждый бот ведет свои логи
- **База данных**: Общая для обоих ботов
- **Метрики**: Встроенная система сбора метрик
- **Здоровье**: Health check endpoints

## 🔒 Безопасность

- ✅ Разделение ролей между ботами
- ✅ Валидация входных данных
- ✅ Rate limiting
- ✅ Аудит действий
- ✅ Защита от SQL инъекций

## 📞 Поддержка

- **GitHub**: https://github.com/merdocx/easy-pass-bot
- **Документация**: `docs/` директория
- **Логи**: `logs/` директория (создается автоматически)

---
**Два бота успешно настроены и готовы к работе! 🎉**



