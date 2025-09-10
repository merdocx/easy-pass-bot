"""
Система оповещений для мониторинга
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
logger = logging.getLogger(__name__)
@dataclass

class Alert:
    """Класс для представления оповещения"""
    id: str
    type: str
    severity: str  # info, warning, error, critical
    message: str
    timestamp: datetime
    source: str
    details: Dict[str, Any]
    resolved: bool = False
    resolved_at: Optional[datetime] = None

class AlertManager:
    """Менеджер оповещений"""
    def __init__(self, log_file: str = "logs/alerts.log"):
        """
        Инициализация менеджера оповещений
        Args:
            log_file: Файл для записи оповещений
        """
        self.alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.log_file = log_file
        self.alert_logger = logging.getLogger('alerts')
        # Настройка логгера для оповещений
        if not self.alert_logger.handlers:
            handler = logging.FileHandler(log_file, encoding='utf-8')
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.alert_logger.addHandler(handler)
            self.alert_logger.setLevel(logging.INFO)
        # Пороговые значения для автоматических оповещений
        self.thresholds = {
            'memory_usage_percent': 85,
            'disk_usage_percent': 90,
            'cpu_usage_percent': 90,
            'db_response_time_ms': 2000,
            'error_rate_percent': 10,
            'rate_limit_violations_per_hour': 50
        }
    def create_alert(self, alert_type: str, severity: str, message: str,
                    source: str, details: Optional[Dict[str, Any]] = None) -> Alert:
        """
        Создание нового оповещения
        Args:
            alert_type: Тип оповещения
            severity: Серьезность (info, warning, error, critical)
            message: Сообщение оповещения
            source: Источник оповещения
            details: Дополнительные детали
        Returns:
            Созданное оповещение
        """
        alert_id = f"{alert_type}_{int(datetime.utcnow().timestamp())}"
        alert = Alert(
            id=alert_id,
            type=alert_type,
            severity=severity,
            message=message,
            timestamp=datetime.utcnow(),
            source=source,
            details=details or {}
        )
        self.alerts[alert_id] = alert
        self.alert_history.append(alert)
        # Логируем оповещение
        self.alert_logger.warning(json.dumps({
            'alert_id': alert_id,
            'type': alert_type,
            'severity': severity,
            'message': message,
            'source': source,
            'details': details or {},
            'timestamp': alert.timestamp.isoformat()
        }, ensure_ascii=False))
        logger.warning(f"Alert created: {alert_type} - {message}")
        return alert
    def resolve_alert(self, alert_id: str) -> bool:
        """
        Разрешение оповещения
        Args:
            alert_id: ID оповещения
        Returns:
            True если оповещение найдено и разрешено
        """
        if alert_id in self.alerts:
            self.alerts[alert_id].resolved = True
            self.alerts[alert_id].resolved_at = datetime.utcnow()
            self.alert_logger.info(json.dumps({
                'alert_id': alert_id,
                'action': 'resolved',
                'timestamp': datetime.utcnow().isoformat()
            }, ensure_ascii=False))
            logger.info(f"Alert resolved: {alert_id}")
            return True
        return False
    def get_active_alerts(self) -> List[Alert]:
        """
        Получение активных оповещений
        Returns:
            Список активных оповещений
        """
        return [alert for alert in self.alerts.values() if not alert.resolved]
    def get_alerts_by_severity(self, severity: str) -> List[Alert]:
        """
        Получение оповещений по серьезности
        Args:
            severity: Серьезность оповещения
        Returns:
            Список оповещений
        """
        return [alert for alert in self.alerts.values()
                if alert.severity == severity and not alert.resolved]
    def get_critical_alerts(self) -> List[Alert]:
        """
        Получение критических оповещений
        Returns:
            Список критических оповещений
        """
        return self.get_alerts_by_severity('critical')
    def check_health_thresholds(self, health_data: Dict[str, Any]) -> List[Alert]:
        """
        Проверка пороговых значений здоровья системы
        Args:
            health_data: Данные о здоровье системы
        Returns:
            Список созданных оповещений
        """
        alerts = []
        # Проверка памяти
        memory_check = health_data.get('checks', {}).get('memory', {})
        if memory_check.get('usage_percent', 0) > self.thresholds['memory_usage_percent']:
            alert = self.create_alert(
                'high_memory_usage',
                'warning' if memory_check['usage_percent'] < 95 else 'critical',
                f"High memory usage: {memory_check['usage_percent']:.1f}%",
                'health_checker',
                memory_check
            )
            alerts.append(alert)
        # Проверка диска
        disk_check = health_data.get('checks', {}).get('disk', {})
        if disk_check.get('usage_percent', 0) > self.thresholds['disk_usage_percent']:
            alert = self.create_alert(
                'high_disk_usage',
                'warning' if disk_check['usage_percent'] < 95 else 'critical',
                f"High disk usage: {disk_check['usage_percent']:.1f}%",
                'health_checker',
                disk_check
            )
            alerts.append(alert)
        # Проверка CPU
        cpu_check = health_data.get('checks', {}).get('cpu', {})
        if cpu_check.get('usage_percent', 0) > self.thresholds['cpu_usage_percent']:
            alert = self.create_alert(
                'high_cpu_usage',
                'warning' if cpu_check['usage_percent'] < 95 else 'critical',
                f"High CPU usage: {cpu_check['usage_percent']:.1f}%",
                'health_checker',
                cpu_check
            )
            alerts.append(alert)
        # Проверка базы данных
        db_check = health_data.get('checks', {}).get('database', {})
        if db_check.get('response_time_ms', 0) > self.thresholds['db_response_time_ms']:
            alert = self.create_alert(
                'slow_database_response',
                'warning',
                f"Slow database response: {db_check['response_time_ms']:.2f}ms",
                'health_checker',
                db_check
            )
            alerts.append(alert)
        return alerts
    def check_rate_limit_violations(self, violations_count: int) -> Optional[Alert]:
        """
        Проверка нарушений rate limiting
        Args:
            violations_count: Количество нарушений за час
        Returns:
            Оповещение если порог превышен
        """
        if violations_count > self.thresholds['rate_limit_violations_per_hour']:
            return self.create_alert(
                'high_rate_limit_violations',
                'warning',
                f"High rate limit violations: {violations_count} per hour",
                'rate_limiter',
                {'violations_count': violations_count}
            )
        return None
    def check_error_rate(self, total_requests: int, error_requests: int) -> Optional[Alert]:
        """
        Проверка частоты ошибок
        Args:
            total_requests: Общее количество запросов
            error_requests: Количество ошибочных запросов
        Returns:
            Оповещение если частота ошибок превышена
        """
        if total_requests == 0:
            return None
        error_rate = (error_requests / total_requests) * 100
        if error_rate > self.thresholds['error_rate_percent']:
            return self.create_alert(
                'high_error_rate',
                'warning' if error_rate < 50 else 'critical',
                f"High error rate: {error_rate:.1f}%",
                'metrics_collector',
                {
                    'error_rate_percent': error_rate,
                    'total_requests': total_requests,
                    'error_requests': error_requests
                }
            )
        return None
    def cleanup_old_alerts(self, days: int = 7):
        """
        Очистка старых оповещений
        Args:
            days: Количество дней для хранения оповещений
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        # Удаляем старые оповещения из истории
        self.alert_history = [
            alert for alert in self.alert_history
            if alert.timestamp > cutoff_date
        ]
        # Удаляем старые активные оповещения
        old_alerts = [
            alert_id for alert_id, alert in self.alerts.items()
            if alert.timestamp < cutoff_date
        ]
        for alert_id in old_alerts:
            del self.alerts[alert_id]
        logger.info(f"Cleaned up {len(old_alerts)} old alerts")
    def get_alert_summary(self) -> Dict[str, Any]:
        """
        Получение сводки по оповещениям
        Returns:
            Словарь со сводкой
        """
        active_alerts = self.get_active_alerts()
        severity_counts = {}
        for alert in active_alerts:
            severity_counts[alert.severity] = severity_counts.get(alert.severity, 0) + 1
        return {
            'total_active_alerts': len(active_alerts),
            'severity_breakdown': severity_counts,
            'critical_alerts': len(self.get_critical_alerts()),
            'oldest_alert': min(active_alerts, key=lambda x: x.timestamp).timestamp.isoformat() if active_alerts else None,
            'newest_alert': max(active_alerts, key=lambda x: x.timestamp).timestamp.isoformat() if active_alerts else None
        }
# Глобальный экземпляр менеджера оповещений
alert_manager = AlertManager()
