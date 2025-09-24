#!/bin/bash

# Скрипт для проверки статуса всех сервисов PM Desk
# Использование: ./check_all_services.sh

echo "🔍 Проверка статуса всех сервисов PM Desk"
echo "=========================================="

# Функция для проверки systemd сервиса
check_systemd_service() {
    local service_name=$1
    local friendly_name=$2
    
    if systemctl is-active --quiet "$service_name"; then
        local pid=$(systemctl show "$service_name" --property=MainPID --value)
        local memory=$(systemctl show "$service_name" --property=MemoryCurrent --value)
        local memory_mb=$((memory / 1024 / 1024))
        
        echo "✅ $friendly_name"
        echo "   Статус: Активен (PID: $pid, Память: ${memory_mb}MB)"
        return 0
    else
        echo "❌ $friendly_name"
        echo "   Статус: Неактивен"
        return 1
    fi
}

# Проверяем systemd сервисы
echo "📊 Systemd сервисы:"
echo "==================="
check_systemd_service "pmdesk-resident-bot" "Resident Bot"
check_systemd_service "pmdesk-security-bot" "Security Bot"
check_systemd_service "pmdesk-admin" "Admin Panel"

echo ""
echo "🌐 Доступность сервисов:"
echo "========================"

# Проверяем Admin Panel
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/ | grep -q "200"; then
    echo "✅ Admin Panel: http://89.110.96.90:8080 - доступна"
else
    echo "❌ Admin Panel: недоступна"
fi

# Проверяем Security Bot API
if curl -s "https://api.telegram.org/bot8069990519:AAHySjIKHlSgVcJpLaXlExZ5Se0juiKX4GQ/getMe" | grep -q '"ok":true'; then
    bot_name=$(curl -s "https://api.telegram.org/bot8069990519:AAHySjIKHlSgVcJpLaXlExZ5Se0juiKX4GQ/getMe" | grep -o '"first_name":"[^"]*"')
    echo "✅ Security Bot: $bot_name - работает"
else
    echo "❌ Security Bot: недоступен"
fi

# Проверяем Resident Bot API (нужен токен)
if curl -s "https://api.telegram.org/bot7961301390:AAGr7wvGtXlExZ5Se0juiKX4GQ/getMe" | grep -q '"ok":true'; then
    bot_name=$(curl -s "https://api.telegram.org/bot7961301390:AAGr7wvGtXlExZ5Se0juiKX4GQ/getMe" | grep -o '"first_name":"[^"]*"')
    echo "✅ Resident Bot: $bot_name - работает"
else
    echo "❌ Resident Bot: недоступен (возможно, неправильный токен)"
fi

echo ""
echo "📝 Последние логи:"
echo "=================="

# Показываем последние записи из логов
echo "📋 Resident Bot (последние 3 строки):"
tail -3 /root/easy-pass-bot/resident_bot.log 2>/dev/null || echo "   Лог недоступен"

echo ""
echo "📋 Security Bot (последние 3 строки):"
tail -3 /root/easy-pass-bot/security_bot.log 2>/dev/null || echo "   Лог недоступен"

echo ""
echo "📋 Admin Panel (последние 3 строки):"
tail -3 /root/easy-pass-bot/admin.log 2>/dev/null || echo "   Лог недоступен"

echo ""
echo "🔧 Управление сервисами:"
echo "========================"
echo "• Запуск всех: ./start_all_services.sh"
echo "• Остановка всех: ./stop_all_services.sh"
echo "• Перезапуск всех: ./restart_all_services.sh"
echo "• Проверка статуса: ./check_all_services.sh"
echo ""
echo "• Systemd управление:"
echo "  - systemctl status pmdesk-*"
echo "  - systemctl restart pmdesk-*"
echo "  - systemctl stop pmdesk-*"
echo "  - systemctl start pmdesk-*"


