"""
Кастомные исключения для системы
"""
from typing import Optional, Dict, Any


class EasyPassBotError(Exception):
    """Базовое исключение для Easy Pass Bot"""
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}


class ValidationError(EasyPassBotError):
    """Ошибка валидации данных"""
    
    def __init__(
        self, 
        message: str, 
        field: Optional[str] = None,
        value: Optional[Any] = None
    ):
        super().__init__(message, "VALIDATION_ERROR")
        self.field = field
        self.value = value


class DatabaseError(EasyPassBotError):
    """Ошибка работы с базой данных"""
    
    def __init__(self, message: str, operation: Optional[str] = None):
        super().__init__(message, "DATABASE_ERROR")
        self.operation = operation


class ExternalServiceError(EasyPassBotError):
    """Ошибка внешнего сервиса"""
    
    def __init__(
        self, 
        message: str, 
        service_name: Optional[str] = None,
        status_code: Optional[int] = None
    ):
        super().__init__(message, "EXTERNAL_SERVICE_ERROR")
        self.service_name = service_name
        self.status_code = status_code


class AuthenticationError(EasyPassBotError):
    """Ошибка аутентификации"""
    
    def __init__(self, message: str, user_id: Optional[int] = None):
        super().__init__(message, "AUTHENTICATION_ERROR")
        self.user_id = user_id


class AuthorizationError(EasyPassBotError):
    """Ошибка авторизации"""
    
    def __init__(
        self, 
        message: str, 
        user_id: Optional[int] = None,
        required_role: Optional[str] = None
    ):
        super().__init__(message, "AUTHORIZATION_ERROR")
        self.user_id = user_id
        self.required_role = required_role


class RateLimitError(EasyPassBotError):
    """Ошибка превышения лимита запросов"""
    
    def __init__(
        self, 
        message: str, 
        user_id: Optional[int] = None,
        retry_after: Optional[int] = None
    ):
        super().__init__(message, "RATE_LIMIT_ERROR")
        self.user_id = user_id
        self.retry_after = retry_after


class NotificationError(EasyPassBotError):
    """Ошибка отправки уведомления"""
    
    def __init__(
        self, 
        message: str, 
        user_id: Optional[int] = None,
        notification_type: Optional[str] = None
    ):
        super().__init__(message, "NOTIFICATION_ERROR")
        self.user_id = user_id
        self.notification_type = notification_type


class CacheError(EasyPassBotError):
    """Ошибка работы с кэшем"""
    
    def __init__(self, message: str, operation: Optional[str] = None):
        super().__init__(message, "CACHE_ERROR")
        self.operation = operation


class ConfigurationError(EasyPassBotError):
    """Ошибка конфигурации"""
    
    def __init__(self, message: str, config_key: Optional[str] = None):
        super().__init__(message, "CONFIGURATION_ERROR")
        self.config_key = config_key
