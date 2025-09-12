#!/usr/bin/env python3
"""
Скрипт для запуска тестов админки
"""

import sys
import os
import subprocess
import pytest

def main():
    """Запуск тестов"""
    print("🧪 Запуск тестов Easy Pass Admin Panel...")
    print("=" * 50)
    
    # Добавляем пути
    sys.path.append('/root/easy_pass_bot/admin')
    sys.path.append('/root/easy_pass_bot/src')
    
    # Устанавливаем переменные окружения для тестов
    os.environ['TESTING'] = 'true'
    
    # Запускаем тесты
    try:
        result = pytest.main([
            '/root/easy_pass_bot/admin/tests/test_admin.py',
            '-v',
            '--tb=short',
            '--color=yes'
        ])
        
        if result == 0:
            print("\n✅ Все тесты прошли успешно!")
            return 0
        else:
            print(f"\n❌ Тесты завершились с ошибками (код: {result})")
            return result
            
    except Exception as e:
        print(f"❌ Ошибка запуска тестов: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
