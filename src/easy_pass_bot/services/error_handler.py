"""
Централизованная система обработки ошибок
"""
import logging
import asyncio
import traceback
from typing import Any, Optional, Dict, Callable, Type
from datetime import datetime
from enum import Enum
logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """Уровни серьезности ошибок"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class BotError(Exception):
    """Базовый класс для ошибок бота"""
    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.severity = severity
        self.error_code = error_code
        self.details = details or {}
        self.timestamp = datetime.utcnow()
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование ошибки в словарь"""
        return {
            'message': self.message,
            'severity': self.severity.value,
            'error_code': self.error_code,
            'details': self.details,
            'timestamp': self.timestamp.isoformat(),
            'type': self.__class__.__name__
        }

class ValidationError(BotError):
    """Ошибка валидации данных"""
    def __init__(self, message: str, field: Optional[str] = None,
                 value: Optional[Any] = None, **kwargs):
        super().__init__(message, ErrorSeverity.LOW, "VALIDATION_ERROR", **kwargs)
        self.field = field
        self.value = value
        self.details.update({
            'field': field,
            'value': str(value) if value is not None else None
        })

class DatabaseError(BotError):
    """Ошибка базы данных"""
    def __init__(self, message: str, operation: Optional[str] = None,
                 table: Optional[str] = None, **kwargs):
        super().__init__(message, ErrorSeverity.HIGH, "DATABASE_ERROR", **kwargs)
        self.operation = operation
        self.table = table
        self.details.update({
            'operation': operation,
            'table': table
        })

class RateLimitError(BotError):
    """Ошибка превышения лимита запросов"""
    def __init__(self, message: str, user_id: Optional[int] = None,
                 retry_after: Optional[int] = None, **kwargs):
        super().__init__(message, ErrorSeverity.MEDIUM, "RATE_LIMIT_ERROR", **kwargs)
        self.user_id = user_id
        self.retry_after = retry_after
        self.details.update({
            'user_id': user_id,
            'retry_after': retry_after
        })

class SecurityError(BotError):
    """Ошибка безопасности"""
    def __init__(self, message: str, user_id: Optional[int] = None,
                 action: Optional[str] = None, **kwargs):
        super().__init__(message, ErrorSeverity.HIGH, "SECURITY_ERROR", **kwargs)
        self.user_id = user_id
        self.action = action
        self.details.update({
            'user_id': user_id,
            'action': action
        })

class ExternalServiceError(BotError):
    """Ошибка внешнего сервиса"""
    def __init__(self, message: str, service: Optional[str] = None,
                 status_code: Optional[int] = None, **kwargs):
        super().__init__(message, ErrorSeverity.MEDIUM, "EXTERNAL_SERVICE_ERROR", **kwargs)
        self.service = service
        self.status_code = status_code
        self.details.update({
            'service': service,
            'status_code': status_code
        })

