"""
Система Dependency Injection
"""
from typing import Any, Dict, Optional, Type, TypeVar, Callable
import asyncio
from functools import wraps

from .interfaces import (
    IUserRepository, IPassRepository, IValidator, 
    INotificationService, ICacheService, IAnalyticsService, IErrorHandler
)
from .exceptions import ConfigurationError

T = TypeVar('T')


class DIContainer:
    """Контейнер для управления зависимостями"""
    
    def __init__(self):
        self._services: Dict[Type, Any] = {}
        self._factories: Dict[Type, Callable] = {}
        self._singletons: Dict[Type, Any] = {}
        self._initialized = False
    
    def register_singleton(self, interface: Type[T], implementation: T) -> None:
        """Зарегистрировать синглтон"""
        self._services[interface] = implementation
        self._singletons[interface] = implementation
    
    def register_factory(self, interface: Type[T], factory: Callable[[], T]) -> None:
        """Зарегистрировать фабрику"""
        self._factories[interface] = factory
    
    def register_transient(self, interface: Type[T], implementation: Type[T]) -> None:
        """Зарегистрировать транзиентный сервис"""
        self._services[interface] = implementation
    
    async def get(self, interface: Type[T]) -> T:
        """Получить экземпляр сервиса"""
        # Проверяем синглтоны
        if interface in self._singletons:
            return self._singletons[interface]
        
        # Проверяем фабрики
        if interface in self._factories:
            instance = self._factories[interface]()
            if hasattr(instance, 'initialize'):
                await instance.initialize()
            return instance
        
        # Проверяем транзиентные сервисы
        if interface in self._services:
            implementation = self._services[interface]
            if isinstance(implementation, type):
                instance = implementation()
                if hasattr(instance, 'initialize'):
                    await instance.initialize()
                return instance
            else:
                return implementation
        
        raise ConfigurationError(f"Service {interface.__name__} not registered")
    
    def get_sync(self, interface: Type[T]) -> T:
        """Получить экземпляр сервиса синхронно"""
        # Проверяем синглтоны
        if interface in self._singletons:
            return self._singletons[interface]
        
        # Проверяем фабрики
        if interface in self._factories:
            return self._factories[interface]()
        
        # Проверяем транзиентные сервисы
        if interface in self._services:
            implementation = self._services[interface]
            if isinstance(implementation, type):
                return implementation()
            else:
                return implementation
        
        raise ConfigurationError(f"Service {interface.__name__} not registered")
    
    async def initialize_all(self) -> None:
        """Инициализировать все сервисы"""
        if self._initialized:
            return
        
        # Инициализируем все зарегистрированные сервисы
        for service in self._services.values():
            if hasattr(service, 'initialize'):
                await service.initialize()
        
        self._initialized = True
    
    async def cleanup_all(self) -> None:
        """Очистить все сервисы"""
        # Очищаем все сервисы
        for service in self._services.values():
            if hasattr(service, 'cleanup'):
                await service.cleanup()
        
        self._initialized = False
    
    def is_registered(self, interface: Type[T]) -> bool:
        """Проверить, зарегистрирован ли сервис"""
        return (interface in self._services or 
                interface in self._factories or 
                interface in self._singletons)
    
    def get_registered_services(self) -> Dict[str, str]:
        """Получить список зарегистрированных сервисов"""
        services = {}
        
        for interface, implementation in self._services.items():
            if isinstance(implementation, type):
                services[interface.__name__] = f"Type: {implementation.__name__}"
            else:
                services[interface.__name__] = f"Instance: {type(implementation).__name__}"
        
        for interface, factory in self._factories.items():
            services[interface.__name__] = f"Factory: {factory.__name__}"
        
        for interface, singleton in self._singletons.items():
            services[interface.__name__] = f"Singleton: {type(singleton).__name__}"
        
        return services


# Глобальный контейнер
container = DIContainer()


def inject(interface: Type[T]) -> T:
    """Декоратор для внедрения зависимостей"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Получаем зависимость из контейнера
            dependency = await container.get(interface)
            
            # Добавляем зависимость в kwargs
            kwargs[interface.__name__.lower()] = dependency
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def inject_sync(interface: Type[T]) -> T:
    """Синхронный декоратор для внедрения зависимостей"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Получаем зависимость из контейнера
            dependency = container.get_sync(interface)
            
            # Добавляем зависимость в kwargs
            kwargs[interface.__name__.lower()] = dependency
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


class ServiceProvider:
    """Провайдер сервисов для удобного доступа"""
    
    def __init__(self, container: DIContainer):
        self._container = container
    
    async def get_user_service(self):
        """Получить сервис пользователей"""
        return await self._container.get(IUserRepository)
    
    async def get_pass_service(self):
        """Получить сервис пропусков"""
        return await self._container.get(IPassRepository)
    
    async def get_validation_service(self):
        """Получить сервис валидации"""
        return await self._container.get(IValidator)
    
    async def get_notification_service(self):
        """Получить сервис уведомлений"""
        return await self._container.get(INotificationService)
    
    async def get_cache_service(self):
        """Получить сервис кэширования"""
        return await self._container.get(ICacheService)
    
    async def get_analytics_service(self):
        """Получить сервис аналитики"""
        return await self._container.get(IAnalyticsService)
    
    async def get_error_handler(self):
        """Получить обработчик ошибок"""
        return await self._container.get(IErrorHandler)


# Глобальный провайдер сервисов
service_provider = ServiceProvider(container)
