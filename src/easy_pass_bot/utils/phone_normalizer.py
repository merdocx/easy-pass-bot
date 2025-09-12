"""
Модуль для нормализации российских номеров телефонов.

Преобразует различные форматы ввода в стандартный формат +7 999 999 99 99
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def normalize_phone_number(phone: str) -> str:
    """
    Нормализация российского номера телефона в формат +7 999 999 99 99
    
    Args:
        phone (str): Исходный номер телефона в любом формате
        
    Returns:
        str: Нормализованный номер в формате +7 999 999 99 99
               или исходный номер, если нормализация невозможна
        
    Поддерживаемые входные форматы:
    - +7 999 999 99 99
    - 8 999 999 99 99  
    - 89999999999
    - 999 999 99 99
    - +7(999)999-99-99
    - 8(999)999-99-99
    - +7 999-999-99-99
    - 8 999-999-99-99
    """
    if not phone or not isinstance(phone, str):
        return phone or ""
    
    # Очищаем от всех символов кроме цифр
    digits_only = re.sub(r'[^\d]', '', phone)
    
    # Если номер пустой после очистки, возвращаем исходный
    if not digits_only:
        logger.warning(f"Phone number contains no digits: '{phone}'")
        return phone
    
    # Если номер содержит слишком много цифр, попробуем найти российский номер в начале
    if len(digits_only) > 11:
        # Ищем российский номер в начале строки (11 цифр: 8/7 + 10 цифр)
        if digits_only.startswith('8') and len(digits_only) >= 11:
            digits_only = digits_only[:11]
        elif digits_only.startswith('7') and len(digits_only) >= 11:
            digits_only = digits_only[:11]
        # Или ищем 10-значный номер, начинающийся с 9
        elif digits_only.startswith('9'):
            # Найдем первый 10-значный блок, начинающийся с 9
            for i in range(len(digits_only) - 9):
                if digits_only[i:i+10].startswith('9'):
                    digits_only = digits_only[i:i+10]
                    break
    
    # Определяем длину номера
    length = len(digits_only)
    
    # Если номер начинается с 8 и имеет 11 цифр (8 + 10 цифр)
    if length == 11 and digits_only.startswith('8'):
        # Заменяем 8 на 7 и форматируем
        formatted = format_russian_phone(digits_only[1:])  # Убираем первую 8
        logger.info(f"Normalized phone: '{phone}' -> '{formatted}'")
        return formatted
    
    # Если номер начинается с 7 и имеет 11 цифр (+7 + 10 цифр)
    elif length == 11 and digits_only.startswith('7'):
        # Форматируем без первой 7
        formatted = format_russian_phone(digits_only[1:])  # Убираем первую 7
        logger.info(f"Normalized phone: '{phone}' -> '{formatted}'")
        return formatted
    
    # Если номер имеет 10 цифр (без кода страны)
    elif length == 10:
        # Проверяем, что это российский номер (начинается с 9)
        if digits_only.startswith('9'):
            formatted = format_russian_phone(digits_only)
            logger.info(f"Normalized phone: '{phone}' -> '{formatted}'")
            return formatted
        else:
            logger.warning(f"Phone number doesn't start with 9: '{phone}'")
            return phone
    
    # Если номер не соответствует российскому формату
    else:
        logger.warning(f"Phone number doesn't match Russian format (length: {length}): '{phone}'")
        return phone


def format_russian_phone(digits: str) -> str:
    """
    Форматирует 10-значный номер в формат +7 999 999 99 99
    
    Args:
        digits (str): 10 цифр номера телефона
        
    Returns:
        str: Отформатированный номер +7 999 999 99 99
    """
    if len(digits) != 10:
        raise ValueError(f"Expected 10 digits, got {len(digits)}")
    
    # Форматируем: +7 XXX XXX XX XX
    formatted = f"+7 {digits[:3]} {digits[3:6]} {digits[6:8]} {digits[8:10]}"
    return formatted


def validate_phone_format(phone: str) -> bool:
    """
    Проверяет, соответствует ли номер российскому формату
    
    Args:
        phone (str): Номер телефона для проверки
        
    Returns:
        bool: True если номер может быть нормализован, False иначе
    """
    if not phone or not isinstance(phone, str):
        return False
    
    # Очищаем от всех символов кроме цифр
    digits_only = re.sub(r'[^\d]', '', phone)
    length = len(digits_only)
    
    # Российские номера: 10 цифр (начинается с 9) или 11 цифр (начинается с 8 или 7)
    if length == 10 and digits_only.startswith('9'):
        return True
    elif length == 11 and (digits_only.startswith('8') or digits_only.startswith('7')):
        return True
    
    return False


def is_russian_phone(phone: str) -> bool:
    """
    Проверяет, является ли номер российским
    
    Args:
        phone (str): Номер телефона
        
    Returns:
        bool: True если номер российский, False иначе
    """
    if not phone:
        return False
    
    digits_only = re.sub(r'[^\d]', '', phone)
    
    # Российские номера начинаются с 8, 7 или 9
    if digits_only.startswith(('8', '7', '9')):
        return True
    
    return False


# Примеры использования и тестирования
if __name__ == "__main__":
    # Тестовые номера
    test_phones = [
        "+7 999 123 45 67",
        "8 999 123 45 67",
        "89991234567",
        "999 123 45 67",
        "+7(999)123-45-67",
        "8(999)123-45-67",
        "+7 999-123-45-67",
        "8 999-123-45-67",
        "9991234567",
        "+380 99 999 99 99",  # Украинский номер
        "123",  # Слишком короткий
        "999999999999",  # Слишком длинный
        "",  # Пустой
        "abc",  # Не цифры
    ]
    
    print("Тестирование нормализации телефонов:")
    print("=" * 50)
    
    for phone in test_phones:
        normalized = normalize_phone_number(phone)
        is_valid = validate_phone_format(phone)
        is_russian = is_russian_phone(phone)
        
        print(f"'{phone}' -> '{normalized}' | Valid: {is_valid} | Russian: {is_russian}")
