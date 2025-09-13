"""
Утилита для генерации безопасных паролей
"""
import secrets
import string
import logging
import bcrypt

logger = logging.getLogger(__name__)

def generate_secure_password(length: int = 12) -> str:
    """
    Генерация безопасного пароля
    
    Args:
        length: Длина пароля (по умолчанию 12 символов)
        
    Returns:
        str: Сгенерированный пароль
    """
    if length < 8:
        length = 8
        logger.warning(f"Password length too short, using minimum length: {length}")
    
    # Определяем набор символов
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    symbols = "!@#$%^&*"
    
    # Гарантируем наличие разных типов символов
    password = [
        secrets.choice(lowercase),
        secrets.choice(uppercase),
        secrets.choice(digits),
        secrets.choice(symbols)
    ]
    
    # Заполняем оставшуюся длину случайными символами
    all_chars = lowercase + uppercase + digits + symbols
    for _ in range(length - 4):
        password.append(secrets.choice(all_chars))
    
    # Перемешиваем символы
    secrets.SystemRandom().shuffle(password)
    
    result = ''.join(password)
    logger.info(f"Generated secure password of length {len(result)}")
    return result

def generate_admin_password() -> str:
    """
    Генерация пароля специально для администраторов
    Использует более сложные символы для безопасности
    """
    return generate_secure_password(16)

def is_password_strong(password: str) -> bool:
    """
    Проверка силы пароля
    
    Args:
        password: Пароль для проверки
        
    Returns:
        bool: True если пароль достаточно сильный
    """
    if len(password) < 8:
        return False
    
    has_lower = any(c.islower() for c in password)
    has_upper = any(c.isupper() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
    
    return has_lower and has_upper and has_digit and has_special

def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Валидация силы пароля с подробным сообщением
    
    Args:
        password: Пароль для проверки
        
    Returns:
        tuple[bool, str]: (валиден, сообщение об ошибке)
    """
    if len(password) < 8:
        return False, "Пароль должен содержать минимум 8 символов"
    
    if not any(c.islower() for c in password):
        return False, "Пароль должен содержать строчные буквы"
    
    if not any(c.isupper() for c in password):
        return False, "Пароль должен содержать заглавные буквы"
    
    if not any(c.isdigit() for c in password):
        return False, "Пароль должен содержать цифры"
    
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        return False, "Пароль должен содержать специальные символы"
    
    return True, ""


def hash_password(password: str) -> str:
    """
    Хеширование пароля с использованием bcrypt
    
    Args:
        password: Пароль для хеширования
        
    Returns:
        str: Хешированный пароль
    """
    if not password:
        raise ValueError("Password cannot be empty")
    
    # Генерируем соль и хешируем пароль
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    
    return hashed.decode('utf-8')


def verify_password_hash(password: str, hashed_password: str) -> bool:
    """
    Проверка пароля против хеша
    
    Args:
        password: Пароль для проверки
        hashed_password: Хешированный пароль
        
    Returns:
        bool: True если пароль верный, False иначе
    """
    if not password or not hashed_password:
        return False
    
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception as e:
        logger.error(f"Error verifying password: {e}")
        return False


# Примеры использования
if __name__ == "__main__":
    # Тестирование функций
    test_password = generate_secure_password()
    test_hash = hash_password(test_password)
    test_verify = verify_password_hash(test_password, test_hash)
    
    print(f"Generated password: {test_password}")
    print(f"Hash: {test_hash}")
    print(f"Verification: {test_verify}")
