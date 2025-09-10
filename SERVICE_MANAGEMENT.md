# Управление сервисом Easy Pass Bot

## 🚀 Автозапуск настроен!

Бот Easy Pass теперь работает как системный сервис и автоматически запускается при перезагрузке сервера.

## 📋 Команды управления

### Использование скрипта управления:
```bash
cd /root/easy_pass_bot
./manage_bot.sh [команда]
```

### Доступные команды:

#### 🚀 **Запуск бота**
```bash
./manage_bot.sh start
```

#### ⏹️ **Остановка бота**
```bash
./manage_bot.sh stop
```

#### 🔄 **Перезапуск бота**
```bash
./manage_bot.sh restart
```

#### 📊 **Статус бота**
```bash
./manage_bot.sh status
```

#### 📋 **Просмотр логов в реальном времени**
```bash
./manage_bot.sh logs
```

#### ✅ **Включить автозапуск**
```bash
./manage_bot.sh enable
```

#### ❌ **Отключить автозапуск**
```bash
./manage_bot.sh disable
```

## 🔧 Прямые команды systemd

### Запуск/остановка:
```bash
systemctl start easy-pass-bot.service
systemctl stop easy-pass-bot.service
systemctl restart easy-pass-bot.service
```

### Статус и логи:
```bash
systemctl status easy-pass-bot.service
journalctl -u easy-pass-bot.service -f
```

### Автозапуск:
```bash
systemctl enable easy-pass-bot.service
systemctl disable easy-pass-bot.service
```

## 📊 Текущий статус

- ✅ **Сервис создан:** `/etc/systemd/system/easy-pass-bot.service`
- ✅ **Автозапуск включен:** бот запускается при перезагрузке
- ✅ **Автоперезапуск:** бот перезапускается при сбоях
- ✅ **Логирование:** все логи сохраняются в systemd journal

## 🔍 Мониторинг

### Проверка работы:
```bash
# Статус сервиса
systemctl status easy-pass-bot.service

# Последние логи
journalctl -u easy-pass-bot.service --since "1 hour ago"

# Логи в реальном времени
journalctl -u easy-pass-bot.service -f
```

### Проверка процессов:
```bash
ps aux | grep python
```

## 🛠️ Устранение проблем

### Если бот не запускается:
1. Проверьте логи: `journalctl -u easy-pass-bot.service`
2. Проверьте права доступа к файлам
3. Убедитесь, что виртуальное окружение создано
4. Проверьте токен бота в `.env`

### Если нужно обновить код:
1. Остановите бота: `./manage_bot.sh stop`
2. Обновите код
3. Запустите бота: `./manage_bot.sh start`

## 📁 Файлы сервиса

- **Конфигурация:** `/etc/systemd/system/easy-pass-bot.service`
- **Скрипт управления:** `/root/easy_pass_bot/manage_bot.sh`
- **Логи:** `journalctl -u easy-pass-bot.service`

## ✅ Готово!

Бот теперь работает как полноценный системный сервис с автозапуском и мониторингом.






