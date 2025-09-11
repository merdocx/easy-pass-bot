"""
Фикстуры для тестирования пользователей
"""
import pytest
from datetime import datetime
from src.easy_pass_bot.database.models import User
from src.easy_pass_bot.config import ROLES, USER_STATUSES


@pytest.fixture
def sample_user_data():
    """Тестовые данные пользователя"""
    return {
        'telegram_id': 123456789,
        'role': ROLES['RESIDENT'],
        'full_name': 'Иванов Иван Иванович',
        'phone_number': '+7 900 123 45 67',
        'apartment': '15',
        'status': USER_STATUSES['PENDING']
    }


@pytest.fixture
def sample_user(sample_user_data):
    """Образец пользователя"""
    return User(**sample_user_data)


@pytest.fixture
def admin_user_data():
    """Тестовые данные администратора"""
    return {
        'telegram_id': 987654321,
        'role': ROLES['ADMIN'],
        'full_name': 'Админ Админович',
        'phone_number': '+7 900 987 65 43',
        'apartment': None,
        'status': USER_STATUSES['APPROVED']
    }


@pytest.fixture
def admin_user(admin_user_data):
    """Образец администратора"""
    return User(**admin_user_data)


@pytest.fixture
def security_user_data():
    """Тестовые данные охранника"""
    return {
        'telegram_id': 555666777,
        'role': ROLES['SECURITY'],
        'full_name': 'Охранник Охранникович',
        'phone_number': '+7 900 555 66 77',
        'apartment': None,
        'status': USER_STATUSES['APPROVED']
    }


@pytest.fixture
def security_user(security_user_data):
    """Образец охранника"""
    return User(**security_user_data)


@pytest.fixture
def approved_user_data():
    """Тестовые данные одобренного пользователя"""
    return {
        'telegram_id': 111222333,
        'role': ROLES['RESIDENT'],
        'full_name': 'Одобренный Пользователь',
        'phone_number': '+7 900 111 22 33',
        'apartment': '42',
        'status': USER_STATUSES['APPROVED']
    }


@pytest.fixture
def approved_user(approved_user_data):
    """Образец одобренного пользователя"""
    return User(**approved_user_data)


@pytest.fixture
def multiple_users(sample_user, admin_user, security_user, approved_user):
    """Несколько пользователей для тестирования"""
    return [sample_user, admin_user, security_user, approved_user]


@pytest.fixture
def user_list():
    """Список пользователей для тестирования"""
    return [
        User(
            telegram_id=1001,
            role=ROLES['RESIDENT'],
            full_name='Пользователь 1',
            phone_number='+7 900 100 01 01',
            apartment='1',
            status=USER_STATUSES['PENDING']
        ),
        User(
            telegram_id=1002,
            role=ROLES['RESIDENT'],
            full_name='Пользователь 2',
            phone_number='+7 900 100 02 02',
            apartment='2',
            status=USER_STATUSES['APPROVED']
        ),
        User(
            telegram_id=1003,
            role=ROLES['ADMIN'],
            full_name='Админ 2',
            phone_number='+7 900 100 03 03',
            apartment=None,
            status=USER_STATUSES['APPROVED']
        )
    ]





