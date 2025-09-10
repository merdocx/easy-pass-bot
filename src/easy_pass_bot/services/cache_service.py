"""
Сервис кэширования для улучшения производительности
"""
import json
import time
import asyncio
import logging
from typing import Any, Optional, Dict, Union, Callable
from functools import wraps
from datetime import datetime, timedelta
import hashlib
logger = logging.getLogger(__name__)

class CacheService:
    """Сервис кэширования с поддержкой TTL и инвалидации"""
    def __init__(self, default_ttl: int = 300):
        """
        Инициализация сервиса кэширования
        Args:
            default_ttl: Время жизни кэша по умолчанию в секундах
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
        self._lock = asyncio.Lock()
        self._cleanup_task = None
        # Задача будет запущена при первом использовании
    def _start_cleanup_task(self):
        """Запуск задачи очистки устаревших записей"""
        if self._cleanup_task is None or self._cleanup_task.done():
            try:
                self._cleanup_task = asyncio.create_task(self._cleanup_expired())
            except RuntimeError:
                # Нет активного event loop, запустим позже
                logger.debug("No event loop available for cleanup task")
    async def _cleanup_expired(self):
        """Очистка устаревших записей из кэша"""
        while True:
            try:
                await asyncio.sleep(60)  # Проверяем каждую минуту
                current_time = time.time()
                async with self._lock:
                    expired_keys = [
                        key for key, data in self.cache.items()
                        if data.get('expires_at', 0) < current_time
                    ]
                    for key in expired_keys:
                        del self.cache[key]
                    if expired_keys:
                        logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
            except Exception as e:
                logger.error("Error in cache cleanup: {e}")
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """
        Генерация ключа кэша
        Args:
            prefix: Префикс ключа
            *args: Позиционные аргументы
            **kwargs: Именованные аргументы
        Returns:
            Сгенерированный ключ
        """
        # Создаем строку из аргументов
        key_data = f"{prefix}:{str(args)}:{str(sorted(kwargs.items()))}"
        # Хэшируем для получения короткого ключа
        return hashlib.md5(key_data.encode()).hexdigest()
    async def get(self, key: str) -> Optional[Any]:
        """
        Получение значения из кэша
        Args:
            key: Ключ кэша
        Returns:
            Значение из кэша или None
        """
        # Запускаем задачу очистки при первом использовании
        if self._cleanup_task is None:
            self._start_cleanup_task()
        async with self._lock:
            if key not in self.cache:
                return None
            data = self.cache[key]
            # Проверяем, не истек ли срок действия
            if data.get('expires_at', 0) < time.time():
                del self.cache[key]
                return None
            # Увеличиваем счетчик обращений
            data['access_count'] = data.get('access_count', 0) + 1
            data['last_accessed'] = time.time()
            return data['value']
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Сохранение значения в кэш
        Args:
            key: Ключ кэша
            value: Значение для сохранения
            ttl: Время жизни в секундах (по умолчанию используется default_ttl)
        Returns:
            True если значение сохранено успешно
        """
        try:
            ttl = ttl or self.default_ttl
            expires_at = time.time() + ttl
            async with self._lock:
                self.cache[key] = {
                    'value': value,
                    'expires_at': expires_at,
                    'created_at': time.time(),
                    'access_count': 0,
                    'last_accessed': time.time()
                }
            logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.error("Error setting cache key {key}: {e}")
            return False
    async def delete(self, key: str) -> bool:
        """
        Удаление значения из кэша
        Args:
            key: Ключ кэша
        Returns:
            True если значение удалено успешно
        """
        async with self._lock:
            if key in self.cache:
                del self.cache[key]
                logger.debug(f"Cache deleted: {key}")
                return True
            return False
    async def clear(self) -> int:
        """
        Очистка всего кэша
        Returns:
            Количество удаленных записей
        """
        async with self._lock:
            count = len(self.cache)
            self.cache.clear()
            logger.info("Cache cleared: {count} entries removed")
            return count
    async def get_or_set(self, key: str, factory: Callable, ttl: Optional[int] = None) -> Any:
        """
        Получение значения из кэша или создание нового
        Args:
            key: Ключ кэша
            factory: Функция для создания значения
            ttl: Время жизни в секундах
        Returns:
            Значение из кэша или новое значение
        """
        # Пытаемся получить из кэша
        cached_value = await self.get(key)
        if cached_value is not None:
            return cached_value
        # Создаем новое значение
        try:
            if asyncio.iscoroutinefunction(factory):
                new_value = await factory()
            else:
                new_value = factory()
            # Сохраняем в кэш
            await self.set(key, new_value, ttl)
            return new_value
        except Exception as e:
            logger.error("Error in get_or_set for key {key}: {e}")
            raise
    async def invalidate_pattern(self, pattern: str) -> int:
        """
        Инвалидация записей по паттерну
        Args:
            pattern: Паттерн для поиска ключей
        Returns:
            Количество удаленных записей
        """
        import re
        async with self._lock:
            keys_to_delete = [
                key for key in self.cache.keys()
                if re.search(pattern, key)
            ]
            for key in keys_to_delete:
                del self.cache[key]
            logger.info("Invalidated {len(keys_to_delete)} cache entries matching pattern: {pattern}")
            return len(keys_to_delete)
    async def get_stats(self) -> Dict[str, Any]:
        """
        Получение статистики кэша
        Returns:
            Словарь со статистикой
        """
        async with self._lock:
            current_time = time.time()
            total_entries = len(self.cache)
            # Подсчитываем статистику
            total_accesses = 0
            expired_entries = 0
            oldest_entry = None
            newest_entry = None
            for data in self.cache.values():
                total_accesses += data.get('access_count', 0)
                if data.get('expires_at', 0) < current_time:
                    expired_entries += 1
                created_at = data.get('created_at', 0)
                if oldest_entry is None or created_at < oldest_entry:
                    oldest_entry = created_at
                if newest_entry is None or created_at > newest_entry:
                    newest_entry = created_at
            return {
                'total_entries': total_entries,
                'total_accesses': total_accesses,
                'expired_entries': expired_entries,
                'hit_rate': total_accesses / max(total_entries, 1),
                'oldest_entry_age': current_time - oldest_entry if oldest_entry else 0,
                'newest_entry_age': current_time - newest_entry if newest_entry else 0,
                'memory_usage_mb': len(str(self.cache)) / 1024 / 1024
            }
    def cached(self, ttl: Optional[int] = None, key_prefix: str = ""):
        """
        Декоратор для кэширования результатов функций
        Args:
            ttl: Время жизни кэша в секундах
            key_prefix: Префикс для ключа кэша
        Returns:
            Декоратор
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Генерируем ключ кэша
                cache_key = self._generate_key(
                    f"{key_prefix}:{func.__name__}",
                    *args,
                    **kwargs
                )
                # Пытаемся получить из кэша
                cached_result = await self.get(cache_key)
                if cached_result is not None:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return cached_result
                # Выполняем функцию
                try:
                    if asyncio.iscoroutinefunction(func):
                        result = await func(*args, **kwargs)
                    else:
                        result = func(*args, **kwargs)
                    # Сохраняем в кэш
                    await self.set(cache_key, result, ttl)
                    logger.debug(f"Cache miss for {func.__name__}, result cached")
                    return result
                except Exception as e:
                    logger.error("Error in cached function {func.__name__}: {e}")
                    raise
            return wrapper
        return decorator
    async def close(self):
        """Закрытие сервиса кэширования"""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
# Глобальный экземпляр сервиса кэширования
cache_service = CacheService(default_ttl=300)  # 5 минут по умолчанию
