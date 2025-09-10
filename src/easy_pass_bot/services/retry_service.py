"""
Сервис повторных попыток (Retry) для повышения надежности
"""
import asyncio
import logging
import random
from typing import Callable, Any, Optional, List, Type, Union
from datetime import datetime, timedelta
from enum import Enum
logger = logging.getLogger(__name__)

class RetryStrategy(Enum):
    """Стратегии повторных попыток"""
    FIXED = "fixed"           # Фиксированная задержка
    EXPONENTIAL = "exponential"  # Экспоненциальная задержка
    LINEAR = "linear"         # Линейная задержка
    RANDOM = "random"         # Случайная задержка

class RetryService:
    """Сервис повторных попыток"""
    def __init__(self, max_attempts: int = 3, base_delay: float = 1.0,
                 max_delay: float = 60.0, strategy: RetryStrategy = RetryStrategy.EXPONENTIAL):
        """
        Инициализация сервиса повторных попыток
        Args:
            max_attempts: Максимальное количество попыток
            base_delay: Базовая задержка в секундах
            max_delay: Максимальная задержка в секундах
            strategy: Стратегия задержки
        """
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.strategy = strategy
        self.retry_logger = logging.getLogger('retry_service')
    def calculate_delay(self, attempt: int) -> float:
        """
        Расчет задержки для попытки
        Args:
            attempt: Номер попытки (начиная с 0)
        Returns:
            Задержка в секундах
        """
        if attempt == 0:
            return 0
        if self.strategy == RetryStrategy.FIXED:
            delay = self.base_delay
        elif self.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.base_delay * (2 ** (attempt - 1))
        elif self.strategy == RetryStrategy.LINEAR:
            delay = self.base_delay * attempt
        elif self.strategy == RetryStrategy.RANDOM:
            delay = random.uniform(self.base_delay, self.base_delay * 2)
        else:
            delay = self.base_delay
        # Ограничиваем максимальной задержкой
        return min(delay, self.max_delay)
    async def execute_with_retry(self, func: Callable, *args,
                               retry_on: Optional[List[Type[Exception]]] = None,
                               **kwargs) -> Any:
        """
        Выполнение функции с повторными попытки
        Args:
            func: Функция для выполнения
            *args: Позиционные аргументы
            retry_on: Список типов исключений для повторных попыток
            **kwargs: Именованные аргументы
        Returns:
            Результат выполнения функции
        Raises:
            Exception: Последнее исключение после всех попыток
        """
        if retry_on is None:
            retry_on = [Exception]
        last_exception = None
        for attempt in range(self.max_attempts):
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                if attempt > 0:
                    self.retry_logger.info(f"Function {func.__name__} succeeded on attempt {attempt + 1}")
                return result
            except Exception as e:
                last_exception = e
                # Проверяем, нужно ли повторять попытку
                should_retry = any(isinstance(e, exc_type) for exc_type in retry_on)
                if not should_retry or attempt == self.max_attempts - 1:
                    if attempt == self.max_attempts - 1:
                        self.retry_logger.error(
                            f"Function {func.__name__} failed after {self.max_attempts} attempts. "
                            f"Last error: {e}"
                        )
                    break
                # Рассчитываем задержку
                delay = self.calculate_delay(attempt)
                self.retry_logger.warning(
                    f"Function {func.__name__} failed on attempt {attempt + 1}: {e}. "
                    f"Retrying in {delay:.2f} seconds..."
                )
                if delay > 0:
                    await asyncio.sleep(delay)
        # Если дошли сюда, все попытки исчерпаны
        raise last_exception
    def retry(self, max_attempts: Optional[int] = None,
              base_delay: Optional[float] = None,
              max_delay: Optional[float] = None,
              strategy: Optional[RetryStrategy] = None,
              retry_on: Optional[List[Type[Exception]]] = None):
        """
        Декоратор для повторных попыток
        Args:
            max_attempts: Максимальное количество попыток
            base_delay: Базовая задержка в секундах
            max_delay: Максимальная задержка в секундах
            strategy: Стратегия задержки
            retry_on: Список типов исключений для повторных попыток
        Returns:
            Декоратор
        """
        def decorator(func: Callable) -> Callable:
            async def wrapper(*args, **kwargs):
                # Используем переданные параметры или значения по умолчанию
                retry_max_attempts = max_attempts or self.max_attempts
                retry_base_delay = base_delay or self.base_delay
                retry_max_delay = max_delay or self.max_delay
                retry_strategy = strategy or self.strategy
                retry_exceptions = retry_on or [Exception]
                # Создаем временный экземпляр сервиса с новыми параметрами
                temp_service = RetryService(
                    max_attempts=retry_max_attempts,
                    base_delay=retry_base_delay,
                    max_delay=retry_max_delay,
                    strategy=retry_strategy
                )
                return await temp_service.execute_with_retry(
                    func, *args, retry_on=retry_exceptions, **kwargs
                )
            return wrapper
        return decorator
    async def execute_with_circuit_breaker(self, func: Callable, *args,
                                         failure_threshold: int = 5,
                                         timeout: float = 60.0,
                                         **kwargs) -> Any:
        """
        Выполнение функции с circuit breaker
        Args:
            func: Функция для выполнения
            *args: Позиционные аргументы
            failure_threshold: Порог количества неудач
            timeout: Время блокировки в секундах
            **kwargs: Именованные аргументы
        Returns:
            Результат выполнения функции
        """
        from .circuit_breaker import CircuitBreaker
        circuit_breaker = CircuitBreaker(
            failure_threshold=failure_threshold,
            timeout=timeout
        )
        return await circuit_breaker.call(func, *args, **kwargs)
    def get_retry_stats(self) -> dict:
        """
        Получение статистики повторных попыток
        Returns:
            Словарь со статистикой
        """
        return {
            'max_attempts': self.max_attempts,
            'base_delay': self.base_delay,
            'max_delay': self.max_delay,
            'strategy': self.strategy.value
        }
# Глобальный экземпляр сервиса повторных попыток
retry_service = RetryService(
    max_attempts=3,
    base_delay=1.0,
    max_delay=30.0,
    strategy=RetryStrategy.EXPONENTIAL
)
