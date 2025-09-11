"""
Тесты для модуля базы данных
"""
import pytest
from src.easy_pass_bot.database.models import User, Pass
from src.easy_pass_bot.config import USER_STATUSES, PASS_STATUSES
@pytest.mark.asyncio

async def test_create_user(test_db, sample_user):
    """Тест создания пользователя"""
    user_id = await test_db.create_user(sample_user)
    assert user_id is not None
    assert user_id > 0
@pytest.mark.asyncio

async def test_get_user_by_telegram_id(test_db, sample_user):
    """Тест получения пользователя по Telegram ID"""
    # Создаем пользователя
    user_id = await test_db.create_user(sample_user)
    sample_user.id = user_id
    # Получаем пользователя
    retrieved_user = await test_db.get_user_by_telegram_id(sample_user.telegram_id)
    assert retrieved_user is not None
    assert retrieved_user.telegram_id == sample_user.telegram_id
    assert retrieved_user.full_name == sample_user.full_name
    assert retrieved_user.role == sample_user.role
    assert retrieved_user.status == sample_user.status
@pytest.mark.asyncio

async def test_get_user_by_id(test_db, sample_user):
    """Тест получения пользователя по ID"""
    # Создаем пользователя
    user_id = await test_db.create_user(sample_user)
    # Получаем пользователя
    retrieved_user = await test_db.get_user_by_id(user_id)
    assert retrieved_user is not None
    assert retrieved_user.id == user_id
    assert retrieved_user.telegram_id == sample_user.telegram_id
@pytest.mark.asyncio

async def test_update_user_status(test_db, sample_user):
    """Тест обновления статуса пользователя"""
    # Создаем пользователя
    user_id = await test_db.create_user(sample_user)
    # Обновляем статус
    await test_db.update_user_status(user_id, USER_STATUSES['APPROVED'])
    # Проверяем обновление
    updated_user = await test_db.get_user_by_id(user_id)
    assert updated_user.status == USER_STATUSES['APPROVED']
@pytest.mark.asyncio

async def test_create_pass(test_db, sample_user, sample_pass):
    """Тест создания пропуска"""
    # Создаем пользователя
    user_id = await test_db.create_user(sample_user)
    sample_pass.user_id = user_id
    # Создаем пропуск
    pass_id = await test_db.create_pass(sample_pass)
    assert pass_id is not None
    assert pass_id > 0
@pytest.mark.asyncio

async def test_get_user_passes(test_db, sample_user, sample_pass):
    """Тест получения пропусков пользователя"""
    # Создаем пользователя
    user_id = await test_db.create_user(sample_user)
    sample_pass.user_id = user_id
    # Создаем пропуск
    pass_id = await test_db.create_pass(sample_pass)
    # Получаем пропуски пользователя
    passes = await test_db.get_user_passes(user_id)
    assert len(passes) == 1
    assert passes[0].car_number == sample_pass.car_number
    assert passes[0].status == sample_pass.status
@pytest.mark.asyncio

async def test_find_pass_by_car_number(test_db, sample_user, sample_pass):
    """Тест поиска пропуска по номеру автомобиля"""
    # Создаем пользователя
    user_id = await test_db.create_user(sample_user)
    sample_pass.user_id = user_id
    # Создаем пропуск
    pass_id = await test_db.create_pass(sample_pass)
    # Ищем пропуск
    found_pass = await test_db.find_pass_by_car_number(sample_pass.car_number)
    assert found_pass is not None
    assert found_pass.car_number == sample_pass.car_number
@pytest.mark.asyncio

async def test_find_all_passes_by_car_number(test_db, sample_user):
    """Тест поиска всех пропусков по номеру автомобиля"""
    # Создаем пользователя
    user_id = await test_db.create_user(sample_user)
    # Создаем несколько пропусков с похожими номерами
    pass1 = Pass(user_id=user_id, car_number="А123БВ777", status=PASS_STATUSES['ACTIVE'])
    pass2 = Pass(user_id=user_id, car_number="А123БВ888", status=PASS_STATUSES['ACTIVE'])
    await test_db.create_pass(pass1)
    await test_db.create_pass(pass2)
    # Ищем по частичному номеру
    found_passes = await test_db.find_all_passes_by_car_number("А123")
    assert len(found_passes) == 2
@pytest.mark.asyncio

async def test_update_pass_status(test_db, sample_user, sample_pass):
    """Тест обновления статуса пропуска"""
    # Создаем пользователя
    user_id = await test_db.create_user(sample_user)
    sample_pass.user_id = user_id
    # Создаем пропуск
    pass_id = await test_db.create_pass(sample_pass)
    # Обновляем статус
    await test_db.update_pass_status(pass_id, PASS_STATUSES['USED'], user_id)
    # Проверяем обновление
    updated_pass = await test_db.get_pass_by_id(pass_id)
    assert updated_pass.status == PASS_STATUSES['USED']
@pytest.mark.asyncio

async def test_get_all_users(test_db, sample_user, admin_user):
    """Тест получения всех пользователей"""
    # Создаем пользователей
    await test_db.create_user(sample_user)
    await test_db.create_user(admin_user)
    # Получаем всех пользователей
    users = await test_db.get_all_users()
    assert len(users) == 2
    telegram_ids = [user.telegram_id for user in users]
    assert sample_user.telegram_id in telegram_ids
    assert admin_user.telegram_id in telegram_ids
