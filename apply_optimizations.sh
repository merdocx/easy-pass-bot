#!/bin/bash

# Скрипт для применения оптимизаций проекта Easy Pass Bot

set -e

echo "🚀 Применение оптимизаций Easy Pass Bot..."

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для вывода сообщений
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Проверка, что мы в правильной директории
if [ ! -f "pyproject.toml" ]; then
    log_error "Запустите скрипт из корневой папки проекта"
    exit 1
fi

# Создание резервной копии
log_info "Создание резервной копии..."
if [ ! -f "pyproject-backup.toml" ]; then
    cp pyproject.toml pyproject-backup.toml
    log_success "Резервная копия pyproject.toml создана"
fi

if [ ! -f "requirements-backup.txt" ]; then
    cp requirements.txt requirements-backup.txt
    log_success "Резервная копия requirements.txt создана"
fi

# Применение оптимизированных файлов
log_info "Применение оптимизированных конфигураций..."
cp pyproject-optimized.toml pyproject.toml
log_success "pyproject.toml обновлен"

# Создание нового виртуального окружения
log_info "Создание нового виртуального окружения..."
if [ -d "venv" ]; then
    log_warning "Удаление старого виртуального окружения..."
    rm -rf venv
fi

python3 -m venv venv
source venv/bin/activate
log_success "Новое виртуальное окружение создано"

# Установка зависимостей
log_info "Установка оптимизированных зависимостей..."
pip install --upgrade pip
pip install -r requirements.txt
log_success "Зависимости установлены"

# Проверка установки
log_info "Проверка установки..."
python -c "import aiogram, aiosqlite, psutil, pydantic; print('Все основные зависимости установлены')"
log_success "Проверка пройдена"

# Запуск тестов
log_info "Запуск тестов..."
if pytest --version >/dev/null 2>&1; then
    pytest tests/ -v --tb=short
    log_success "Тесты пройдены"
else
    log_warning "pytest не установлен, пропускаем тесты"
fi

# Проверка кода
log_info "Проверка кода..."
if flake8 --version >/dev/null 2>&1; then
    flake8 src/ --exclude=__pycache__ || log_warning "Найдены проблемы в коде"
else
    log_warning "flake8 не установлен, пропускаем проверку кода"
fi

# Форматирование кода
log_info "Форматирование кода..."
if black --version >/dev/null 2>&1; then
    black src/ --check || log_warning "Код нуждается в форматировании"
else
    log_warning "black не установлен, пропускаем форматирование"
fi

# Проверка безопасности
log_info "Проверка безопасности..."
if safety --version >/dev/null 2>&1; then
    safety check || log_warning "Найдены уязвимости в зависимостях"
else
    log_warning "safety не установлен, пропускаем проверку безопасности"
fi

# Очистка временных файлов
log_info "Очистка временных файлов..."
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.log" -delete
find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name ".mypy_cache" -type d -exec rm -rf {} + 2>/dev/null || true
log_success "Временные файлы очищены"

# Статистика
log_info "Статистика оптимизации:"
echo "📊 Размер проекта: $(du -sh . --exclude=venv | cut -f1)"
echo "📦 Количество зависимостей: $(pip list | wc -l)"
echo "🐍 Python файлы: $(find . -name "*.py" -not -path "./venv/*" | wc -l)"

log_success "Оптимизация завершена!"
echo ""
echo "📋 Следующие шаги:"
echo "1. Протестируйте бота: python -m easy_pass_bot.bot.main"
echo "2. Проверьте логи: tail -f logs/bot.log"
echo "3. Запустите мониторинг: python scripts/log_monitor.py"
echo ""
echo "🔧 Полезные команды:"
echo "- Установка dev зависимостей: pip install -e .[dev]"
echo "- Запуск тестов: pytest"
echo "- Проверка кода: flake8 src/"
echo "- Форматирование: black src/"
echo "- Проверка безопасности: safety check"
