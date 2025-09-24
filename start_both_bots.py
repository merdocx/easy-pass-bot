#!/usr/bin/env python3
"""
Скрипт запуска обоих ботов одновременно
"""
import asyncio
import sys
import os
import logging

# Добавляем путь к ботам
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'bots'))

from resident_bot.main import main as resident_main
from security_bot.main import main as security_main

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def run_both_bots():
    """Запуск обоих ботов параллельно"""
    try:
        logger.info("Starting both bots...")
        
        # Запускаем оба бота параллельно
        await asyncio.gather(
            resident_main(),
            security_main()
        )
        
    except Exception as e:
        logger.error(f"Error running bots: {e}")
    finally:
        logger.info("Both bots stopped")

if __name__ == "__main__":
    try:
        asyncio.run(run_both_bots())
    except KeyboardInterrupt:
        logger.info("Bots stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")



