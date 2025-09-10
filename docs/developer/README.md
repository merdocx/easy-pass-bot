# Документация для разработчиков

## Обзор архитектуры

Easy Pass Bot построен на современной архитектуре с использованием принципов SOLID, Dependency Injection и Clean Architecture.

## Структура проекта

```
src/easy_pass_bot/
├── bot/                    # Основной код бота
│   └── main.py            # Точка входа
├── core/                   # Ядро системы
│   ├── interfaces.py      # Интерфейсы
│   ├── exceptions.py      # Исключения
│   ├── base.py           # Базовые классы
│   ├── container.py      # DI контейнер
│   └── service_config.py # Конфигурация сервисов
├── database/               # Работа с БД
│   ├── models.py         # Модели данных
│   ├── database.py       # Основной класс БД
│   └── __init__.py
├── handlers/               # Обработчики сообщений
│   ├── resident_handlers.py
│   ├── security_handlers.py
│   ├── admin_handlers.py
│   └── common_handlers.py
├── keyboards/              # Клавиатуры Telegram
│   ├── resident_keyboards.py
│   ├── security_keyboards.py
│   └── admin_keyboards.py
├── services/               # Бизнес-логика
│   ├── user_service.py
│   ├── pass_service.py
│   ├── validation_service.py
│   └── notification_service.py
├── security/               # Безопасность
│   ├── rate_limiter.py
│   ├── validator.py
│   └── audit_logger.py
├── monitoring/             # Мониторинг
│   ├── metrics.py
│   ├── health_check.py
│   └── alerting.py
├── features/               # Дополнительные функции
│   ├── analytics.py
│   ├── navigation.py
│   └── confirmation.py
└── utils/                  # Утилиты
    ├── validators.py
    └── notifications.py
```

## Принципы архитектуры

### 1. Dependency Injection (DI)

Система использует DI контейнер для управления зависимостями:

```python
from easy_pass_bot.core.container import Container, inject

# Регистрация сервиса
container = Container()
container.register('user_service', UserService)

# Инъекция зависимостей
@inject('user_service')
class SomeHandler:
    def __init__(self, user_service: IUserService):
        self.user_service = user_service
```

### 2. Интерфейсы

Все сервисы реализуют интерфейсы:

```python
from abc import ABC, abstractmethod

class IUserService(ABC):
    @abstractmethod
    async def create_user(self, **kwargs) -> User:
        pass
    
    @abstractmethod
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        pass
```

### 3. Базовые классы

Общие функции вынесены в базовые классы:

```python
class BaseService(ABC):
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def initialize(self):
        """Инициализация сервиса"""
        pass
    
    async def cleanup(self):
        """Очистка ресурсов"""
        pass
```

## Разработка

### Настройка окружения

1. **Клонирование репозитория**
```bash
git clone https://github.com/merdocx/easy-pass-bot.git
cd easy-pass-bot
```

2. **Создание виртуального окружения**
```bash
python3 -m venv venv
source venv/bin/activate
```

3. **Установка зависимостей**
```bash
pip install -r deploy/requirements.txt
pip install -r deploy/requirements-dev.txt
```

4. **Настройка pre-commit хуков**
```bash
pre-commit install
```

### Структура кода

#### Создание нового сервиса

1. **Создайте интерфейс** в `core/interfaces.py`:

```python
class INewService(ABC):
    @abstractmethod
    async def do_something(self, param: str) -> bool:
        pass
```

2. **Реализуйте сервис** в `services/new_service.py`:

```python
from ..core.interfaces import INewService
from ..core.base import BaseService

class NewService(BaseService, INewService):
    def __init__(self):
        super().__init__()
    
    async def do_something(self, param: str) -> bool:
        # Реализация
        return True
```

3. **Зарегистрируйте в контейнере** в `core/service_config.py`:

```python
container.register('new_service', NewService)
```

#### Создание нового обработчика

1. **Создайте файл** в `handlers/new_handlers.py`:

```python
import logging
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

logger = logging.getLogger(__name__)
router = Router()

@router.message(Command("new_command"))
async def handle_new_command(message: Message):
    """Обработка новой команды"""
    await message.answer("Новая команда обработана!")
```

2. **Зарегистрируйте роутер** в `bot/main.py`:

```python
from .handlers.new_handlers import router as new_router
dp.include_router(new_router)
```

### Тестирование

#### Unit тесты

```python
import pytest
from unittest.mock import AsyncMock
from src.easy_pass_bot.services.user_service import UserService

class TestUserService:
    @pytest.fixture
    def user_service(self):
        mock_repo = AsyncMock()
        mock_notification = AsyncMock()
        return UserService(mock_repo, mock_notification)
    
    @pytest.mark.asyncio
    async def test_create_user(self, user_service):
        # Тест создания пользователя
        user = await user_service.create_user(
            telegram_id=123456789,
            full_name="Test User",
            phone_number="+7 900 123 45 67",
            apartment="15"
        )
        assert user.telegram_id == 123456789
```

#### Интеграционные тесты

```python
import pytest
from src.easy_pass_bot.database import db

@pytest.mark.asyncio
async def test_user_workflow():
    # Создание пользователя
    user = await db.create_user(User(...))
    
    # Создание пропуска
    pass_obj = await db.create_pass(Pass(...))
    
    # Проверка связей
    assert pass_obj.user_id == user.id
```

#### Запуск тестов

```bash
# Все тесты
python run_tests.py

# Только unit тесты
python run_tests.py --type unit

# С покрытием
python run_tests.py --coverage

# Параллельно
python run_tests.py --parallel 4
```

### Линтинг и форматирование

