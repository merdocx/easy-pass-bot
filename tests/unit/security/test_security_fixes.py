"""
Тесты безопасности для Easy Pass Bot
"""
import pytest
import asyncio
from unittest.mock import Mock, patch
from ..security.validator import validator
from ..security.rate_limiter import rate_limiter
from ..security.audit_logger import audit_logger

class TestSecurityValidator:
    """Тесты валидатора"""
    
    def test_validate_telegram_id_valid(self):
        """Тест валидации корректного Telegram ID"""
        is_valid, error = validator.validate_telegram_id(123456789)
        assert is_valid
        assert error is None
    
    def test_validate_telegram_id_invalid(self):
        """Тест валидации некорректного Telegram ID"""
        is_valid, error = validator.validate_telegram_id(-1)
        assert not is_valid
        assert "Invalid Telegram ID" in error
    
    def test_validate_car_number_valid(self):
        """Тест валидации корректного номера автомобиля"""
        is_valid, error = validator.validate_car_number("А123БВ77")
        assert is_valid
        assert error is None
    
    def test_validate_car_number_invalid(self):
        """Тест валидации некорректного номера автомобиля"""
        is_valid, error = validator.validate_car_number("")
        assert not is_valid
        assert "Car number is required" in error
    
    def test_validate_phone_number_valid(self):
        """Тест валидации корректного номера телефона"""
        is_valid, error = validator.validate_phone_number("+7 (999) 123-45-67")
        assert is_valid
        assert error is None
    
    def test_validate_phone_number_invalid(self):
        """Тест валидации некорректного номера телефона"""
        is_valid, error = validator.validate_phone_number("invalid")
        assert not is_valid
        assert "Invalid phone number" in error

class TestRateLimiter:
    """Тесты rate limiter"""
    
    @pytest.mark.asyncio
    async def test_rate_limiter_allows_requests(self):
        """Тест разрешения запросов в пределах лимита"""
        user_id = 123456789
        
        # Первые несколько запросов должны быть разрешены
        for _ in range(5):
            is_allowed = await rate_limiter.is_allowed(user_id)
            assert is_allowed
    
    @pytest.mark.asyncio
    async def test_rate_limiter_blocks_excessive_requests(self):
        """Тест блокировки избыточных запросов"""
        user_id = 123456789
        
        # Делаем много запросов подряд
        for _ in range(20):
            await rate_limiter.is_allowed(user_id)
        
        # Последние запросы должны быть заблокированы
        is_allowed = await rate_limiter.is_allowed(user_id)
        assert not is_allowed

class TestAuditLogger:
    """Тесты аудит-логгера"""
    
    def test_log_user_registration(self):
        """Тест логирования регистрации пользователя"""
        user_id = 123456789
        user_data = {"full_name": "Test User"}
        
        # Не должно вызывать исключений
        audit_logger.log_user_registration(user_id, user_data)
    
    def test_log_pass_creation(self):
        """Тест логирования создания пропуска"""
        user_id = 123456789
        car_number = "А123БВ77"
        
        # Не должно вызывать исключений
        audit_logger.log_pass_creation(user_id, car_number)
    
    def test_log_pass_usage(self):
        """Тест логирования использования пропуска"""
        user_id = 123456789
        pass_id = 1
        car_number = "А123БВ77"
        used_by_id = 987654321
        
        # Не должно вызывать исключений
        audit_logger.log_pass_usage(user_id, pass_id, car_number, used_by_id)

class TestSecurityIntegration:
    """Интеграционные тесты безопасности"""
    
    @pytest.mark.asyncio
    async def test_security_middleware_flow(self):
        """Тест работы security middleware"""
        from ..security.middleware import SecurityMiddleware
        
        middleware = SecurityMiddleware()
        
        # Создаем мок-событие
        mock_event = Mock()
        mock_event.from_user.id = 123456789
        
        # Создаем мок-обработчик
        mock_handler = Mock(return_value="success")
        
        # Тестируем middleware
        result = await middleware(mock_handler, mock_event, {})
        
        # Проверяем, что обработчик был вызван
        mock_handler.assert_called_once()
        assert result == "success"
    
    def test_security_config_loading(self):
        """Тест загрузки конфигурации безопасности"""
        from ..security.config import get_security_config, is_secure_mode
        
        config = get_security_config()
        assert isinstance(config, dict)
        assert 'RATE_LIMIT_MAX_REQUESTS' in config
        assert 'MAX_CAR_NUMBER_LENGTH' in config
        
        # Тест безопасного режима
        secure_mode = is_secure_mode()
        assert isinstance(secure_mode, bool)
