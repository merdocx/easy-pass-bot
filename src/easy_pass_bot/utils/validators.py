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
    car_number = car_number.strip().upper()
    
    # Убираем пробелы и дефисы
    car_number = re.sub(r'[\s\-]', '', car_number)
    
    # Проверяем различные форматы российских номеров:
    # А123БВ456 (1 буква + 3 цифры + 2 буквы + 3 цифры)
    # А123БВ45 (1 буква + 3 цифры + 2 буквы + 2 цифры) 
    # А123БВ4 (1 буква + 3 цифры + 2 буквы + 1 цифра)
    # А123БВ (1 буква + 3 цифры + 2 буквы)
    patterns = [
        r'^[А-Я]\d{3}[А-Я]{2}\d{1,3}$',  # А123БВ456, А123БВ45, А123БВ4
        r'^[А-Я]\d{3}[А-Я]{2}$',         # А123БВ
        r'^\d{3}[А-Я]{2}\d{1,3}$',       # 123БВ456, 123БВ45, 123БВ4
        r'^\d{3}[А-Я]{2}$',              # 123БВ
    ]
    
    for pattern in patterns:
        if re.match(pattern, car_number):
            return True
    
    return False
