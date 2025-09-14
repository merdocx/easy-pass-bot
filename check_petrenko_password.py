#!/usr/bin/env python3
"""
Проверка пароля Петренко
"""

import asyncio
import sys
import os

# Добавляем путь к модулям
sys.path.append('/root/easy_pass_bot/src')

from easy_pass_bot.utils.password_generator import verify_password_hash

async def check_passwords():
    """Проверка различных паролей для Петренко"""
    
    # Хэш из базы данных
    stored_hash = "$2b$12$cGVndtifb3rBfGLE6zagbe6wQ.3VWa4kBn17NViIj8.O8TByrr/ae"
    
    # Возможные пароли
    possible_passwords = [
        "admin123",
        "Admin123",
        "ADMIN123",
        "petrenko123",
        "Petrenko123",
        "9099297070",
        "+7 909 929 70 70",
        "test123",
        "password",
        "123456"
    ]
    
    print("Проверка паролей для Петренко:")
    print("=" * 40)
    
    for password in possible_passwords:
        is_valid = verify_password_hash(password, stored_hash)
        status = "✅ ПРАВИЛЬНЫЙ" if is_valid else "❌"
        print(f"{status} {password}")
        
        if is_valid:
            print(f"\n🎉 Найден правильный пароль: {password}")
            return password
    
    print("\n❌ Ни один из проверенных паролей не подходит")
    return None

if __name__ == "__main__":
    result = asyncio.run(check_passwords())
    if result:
        print(f"\nИспользуйте пароль: {result}")
    else:
        print("\nНужно сгенерировать новый пароль для Петренко")

