#!/usr/bin/env python3
"""
Скрипт для инициализации администраторов и сотрудников охраны
"""
import asyncio
import logging
from database import db, User
from config import ROLES, USER_STATUSES
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def init_users():
    """Инициализация пользователей"""
    await db.init_db()
    # Создание администратора
    admin = User(
        telegram_id=46701395,
        role=ROLES['ADMIN'],
        full_name="Петренко Никита Викторович",
        phone_number="+79099297070",
        apartment="57",
        status=USER_STATUSES['APPROVED']
    )
    # Создание сотрудника охраны (замените на реальные данные)
    security = User(
        telegram_id=987654321,  # Замените на реальный Telegram ID
        role=ROLES['SECURITY'],
        full_name="Сотрудник охраны",
        phone_number="+7 900 000 00 01",
        apartment=None,
        status=USER_STATUSES['APPROVED']
    )
    try:
        # Проверяем, существует ли уже администратор
        existing_admin = await db.get_user_by_telegram_id(admin.telegram_id)
        if not existing_admin:
            await db.create_user(admin)
            logger.info("Admin user created")
        else:
            logger.info("Admin user already exists")
        # Проверяем, существует ли уже сотрудник охраны
        existing_security = await db.get_user_by_telegram_id(security.telegram_id)
        if not existing_security:
            await db.create_user(security)
            logger.info("Security user created")
        else:
            logger.info("Security user already exists")
    except Exception as e:
        logger.error(f"Failed to create users: {e}")
if __name__ == "__main__":
    print("Инициализация пользователей...")
    print("ВАЖНО: Замените telegram_id в файле init_users.py на реальные ID!")
    asyncio.run(init_users())
