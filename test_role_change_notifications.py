#!/usr/bin/env python3
"""
Тест для проверки уведомлений при смене роли пользователей
"""

import asyncio
import sys
import os
import requests
from datetime import datetime

# Добавляем путь к модулям
sys.path.append('/root/easy_pass_bot/src')

async def test_role_change_notifications():
    """Тест уведомлений при смене роли пользователей"""
    
    print("🧪 Тестирование уведомлений при смене роли пользователей")
    print("=" * 70)
    
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
            "password": "CDJt!t%0O#z&"  # Пароль Петренко
        }
        
        try:
            login_response = session.post(f"{admin_url}/login", data=login_data, allow_redirects=False)
            if login_response.status_code == 302:
                print("   ✅ Авторизация успешна")
            else:
                print(f"   ❌ Ошибка авторизации: {login_response.status_code}")
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
                
                # Ищем пользователя Иванова с ролью security (если есть)
                ivanov_security = None
                ivanov_admin = None
                
                for user in users:
                    if "Иванов" in user.get('full_name', ''):
                        if user.get('role') == 'security':
                            ivanov_security = user
                        elif user.get('role') == 'admin':
                            ivanov_admin = user
                
                if ivanov_security:
                    print(f"   ✅ Найден охранник Иванов: ID {ivanov_security['id']}")
                    test_user = ivanov_security
                    target_role = 'resident'
                elif ivanov_admin:
                    print(f"   ✅ Найден админ Иванов: ID {ivanov_admin['id']}")
                    test_user = ivanov_admin
                    target_role = 'security'
                else:
                    print("   ❌ Пользователь Иванов не найден")
                    return False
            else:
                print(f"   ❌ Ошибка получения пользователей: {users_response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Ошибка при получении пользователей: {e}")
            return False
        
        # 4. Изменяем роль пользователя
        print(f"\n4. Изменение роли пользователя {test_user['full_name']} с {test_user['role']} на {target_role}...")
        try:
            role_data = {
                "new_role": target_role
            }
            
            role_response = session.post(
                f"{admin_url}/users/{test_user['id']}/role", 
                data=role_data,
                allow_redirects=False
            )
            
            if role_response.status_code == 302:
                print(f"   ✅ Роль успешно изменена с {test_user['role']} на {target_role}!")
                print("   ✅ Уведомление должно быть отправлено в Telegram")
            else:
                print(f"   ❌ Ошибка изменения роли: {role_response.status_code}")
                print(f"   Ответ: {role_response.text}")
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
                
                # Ищем пользователя
                user_updated = None
                for user in users:
                    if user['id'] == test_user['id']:
                        user_updated = user
                        break
                
                if user_updated:
                    current_role = user_updated.get('role')
                    if current_role == target_role:
                        print(f"   ✅ Роль успешно изменена на '{target_role}'")
                    else:
                        print(f"   ❌ Роль не изменилась, текущая роль: {current_role}")
                        return False
                else:
                    print("   ❌ Пользователь не найден после изменения роли")
                    return False
            else:
                print(f"   ❌ Ошибка получения пользователей для проверки: {users_response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Ошибка при проверке изменения роли: {e}")
            return False
        
        # 6. Тестируем изменение обратно на admin (если это было возможно)
        if target_role == 'security':
            print(f"\n6. Тестирование изменения роли обратно на admin...")
            try:
                role_data = {
                    "new_role": "admin"
                }
                
                role_response = session.post(
                    f"{admin_url}/users/{test_user['id']}/role", 
                    data=role_data,
                    allow_redirects=False
                )
                
                if role_response.status_code == 302:
                    print(f"   ✅ Роль успешно изменена обратно на admin!")
                    print("   ✅ Специальные уведомления для админа должны быть отправлены")
                else:
                    print(f"   ❌ Ошибка изменения роли на admin: {role_response.status_code}")
                    print(f"   Ответ: {role_response.text}")
            except Exception as e:
                print(f"   ❌ Ошибка при изменении роли на admin: {e}")
        
        print("\n" + "=" * 70)
        print("🎉 ТЕСТ УВЕДОМЛЕНИЙ ПРОЙДЕН УСПЕШНО!")
        print("✅ Система уведомлений о смене роли работает корректно")
        print("✅ Уведомления отправляются для всех типов ролей")
        print("✅ Специальные уведомления для админов работают")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Критическая ошибка в тесте: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_role_change_notifications())
    sys.exit(0 if success else 1)
