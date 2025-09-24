#!/bin/bash

# Скрипт для запуска всех сервисов PM Desk
# Использование: ./start_all_services.sh

echo "🚀 Запуск всех сервисов PM Desk"
echo "================================="

# Переходим в директорию проекта
cd /root/easy-pass-bot

# Активируем виртуальное окружение
source venv/bin/activate

# Функция для проверки запуска процесса
check_process() {
    local process_name=$1
    local max_attempts=10
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if pgrep -f "$process_name" > /dev/null; then
            echo "✅ $process_name запущен"
            return 0
        fi
        echo "   Попытка $attempt/$max_attempts..."
        sleep 2
        ((attempt++))
    done
    
    echo "❌ $process_name не запустился"
    return 1
}

# 1. Запускаем Resident Bot
echo "🤖 Запуск Resident Bot..."
nohup python start_resident_bot.py > resident_bot.log 2>&1 &
if check_process "start_resident_bot.py"; then
    echo "   PID: $(pgrep -f 'start_resident_bot.py')"
else
    echo "   ❌ Ошибка запуска Resident Bot"
fi

echo ""

# 2. Запускаем Security Bot
echo "👮 Запуск Security Bot..."
nohup python start_security_bot.py > security_bot.log 2>&1 &
if check_process "start_security_bot.py"; then
    echo "   PID: $(pgrep -f 'start_security_bot.py')"
else
    echo "   ❌ Ошибка запуска Security Bot"
fi

echo ""

# 3. Запускаем Admin Panel
echo "🌐 Запуск Admin Panel..."
cd admin
nohup python start_admin.py > ../admin.log 2>&1 &
cd ..
if check_process "start_admin.py"; then
    echo "   PID: $(pgrep -f 'start_admin.py')"
else
    echo "   ❌ Ошибка запуска Admin Panel"
fi

echo ""
echo "📊 Итоговый статус:"
echo "==================="

# Проверяем все процессы
processes=("start_resident_bot.py" "start_security_bot.py" "start_admin.py")
for process in "${processes[@]}"; do
    if pgrep -f "$process" > /dev/null; then
        pid=$(pgrep -f "$process")
        echo "✅ $process (PID: $pid)"
    else
        echo "❌ $process не запущен"
    fi
done

echo ""
echo "🌐 Доступные сервисы:"
echo "   • Resident Bot: @permitdeskbot"
echo "   • Security/Admin Bot: @permitadminbot"
echo "   • Admin Panel: http://89.110.96.90:8080"
echo ""
echo "📝 Логи:"
echo "   • Resident Bot: resident_bot.log"
echo "   • Security Bot: security_bot.log"
echo "   • Admin Panel: admin.log"


