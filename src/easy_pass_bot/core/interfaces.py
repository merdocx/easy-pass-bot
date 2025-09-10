"""
Интерфейсы для основных компонентов системы
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from datetime import datetime


class IRepository(ABC):
    """Базовый интерфейс для репозиториев"""
    
    @abstractmethod
    async def create(self, entity: Any) -> int:
        """Создать сущность"""
        pass
    
    @abstractmethod
    async def get_by_id(self, entity_id: int) -> Optional[Any]:
        """Получить сущность по ID"""
        pass
    
    @abstractmethod
    async def update(self, entity: Any) -> bool:
        """Обновить сущность"""
        pass
    
    @abstractmethod
    async def delete(self, entity_id: int) -> bool:
        """Удалить сущность"""
        pass


class IUserRepository(IRepository):
    """Интерфейс для работы с пользователями"""
    
    @abstractmethod
    async def get_by_telegram_id(self, telegram_id: int) -> Optional[Any]:
        """Получить пользователя по Telegram ID"""
        pass
    
    @abstractmethod
    async def get_by_role(self, role: str) -> List[Any]:
        """Получить пользователей по роли"""
        pass
    
    @abstractmethod
    async def get_pending_users(self) -> List[Any]:
        """Получить пользователей на модерации"""
        pass


class IPassRepository(IRepository):
    """Интерфейс для работы с пропусками"""
    
    @abstractmethod
    async def get_by_car_number(self, car_number: str) -> List[Any]:
        """Получить пропуски по номеру автомобиля"""
        pass
    
    @abstractmethod
    async def get_user_passes(self, user_id: int) -> List[Any]:
        """Получить пропуски пользователя"""
        pass
    
    @abstractmethod
    async def mark_as_used(self, pass_id: int, used_by_id: int) -> bool:
        """Отметить пропуск как использованный"""
        pass
    
    @abstractmethod
    async def get_all(self) -> List[Any]:
        """Получить все пропуски (включая архивные)"""
        pass
    
    @abstractmethod
    async def archive_pass(self, pass_id: int) -> bool:
        """Переместить пропуск в архив"""
        pass
    
    @abstractmethod
    async def get_passes_for_archiving(self) -> List[Any]:
        """Получить пропуски для архивации"""
        pass


class IValidator(ABC):
    """Интерфейс для валидаторов"""
    
    @abstractmethod
    async def validate(self, data: Any) -> bool:
        """Валидировать данные"""
        pass
    
    @abstractmethod
    def get_errors(self) -> List[str]:
        """Получить список ошибок валидации"""
        pass


class INotificationService(ABC):
    """Интерфейс для сервиса уведомлений"""
    
    @abstractmethod
    async def send_notification(
        self, 
        user_id: int, 
        message: str, 
        keyboard: Optional[Any] = None
    ) -> bool:
        """Отправить уведомление пользователю"""
        pass
    
    @abstractmethod
    async def notify_admins(self, message: str) -> bool:
        """Уведомить администраторов"""
        pass


class ICacheService(ABC):
    """Интерфейс для сервиса кэширования"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Получить значение из кэша"""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Сохранить значение в кэш"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Удалить значение из кэша"""
        pass
    
    @abstractmethod
    async def invalidate_pattern(self, pattern: str) -> bool:
        """Инвалидировать кэш по паттерну"""
        pass


class IAnalyticsService(ABC):
    """Интерфейс для сервиса аналитики"""
    
    @abstractmethod
    async def track_event(
        self, 
        event_type: str, 
        user_id: int, 
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Отследить событие"""
        pass
    
    @abstractmethod
    async def get_metrics(self, period: str) -> Dict[str, Any]:
        """Получить метрики за период"""
        pass


class IErrorHandler(ABC):
    """Интерфейс для обработки ошибок"""
    
    @abstractmethod
    async def handle_error(
        self, 
        error: Exception, 
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Обработать ошибку"""
        pass
    
    @abstractmethod
    def get_user_friendly_message(self, error: Exception) -> str:
        """Получить понятное пользователю сообщение об ошибке"""
        pass


class ILogger(ABC):
    """Интерфейс для логирования"""
    
    @abstractmethod
    def info(self, message: str, **kwargs) -> None:
        """Информационное сообщение"""
        pass
    
    @abstractmethod
    def warning(self, message: str, **kwargs) -> None:
        """Предупреждение"""
        pass
    
    @abstractmethod
    def error(self, message: str, **kwargs) -> None:
        """Ошибка"""
        pass
    
    @abstractmethod
    def debug(self, message: str, **kwargs) -> None:
        """Отладочное сообщение"""
        pass

