"""
Фикстуры для тестирования пропусков
"""
import pytest
from datetime import datetime, timedelta
from src.easy_pass_bot.database.models import Pass
from src.easy_pass_bot.config import PASS_STATUSES


@pytest.fixture
def sample_pass_data():
    """Тестовые данные пропуска"""
    return {
        'user_id': 1,
        'car_number': 'А123БВ777',
        'status': PASS_STATUSES['ACTIVE'],
        'created_at': datetime.now()
    }


@pytest.fixture
def sample_pass(sample_pass_data):
    """Образец пропуска"""
    return Pass(**sample_pass_data)


@pytest.fixture
def used_pass_data():
    """Тестовые данные использованного пропуска"""
    return {
        'user_id': 1,
        'car_number': 'В456ГД888',
        'status': PASS_STATUSES['USED'],
        'created_at': datetime.now() - timedelta(hours=2),
        'used_at': datetime.now() - timedelta(hours=1),
        'used_by_id': 2
    }


@pytest.fixture
def used_pass(used_pass_data):
    """Образец использованного пропуска"""
    return Pass(**used_pass_data)


@pytest.fixture
def cancelled_pass_data():
    """Тестовые данные отмененного пропуска"""
    return {
        'user_id': 1,
        'car_number': 'Е789ЖЗ999',
        'status': PASS_STATUSES['CANCELLED'],
        'created_at': datetime.now() - timedelta(hours=3),
        'used_at': datetime.now() - timedelta(hours=2),
        'used_by_id': 1
    }


@pytest.fixture
def cancelled_pass(cancelled_pass_data):
    """Образец отмененного пропуска"""
    return Pass(**cancelled_pass_data)


@pytest.fixture
def multiple_passes(sample_pass, used_pass, cancelled_pass):
    """Несколько пропусков для тестирования"""
    return [sample_pass, used_pass, cancelled_pass]


@pytest.fixture
def pass_list():
    """Список пропусков для тестирования"""
    now = datetime.now()
    return [
        Pass(
            user_id=1,
            car_number='А111АА111',
            status=PASS_STATUSES['ACTIVE'],
            created_at=now - timedelta(hours=1)
        ),
        Pass(
            user_id=1,
            car_number='В222ВВ222',
            status=PASS_STATUSES['ACTIVE'],
            created_at=now - timedelta(hours=2)
        ),
        Pass(
            user_id=2,
            car_number='С333СС333',
            status=PASS_STATUSES['USED'],
            created_at=now - timedelta(hours=3),
            used_at=now - timedelta(hours=1),
            used_by_id=3
        ),
        Pass(
            user_id=2,
            car_number='Д444ДД444',
            status=PASS_STATUSES['CANCELLED'],
            created_at=now - timedelta(hours=4),
            used_at=now - timedelta(hours=2),
            used_by_id=2
        )
    ]


@pytest.fixture
def old_pass_data():
    """Тестовые данные старого пропуска"""
    return {
        'user_id': 1,
        'car_number': 'СТАРЫЙ123',
        'status': PASS_STATUSES['USED'],
        'created_at': datetime.now() - timedelta(days=35),
        'used_at': datetime.now() - timedelta(days=30),
        'used_by_id': 2
    }


@pytest.fixture
def old_pass(old_pass_data):
    """Образец старого пропуска"""
    return Pass(**old_pass_data)





