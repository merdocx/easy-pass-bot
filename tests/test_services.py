"""
Тесты для сервисов
"""
import pytest
import asyncio
from src.easy_pass_bot.services.cache_service import CacheService
from src.easy_pass_bot.services.error_handler import ErrorHandler, ValidationError, DatabaseError
from src.easy_pass_bot.services.retry_service import RetryService, RetryStrategy
from src.easy_pass_bot.services.circuit_breaker import CircuitBreaker, CircuitState
from src.easy_pass_bot.features.analytics import AnalyticsService
from src.easy_pass_bot.features.navigation import NavigationService
from src.easy_pass_bot.features.confirmation import ConfirmationService
@pytest.mark.asyncio

async def test_cache_service():
    """Тест сервиса кэширования"""
    cache = CacheService(default_ttl=1)  # 1 секунда для быстрого теста
    # Тест установки и получения значения
    await cache.set("test_key", "test_value")
    assert await cache.get("test_key") == "test_value"
    # Тест истечения TTL
    await asyncio.sleep(1.1)
    assert await cache.get("test_key") is None
    # Тест get_or_set
    result = await cache.get_or_set("new_key", lambda: "new_value")
    assert result == "new_value"
    assert await cache.get("new_key") == "new_value"
@pytest.mark.asyncio

async def test_error_handler():
    """Тест обработчика ошибок"""
    handler = ErrorHandler()
    # Тест обработки ValidationError
    error = ValidationError("Invalid input", field="email")
    response = await handler.handle_error(error)
    assert "Ошибка валидации" in response
    # Тест обработки DatabaseError
    error = DatabaseError("Connection failed", operation="SELECT")
    response = await handler.handle_error(error)
    assert "Ошибка базы данных" in response
@pytest.mark.asyncio

async def test_retry_service():
    """Тест сервиса повторных попыток"""
    retry = RetryService(max_attempts=3, base_delay=0.1)
    # Тест успешного выполнения
    async def success_func():
        return "success"
    result = await retry.execute_with_retry(success_func)
    assert result == "success"
    # Тест с повторными попытками
    attempt_count = 0
    async def failing_func():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise Exception("Temporary failure")
        return "success"
    result = await retry.execute_with_retry(failing_func)
    assert result == "success"
    assert attempt_count == 3
@pytest.mark.asyncio

async def test_circuit_breaker():
    """Тест Circuit Breaker"""
    breaker = CircuitBreaker(failure_threshold=2, timeout=1)
    # Тест нормальной работы
    async def success_func():
        return "success"
    result = await breaker.call(success_func)
    assert result == "success"
    assert breaker.get_state() == CircuitState.CLOSED
    # Тест открытия Circuit Breaker
    async def failing_func():
        raise Exception("Service down")
    # Вызываем функцию до превышения порога
    for _ in range(2):
        try:
            await breaker.call(failing_func)
        except Exception:
            pass
    # Circuit Breaker должен быть открыт
    assert breaker.get_state() == CircuitState.OPEN

def test_analytics_service():
    """Тест сервиса аналитики"""
    analytics = AnalyticsService()
    # Тест отслеживания действий
    analytics.track_action(12345, "test_action", {"param": "value"})
    analytics.track_page_view(12345, "test_page")
    # Тест сессий
    analytics.start_session(12345)
    analytics.end_session(12345)
    # Тест получения аналитики
    user_analytics = analytics.get_user_analytics(12345)
    assert user_analytics['user_id'] == 12345
    assert user_analytics['total_actions'] > 0

def test_navigation_service():
    """Тест сервиса навигации"""
    nav = NavigationService()
    # Тест истории навигации
    nav.add_to_history(12345, "page1")
    nav.add_to_history(12345, "page2")
    history = nav.get_history(12345)
    assert len(history) == 2
    assert history[-1] == "page2"
    # Тест предыдущей страницы
    prev_page = nav.get_previous_page(12345)
    assert prev_page == "page1"
@pytest.mark.asyncio

async def test_confirmation_service():
    """Тест сервиса подтверждений"""
    conf = ConfirmationService(timeout=1)
    # Тест регистрации подтверждения
    confirmation_id = conf.register_confirmation(
        "test_123", "delete_user", {"user_id": 12345}, lambda x: "deleted"
    )
    assert confirmation_id == "test_123"
    # Тест обработки подтверждения
    result = await conf.handle_confirmation("test_123", "delete_user", True)
    assert result == "deleted"
    # Тест отмены
    conf.register_confirmation("test_456", "delete_user", {"user_id": 12345}, lambda x: "deleted")
    result = await conf.handle_confirmation("test_456", "delete_user", False)
    assert result is None
@pytest.mark.asyncio

async def test_cache_decorator():
    """Тест декоратора кэширования"""
    cache = CacheService()
    call_count = 0
    @cache.cached(ttl=1, key_prefix="test")
    async def expensive_function(param):
        nonlocal call_count
        call_count += 1
        return f"result_{param}"
    # Первый вызов - должен выполнить функцию
    result1 = await expensive_function("test")
    assert result1 == "result_test"
    assert call_count == 1
    # Второй вызов - должен взять из кэша
    result2 = await expensive_function("test")
    assert result2 == "result_test"
    assert call_count == 1  # Не должно увеличиться

def test_error_types():
    """Тест типов ошибок"""
    # ValidationError
    error = ValidationError("Invalid email", field="email", value="invalid")
    assert error.field == "email"
    assert error.value == "invalid"
    assert error.severity.value == "low"
    # DatabaseError
    error = DatabaseError("Connection failed", operation="SELECT", table="users")
    assert error.operation == "SELECT"
    assert error.table == "users"
    assert error.severity.value == "high"
@pytest.mark.asyncio

async def test_retry_strategies():
    """Тест стратегий повторных попыток"""
    retry = RetryService(strategy=RetryStrategy.EXPONENTIAL, base_delay=0.1)
    # Тест экспоненциальной стратегии
    delay1 = retry.calculate_delay(1)
    delay2 = retry.calculate_delay(2)
    delay3 = retry.calculate_delay(3)
    assert delay1 == 0.1
    assert delay2 == 0.2
    assert delay3 == 0.4
    # Тест фиксированной стратегии
    retry_fixed = RetryService(strategy=RetryStrategy.FIXED, base_delay=0.1)
    assert retry_fixed.calculate_delay(1) == 0.1
    assert retry_fixed.calculate_delay(5) == 0.1





