#!/usr/bin/env python3
"""
Скрипт для запуска тестов Easy Pass Bot
"""
import sys
import subprocess
import argparse
import os
from pathlib import Path


def run_command(command, description):
    """Запустить команду и вывести результат"""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            check=True, 
            capture_output=True, 
            text=True
        )
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка выполнения команды: {e}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False


def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(description='Запуск тестов Easy Pass Bot')
    parser.add_argument(
        '--type', 
        choices=['unit', 'integration', 'e2e', 'all'], 
        default='all',
        help='Тип тестов для запуска'
    )
    parser.add_argument(
        '--coverage', 
        action='store_true',
        help='Включить проверку покрытия кода'
    )
    parser.add_argument(
        '--performance', 
        action='store_true',
        help='Включить тесты производительности'
    )
    parser.add_argument(
        '--security', 
        action='store_true',
        help='Включить тесты безопасности'
    )
    parser.add_argument(
        '--verbose', 
        action='store_true',
        help='Подробный вывод'
    )
    parser.add_argument(
        '--parallel', 
        type=int,
        default=0,
        help='Количество параллельных процессов (0 = отключено)'
    )
    parser.add_argument(
        '--html-report', 
        action='store_true',
        help='Создать HTML отчет'
    )
    
    args = parser.parse_args()
    
    # Переходим в директорию проекта
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    print("🧪 Easy Pass Bot - Система тестирования")
    print(f"📁 Рабочая директория: {project_root}")
    
    # Базовые команды pytest
    pytest_cmd = "python -m pytest"
    
    # Добавляем опции
    if args.verbose:
        pytest_cmd += " -v"
    
    if args.coverage:
        pytest_cmd += " --cov=src/easy_pass_bot --cov-report=html:htmlcov --cov-report=term-missing"
    
    if args.parallel > 0:
        pytest_cmd += f" -n {args.parallel}"
    elif args.parallel == 0:
        pytest_cmd += " -n 0"  # Отключаем параллельное выполнение
    
    if args.html_report:
        pytest_cmd += " --html=report.html --self-contained-html"
    
    # Выбираем тесты по типу
    if args.type == 'unit':
        pytest_cmd += " tests/unit/"
    elif args.type == 'integration':
        pytest_cmd += " tests/integration/"
    elif args.type == 'e2e':
        pytest_cmd += " tests/e2e/"
    else:  # all
        pytest_cmd += " tests/"
    
    # Исключаем медленные тесты по умолчанию
    if not args.performance:
        pytest_cmd += " -m 'not slow'"
    
    if not args.security:
        pytest_cmd += " -m 'not security'"
    
    # Запускаем тесты
    success = run_command(pytest_cmd, "Запуск тестов")
    
    if not success:
        print("\n❌ Тесты завершились с ошибками!")
        sys.exit(1)
    
    # Дополнительные проверки
    if args.coverage:
        print("\n📊 Отчет о покрытии кода создан в htmlcov/index.html")
    
    if args.html_report:
        print("\n📄 HTML отчет создан в report.html")
    
    print("\n✅ Все тесты выполнены успешно!")
    
    # Запускаем дополнительные проверки
    print("\n🔍 Дополнительные проверки...")
    
    # Проверка стиля кода
    if run_command("python -m flake8 src/ --exclude=__pycache__", "Проверка стиля кода (flake8)"):
        print("✅ Стиль кода соответствует стандартам")
    else:
        print("⚠️  Найдены нарушения стиля кода")
    
    # Проверка типов
    if run_command("python -m mypy src/ --ignore-missing-imports", "Проверка типов (mypy)"):
        print("✅ Типизация корректна")
    else:
        print("⚠️  Найдены проблемы с типизацией")
    
    print("\n🎉 Все проверки завершены!")


if __name__ == "__main__":
    main()