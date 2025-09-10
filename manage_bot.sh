#!/bin/bash
# Скрипт управления ботом Easy Pass

SERVICE_NAME="easy-pass-bot.service"

case "$1" in
    start)
        echo "🚀 Запуск бота..."
        systemctl start $SERVICE_NAME
        systemctl status $SERVICE_NAME --no-pager
        ;;
    stop)
        echo "⏹️ Остановка бота..."
        systemctl stop $SERVICE_NAME
        echo "✅ Бот остановлен"
        ;;
    restart)
        echo "🔄 Перезапуск бота..."
        systemctl restart $SERVICE_NAME
        systemctl status $SERVICE_NAME --no-pager
        ;;
    status)
        echo "📊 Статус бота:"
        systemctl status $SERVICE_NAME --no-pager
        ;;
    logs)
        echo "📋 Логи бота:"
        journalctl -u $SERVICE_NAME -f --no-pager
        ;;
    enable)
        echo "✅ Включение автозапуска..."
        systemctl enable $SERVICE_NAME
        echo "✅ Автозапуск включен"
        ;;
    disable)
        echo "❌ Отключение автозапуска..."
        systemctl disable $SERVICE_NAME
        echo "❌ Автозапуск отключен"
        ;;
    *)
        echo "🤖 Управление ботом Easy Pass"
        echo ""
        echo "Использование: $0 {start|stop|restart|status|logs|enable|disable}"
        echo ""
        echo "Команды:"
        echo "  start    - Запустить бота"
        echo "  stop     - Остановить бота"
        echo "  restart  - Перезапустить бота"
        echo "  status   - Показать статус"
        echo "  logs     - Показать логи в реальном времени"
        echo "  enable   - Включить автозапуск"
        echo "  disable  - Отключить автозапуск"
        ;;
esac






