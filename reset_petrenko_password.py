#!/usr/bin/env python3
"""
Сброс пароля для Петренко
"""

import asyncio
import sys
import os
import sqlite3

# Добавляем путь к модулям
sys.path.append('/root/easy_pass_bot/src')

from easy_pass_bot.utils.password_generator import generate_secure_password, hash_password

async def reset_petrenko_password():
    """Генерация нового пароля для Петренко"""
    
    print("🔑 Сброс пароля для Петренко")
    print("=" * 40)
    
    # Генерируем новый пароль
    new_password = generate_secure_password()
    password_hash = hash_password(new_password)
    
    print(f"Новый пароль: {new_password}")
    print(f"Хэш пароля: {password_hash}")
    
    # Обновляем пароль в базе данных
    try:
        conn = sqlite3.connect('/root/easy_pass_bot/database/easy_pass.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE admins 
            SET password_hash = ? 
            WHERE username = '+7 909 929 70 70'
        """, (password_hash,))
        
        if cursor.rowcount > 0:
            print("✅ Пароль успешно обновлен в базе данных")
        else:
            print("❌ Не удалось обновить пароль")
            
        conn.commit()
        conn.close()
        
        print(f"\n🎉 Новые учетные данные для Петренко:")
        print(f"   Логин: +7 909 929 70 70")
        print(f"   Пароль: {new_password}")
        
        return new_password
        
    except Exception as e:
        print(f"❌ Ошибка при обновлении пароля: {e}")
        return None

if __name__ == "__main__":
    result = asyncio.run(reset_petrenko_password())
    if result:
        print(f"\nИспользуйте эти данные для входа в админку!")
    else:
        print("\nОшибка при сбросе пароля")

