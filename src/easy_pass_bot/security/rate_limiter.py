"""
Ограничитель частоты запросов для защиты от спама и атак
"""
import asyncio
import time
from collections import defaultdict
from typing import Dict, List, Optional
import logging
logger = logging.getLogger(__name__)

class RateLimiter:
    """Ограничитель частоты запросов"""
    def __init__(self, max_requests: int = 10, window: int = 60):
        """
        Инициализация ограничителя
        Args:
            max_requests: Максимальное количество запросов в окне
            window: Временное окно в секундах
        """
        self.max_requests = max_requests
        self.window = window
        self.requests: Dict[int, List[float]] = defaultdict(list)
        self.blocked_users: Dict[int, float] = {}  # user_id -> block_until_timestamp
        self._lock = asyncio.Lock()
    async def is_allowed(self, user_id: int) -> bool:
        """
        Проверка, разрешен ли запрос для пользователя
        Args:
            user_id: ID пользователя Telegram
        Returns:
            True если запрос разрешен, False если заблокирован
        """
        async with self._lock:
            now = time.time()
            # Проверяем, не заблокирован ли пользователь
            if user_id in self.blocked_users:
                if now < self.blocked_users[user_id]:
                    logger.warning(f"User {user_id} is blocked until {self.blocked_users[user_id]}")
                    return False
                else:
                    # Блокировка истекла
                    del self.blocked_users[user_id]
            # Получаем список запросов пользователя
            user_requests = self.requests[user_id]
            # Очищаем старые запросы
            user_requests[:] = [req_time for req_time in user_requests
                               if now - req_time < self.window]
            # Проверяем лимит
            if len(user_requests) >= self.max_requests:
                # Блокируем пользователя на время окна
                self.blocked_users[user_id] = now + self.window
                logger.warning(f"User {user_id} blocked for {self.window} seconds due to rate limit")
                return False
            # Добавляем текущий запрос
            user_requests.append(now)
            return True
    def get_remaining_requests(self, user_id: int) -> int:
        """
        Получение количества оставшихся запросов для пользователя
        Args:
            user_id: ID пользователя Telegram
        Returns:
            Количество оставшихся запросов
        """
        now = time.time()
        user_requests = self.requests[user_id]
        # Очищаем старые запросы
        user_requests[:] = [req_time for req_time in user_requests
                           if now - req_time < self.window]
        return max(0, self.max_requests - len(user_requests))
    def get_block_time_remaining(self, user_id: int) -> Optional[float]:
        """
        Получение оставшегося времени блокировки
        Args:
            user_id: ID пользователя Telegram
        Returns:
            Оставшееся время блокировки в секундах или None если не заблокирован
        """
        if user_id not in self.blocked_users:
            return None
        remaining = self.blocked_users[user_id] - time.time()
        return max(0, remaining) if remaining > 0 else None
    def reset_user_limit(self, user_id: int):
        """
        Сброс лимита для пользователя (для административных целей)
        Args:
            user_id: ID пользователя Telegram
        """
        if user_id in self.requests:
            del self.requests[user_id]
        if user_id in self.blocked_users:
            del self.blocked_users[user_id]
        logger.info(f"Rate limit reset for user {user_id}")
    def get_stats(self) -> Dict[str, any]:
        """
        Получение статистики по ограничителю
        Returns:
            Словарь со статистикой
        """
        now = time.time()
        active_users = 0
        blocked_users = 0
        for user_requests in self.requests.values():
            # Очищаем старые запросы
            user_requests[:] = [req_time for req_time in user_requests
                               if now - req_time < self.window]
            if user_requests:
                active_users += 1
        # Очищаем истекшие блокировки
        expired_blocks = [uid for uid, block_until in self.blocked_users.items()
                         if now >= block_until]
        for uid in expired_blocks:
            del self.blocked_users[uid]
        blocked_users = len(self.blocked_users)
        return {
            'active_users': active_users,
            'blocked_users': blocked_users,
            'max_requests_per_window': self.max_requests,
            'window_seconds': self.window
        }
# Глобальный экземпляр ограничителя
rate_limiter = RateLimiter(max_requests=15, window=60)  # 15 запросов в минуту
