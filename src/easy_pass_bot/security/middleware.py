"""
Security middleware для Easy Pass Bot
"""
import time
import logging
from typing import Callable, Any
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from .rate_limiter import rate_limiter
from .validator import validator
from .audit_logger import audit_logger

logger = logging.getLogger(__name__)

class SecurityMiddleware(BaseMiddleware):
    """Middleware для проверки безопасности"""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Any],
        event: TelegramObject,
        data: dict[str, Any]
    ) -> Any:
        """Обработка события через security middleware"""
        
        # Получаем информацию о пользователе
        user_id = None
        if hasattr(event, 'from_user') and event.from_user:
            user_id = event.from_user.id
        
        if user_id is None:
            logger.warning("Security middleware: No user ID found")
            return await handler(event, data)
        
        # Проверка rate limiting
        if not await rate_limiter.is_allowed(user_id):
            logger.warning(f"Rate limit exceeded for user {user_id}")
            if hasattr(event, 'answer'):
                await event.answer("⏰ Слишком много запросов. Попробуйте позже.")
            return
        
        # Валидация Telegram ID
        is_valid, error = validator.validate_telegram_id(user_id)
        if not is_valid:
            logger.warning(f"Invalid Telegram ID: {user_id}, error: {error}")
            if hasattr(event, 'answer'):
                await event.answer("❌ Ошибка валидации")
            return
        
        # Логирование запроса
        audit_logger.log_user_action(user_id, "request", {
            "event_type": type(event).__name__,
            "timestamp": time.time()
        })
        
        # Продолжаем обработку
        return await handler(event, data)

class InputValidationMiddleware(BaseMiddleware):
    """Middleware для валидации входных данных"""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Any],
        event: TelegramObject,
        data: dict[str, Any]
    ) -> Any:
        """Валидация входных данных"""
        
        # Валидация текстовых сообщений
        if hasattr(event, 'text') and event.text:
            is_valid, error = validator.validate_text(event.text)
            if not is_valid:
                logger.warning(f"Invalid text input: {error}")
                if hasattr(event, 'answer'):
                    await event.answer("❌ Некорректный ввод")
                return
        
        # Валидация callback данных
        if hasattr(event, 'data') and event.data:
            is_valid, error = validator.validate_callback_data(event.data)
            if not is_valid:
                logger.warning(f"Invalid callback data: {error}")
                if hasattr(event, 'answer'):
                    await event.answer("❌ Некорректные данные")
                return
        
        return await handler(event, data)
