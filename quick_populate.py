#!/usr/bin/env python3
"""
Быстрое наполнение базы данных пропусками
"""

import sqlite3
import random
from datetime import datetime, timedelta

DB_PATH = "/root/easy_pass_bot/database/easy_pass.db"

def quick_populate(num_passes=50):
    """Быстро создать пропуски"""
    print(f"🚀 Создаем {num_passes} пропусков...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Получаем пользователей
    cursor.execute("SELECT id FROM users WHERE status = 'approved'")
    user_ids = [row[0] for row in cursor.fetchall()]
    
    if not user_ids:
        print("❌ Нет одобренных пользователей!")
        return
    
    # Список номеров автомобилей
    car_numbers = [
        "А123БВ777", "В456ГД123", "Е789ЖЗ456", "К012ЛМ789", "Н345ОП012",
        "Р678СТ345", "У901ФХ678", "Ц234ШЩ901", "Ю567ЭЮ234", "Я890АБ567",
        "А111АА777", "В222ВВ123", "Е333ЕЕ456", "К444КК789", "Н555НН012",
        "Р666РР345", "У777УУ678", "Ц888ЦЦ901", "Ю999ЮЮ234", "Я000ЯЯ567"
    ]
    
    statuses = ['active', 'used', 'cancelled']
    
    for i in range(num_passes):
        user_id = random.choice(user_ids)
        car_number = random.choice(car_numbers)
        status = random.choice(statuses)
        
        # Дата создания (последние 30 дней)
        days_ago = random.randint(0, 30)
        created_at = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d %H:%M:%S")
        
        # Дополнительные поля
        used_at = None
        used_by_id = None
        
        if status == 'used':
            # Дата использования через 1-7 дней после создания
            used_days = random.randint(1, 7)
            used_at = (datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S") + 
                      timedelta(days=used_days)).strftime("%Y-%m-%d %H:%M:%S")
            used_by_id = random.choice(user_ids)
        
        cursor.execute("""
            INSERT INTO passes (user_id, car_number, status, created_at, used_at, used_by_id, is_archived)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, car_number, status, created_at, used_at, used_by_id, False))
    
    conn.commit()
    conn.close()
    
    print(f"✅ Создано {num_passes} пропусков!")
    
    # Показываем статистику
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM passes")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT status, COUNT(*) FROM passes GROUP BY status")
    print(f"📊 Всего пропусков: {total}")
    for status, count in cursor.fetchall():
        print(f"   {status}: {count}")
    conn.close()

if __name__ == "__main__":
    quick_populate(50)
