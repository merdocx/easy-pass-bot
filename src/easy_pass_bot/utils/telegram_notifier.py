"""
Утилита для отправки уведомлений в Telegram
"""
import asyncio
import logging
from typing import Optional, Dict, Any
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

logger = logging.getLogger(__name__)

class TelegramNotifier:
    """Класс для отправки уведомлений в Telegram"""
    
    def __init__(self, bot_token: str):
        """
        Инициализация уведомлений
        
        Args:
            bot_token: Токен бота для отправки уведомлений
        """
        self.bot_token = bot_token
        self.bot = Bot(
            token=bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
    
    async def send_admin_credentials(self, user_id: int, full_name: str, 
                                   phone_number: str, password: str) -> bool:
        """
        Отправка учетных данных администратора в Telegram
        
        Args:
            user_id: Telegram ID пользователя
            full_name: Полное имя администратора
            phone_number: Номер телефона (логин)
            password: Пароль для входа
            
        Returns:
            bool: True если уведомление отправлено успешно
        """
        try:
            message = self._format_admin_credentials_message(
                full_name, phone_number, password
            )
            
            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode=ParseMode.HTML
            )
            
            logger.info(f"Admin credentials sent to user {user_id} ({full_name})")
            return True
            
        except TelegramForbiddenError:
            logger.warning(f"User {user_id} ({full_name}) blocked the bot")
            return False
        except TelegramBadRequest as e:
            logger.error(f"Bad request when sending to user {user_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending admin credentials to user {user_id}: {e}")
            return False
    
    async def send_admin_welcome(self, user_id: int, full_name: str) -> bool:
        """
        Отправка приветственного сообщения новому администратору
        
        Args:
            user_id: Telegram ID пользователя
            full_name: Полное имя администратора
            
        Returns:
            bool: True если уведомление отправлено успешно
        """
        try:
            message = f"""
🎉 <b>Поздравляем!</b>

Вы назначены администратором системы Easy Pass Bot!

🔐 Ваши учетные данные для входа в админ-панель:
• <b>Логин:</b> Ваш номер телефона
• <b>Пароль:</b> Персональный пароль (будет отправлен отдельным сообщением)

🌐 <b>Адрес админ-панели:</b> <code>http://localhost:8080</code>

⚠️ <b>Важно:</b> Сохраните учетные данные в безопасном месте!
            """
            
            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode=ParseMode.HTML
            )
            
            logger.info(f"Admin welcome sent to user {user_id} ({full_name})")
            return True
            
        except Exception as e:
            logger.error(f"Error sending admin welcome to user {user_id}: {e}")
            return False
    
    async def send_role_change_notification(self, user_id: int, full_name: str, 
                                          old_role: str, new_role: str) -> bool:
        """
        Отправка уведомления об изменении роли пользователя
        
        Args:
            user_id: Telegram ID пользователя
            full_name: Полное имя пользователя
            old_role: Старая роль
            new_role: Новая роль
            
        Returns:
            bool: True если уведомление отправлено успешно
        """
        try:
            message = self._format_role_change_message(full_name, old_role, new_role)
            
            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode=ParseMode.HTML
            )
            
            logger.info(f"Role change notification sent to user {user_id} ({full_name}): {old_role} -> {new_role}")
            return True
            
        except TelegramForbiddenError:
            logger.warning(f"User {user_id} ({full_name}) blocked the bot")
            return False
        except TelegramBadRequest as e:
            logger.error(f"Bad request when sending role change to user {user_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending role change notification to user {user_id}: {e}")
            return False
    
    def _format_role_change_message(self, full_name: str, old_role: str, new_role: str) -> str:
        """
        Форматирование сообщения об изменении роли
        
        Args:
            full_name: Полное имя пользователя
            old_role: Старая роль
            new_role: Новая роль
            
        Returns:
            str: Отформатированное сообщение
        """
        # Перевод ролей на русский
        role_translations = {
            'admin': 'Администратор',
            'security': 'Охрана',
            'resident': 'Житель'
        }
        
        old_role_ru = role_translations.get(old_role, old_role)
        new_role_ru = role_translations.get(new_role, new_role)
        
        # Определяем эмодзи и текст в зависимости от роли
        if new_role == 'admin':
            emoji = "🎉"
            message_type = "повышена"
            details = """
🔐 <b>Теперь у вас есть доступ к админ-панели!</b>
• Вы можете управлять пользователями и пропусками
• Ваши учетные данные для входа будут отправлены отдельным сообщением

🌐 <b>Адрес админ-панели:</b> <code>http://localhost:8080</code>
            """
        elif new_role == 'security':
            emoji = "🛡️"
            message_type = "назначена"
            details = """
🛡️ <b>Теперь вы работаете в службе охраны!</b>
• Вы можете просматривать и контролировать пропуски
• Обращайтесь к администратору за дополнительными инструкциями
            """
        elif new_role == 'resident':
            emoji = "🏠"
            message_type = "изменена"
            details = """
🏠 <b>Теперь вы являетесь жителем!</b>
• Вы можете подавать заявки на пропуски
• Обращайтесь к администратору или охране при необходимости
            """
        else:
            emoji = "📝"
            message_type = "изменена"
            details = f"Ваша роль изменена на: <b>{new_role_ru}</b>"
        
        return f"""
{emoji} <b>Уведомление об изменении роли</b>

👤 <b>Пользователь:</b> {full_name}
📋 <b>Ваша роль {message_type} с:</b> <b>{old_role_ru}</b> → <b>{new_role_ru}</b>

{details}

📅 <b>Дата изменения:</b> {self._get_current_time()}

ℹ️ <b>Примечание:</b> Если у вас есть вопросы по поводу изменения роли, обратитесь к администратору системы.
        """
    
    def _get_current_time(self) -> str:
        """Получение текущего времени в формате для сообщения"""
        from datetime import datetime
        return datetime.now().strftime("%d.%m.%Y %H:%M")
    
    def _format_admin_credentials_message(self, full_name: str, phone_number: str, password: str) -> str:
        """
        Форматирование сообщения с учетными данными
        
        Args:
            full_name: Полное имя администратора
            phone_number: Номер телефона
            password: Пароль
            
        Returns:
            str: Отформатированное сообщение
        """
        return f"""
🔐 <b>Ваши учетные данные для админ-панели</b>

👤 <b>Администратор:</b> {full_name}
📱 <b>Логин (телефон):</b> <code>{phone_number}</code>
🔑 <b>Пароль:</b> <code>{password}</code>

🌐 <b>Адрес админ-панели:</b> <code>http://localhost:8080</code>

⚠️ <b>ВАЖНО:</b>
• Сохраните эти данные в безопасном месте
• Не передавайте учетные данные третьим лицам

🔒 <b>Безопасность:</b> Пароль сгенерирован автоматически и содержит символы разного регистра, цифры и специальные символы.
        """
    
    async def close(self):
        """Закрытие соединения с ботом"""
        try:
            await self.bot.session.close()
        except Exception as e:
            logger.error(f"Error closing bot session: {e}")

