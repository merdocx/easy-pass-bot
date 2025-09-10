#!/usr/bin/env python3
"""
Easy Pass Bot - Точка входа в приложение
"""
import sys
import os
import asyncio

# Добавляем src в путь для импортов
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from easy_pass_bot.bot.main import main

if __name__ == "__main__":
    asyncio.run(main())