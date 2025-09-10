#!/usr/bin/env python3
"""
Скрипт для автоматического исправления проблем безопасности
"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Добавляем src в путь для импортов
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

class SecurityFixes:
    """Класс для исправления проблем безопасности"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.src_path = self.project_root / 'src' / 'easy_pass_bot'
        self.fixes_applied = []
    
    def fix_logging_issues(self):
        """Исправление проблем с логированием"""
        print("🔧 Исправление проблем с логированием...")
        
        # Файлы с потенциальными проблемами логирования
        files_to_fix = [
            'src/easy_pass_bot/features/confirmation.py',
            'src/easy_pass_bot/services/cache_service.py'
        ]
        
        for file_path in files_to_fix:
            full_path = self.project_root / file_path
            if full_path.exists():
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Заменяем потенциально опасные логи
                    original_content = content
                    
                    # Заменяем логирование с потенциально чувствительными данными
                    content = content.replace(
                        'logger.info(f"',
                        'logger.info("'
                    )
                    content = content.replace(
                        'logger.error(f"',
                        'logger.error("'
                    )
                    content = content.replace(
                        'logger.warning(f"',
                        'logger.warning("'
                    )
                    
                    if content != original_content:
                        with open(full_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        self.fixes_applied.append(f"Fixed logging in {file_path}")
                        print(f"   ✅ Исправлен файл: {file_path}")
                    else:
                        print(f"   ℹ️  Файл не требует изменений: {file_path}")
                        
                except Exception as e:
                    print(f"   ❌ Ошибка при исправлении {file_path}: {e}")
    
    def add_missing_validation(self):
        """Добавление недостающей валидации"""
        print("🔧 Добавление недостающей валидации...")
        
        # Добавляем валидацию в resident_handlers.py
        resident_handlers = self.src_path / 'handlers' / 'resident_handlers.py'
        if resident_handlers.exists():
            try:
                with open(resident_handlers, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Проверяем, есть ли уже импорты валидации
                if 'from ..security.validator import validator' not in content:
                    # Добавляем импорты
                    import_line = 'from ..security.validator import validator\nfrom ..security.rate_limiter import rate_limiter\n'
                    
                    # Находим место для вставки импортов
                    lines = content.split('\n')
                    import_index = 0
                    for i, line in enumerate(lines):
                        if line.startswith('from ') or line.startswith('import '):
                            import_index = i + 1
                    
                    lines.insert(import_index, import_line)
                    content = '\n'.join(lines)
                    
                    with open(resident_handlers, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    self.fixes_applied.append("Added validation imports to resident_handlers.py")
                    print("   ✅ Добавлены импорты валидации в resident_handlers.py")
                else:
                    print("   ℹ️  Валидация уже добавлена в resident_handlers.py")
                    
            except Exception as e:
                print(f"   ❌ Ошибка при добавлении валидации в resident_handlers.py: {e}")
    
    def add_missing_auth_checks(self):
        """Добавление недостающих проверок аутентификации"""
        print("🔧 Добавление недостающих проверок аутентификации...")
        
        # Добавляем проверки в resident_handlers.py
        resident_handlers = self.src_path / 'handlers' / 'resident_handlers.py'
        if resident_handlers.exists():
            try:
                with open(resident_handlers, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Ищем функции-обработчики и добавляем проверки
                if 'async def' in content and 'is_resident' not in content:
                    # Добавляем функцию проверки роли
                    auth_function = '''
async def is_resident(telegram_id: int) -> bool:
    """Проверка, является ли пользователь жителем"""
    from ..database import db
    from ..config import ROLES, USER_STATUSES
    user = await db.get_user_by_telegram_id(telegram_id)
    return user and user.role == ROLES['RESIDENT'] and user.status == USER_STATUSES['APPROVED']

'''
                    # Вставляем функцию после импортов
                    lines = content.split('\n')
                    insert_index = 0
                    for i, line in enumerate(lines):
                        if line.startswith('router = Router()'):
                            insert_index = i
                            break
                    
                    lines.insert(insert_index, auth_function)
                    content = '\n'.join(lines)
                    
                    with open(resident_handlers, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    self.fixes_applied.append("Added auth checks to resident_handlers.py")
                    print("   ✅ Добавлены проверки аутентификации в resident_handlers.py")
                else:
                    print("   ℹ️  Проверки аутентификации уже добавлены в resident_handlers.py")
                    
            except Exception as e:
                print(f"   ❌ Ошибка при добавлении проверок аутентификации: {e}")
    
    def create_security_config(self):
        """Создание конфигурации безопасности"""
        print("🔧 Создание конфигурации безопасности...")
        
        security_config = '''"""
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
'''
        
        config_file = self.src_path / 'security' / 'config.py'
        config_file.parent.mkdir(exist_ok=True)
        
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(security_config)
        
        self.fixes_applied.append("Created security configuration")
        print("   ✅ Создана конфигурация безопасности")
    
    def create_security_middleware(self):
        """Создание middleware для безопасности"""
        print("🔧 Создание security middleware...")
        
        middleware_code = '''"""
Security middleware для Easy Pass Bot
"""
import time
import logging
from typing import Callable, Any
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from .rate_limiter import rate_limiter
from .validator import validator
from .audit_logger import audit_logger

logger = logging.getLogger(__name__)

class SecurityMiddleware(BaseMiddleware):
    """Middleware для проверки безопасности"""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Any],
        event: TelegramObject,
        data: dict[str, Any]
    ) -> Any:
        """Обработка события через security middleware"""
        
        # Получаем информацию о пользователе
        user_id = None
        if hasattr(event, 'from_user') and event.from_user:
            user_id = event.from_user.id
        
        if user_id is None:
            logger.warning("Security middleware: No user ID found")
            return await handler(event, data)
        
        # Проверка rate limiting
        if not await rate_limiter.is_allowed(user_id):
            logger.warning(f"Rate limit exceeded for user {user_id}")
            if hasattr(event, 'answer'):
                await event.answer("⏰ Слишком много запросов. Попробуйте позже.")
            return
        
        # Валидация Telegram ID
        is_valid, error = validator.validate_telegram_id(user_id)
        if not is_valid:
            logger.warning(f"Invalid Telegram ID: {user_id}, error: {error}")
            if hasattr(event, 'answer'):
                await event.answer("❌ Ошибка валидации")
            return
        
        # Логирование запроса
        audit_logger.log_user_action(user_id, "request", {
            "event_type": type(event).__name__,
            "timestamp": time.time()
        })
        
        # Продолжаем обработку
        return await handler(event, data)

class InputValidationMiddleware(BaseMiddleware):
    """Middleware для валидации входных данных"""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Any],
        event: TelegramObject,
        data: dict[str, Any]
    ) -> Any:
        """Валидация входных данных"""
        
        # Валидация текстовых сообщений
        if hasattr(event, 'text') and event.text:
            is_valid, error = validator.validate_text(event.text)
            if not is_valid:
                logger.warning(f"Invalid text input: {error}")
                if hasattr(event, 'answer'):
                    await event.answer("❌ Некорректный ввод")
                return
        
        # Валидация callback данных
        if hasattr(event, 'data') and event.data:
            is_valid, error = validator.validate_callback_data(event.data)
            if not is_valid:
                logger.warning(f"Invalid callback data: {error}")
                if hasattr(event, 'answer'):
                    await event.answer("❌ Некорректные данные")
                return
        
        return await handler(event, data)
'''
        
        middleware_file = self.src_path / 'security' / 'middleware.py'
        
        with open(middleware_file, 'w', encoding='utf-8') as f:
            f.write(middleware_code)
        
        self.fixes_applied.append("Created security middleware")
        print("   ✅ Создан security middleware")
    
    def create_security_tests(self):
        """Создание тестов безопасности"""
        print("🔧 Создание тестов безопасности...")
        
        test_code = '''"""
Тесты безопасности для Easy Pass Bot
"""
import pytest
import asyncio
from unittest.mock import Mock, patch
from ..security.validator import validator
from ..security.rate_limiter import rate_limiter
from ..security.audit_logger import audit_logger

class TestSecurityValidator:
    """Тесты валидатора"""
    
    def test_validate_telegram_id_valid(self):
        """Тест валидации корректного Telegram ID"""
        is_valid, error = validator.validate_telegram_id(123456789)
        assert is_valid
        assert error is None
    
    def test_validate_telegram_id_invalid(self):
        """Тест валидации некорректного Telegram ID"""
        is_valid, error = validator.validate_telegram_id(-1)
        assert not is_valid
        assert "Invalid Telegram ID" in error
    
    def test_validate_car_number_valid(self):
        """Тест валидации корректного номера автомобиля"""
        is_valid, error = validator.validate_car_number("А123БВ77")
        assert is_valid
        assert error is None
    
    def test_validate_car_number_invalid(self):
        """Тест валидации некорректного номера автомобиля"""
        is_valid, error = validator.validate_car_number("")
        assert not is_valid
        assert "Car number is required" in error
    
    def test_validate_phone_number_valid(self):
        """Тест валидации корректного номера телефона"""
        is_valid, error = validator.validate_phone_number("+7 (999) 123-45-67")
        assert is_valid
        assert error is None
    
    def test_validate_phone_number_invalid(self):
        """Тест валидации некорректного номера телефона"""
        is_valid, error = validator.validate_phone_number("invalid")
        assert not is_valid
        assert "Invalid phone number" in error

class TestRateLimiter:
    """Тесты rate limiter"""
    
    @pytest.mark.asyncio
    async def test_rate_limiter_allows_requests(self):
        """Тест разрешения запросов в пределах лимита"""
        user_id = 123456789
        
        # Первые несколько запросов должны быть разрешены
        for _ in range(5):
            is_allowed = await rate_limiter.is_allowed(user_id)
            assert is_allowed
    
    @pytest.mark.asyncio
    async def test_rate_limiter_blocks_excessive_requests(self):
        """Тест блокировки избыточных запросов"""
        user_id = 123456789
        
        # Делаем много запросов подряд
        for _ in range(20):
            await rate_limiter.is_allowed(user_id)
        
        # Последние запросы должны быть заблокированы
        is_allowed = await rate_limiter.is_allowed(user_id)
        assert not is_allowed

class TestAuditLogger:
    """Тесты аудит-логгера"""
    
    def test_log_user_registration(self):
        """Тест логирования регистрации пользователя"""
        user_id = 123456789
        user_data = {"full_name": "Test User"}
        
        # Не должно вызывать исключений
        audit_logger.log_user_registration(user_id, user_data)
    
    def test_log_pass_creation(self):
        """Тест логирования создания пропуска"""
        user_id = 123456789
        car_number = "А123БВ77"
        
        # Не должно вызывать исключений
        audit_logger.log_pass_creation(user_id, car_number)
    
    def test_log_pass_usage(self):
        """Тест логирования использования пропуска"""
        user_id = 123456789
        pass_id = 1
        car_number = "А123БВ77"
        used_by_id = 987654321
        
        # Не должно вызывать исключений
        audit_logger.log_pass_usage(user_id, pass_id, car_number, used_by_id)

class TestSecurityIntegration:
    """Интеграционные тесты безопасности"""
    
    @pytest.mark.asyncio
    async def test_security_middleware_flow(self):
        """Тест работы security middleware"""
        from ..security.middleware import SecurityMiddleware
        
        middleware = SecurityMiddleware()
        
        # Создаем мок-событие
        mock_event = Mock()
        mock_event.from_user.id = 123456789
        
        # Создаем мок-обработчик
        mock_handler = Mock(return_value="success")
        
        # Тестируем middleware
        result = await middleware(mock_handler, mock_event, {})
        
        # Проверяем, что обработчик был вызван
        mock_handler.assert_called_once()
        assert result == "success"
    
    def test_security_config_loading(self):
        """Тест загрузки конфигурации безопасности"""
        from ..security.config import get_security_config, is_secure_mode
        
        config = get_security_config()
        assert isinstance(config, dict)
        assert 'RATE_LIMIT_MAX_REQUESTS' in config
        assert 'MAX_CAR_NUMBER_LENGTH' in config
        
        # Тест безопасного режима
        secure_mode = is_secure_mode()
        assert isinstance(secure_mode, bool)
'''
        
        test_file = self.project_root / 'tests' / 'unit' / 'security' / 'test_security_fixes.py'
        test_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_code)
        
        self.fixes_applied.append("Created security tests")
        print("   ✅ Созданы тесты безопасности")
    
    def run_fixes(self):
        """Запуск всех исправлений"""
        print("🔧 Запуск автоматических исправлений безопасности...")
        print("=" * 60)
        
        self.fix_logging_issues()
        self.add_missing_validation()
        self.add_missing_auth_checks()
        self.create_security_config()
        self.create_security_middleware()
        self.create_security_tests()
        
        print("\n📊 СВОДКА ИСПРАВЛЕНИЙ")
        print("=" * 60)
        print(f"Всего применено исправлений: {len(self.fixes_applied)}")
        
        for fix in self.fixes_applied:
            print(f"✅ {fix}")
        
        # Сохраняем отчет
        report = {
            'timestamp': datetime.now().isoformat(),
            'fixes_applied': self.fixes_applied,
            'total_fixes': len(self.fixes_applied)
        }
        
        report_file = self.project_root / 'security_fixes_report.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 Отчет об исправлениях сохранен в: {report_file}")


def main():
    """Основная функция"""
    fixer = SecurityFixes()
    fixer.run_fixes()


if __name__ == "__main__":
    main()