# Глобальный экземпляр для использования в приложении
_notifier_instance: Optional[TelegramNotifier] = None

def get_notifier() -> Optional[TelegramNotifier]:
    """Получение глобального экземпляра уведомлений"""
    return _notifier_instance

def init_notifier(bot_token: str) -> TelegramNotifier:
    """Инициализация глобального экземпляра уведомлений"""
    global _notifier_instance
    _notifier_instance = TelegramNotifier(bot_token)
    return _notifier_instance

async def send_admin_credentials_async(user_id: int, full_name: str, 
                                     phone_number: str, password: str) -> bool:
    """
    Асинхронная отправка учетных данных администратора
    
    Args:
        user_id: Telegram ID пользователя
        full_name: Полное имя администратора
        phone_number: Номер телефона
        password: Пароль
        
    Returns:
        bool: True если уведомление отправлено успешно
    """
    notifier = get_notifier()
    if not notifier:
        logger.error("TelegramNotifier not initialized")
        return False
    
    return await notifier.send_admin_credentials(user_id, full_name, phone_number, password)

async def send_role_change_notification_async(user_id: int, full_name: str, 
                                            old_role: str, new_role: str) -> bool:
    """
    Асинхронная отправка уведомления об изменении роли
    
    Args:
        user_id: Telegram ID пользователя
        full_name: Полное имя пользователя
        old_role: Старая роль
        new_role: Новая роль
        
    Returns:
        bool: True если уведомление отправлено успешно
    """
    notifier = get_notifier()
    if not notifier:
        logger.error("TelegramNotifier not initialized")
        return False
    
    return await notifier.send_role_change_notification(user_id, full_name, old_role, new_role)

