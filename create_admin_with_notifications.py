#!/usr/bin/env python3
"""
Скрипт для создания администратора с отправкой уведомлений в Telegram
"""
import asyncio
import sys
import os
import logging
from datetime import datetime

# Добавляем путь к модулям проекта
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from easy_pass_bot.database.database import Database
from easy_pass_bot.utils.password_generator import generate_admin_password
from easy_pass_bot.utils.phone_normalizer import normalize_phone_number
from easy_pass_bot.utils.telegram_notifier import TelegramNotifier, init_notifier
import bcrypt

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def create_admin_with_notifications(user_id: int, bot_token: str) -> bool:
    """
    Создание администратора с отправкой уведомлений в Telegram
    
    Args:
        user_id: ID пользователя в таблице users
        bot_token: Токен бота для отправки уведомлений
        
    Returns:
        bool: True если администратор создан и уведомления отправлены
    """
    try:
        # Инициализируем уведомления
        notifier = init_notifier(bot_token)
        
        db = Database()
        
        # Получаем данные пользователя
        logger.info(f"🔍 Получение данных пользователя с ID: {user_id}")
        user = await db.get_user_by_id(user_id)
        
        if not user:
            logger.error(f"❌ Пользователь с ID {user_id} не найден!")
            return False
        
        if user.role != 'admin':
            logger.error(f"❌ Пользователь {user.full_name} не является администратором!")
            return False
        
        logger.info(f"✅ Найден администратор: {user.full_name}")
        logger.info(f"   Telegram ID: {user.telegram_id}")
        logger.info(f"   Телефон: {user.phone_number}")
        
        # Проверяем, есть ли уже запись в таблице admins
        existing_admin = await db.get_admin_by_user_id(user.id)
        if existing_admin:
            logger.warning(f"⚠️ Администратор {user.full_name} уже существует в таблице admins!")
            logger.info(f"   ID: {existing_admin.id}")
            logger.info(f"   Логин: {existing_admin.phone_number}")
            return True
        
        # Нормализуем номер телефона
        normalized_phone = normalize_phone_number(user.phone_number)
        logger.info(f"📱 Нормализованный номер телефона: {normalized_phone}")
        
        # Генерируем случайный пароль
        new_password = generate_admin_password()
        logger.info(f"🔑 Сгенерирован новый пароль: {new_password}")
        
        # Хэшируем пароль
        password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Создаем запись в таблице admins
        logger.info("📝 Создание записи администратора в таблице admins...")
        success = await db.create_admin(
            username=normalized_phone,
            full_name=user.full_name,
            password_hash=password_hash,
            user_id=user.id,
            phone_number=normalized_phone,
            role="admin"
        )
        
        if not success:
            logger.error("❌ Ошибка при создании администратора!")
            return False
        
        logger.info("✅ Администратор успешно создан в новой системе!")
        
        # Отправляем уведомления в Telegram
        logger.info("📱 Отправка уведомлений в Telegram...")
        
        # Сначала отправляем приветственное сообщение
        welcome_sent = await notifier.send_admin_welcome(user.telegram_id, user.full_name)
        if welcome_sent:
            logger.info("✅ Приветственное сообщение отправлено")
        else:
            logger.warning("⚠️ Не удалось отправить приветственное сообщение")
        
        # Затем отправляем учетные данные
        credentials_sent = await notifier.send_admin_credentials(
            user.telegram_id, 
            user.full_name, 
            normalized_phone, 
            new_password
        )
        
        if credentials_sent:
            logger.info("✅ Учетные данные отправлены в Telegram")
        else:
            logger.warning("⚠️ Не удалось отправить учетные данные в Telegram")
            logger.info("📋 Учетные данные для ручной передачи:")
            logger.info(f"   Логин: {normalized_phone}")
            logger.info(f"   Пароль: {new_password}")
        
        # Закрываем соединение с ботом
        await notifier.close()
        
        logger.info("🎉 Процесс создания администратора завершен!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка при создании администратора: {e}")
        return False

async def main():
    """Основная функция"""
    if len(sys.argv) != 3:
        print("Использование: python create_admin_with_notifications.py <user_id> <bot_token>")
        print("Пример: python create_admin_with_notifications.py 122 '1234567890:ABC...'")
        sys.exit(1)
    
    try:
        user_id = int(sys.argv[1])
        bot_token = sys.argv[2]
    except ValueError:
        print("❌ Ошибка: user_id должен быть числом")
        sys.exit(1)
    
    logger.info("🚀 Создание администратора с уведомлениями")
    logger.info("=" * 60)
    logger.info(f"👤 User ID: {user_id}")
    logger.info(f"🤖 Bot Token: {bot_token[:20]}...")
    logger.info("=" * 60)
    
    success = await create_admin_with_notifications(user_id, bot_token)
    
    if success:
        logger.info("✅ Администратор создан и уведомления отправлены!")
    else:
        logger.error("❌ Ошибка при создании администратора!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
