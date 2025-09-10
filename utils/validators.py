import re
from typing import Optional, Dict

def validate_registration_form(text: str) -> Optional[Dict[str, str]]:
    """Валидация формы регистрации"""
    parts = text.split(',')
    if len(parts) != 3:
        return None
    
    full_name = parts[0].strip()
    phone = parts[1].strip()
    apartment = parts[2].strip()
    
    if not full_name or not phone or not apartment:
        return None
    
    # Простая валидация телефона
    phone_clean = re.sub(r'[^\d+]', '', phone)
    if len(phone_clean) < 10:
        return None
    
    return {
        'full_name': full_name,
        'phone_number': phone,
        'apartment': apartment
    }

def validate_car_number(car_number: str) -> bool:
    """Валидация номера автомобиля"""
    if not car_number:
        return False
    
    car_number = car_number.strip()
    # Проверяем формат: 1 буква + 3 цифры + 2 буквы + 3 цифры
    pattern = r'^[А-Яа-я]\d{3}[А-Яа-я]{2}\d{3}$'
    return bool(re.match(pattern, car_number))
