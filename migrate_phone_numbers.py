#!/usr/bin/env python3
"""
Скрипт для миграции номеров телефонов в базе данных
Нормализует все существующие номера телефонов в формат +7 999 999 99 99
"""

import asyncio
import aiosqlite
import logging
from pathlib import Path
import sys

# Добавляем путь к модулям проекта
sys.path.insert(0, str(Path(__file__).parent / "src"))

from easy_pass_bot.utils.phone_normalizer import normalize_phone_number, validate_phone_format, is_russian_phone

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATABASE_PATH = "/root/easy_pass_bot/database/easy_pass.db"

async def migrate_phone_numbers():
    """Миграция номеров телефонов в базе данных"""
    
    if not Path(DATABASE_PATH).exists():
        logger.error(f"База данных не найдена: {DATABASE_PATH}")
        return
    
    logger.info("Начинаем миграцию номеров телефонов...")
    
    # Создаем резервную копию
    backup_path = f"{DATABASE_PATH}.backup_before_phone_migration"
    logger.info(f"Создаем резервную копию: {backup_path}")
    
    try:
        # Читаем текущую базу данных
        with open(DATABASE_PATH, 'rb') as src:
            with open(backup_path, 'wb') as dst:
                dst.write(src.read())
        logger.info("Резервная копия создана успешно")
    except Exception as e:
        logger.error(f"Ошибка создания резервной копии: {e}")
        return
    
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Получаем всех пользователей
        async with db.execute("SELECT id, phone_number FROM users") as cursor:
            users = await cursor.fetchall()
        
        logger.info(f"Найдено пользователей: {len(users)}")
        
        updated_count = 0
        error_count = 0
        
        for user_id, current_phone in users:
            try:
                # Нормализуем номер телефона
                normalized_phone = normalize_phone_number(current_phone)
                
                # Если номер изменился, обновляем в базе данных
                if normalized_phone != current_phone:
                    # Проверяем, что нормализованный номер валидный
                    if validate_phone_format(normalized_phone) and is_russian_phone(normalized_phone):
                        await db.execute(
                            "UPDATE users SET phone_number = ? WHERE id = ?",
                            (normalized_phone, user_id)
                        )
                        updated_count += 1
                        logger.info(f"Пользователь ID {user_id}: '{current_phone}' -> '{normalized_phone}'")
                    else:
                        logger.warning(f"Пользователь ID {user_id}: не удалось нормализовать номер '{current_phone}'")
                        error_count += 1
                else:
                    logger.debug(f"Пользователь ID {user_id}: номер '{current_phone}' уже в правильном формате")
            
            except Exception as e:
                logger.error(f"Ошибка обработки пользователя ID {user_id}: {e}")
                error_count += 1
        
        # Сохраняем изменения
        await db.commit()
        
        logger.info("=" * 50)
        logger.info("МИГРАЦИЯ ЗАВЕРШЕНА")
        logger.info("=" * 50)
        logger.info(f"Всего пользователей обработано: {len(users)}")
        logger.info(f"Номеров обновлено: {updated_count}")
        logger.info(f"Ошибок: {error_count}")
        logger.info(f"Резервная копия: {backup_path}")
        
        if error_count > 0:
            logger.warning("Обнаружены ошибки при миграции. Проверьте логи.")
        else:
            logger.info("Миграция прошла успешно!")

async def show_phone_statistics():
    """Показывает статистику номеров телефонов до миграции"""
    
    logger.info("Анализ номеров телефонов в базе данных...")
    
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Получаем всех пользователей
        async with db.execute("SELECT id, phone_number FROM users") as cursor:
            users = await cursor.fetchall()
        
        total_users = len(users)
        valid_russian_phones = 0
        invalid_phones = 0
        already_normalized = 0
        
        examples = {
            'valid_russian': [],
            'invalid': [],
            'already_normalized': []
        }
        
        for user_id, phone in users:
            if validate_phone_format(phone) and is_russian_phone(phone):
                if phone.startswith('+7 ') and len(phone) == 17:  # Уже нормализован
                    already_normalized += 1
                    if len(examples['already_normalized']) < 3:
                        examples['already_normalized'].append((user_id, phone))
                else:
                    valid_russian_phones += 1
                    if len(examples['valid_russian']) < 5:
                        examples['valid_russian'].append((user_id, phone))
            else:
                invalid_phones += 1
                if len(examples['invalid']) < 3:
                    examples['invalid'].append((user_id, phone))
        
        logger.info("=" * 50)
        logger.info("СТАТИСТИКА НОМЕРОВ ТЕЛЕФОНОВ")
        logger.info("=" * 50)
        logger.info(f"Всего пользователей: {total_users}")
        logger.info(f"Уже нормализованных: {already_normalized}")
        logger.info(f"Российских (требуют нормализации): {valid_russian_phones}")
        logger.info(f"Некорректных номеров: {invalid_phones}")
        
        if examples['already_normalized']:
            logger.info("\nПримеры уже нормализованных номеров:")
            for user_id, phone in examples['already_normalized']:
                logger.info(f"  ID {user_id}: {phone}")
        
        if examples['valid_russian']:
            logger.info("\nПримеры номеров, требующих нормализации:")
            for user_id, phone in examples['valid_russian']:
                normalized = normalize_phone_number(phone)
                logger.info(f"  ID {user_id}: '{phone}' -> '{normalized}'")
        
        if examples['invalid']:
            logger.info("\nПримеры некорректных номеров:")
            for user_id, phone in examples['invalid']:
                logger.info(f"  ID {user_id}: {phone}")
        
        logger.info("=" * 50)

async def main():
    """Основная функция"""
    if len(sys.argv) > 1 and sys.argv[1] == "--stats":
        await show_phone_statistics()
    else:
        await show_phone_statistics()
        print("\nДля запуска миграции выполните: python migrate_phone_numbers.py --migrate")
        
        if len(sys.argv) > 1 and sys.argv[1] == "--migrate":
            await migrate_phone_numbers()

if __name__ == "__main__":
    asyncio.run(main())
