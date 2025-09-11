"""
Сервис уведомлений
"""
import asyncio
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup

from ..core.base import BaseService
from ..core.interfaces import INotificationService
from ..core.exceptions import NotificationError, ConfigurationError
from ..config import BOT_TOKEN, MESSAGES


class NotificationService(BaseService, INotificationService):
    """Сервис уведомлений"""
    
    def __init__(
        self, 
        bot_token: Optional[str] = None,
        logger: Optional[Any] = None,
        error_handler: Optional[Any] = None
    ):
        super().__init__(logger, error_handler)
        self.bot_token = bot_token or BOT_TOKEN
        self._bot: Optional[Bot] = None
        self._notification_queue: List[Dict[str, Any]] = []
        self._max_queue_size = 1000
        self._processing = False
    
    async def _do_initialize(self) -> None:
        """Инициализация сервиса уведомлений"""
        if not self.bot_token:
            raise ConfigurationError("Bot token is required")
        
        self._bot = Bot(
            token=self.bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        
        # Запускаем обработку очереди уведомлений
        asyncio.create_task(self._process_notification_queue())
        
        self.logger.info("Notification service initialized")
    
    async def _do_cleanup(self) -> None:
        """Очистка сервиса уведомлений"""
        self._processing = False
        
        if self._bot:
            await self._bot.session.close()
            self._bot = None
        
        self.logger.info("Notification service cleaned up")
    
    async def send_notification(
        self, 
        user_id: int, 
        message: str, 
        keyboard: Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup]] = None
    ) -> bool:
        """Отправить уведомление пользователю"""
        try:
            if not self._bot:
                raise NotificationError("Bot not initialized")
            
            await self._bot.send_message(
                chat_id=user_id,
                text=message,
                reply_markup=keyboard
            )
            
            self.logger.info(f"Notification sent to user {user_id}")
            return True
            
        except Exception as e:
            error_msg = f"Failed to send notification to user {user_id}: {e}"
            self.logger.error(error_msg)
            
            # Добавляем в очередь для повторной отправки
            await self._add_to_queue(user_id, message, keyboard)
            
            raise NotificationError(error_msg, user_id=user_id)
    
    async def notify_admins(self, message: str) -> bool:
        """Уведомить администраторов"""
        try:
            # Получаем список администраторов
            admin_ids = await self._get_admin_ids()
            
            if not admin_ids:
                self.logger.warning("No admin users found")
                return False
            
            success_count = 0
            for admin_id in admin_ids:
                try:
                    await self.send_notification(admin_id, message)
                    success_count += 1
                except Exception as e:
                    self.logger.error(f"Failed to notify admin {admin_id}: {e}")
            
            self.logger.info(f"Notified {success_count}/{len(admin_ids)} admins")
            return success_count > 0
            
        except Exception as e:
            error_msg = f"Failed to notify admins: {e}"
            self.logger.error(error_msg)
            raise NotificationError(error_msg)
    
    async def send_bulk_notifications(
        self, 
        notifications: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Отправить массовые уведомления"""
        results = {
            'sent': 0,
            'failed': 0,
            'queued': 0
        }
        
        for notification in notifications:
            try:
                user_id = notification.get('user_id')
                message = notification.get('message')
                keyboard = notification.get('keyboard')
                
                if not user_id or not message:
                    results['failed'] += 1
                    continue
                
                await self.send_notification(user_id, message, keyboard)
                results['sent'] += 1
                
            except Exception as e:
                self.logger.error(f"Failed to send bulk notification: {e}")
                results['failed'] += 1
        
        self.logger.info(f"Bulk notifications sent: {results}")
        return results
    
    async def send_delayed_notification(
        self, 
        user_id: int, 
        message: str, 
        delay_seconds: int,
        keyboard: Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup]] = None
    ) -> None:
        """Отправить уведомление с задержкой"""
        async def delayed_send():
            await asyncio.sleep(delay_seconds)
            try:
                await self.send_notification(user_id, message, keyboard)
            except Exception as e:
                self.logger.error(f"Failed to send delayed notification: {e}")
        
        asyncio.create_task(delayed_send())
    
    async def send_self_destructing_notification(
        self, 
        user_id: int, 
        message: str, 
        destruct_after_seconds: int = 5,
        keyboard: Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup]] = None
    ) -> None:
        """Отправить самоудаляющееся уведомление"""
        try:
            sent_message = await self._bot.send_message(
                chat_id=user_id,
                text=message,
                reply_markup=keyboard
            )
            
            # Удаляем сообщение через указанное время
            async def delete_message():
                await asyncio.sleep(destruct_after_seconds)
                try:
                    await sent_message.delete()
                except Exception as e:
                    self.logger.error(f"Failed to delete message: {e}")
            
            asyncio.create_task(delete_message())
            
        except Exception as e:
            error_msg = f"Failed to send self-destructing notification: {e}"
            self.logger.error(error_msg)
            raise NotificationError(error_msg, user_id=user_id)
    
    async def _add_to_queue(
        self, 
        user_id: int, 
        message: str, 
        keyboard: Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup]] = None
    ) -> None:
        """Добавить уведомление в очередь"""
        if len(self._notification_queue) >= self._max_queue_size:
            self.logger.warning("Notification queue is full, dropping oldest notification")
            self._notification_queue.pop(0)
        
        notification = {
            'user_id': user_id,
            'message': message,
            'keyboard': keyboard,
            'created_at': datetime.now(),
            'retry_count': 0
        }
        
        self._notification_queue.append(notification)
    
    async def _process_notification_queue(self) -> None:
        """Обработка очереди уведомлений"""
        self._processing = True
        
        while self._processing:
            if not self._notification_queue:
                await asyncio.sleep(1)
                continue
            
            # Обрабатываем уведомления по одному
            notification = self._notification_queue.pop(0)
            
            try:
                await self.send_notification(
                    notification['user_id'],
                    notification['message'],
                    notification['keyboard']
                )
                
            except Exception as e:
                # Увеличиваем счетчик попыток
                notification['retry_count'] += 1
                
                if notification['retry_count'] < 3:
                    # Возвращаем в очередь для повторной попытки
                    self._notification_queue.append(notification)
                else:
                    self.logger.error(
                        f"Failed to send notification after 3 attempts: {e}"
                    )
            
            # Небольшая задержка между уведомлениями
            await asyncio.sleep(0.1)
    
    async def _get_admin_ids(self) -> List[int]:
        """Получить список ID администраторов"""
        # TODO: Реализовать получение администраторов из базы данных
        # Пока возвращаем пустой список
        return []
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Получить статус очереди уведомлений"""
        return {
            'queue_size': len(self._notification_queue),
            'max_queue_size': self._max_queue_size,
            'processing': self._processing,
            'bot_initialized': self._bot is not None
        }
    
    async def clear_queue(self) -> None:
        """Очистить очередь уведомлений"""
        self._notification_queue.clear()
        self.logger.info("Notification queue cleared")





