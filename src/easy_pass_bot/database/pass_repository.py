"""
Репозиторий для работы с пропусками
"""
import logging
from typing import List, Optional
from datetime import datetime

from ..core.interfaces import IPassRepository
from ..core.exceptions import DatabaseError
from .models import Pass
from .database import db


logger = logging.getLogger(__name__)


class PassRepository(IPassRepository):
    """Репозиторий для работы с пропусками"""
    
    async def create(self, entity: Pass) -> int:
        """Создать пропуск"""
        try:
            return await db.create_pass(entity)
        except Exception as e:
            raise DatabaseError(f"Failed to create pass: {e}")
    
    async def get_by_id(self, entity_id: int) -> Optional[Pass]:
        """Получить пропуск по ID"""
        try:
            return await db.get_pass_by_id(entity_id)
        except Exception as e:
            raise DatabaseError(f"Failed to get pass by ID: {e}")
    
    async def update(self, entity: Pass) -> bool:
        """Обновить пропуск"""
        try:
            # Обновляем статус пропуска
            if entity.status == 'used':
                return await db.update_pass_status(entity.id, entity.status, entity.used_by_id)
            else:
                return await db.update_pass_status(entity.id, entity.status)
        except Exception as e:
            raise DatabaseError(f"Failed to update pass: {e}")
    
    async def delete(self, entity_id: int) -> bool:
        """Удалить пропуск"""
        try:
            # В реальной реализации можно добавить мягкое удаление
            # или физическое удаление из базы данных
            # Пока что просто помечаем как удаленный
            pass_obj = await self.get_by_id(entity_id)
            if pass_obj:
                pass_obj.status = 'cancelled'
                return await self.update(pass_obj)
            return False
        except Exception as e:
            raise DatabaseError(f"Failed to delete pass: {e}")
    
    async def get_by_car_number(self, car_number: str) -> List[Pass]:
        """Получить пропуски по номеру автомобиля"""
        try:
            return await db.find_all_passes_by_car_number(car_number)
        except Exception as e:
            raise DatabaseError(f"Failed to get passes by car number: {e}")
    
    async def get_user_passes(self, user_id: int) -> List[Pass]:
        """Получить пропуски пользователя"""
        try:
            return await db.get_user_passes(user_id)
        except Exception as e:
            raise DatabaseError(f"Failed to get user passes: {e}")
    
    async def mark_as_used(self, pass_id: int, used_by_id: int) -> bool:
        """Отметить пропуск как использованный"""
        try:
            await db.mark_pass_as_used(pass_id, used_by_id)
            return True
        except Exception as e:
            raise DatabaseError(f"Failed to mark pass as used: {e}")
    
    async def get_all(self) -> List[Pass]:
        """Получить все пропуски (включая архивные)"""
        try:
            return await db.get_all_passes()
        except Exception as e:
            raise DatabaseError(f"Failed to get all passes: {e}")
    
    async def archive_pass(self, pass_id: int) -> bool:
        """Переместить пропуск в архив"""
        try:
            return await db.archive_pass(pass_id)
        except Exception as e:
            raise DatabaseError(f"Failed to archive pass: {e}")
    
    async def get_passes_for_archiving(self) -> List[Pass]:
        """Получить пропуски для архивации"""
        try:
            return await db.get_passes_for_archiving()
        except Exception as e:
            raise DatabaseError(f"Failed to get passes for archiving: {e}")




