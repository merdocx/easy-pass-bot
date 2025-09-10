"""
Circuit Breaker для предотвращения каскадных сбоев
"""
import asyncio
import time
import logging
from typing import Callable, Any, Optional
from enum import Enum
from datetime import datetime, timedelta
logger = logging.getLogger(__name__)

class CircuitState(Enum):
    """Состояния Circuit Breaker"""
    CLOSED = "closed"      # Нормальная работа
    OPEN = "open"          # Блокировка
    HALF_OPEN = "half_open"  # Тестирование

class CircuitBreaker:
    """Circuit Breaker для предотвращения каскадных сбоев"""
    def __init__(self, failure_threshold: int = 5, timeout: float = 60.0,
                 success_threshold: int = 3, name: str = "default"):
        """
        Инициализация Circuit Breaker
        Args:
            failure_threshold: Порог количества неудач для открытия
            timeout: Время блокировки в секундах
            success_threshold: Количество успешных вызовов для закрытия
            name: Имя Circuit Breaker для логирования
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.success_threshold = success_threshold
        self.name = name
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        self.cb_logger = logging.getLogger(f'circuit_breaker.{name}')
        self._lock = asyncio.Lock()
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Выполнение функции через Circuit Breaker
        Args:
            func: Функция для выполнения
            *args: Позиционные аргументы
            **kwargs: Именованные аргументы
        Returns:
            Результат выполнения функции
        Raises:
            Exception: Если Circuit Breaker открыт или функция не выполнилась
        """
        async with self._lock:
            # Проверяем состояние
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    self.cb_logger.info(f"Circuit breaker {self.name} transitioning to HALF_OPEN")
                else:
                    raise Exception(f"Circuit breaker {self.name} is OPEN")
            elif self.state == CircuitState.HALF_OPEN:
                # В состоянии HALF_OPEN разрешаем только ограниченное количество вызовов
                pass
        try:
            # Выполняем функцию
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            # Успешное выполнение
            await self._on_success()
            return result
        except Exception as e:
            # Неудачное выполнение
            await self._on_failure()
            raise e
    def _should_attempt_reset(self) -> bool:
        """Проверка, можно ли попытаться сбросить Circuit Breaker"""
        if self.last_failure_time is None:
            return True
        return time.time() - self.last_failure_time >= self.timeout
    async def _on_success(self):
        """Обработка успешного выполнения"""
        async with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                self.cb_logger.info(
                    f"Circuit breaker {self.name} success count: {self.success_count}/{self.success_threshold}"
                )
                if self.success_count >= self.success_threshold:
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    self.success_count = 0
                    self.cb_logger.info(f"Circuit breaker {self.name} transitioning to CLOSED")
            elif self.state == CircuitState.CLOSED:
                # Сбрасываем счетчик неудач при успешном выполнении
                self.failure_count = 0
    async def _on_failure(self):
        """Обработка неудачного выполнения"""
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            self.cb_logger.warning(
                f"Circuit breaker {self.name} failure count: {self.failure_count}/{self.failure_threshold}"
            )
            if self.state == CircuitState.HALF_OPEN:
                # В состоянии HALF_OPEN любая неудача возвращает в OPEN
                self.state = CircuitState.OPEN
                self.success_count = 0
                self.cb_logger.warning(f"Circuit breaker {self.name} transitioning to OPEN")
            elif self.state == CircuitState.CLOSED and self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                self.cb_logger.error(f"Circuit breaker {self.name} transitioning to OPEN")
    def get_state(self) -> CircuitState:
        """Получение текущего состояния"""
        return self.state
    def get_stats(self) -> dict:
        """
        Получение статистики Circuit Breaker
        Returns:
            Словарь со статистикой
        """
        return {
            'name': self.name,
            'state': self.state.value,
            'failure_count': self.failure_count,
            'success_count': self.success_count,
            'last_failure_time': self.last_failure_time,
            'failure_threshold': self.failure_threshold,
            'success_threshold': self.success_threshold,
            'timeout': self.timeout
        }
    def reset(self):
        """Сброс Circuit Breaker в исходное состояние"""
        async def _reset():
            async with self._lock:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
                self.last_failure_time = None
                self.cb_logger.info(f"Circuit breaker {self.name} reset to CLOSED")
        # Выполняем сброс асинхронно
        asyncio.create_task(_reset())
    def is_available(self) -> bool:
        """Проверка доступности Circuit Breaker"""
        if self.state == CircuitState.CLOSED:
            return True
        elif self.state == CircuitState.HALF_OPEN:
            return True
        else:  # OPEN
            return self._should_attempt_reset()

class CircuitBreakerManager:
    """Менеджер для управления несколькими Circuit Breaker"""
    def __init__(self):
        self.breakers: dict = {}
        self.manager_logger = logging.getLogger('circuit_breaker_manager')
    def get_breaker(self, name: str, **kwargs) -> CircuitBreaker:
        """
        Получение или создание Circuit Breaker
        Args:
            name: Имя Circuit Breaker
            **kwargs: Параметры для создания Circuit Breaker
        Returns:
            Экземпляр Circuit Breaker
        """
        if name not in self.breakers:
            self.breakers[name] = CircuitBreaker(name=name, **kwargs)
            self.manager_logger.info(f"Created circuit breaker: {name}")
        return self.breakers[name]
    def get_all_stats(self) -> dict:
        """
        Получение статистики всех Circuit Breaker
        Returns:
            Словарь со статистикой всех Circuit Breaker
        """
        return {
            name: breaker.get_stats()
            for name, breaker in self.breakers.items()
        }
    def reset_all(self):
        """Сброс всех Circuit Breaker"""
        for breaker in self.breakers.values():
            breaker.reset()
        self.manager_logger.info("Reset all circuit breakers")
    def reset(self, name: str):
        """Сброс конкретного Circuit Breaker"""
        if name in self.breakers:
            self.breakers[name].reset()
            self.manager_logger.info(f"Reset circuit breaker: {name}")
# Глобальный менеджер Circuit Breaker
circuit_breaker_manager = CircuitBreakerManager()
