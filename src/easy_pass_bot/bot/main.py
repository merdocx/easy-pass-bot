import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from ..config import BOT_TOKEN
from ..core.service_config import initialize_services, cleanup_services
from ..handlers import (
    register_common_handlers,
    register_resident_handlers,
    register_security_handlers,
    register_admin_handlers
)
# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Основная функция запуска бота"""
    try:
        # Инициализация сервисов
        logger.info("Initializing services...")
        await initialize_services()
        logger.info("Services initialized")
        
        # Создание бота
        bot = Bot(
            token=BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        
        # Создание диспетчера
        dp = Dispatcher()
        
        # Регистрация обработчиков (порядок важен!)
        register_common_handlers(dp)
        # Жители сначала (у них более специфичные фильтры)
        register_resident_handlers(dp)
        # Охранники после жителей
        register_security_handlers(dp)
        register_admin_handlers(dp)
        logger.info("Handlers registered")
        
        # Запуск бота
        logger.info("Starting bot...")
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"Bot error: {e}")
    finally:
        # Очистка сервисов
        logger.info("Cleaning up services...")
        await cleanup_services()
        logger.info("Services cleaned up")
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
