#!/usr/bin/env python3
"""
Скрипт для наполнения базы данных пропусками
"""

import sqlite3
import random
from datetime import datetime, timedelta
from typing import List, Tuple

# Подключение к базе данных
DB_PATH = "/root/easy_pass_bot/database/easy_pass.db"

# Список российских номеров автомобилей для генерации
CAR_NUMBERS = [
    "А123БВ777", "В456ГД123", "Е789ЖЗ456", "К012ЛМ789", "Н345ОП012",
    "Р678СТ345", "У901ФХ678", "Ц234ШЩ901", "Ю567ЭЮ234", "Я890АБ567",
    "А111АА777", "В222ВВ123", "Е333ЕЕ456", "К444КК789", "Н555НН012",
    "Р666РР345", "У777УУ678", "Ц888ЦЦ901", "Ю999ЮЮ234", "Я000ЯЯ567",
    "А777АА199", "В123ВВ777", "Е456ЕЕ199", "К789КК777", "Н012НН199",
    "Р345РР777", "У678УУ199", "Ц901ЦЦ777", "Ю234ЮЮ199", "Я567ЯЯ777"
]

STATUSES = ['active', 'used', 'cancelled']
STATUS_WEIGHTS = [0.6, 0.3, 0.1]  # 60% активных, 30% использованных, 10% отмененных

def get_connection():
    """Получить соединение с базой данных"""
    return sqlite3.connect(DB_PATH)

def get_all_users() -> List[Tuple]:
    """Получить всех пользователей из базы данных"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, full_name, role FROM users WHERE status = 'approved'")
    users = cursor.fetchall()
    conn.close()
    return users

def generate_car_number() -> str:
    """Генерировать случайный номер автомобиля"""
    return random.choice(CAR_NUMBERS)

def generate_created_date() -> str:
    """Генерировать дату создания (последние 90 дней)"""
    now = datetime.now()
    days_ago = random.randint(0, 90)
    created_date = now - timedelta(days=days_ago)
    return created_date.strftime("%Y-%m-%d %H:%M:%S")

def generate_used_date(created_date: str) -> str:
    """Генерировать дату использования (после даты создания)"""
    created = datetime.strptime(created_date, "%Y-%m-%d %H:%M:%S")
    # Использование через 1-30 дней после создания
    days_after = random.randint(1, 30)
    used_date = created + timedelta(days=days_after)
    return used_date.strftime("%Y-%m-%d %H:%M:%S")

def get_random_user_for_usage(all_users: List[Tuple]) -> int:
    """Получить случайного пользователя для поля used_by_id"""
    # Выбираем пользователей с ролью 'security' или 'admin'
    security_users = [user[0] for user in all_users if user[2] in ['security', 'admin']]
    if security_users:
        return random.choice(security_users)
    # Если нет security/admin, выбираем любого пользователя
    return random.choice(all_users)[0]

def create_pass(user_id: int, car_number: str, status: str, created_at: str, 
                used_at: str = None, used_by_id: int = None) -> str:
    """Создать SQL запрос для вставки пропуска"""
    if status == 'used' and used_at is None:
        used_at = generate_used_date(created_at)
    
    if status == 'used' and used_by_id is None:
        users = get_all_users()
        used_by_id = get_random_user_for_usage(users)
    
    sql = """
    INSERT INTO passes (user_id, car_number, status, created_at, used_at, used_by_id, is_archived)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    return sql, (user_id, car_number, status, created_at, used_at, used_by_id, False)

