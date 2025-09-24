"""
Unified configuration system for Easy Pass Bot
"""
import os
from typing import Dict, Any, Optional, List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Unified settings for Easy Pass Bot"""
    
    # Bot tokens
    resident_bot_token: str = Field(..., env="RESIDENT_BOT_TOKEN")
    security_bot_token: str = Field(..., env="SECURITY_BOT_TOKEN")
    
    # Database
    database_path: str = Field(default="database/easy_pass.db", env="DATABASE_PATH")
    
    # Security
    rate_limit_max_requests: int = Field(default=15, env="RATE_LIMIT_MAX_REQUESTS")
    rate_limit_window_seconds: int = Field(default=60, env="RATE_LIMIT_WINDOW_SECONDS")
    
    # Validation limits
    max_name_length: int = Field(default=50, env="MAX_NAME_LENGTH")
    max_phone_length: int = Field(default=20, env="MAX_PHONE_LENGTH")
    max_apartment_length: int = Field(default=10, env="MAX_APARTMENT_LENGTH")
    max_car_number_length: int = Field(default=15, env="MAX_CAR_NUMBER_LENGTH")
    
    # Cache settings
    cache_default_ttl: int = Field(default=300, env="CACHE_DEFAULT_TTL")
    cache_max_size: int = Field(default=1000, env="CACHE_MAX_SIZE")
    
    # Retry settings
    retry_max_attempts: int = Field(default=3, env="RETRY_MAX_ATTEMPTS")
    retry_base_delay: float = Field(default=1.0, env="RETRY_BASE_DELAY")
    retry_max_delay: float = Field(default=60.0, env="RETRY_MAX_DELAY")
    
    # Circuit breaker
    circuit_breaker_failure_threshold: int = Field(default=5, env="CIRCUIT_BREAKER_FAILURE_THRESHOLD")
    circuit_breaker_timeout: int = Field(default=30, env="CIRCUIT_BREAKER_TIMEOUT")
    circuit_breaker_success_threshold: int = Field(default=2, env="CIRCUIT_BREAKER_SUCCESS_THRESHOLD")
    
    # Analytics
    analytics_retention_days: int = Field(default=30, env="ANALYTICS_RETENTION_DAYS")
    analytics_batch_size: int = Field(default=100, env="ANALYTICS_BATCH_SIZE")
    
    # Confirmations
    confirmation_timeout: int = Field(default=300, env="CONFIRMATION_TIMEOUT")
    confirmation_cleanup_interval: int = Field(default=60, env="CONFIRMATION_CLEANUP_INTERVAL")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")  # json or text
    log_file: Optional[str] = Field(default="logs/app.log", env="LOG_FILE")
    log_rotation: str = Field(default="daily", env="LOG_ROTATION")
    log_retention_days: int = Field(default=30, env="LOG_RETENTION_DAYS")
    
    # Admin panel
    admin_secret_key: str = Field(default="your-secret-key-change-in-production", env="ADMIN_SECRET_KEY")
    admin_host: str = Field(default="0.0.0.0", env="ADMIN_HOST")
    admin_port: int = Field(default=8080, env="ADMIN_PORT")
    
    # Pass limits
    max_active_passes: int = Field(default=3, env="MAX_ACTIVE_PASSES")
    
    # User roles
    roles: Dict[str, str] = Field(default={
        "RESIDENT": "resident",
        "SECURITY": "security", 
        "ADMIN": "admin"
    })
    
    # User statuses
    user_statuses: Dict[str, str] = Field(default={
        "PENDING": "pending",
        "APPROVED": "approved",
        "REJECTED": "rejected",
        "BLOCKED": "blocked"
    })
    
    # Pass statuses
    pass_statuses: Dict[str, str] = Field(default={
        "ACTIVE": "active",
        "USED": "used",
        "CANCELLED": "cancelled"
    })
    
    # Messages
    messages: Dict[str, str] = Field(default={
        "WELCOME": """🏠 Добро пожаловать в PM Desk!
Заполните форму регистрации:
Отправьте сообщение в формате:
ФИО, Телефон, Квартира
Например: Иванов Иван Иванович, 89997776655, 27""",
        
        "WELCOME_STAFF": """👮 Добро пожаловать в PM Desk для персонала!
