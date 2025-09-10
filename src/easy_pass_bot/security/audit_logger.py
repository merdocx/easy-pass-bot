"""
Система аудита безопасности для логирования всех действий пользователей
"""
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

class AuditLogger:
    """Логгер для аудита безопасности"""
    def __init__(self, log_dir: str = "logs"):
        """
        Инициализация аудит-логгера
        Args:
            log_dir: Директория для логов
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        # Настройка логгера для аудита
        self.logger = logging.getLogger('security_audit')
        self.logger.setLevel(logging.INFO)
        # Убираем дублирующие обработчики
        if not self.logger.handlers:
            # Файловый обработчик для аудита
            audit_file = self.log_dir / 'security_audit.log'
            file_handler = logging.FileHandler(audit_file, encoding='utf-8')
            file_handler.setLevel(logging.INFO)
            # Форматтер для структурированных логов
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            # Консольный обработчик для критических событий
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.WARNING)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
    def _create_log_entry(self, event_type: str, user_id: int,
                         details: Dict[str, Any], severity: str = "INFO") -> Dict[str, Any]:
        """
        Создание записи лога
        Args:
            event_type: Тип события
            user_id: ID пользователя
            details: Детали события
            severity: Уровень серьезности
        Returns:
            Словарь с записью лога
        """
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'user_id': user_id,
            'details': details,
            'severity': severity,
            'session_id': self._get_session_id(user_id)
        }
    def _get_session_id(self, user_id: int) -> str:
        """
        Получение ID сессии пользователя (упрощенная версия)
        Args:
            user_id: ID пользователя
        Returns:
            ID сессии
        """
        # В реальном приложении здесь была бы более сложная логика
        return f"session_{user_id}_{datetime.now().strftime('%Y%m%d')}"
    def log_security_event(self, event_type: str, user_id: int,
                          details: Dict[str, Any], severity: str = "INFO"):
        """
        Логирование события безопасности
        Args:
            event_type: Тип события
            user_id: ID пользователя
            details: Детали события
            severity: Уровень серьезности
        """
        log_entry = self._create_log_entry(event_type, user_id, details, severity)
        # Логируем в файл
        self.logger.info(json.dumps(log_entry, ensure_ascii=False, default=str))
        # Для критических событий также логируем в консоль
        if severity in ["ERROR", "CRITICAL"]:
            self.logger.warning(f"CRITICAL SECURITY EVENT: {event_type} - User: {user_id}")
    def log_failed_attempt(self, user_id: int, attempt_type: str,
                          reason: str, ip_address: Optional[str] = None,
                          additional_data: Optional[Dict[str, Any]] = None):
        """
        Логирование неудачной попытки
        Args:
            user_id: ID пользователя
            attempt_type: Тип попытки (login, registration, etc.)
            reason: Причина неудачи
            ip_address: IP адрес (если доступен)
            additional_data: Дополнительные данные
        """
        details = {
            'attempt_type': attempt_type,
            'reason': reason,
            'ip_address': ip_address,
            'additional_data': additional_data or {}
        }
        self.log_security_event(
            'failed_attempt',
            user_id,
            details,
            'WARNING'
        )
    def log_successful_action(self, user_id: int, action: str,
                             details: Dict[str, Any]):
        """
        Логирование успешного действия
        Args:
            user_id: ID пользователя
            action: Выполненное действие
            details: Детали действия
        """
        self.log_security_event(
            'successful_action',
            user_id,
            {
                'action': action,
                'details': details
            },
            'INFO'
        )
    def log_user_registration(self, user_id: int, registration_data: Dict[str, str]):
        """
        Логирование регистрации пользователя
        Args:
            user_id: ID пользователя
            registration_data: Данные регистрации
        """
        self.log_security_event(
            'user_registration',
            user_id,
            {
                'action': 'registration_attempt',
                'registration_data': {
                    'full_name': registration_data.get('full_name'),
                    'phone_number': registration_data.get('phone_number'),
                    'apartment': registration_data.get('apartment')
                }
            },
            'INFO'
        )
    def log_pass_creation(self, user_id: int, car_number: str):
        """
        Логирование создания пропуска
        Args:
            user_id: ID пользователя
            car_number: Номер автомобиля
        """
        self.log_security_event(
            'pass_creation',
            user_id,
            {
                'action': 'pass_created',
                'car_number': car_number
            },
            'INFO'
        )
    def log_pass_usage(self, user_id: int, pass_id: int, car_number: str,
                      used_by_security_id: int):
        """
        Логирование использования пропуска
        Args:
            user_id: ID владельца пропуска
            pass_id: ID пропуска
            car_number: Номер автомобиля
            used_by_security_id: ID охранника, отметившего использование
        """
        self.log_security_event(
            'pass_usage',
            user_id,
            {
                'action': 'pass_used',
                'pass_id': pass_id,
                'car_number': car_number,
                'used_by_security_id': used_by_security_id
            },
            'INFO'
        )
    def log_admin_action(self, admin_id: int, action: str, target_user_id: int,
                        details: Dict[str, Any]):
        """
        Логирование действий администратора
        Args:
            admin_id: ID администратора
            action: Действие (approve, reject, etc.)
            target_user_id: ID целевого пользователя
            details: Детали действия
        """
        self.log_security_event(
            'admin_action',
            admin_id,
            {
                'action': action,
                'target_user_id': target_user_id,
                'details': details
            },
            'INFO'
        )
    def log_rate_limit_exceeded(self, user_id: int, attempts_count: int):
        """
        Логирование превышения лимита запросов
        Args:
            user_id: ID пользователя
            attempts_count: Количество попыток
        """
        self.log_security_event(
            'rate_limit_exceeded',
            user_id,
            {
                'action': 'rate_limit_exceeded',
                'attempts_count': attempts_count
            },
            'WARNING'
        )
    def log_suspicious_activity(self, user_id: int, activity_type: str,
                               details: Dict[str, Any]):
        """
        Логирование подозрительной активности
        Args:
            user_id: ID пользователя
            activity_type: Тип активности
            details: Детали активности
        """
        self.log_security_event(
            'suspicious_activity',
            user_id,
            {
                'activity_type': activity_type,
                'details': details
            },
            'ERROR'
        )
    def get_recent_events(self, hours: int = 24, event_type: Optional[str] = None) -> list:
        """
        Получение недавних событий из лога
        Args:
            hours: Количество часов назад
            event_type: Фильтр по типу события
        Returns:
            Список событий
        """
        # В реальном приложении здесь была бы более сложная логика чтения логов
        # Для простоты возвращаем пустой список
        return []
    def cleanup_old_logs(self, days: int = 30):
        """
        Очистка старых логов
        Args:
            days: Количество дней для хранения логов
        """
        cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
        for log_file in self.log_dir.glob("*.log"):
            if log_file.stat().st_mtime < cutoff_date:
                log_file.unlink()
                self.logger.info(f"Deleted old log file: {log_file}")
# Глобальный экземпляр аудит-логгера
audit_logger = AuditLogger()