def populate_passes(num_passes: int = 100):
    """Наполнить базу данных пропусками"""
    print(f"🚀 Начинаем создание {num_passes} пропусков...")
    
    # Получаем всех пользователей
    users = get_all_users()
    if not users:
        print("❌ Ошибка: Нет одобренных пользователей в базе данных")
        return
    
    print(f"📋 Найдено {len(users)} пользователей")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    created_count = 0
    
    try:
        for i in range(num_passes):
            # Выбираем случайного пользователя
            user = random.choice(users)
            user_id = user[0]
            
            # Генерируем данные пропуска
            car_number = generate_car_number()
            status = random.choices(STATUSES, weights=STATUS_WEIGHTS)[0]
            created_at = generate_created_date()
            
            # Определяем дополнительные поля в зависимости от статуса
            used_at = None
            used_by_id = None
            
            if status == 'used':
                used_at = generate_used_date(created_at)
                used_by_id = get_random_user_for_usage(users)
            
            # Создаем пропуск
            sql, params = create_pass(user_id, car_number, status, created_at, used_at, used_by_id)
            cursor.execute(sql, params)
            
            created_count += 1
            
            if created_count % 20 == 0:
                print(f"📊 Создано {created_count}/{num_passes} пропусков...")
        
        # Сохраняем изменения
        conn.commit()
        print(f"✅ Успешно создано {created_count} пропусков!")
        
        # Показываем статистику
        show_statistics(cursor)
        
    except Exception as e:
        print(f"❌ Ошибка при создании пропусков: {e}")
        conn.rollback()
    finally:
        conn.close()

def show_statistics(cursor):
    """Показать статистику созданных пропусков"""
    print("\n📊 Статистика пропусков:")
    
    # Общее количество
    cursor.execute("SELECT COUNT(*) FROM passes")
    total = cursor.fetchone()[0]
    print(f"   Всего пропусков: {total}")
    
    # По статусам
    cursor.execute("SELECT status, COUNT(*) FROM passes GROUP BY status")
    for status, count in cursor.fetchall():
        print(f"   {status}: {count}")
    
    # По пользователям (топ 5)
    cursor.execute("""
        SELECT u.full_name, COUNT(p.id) as pass_count 
        FROM users u 
        JOIN passes p ON u.id = p.user_id 
        GROUP BY u.id, u.full_name 
        ORDER BY pass_count DESC 
        LIMIT 5
    """)
    print("\n🏆 Топ-5 пользователей по количеству пропусков:")
    for name, count in cursor.fetchall():
        print(f"   {name}: {count} пропусков")
    
    # Архивные пропуски
    cursor.execute("SELECT COUNT(*) FROM passes WHERE is_archived = 1")
    archived = cursor.fetchone()[0]
    print(f"\n📦 Архивированных пропусков: {archived}")

def clear_all_passes():
    """Удалить все пропуски из базы данных"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM passes")
        conn.commit()
        print("🗑️ Все пропуски удалены из базы данных")
    except Exception as e:
        print(f"❌ Ошибка при удалении пропусков: {e}")
        conn.rollback()
    finally:
        conn.close()

def main():
    """Главная функция"""
    print("🗄️ Генератор пропусков для Easy Pass Bot")
    print("=" * 50)
    
    while True:
        print("\nВыберите действие:")
        print("1. Создать 50 тестовых пропусков")
        print("2. Создать 100 тестовых пропусков")
        print("3. Создать 200 тестовых пропусков")
        print("4. Создать произвольное количество пропусков")
        print("5. Показать текущую статистику")
        print("6. Удалить все пропуски")
        print("0. Выход")
        
        choice = input("\nВведите номер действия: ").strip()
        
        if choice == "1":
            populate_passes(50)
        elif choice == "2":
            populate_passes(100)
        elif choice == "3":
            populate_passes(200)
        elif choice == "4":
            try:
                num = int(input("Введите количество пропусков: "))
                if num > 0:
                    populate_passes(num)
                else:
                    print("❌ Количество должно быть больше 0")
            except ValueError:
                print("❌ Введите корректное число")
        elif choice == "5":
            conn = get_connection()
            cursor = conn.cursor()
            show_statistics(cursor)
            conn.close()
        elif choice == "6":
            confirm = input("⚠️ Вы уверены, что хотите удалить ВСЕ пропуски? (yes/no): ")
            if confirm.lower() in ['yes', 'y', 'да', 'д']:
                clear_all_passes()
            else:
                print("❌ Операция отменена")
        elif choice == "0":
            print("👋 До свидания!")
            break
        else:
            print("❌ Неверный выбор. Попробуйте снова.")

if __name__ == "__main__":
    main()

