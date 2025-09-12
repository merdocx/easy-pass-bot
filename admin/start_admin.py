#!/usr/bin/env python3
"""
Скрипт запуска веб-админки Easy Pass
"""

import os
import sys
import asyncio
import uvicorn
from pathlib import Path

# Добавляем путь к основному проекту
sys.path.append('/root/easy_pass_bot/src')

async def main():
    """Основная функция запуска"""
    print("🚀 Запуск Easy Pass Admin Panel...")
    
    # Проверяем наличие базы данных
    db_path = "/root/easy_pass_bot/database/easy_pass.db"
    if not os.path.exists(db_path):
        print("❌ База данных не найдена. Создаем...")
        from easy_pass_bot.database.database import db
        await db.init_db()
        print("✅ База данных инициализирована")
    
    # Запускаем сервер
    print("🌐 Запуск веб-сервера на http://89.110.96.90:8080")
    print("📱 Админка доступна по адресу: http://89.110.96.90:8080")
    print("🔑 Логин: admin")
    print("🔐 Пароль: admin123")
    print("=" * 50)
    
    config = uvicorn.Config(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=False,
        log_level="info",
        access_log=True
    )
    
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Остановка админки...")
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
        sys.exit(1)
