"""
Базовые классы для компонентов системы
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
import logging
from datetime import datetime

from .interfaces import ILogger, IErrorHandler
from .exceptions import EasyPassBotError


class BaseService(ABC):
    """Базовый класс для всех сервисов"""
    
    def __init__(
        self, 
        logger: Optional[ILogger] = None,
        error_handler: Optional[IErrorHandler] = None
    ):
        self.logger = logger or self._get_default_logger()
        self.error_handler = error_handler
        self._initialized = False
    
    def _get_default_logger(self) -> ILogger:
        """Получить логгер по умолчанию"""
        return DefaultLogger(self.__class__.__name__)
    
    async def initialize(self) -> None:
        """Инициализация сервиса"""
        if not self._initialized:
            await self._do_initialize()
            self._initialized = True
            self.logger.info(f"{self.__class__.__name__} initialized")
    
    @abstractmethod
    async def _do_initialize(self) -> None:
        """Выполнить инициализацию сервиса"""
        pass
    
    async def cleanup(self) -> None:
        """Очистка ресурсов сервиса"""
        if self._initialized:
            await self._do_cleanup()
            self._initialized = False
            self.logger.info(f"{self.__class__.__name__} cleaned up")
    
    @abstractmethod
    async def _do_cleanup(self) -> None:
        """Выполнить очистку ресурсов"""
        pass
    
    async def _handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """Обработать ошибку"""
        if self.error_handler:
            await self.error_handler.handle_error(error, context)
        else:
            self.logger.error(f"Unhandled error: {error}", extra=context)


class BaseRepository(BaseService):
    """Базовый класс для репозиториев"""
    
    def __init__(
        self, 
        logger: Optional[ILogger] = None,
        error_handler: Optional[IErrorHandler] = None
    ):
        super().__init__(logger, error_handler)
        self._cache = {}
    
    async def _do_initialize(self) -> None:
        """Инициализация репозитория"""
        pass
    
    async def _do_cleanup(self) -> None:
        """Очистка репозитория"""
        self._cache.clear()
    
    def _get_cache_key(self, prefix: str, **kwargs) -> str:
        """Получить ключ кэша"""
        key_parts = [prefix]
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}:{v}")
        return ":".join(key_parts)
    
    async def _execute_with_retry(
        self, 
        operation, 
        max_retries: int = 3,
        **kwargs
    ) -> Any:
        """Выполнить операцию с повторными попытками"""
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                return await operation(**kwargs)
            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    self.logger.warning(
                        f"Operation failed (attempt {attempt + 1}/{max_retries + 1}): {e}"
                    )
                    await self._wait_before_retry(attempt)
                else:
                    self.logger.error(f"Operation failed after {max_retries + 1} attempts: {e}")
        
        raise last_error
    
    async def _wait_before_retry(self, attempt: int) -> None:
        """Ожидание перед повторной попыткой"""
        import asyncio
        wait_time = 2 ** attempt  # Экспоненциальная задержка
        await asyncio.sleep(wait_time)


class BaseValidator(BaseService):
    """Базовый класс для валидаторов"""
    
    def __init__(
        self, 
        logger: Optional[ILogger] = None,
        error_handler: Optional[IErrorHandler] = None
    ):
        super().__init__(logger, error_handler)
        self._errors: List[str] = []
    
    async def _do_initialize(self) -> None:
        """Инициализация валидатора"""
        pass
    
    async def _do_cleanup(self) -> None:
        """Очистка валидатора"""
        self._errors.clear()
    
    def add_error(self, error: str) -> None:
        """Добавить ошибку валидации"""
        self._errors.append(error)
    
    def get_errors(self) -> List[str]:
        """Получить список ошибок"""
        return self._errors.copy()
    
    def clear_errors(self) -> None:
        """Очистить список ошибок"""
        self._errors.clear()
    
    def has_errors(self) -> bool:
        """Проверить наличие ошибок"""
        return len(self._errors) > 0


class DefaultLogger(ILogger):
    """Реализация логгера по умолчанию"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def info(self, message: str, **kwargs) -> None:
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        self.logger.error(message, extra=kwargs)
    
    def debug(self, message: str, **kwargs) -> None:
        self.logger.debug(message, extra=kwargs)


class BaseEntity:
    """Базовый класс для сущностей"""
    
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразовать в словарь"""
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
    
    def __repr__(self) -> str:
        attrs = ', '.join(f"{k}={v}" for k, v in self.to_dict().items())
        return f"{self.__class__.__name__}({attrs})"




