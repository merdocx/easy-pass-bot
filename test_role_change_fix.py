#!/usr/bin/env python3
"""
Тест для проверки исправления изменения ролей администраторов
"""

import asyncio
import sys
import os
import requests
from datetime import datetime

# Добавляем путь к модулям
sys.path.append('/root/easy_pass_bot/src')

async def test_role_change_fix():
    """Тест изменения роли админа на охранника"""
    
    print("🧪 Тестирование исправления изменения ролей администраторов")
    print("=" * 60)
    
    try:
        # URL админки
        admin_url = "http://localhost:8080"
        
        # 1. Проверяем доступность админки
        print("1. Проверка доступности админки...")
        try:
            response = requests.get(f"{admin_url}/login", timeout=5)
            if response.status_code == 200:
                print("   ✅ Админка доступна")
            else:
                print(f"   ❌ Админка недоступна: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Ошибка подключения к админке: {e}")
            return False
        
        # 2. Авторизация как Петренко
        print("\n2. Авторизация как Петренко...")
        session = requests.Session()
        
        login_data = {
            "username": "+7 909 929 70 70",  # Номер Петренко
            "password": "CDJt!t%0O#z&"  # Новый пароль Петренко
        }
        
        try:
            login_response = session.post(f"{admin_url}/login", data=login_data, allow_redirects=False)
            if login_response.status_code == 302:
                print("   ✅ Авторизация успешна")
            else:
                print(f"   ❌ Ошибка авторизации: {login_response.status_code}")
                print(f"   Ответ: {login_response.text}")
                return False
        except Exception as e:
            print(f"   ❌ Ошибка при авторизации: {e}")
            return False
        
        # 3. Получаем список пользователей
        print("\n3. Получение списка пользователей...")
        try:
            users_response = session.get(f"{admin_url}/api/users")
            if users_response.status_code == 200:
                users_data = users_response.json()
                users = users_data.get('users', [])
                print(f"   ✅ Получено {len(users)} пользователей")
                
                # Ищем пользователя Иванова с ролью admin
                ivanov_admin = None
                for user in users:
                    if "Иванов" in user.get('full_name', '') and user.get('role') == 'admin':
                        ivanov_admin = user
                        break
                
                if ivanov_admin:
                    print(f"   ✅ Найден админ Иванов: ID {ivanov_admin['id']}")
                else:
                    print("   ❌ Админ Иванов не найден")
                    return False
            else:
                print(f"   ❌ Ошибка получения пользователей: {users_response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Ошибка при получении пользователей: {e}")
            return False
        
        # 4. Пытаемся изменить роль Иванова с admin на security
        print("\n4. Изменение роли Иванова с admin на security...")
        try:
            role_data = {
                "new_role": "security"
            }
            
            role_response = session.post(
                f"{admin_url}/users/{ivanov_admin['id']}/role", 
                data=role_data,
                allow_redirects=False
            )
            
            if role_response.status_code == 302:
                print("   ✅ Роль успешно изменена!")
                print("   ✅ Исправление работает - админ может изменить роль другого админа")
            else:
                print(f"   ❌ Ошибка изменения роли: {role_response.status_code}")
                print(f"   Ответ: {role_response.text}")
                
                # Проверяем, содержит ли ответ старую ошибку
                if "Нельзя изменить роль другого администратора" in role_response.text:
                    print("   ❌ Старая ошибка все еще присутствует")
                    return False
                else:
                    print("   ❌ Другая ошибка при изменении роли")
                    return False
        except Exception as e:
            print(f"   ❌ Ошибка при изменении роли: {e}")
            return False
        
        # 5. Проверяем, что роль действительно изменилась
        print("\n5. Проверка изменения роли...")
        try:
            users_response = session.get(f"{admin_url}/api/users")
            if users_response.status_code == 200:
                users_data = users_response.json()
                users = users_data.get('users', [])
                
                # Ищем пользователя Иванова
                ivanov_updated = None
                for user in users:
                    if user['id'] == ivanov_admin['id']:
                        ivanov_updated = user
                        break
                
                if ivanov_updated:
                    current_role = ivanov_updated.get('role')
                    if current_role == 'security':
                        print("   ✅ Роль успешно изменена на 'security'")
                    else:
                        print(f"   ❌ Роль не изменилась, текущая роль: {current_role}")
                        return False
                else:
                    print("   ❌ Пользователь Иванов не найден после изменения роли")
                    return False
            else:
                print(f"   ❌ Ошибка получения пользователей для проверки: {users_response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Ошибка при проверке изменения роли: {e}")
            return False
        
        print("\n" + "=" * 60)
        print("🎉 ТЕСТ ПРОЙДЕН УСПЕШНО!")
        print("✅ Исправление работает корректно")
        print("✅ Админы теперь могут изменять роли других админов")
        print("✅ Роль успешно изменилась с 'admin' на 'security'")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Критическая ошибка в тесте: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_role_change_fix())
    sys.exit(0 if success else 1)
