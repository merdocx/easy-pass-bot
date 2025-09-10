# 🛡️ План улучшения безопасности Easy Pass Bot

## 🎯 Цели безопасности

1. **Защита конфиденциальных данных** пользователей
2. **Предотвращение несанкционированного доступа** к системе
3. **Обеспечение целостности** данных и операций
4. **Быстрое обнаружение и реагирование** на инциденты

---

## 🚨 Критические исправления (0-7 дней)

### 1. Управление секретами

#### Проблема
BOT_TOKEN и другие секреты хранятся в переменных окружения без дополнительной защиты.

#### Решение
```python
# Создать файл: src/easy_pass_bot/security/secrets_manager.py
import os
import base64
from cryptography.fernet import Fernet
from typing import Optional

class SecretsManager:
    def __init__(self):
        self.encryption_key = os.getenv('ENCRYPTION_KEY')
        if not self.encryption_key:
            raise ValueError("ENCRYPTION_KEY not set")
        self.cipher = Fernet(self.encryption_key.encode())
    
    def encrypt_secret(self, secret: str) -> str:
        """Шифрование секрета"""
        return self.cipher.encrypt(secret.encode()).decode()
    
    def decrypt_secret(self, encrypted_secret: str) -> str:
        """Расшифровка секрета"""
        return self.cipher.decrypt(encrypted_secret.encode()).decode()
    
    def get_bot_token(self) -> str:
        """Получение зашифрованного токена бота"""
        encrypted_token = os.getenv('ENCRYPTED_BOT_TOKEN')
        if not encrypted_token:
            raise ValueError("ENCRYPTED_BOT_TOKEN not set")
        return self.decrypt_secret(encrypted_token)

# Обновить config.py
from .security.secrets_manager import SecretsManager

secrets_manager = SecretsManager()
BOT_TOKEN = secrets_manager.get_bot_token()
```

#### Действия
- [ ] Создать SecretsManager
- [ ] Зашифровать существующие токены
- [ ] Обновить конфигурацию
- [ ] Создать скрипт ротации ключей

### 2. HTTPS/TLS принуждение

#### Проблема
Отсутствует принудительное использование HTTPS.

#### Решение
```python
# Создать файл: src/easy_pass_bot/security/ssl_middleware.py
from aiogram import Bot
from aiogram.types import Update
import ssl
import certifi

class SSLEnforcer:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.ssl_context = ssl.create_default_context(cafile=certifi.where())
    
    async def enforce_https(self, update: Update):
        """Принуждение HTTPS для всех запросов"""
        # Проверка заголовков безопасности
        if hasattr(update, 'webhook') and update.webhook:
            # Проверка HTTPS для webhook
            pass
```

#### Действия
- [ ] Настроить SSL сертификаты
- [ ] Добавить SSL middleware
- [ ] Настроить HSTS заголовки
- [ ] Тестировать HTTPS соединения

### 3. Улучшение логирования безопасности

#### Проблема
Аудит-логгер не интегрирован во все критические операции.

#### Решение
```python
# Обновить: src/easy_pass_bot/security/audit_logger.py
class EnhancedAuditLogger(AuditLogger):
    def __init__(self, log_dir: str = "logs"):
        super().__init__(log_dir)
        self.security_events = []
        self.anomaly_detector = AnomalyDetector()
    
    def log_critical_operation(self, operation: str, user_id: int, 
                             details: Dict[str, Any], success: bool):
        """Логирование критических операций"""
        severity = "INFO" if success else "ERROR"
        self.log_security_event(
            f"critical_operation_{operation}",
            user_id,
            {
                'operation': operation,
                'success': success,
                'details': details,
                'timestamp': datetime.utcnow().isoformat()
            },
            severity
        )
        
        # Проверка на аномалии
        if not success:
            self.anomaly_detector.detect_anomaly(user_id, operation, details)
    
    def log_data_access(self, user_id: int, data_type: str, 
                       operation: str, record_id: int):
        """Логирование доступа к данным"""
        self.log_security_event(
            'data_access',
            user_id,
            {
                'data_type': data_type,
                'operation': operation,
                'record_id': record_id,
                'timestamp': datetime.utcnow().isoformat()
            }
        )

# Добавить декоратор для автоматического логирования
def audit_critical_operation(operation_name: str):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            user_id = kwargs.get('user_id') or args[1] if len(args) > 1 else None
            try:
                result = await func(*args, **kwargs)
                audit_logger.log_critical_operation(
                    operation_name, user_id, 
                    {'args': args, 'kwargs': kwargs}, True
                )
                return result
            except Exception as e:
                audit_logger.log_critical_operation(
                    operation_name, user_id, 
                    {'args': args, 'kwargs': kwargs, 'error': str(e)}, False
                )
                raise
        return wrapper
    return decorator
```

#### Действия
- [ ] Расширить AuditLogger
- [ ] Добавить декораторы для автоматического логирования
- [ ] Интегрировать во все критические операции
- [ ] Настроить централизованный сбор логов

