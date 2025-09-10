"""
Конфигурация и инициализация сервисов
"""
import logging
from typing import Optional

from .container import container
from .interfaces import (
    IUserRepository, IPassRepository, IValidator, 
    INotificationService, ICacheService, IAnalyticsService, IErrorHandler
)
from ..services.validation_service import ValidationService
from ..services.notification_service import NotificationService
from ..services.user_service import UserService
from ..services.pass_service import PassService
from ..services.cache_service import CacheService
from ..services.error_handler import ErrorHandler
from ..features.analytics import AnalyticsService
from ..database.database import Database
from ..config import BOT_TOKEN


class ServiceConfigurator:
    """Конфигуратор сервисов"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def configure_services(self) -> None:
        """Настроить все сервисы"""
        try:
            self.logger.info("Configuring services...")
            
            # Настраиваем базовые сервисы
            await self._configure_core_services()
            
            # Настраиваем репозитории
            await self._configure_repositories()
            
            # Настраиваем бизнес-сервисы
            await self._configure_business_services()
            
            # Инициализируем все сервисы
            await container.initialize_all()
            
            self.logger.info("All services configured successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to configure services: {e}")
            raise
    
    async def _configure_core_services(self) -> None:
        """Настроить основные сервисы"""
        # Сервис кэширования
        cache_service = CacheService()
        container.register_singleton(ICacheService, cache_service)
        
        # Обработчик ошибок
        error_handler = ErrorHandler()
        container.register_singleton(IErrorHandler, error_handler)
        
        # Сервис аналитики
        analytics_service = AnalyticsService()
        container.register_singleton(IAnalyticsService, analytics_service)
        
        # Сервис уведомлений
        notification_service = NotificationService(bot_token=BOT_TOKEN)
        container.register_singleton(INotificationService, notification_service)
        
        # Сервис валидации
        validation_service = ValidationService()
        container.register_singleton(IValidator, validation_service)
    
    async def _configure_repositories(self) -> None:
        """Настроить репозитории"""
        # База данных
        database = Database()
        await database.init_db()
        
        # Репозиторий пользователей
        container.register_singleton(IUserRepository, database)
        
        # Репозиторий пропусков
        container.register_singleton(IPassRepository, database)
    
    async def _configure_business_services(self) -> None:
        """Настроить бизнес-сервисы"""
        # Получаем зависимости
        user_repository = await container.get(IUserRepository)
        pass_repository = await container.get(IPassRepository)
        notification_service = await container.get(INotificationService)
        cache_service = await container.get(ICacheService)
        error_handler = await container.get(IErrorHandler)
        
        # Сервис пользователей
        user_service = UserService(
            user_repository=user_repository,
            notification_service=notification_service,
            error_handler=error_handler
        )
        container.register_singleton(UserService, user_service)
        
        # Сервис пропусков
        pass_service = PassService(
            pass_repository=pass_repository,
            user_repository=user_repository,
            notification_service=notification_service,
            error_handler=error_handler
        )
        container.register_singleton(PassService, pass_service)
    
    async def cleanup_services(self) -> None:
        """Очистить все сервисы"""
        try:
            self.logger.info("Cleaning up services...")
            await container.cleanup_all()
            self.logger.info("All services cleaned up successfully")
        except Exception as e:
            self.logger.error(f"Failed to cleanup services: {e}")
    
    def get_service_status(self) -> dict:
        """Получить статус сервисов"""
        return {
            'registered_services': container.get_registered_services(),
            'initialized': container._initialized
        }


# Глобальный конфигуратор
service_configurator = ServiceConfigurator()


async def initialize_services() -> None:
    """Инициализировать все сервисы"""
    await service_configurator.configure_services()


async def cleanup_services() -> None:
    """Очистить все сервисы"""
    await service_configurator.cleanup_services()


def get_service_status() -> dict:
    """Получить статус сервисов"""
    return service_configurator.get_service_status()
