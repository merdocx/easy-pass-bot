"""
Сервис управления пользователями
"""
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from ..core.base import BaseService
from ..core.interfaces import IUserRepository, INotificationService
from ..core.exceptions import ValidationError, DatabaseError, AuthorizationError
from ..database.models import User
from ..config import ROLES, USER_STATUSES
from ..security.audit_logger import audit_logger


class UserService(BaseService):
    """Сервис управления пользователями"""
    
    def __init__(
        self,
        user_repository: IUserRepository,
        notification_service: Optional[INotificationService] = None,
        logger: Optional[Any] = None,
        error_handler: Optional[Any] = None
    ):
        super().__init__(logger, error_handler)
        self.user_repository = user_repository
        self.notification_service = notification_service
    
    async def _do_initialize(self) -> None:
        """Инициализация сервиса пользователей"""
        self.logger.info("User service initialized")
    
    async def _do_cleanup(self) -> None:
        """Очистка сервиса пользователей"""
        self.logger.info("User service cleaned up")
    
    async def create_user(
        self, 
        telegram_id: int,
        full_name: str,
        phone_number: str,
        apartment: str,
        role: str = ROLES['RESIDENT']
    ) -> User:
        """Создать нового пользователя"""
        try:
            # Проверяем, не существует ли уже пользователь
            existing_user = await self.user_repository.get_by_telegram_id(telegram_id)
            if existing_user:
                raise ValidationError(
                    f"Пользователь с Telegram ID {telegram_id} уже существует"
                )
            
            # Нормализуем номер телефона
            from ..utils.phone_normalizer import normalize_phone_number
            normalized_phone = normalize_phone_number(phone_number)
            
            # Создаем пользователя
            user = User(
                telegram_id=telegram_id,
                role=role,
                full_name=full_name,
                phone_number=normalized_phone,
                apartment=apartment,
                status=USER_STATUSES['PENDING']
            )
            
            user_id = await self.user_repository.create(user)
            user.id = user_id
            
            # Аудит-логирование регистрации пользователя
            audit_logger.log_user_registration(telegram_id, {
                'full_name': full_name,
                'phone_number': phone_number,
                'apartment': apartment
            })
            
            self.logger.info(f"User created: {user.full_name} (ID: {user_id})")
            return user
            
        except Exception as e:
            error_msg = f"Failed to create user: {e}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg, operation="create_user")
    
    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Получить пользователя по Telegram ID"""
        try:
            return await self.user_repository.get_by_telegram_id(telegram_id)
        except Exception as e:
            error_msg = f"Failed to get user by telegram ID: {e}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg, operation="get_user_by_telegram_id")
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Получить пользователя по ID"""
        try:
            return await self.user_repository.get_by_id(user_id)
        except Exception as e:
            error_msg = f"Failed to get user by ID: {e}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg, operation="get_user_by_id")
    
    async def update_user_status(
        self, 
        user_id: int, 
        status: str,
        updated_by: Optional[int] = None
    ) -> bool:
        """Обновить статус пользователя"""
        try:
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                raise ValidationError(f"User with ID {user_id} not found")
            
            old_status = user.status
            user.status = status
            user.updated_at = datetime.now()
            
            success = await self.user_repository.update(user)
            
            if success:
                self.logger.info(
                    f"User {user_id} status updated from {old_status} to {status}"
                )
                
                # Отправляем уведомление пользователю
                if self.notification_service:
                    await self._notify_user_status_change(user, old_status, status)
            
            return success
            
        except Exception as e:
            error_msg = f"Failed to update user status: {e}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg, operation="update_user_status")
    
    async def approve_user(self, user_id: int, approved_by: int) -> bool:
        """Одобрить пользователя"""
        return await self.update_user_status(
            user_id, 
            USER_STATUSES['APPROVED'], 
            approved_by
        )
    
    async def reject_user(self, user_id: int, rejected_by: int) -> bool:
        """Отклонить пользователя"""
        return await self.update_user_status(
            user_id, 
            USER_STATUSES['REJECTED'], 
            rejected_by
        )
    
    async def get_pending_users(self) -> List[User]:
        """Получить пользователей на модерации"""
        try:
            return await self.user_repository.get_pending_users()
        except Exception as e:
            error_msg = f"Failed to get pending users: {e}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg, operation="get_pending_users")
    
    async def get_users_by_role(self, role: str) -> List[User]:
        """Получить пользователей по роли"""
        try:
            return await self.user_repository.get_by_role(role)
        except Exception as e:
            error_msg = f"Failed to get users by role: {e}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg, operation="get_users_by_role")
    
    async def is_admin(self, telegram_id: int) -> bool:
        """Проверить, является ли пользователь администратором"""
        try:
            user = await self.get_user_by_telegram_id(telegram_id)
            return user and user.role == ROLES['ADMIN'] and user.status == USER_STATUSES['APPROVED']
        except Exception as e:
            self.logger.error(f"Failed to check admin status: {e}")
            return False
    
    async def is_security(self, telegram_id: int) -> bool:
        """Проверить, является ли пользователь охранником"""
        try:
            user = await self.get_user_by_telegram_id(telegram_id)
            return user and user.role == ROLES['SECURITY'] and user.status == USER_STATUSES['APPROVED']
        except Exception as e:
            self.logger.error(f"Failed to check security status: {e}")
            return False
    
    async def is_resident(self, telegram_id: int) -> bool:
        """Проверить, является ли пользователь жителем"""
        try:
            user = await self.get_user_by_telegram_id(telegram_id)
            return user and user.role == ROLES['RESIDENT'] and user.status == USER_STATUSES['APPROVED']
        except Exception as e:
            self.logger.error(f"Failed to check resident status: {e}")
            return False
    
    async def get_user_role(self, telegram_id: int) -> Optional[str]:
        """Получить роль пользователя"""
        try:
            user = await self.get_user_by_telegram_id(telegram_id)
            return user.role if user else None
        except Exception as e:
            self.logger.error(f"Failed to get user role: {e}")
            return None
    
    async def get_user_status(self, telegram_id: int) -> Optional[str]:
        """Получить статус пользователя"""
        try:
            user = await self.get_user_by_telegram_id(telegram_id)
            return user.status if user else None
        except Exception as e:
            self.logger.error(f"Failed to get user status: {e}")
            return None
    
    async def require_role(
        self, 
        telegram_id: int, 
        required_role: str
    ) -> User:
        """Требовать определенную роль от пользователя"""
        user = await self.get_user_by_telegram_id(telegram_id)
        
        if not user:
            raise AuthorizationError(
                "Пользователь не найден",
                user_id=telegram_id,
                required_role=required_role
            )
        
        if user.role != required_role:
            raise AuthorizationError(
                f"Требуется роль {required_role}",
                user_id=telegram_id,
                required_role=required_role
            )
        
        if user.status != USER_STATUSES['APPROVED']:
            raise AuthorizationError(
                "Пользователь не одобрен",
                user_id=telegram_id,
                required_role=required_role
            )
        
        return user
    
    async def _notify_user_status_change(
        self, 
        user: User, 
        old_status: str, 
        new_status: str
    ) -> None:
        """Уведомить пользователя об изменении статуса"""
        if not self.notification_service:
            return
        
        try:
            if new_status == USER_STATUSES['APPROVED']:
                message = "✅ Регистрация одобрена!"
            elif new_status == USER_STATUSES['REJECTED']:
                message = "❌ Заявка отклонена. Обратитесь к администратору."
            else:
                return
            
            await self.notification_service.send_notification(
                user.telegram_id, 
                message
            )
            
        except Exception as e:
            self.logger.error(f"Failed to notify user about status change: {e}")
    
    async def get_user_statistics(self) -> Dict[str, Any]:
        """Получить статистику пользователей"""
        try:
            all_users = await self.user_repository.get_all()
            
            stats = {
                'total': len(all_users),
                'by_status': {},
                'by_role': {},
                'pending_count': 0,
                'approved_count': 0,
                'rejected_count': 0
            }
            
            for user in all_users:
                # Статистика по статусам
                status = user.status
                stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
                
                # Статистика по ролям
                role = user.role
                stats['by_role'][role] = stats['by_role'].get(role, 0) + 1
                
                # Подсчет статусов
                if status == USER_STATUSES['PENDING']:
                    stats['pending_count'] += 1
                elif status == USER_STATUSES['APPROVED']:
                    stats['approved_count'] += 1
                elif status == USER_STATUSES['REJECTED']:
                    stats['rejected_count'] += 1
            
            return stats
            
        except Exception as e:
            error_msg = f"Failed to get user statistics: {e}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg, operation="get_user_statistics")