---

## ⚠️ Высокие приоритеты (1-2 недели)

### 4. Усиление Rate Limiting

#### Решение
```python
# Обновить: src/easy_pass_bot/security/rate_limiter.py
class AdvancedRateLimiter(RateLimiter):
    def __init__(self, max_requests: int = 10, window: int = 60):
        super().__init__(max_requests, window)
        self.ip_limits = defaultdict(lambda: defaultdict(list))
        self.suspicious_ips = set()
        self.captcha_required = set()
    
    async def is_allowed_with_ip(self, user_id: int, ip_address: str = None) -> bool:
        """Проверка лимитов с учетом IP"""
        # Проверка по пользователю
        if not await self.is_allowed(user_id):
            return False
        
        # Проверка по IP
        if ip_address:
            if ip_address in self.suspicious_ips:
                return False
            
            if ip_address in self.captcha_required:
                # Требуется CAPTCHA
                return False
            
            ip_requests = self.ip_limits[ip_address]['requests']
            now = time.time()
            ip_requests[:] = [req_time for req_time in ip_requests
                             if now - req_time < self.window]
            
            if len(ip_requests) >= self.max_requests:
                self.suspicious_ips.add(ip_address)
                return False
            
            ip_requests.append(now)
        
        return True
    
    def require_captcha(self, user_id: int):
        """Требование CAPTCHA для пользователя"""
        self.captcha_required.add(user_id)
    
    def verify_captcha(self, user_id: int, captcha_response: str) -> bool:
        """Проверка CAPTCHA"""
        # Реализация проверки CAPTCHA
        if captcha_response == "valid":
            self.captcha_required.discard(user_id)
            return True
        return False
```

### 5. Мониторинг безопасности

#### Решение
```python
# Создать: src/easy_pass_bot/security/security_monitor.py
class SecurityMonitor:
    def __init__(self):
        self.alert_manager = AlertManager()
        self.anomaly_detector = AnomalyDetector()
        self.threat_intelligence = ThreatIntelligence()
    
    async def monitor_security_events(self):
        """Мониторинг событий безопасности"""
        while True:
            # Анализ логов на предмет аномалий
            recent_events = await self.get_recent_security_events()
            anomalies = self.anomaly_detector.detect(recent_events)
            
            for anomaly in anomalies:
                await self.handle_security_anomaly(anomaly)
            
            await asyncio.sleep(60)  # Проверка каждую минуту
    
    async def handle_security_anomaly(self, anomaly):
        """Обработка аномалии безопасности"""
        if anomaly.severity == "CRITICAL":
            # Немедленное уведомление
            await self.send_critical_alert(anomaly)
            # Блокировка подозрительного IP/пользователя
            await self.block_suspicious_activity(anomaly)
        elif anomaly.severity == "HIGH":
            # Уведомление администраторов
            await self.send_high_priority_alert(anomaly)
```

### 6. Улучшение обработки ошибок

#### Решение
```python
# Создать: src/easy_pass_bot/security/error_handler.py
class SecureErrorHandler:
    def __init__(self):
        self.error_tracker = ErrorTracker()
        self.audit_logger = AuditLogger()
    
    def handle_error(self, error: Exception, context: Dict[str, Any]):
        """Безопасная обработка ошибок"""
        # Логирование ошибки
        self.audit_logger.log_security_event(
            'error_occurred',
            context.get('user_id', 0),
            {
                'error_type': type(error).__name__,
                'error_message': str(error),
                'context': self.sanitize_context(context),
                'timestamp': datetime.utcnow().isoformat()
            },
            'ERROR'
        )
        
        # Отслеживание ошибок
        self.error_tracker.track_error(error, context)
        
        # Возврат безопасного сообщения пользователю
        return self.get_safe_error_message(error)
    
    def get_safe_error_message(self, error: Exception) -> str:
        """Получение безопасного сообщения об ошибке"""
        # Не раскрываем технические детали
        if isinstance(error, DatabaseError):
            return "Произошла ошибка при работе с данными. Попробуйте позже."
        elif isinstance(error, ValidationError):
            return "Проверьте правильность введенных данных."
        else:
            return "Произошла внутренняя ошибка. Обратитесь к администратору."
    
    def sanitize_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Очистка контекста от чувствительных данных"""
        sanitized = {}
        for key, value in context.items():
            if key in ['password', 'token', 'secret']:
                sanitized[key] = '[REDACTED]'
            else:
                sanitized[key] = value
        return sanitized
```

---

## 🟡 Средние приоритеты (2-4 недели)

### 7. Двухфакторная аутентификация

