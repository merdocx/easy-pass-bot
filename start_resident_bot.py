#!/usr/bin/env python3
"""
Скрипт запуска бота для жителей
"""
import sys
import os

# Добавляем путь к ботам
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'bots'))

from resident_bot.main import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())



