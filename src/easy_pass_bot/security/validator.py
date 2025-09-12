"""
Валидатор входных данных для обеспечения безопасности
"""
import re
from typing import Optional, Tuple, Dict, Any
import logging
logger = logging.getLogger(__name__)

class InputValidator:
    """Валидатор входных данных"""
    # Регулярные выражения для валидации
    PHONE_PATTERN = r'^\+?[1-9]\d{1,14}$'
    CAR_NUMBER_PATTERN = r'^[А-Яа-я]\d{3}[А-Яа-я]{2}\d{3}$'
    NAME_PATTERN = r'^[А-Яа-я\s\-]{2,50}$'
    APARTMENT_PATTERN = r'^\d{1,4}[А-Яа-я]?$'
    TELEGRAM_ID_PATTERN = r'^\d{1,20}$'
    # Максимальные длины полей
    MAX_NAME_LENGTH = 50
    MAX_PHONE_LENGTH = 20
    MAX_APARTMENT_LENGTH = 10
    MAX_CAR_NUMBER_LENGTH = 20
    @classmethod
    def validate_phone(cls, phone: str) -> Tuple[bool, Optional[str]]:
        """
        Валидация номера телефона
        Args:
            phone: Номер телефона для проверки
        Returns:
            Tuple[bool, Optional[str]]: (валидность, ошибка)
        """
        if not phone or not isinstance(phone, str):
            return False, "Номер телефона не может быть пустым"
        
        # Используем нормализатор для проверки формата
        from ..utils.phone_normalizer import validate_phone_format, is_russian_phone
        
        # Проверяем, является ли номер российским и может ли быть нормализован
        if is_russian_phone(phone) and validate_phone_format(phone):
            return True, None
        
        # Если это не российский номер, отклоняем его
        return False, "Поддерживаются только российские номера телефонов. Используйте формат: +7XXXXXXXXXX или 8XXXXXXXXXX"
    @classmethod
    def validate_car_number(cls, car_number: str) -> Tuple[bool, Optional[str]]:
        """
        Валидация номера автомобиля
        Args:
            car_number: Номер автомобиля для проверки
        Returns:
            Tuple[bool, Optional[str]]: (валидность, ошибка)
        """
        if not car_number or not isinstance(car_number, str):
            return False, "Номер автомобиля не может быть пустым"
        clean_number = car_number.strip().upper()
        if len(clean_number) > cls.MAX_CAR_NUMBER_LENGTH:
            return False, f"Номер автомобиля слишком длинный (максимум {cls.MAX_CAR_NUMBER_LENGTH} символов)"
        if not re.match(cls.CAR_NUMBER_PATTERN, clean_number):
            return False, "Неверный формат номера автомобиля. Используйте формат: А123БВ777"
        return True, None
    @classmethod
    def validate_name(cls, name: str) -> Tuple[bool, Optional[str]]:
        """
        Валидация ФИО
        Args:
            name: ФИО для проверки
        Returns:
            Tuple[bool, Optional[str]]: (валидность, ошибка)
        """
        if not name or not isinstance(name, str):
            return False, "ФИО не может быть пустым"
        clean_name = name.strip()
        if len(clean_name) < 2:
            return False, "ФИО слишком короткое (минимум 2 символа)"
        if len(clean_name) > cls.MAX_NAME_LENGTH:
            return False, f"ФИО слишком длинное (максимум {cls.MAX_NAME_LENGTH} символов)"
        if not re.match(cls.NAME_PATTERN, clean_name):
            return False, "ФИО может содержать только буквы, пробелы и дефисы"
        # Проверяем, что есть хотя бы одно слово
        words = clean_name.split()
        if len(words) < 2:
            return False, "Введите полное ФИО (минимум 2 слова)"
        return True, None
    @classmethod
    def validate_apartment(cls, apartment: str) -> Tuple[bool, Optional[str]]:
        """
        Валидация номера квартиры
        Args:
            apartment: Номер квартиры для проверки
        Returns:
            Tuple[bool, Optional[str]]: (валидность, ошибка)
        """
        if not apartment or not isinstance(apartment, str):
            return False, "Номер квартиры не может быть пустым"
        clean_apartment = apartment.strip()
        if len(clean_apartment) > cls.MAX_APARTMENT_LENGTH:
            return False, f"Номер квартиры слишком длинный (максимум {cls.MAX_APARTMENT_LENGTH} символов)"
        if not re.match(cls.APARTMENT_PATTERN, clean_apartment):
            return False, "Неверный формат номера квартиры. Используйте формат: 15 или 15А"
        return True, None
    @classmethod
    def validate_telegram_id(cls, telegram_id: Any) -> Tuple[bool, Optional[str]]:
        """
        Валидация Telegram ID
        Args:
            telegram_id: Telegram ID для проверки
        Returns:
            Tuple[bool, Optional[str]]: (валидность, ошибка)
        """
        if telegram_id is None:
            return False, "Telegram ID не может быть пустым"
        # Преобразуем в строку для проверки
        id_str = str(telegram_id)
        if not re.match(cls.TELEGRAM_ID_PATTERN, id_str):
            return False, "Неверный формат Telegram ID"
        # Проверяем диапазон значений
        try:
            id_int = int(telegram_id)
            if id_int <= 0:
                return False, "Telegram ID должен быть положительным числом"
        except (ValueError, TypeError):
            return False, "Telegram ID должен быть числом"
        return True, None
    @classmethod
    def validate_registration_data(cls, data: str) -> Tuple[bool, Optional[str], Optional[Dict[str, str]]]:
        """
        Валидация данных регистрации в формате "ФИО, Телефон, Квартира"
        Args:
            data: Строка с данными регистрации
        Returns:
            Tuple[bool, Optional[str], Optional[Dict[str, str]]]: (валидность, ошибка, данные)
        """
        if not data or not isinstance(data, str):
            return False, "Данные регистрации не могут быть пустыми", None
        # Разделяем по запятой
        parts = [part.strip() for part in data.split(',')]
        if len(parts) != 3:
            return False, "Неверный формат. Отправьте: ФИО, Телефон, Квартира", None
        full_name, phone, apartment = parts
        # Валидируем каждое поле
        name_valid, name_error = cls.validate_name(full_name)
        if not name_valid:
            return False, name_error, None
        phone_valid, phone_error = cls.validate_phone(phone)
        if not phone_valid:
            return False, phone_error, None
        apartment_valid, apartment_error = cls.validate_apartment(apartment)
        if not apartment_valid:
            return False, apartment_error, None
        # Нормализуем номер телефона
        from ..utils.phone_normalizer import normalize_phone_number
        normalized_phone = normalize_phone_number(phone)
        
        return True, None, {
            'full_name': full_name,
            'phone_number': normalized_phone,
            'apartment': apartment
        }
    @classmethod
    def sanitize_input(cls, text: str) -> str:
        """
        Очистка входных данных от потенциально опасных символов
        Args:
            text: Текст для очистки
        Returns:
            Очищенный текст
        """
        if not text or not isinstance(text, str):
            return ""
        # Убираем HTML теги
        text = re.sub(r'<[^>]+>', '', text)
        # Убираем управляющие символы
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        # Ограничиваем длину
        text = text[:1000]
        return text.strip()
    @classmethod
    def validate_search_query(cls, query: str) -> Tuple[bool, Optional[str]]:
        """
        Валидация поискового запроса
        Args:
            query: Поисковый запрос
        Returns:
            Tuple[bool, Optional[str]]: (валидность, ошибка)
        """
        if not query or not isinstance(query, str):
            return False, "Поисковый запрос не может быть пустым"
        clean_query = query.strip()
        if len(clean_query) < 1:
            return False, "Поисковый запрос слишком короткий"
        if len(clean_query) > 50:
            return False, "Поисковый запрос слишком длинный (максимум 50 символов)"
        # Проверяем на подозрительные символы
        if re.search(r'[<>"\']', clean_query):
            return False, "Поисковый запрос содержит недопустимые символы"
        return True, None
# Глобальный экземпляр валидатора
validator = InputValidator()
