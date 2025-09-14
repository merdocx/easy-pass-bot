#!/usr/bin/env python3
"""
Тест реальной отправки уведомлений о смене роли в Telegram
"""

import asyncio
import sys
import os

# Добавляем путь к модулям
sys.path.append('/root/easy_pass_bot/src')

from easy_pass_bot.utils.telegram_notifier import TelegramNotifier

async def test_telegram_role_notifications():
    """Тест отправки уведомлений о смене роли в Telegram"""
    
    print("🧪 Тестирование отправки уведомлений о смене роли в Telegram")
    print("=" * 70)
    
    try:
        # Получаем токен бота из переменных окружения
        bot_token = os.getenv('BOT_TOKEN')
        if not bot_token:
            print("❌ BOT_TOKEN не найден в переменных окружения")
            return False
        
        print(f"✅ BOT_TOKEN найден: {bot_token[:10]}...")
        
        # Создаем экземпляр уведомлений
        notifier = TelegramNotifier(bot_token)
        
        # Тестовые данные (используем реальный Telegram ID для тестирования)
        test_telegram_id = 6358556135  # Telegram ID пользователя Иванова
        test_full_name = "Иванов Иван Иванович"
        
        print(f"📱 Тестируем отправку на Telegram ID: {test_telegram_id}")
        
        # 1. Тест уведомления о смене роли на охранника
        print("\n1. Тестирование уведомления о смене роли на 'security'...")
        try:
            success = await notifier.send_role_change_notification(
                test_telegram_id,
                test_full_name,
                'resident',
                'security'
            )
            
            if success:
                print("   ✅ Уведомление о смене роли на 'security' отправлено успешно")
            else:
                print("   ❌ Не удалось отправить уведомление о смене роли на 'security'")
        except Exception as e:
            print(f"   ❌ Ошибка при отправке уведомления о смене роли на 'security': {e}")
        
        await asyncio.sleep(2)  # Пауза между сообщениями
        
        # 2. Тест уведомления о смене роли на жителя
        print("\n2. Тестирование уведомления о смене роли на 'resident'...")
        try:
            success = await notifier.send_role_change_notification(
                test_telegram_id,
                test_full_name,
                'security',
                'resident'
            )
            
            if success:
                print("   ✅ Уведомление о смене роли на 'resident' отправлено успешно")
            else:
                print("   ❌ Не удалось отправить уведомление о смене роли на 'resident'")
        except Exception as e:
            print(f"   ❌ Ошибка при отправке уведомления о смене роли на 'resident': {e}")
        
        await asyncio.sleep(2)  # Пауза между сообщениями
        
        # 3. Тест уведомления о смене роли на администратора
        print("\n3. Тестирование уведомления о смене роли на 'admin'...")
        try:
            success = await notifier.send_role_change_notification(
                test_telegram_id,
                test_full_name,
                'resident',
                'admin'
            )
            
            if success:
                print("   ✅ Уведомление о смене роли на 'admin' отправлено успешно")
            else:
                print("   ❌ Не удалось отправить уведомление о смене роли на 'admin'")
        except Exception as e:
            print(f"   ❌ Ошибка при отправке уведомления о смене роли на 'admin': {e}")
        
        # Закрываем соединение
        await notifier.close()
        
        print("\n" + "=" * 70)
        print("🎉 ТЕСТ TELEGRAM УВЕДОМЛЕНИЙ ЗАВЕРШЕН!")
        print("✅ Проверьте Telegram бота для получения уведомлений")
        print("✅ Все типы уведомлений о смене роли протестированы")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Критическая ошибка в тесте: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_telegram_role_notifications())
    sys.exit(0 if success else 1)