class ErrorHandler:
    """Централизованный обработчик ошибок"""
    def __init__(self):
        self.error_handlers: Dict[Type[Exception], Callable] = {}
        self.fallback_handler: Optional[Callable] = None
        self.error_logger = logging.getLogger('error_handler')
        # Настройка обработчиков по умолчанию
        self._setup_default_handlers()
    def _setup_default_handlers(self):
        """Настройка обработчиков ошибок по умолчанию"""
        self.register_handler(ValidationError, self._handle_validation_error)
        self.register_handler(DatabaseError, self._handle_database_error)
        self.register_handler(RateLimitError, self._handle_rate_limit_error)
        self.register_handler(SecurityError, self._handle_security_error)
        self.register_handler(ExternalServiceError, self._handle_external_service_error)
        self.register_handler(Exception, self._handle_generic_error)
    def register_handler(self, exception_type: Type[Exception],
                        handler: Callable[[Exception], Any]):
        """
        Регистрация обработчика для типа ошибки
        Args:
            exception_type: Тип исключения
            handler: Функция-обработчик
        """
        self.error_handlers[exception_type] = handler
        logger.debug(f"Registered error handler for {exception_type.__name__}")
    def set_fallback_handler(self, handler: Callable[[Exception], Any]):
        """
        Установка обработчика по умолчанию
        Args:
            handler: Функция-обработчик по умолчанию
        """
        self.fallback_handler = handler
        logger.debug("Set fallback error handler")
    async def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> Any:
        """
        Обработка ошибки
        Args:
            error: Исключение для обработки
            context: Дополнительный контекст
        Returns:
            Результат обработки ошибки
        """
        # Логируем ошибку
        self._log_error(error, context)
        # Ищем подходящий обработчик
        handler = self._find_handler(error)
        if handler:
            try:
                if asyncio.iscoroutinefunction(handler):
                    return await handler(error)
                else:
                    return handler(error)
            except Exception as handler_error:
                logger.error(f"Error in error handler: {handler_error}")
                return await self._handle_fallback(error)
        else:
            return await self._handle_fallback(error)
    def _find_handler(self, error: Exception) -> Optional[Callable]:
        """Поиск подходящего обработчика для ошибки"""
        # Ищем точное совпадение типа
        if type(error) in self.error_handlers:
            return self.error_handlers[type(error)]
        # Ищем по базовым классам
        for exception_type, handler in self.error_handlers.items():
            if isinstance(error, exception_type):
                return handler
        return None
    async def _handle_fallback(self, error: Exception) -> Any:
        """Обработка ошибки через fallback handler"""
        if self.fallback_handler:
            try:
                if asyncio.iscoroutinefunction(self.fallback_handler):
                    return await self.fallback_handler(error)
                else:
                    return self.fallback_handler(error)
            except Exception as fallback_error:
                logger.error(f"Error in fallback handler: {fallback_error}")
        # Последний резерв - простое логирование
        logger.critical(f"Unhandled error: {error}")
        return None
    def _log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None):
        """Логирование ошибки"""
        error_data = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc(),
            'context': context or {},
            'timestamp': datetime.utcnow().isoformat()
        }
        # Если это наша ошибка, добавляем дополнительные данные
        if isinstance(error, BotError):
            error_data.update(error.to_dict())
            severity = error.severity
        else:
            severity = ErrorSeverity.MEDIUM
        # Логируем в зависимости от серьезности
        if severity == ErrorSeverity.CRITICAL:
            self.error_logger.critical(f"CRITICAL ERROR: {error_data}")
        elif severity == ErrorSeverity.HIGH:
            self.error_logger.error(f"HIGH SEVERITY ERROR: {error_data}")
        elif severity == ErrorSeverity.MEDIUM:
            self.error_logger.warning(f"MEDIUM SEVERITY ERROR: {error_data}")
        else:
            self.error_logger.info(f"LOW SEVERITY ERROR: {error_data}")
    def _handle_validation_error(self, error: ValidationError) -> str:
        """Обработка ошибки валидации"""
        return f"❌ Ошибка валидации: {error.message}"
    def _handle_database_error(self, error: DatabaseError) -> str:
        """Обработка ошибки базы данных"""
        logger.error(f"Database error: {error.message}")
        return "❌ Ошибка базы данных. Попробуйте позже."
    def _handle_rate_limit_error(self, error: RateLimitError) -> str:
        """Обработка ошибки превышения лимита"""
        if error.retry_after:
            return f"⏳ Слишком много запросов. Попробуйте через {error.retry_after} секунд."
        return "⏳ Слишком много запросов. Попробуйте позже."
    def _handle_security_error(self, error: SecurityError) -> str:
        """Обработка ошибки безопасности"""
        logger.warning(f"Security error: {error.message}")
        return "❌ Ошибка безопасности. Обратитесь к администратору."
    def _handle_external_service_error(self, error: ExternalServiceError) -> str:
        """Обработка ошибки внешнего сервиса"""
        logger.error(f"External service error: {error.message}")
        return "❌ Временная недоступность сервиса. Попробуйте позже."
    def _handle_generic_error(self, error: Exception) -> str:
        """Обработка общей ошибки"""
        logger.error(f"Generic error: {error}")
        return "❌ Произошла неожиданная ошибка. Попробуйте позже."
    def create_error_response(self, error: Exception,
                            user_friendly: bool = True) -> Dict[str, Any]:
        """
        Создание ответа об ошибке
        Args:
            error: Исключение
            user_friendly: Создавать ли дружелюбное сообщение для пользователя
        Returns:
            Словарь с информацией об ошибке
        """
        response = {
            'success': False,
            'error_type': type(error).__name__,
            'timestamp': datetime.utcnow().isoformat()
        }
        if user_friendly:
            if isinstance(error, BotError):
                response['message'] = error.message
                response['error_code'] = error.error_code
            else:
                response['message'] = "Произошла неожиданная ошибка"
        else:
            response['message'] = str(error)
            response['traceback'] = traceback.format_exc()
        return response
# Глобальный экземпляр обработчика ошибок
error_handler = ErrorHandler()
