"""
Сервис навигации для улучшения пользовательского опыта
"""
import logging
from typing import Dict, Any, Optional, List
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
logger = logging.getLogger(__name__)

class NavigationService:
    """Сервис навигации с хлебными крошками и историей"""
    def __init__(self):
        self.user_history: Dict[int, List[str]] = {}
        self.nav_logger = logging.getLogger('navigation')
    def add_to_history(self, user_id: int, page: str, context: Optional[Dict[str, Any]] = None):
        """
        Добавление страницы в историю пользователя
        Args:
            user_id: ID пользователя
            page: Название страницы
            context: Дополнительный контекст
        """
        if user_id not in self.user_history:
            self.user_history[user_id] = []
        # Ограничиваем историю 10 страницами
        if len(self.user_history[user_id]) >= 10:
            self.user_history[user_id].pop(0)
        self.user_history[user_id].append(page)
        self.nav_logger.debug(f"Added to history for user {user_id}: {page}")
    def get_history(self, user_id: int) -> List[str]:
        """
        Получение истории навигации пользователя
        Args:
            user_id: ID пользователя
        Returns:
            Список страниц в истории
        """
        return self.user_history.get(user_id, [])
    def get_previous_page(self, user_id: int) -> Optional[str]:
        """
        Получение предыдущей страницы
        Args:
            user_id: ID пользователя
        Returns:
            Название предыдущей страницы или None
        """
        history = self.get_history(user_id)
        if len(history) >= 2:
            return history[-2]
        return None
    def clear_history(self, user_id: int):
        """
        Очистка истории пользователя
        Args:
            user_id: ID пользователя
        """
        if user_id in self.user_history:
            del self.user_history[user_id]
            self.nav_logger.debug(f"Cleared history for user {user_id}")
    def create_breadcrumb_keyboard(self, current_page: str, user_id: int,
                                 additional_buttons: Optional[List[Dict[str, str]]] = None) -> InlineKeyboardMarkup:
        """
        Создание клавиатуры с хлебными крошками
        Args:
            current_page: Текущая страница
            user_id: ID пользователя
            additional_buttons: Дополнительные кнопки
        Returns:
            Inline клавиатура с навигацией
        """
        builder = InlineKeyboardBuilder()
        # Добавляем кнопку "Назад" если есть история
        history = self.get_history(user_id)
        if len(history) > 1:
            builder.button(text="🔙 Назад", callback_data="nav_back")
        # Добавляем кнопку "Главная"
        if current_page != "main":
            builder.button(text="🏠 Главная", callback_data="nav_main")
        # Добавляем дополнительные кнопки
        if additional_buttons:
            for button in additional_buttons:
                builder.button(
                    text=button['text'],
                    callback_data=button['callback_data']
                )
        # Настраиваем количество кнопок в ряду
        builder.adjust(2)
        return builder.as_markup()
    def create_pagination_keyboard(self, current_page: int, total_pages: int,
                                 base_callback: str, **kwargs) -> InlineKeyboardMarkup:
        """
        Создание клавиатуры пагинации
        Args:
            current_page: Текущая страница
            total_pages: Общее количество страниц
            base_callback: Базовый callback для кнопок
            **kwargs: Дополнительные параметры для callback
        Returns:
            Inline клавиатура с пагинацией
        """
        builder = InlineKeyboardBuilder()
        # Кнопка "Предыдущая"
        if current_page > 1:
            prev_callback = f"{base_callback}_page_{current_page - 1}"
            for key, value in kwargs.items():
                prev_callback += f"_{key}_{value}"
            builder.button(text="◀️", callback_data=prev_callback)
        # Информация о странице
        builder.button(text=f"{current_page}/{total_pages}", callback_data="noop")
        # Кнопка "Следующая"
        if current_page < total_pages:
            next_callback = f"{base_callback}_page_{current_page + 1}"
            for key, value in kwargs.items():
                next_callback += f"_{key}_{value}"
            builder.button(text="▶️", callback_data=next_callback)
        builder.adjust(3)
        return builder.as_markup()
    def create_quick_actions_keyboard(self, actions: List[Dict[str, str]]) -> InlineKeyboardMarkup:
        """
        Создание клавиатуры быстрых действий
        Args:
            actions: Список действий с текстом и callback_data
        Returns:
            Inline клавиатура с действиями
        """
        builder = InlineKeyboardBuilder()
        for action in actions:
            builder.button(
                text=action['text'],
                callback_data=action['callback_data']
            )
        # Настраиваем количество кнопок в ряду
        builder.adjust(2)
        return builder.as_markup()
    def create_tab_keyboard(self, tabs: List[Dict[str, str]], active_tab: str) -> InlineKeyboardMarkup:
        """
        Создание клавиатуры с вкладками
        Args:
            tabs: Список вкладок
            active_tab: Активная вкладка
        Returns:
            Inline клавиатура с вкладками
        """
        builder = InlineKeyboardBuilder()
        for tab in tabs:
            # Добавляем индикатор активности
            text = tab['text']
            if tab['id'] == active_tab:
                text = f"🔹 {text}"
            else:
                text = f"⚪ {text}"
            builder.button(
                text=text,
                callback_data=tab['callback_data']
            )
        builder.adjust(1)
        return builder.as_markup()
    def get_navigation_stats(self) -> Dict[str, Any]:
        """
        Получение статистики навигации
        Returns:
            Словарь со статистикой
        """
        total_users = len(self.user_history)
        total_pages = sum(len(history) for history in self.user_history.values())
        return {
            'total_users_with_history': total_users,
            'total_page_visits': total_pages,
            'average_pages_per_user': total_pages / max(total_users, 1),
            'most_common_pages': self._get_most_common_pages()
        }
    def _get_most_common_pages(self) -> List[Dict[str, Any]]:
        """Получение наиболее часто посещаемых страниц"""
        page_counts = {}
        for history in self.user_history.values():
            for page in history:
                page_counts[page] = page_counts.get(page, 0) + 1
        # Сортируем по популярности
        sorted_pages = sorted(page_counts.items(), key=lambda x: x[1], reverse=True)
        return [
            {'page': page, 'visits': count}
            for page, count in sorted_pages[:10]
        ]
# Глобальный экземпляр сервиса навигации
navigation_service = NavigationService()