```bash
# Проверка стиля кода
flake8 src/

# Автоисправление
autopep8 --in-place --recursive src/

# Проверка типов
mypy src/

# Форматирование
black src/
```

## Конфигурация

### Переменные окружения

```bash
# .env файл
BOT_TOKEN=your_telegram_bot_token
DATABASE_PATH=database/easy_pass.db
LOG_LEVEL=INFO
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600
```

### Конфигурация сервисов

```python
# core/service_config.py
async def initialize_services():
    """Инициализация всех сервисов"""
    container = Container()
    
    # Регистрация сервисов
    container.register('user_service', UserService)
    container.register('pass_service', PassService)
    
    # Инициализация
    for service in container.get_all_services():
        await service.initialize()
```

## Мониторинг и логирование

### Логирование

```python
import logging

logger = logging.getLogger(__name__)

# Различные уровни
logger.debug("Отладочная информация")
logger.info("Информационное сообщение")
logger.warning("Предупреждение")
logger.error("Ошибка")
logger.critical("Критическая ошибка")
```

### Метрики

```python
from monitoring.metrics import metrics_collector

# Счетчики
metrics_collector.increment_counter('user_created')

# Время выполнения
with metrics_collector.timer('database_query'):
    result = await db.query()

# Размеры
metrics_collector.record_gauge('active_users', count)
```

### Health Checks

```python
from monitoring.health_check import check_database_health

# Проверка здоровья БД
is_healthy = await check_database_health()
```

## Безопасность

### Валидация входных данных

```python
from security.validator import validator

# Валидация данных
is_valid = await validator.validate_user_data({
    'full_name': 'Иванов Иван Иванович',
    'phone_number': '+7 900 123 45 67',
    'apartment': '15'
})
```

### Rate Limiting

```python
from security.rate_limiter import rate_limiter

# Проверка лимитов
if not await rate_limiter.check_rate_limit(user_id, 'message'):
    raise RateLimitExceeded()
```

### Аудит

```python
from security.audit_logger import audit_logger

# Логирование действий
await audit_logger.log_action(
    user_id=user_id,
    action='user_created',
    details={'telegram_id': telegram_id}
)
```

## Производительность

### Кэширование

```python
from services.cache_service import cache_service

# Получение из кэша
cached_data = await cache_service.get('user:123')

# Сохранение в кэш
await cache_service.set('user:123', user_data, ttl=3600)
```

### Асинхронность

```python
import asyncio

# Параллельное выполнение
results = await asyncio.gather(
    service1.do_something(),
    service2.do_something(),
    service3.do_something()
)
```

### Оптимизация запросов

```python
# Batch операции
users = await db.get_users_batch(user_ids)

# Индексы в БД
CREATE INDEX idx_users_telegram_id ON users(telegram_id);
CREATE INDEX idx_passes_car_number ON passes(car_number);
```

## Развертывание

### Локальная разработка

```bash
# Запуск в режиме разработки
python main.py

# С отладкой
python -m pdb main.py
```

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "main.py"]
```

### Systemd

```ini
[Unit]
Description=Easy Pass Bot
After=network.target

[Service]
Type=simple
User=bot
WorkingDirectory=/opt/easy-pass-bot
ExecStart=/opt/easy-pass-bot/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## Отладка

### Логи

```bash
# Просмотр логов
tail -f logs/bot.log

# Фильтрация по уровню
grep "ERROR" logs/bot.log

# Поиск по пользователю
grep "user_id:123" logs/bot.log
```

### Профилирование

```python
import cProfile
import pstats

# Профилирование
profiler = cProfile.Profile()
profiler.enable()

# Ваш код
await some_function()

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative').print_stats(10)
```

### Отладка в IDE

```python
# Точки останова
import pdb; pdb.set_trace()

# Логирование переменных
logger.debug(f"Variable value: {variable}")
```

## Лучшие практики

### 1. Код

- Используйте type hints
- Пишите docstrings
- Следуйте PEP 8
- Используйте async/await правильно
- Обрабатывайте исключения

### 2. Тестирование

- Покрытие кода > 80%
- Тестируйте граничные случаи
- Используйте моки для внешних зависимостей
- Параллельные тесты

### 3. Безопасность

- Валидируйте все входные данные
- Используйте параметризованные запросы
- Логируйте подозрительную активность
- Ограничивайте частоту запросов

### 4. Производительность

- Используйте кэширование
- Оптимизируйте запросы к БД
- Мониторьте использование ресурсов
- Профилируйте код

## Полезные ресурсы

- [aiogram документация](https://docs.aiogram.dev)
- [asyncio документация](https://docs.python.org/3/library/asyncio.html)
- [pytest документация](https://docs.pytest.org)
- [SQLite документация](https://www.sqlite.org/docs.html)
- [Python best practices](https://docs.python-guide.org)

## FAQ

### Q: Как добавить новую команду?
A: Создайте обработчик в `handlers/` и зарегистрируйте роутер в `main.py`.

### Q: Как изменить логику валидации?
A: Отредактируйте методы в `services/validation_service.py`.

### Q: Как добавить новый тип уведомлений?
A: Расширьте `services/notification_service.py` и добавьте соответствующие методы.

### Q: Как настроить мониторинг?
A: Используйте встроенные метрики в `monitoring/` или интегрируйте внешние системы.

## Контакты

- **Lead Developer**: [@merdocx](https://github.com/merdocx)
- **Issues**: [GitHub Issues](https://github.com/merdocx/easy-pass-bot/issues)
- **Discussions**: [GitHub Discussions](https://github.com/merdocx/easy-pass-bot/discussions)




