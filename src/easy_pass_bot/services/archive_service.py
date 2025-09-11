"""
Сервис архивации пропусков
"""
from typing import Any, List, Optional
from datetime import datetime, timedelta
import asyncio
import logging

from ..core.base import BaseService
from ..core.interfaces import IPassRepository
from ..core.exceptions import DatabaseError
from ..database.models import Pass


class ArchiveService(BaseService):
    """Сервис архивации пропусков"""
    
    def __init__(
        self,
        pass_repository: IPassRepository,
        logger: Optional[Any] = None,
        error_handler: Optional[Any] = None
    ):
        super().__init__(logger, error_handler)
        self.pass_repository = pass_repository
        self._archiving_task: Optional[asyncio.Task] = None
        self._stop_archiving = False
    
    async def _do_initialize(self) -> None:
        """Инициализация сервиса архивации"""
        self.logger.info("Archive service initialized")
        # Запускаем фоновую задачу архивации
        self._archiving_task = asyncio.create_task(self._archiving_loop())
    
    async def _do_cleanup(self) -> None:
        """Очистка сервиса архивации"""
        self.logger.info("Stopping archive service...")
        self._stop_archiving = True
        if self._archiving_task:
            self._archiving_task.cancel()
            try:
                await self._archiving_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Archive service cleaned up")
    
    async def _archiving_loop(self) -> None:
        """Фоновая задача для автоматической архивации"""
        while not self._stop_archiving:
            try:
                await self.archive_old_passes()
                # Проверяем каждые 6 часов
                await asyncio.sleep(6 * 60 * 60)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in archiving loop: {e}")
                # При ошибке ждем 1 час перед следующей попыткой
                await asyncio.sleep(60 * 60)
    
    async def archive_old_passes(self) -> int:
        """Архивировать старые пропуски"""
        try:
            # Получаем пропуски для архивации
            passes_to_archive = await self.pass_repository.get_passes_for_archiving()
            
            archived_count = 0
            for pass_obj in passes_to_archive:
                try:
                    success = await self.pass_repository.archive_pass(pass_obj.id)
                    if success:
                        archived_count += 1
                        self.logger.info(
                            f"Archived pass {pass_obj.id} (car: {pass_obj.car_number}, "
                            f"status: {pass_obj.status})"
                        )
                except Exception as e:
                    self.logger.error(f"Failed to archive pass {pass_obj.id}: {e}")
            
            if archived_count > 0:
                self.logger.info(f"Archived {archived_count} passes")
            
            return archived_count
            
        except Exception as e:
            error_msg = f"Failed to archive old passes: {e}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg, operation="archive_old_passes")
    
    async def get_archived_passes(self, limit: int = 100) -> List[Pass]:
        """Получить архивные пропуски (для административных целей)"""
        try:
            all_passes = await self.pass_repository.get_all()
            archived_passes = [p for p in all_passes if p.is_archived]
            
            # Сортируем по дате создания (новые сначала)
            archived_passes.sort(key=lambda p: p.created_at, reverse=True)
            
            return archived_passes[:limit]
            
        except Exception as e:
            error_msg = f"Failed to get archived passes: {e}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg, operation="get_archived_passes")
    
    async def get_archive_statistics(self) -> dict:
        """Получить статистику архива"""
        try:
            all_passes = await self.pass_repository.get_all()
            
            total_passes = len(all_passes)
            archived_passes = [p for p in all_passes if p.is_archived]
            active_passes = [p for p in all_passes if not p.is_archived]
            
            stats = {
                'total_passes': total_passes,
                'archived_count': len(archived_passes),
                'active_count': len(active_passes),
                'archived_by_status': {},
                'archived_by_month': {}
            }
            
            # Статистика по статусам в архиве
            for pass_obj in archived_passes:
                status = pass_obj.status
                stats['archived_by_status'][status] = stats['archived_by_status'].get(status, 0) + 1
                
                # Статистика по месяцам
                if pass_obj.created_at:
                    month_key = pass_obj.created_at.strftime('%Y-%m')
                    stats['archived_by_month'][month_key] = stats['archived_by_month'].get(month_key, 0) + 1
            
            return stats
            
        except Exception as e:
            error_msg = f"Failed to get archive statistics: {e}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg, operation="get_archive_statistics")
    
    async def restore_pass(self, pass_id: int) -> bool:
        """Восстановить пропуск из архива (для административных целей)"""
        try:
            # Получаем пропуск
            pass_obj = await self.pass_repository.get_by_id(pass_id)
            if not pass_obj:
                raise ValueError(f"Pass with ID {pass_id} not found")
            
            if not pass_obj.is_archived:
                raise ValueError("Pass is not archived")
            
            # Восстанавливаем пропуск
            pass_obj.is_archived = False
            success = await self.pass_repository.update(pass_obj)
            
            if success:
                self.logger.info(f"Restored pass {pass_id} from archive")
            
            return success
            
        except Exception as e:
            error_msg = f"Failed to restore pass: {e}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg, operation="restore_pass")
    
    async def permanently_delete_archived_passes(self, older_than_days: int = 90) -> int:
        """Удалить архивные пропуски старше указанного количества дней"""
        try:
            cutoff_date = datetime.now() - timedelta(days=older_than_days)
            all_passes = await self.pass_repository.get_all()
            
            old_archived_passes = [
                p for p in all_passes 
                if p.is_archived and p.created_at and p.created_at < cutoff_date
            ]
            
            deleted_count = 0
            for pass_obj in old_archived_passes:
                try:
                    success = await self.pass_repository.delete(pass_obj.id)
                    if success:
                        deleted_count += 1
                        self.logger.info(f"Permanently deleted archived pass {pass_obj.id}")
                except Exception as e:
                    self.logger.error(f"Failed to delete archived pass {pass_obj.id}: {e}")
            
            if deleted_count > 0:
                self.logger.info(f"Permanently deleted {deleted_count} old archived passes")
            
            return deleted_count
            
        except Exception as e:
            error_msg = f"Failed to permanently delete archived passes: {e}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg, operation="permanently_delete_archived_passes")




