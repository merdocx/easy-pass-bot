#!/bin/bash

# Скрипт для остановки всех сервисов PM Desk
# Использование: ./stop_all_services.sh

echo "⏹️  Остановка всех сервисов PM Desk"
echo "=================================="

# Функция для остановки процесса
stop_process() {
    local process_name=$1
    local friendly_name=$2
    
    if pgrep -f "$process_name" > /dev/null; then
        pids=$(pgrep -f "$process_name")
        echo "⏹️  Остановка $friendly_name (PID: $pids)..."
        pkill -f "$process_name"
        
        # Ждем завершения
        local max_wait=10
        local wait_count=0
        while [ $wait_count -lt $max_wait ]; do
            if ! pgrep -f "$process_name" > /dev/null; then
                echo "✅ $friendly_name остановлен"
                return 0
            fi
            sleep 1
            ((wait_count++))
        done
        
        # Принудительная остановка
        echo "🔨 Принудительная остановка $friendly_name..."
        pkill -9 -f "$process_name"
        sleep 2
        
        if ! pgrep -f "$process_name" > /dev/null; then
            echo "✅ $friendly_name остановлен принудительно"
        else
            echo "❌ Не удалось остановить $friendly_name"
        fi
    else
        echo "ℹ️  $friendly_name не был запущен"
    fi
}

# Останавливаем все процессы
stop_process "start_resident_bot.py" "Resident Bot"
stop_process "start_security_bot.py" "Security Bot"
stop_process "start_admin.py" "Admin Panel"

echo ""
echo "📊 Финальная проверка:"
echo "====================="

# Проверяем, что все процессы остановлены
remaining_processes=$(ps aux | grep -E "(start_resident_bot|start_security_bot|start_admin)" | grep -v grep | wc -l)

if [ $remaining_processes -eq 0 ]; then
    echo "✅ Все сервисы успешно остановлены"
else
    echo "⚠️  Остались активные процессы:"
    ps aux | grep -E "(start_resident_bot|start_security_bot|start_admin)" | grep -v grep
fi

echo ""
echo "🔍 Проверка портов:"
echo "==================="

# Проверяем, что порты освобождены
if ! netstat -tlnp 2>/dev/null | grep -q ":8080 "; then
    echo "✅ Порт 8080 (Admin Panel) освобожден"
else
    echo "⚠️  Порт 8080 все еще занят"
fi

echo ""
echo "🏁 Остановка завершена"


