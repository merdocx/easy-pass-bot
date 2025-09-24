#!/usr/bin/env python3
"""
Бот для охраны и администраторов - Easy Pass Bot
Токен: 8069990519:AAHySjIKHlSgVcJpLaXlExZ5Se0juiKX4GQ
"""
import sys
import os
import asyncio
import logging

# Добавляем пути для импортов
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import SECURITY_BOT_TOKEN
from easy_pass_bot.core.service_config import initialize_services, cleanup_services
from .handlers import register_security_handlers
from .admin_handlers import register_admin_handlers

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Основная функция запуска бота для охраны и админов"""
    try:
        # Инициализация сервисов
        logger.info("Initializing security bot services...")
        await initialize_services()
        logger.info("Services initialized")
        
        # Создание бота
        bot = Bot(
            token=SECURITY_BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        
        # Создание диспетчера
        dp = Dispatcher()
        
        # Регистрация обработчиков для охраны и админов
        register_security_handlers(dp)
        register_admin_handlers(dp)
        logger.info("Security and admin handlers registered")
        
        # Запуск бота
        logger.info("Starting security bot...")
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"Security bot error: {e}")
    finally:
        # Очистка сервисов
        logger.info("Cleaning up security bot services...")
        await cleanup_services()
        logger.info("Services cleaned up")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Security bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error in security bot: {e}")
