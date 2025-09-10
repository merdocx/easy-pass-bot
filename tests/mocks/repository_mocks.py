"""
Моки для репозиториев
"""
from unittest.mock import AsyncMock, MagicMock
from typing import List, Optional, Any
from src.easy_pass_bot.database.models import User, Pass
from src.easy_pass_bot.core.interfaces import IUserRepository, IPassRepository


class MockUserRepository(IUserRepository):
    """Мок репозитория пользователей"""
    
    def __init__(self):
        self._users: List[User] = []
        self._next_id = 1
    
    async def create(self, entity: User) -> int:
        """Создать пользователя"""
        entity.id = self._next_id
        self._next_id += 1
        self._users.append(entity)
        return entity.id
    
    async def get_by_id(self, entity_id: int) -> Optional[User]:
        """Получить пользователя по ID"""
        for user in self._users:
            if user.id == entity_id:
                return user
        return None
    
    async def update(self, entity: User) -> bool:
        """Обновить пользователя"""
        for i, user in enumerate(self._users):
            if user.id == entity.id:
                self._users[i] = entity
                return True
        return False
    
    async def delete(self, entity_id: int) -> bool:
        """Удалить пользователя"""
        for i, user in enumerate(self._users):
            if user.id == entity_id:
                del self._users[i]
                return True
        return False
    
    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Получить пользователя по Telegram ID"""
        for user in self._users:
            if user.telegram_id == telegram_id:
                return user
        return None
    
    async def get_by_role(self, role: str) -> List[User]:
        """Получить пользователей по роли"""
        return [user for user in self._users if user.role == role]
    
    async def get_pending_users(self) -> List[User]:
        """Получить пользователей на модерации"""
        from src.easy_pass_bot.config import USER_STATUSES
        return [user for user in self._users if user.status == USER_STATUSES['PENDING']]
    
    async def get_all(self) -> List[User]:
        """Получить всех пользователей"""
        return self._users.copy()
    
    def clear(self):
        """Очистить репозиторий"""
        self._users.clear()
        self._next_id = 1


class MockPassRepository(IPassRepository):
    """Мок репозитория пропусков"""
    
    def __init__(self):
        self._passes: List[Pass] = []
        self._next_id = 1
    
    async def create(self, entity: Pass) -> int:
        """Создать пропуск"""
        entity.id = self._next_id
        self._next_id += 1
        self._passes.append(entity)
        return entity.id
    
    async def get_by_id(self, entity_id: int) -> Optional[Pass]:
        """Получить пропуск по ID"""
        for pass_obj in self._passes:
            if pass_obj.id == entity_id:
                return pass_obj
        return None
    
    async def update(self, entity: Pass) -> bool:
        """Обновить пропуск"""
        for i, pass_obj in enumerate(self._passes):
            if pass_obj.id == entity.id:
                self._passes[i] = entity
                return True
        return False
    
    async def delete(self, entity_id: int) -> bool:
        """Удалить пропуск"""
        for i, pass_obj in enumerate(self._passes):
            if pass_obj.id == entity_id:
                del self._passes[i]
                return True
        return False
    
    async def get_by_car_number(self, car_number: str) -> List[Pass]:
        """Получить пропуски по номеру автомобиля"""
        return [p for p in self._passes if p.car_number == car_number]
    
    async def get_user_passes(self, user_id: int) -> List[Pass]:
        """Получить пропуски пользователя"""
        return [p for p in self._passes if p.user_id == user_id]
    
    async def mark_as_used(self, pass_id: int, used_by_id: int) -> bool:
        """Отметить пропуск как использованный"""
        from src.easy_pass_bot.config import PASS_STATUSES
        from datetime import datetime
        
        for pass_obj in self._passes:
            if pass_obj.id == pass_id:
                pass_obj.status = PASS_STATUSES['USED']
                pass_obj.used_at = datetime.now()
                pass_obj.used_by_id = used_by_id
                return True
        return False
    
    async def get_all(self) -> List[Pass]:
        """Получить все пропуски"""
        return self._passes.copy()
    
    async def archive_pass(self, pass_id: int) -> bool:
        """Переместить пропуск в архив"""
        for pass_obj in self._passes:
            if pass_obj.id == pass_id:
                pass_obj.is_archived = True
                return True
        return False
    
    async def get_passes_for_archiving(self) -> List[Pass]:
        """Получить пропуски для архивации"""
        from datetime import datetime, timedelta
        now = datetime.now()
        passes_to_archive = []
        
        for pass_obj in self._passes:
            if pass_obj.is_archived:
                continue
                
            # Использованные пропуски старше 24 часов
            if (pass_obj.status == 'used' and 
                pass_obj.used_at and 
                pass_obj.used_at < now - timedelta(hours=24)):
                passes_to_archive.append(pass_obj)
            
            # Неиспользованные пропуски старше 7 дней
            elif (pass_obj.status == 'active' and 
                  pass_obj.created_at and 
                  pass_obj.created_at < now - timedelta(days=7)):
                passes_to_archive.append(pass_obj)
        
        return passes_to_archive
    
    def clear(self):
        """Очистить репозиторий"""
        self._passes.clear()
        self._next_id = 1


class MockNotificationService:
    """Мок сервиса уведомлений"""
    
    def __init__(self):
        self.sent_notifications = []
        self.admin_notifications = []
    
    async def send_notification(self, user_id: int, message: str, keyboard=None) -> bool:
        """Отправить уведомление"""
        self.sent_notifications.append({
            'user_id': user_id,
            'message': message,
            'keyboard': keyboard
        })
        return True
    
    async def notify_admins(self, message: str) -> bool:
        """Уведомить администраторов"""
        self.admin_notifications.append(message)
        return True
    
    def clear(self):
        """Очистить уведомления"""
        self.sent_notifications.clear()
        self.admin_notifications.clear()


class MockCacheService:
    """Мок сервиса кэширования"""
    
    def __init__(self):
        self._cache = {}
    
    async def get(self, key: str) -> Optional[Any]:
        """Получить значение из кэша"""
        return self._cache.get(key)
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Сохранить значение в кэш"""
        self._cache[key] = value
        return True
    
    async def delete(self, key: str) -> bool:
        """Удалить значение из кэша"""
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    async def invalidate_pattern(self, pattern: str) -> bool:
        """Инвалидировать кэш по паттерну"""
        # Простая реализация - удаляем все ключи, содержащие паттерн
        keys_to_delete = [k for k in self._cache.keys() if pattern.replace('*', '') in k]
        for key in keys_to_delete:
            del self._cache[key]
        return True
    
    def clear(self):
        """Очистить кэш"""
        self._cache.clear()


class MockErrorHandler:
    """Мок обработчика ошибок"""
    
    def __init__(self):
        self.handled_errors = []
    
    async def handle_error(self, error: Exception, context: Optional[dict] = None) -> None:
        """Обработать ошибку"""
        self.handled_errors.append({
            'error': error,
            'context': context
        })
    
    def get_user_friendly_message(self, error: Exception) -> str:
        """Получить понятное пользователю сообщение"""
        return f"Произошла ошибка: {str(error)}"
    
    def clear(self):
        """Очистить обработанные ошибки"""
        self.handled_errors.clear()

