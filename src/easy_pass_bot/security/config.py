"""
Конфигурация безопасности Easy Pass Bot
"""
import os
from typing import Dict, Any

# Настройки безопасности
SECURITY_CONFIG = {
    # Rate limiting
    'RATE_LIMIT_MAX_REQUESTS': int(os.getenv('RATE_LIMIT_MAX_REQUESTS', '15')),
    'RATE_LIMIT_WINDOW_SECONDS': int(os.getenv('RATE_LIMIT_WINDOW_SECONDS', '60')),
    
    # Валидация
    'MAX_CAR_NUMBER_LENGTH': 20,
    'MAX_NAME_LENGTH': 100,
    'MAX_PHONE_LENGTH': 20,
    'MAX_APARTMENT_LENGTH': 10,
    
    # Аутентификация
    'SESSION_TIMEOUT_MINUTES': 30,
    'MAX_LOGIN_ATTEMPTS': 5,
    'LOCKOUT_DURATION_MINUTES': 15,
    
    # Логирование
    'LOG_SENSITIVE_DATA': False,
    'AUDIT_LOG_RETENTION_DAYS': 90,
    
    # Шифрование
    'ENCRYPTION_KEY_LENGTH': 32,
    'HASH_ALGORITHM': 'sha256',
    'SALT_LENGTH': 16,
    
    # Мониторинг
    'SECURITY_ALERT_THRESHOLD': 10,
    'MONITORING_INTERVAL_SECONDS': 300,
    
    # Файлы
    'ALLOWED_FILE_EXTENSIONS': ['.jpg', '.jpeg', '.png', '.pdf'],
    'MAX_FILE_SIZE_MB': 5,
    'UPLOAD_DIR': 'uploads',
    
    # База данных
    'DB_CONNECTION_TIMEOUT': 30,
    'DB_QUERY_TIMEOUT': 10,
    'DB_MAX_CONNECTIONS': 10,
    
    # API
    'API_RATE_LIMIT_PER_MINUTE': 100,
    'API_TIMEOUT_SECONDS': 30,
    'CORS_ALLOWED_ORIGINS': ['*'],
    
    # Уведомления
    'NOTIFICATION_RETRY_ATTEMPTS': 3,
    'NOTIFICATION_TIMEOUT_SECONDS': 30,
    'ADMIN_NOTIFICATION_ENABLED': True,
    
    # Архивация
    'ARCHIVE_INTERVAL_HOURS': 6,
    'ARCHIVE_USED_PASSES_HOURS': 24,
    'ARCHIVE_UNUSED_PASSES_DAYS': 7,
    'ARCHIVE_CLEANUP_DAYS': 30
}

def get_security_config() -> Dict[str, Any]:
    """Получить конфигурацию безопасности"""
    return SECURITY_CONFIG.copy()

def is_secure_mode() -> bool:
    """Проверить, включен ли безопасный режим"""
    return os.getenv('SECURE_MODE', 'false').lower() == 'true'

def get_encryption_key() -> str:
    """Получить ключ шифрования"""
    key = os.getenv('ENCRYPTION_KEY')
    if not key:
        raise ValueError("ENCRYPTION_KEY environment variable is required")
    if len(key) != 32:
        raise ValueError("ENCRYPTION_KEY must be exactly 32 characters long")
    return key
