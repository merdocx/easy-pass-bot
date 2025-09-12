#!/bin/bash

# Скрипт для перезапуска админки Easy Pass Bot

echo "🔄 Перезапуск админки Easy Pass Bot"
echo "===================================="

# Останавливаем текущий процесс
echo "⏹️  Остановка текущего процесса..."
if pgrep -f "start_admin.py" > /dev/null; then
    pkill -f "start_admin.py"
    sleep 2
    echo "✅ Процесс остановлен"
else
    echo "ℹ️  Процесс не был запущен"
fi

# Ждем освобождения порта
echo "⏳ Ожидание освобождения порта 8080..."
for i in {1..10}; do
    if ! netstat -tlnp 2>/dev/null | grep -q ":8080 "; then
        echo "✅ Порт 8080 освобожден"
        break
    fi
    echo "   Попытка $i/10..."
    sleep 1
done

# Переходим в директорию админки и запускаем
echo "🚀 Запуск админки..."
cd /root/easy_pass_bot/admin

# Запускаем в фоновом режиме
nohup python start_admin.py > /dev/null 2>&1 &

# Ждем запуска
echo "⏳ Ожидание запуска..."
for i in {1..10}; do
    if pgrep -f "start_admin.py" > /dev/null; then
        echo "✅ Админка запущена"
        break
    fi
    echo "   Попытка $i/10..."
    sleep 2
done

# Проверяем доступность
echo "🔍 Проверка доступности..."
sleep 3
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/ | grep -q "200"; then
    echo "✅ Админка доступна по адресу: http://localhost:8080"
else
    echo "❌ Админка недоступна, проверьте логи"
fi

echo ""
echo "📊 Статус процесса:"
if pgrep -f "start_admin.py" > /dev/null; then
    PID=$(pgrep -f "start_admin.py")
    echo "   PID: $PID"
    ps -o pid,vsz,rss,pcpu,pmem,comm -p $PID | tail -1
fi
