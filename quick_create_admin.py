#!/usr/bin/env python3
"""
Быстрое создание администратора с уведомлениями
Использование: python quick_create_admin.py <user_id>
"""
import asyncio
import sys
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Добавляем путь к модулям проекта
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from create_admin_with_notifications import create_admin_with_notifications

async def main():
    """Основная функция"""
    if len(sys.argv) != 2:
        print("Использование: python quick_create_admin.py <user_id>")
        print("Пример: python quick_create_admin.py 122")
        sys.exit(1)
    
    try:
        user_id = int(sys.argv[1])
    except ValueError:
        print("❌ Ошибка: user_id должен быть числом")
        sys.exit(1)
    
    # Получаем токен из переменных окружения
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        print("❌ Ошибка: BOT_TOKEN не найден в переменных окружения")
        print("Убедитесь, что файл .env содержит BOT_TOKEN")
        sys.exit(1)
    
    print(f"🚀 Создание администратора для пользователя ID: {user_id}")
    print("=" * 50)
    
    success = await create_admin_with_notifications(user_id, bot_token)
    
    if success:
        print("✅ Администратор создан и уведомления отправлены!")
        print("📱 Пользователь получил учетные данные в Telegram")
    else:
        print("❌ Ошибка при создании администратора!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

