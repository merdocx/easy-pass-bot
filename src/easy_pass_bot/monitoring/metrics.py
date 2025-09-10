"""
Система сбора метрик для мониторинга производительности
"""
import time
import logging
from collections import defaultdict
from typing import Dict, Any, Optional
from datetime import datetime
import json
import os
logger = logging.getLogger(__name__)

class MetricsCollector:
    """Сборщик метрик для мониторинга"""
    def __init__(self, log_file: str = "logs/metrics.log"):
        """
        Инициализация сборщика метрик
        Args:
            log_file: Файл для записи метрик
        """
        self.metrics = defaultdict(int)
        self.timers = {}
        self.gauges = {}
        self.log_file = log_file
        self.logger = logging.getLogger('metrics')
        # Создаем директорию для логов
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        # Настройка логгера для метрик
        if not self.logger.handlers:
            handler = logging.FileHandler(log_file, encoding='utf-8')
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    def _build_key(self, metric_name: str, tags: Optional[Dict[str, str]] = None) -> str:
        """
        Построение ключа метрики с тегами
        Args:
            metric_name: Название метрики
            tags: Теги для метрики
        Returns:
            Ключ метрики
        """
        if not tags:
            return metric_name
        tag_str = ",".join([f"{k}={v}" for k, v in sorted(tags.items())])
        return f"{metric_name}[{tag_str}]"
    def increment(self, metric_name: str, value: int = 1,
                 tags: Optional[Dict[str, str]] = None):
        """
        Увеличение счетчика метрики
        Args:
            metric_name: Название метрики
            value: Значение для увеличения
            tags: Теги для метрики
        """
        key = self._build_key(metric_name, tags)
        self.metrics[key] += value
        # Логируем метрику
        self.logger.info(json.dumps({
            'type': 'counter',
            'metric': metric_name,
            'value': value,
            'tags': tags or {},
            'timestamp': datetime.utcnow().isoformat()
        }, ensure_ascii=False))
    def set_gauge(self, metric_name: str, value: float,
                  tags: Optional[Dict[str, str]] = None):
        """
        Установка значения метрики-счетчика
        Args:
            metric_name: Название метрики
            value: Значение
            tags: Теги для метрики
        """
        key = self._build_key(metric_name, tags)
        self.gauges[key] = value
        # Логируем метрику
        self.logger.info(json.dumps({
            'type': 'gauge',
            'metric': metric_name,
            'value': value,
            'tags': tags or {},
            'timestamp': datetime.utcnow().isoformat()
        }, ensure_ascii=False))
    def start_timer(self, metric_name: str, tags: Optional[Dict[str, str]] = None) -> str:
        """
        Запуск таймера
        Args:
            metric_name: Название метрики
            tags: Теги для метрики
        Returns:
            ID таймера
        """
        timer_id = f"{metric_name}_{int(time.time() * 1000)}"
        key = self._build_key(metric_name, tags)
        self.timers[timer_id] = {
            'key': key,
            'start_time': time.time(),
            'tags': tags or {}
        }
        return timer_id
    def end_timer(self, timer_id: str):
        """
        Остановка таймера
        Args:
            timer_id: ID таймера
        """
        if timer_id not in self.timers:
            logger.warning(f"Timer {timer_id} not found")
            return
        timer_data = self.timers[timer_id]
        duration = time.time() - timer_data['start_time']
        # Сохраняем длительность
        self.metrics[f"{timer_data['key']}_duration"] = duration
        # Логируем метрику
        self.logger.info(json.dumps({
            'type': 'timer',
            'metric': timer_data['key'],
            'duration': duration,
            'tags': timer_data['tags'],
            'timestamp': datetime.utcnow().isoformat()
        }, ensure_ascii=False))
        del self.timers[timer_id]
    def record_response_time(self, handler_name: str, duration: float,
                           status: str = "success", user_id: Optional[int] = None):
        """
        Запись времени ответа обработчика
        Args:
            handler_name: Название обработчика
            duration: Время выполнения в секундах
            status: Статус выполнения
            user_id: ID пользователя
        """
        tags = {
            'handler': handler_name,
            'status': status
        }
        if user_id:
            tags['user_id'] = str(user_id)
        self.set_gauge('response_time', duration, tags)
        self.increment('requests_total', 1, tags)
    def record_user_action(self, action: str, user_id: int, success: bool = True):
        """
        Запись действия пользователя
        Args:
            action: Действие пользователя
            user_id: ID пользователя
            success: Успешность действия
        """
        tags = {
            'action': action,
            'user_id': str(user_id),
            'status': 'success' if success else 'error'
        }
        self.increment('user_actions', 1, tags)
    def record_database_operation(self, operation: str, table: str,
                                duration: float, success: bool = True):
        """
        Запись операции с базой данных
        Args:
            operation: Тип операции (SELECT, INSERT, UPDATE, DELETE)
            table: Название таблицы
            duration: Время выполнения
            success: Успешность операции
        """
        tags = {
            'operation': operation,
            'table': table,
            'status': 'success' if success else 'error'
        }
        self.record_response_time('database', duration, 'success' if success else 'error')
        self.increment('database_operations', 1, tags)
    def record_error(self, error_type: str, handler_name: str,
                    user_id: Optional[int] = None, error_message: str = ""):
        """
        Запись ошибки
        Args:
            error_type: Тип ошибки
            handler_name: Название обработчика
            user_id: ID пользователя
            error_message: Сообщение об ошибке
        """
        tags = {
            'error_type': error_type,
            'handler': handler_name
        }
        if user_id:
            tags['user_id'] = str(user_id)
        self.increment('errors_total', 1, tags)
        # Логируем детали ошибки
        self.logger.error(json.dumps({
            'type': 'error',
            'error_type': error_type,
            'handler': handler_name,
            'user_id': user_id,
            'message': error_message,
            'timestamp': datetime.utcnow().isoformat()
        }, ensure_ascii=False))
    def get_metrics_summary(self) -> Dict[str, Any]:
        """
        Получение сводки по метрикам
        Returns:
            Словарь с метриками
        """
        now = time.time()
        # Очищаем старые таймеры (старше 1 часа)
        expired_timers = [
            tid for tid, data in self.timers.items()
            if now - data['start_time'] > 3600
        ]
        for tid in expired_timers:
            del self.timers[tid]
        return {
            'counters': dict(self.metrics),
            'gauges': dict(self.gauges),
            'active_timers': len(self.timers),
            'timestamp': datetime.utcnow().isoformat()
        }
    def get_metrics_for_period(self, hours: int = 1) -> Dict[str, Any]:
        """
        Получение метрик за период
        Args:
            hours: Количество часов назад
        Returns:
            Метрики за период
        """
        # В реальном приложении здесь была бы более сложная логика
        # для чтения метрик из файла за определенный период
        return self.get_metrics_summary()
    def reset_metrics(self):
        """Сброс всех метрик"""
        self.metrics.clear()
        self.gauges.clear()
        self.timers.clear()
        logger.info("Metrics reset")
# Глобальный экземпляр сборщика метрик
metrics_collector = MetricsCollector()
