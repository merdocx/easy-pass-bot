"""
Сервис валидации данных
"""
import re
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from ..core.base import BaseValidator
from ..core.interfaces import IValidator
from ..core.exceptions import ValidationError


class ValidationService(BaseValidator):
    """Сервис валидации данных"""
    
    # Регулярные выражения для валидации
    PHONE_PATTERN = re.compile(r'^\+?[1-9]\d{1,14}$')
    CAR_NUMBER_PATTERN = re.compile(r'^[А-Яа-я]\d{3}[А-Яа-я]{2}\d{3}$')
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    
    # Минимальные и максимальные длины
    MIN_NAME_LENGTH = 2
    MAX_NAME_LENGTH = 100
    MIN_APARTMENT_LENGTH = 1
    MAX_APARTMENT_LENGTH = 10
    
    async def _do_initialize(self) -> None:
        """Инициализация сервиса валидации"""
        self.logger.info("Validation service initialized")
    
    async def _do_cleanup(self) -> None:
        """Очистка сервиса валидации"""
        self.clear_errors()
    
    async def validate_user_data(self, data: Dict[str, Any]) -> bool:
        """Валидация данных пользователя"""
        self.clear_errors()
        
        # Валидация обязательных полей
        required_fields = ['full_name', 'phone_number', 'apartment']
        for field in required_fields:
            if not data.get(field):
                self.add_error(f"Поле '{field}' обязательно для заполнения")
        
        # Валидация имени
        if 'full_name' in data:
            await self._validate_name(data['full_name'])
        
        # Валидация телефона
        if 'phone_number' in data:
            await self._validate_phone(data['phone_number'])
        
        # Валидация квартиры
        if 'apartment' in data:
            await self._validate_apartment(data['apartment'])
        
        return not self.has_errors()
    
    async def validate_car_number(self, car_number: str) -> bool:
        """Валидация номера автомобиля"""
        self.clear_errors()
        
        if not car_number:
            self.add_error("Номер автомобиля не может быть пустым")
            return False
        
        # Приводим к верхнему регистру
        car_number = car_number.upper().strip()
        
        if not self.CAR_NUMBER_PATTERN.match(car_number):
            self.add_error(
                "Неверный формат номера автомобиля. "
                "Используйте формат: А123БВ777"
            )
            return False
        
        return True
    
    async def validate_registration_form(self, text: str) -> bool:
        """Валидация формы регистрации"""
        self.clear_errors()
        
        if not text or not text.strip():
            self.add_error("Форма регистрации не может быть пустой")
            return False
        
        # Разбиваем по запятым
        parts = [part.strip() for part in text.split(',')]
        
        if len(parts) != 3:
            self.add_error(
                "Неверный формат. Отправьте: ФИО, Телефон, Квартира"
            )
            return False
        
        # Валидируем каждую часть
        full_name, phone_number, apartment = parts
        
        await self._validate_name(full_name)
        await self._validate_phone(phone_number)
        await self._validate_apartment(apartment)
        
        return not self.has_errors()
    
    async def validate_search_query(self, query: str) -> bool:
        """Валидация поискового запроса"""
        self.clear_errors()
        
        if not query or not query.strip():
            self.add_error("Поисковый запрос не может быть пустым")
            return False
        
        query = query.strip()
        
        # Проверяем минимальную длину
        if len(query) < 2:
            self.add_error("Поисковый запрос должен содержать минимум 2 символа")
            return False
        
        # Проверяем максимальную длину
        if len(query) > 20:
            self.add_error("Поисковый запрос слишком длинный")
            return False
        
        return True
    
    async def _validate_name(self, name: str) -> None:
        """Валидация имени"""
        if not name:
            self.add_error("Имя не может быть пустым")
            return
        
        name = name.strip()
        
        if len(name) < self.MIN_NAME_LENGTH:
            self.add_error(f"Имя должно содержать минимум {self.MIN_NAME_LENGTH} символа")
        
        if len(name) > self.MAX_NAME_LENGTH:
            self.add_error(f"Имя должно содержать максимум {self.MAX_NAME_LENGTH} символов")
        
        # Проверяем, что имя содержит только буквы, пробелы и дефисы
        if not re.match(r'^[а-яА-ЯёЁa-zA-Z\s\-]+$', name):
            self.add_error("Имя может содержать только буквы, пробелы и дефисы")
    
    async def _validate_phone(self, phone: str) -> None:
        """Валидация телефона"""
        if not phone:
            self.add_error("Телефон не может быть пустым")
            return
        
        phone = phone.strip()
        
        # Убираем все пробелы и дефисы
        clean_phone = re.sub(r'[\s\-\(\)]', '', phone)
        
        if not self.PHONE_PATTERN.match(clean_phone):
            self.add_error(
                "Неверный формат телефона. "
                "Используйте формат: +7 900 123 45 67"
            )
    
    async def _validate_apartment(self, apartment: str) -> None:
        """Валидация номера квартиры"""
        if not apartment:
            self.add_error("Номер квартиры не может быть пустым")
            return
        
        apartment = apartment.strip()
        
        if len(apartment) < self.MIN_APARTMENT_LENGTH:
            self.add_error(f"Номер квартиры должен содержать минимум {self.MIN_APARTMENT_LENGTH} символ")
        
        if len(apartment) > self.MAX_APARTMENT_LENGTH:
            self.add_error(f"Номер квартиры должен содержать максимум {self.MAX_APARTMENT_LENGTH} символов")
        
        # Проверяем, что номер квартиры содержит только цифры и буквы
        if not re.match(r'^[0-9а-яА-ЯёЁa-zA-Z]+$', apartment):
            self.add_error("Номер квартиры может содержать только цифры и буквы")
    
    async def validate_email(self, email: str) -> bool:
        """Валидация email"""
        self.clear_errors()
        
        if not email:
            self.add_error("Email не может быть пустым")
            return False
        
        email = email.strip().lower()
        
        if not self.EMAIL_PATTERN.match(email):
            self.add_error("Неверный формат email")
            return False
        
        return True
    
    async def validate_telegram_id(self, telegram_id: Any) -> bool:
        """Валидация Telegram ID"""
        self.clear_errors()
        
        if not telegram_id:
            self.add_error("Telegram ID не может быть пустым")
            return False
        
        try:
            telegram_id = int(telegram_id)
        except (ValueError, TypeError):
            self.add_error("Telegram ID должен быть числом")
            return False
        
        if telegram_id <= 0:
            self.add_error("Telegram ID должен быть положительным числом")
            return False
        
        return True
    
    def get_validation_rules(self) -> Dict[str, Any]:
        """Получить правила валидации"""
        return {
            'name': {
                'min_length': self.MIN_NAME_LENGTH,
                'max_length': self.MAX_NAME_LENGTH,
                'pattern': r'^[а-яА-ЯёЁa-zA-Z\s\-]+$'
            },
            'phone': {
                'pattern': self.PHONE_PATTERN.pattern
            },
            'apartment': {
                'min_length': self.MIN_APARTMENT_LENGTH,
                'max_length': self.MAX_APARTMENT_LENGTH,
                'pattern': r'^[0-9а-яА-ЯёЁa-zA-Z]+$'
            },
            'car_number': {
                'pattern': self.CAR_NUMBER_PATTERN.pattern
            },
            'email': {
                'pattern': self.EMAIL_PATTERN.pattern
            }
        }