Заполните форму регистрации:
Отправьте сообщение в формате:
ФИО, Телефон
Например: Иванов Иван Иванович, 89997776655""",
        
        "REGISTRATION_SENT": "✅ Заявка отправлена на модерацию!",
        "REGISTRATION_APPROVED": "✅ Регистрация одобрена!",
        "REGISTRATION_REJECTED": "❌ Заявка отклонена. Обратитесь к администратору.",
        
        "PASS_CREATION_REQUEST": """🚗 Подача заявки на пропуск
Введите номер автомобиля:
Например: А123АА777""",
        
        "PASS_CREATED": "✅ Заявка создана! Номер: {car_number}",
        "INVALID_FORMAT": """❌ Неверный формат.
Отправьте: ФИО, Телефон, Квартира
Например: Иванов Иван Иванович, +7 900 123 45 67, 15""",
        
        "INVALID_FORMAT_STAFF": """❌ Неверный формат.
Отправьте: ФИО, Телефон
Например: Иванов Иван Иванович, +7 900 123 45 67""",
        
        "ALL_FIELDS_REQUIRED": "❌ Все поля обязательны",
        "ENTER_CAR_NUMBER": "❌ Введите номер автомобиля",
        "MAX_PASSES_REACHED": "❌ Вы достигли максимального числа активных заявок",
        "DUPLICATE_PASS": "❌ У вас уже есть заявка с таким номером",
        "NO_RIGHTS": "❌ Нет прав",
        "PASS_ALREADY_USED": "❌ Пропуск уже использован",
        "REQUEST_ALREADY_PROCESSED": "❌ Заявка уже обработана"
    })
    
    # Security messages
    security_messages: Dict[str, str] = Field(default={
        "WELCOME": """Нажмите на кнопку \"🔍 Найти пропуск\" для поиска заявки. После открытия шлагбаума отметьте пропуск как использованный, нажав \"✅\" под пропуском.""",
        
        "ADMIN_WELCOME": """👑 Добро пожаловать в панель администратора PM Desk. Здесь вы сможете управлять входящими заявками на регистрацию в системе.""",
        
        "PASS_NOT_FOUND": "❌ Пропуск с номером {car_number} не найден.\n\nПроверьте правильность номера.",
        "PASS_USED": "✅ Пропуск отмечен как использованный!",
        "PASS_ALREADY_USED": "❌ Пропуск уже использован",
        "NO_RIGHTS": "❌ Нет прав",
        "ENTER_CAR_NUMBER": "❌ Введите номер автомобиля",
        "USER_APPROVED": "✅ Пользователь одобрен",
        "USER_REJECTED": "❌ Пользователь отклонен",
        "USER_BLOCKED": "🚫 Пользователь заблокирован",
        "USER_UNBLOCKED": "✅ Пользователь разблокирован"
    })
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'log_level must be one of {valid_levels}')
        return v.upper()
    
    @field_validator('log_format')
    @classmethod
    def validate_log_format(cls, v):
        valid_formats = ['json', 'text']
        if v.lower() not in valid_formats:
            raise ValueError(f'log_format must be one of {valid_formats}')
        return v.lower()
    
    @field_validator('log_rotation')
    @classmethod
    def validate_log_rotation(cls, v):
        valid_rotations = ['daily', 'weekly', 'monthly', 'size']
        if v.lower() not in valid_rotations:
            raise ValueError(f'log_rotation must be one of {valid_rotations}')
        return v.lower()
    
    @field_validator('database_path')
    @classmethod
    def validate_database_path(cls, v):
        # Ensure database directory exists
        db_path = Path(v)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return str(db_path)
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "validate_assignment": True,
        "extra": "ignore"  # Ignore extra fields from .env
    }


# Global settings instance
settings = Settings()

# Backward compatibility exports
BOT_TOKEN = settings.resident_bot_token
RESIDENT_BOT_TOKEN = settings.resident_bot_token
SECURITY_BOT_TOKEN = settings.security_bot_token
DATABASE_PATH = settings.database_path
ROLES = settings.roles
USER_STATUSES = settings.user_statuses
PASS_STATUSES = settings.pass_statuses
MESSAGES = settings.messages
SECURITY_MESSAGES = settings.security_messages
MAX_ACTIVE_PASSES = settings.max_active_passes
