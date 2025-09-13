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
• Рекомендуется сменить пароль после первого входа
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