```python
# Создать: src/easy_pass_bot/security/two_factor_auth.py
import pyotp
import qrcode
from io import BytesIO

class TwoFactorAuth:
    def __init__(self):
        self.totp = pyotp.TOTP
    
    def generate_secret(self, user_id: int) -> str:
        """Генерация секрета для 2FA"""
        secret = pyotp.random_base32()
        # Сохранение в базе данных
        return secret
    
    def generate_qr_code(self, secret: str, user_email: str) -> BytesIO:
        """Генерация QR кода для настройки 2FA"""
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user_email,
            issuer_name="Easy Pass Bot"
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        return img_bytes
    
    def verify_code(self, secret: str, code: str) -> bool:
        """Проверка 2FA кода"""
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=1)
```

### 8. Шифрование чувствительных данных

```python
# Создать: src/easy_pass_bot/security/encryption.py
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

class DataEncryption:
    def __init__(self, password: str):
        self.password = password.encode()
        self.salt = b'easy_pass_salt_2025'  # В продакшене использовать случайную соль
        self.key = self._derive_key()
        self.cipher = Fernet(self.key)
    
    def _derive_key(self) -> bytes:
        """Получение ключа шифрования"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(self.password))
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Шифрование чувствительных данных"""
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Расшифровка чувствительных данных"""
        return self.cipher.decrypt(encrypted_data.encode()).decode()
```

---

## 🟢 Низкие приоритеты (1-2 месяца)

### 9. Централизованная система авторизации

```python
# Создать: src/easy_pass_bot/security/authorization.py
class AuthorizationManager:
    def __init__(self):
        self.permissions = {
            'resident': ['create_pass', 'view_own_passes', 'cancel_own_pass'],
            'security': ['search_passes', 'mark_pass_used', 'view_all_passes'],
            'admin': ['approve_users', 'reject_users', 'view_statistics', 'manage_users']
        }
    
    def has_permission(self, user_role: str, action: str) -> bool:
        """Проверка разрешений"""
        return action in self.permissions.get(user_role, [])
    
    def check_authorization(self, user_id: int, action: str) -> bool:
        """Проверка авторизации для действия"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        
        return self.has_permission(user.role, action)
```

### 10. Мониторинг производительности

```python
# Создать: src/easy_pass_bot/monitoring/performance_monitor.py
class PerformanceMonitor:
    def __init__(self):
        self.metrics = defaultdict(list)
        self.alert_thresholds = {
            'response_time': 2000,  # мс
            'memory_usage': 85,     # %
            'cpu_usage': 90,        # %
            'error_rate': 5         # %
        }
    
    async def track_operation(self, operation_name: str, func, *args, **kwargs):
        """Отслеживание производительности операции"""
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss
        
        try:
            result = await func(*args, **kwargs)
            success = True
        except Exception as e:
            result = None
            success = False
            raise
        finally:
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss
            
            duration = (end_time - start_time) * 1000  # мс
            memory_delta = end_memory - start_memory
            
            self.metrics[operation_name].append({
                'duration': duration,
                'memory_delta': memory_delta,
                'success': success,
                'timestamp': time.time()
            })
            
            # Проверка пороговых значений
            await self.check_thresholds(operation_name, duration, memory_delta, success)
        
        return result
```

---

## 📋 Чек-лист внедрения

### Неделя 1
- [ ] Создать SecretsManager
- [ ] Зашифровать BOT_TOKEN
- [ ] Настроить SSL сертификаты
- [ ] Расширить AuditLogger
- [ ] Добавить декораторы логирования

### Неделя 2
- [ ] Реализовать AdvancedRateLimiter
- [ ] Добавить IP-based ограничения
- [ ] Создать SecurityMonitor
- [ ] Настроить алерты
- [ ] Улучшить обработку ошибок

### Неделя 3
- [ ] Интегрировать 2FA для админов
- [ ] Добавить шифрование данных
- [ ] Создать AuthorizationManager
- [ ] Настроить мониторинг производительности

### Неделя 4
- [ ] Провести тестирование безопасности
- [ ] Обновить документацию
- [ ] Обучить команду
- [ ] Провести повторный аудит

---

## 🧪 Тестирование безопасности

### Автоматизированные тесты
```bash
# Запуск тестов безопасности
pytest tests/unit/security/ -v --tb=short

# Анализ зависимостей
pip-audit

# Статический анализ
bandit -r src/easy_pass_bot/

# Проверка на уязвимости
safety check
```

### Ручное тестирование
- [ ] Penetration testing
- [ ] Социальная инженерия
- [ ] Тестирование на отказ в обслуживании
- [ ] Проверка конфигурации

---

## 📊 Метрики успеха

### Ключевые показатели
- **Время обнаружения инцидентов**: < 5 минут
- **Время реагирования**: < 15 минут
- **Покрытие логированием**: > 95%
- **Успешность тестов безопасности**: > 95%
- **Количество ложных срабатываний**: < 5%

### Мониторинг
- Ежедневные отчеты по безопасности
- Еженедельные метрики производительности
- Ежемесячные отчеты по инцидентам
- Ежеквартальные аудиты безопасности

---

*Этот план должен быть адаптирован под конкретные потребности и ресурсы проекта.*


