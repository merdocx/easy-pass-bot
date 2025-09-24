#!/bin/bash

# Скрипт для перезапуска всех сервисов PM Desk
# Использование: ./restart_all_services.sh

echo "🔄 Перезапуск всех сервисов PM Desk"
echo "==================================="

# Получаем директорию скрипта
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Останавливаем все сервисы
echo "1️⃣ Остановка сервисов..."
./stop_all_services.sh

echo ""
echo "⏳ Ожидание завершения остановки..."
sleep 5

echo ""
echo "2️⃣ Запуск сервисов..."
./start_all_services.sh

echo ""
echo "🎉 Перезапуск завершен!"


