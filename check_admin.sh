#!/bin/bash

# Скрипт для проверки состояния админки Easy Pass Bot

echo "🔍 Проверка состояния админки Easy Pass Bot"
echo "=============================================="

# Проверяем, запущен ли процесс
if pgrep -f "start_admin.py" > /dev/null; then
    echo "✅ Процесс админки запущен"
    PID=$(pgrep -f "start_admin.py")
    echo "   PID: $PID"
else
    echo "❌ Процесс админки НЕ запущен"
    echo "   Запустите: cd /root/easy_pass_bot/admin && python start_admin.py"
fi

# Проверяем, слушается ли порт 8080
if netstat -tlnp 2>/dev/null | grep -q ":8080 "; then
    echo "✅ Порт 8080 слушается"
else
    echo "❌ Порт 8080 НЕ слушается"
fi

# Проверяем доступность веб-интерфейса
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/ | grep -q "200"; then
    echo "✅ Веб-интерфейс доступен"
    echo "   URL: http://localhost:8080"
else
    echo "❌ Веб-интерфейс НЕ доступен"
fi

# Проверяем базу данных
if [ -f "/root/easy_pass_bot/database/easy_pass.db" ]; then
    echo "✅ База данных существует"
    SIZE=$(du -h /root/easy_pass_bot/database/easy_pass.db | cut -f1)
    echo "   Размер: $SIZE"
else
    echo "❌ База данных НЕ найдена"
fi

# Проверяем проблемные службы
echo ""
echo "🔧 Проверка системных служб:"
if systemctl is-active --quiet easy-pass-admin-frontend.service 2>/dev/null; then
    echo "⚠️  easy-pass-admin-frontend.service активна (может вызывать конфликты)"
else
    echo "✅ easy-pass-admin-frontend.service отключена"
fi

if systemctl is-active --quiet easy-pass-frontend.service 2>/dev/null; then
    echo "⚠️  easy-pass-frontend.service активна (может вызывать конфликты)"
else
    echo "✅ easy-pass-frontend.service отключена"
fi

echo ""
echo "📊 Использование ресурсов:"
if pgrep -f "start_admin.py" > /dev/null; then
    PID=$(pgrep -f "start_admin.py")
    MEM=$(ps -o pid,vsz,rss,pcpu,pmem,comm -p $PID | tail -1)
    echo "   $MEM"
fi

echo ""
echo "🚀 Для запуска админки:"
echo "   cd /root/easy_pass_bot/admin && python start_admin.py"
echo ""
echo "🌐 Админка доступна по адресу: http://localhost:8080"

