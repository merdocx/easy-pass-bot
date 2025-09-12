"""
Сервис управления пропусками
"""
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta

from ..core.base import BaseService
from ..core.interfaces import IPassRepository, IUserRepository, INotificationService
from ..core.exceptions import ValidationError, DatabaseError, AuthorizationError
from ..database.models import Pass
from ..config import PASS_STATUSES, ROLES, USER_STATUSES
from ..security.audit_logger import audit_logger


class PassService(BaseService):
    """Сервис управления пропусками"""
    
    def __init__(
        self,
        pass_repository: IPassRepository,
        user_repository: IUserRepository,
        notification_service: Optional[INotificationService] = None,
        logger: Optional[Any] = None,
        error_handler: Optional[Any] = None
    ):
        super().__init__(logger, error_handler)
        self.pass_repository = pass_repository
        self.user_repository = user_repository
        self.notification_service = notification_service
    
    async def _do_initialize(self) -> None:
        """Инициализация сервиса пропусков"""
        self.logger.info("Pass service initialized")
    
    async def _do_cleanup(self) -> None:
        """Очистка сервиса пропусков"""
        self.logger.info("Pass service cleaned up")
    
    async def create_pass(
        self, 
        user_id: int,
        car_number: str,
        created_by: Optional[int] = None
    ) -> Pass:
        """Создать новый пропуск"""
        try:
            # Проверяем, что пользователь существует и одобрен
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                raise ValidationError(f"User with ID {user_id} not found")
            
            if user.status != USER_STATUSES['APPROVED']:
                if user.status == USER_STATUSES['BLOCKED']:
                    # Проверяем, не истекла ли блокировка
                    if user.blocked_until:
                        from datetime import datetime
                        try:
                            blocked_until = datetime.fromisoformat(user.blocked_until)
                            if datetime.now() < blocked_until:
                                raise ValidationError(f"Пользователь заблокирован до {user.blocked_until}. Причина: {user.block_reason or 'Не указана'}")
                            else:
                                # Блокировка истекла, можно создать пропуск
                                pass
                        except ValueError:
                            # Если дата в неправильном формате, считаем заблокированным
                            raise ValidationError(f"Пользователь заблокирован. Причина: {user.block_reason or 'Не указана'}")
                    else:
                        raise ValidationError(f"Пользователь заблокирован. Причина: {user.block_reason or 'Не указана'}")
                else:
                    raise ValidationError("User must be approved to create passes")
            
            # Нормализуем номер автомобиля
            car_number = car_number.upper().strip()
            
            # Создаем пропуск
            pass_obj = Pass(
                user_id=user_id,
                car_number=car_number,
                status=PASS_STATUSES['ACTIVE'],
                created_at=datetime.now()
            )
            
            pass_id = await self.pass_repository.create(pass_obj)
            pass_obj.id = pass_id
            
            # Аудит-логирование создания пропуска
            audit_logger.log_pass_creation(user_id, car_number)
            
            self.logger.info(
                f"Pass created: {car_number} for user {user_id} (ID: {pass_id})"
            )
            return pass_obj
            
        except Exception as e:
            error_msg = f"Failed to create pass: {e}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg, operation="create_pass")
    
    async def get_pass_by_id(self, pass_id: int) -> Optional[Pass]:
        """Получить пропуск по ID"""
        try:
            return await self.pass_repository.get_by_id(pass_id)
        except Exception as e:
            error_msg = f"Failed to get pass by ID: {e}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg, operation="get_pass_by_id")
    
    async def get_user_passes(self, user_id: int) -> List[Pass]:
        """Получить пропуски пользователя"""
        try:
            return await self.pass_repository.get_user_passes(user_id)
        except Exception as e:
            error_msg = f"Failed to get user passes: {e}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg, operation="get_user_passes")
    
    async def get_active_user_passes(self, user_id: int) -> List[Pass]:
        """Получить активные пропуски пользователя"""
        try:
            all_passes = await self.get_user_passes(user_id)
            return [p for p in all_passes if p.status == PASS_STATUSES['ACTIVE']]
        except Exception as e:
            error_msg = f"Failed to get active user passes: {e}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg, operation="get_active_user_passes")
    
    async def search_passes_by_car_number(
        self, 
        car_number: str,
        partial: bool = False
    ) -> List[Pass]:
        """Поиск пропусков по номеру автомобиля (исключая архивные)"""
        try:
            car_number = car_number.upper().strip()
            
            if partial:
                # Частичный поиск - ищем все пропуски, содержащие номер
                all_passes = await self.pass_repository.get_all()
                matching_passes = [
                    p for p in all_passes 
                    if (p.status == PASS_STATUSES['ACTIVE'] and 
                        not p.is_archived and 
                        car_number in p.car_number)
                ]
            else:
                # Точный поиск - репозиторий уже исключает архивные
                matching_passes = await self.pass_repository.get_by_car_number(car_number)
                matching_passes = [
                    p for p in matching_passes 
                    if p.status == PASS_STATUSES['ACTIVE']
                ]
            
            self.logger.info(
                f"Found {len(matching_passes)} passes for car number: {car_number}"
            )
            return matching_passes
            
        except Exception as e:
            error_msg = f"Failed to search passes by car number: {e}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg, operation="search_passes_by_car_number")
    
    async def mark_pass_as_used(
        self, 
        pass_id: int, 
        used_by_id: int
    ) -> bool:
        """Отметить пропуск как использованный"""
        try:
            # Проверяем, что пропуск существует
            pass_obj = await self.get_pass_by_id(pass_id)
            if not pass_obj:
                raise ValidationError(f"Pass with ID {pass_id} not found")
            
            if pass_obj.status != PASS_STATUSES['ACTIVE']:
                raise ValidationError("Pass is not active")
            
            # Проверяем, что пользователь, отмечающий пропуск, имеет права
            user = await self.user_repository.get_by_id(used_by_id)
            if not user:
                raise ValidationError(f"User with ID {used_by_id} not found")
            
            if user.role not in [ROLES['SECURITY'], ROLES['ADMIN']]:
                raise AuthorizationError(
                    "Only security or admin can mark passes as used",
                    user_id=used_by_id
                )
            
            # Обновляем пропуск
            pass_obj.status = PASS_STATUSES['USED']
            pass_obj.used_at = datetime.now()
            pass_obj.used_by_id = used_by_id
            
            success = await self.pass_repository.update(pass_obj)
            
            if success:
                # Аудит-логирование использования пропуска
                audit_logger.log_pass_usage(pass_obj.user_id, pass_id, pass_obj.car_number, used_by_id)
                
                self.logger.info(
                    f"Pass {pass_id} marked as used by user {used_by_id}"
                )
                
                # Уведомляем владельца пропуска
                if self.notification_service:
                    await self._notify_pass_used(pass_obj, user)
            
            return success
            
        except Exception as e:
            error_msg = f"Failed to mark pass as used: {e}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg, operation="mark_pass_as_used")
    
    async def cancel_pass(self, pass_id: int, cancelled_by: int) -> bool:
        """Отменить пропуск"""
        try:
            pass_obj = await self.get_pass_by_id(pass_id)
            if not pass_obj:
                raise ValidationError(f"Pass with ID {pass_id} not found")
            
            if pass_obj.status != PASS_STATUSES['ACTIVE']:
                raise ValidationError("Only active passes can be cancelled")
            
            # Проверяем права на отмену
            user = await self.user_repository.get_by_id(cancelled_by)
            if not user:
                raise ValidationError(f"User with ID {cancelled_by} not found")
            
            # Пользователь может отменить только свои пропуски, админ - любые
            if user.role != ROLES['ADMIN'] and pass_obj.user_id != cancelled_by:
                raise AuthorizationError(
                    "You can only cancel your own passes",
                    user_id=cancelled_by
                )
            
            # Отменяем пропуск
            pass_obj.status = PASS_STATUSES['CANCELLED']
            pass_obj.used_at = datetime.now()
            pass_obj.used_by_id = cancelled_by
            
            success = await self.pass_repository.update(pass_obj)
            
            if success:
                self.logger.info(f"Pass {pass_id} cancelled by user {cancelled_by}")
            
            return success
            
        except Exception as e:
            error_msg = f"Failed to cancel pass: {e}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg, operation="cancel_pass")
    
    async def get_pass_statistics(self) -> Dict[str, Any]:
        """Получить статистику пропусков"""
        try:
            all_passes = await self.pass_repository.get_all()
            
            # Разделяем на активные и архивные
            active_passes = [p for p in all_passes if not p.is_archived]
            archived_passes = [p for p in all_passes if p.is_archived]
            
            stats = {
                'total': len(all_passes),
                'active_total': len(active_passes),
                'archived_total': len(archived_passes),
                'by_status': {},
                'active_by_status': {},
                'archived_by_status': {},
                'active_count': 0,
                'used_count': 0,
                'cancelled_count': 0,
                'today_created': 0,
                'today_used': 0
            }
            
            today = datetime.now().date()
            
            # Статистика по всем пропускам
            for pass_obj in all_passes:
                status = pass_obj.status
                stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
                
                # Статистика за сегодня
                if pass_obj.created_at.date() == today:
                    stats['today_created'] += 1
                
                if (pass_obj.used_at and 
                    pass_obj.used_at.date() == today and 
                    status == PASS_STATUSES['USED']):
                    stats['today_used'] += 1
            
            # Статистика по активным пропускам
            for pass_obj in active_passes:
                status = pass_obj.status
                stats['active_by_status'][status] = stats['active_by_status'].get(status, 0) + 1
                
                if status == PASS_STATUSES['ACTIVE']:
                    stats['active_count'] += 1
                elif status == PASS_STATUSES['USED']:
                    stats['used_count'] += 1
                elif status == PASS_STATUSES['CANCELLED']:
                    stats['cancelled_count'] += 1
            
            # Статистика по архивным пропускам
            for pass_obj in archived_passes:
                status = pass_obj.status
                stats['archived_by_status'][status] = stats['archived_by_status'].get(status, 0) + 1
            
            return stats
            
        except Exception as e:
            error_msg = f"Failed to get pass statistics: {e}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg, operation="get_pass_statistics")
    
    async def get_recent_passes(self, limit: int = 10) -> List[Pass]:
        """Получить последние пропуски (исключая архивные)"""
        try:
            all_passes = await self.pass_repository.get_all()
            # Фильтруем архивные пропуски и сортируем по дате создания (новые сначала)
            active_passes = [p for p in all_passes if not p.is_archived]
            sorted_passes = sorted(
                active_passes, 
                key=lambda p: p.created_at, 
                reverse=True
            )
            return sorted_passes[:limit]
            
        except Exception as e:
            error_msg = f"Failed to get recent passes: {e}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg, operation="get_recent_passes")
    
    async def _notify_pass_used(self, pass_obj: Pass, used_by_user) -> None:
        """Уведомить о использовании пропуска"""
        if not self.notification_service:
            return
        
        try:
            # Получаем владельца пропуска
            owner = await self.user_repository.get_by_id(pass_obj.user_id)
            if not owner:
                return
            
            message = (
                f"✅ Ваш пропуск {pass_obj.car_number} был использован "
                f"сотрудником {used_by_user.full_name}"
            )
            
            await self.notification_service.send_notification(
                owner.telegram_id, 
                message
            )
            
        except Exception as e:
            self.logger.error(f"Failed to notify about pass usage: {e}")
    
    async def cleanup_old_passes(self, days_old: int = 30) -> int:
        """Очистить старые использованные пропуски"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            all_passes = await self.pass_repository.get_all()
            
            old_passes = [
                p for p in all_passes 
                if (p.status == PASS_STATUSES['USED'] and 
                    p.used_at and 
                    p.used_at < cutoff_date)
            ]
            
            deleted_count = 0
            for pass_obj in old_passes:
                if await self.pass_repository.delete(pass_obj.id):
                    deleted_count += 1
            
            self.logger.info(f"Cleaned up {deleted_count} old passes")
            return deleted_count
            
        except Exception as e:
            error_msg = f"Failed to cleanup old passes: {e}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg, operation="cleanup_old_passes")

