#!/usr/bin/env python3
"""
Скрипт миграции существующего администратора (Петренко) в новую систему авторизации
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
import bcrypt

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def migrate_petrenko_to_admin_system():
    """Миграция Петренко в новую систему админов"""
    try:
        db = Database()
        
        # Получаем данные Петренко из таблицы users
        logger.info("🔍 Поиск пользователя Петренко в системе...")
        petrenko_user = await db.get_user_by_id(1)
        
        if not petrenko_user:
            logger.error("❌ Пользователь Петренко не найден в системе!")
            return False
        
        if petrenko_user.role != 'admin':
            logger.error(f"❌ Пользователь {petrenko_user.full_name} не является администратором!")
            return False
        
        logger.info(f"✅ Найден администратор: {petrenko_user.full_name}")
        logger.info(f"   Телефон: {petrenko_user.phone_number}")
        logger.info(f"   Роль: {petrenko_user.role}")
        
        # Проверяем, есть ли уже запись в таблице admins
        existing_admin = await db.get_admin_by_user_id(petrenko_user.id)
        if existing_admin:
            logger.warning(f"⚠️ Администратор {petrenko_user.full_name} уже существует в таблице admins!")
            logger.info(f"   ID: {existing_admin.id}")
            logger.info(f"   Логин (телефон): {existing_admin.phone_number}")
            return True
        
        # Нормализуем номер телефона
        normalized_phone = normalize_phone_number(petrenko_user.phone_number)
        logger.info(f"📱 Нормализованный номер телефона: {normalized_phone}")
        
        # Генерируем случайный пароль
        new_password = generate_admin_password()
        logger.info(f"🔑 Сгенерирован новый пароль: {new_password}")
        
        # Хэшируем пароль
        password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Создаем запись в таблице admins
        logger.info("📝 Создание записи администратора в таблице admins...")
        success = await db.create_admin(
            username=normalized_phone,  # Используем номер телефона как username
            full_name=petrenko_user.full_name,
            password_hash=password_hash,
            user_id=petrenko_user.id,
            phone_number=normalized_phone,
            role="admin"
        )
        
        if success:
            logger.info("✅ Администратор успешно создан в новой системе!")
            logger.info("")
            logger.info("=" * 60)
            logger.info("🔐 УЧЕТНЫЕ ДАННЫЕ ДЛЯ ВХОДА В АДМИНКУ")
            logger.info("=" * 60)
            logger.info(f"👤 Администратор: {petrenko_user.full_name}")
            logger.info(f"📱 Логин (телефон): {normalized_phone}")
            logger.info(f"🔑 Пароль: {new_password}")
            logger.info("=" * 60)
            logger.info("⚠️  ВАЖНО: Сохраните эти данные в безопасном месте!")
            logger.info("⚠️  Рекомендуется сменить пароль после первого входа!")
            logger.info("=" * 60)
            
            return True
        else:
            logger.error("❌ Ошибка при создании администратора!")
            return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка во время миграции: {e}")
        return False

async def verify_migration():
    """Проверка успешности миграции"""
    try:
        db = Database()
        
        logger.info("🔍 Проверка миграции...")
        
        # Проверяем, что Петренко есть в таблице users с ролью admin
        petrenko_user = await db.get_user_by_id(1)
        if not petrenko_user or petrenko_user.role != 'admin':
            logger.error("❌ Пользователь Петренко не найден или не является админом!")
            return False
        
        # Проверяем, что есть запись в таблице admins
        admin_record = await db.get_admin_by_user_id(petrenko_user.id)
        if not admin_record:
            logger.error("❌ Запись администратора не найдена в таблице admins!")
            return False
        
        logger.info("✅ Миграция прошла успешно!")
        logger.info(f"   Пользователь: {petrenko_user.full_name}")
        logger.info(f"   Роль в users: {petrenko_user.role}")
        logger.info(f"   Телефон: {admin_record.phone_number}")
        logger.info(f"   Активен: {admin_record.is_active}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка при проверке миграции: {e}")
        return False

async def main():
    """Основная функция"""
    logger.info("🚀 Начало миграции администратора в новую систему авторизации")
    logger.info("=" * 70)
    
    # Выполняем миграцию
    success = await migrate_petrenko_to_admin_system()
    
    if success:
        logger.info("")
        logger.info("🔍 Проверка результатов миграции...")
        await verify_migration()
        logger.info("")
        logger.info("✅ Миграция завершена успешно!")
        logger.info("🌐 Теперь можно войти в админку с новыми учетными данными")
    else:
        logger.error("❌ Миграция завершилась с ошибкой!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
