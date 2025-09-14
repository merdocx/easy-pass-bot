"""
Тесты для модуля безопасности
"""
import pytest
import asyncio
from src.easy_pass_bot.security.rate_limiter import RateLimiter
from src.easy_pass_bot.security.validator import InputValidator
from src.easy_pass_bot.security.audit_logger import AuditLogger
@pytest.mark.asyncio

async def test_rate_limiter_allows_requests():
    """Тест разрешения запросов в пределах лимита"""
    limiter = RateLimiter(max_requests=5, window=60)
    # Первые 5 запросов должны быть разрешены
    for i in range(5):
        assert await limiter.is_allowed(12345) is True
    # 6-й запрос должен быть заблокирован
    assert await limiter.is_allowed(12345) is False
@pytest.mark.asyncio

async def test_rate_limiter_resets_after_window():
    """Тест сброса лимита после временного окна"""
    limiter = RateLimiter(max_requests=2, window=1)  # 1 секунда для быстрого теста
    # Исчерпываем лимит
    assert await limiter.is_allowed(12345) is True
    assert await limiter.is_allowed(12345) is True
    assert await limiter.is_allowed(12345) is False
    # Ждем окончания окна
    await asyncio.sleep(1.1)
    # Запросы должны снова быть разрешены
    assert await limiter.is_allowed(12345) is True

def test_validator_phone():
    """Тест валидации номера телефона"""
    validator = InputValidator()
    # Валидные номера
    assert validator.validate_phone("+7900123456")[0] is True
    assert validator.validate_phone("7900123456")[0] is True
    assert validator.validate_phone("+7 900 123 45 67")[0] is True
    # Невалидные номера
    assert validator.validate_phone("")[0] is False
    assert validator.validate_phone("123")[0] is False
    assert validator.validate_phone("+7abc123456")[0] is False

def test_validator_car_number():
    """Тест валидации номера автомобиля"""
    validator = InputValidator()
    # Валидные номера с кириллицей
    assert validator.validate_car_number("А123БВ777")[0] is True
    assert validator.validate_car_number("а123бв777")[0] is True  # Проверка регистра
    # Валидные номера с латиницей
    assert validator.validate_car_number("A123BC777")[0] is True
    assert validator.validate_car_number("a123bc777")[0] is True  # Проверка регистра
    # Валидные смешанные номера
    assert validator.validate_car_number("A123БВ777")[0] is True  # Латиница + кириллица
    assert validator.validate_car_number("А123BC777")[0] is True  # Кириллица + латиница
    # Невалидные номера
    assert validator.validate_car_number("")[0] is False
    assert validator.validate_car_number("123")[0] is False
    assert validator.validate_car_number("А123БВ77")[0] is False  # Неправильная длина
    assert validator.validate_car_number("123ABC777")[0] is False  # Начинается с цифры

def test_validator_name():
    """Тест валидации ФИО"""
    validator = InputValidator()
    # Валидные имена
    assert validator.validate_name("Иван Иванов")[0] is True
    assert validator.validate_name("Мария-Анна Петрова-Сидорова")[0] is True
    # Невалидные имена
    assert validator.validate_name("")[0] is False
    assert validator.validate_name("И")[0] is False  # Слишком короткое
    assert validator.validate_name("Иван123")[0] is False  # Цифры
    assert validator.validate_name("Иван")[0] is False  # Одно слово

def test_validator_apartment():
    """Тест валидации номера квартиры"""
    validator = InputValidator()
    # Валидные номера
    assert validator.validate_apartment("15")[0] is True
    assert validator.validate_apartment("15А")[0] is True
    assert validator.validate_apartment("1234")[0] is True
    # Невалидные номера
    assert validator.validate_apartment("")[0] is False
    assert validator.validate_apartment("А15")[0] is False  # Буква в начале
    assert validator.validate_apartment("15-А")[0] is False  # Дефис

def test_validator_registration_data():
    """Тест валидации данных регистрации"""
    validator = InputValidator()
    # Валидные данные
    is_valid, error, data = validator.validate_registration_data(
        "Иван Иванов, +7900123456, 15"
    )
    assert is_valid is True
    assert error is None
    assert data['full_name'] == "Иван Иванов"
    assert data['phone_number'] == "+7900123456"
    assert data['apartment'] == "15"
    # Невалидные данные
    is_valid, error, data = validator.validate_registration_data(
        "Иван, +7900123456, 15"  # Неполное ФИО
    )
    assert is_valid is False
    assert error is not None

def test_audit_logger():
    """Тест аудит-логгера"""
    logger = AuditLogger("test_logs")
    # Тест логирования события
    logger.log_security_event("test_event", 12345, {"test": "data"})
    # Тест логирования неудачной попытки
    logger.log_failed_attempt(12345, "test_attempt", "test_reason")
    # Тест логирования успешного действия
    logger.log_successful_action(12345, "test_action", {"result": "success"})
    # Проверяем, что логи созданы
    assert logger.log_dir.exists()
    assert (logger.log_dir / "security_audit.log").exists()

def test_sanitize_input():
    """Тест очистки входных данных"""
    validator = InputValidator()
    # Тест очистки HTML тегов
    assert validator.sanitize_input("<script>alert('test')</script>") == "alert('test')"
    # Тест очистки управляющих символов
    assert validator.sanitize_input("test\x00\x1f\x7f") == "test"
    # Тест ограничения длины
    long_text = "a" * 2000
    sanitized = validator.sanitize_input(long_text)
    assert len(sanitized) <= 1000





