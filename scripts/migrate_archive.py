#!/usr/bin/env python3
"""
Скрипт миграции базы данных для добавления поля архивации
"""
import sys
import os
import asyncio
import aiosqlite
from datetime import datetime

# Добавляем src в путь для импортов
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from easy_pass_bot.config import DATABASE_PATH


async def migrate_database():
    """Выполнить миграцию базы данных"""
    print("Starting database migration for archive functionality...")
    
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            # Проверяем, существует ли уже поле is_archived
            cursor = await db.execute("PRAGMA table_info(passes)")
            columns = await cursor.fetchall()
            
            has_archived_field = any(col[1] == 'is_archived' for col in columns)
            
            if has_archived_field:
                print("Field 'is_archived' already exists. Migration not needed.")
                return
            
            print("Adding 'is_archived' field to passes table...")
            
            # Добавляем поле is_archived
            await db.execute("""
                ALTER TABLE passes ADD COLUMN is_archived BOOLEAN NOT NULL DEFAULT 0
            """)
            
            # Создаем индекс для поля is_archived
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_passes_is_archived 
                ON passes(is_archived)
            """)
            
            await db.commit()
            print("Migration completed successfully!")
            
            # Показываем статистику
            cursor = await db.execute("SELECT COUNT(*) FROM passes")
            total_passes = (await cursor.fetchone())[0]
            
            cursor = await db.execute("SELECT COUNT(*) FROM passes WHERE is_archived = 1")
            archived_passes = (await cursor.fetchone())[0]
            
            print(f"Total passes: {total_passes}")
            print(f"Archived passes: {archived_passes}")
            print(f"Active passes: {total_passes - archived_passes}")
            
    except Exception as e:
        print(f"Migration failed: {e}")
        raise


async def rollback_migration():
    """Откатить миграцию (удалить поле is_archived)"""
    print("Rolling back archive migration...")
    
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            # SQLite не поддерживает DROP COLUMN, поэтому нужно пересоздать таблицу
            print("Recreating passes table without is_archived field...")
            
            # Создаем временную таблицу со старой структурой
            await db.execute("""
                CREATE TABLE passes_backup (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    car_number VARCHAR(20) NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (
                        status IN ('active', 'used', 'cancelled')
                    ),
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    used_at TIMESTAMP NULL,
                    used_by_id INTEGER NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (used_by_id) REFERENCES users(id)
                )
            """)
            
            # Копируем данные (исключая архивные записи)
            await db.execute("""
                INSERT INTO passes_backup (id, user_id, car_number, status, created_at, used_at, used_by_id)
                SELECT id, user_id, car_number, status, created_at, used_at, used_by_id
                FROM passes WHERE is_archived = 0
            """)
            
            # Удаляем старую таблицу
            await db.execute("DROP TABLE passes")
            
            # Переименовываем временную таблицу
            await db.execute("ALTER TABLE passes_backup RENAME TO passes")
            
            # Восстанавливаем индексы
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_passes_user_id 
                ON passes(user_id)
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_passes_status 
                ON passes(status)
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_passes_car_number 
                ON passes(car_number)
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_passes_created_at 
                ON passes(created_at)
            """)
            
            await db.commit()
            print("Rollback completed successfully!")
            
    except Exception as e:
        print(f"Rollback failed: {e}")
        raise


async def main():
    """Основная функция"""
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        await rollback_migration()
    else:
        await migrate_database()


if __name__ == "__main__":
    asyncio.run(main())



