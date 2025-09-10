# Easy Pass Bot

> Современный Telegram-бот для управления пропусками в жилом комплексе

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![aiogram](https://img.shields.io/badge/aiogram-3.13.1-green.svg)](https://docs.aiogram.dev)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-100%2B-brightgreen.svg)](tests/)
[![Coverage](https://img.shields.io/badge/Coverage-85%25-success.svg)](tests/)

## 🚀 Возможности

### 👥 Для жителей
- **Регистрация** в системе с модерацией
- **Подача заявок** на пропуски для автомобилей
- **Просмотр** своих активных пропусков
- **Отмена** неиспользованных пропусков

### 🛡️ Для охранников
- **Поиск пропусков** по номеру автомобиля
- **Отметка использования** пропусков
- **Просмотр списка** активных пропусков
- **Быстрый доступ** к информации

### 👑 Для администраторов
- **Модерация заявок** на регистрацию
- **Управление пользователями** и их ролями
- **Статистика** использования системы
- **Уведомления** о новых заявках

## 🏗️ Архитектура

```
src/easy_pass_bot/
├── bot/                    # Основной код бота
├── core/                   # Ядро системы (интерфейсы, DI)
├── database/               # Работа с базой данных
├── handlers/               # Обработчики сообщений
├── keyboards/              # Клавиатуры Telegram
├── services/               # Бизнес-логика
├── security/               # Безопасность и валидация
├── monitoring/             # Мониторинг и метрики
├── features/               # Дополнительные функции
└── utils/                  # Утилиты
```

## 🚀 Быстрый старт

### Требования
- Python 3.8+
- SQLite 3
- Telegram Bot Token

### Установка

1. **Клонирование репозитория**
```bash
git clone https://github.com/merdocx/easy-pass-bot.git
cd easy-pass-bot
```

2. **Создание виртуального окружения**
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows
```

3. **Установка зависимостей**
```bash
pip install -r deploy/requirements.txt
```

4. **Настройка окружения**
```bash
cp .env.example .env
# Отредактируйте .env файл с вашими настройками
```

5. **Запуск бота**
```bash
python main.py
```

### Docker (рекомендуется)

```bash
docker-compose up -d
```

## 📖 Документация

- [**Руководство пользователя**](docs/user/README.md) - Как использовать бота
- [**Документация для разработчиков**](docs/developer/README.md) - Разработка и расширение
- [**API документация**](docs/api/README.md) - Интерфейсы и сервисы
- [**Развертывание**](docs/deployment/README.md) - Установка в продакшн
- [**Архитектура**](docs/architecture/README.md) - Схемы и диаграммы

## 🧪 Тестирование

```bash
# Запуск всех тестов
python run_tests.py

# Только unit тесты
python run_tests.py --type unit

# С покрытием кода
python run_tests.py --coverage

# Тесты производительности
python run_tests.py --performance
```

## 🔧 Управление

### Systemd (Linux)

```bash
# Запуск
sudo systemctl start easy-pass-bot

# Остановка
sudo systemctl stop easy-pass-bot

# Перезапуск
sudo systemctl restart easy-pass-bot

# Статус
sudo systemctl status easy-pass-bot

# Логи
sudo journalctl -u easy-pass-bot -f
```

### Docker

```bash
# Запуск
docker-compose up -d

# Остановка
docker-compose down

# Логи
docker-compose logs -f
```

## 📊 Мониторинг

- **Логи**: `logs/` директория
- **Метрики**: Встроенная система сбора метрик
- **Здоровье**: Health check endpoints
- **Алерты**: Уведомления о критических событиях

## 🔒 Безопасность

- ✅ **Валидация входных данных**
- ✅ **Защита от SQL инъекций**
- ✅ **Rate limiting**
- ✅ **Аудит действий**
- ✅ **Шифрование чувствительных данных**

## 🚀 Производительность

- **Валидация**: 1000+ операций/сек
- **CRUD операции**: 50+ операций/сек
- **Поиск**: 30+ операций/сек
- **Concurrent**: 10+ параллельных операций/сек
- **Память**: < 100MB для 1000 пользователей

## 🤝 Участие в разработке

1. Fork репозитория
2. Создайте feature branch (`git checkout -b feature/amazing-feature`)
3. Commit изменения (`git commit -m 'Add amazing feature'`)
4. Push в branch (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

См. [CONTRIBUTING.md](CONTRIBUTING.md) для подробностей.

## 📝 Лицензия

Этот проект лицензирован под MIT License - см. [LICENSE](LICENSE) файл.

## 📞 Поддержка

- **Issues**: [GitHub Issues](https://github.com/merdocx/easy-pass-bot/issues)
- **Discussions**: [GitHub Discussions](https://github.com/merdocx/easy-pass-bot/discussions)
- **Email**: support@example.com

## 🏆 Благодарности

- [aiogram](https://docs.aiogram.dev) - Асинхронная библиотека для Telegram Bot API
- [aiosqlite](https://aiosqlite.omnilib.dev) - Асинхронный SQLite
- [pytest](https://pytest.org) - Фреймворк для тестирования

---

**Сделано с ❤️ для удобства жителей и охранников**