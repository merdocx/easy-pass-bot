from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class User:
    """Модель пользователя"""
    id: Optional[int] = None
    telegram_id: int = 0
    role: str = 'resident'
    full_name: str = ''
    phone_number: str = ''
    apartment: Optional[str] = None
    status: str = 'pending'
    blocked_until: Optional[str] = None
    block_reason: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class Pass:
    """Модель пропуска"""
    id: Optional[int] = None
    user_id: int = 0
    car_number: str = ''
    status: str = 'active'
    created_at: Optional[datetime] = None
    used_at: Optional[datetime] = None
    used_by_id: Optional[int] = None
    is_archived: bool = False

@dataclass
class Admin:
    """Модель администратора для веб-админки"""
    id: Optional[int] = None
    username: str = ''
    full_name: str = ''
    password_hash: str = ''
    role: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    user_id: Optional[int] = None  # Связь с таблицей users
    phone_number: Optional[str] = None  # Нормализованный номер телефона
    last_login_at: Optional[datetime] = None

    def __post_init__(self):
        """Инициализация после создания объекта"""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
        if self.is_active is None:
            self.is_active = True
