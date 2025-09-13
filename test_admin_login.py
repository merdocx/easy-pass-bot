#!/usr/bin/env python3
"""
Тест для проверки входа в админку
"""
import requests
import urllib.parse

def test_admin_login():
    """Тестирование входа в админку"""
    print('🧪 Тестирование входа в админку')
    print('='*50)
    
    base_url = 'http://localhost:8080'
    
    # Данные для входа
    login_data = {
        'username': '+7 909 929 70 70',
        'password': 'mS3KU8NJ5nKiQ@yj',
        'redirect_url': '/dashboard'
    }
    
    print(f'📱 Логин: {login_data["username"]}')
    print(f'🔑 Пароль: {login_data["password"]}')
    
    # Создаем сессию
    session = requests.Session()
    
    # Получаем страницу логина
    print('\\n🔍 Получение страницы логина...')
    login_page = session.get(f'{base_url}/login')
    print(f'   Статус: {login_page.status_code}')
    
    if login_page.status_code != 200:
        print('❌ Не удалось получить страницу логина')
        return False
    
    # Пытаемся войти
    print('\\n🔐 Попытка входа...')
    login_response = session.post(f'{base_url}/login', data=login_data, allow_redirects=False)
    print(f'   Статус: {login_response.status_code}')
    print(f'   Заголовки: {dict(login_response.headers)}')
    
    if login_response.status_code == 302:
        print('✅ Вход успешен! Получен редирект')
        
        # Проверяем, что получили cookie
        cookies = session.cookies.get_dict()
        if 'admin_session' in cookies:
            print(f'✅ Получена сессия: {cookies["admin_session"][:20]}...')
        else:
            print('❌ Сессия не получена')
            return False
        
        # Проверяем доступ к dashboard
        print('\\n🏠 Проверка доступа к dashboard...')
        dashboard_response = session.get(f'{base_url}/dashboard')
        print(f'   Статус: {dashboard_response.status_code}')
        
        if dashboard_response.status_code == 200:
            print('✅ Доступ к dashboard получен!')
            return True
        else:
            print('❌ Нет доступа к dashboard')
            return False
            
    else:
        print('❌ Вход не удался')
        print(f'   Ответ: {login_response.text[:200]}...')
        return False

if __name__ == '__main__':
    success = test_admin_login()
    if success:
        print('\\n🎉 Тест пройден успешно!')
    else:
        print('\\n💥 Тест провален!')
