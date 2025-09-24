#!/usr/bin/env python3
"""
Бот для жителей - Easy Pass Bot
Токен: 7961301390:AAFz7gE__kiwT_B8GPleVvrsf-qxqXbd8X4
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

from config import RESIDENT_BOT_TOKEN
from easy_pass_bot.core.service_config import initialize_services, cleanup_services
from .handlers import register_resident_handlers

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Основная функция запуска бота для жителей"""
    try:
        # Инициализация сервисов
        logger.info("Initializing resident bot services...")
        await initialize_services()
        logger.info("Services initialized")
        
        # Создание бота
        bot = Bot(
            token=RESIDENT_BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        
        # Создание диспетчера
        dp = Dispatcher()
        
        # Регистрация обработчиков только для жителей
        register_resident_handlers(dp)
        logger.info("Resident handlers registered")
        
        # Запуск бота
        logger.info("Starting resident bot...")
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"Resident bot error: {e}")
    finally:
        # Очистка сервисов
        logger.info("Cleaning up resident bot services...")
        await cleanup_services()
        logger.info("Services cleaned up")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Resident bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error in resident bot: {e}")
