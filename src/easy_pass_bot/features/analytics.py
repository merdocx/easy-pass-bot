"""
Сервис аналитики для отслеживания пользовательского поведения
"""
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict
logger = logging.getLogger(__name__)
@dataclass

class UserAction:
    """Действие пользователя"""
    user_id: int
    action: str
    timestamp: datetime
    details: Dict[str, Any]
    success: bool = True
@dataclass

class SessionData:
    """Данные сессии пользователя"""
    user_id: int
    start_time: datetime
    last_activity: datetime
    actions_count: int = 0
    pages_visited: List[str] = None
    def __post_init__(self):
        if self.pages_visited is None:
            self.pages_visited = []

class AnalyticsService:
    """Сервис аналитики пользовательского поведения"""
    def __init__(self, log_file: str = "logs/analytics.log"):
        """
        Инициализация сервиса аналитики
        Args:
            log_file: Файл для записи аналитики
        """
        self.analytics_logger = logging.getLogger('analytics')
        # Настройка логгера для аналитики
        if not self.analytics_logger.handlers:
            handler = logging.FileHandler(log_file, encoding='utf-8')
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.analytics_logger.addHandler(handler)
            self.analytics_logger.setLevel(logging.INFO)
        # Хранение данных
        self.user_actions: List[UserAction] = []
        self.active_sessions: Dict[int, SessionData] = {}
        self.daily_stats: Dict[str, Dict[str, Any]] = {}
        # Метрики
        self.action_counts = Counter()
        self.error_counts = Counter()
        self.user_activity = defaultdict(list)
        self.page_views = Counter()
    def track_action(self, user_id: int, action: str, details: Optional[Dict[str, Any]] = None,
                    success: bool = True):
        """
        Отслеживание действия пользователя
        Args:
            user_id: ID пользователя
            action: Действие
            details: Дополнительные детали
            success: Успешность действия
        """
        action_data = UserAction(
            user_id=user_id,
            action=action,
            timestamp=datetime.utcnow(),
            details=details or {},
            success=success
        )
        self.user_actions.append(action_data)
        # Обновляем метрики
        self.action_counts[action] += 1
        if not success:
            self.error_counts[action] += 1
        self.user_activity[user_id].append(action_data)
        # Обновляем сессию
        self._update_session(user_id, action)
        # Логируем действие
        self.analytics_logger.info(json.dumps(asdict(action_data), default=str, ensure_ascii=False))
    def track_page_view(self, user_id: int, page: str, details: Optional[Dict[str, Any]] = None):
        """
        Отслеживание просмотра страницы
        Args:
            user_id: ID пользователя
            page: Название страницы
            details: Дополнительные детали
        """
        self.page_views[page] += 1
        # Добавляем в сессию
        if user_id in self.active_sessions:
            if page not in self.active_sessions[user_id].pages_visited:
                self.active_sessions[user_id].pages_visited.append(page)
        self.track_action(user_id, "page_view", {
            'page': page,
            **(details or {})
        })
    def start_session(self, user_id: int):
        """
        Начало сессии пользователя
        Args:
            user_id: ID пользователя
        """
        self.active_sessions[user_id] = SessionData(
            user_id=user_id,
            start_time=datetime.utcnow(),
            last_activity=datetime.utcnow()
        )
        self.track_action(user_id, "session_start")
    def end_session(self, user_id: int):
        """
        Завершение сессии пользователя
        Args:
            user_id: ID пользователя
        """
        if user_id in self.active_sessions:
            session = self.active_sessions[user_id]
            duration = datetime.utcnow() - session.start_time
            self.track_action(user_id, "session_end", {
                'duration_seconds': duration.total_seconds(),
                'actions_count': session.actions_count,
                'pages_visited': len(session.pages_visited)
            })
            del self.active_sessions[user_id]
    def _update_session(self, user_id: int, action: str):
        """Обновление данных сессии"""
        if user_id in self.active_sessions:
            session = self.active_sessions[user_id]
            session.last_activity = datetime.utcnow()
            session.actions_count += 1
    def get_user_analytics(self, user_id: int) -> Dict[str, Any]:
        """
        Получение аналитики пользователя
        Args:
            user_id: ID пользователя
        Returns:
            Словарь с аналитикой пользователя
        """
        user_actions = [action for action in self.user_actions if action.user_id == user_id]
        if not user_actions:
            return {'error': 'No data found for user'}
        # Группируем по действиям
        action_counts = Counter(action.action for action in user_actions)
        success_rate = sum(1 for action in user_actions if action.success) / len(user_actions)
        # Время активности
        first_action = min(user_actions, key=lambda x: x.timestamp)
        last_action = max(user_actions, key=lambda x: x.timestamp)
        # Сессия
        session_data = self.active_sessions.get(user_id)
        return {
            'user_id': user_id,
            'total_actions': len(user_actions),
            'action_breakdown': dict(action_counts),
            'success_rate': success_rate,
            'first_activity': first_action.timestamp.isoformat(),
            'last_activity': last_action.timestamp.isoformat(),
            'is_active': session_data is not None,
            'session_duration': (datetime.utcnow() - session_data.start_time).total_seconds() if session_data else None
        }
    def get_global_analytics(self, days: int = 7) -> Dict[str, Any]:
        """
        Получение глобальной аналитики
        Args:
            days: Количество дней для анализа
        Returns:
            Словарь с глобальной аналитикой
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        recent_actions = [action for action in self.user_actions if action.timestamp >= cutoff_date]
        if not recent_actions:
            return {'error': 'No data found for the specified period'}
        # Основные метрики
        total_actions = len(recent_actions)
        unique_users = len(set(action.user_id for action in recent_actions))
        success_rate = sum(1 for action in recent_actions if action.success) / total_actions
        # Топ действий
        top_actions = Counter(action.action for action in recent_actions).most_common(10)
        # Топ страниц
        page_views = [action for action in recent_actions if action.action == "page_view"]
        top_pages = Counter(action.details.get('page', 'unknown') for action in page_views).most_common(10)
        # Активность по дням
        daily_activity = defaultdict(int)
        for action in recent_actions:
            day = action.timestamp.strftime('%Y-%m-%d')
            daily_activity[day] += 1
        return {
            'period_days': days,
            'total_actions': total_actions,
            'unique_users': unique_users,
            'success_rate': success_rate,
            'active_sessions': len(self.active_sessions),
            'top_actions': top_actions,
            'top_pages': top_pages,
            'daily_activity': dict(daily_activity),
            'error_rate': sum(1 for action in recent_actions if not action.success) / total_actions
        }
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Получение метрик производительности
        Returns:
            Словарь с метриками производительности
        """
        # Группируем по часам для анализа пиков
        hourly_activity = defaultdict(int)
        for action in self.user_actions:
            hour = action.timestamp.hour
            hourly_activity[hour] += 1
        # Средняя активность на пользователя
        user_activity_counts = Counter(action.user_id for action in self.user_actions)
        avg_actions_per_user = sum(user_activity_counts.values()) / max(len(user_activity_counts), 1)
        return {
            'total_actions_tracked': len(self.user_actions),
            'active_users': len(user_activity_counts),
            'active_sessions': len(self.active_sessions),
            'avg_actions_per_user': avg_actions_per_user,
            'hourly_distribution': dict(hourly_activity),
            'most_active_hour': max(hourly_activity.items(), key=lambda x: x[1])[0] if hourly_activity else None
        }
    def get_error_analytics(self) -> Dict[str, Any]:
        """
        Получение аналитики ошибок
        Returns:
            Словарь с аналитикой ошибок
        """
        error_actions = [action for action in self.user_actions if not action.success]
        if not error_actions:
            return {'error': 'No errors found'}
        # Группируем по типам ошибок
        error_types = Counter(action.action for action in error_actions)
        # Ошибки по пользователям
        user_errors = Counter(action.user_id for action in error_actions)
        # Ошибки по времени
        hourly_errors = defaultdict(int)
        for action in error_actions:
            hour = action.timestamp.hour
            hourly_errors[hour] += 1
        return {
            'total_errors': len(error_actions),
            'error_rate': len(error_actions) / len(self.user_actions),
            'error_types': dict(error_types),
            'users_with_errors': len(user_errors),
            'top_error_users': user_errors.most_common(10),
            'hourly_error_distribution': dict(hourly_errors)
        }
    def export_data(self, format: str = 'json') -> str:
        """
        Экспорт данных аналитики
        Args:
            format: Формат экспорта ('json' или 'csv')
        Returns:
            Экспортированные данные
        """
        if format == 'json':
            return json.dumps({
                'actions': [asdict(action) for action in self.user_actions],
                'sessions': {str(uid): asdict(session) for uid, session in self.active_sessions.items()},
                'stats': self.get_global_analytics()
            }, default=str, ensure_ascii=False, indent=2)
        elif format == 'csv':
            # Простая CSV экспорт для действий
            csv_data = "user_id,action,timestamp,success,details\n"
            for action in self.user_actions:
                csv_data += f"{action.user_id},{action.action},{action.timestamp.isoformat()},{action.success},{json.dumps(action.details)}\n"
            return csv_data
        else:
            raise ValueError(f"Unsupported format: {format}")
    def cleanup_old_data(self, days: int = 30):
        """
        Очистка старых данных
        Args:
            days: Количество дней для хранения данных
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        # Удаляем старые действия
        self.user_actions = [action for action in self.user_actions if action.timestamp >= cutoff_date]
        # Очищаем неактивные сессии
        current_time = datetime.utcnow()
        inactive_sessions = [
            uid for uid, session in self.active_sessions.items()
            if current_time - session.last_activity > timedelta(hours=24)
        ]
        for uid in inactive_sessions:
            del self.active_sessions[uid]
        logger.info(f"Cleaned up analytics data older than {days} days")
# Глобальный экземпляр сервиса аналитики
analytics_service = AnalyticsService()
