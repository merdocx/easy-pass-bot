#!/bin/bash

# Скрипт для проверки статуса админки

echo "🔍 Проверка статуса админки PM Desk"
echo "===================================="

# Проверяем, запущен ли процесс
if pgrep -f "start_admin.py" > /dev/null; then
    PID=$(pgrep -f "start_admin.py")
    echo "✅ Процесс админки запущен (PID: $PID)"
    
    # Проверяем использование ресурсов
    echo "📊 Использование ресурсов:"
    ps -o pid,vsz,rss,pcpu,pmem,comm -p $PID | tail -1
else
    echo "❌ Процесс админки не запущен"
    exit 1
fi

echo ""

# Проверяем доступность по localhost
echo "🌐 Проверка доступности:"
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/ | grep -q "200"; then
    echo "✅ Localhost (http://localhost:8080) - доступен"
else
    echo "❌ Localhost (http://localhost:8080) - недоступен"
fi

# Проверяем доступность по внешнему IP
if curl -s -o /dev/null -w "%{http_code}" http://89.110.96.90:8080/ | grep -q "200"; then
    echo "✅ Внешний IP (http://89.110.96.90:8080) - доступен"
else
    echo "❌ Внешний IP (http://89.110.96.90:8080) - недоступен"
fi

echo ""

# Проверяем порт
echo "🔌 Проверка порта 8080:"
if netstat -tlnp | grep ":8080 " > /dev/null; then
    echo "✅ Порт 8080 слушается"
    netstat -tlnp | grep ":8080 "
else
    echo "❌ Порт 8080 не слушается"
fi

echo ""
echo "📝 Последние логи (если доступны):"
if [ -f "/root/easy-pass-bot/admin.log" ]; then
    tail -5 /root/easy-pass-bot/admin.log
else
    echo "   Лог файл не найден"
fi


