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
