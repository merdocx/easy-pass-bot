#!/usr/bin/env python3
"""
Скрипт автоматической проверки безопасности Easy Pass Bot
"""
import os
import sys
import subprocess
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Добавляем src в путь для импортов
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

class SecurityChecker:
    """Класс для проверки безопасности"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.src_path = self.project_root / 'src' / 'easy_pass_bot'
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'checks': {},
            'summary': {
                'total_checks': 0,
                'passed': 0,
                'failed': 0,
                'warnings': 0
            }
        }
    
    def run_check(self, check_name: str, check_func) -> Dict[str, Any]:
        """Запуск проверки безопасности"""
        print(f"🔍 Выполняется проверка: {check_name}")
        try:
            result = check_func()
            self.results['checks'][check_name] = result
            self.results['summary']['total_checks'] += 1
            
            if result['status'] == 'PASS':
                self.results['summary']['passed'] += 1
                print(f"✅ {check_name}: ПРОЙДЕНО")
            elif result['status'] == 'WARNING':
                self.results['summary']['warnings'] += 1
                print(f"⚠️  {check_name}: ПРЕДУПРЕЖДЕНИЕ")
            else:
                self.results['summary']['failed'] += 1
                print(f"❌ {check_name}: НЕ ПРОЙДЕНО")
            
            if result.get('details'):
                for detail in result['details']:
                    print(f"   - {detail}")
            
            return result
        except Exception as e:
            error_result = {
                'status': 'ERROR',
                'message': f'Ошибка при выполнении проверки: {str(e)}',
                'details': []
            }
            self.results['checks'][check_name] = error_result
            self.results['summary']['total_checks'] += 1
            self.results['summary']['failed'] += 1
            print(f"💥 {check_name}: ОШИБКА - {str(e)}")
            return error_result
    
    def check_hardcoded_secrets(self) -> Dict[str, Any]:
        """Проверка на захардкоженные секреты"""
        secret_patterns = [
            r'BOT_TOKEN\s*=\s*["\'][^"\']+["\']',
            r'password\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
            r'api_key\s*=\s*["\'][^"\']+["\']',
            r'token\s*=\s*["\'][^"\']+["\']',
        ]
        
        issues = []
        for file_path in self.src_path.rglob('*.py'):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    for pattern in secret_patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        for match in matches:
                            issues.append(f"{file_path}: {match}")
            except Exception:
                continue
        
        if issues:
            return {
                'status': 'FAIL',
                'message': f'Найдено {len(issues)} потенциальных захардкоженных секретов',
                'details': issues[:10]  # Показываем только первые 10
            }
        else:
            return {
                'status': 'PASS',
                'message': 'Захардкоженные секреты не найдены',
                'details': []
            }
    
    def check_sql_injection(self) -> Dict[str, Any]:
        """Проверка защиты от SQL инъекций"""
        dangerous_patterns = [
            r'execute\s*\(\s*["\'].*%s.*["\']',
            r'execute\s*\(\s*f["\'].*{.*}.*["\']',
            r'execute\s*\(\s*["\'].*\+.*["\']',
            r'query\s*=\s*["\'].*\+.*["\']',
        ]
        
        issues = []
        for file_path in self.src_path.rglob('*.py'):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    for pattern in dangerous_patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
                        for match in matches:
                            issues.append(f"{file_path}: {match}")
            except Exception:
                continue
        
        if issues:
            return {
                'status': 'FAIL',
                'message': f'Найдено {len(issues)} потенциальных SQL инъекций',
                'details': issues[:10]
            }
        else:
            return {
                'status': 'PASS',
                'message': 'SQL инъекции не обнаружены',
                'details': []
            }
    
    def check_input_validation(self) -> Dict[str, Any]:
        """Проверка валидации входных данных"""
        validation_files = [
            'security/validator.py',
            'services/validation_service.py'
        ]
        
        issues = []
        for file_name in validation_files:
            file_path = self.src_path / file_name
            if not file_path.exists():
                issues.append(f"Файл валидации не найден: {file_name}")
        
        # Проверяем использование валидации в обработчиках
        handler_files = list(self.src_path.glob('handlers/*.py'))
        for handler_file in handler_files:
            try:
                with open(handler_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'validator' not in content.lower():
                        issues.append(f"Валидация не используется в {handler_file.name}")
            except Exception:
                continue
        
        if issues:
            return {
                'status': 'WARNING',
                'message': f'Найдено {len(issues)} проблем с валидацией',
                'details': issues
            }
        else:
            return {
                'status': 'PASS',
                'message': 'Валидация входных данных настроена корректно',
                'details': []
            }
    
    def check_authentication(self) -> Dict[str, Any]:
        """Проверка системы аутентификации"""
        issues = []
        
        # Проверяем наличие проверок ролей
        handler_files = list(self.src_path.glob('handlers/*.py'))
        for handler_file in handler_files:
            try:
                with open(handler_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'is_admin' not in content and 'is_security' not in content:
                        issues.append(f"Отсутствуют проверки ролей в {handler_file.name}")
            except Exception:
                continue
        
        if issues:
            return {
                'status': 'WARNING',
                'message': f'Найдено {len(issues)} проблем с аутентификацией',
                'details': issues
            }
        else:
            return {
                'status': 'PASS',
                'message': 'Система аутентификации настроена корректно',
                'details': []
            }
    
    def check_logging(self) -> Dict[str, Any]:
        """Проверка системы логирования"""
        issues = []
        
        # Проверяем наличие аудит-логгера
        audit_file = self.src_path / 'security' / 'audit_logger.py'
        if not audit_file.exists():
            issues.append("Аудит-логгер не найден")
        
        # Проверяем использование логирования в критических операциях
        critical_files = [
            'handlers/admin_handlers.py',
            'handlers/security_handlers.py',
            'services/pass_service.py',
            'services/user_service.py'
        ]
        
        for file_name in critical_files:
            file_path = self.src_path / file_name
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if 'audit_logger' not in content:
                            issues.append(f"Аудит-логирование не используется в {file_name}")
                except Exception:
                    continue
        
        if issues:
            return {
                'status': 'WARNING',
                'message': f'Найдено {len(issues)} проблем с логированием',
                'details': issues
            }
        else:
            return {
                'status': 'PASS',
                'message': 'Система логирования настроена корректно',
                'details': []
            }
    
    def check_rate_limiting(self) -> Dict[str, Any]:
        """Проверка системы ограничения частоты запросов"""
        rate_limiter_file = self.src_path / 'security' / 'rate_limiter.py'
        if not rate_limiter_file.exists():
            return {
                'status': 'FAIL',
                'message': 'Rate limiter не найден',
                'details': []
            }
        
        # Проверяем использование rate limiting в обработчиках
        handler_files = list(self.src_path.glob('handlers/*.py'))
        usage_count = 0
        
        for handler_file in handler_files:
            try:
                with open(handler_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'rate_limiter' in content:
                        usage_count += 1
            except Exception:
                continue
        
        if usage_count == 0:
            return {
                'status': 'WARNING',
                'message': 'Rate limiting не используется в обработчиках',
                'details': []
            }
        else:
            return {
                'status': 'PASS',
                'message': f'Rate limiting используется в {usage_count} файлах',
                'details': []
            }
    
    def check_dependencies(self) -> Dict[str, Any]:
        """Проверка зависимостей на уязвимости"""
        try:
            # Запускаем safety check
            result = subprocess.run(
                ['safety', 'check', '--json'],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.returncode == 0:
                return {
                    'status': 'PASS',
                    'message': 'Уязвимости в зависимостях не найдены',
                    'details': []
                }
            else:
                try:
                    vulnerabilities = json.loads(result.stdout)
                    return {
                        'status': 'FAIL',
                        'message': f'Найдено {len(vulnerabilities)} уязвимостей в зависимостях',
                        'details': [f"{v['package']}: {v['advisory']}" for v in vulnerabilities[:10]]
                    }
                except json.JSONDecodeError:
                    return {
                        'status': 'WARNING',
                        'message': 'Не удалось проанализировать зависимости',
                        'details': [result.stderr]
                    }
        except FileNotFoundError:
            return {
                'status': 'WARNING',
                'message': 'Safety не установлен. Установите: pip install safety',
                'details': []
            }
    
    def check_file_permissions(self) -> Dict[str, Any]:
        """Проверка прав доступа к файлам"""
        issues = []
        
        # Проверяем права на конфигурационные файлы
        config_files = [
            '.env',
            'database/easy_pass.db',
            'logs/',
        ]
        
        for file_name in config_files:
            file_path = self.project_root / file_name
            if file_path.exists():
                stat = file_path.stat()
                # Проверяем, что файл не доступен для записи всем
                if stat.st_mode & 0o002:
                    issues.append(f"Файл {file_name} доступен для записи всем пользователям")
        
        if issues:
            return {
                'status': 'WARNING',
                'message': f'Найдено {len(issues)} проблем с правами доступа',
                'details': issues
            }
        else:
            return {
                'status': 'PASS',
                'message': 'Права доступа к файлам настроены корректно',
                'details': []
            }
    
    def check_environment_config(self) -> Dict[str, Any]:
        """Проверка конфигурации окружения"""
        issues = []
        
        # Проверяем наличие .env файла
        env_file = self.project_root / '.env'
        if not env_file.exists():
            issues.append(".env файл не найден")
        
        # Проверяем наличие .env.example
        env_example = self.project_root / '.env.example'
        if not env_example.exists():
            issues.append(".env.example файл не найден")
        
        # Проверяем, что .env не в git
        gitignore = self.project_root / '.gitignore'
        if gitignore.exists():
            with open(gitignore, 'r') as f:
                content = f.read()
                if '.env' not in content:
                    issues.append(".env не добавлен в .gitignore")
        
        if issues:
            return {
                'status': 'WARNING',
                'message': f'Найдено {len(issues)} проблем с конфигурацией окружения',
                'details': issues
            }
        else:
            return {
                'status': 'PASS',
                'message': 'Конфигурация окружения настроена корректно',
                'details': []
            }
    
    def run_all_checks(self):
        """Запуск всех проверок безопасности"""
        print("🛡️  Запуск проверки безопасности Easy Pass Bot")
        print("=" * 50)
        
        checks = [
            ("hardcoded_secrets", self.check_hardcoded_secrets),
            ("sql_injection", self.check_sql_injection),
            ("input_validation", self.check_input_validation),
            ("authentication", self.check_authentication),
            ("logging", self.check_logging),
            ("rate_limiting", self.check_rate_limiting),
            ("dependencies", self.check_dependencies),
            ("file_permissions", self.check_file_permissions),
            ("environment_config", self.check_environment_config),
        ]
        
        for check_name, check_func in checks:
            self.run_check(check_name, check_func)
            print()
        
        self.print_summary()
        self.save_report()
    
    def print_summary(self):
        """Вывод сводки результатов"""
        print("=" * 50)
        print("📊 СВОДКА РЕЗУЛЬТАТОВ")
        print("=" * 50)
        
        summary = self.results['summary']
        total = summary['total_checks']
        passed = summary['passed']
        failed = summary['failed']
        warnings = summary['warnings']
        
        print(f"Всего проверок: {total}")
        print(f"✅ Пройдено: {passed}")
        print(f"❌ Не пройдено: {failed}")
        print(f"⚠️  Предупреждения: {warnings}")
        
        if failed == 0 and warnings == 0:
            print("\n🎉 Все проверки безопасности пройдены успешно!")
        elif failed == 0:
            print(f"\n⚠️  Есть {warnings} предупреждений, которые стоит исправить")
        else:
            print(f"\n🚨 Найдено {failed} критических проблем безопасности!")
    
    def save_report(self):
        """Сохранение отчета"""
        report_file = self.project_root / 'security_report.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 Отчет сохранен в: {report_file}")


def main():
    """Основная функция"""
    checker = SecurityChecker()
    checker.run_all_checks()


if __name__ == "__main__":
    main()


