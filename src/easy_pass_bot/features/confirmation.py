"""
Сервис подтверждений для критических действий
"""
import asyncio
import logging
from typing import Dict, Any, Optional, Callable
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime, timedelta
logger = logging.getLogger(__name__)

class ConfirmationService:
    """Сервис подтверждений для критических действий"""
    def __init__(self, timeout: int = 300):
        """
        Инициализация сервиса подтверждений
        Args:
            timeout: Время ожидания подтверждения в секундах
        """
        self.timeout = timeout
        self.pending_confirmations: Dict[str, Dict[str, Any]] = {}
        self.confirmation_logger = logging.getLogger('confirmation')
        # Запускаем задачу очистки истекших подтверждений
        self._cleanup_task = None
        # Задача будет запущена при первом использовании
    def _start_cleanup_task(self):
        """Запуск задачи очистки истекших подтверждений"""
        if self._cleanup_task is None or self._cleanup_task.done():
            try:
                self._cleanup_task = asyncio.create_task(self._cleanup_expired_confirmations())
            except RuntimeError:
                # Нет активного event loop, запустим позже
                self.confirmation_logger.debug("No event loop available for cleanup task")
    async def _cleanup_expired_confirmations(self):
        """Очистка истекших подтверждений"""
        while True:
            try:
                await asyncio.sleep(60)  # Проверяем каждую минуту
                current_time = datetime.utcnow()
                expired_keys = []
                for key, data in self.pending_confirmations.items():
                    if current_time - data['created_at'] > timedelta(seconds=self.timeout):
                        expired_keys.append(key)
                for key in expired_keys:
                    del self.pending_confirmations[key]
                    self.confirmation_logger.debug(f"Expired confirmation: {key}")
                if expired_keys:
                    self.confirmation_logger.info(f"Cleaned up {len(expired_keys)} expired confirmations")
            except Exception as e:
                self.confirmation_logger.error(f"Error in confirmation cleanup: {e}")
    def create_confirmation_keyboard(self, action: str, confirmation_id: str,
                                   confirm_text: str = "✅ Да",
                                   cancel_text: str = "❌ Нет") -> InlineKeyboardMarkup:
        """
        Создание клавиатуры подтверждения
        Args:
            action: Действие для подтверждения
            confirmation_id: Уникальный ID подтверждения
            confirm_text: Текст кнопки подтверждения
            cancel_text: Текст кнопки отмены
        Returns:
            Inline клавиатура с подтверждением
        """
        builder = InlineKeyboardBuilder()
        builder.button(
            text=confirm_text,
            callback_data=f"confirm_{action}_{confirmation_id}"
        )
        builder.button(
            text=cancel_text,
            callback_data=f"cancel_{action}_{confirmation_id}"
        )
        builder.adjust(2)
        return builder.as_markup()
    def create_dangerous_action_keyboard(self, action: str, confirmation_id: str) -> InlineKeyboardMarkup:
        """
        Создание клавиатуры для опасных действий
        Args:
            action: Действие для подтверждения
            confirmation_id: Уникальный ID подтверждения
        Returns:
            Inline клавиатура с подтверждением
        """
        return self.create_confirmation_keyboard(
            action, confirmation_id,
            confirm_text="⚠️ Да, выполнить",
            cancel_text="✅ Отмена"
        )
    def create_double_confirmation_keyboard(self, action: str, confirmation_id: str) -> InlineKeyboardMarkup:
        """
        Создание клавиатуры с двойным подтверждением
        Args:
            action: Действие для подтверждения
            confirmation_id: Уникальный ID подтверждения
        Returns:
            Inline клавиатура с двойным подтверждением
        """
        builder = InlineKeyboardBuilder()
        builder.button(
            text="⚠️ Подтвердить",
            callback_data=f"confirm_{action}_{confirmation_id}"
        )
        builder.button(
            text="❌ Отмена",
            callback_data=f"cancel_{action}_{confirmation_id}"
        )
        builder.button(
            text="🔄 Изменить",
            callback_data=f"edit_{action}_{confirmation_id}"
        )
        builder.adjust(1)
        return builder.as_markup()
    def register_confirmation(self, confirmation_id: str, action: str,
                            data: Dict[str, Any], callback: Callable) -> str:
        """
        Регистрация подтверждения
        Args:
            confirmation_id: Уникальный ID подтверждения
            action: Действие для подтверждения
            data: Данные для передачи в callback
            callback: Функция для выполнения при подтверждении
        Returns:
            ID подтверждения
        """
        # Запускаем задачу очистки при первом использовании
        if self._cleanup_task is None:
            self._start_cleanup_task()
        self.pending_confirmations[confirmation_id] = {
            'action': action,
            'data': data,
            'callback': callback,
            'created_at': datetime.utcnow(),
            'status': 'pending'
        }
        self.confirmation_logger.debug(f"Registered confirmation: {confirmation_id} for action: {action}")
        return confirmation_id
    async def handle_confirmation(self, confirmation_id: str, action: str,
                                confirmed: bool) -> Optional[Any]:
        """
        Обработка подтверждения
        Args:
            confirmation_id: ID подтверждения
            action: Действие
            confirmed: Подтверждено ли действие
        Returns:
            Результат выполнения callback или None
        """
        if confirmation_id not in self.pending_confirmations:
            self.confirmation_logger.warning(f"Confirmation not found: {confirmation_id}")
            return None
        confirmation_data = self.pending_confirmations[confirmation_id]
        # Проверяем, что действие совпадает
        if confirmation_data['action'] != action:
            self.confirmation_logger.warning(
                f"Action mismatch for confirmation {confirmation_id}: "
                f"expected {action}, got {confirmation_data['action']}"
            )
            return None
        # Обновляем статус
        confirmation_data['status'] = 'confirmed' if confirmed else 'cancelled'
        confirmation_data['processed_at'] = datetime.utcnow()
        if confirmed:
            try:
                # Выполняем callback
                callback = confirmation_data['callback']
                data = confirmation_data['data']
                if asyncio.iscoroutinefunction(callback):
                    result = await callback(data)
                else:
                    result = callback(data)
                self.confirmation_logger.info(f"Confirmation executed: {confirmation_id}")
                return result
            except Exception as e:
                self.confirmation_logger.error(f"Error executing confirmation {confirmation_id}: {e}")
                raise
        else:
            self.confirmation_logger.info(f"Confirmation cancelled: {confirmation_id}")
            return None
    def get_confirmation_status(self, confirmation_id: str) -> Optional[Dict[str, Any]]:
        """
        Получение статуса подтверждения
        Args:
            confirmation_id: ID подтверждения
        Returns:
            Словарь со статусом или None
        """
        if confirmation_id not in self.pending_confirmations:
            return None
        data = self.pending_confirmations[confirmation_id]
        return {
            'action': data['action'],
            'status': data['status'],
            'created_at': data['created_at'].isoformat(),
            'processed_at': data.get('processed_at', {}).isoformat() if data.get('processed_at') else None
        }
    def cancel_confirmation(self, confirmation_id: str) -> bool:
        """
        Отмена подтверждения
        Args:
            confirmation_id: ID подтверждения
        Returns:
            True если подтверждение было отменено
        """
        if confirmation_id in self.pending_confirmations:
            del self.pending_confirmations[confirmation_id]
            self.confirmation_logger.info(f"Confirmation cancelled: {confirmation_id}")
            return True
        return False
    def get_pending_confirmations(self) -> Dict[str, Dict[str, Any]]:
        """
        Получение всех ожидающих подтверждений
        Returns:
            Словарь с ожидающими подтверждениями
        """
        return {
            key: {
                'action': data['action'],
                'created_at': data['created_at'].isoformat(),
                'status': data['status']
            }
            for key, data in self.pending_confirmations.items()
        }
    def get_stats(self) -> Dict[str, Any]:
        """
        Получение статистики подтверждений
        Returns:
            Словарь со статистикой
        """
        total_confirmations = len(self.pending_confirmations)
        confirmed_count = sum(1 for data in self.pending_confirmations.values()
                            if data['status'] == 'confirmed')
        cancelled_count = sum(1 for data in self.pending_confirmations.values()
                            if data['status'] == 'cancelled')
        pending_count = sum(1 for data in self.pending_confirmations.values()
                          if data['status'] == 'pending')
        return {
            'total_confirmations': total_confirmations,
            'confirmed': confirmed_count,
            'cancelled': cancelled_count,
            'pending': pending_count,
            'confirmation_rate': confirmed_count / max(total_confirmations, 1)
        }
    async def close(self):
        """Закрытие сервиса подтверждений"""
        if hasattr(self, '_cleanup_task') and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
# Глобальный экземпляр сервиса подтверждений
confirmation_service = ConfirmationService()
