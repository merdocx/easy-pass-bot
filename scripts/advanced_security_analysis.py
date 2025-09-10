#!/usr/bin/env python3
"""
Расширенный анализ безопасности Easy Pass Bot
"""
import os
import sys
import json
import re
import ast
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Set
import importlib.util

# Добавляем src в путь для импортов
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

class AdvancedSecurityAnalyzer:
    """Расширенный анализатор безопасности"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.src_path = self.project_root / 'src' / 'easy_pass_bot'
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'analysis_type': 'advanced_security',
            'findings': {
                'critical': [],
                'high': [],
                'medium': [],
                'low': [],
                'info': []
            },
            'metrics': {},
            'recommendations': []
        }
    
    def analyze_code_quality(self) -> Dict[str, Any]:
        """Анализ качества кода с точки зрения безопасности"""
        findings = []
        
        # Проверка на использование eval/exec
        for file_path in self.src_path.rglob('*.py'):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'eval(' in content or 'exec(' in content:
                        findings.append({
                            'file': str(file_path.relative_to(self.project_root)),
                            'issue': 'Use of eval/exec detected',
                            'severity': 'high',
                            'description': 'eval() and exec() can lead to code injection vulnerabilities'
                        })
            except Exception:
                continue
        
        # Проверка на использование pickle
        for file_path in self.src_path.rglob('*.py'):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'pickle' in content:
                        findings.append({
                            'file': str(file_path.relative_to(self.project_root)),
                            'issue': 'Use of pickle detected',
                            'severity': 'medium',
                            'description': 'pickle can lead to arbitrary code execution'
                        })
            except Exception:
                continue
        
        # Проверка на использование os.system/subprocess без валидации
        for file_path in self.src_path.rglob('*.py'):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'os.system(' in content or 'subprocess.call(' in content:
                        findings.append({
                            'file': str(file_path.relative_to(self.project_root)),
                            'issue': 'Use of os.system/subprocess detected',
                            'severity': 'high',
                            'description': 'Command execution without proper validation'
                        })
            except Exception:
                continue
        
        return {
            'total_issues': len(findings),
            'findings': findings
        }
    
    def analyze_dependencies(self) -> Dict[str, Any]:
        """Анализ зависимостей на уязвимости"""
        try:
            # Проверяем requirements.txt
            requirements_file = self.project_root / 'requirements.txt'
            if requirements_file.exists():
                with open(requirements_file, 'r') as f:
                    requirements = f.read()
                
                # Анализируем версии зависимостей
                outdated_packages = []
                for line in requirements.split('\n'):
                    if '==' in line:
                        package, version = line.split('==')
                        package = package.strip()
                        version = version.strip()
                        
                        # Проверяем известные уязвимости
                        if package == 'aiogram' and version < '3.13.0':
                            outdated_packages.append({
                                'package': package,
                                'version': version,
                                'severity': 'medium',
                                'description': 'Outdated aiogram version may have security issues'
                            })
                
                return {
                    'total_packages': len([line for line in requirements.split('\n') if line.strip()]),
                    'outdated_packages': outdated_packages,
                    'vulnerabilities': []
                }
        except Exception as e:
            return {
                'error': str(e),
                'total_packages': 0,
                'outdated_packages': [],
                'vulnerabilities': []
            }
    
    def analyze_authentication_flow(self) -> Dict[str, Any]:
        """Анализ потока аутентификации"""
        issues = []
        
        # Проверяем наличие проверок ролей
        handler_files = list(self.src_path.glob('handlers/*.py'))
        auth_coverage = 0
        
        for handler_file in handler_files:
            try:
                with open(handler_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'is_admin' in content or 'is_security' in content:
                        auth_coverage += 1
            except Exception:
                continue
        
        if auth_coverage < len(handler_files) * 0.8:
            issues.append({
                'issue': 'Incomplete authentication coverage',
                'severity': 'high',
                'description': f'Only {auth_coverage}/{len(handler_files)} handler files have auth checks'
            })
        
        # Проверяем наличие session management
        session_management = False
        for file_path in self.src_path.rglob('*.py'):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'session' in content.lower() or 'jwt' in content.lower():
                        session_management = True
                        break
            except Exception:
                continue
        
        if not session_management:
            issues.append({
                'issue': 'No session management detected',
                'severity': 'medium',
                'description': 'No session or JWT token management found'
            })
        
        return {
            'auth_coverage_percent': (auth_coverage / len(handler_files)) * 100 if handler_files else 0,
            'session_management': session_management,
            'issues': issues
        }
    
    def analyze_data_validation(self) -> Dict[str, Any]:
        """Анализ валидации данных"""
        validation_coverage = 0
        total_endpoints = 0
        issues = []
        
        # Подсчитываем эндпоинты и их валидацию
        for file_path in self.src_path.rglob('*.py'):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # Ищем функции-обработчики
                    if 'async def' in content and ('message' in content or 'callback' in content):
                        total_endpoints += 1
                        
                        # Проверяем наличие валидации
                        if 'validator' in content or 'validate' in content:
                            validation_coverage += 1
            except Exception:
                continue
        
        if validation_coverage < total_endpoints * 0.7:
            issues.append({
                'issue': 'Insufficient input validation',
                'severity': 'high',
                'description': f'Only {validation_coverage}/{total_endpoints} endpoints have validation'
            })
        
        return {
            'validation_coverage_percent': (validation_coverage / total_endpoints) * 100 if total_endpoints else 0,
            'total_endpoints': total_endpoints,
            'validated_endpoints': validation_coverage,
            'issues': issues
        }
    
    def analyze_error_handling(self) -> Dict[str, Any]:
        """Анализ обработки ошибок"""
        issues = []
        
        # Проверяем на раскрытие чувствительной информации в ошибках
        for file_path in self.src_path.rglob('*.py'):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # Ищем потенциально опасные сообщения об ошибках
                    dangerous_patterns = [
                        r'raise.*Exception.*str\(.*\)',
                        r'logger\.error.*str\(.*\)',
                        r'print.*str\(.*\)'
                    ]
                    
                    for pattern in dangerous_patterns:
                        if re.search(pattern, content):
                            issues.append({
                                'file': str(file_path.relative_to(self.project_root)),
                                'issue': 'Potential information disclosure in error handling',
                                'severity': 'medium',
                                'description': 'Error messages may expose sensitive information'
                            })
            except Exception:
                continue
        
        return {
            'total_issues': len(issues),
            'issues': issues
        }
    
    def analyze_logging_security(self) -> Dict[str, Any]:
        """Анализ безопасности логирования"""
        issues = []
        
        # Проверяем логирование чувствительных данных
        for file_path in self.src_path.rglob('*.py'):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # Ищем логирование потенциально чувствительных данных
                    sensitive_patterns = [
                        r'logger.*password',
                        r'logger.*token',
                        r'logger.*secret',
                        r'logger.*key'
                    ]
                    
                    for pattern in sensitive_patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            issues.append({
                                'file': str(file_path.relative_to(self.project_root)),
                                'issue': 'Potential sensitive data in logs',
                                'severity': 'medium',
                                'description': 'Sensitive data may be logged'
                            })
            except Exception:
                continue
        
        return {
            'total_issues': len(issues),
            'issues': issues
        }
    
    def analyze_crypto_usage(self) -> Dict[str, Any]:
        """Анализ использования криптографии"""
        crypto_usage = {
            'hashing': False,
            'encryption': False,
            'signing': False,
            'random': False
        }
        
        for file_path in self.src_path.rglob('*.py'):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    if 'hashlib' in content or 'hash' in content:
                        crypto_usage['hashing'] = True
                    if 'cryptography' in content or 'encrypt' in content:
                        crypto_usage['encryption'] = True
                    if 'hmac' in content or 'sign' in content:
                        crypto_usage['signing'] = True
                    if 'secrets' in content or 'random' in content:
                        crypto_usage['random'] = True
            except Exception:
                continue
        
        return crypto_usage
    
    def analyze_file_permissions(self) -> Dict[str, Any]:
        """Анализ прав доступа к файлам"""
        issues = []
        
        # Проверяем права на конфигурационные файлы
        sensitive_files = [
            '.env',
            'database/easy_pass.db',
            'logs/',
            'config.py'
        ]
        
        for file_name in sensitive_files:
            file_path = self.project_root / file_name
            if file_path.exists():
                try:
                    stat = file_path.stat()
                    # Проверяем права доступа
                    if stat.st_mode & 0o002:  # World writable
                        issues.append({
                            'file': file_name,
                            'issue': 'World writable file',
                            'severity': 'high',
                            'description': 'File is writable by all users'
                        })
                    elif stat.st_mode & 0o020:  # Group writable
                        issues.append({
                            'file': file_name,
                            'issue': 'Group writable file',
                            'severity': 'medium',
                            'description': 'File is writable by group members'
                        })
                except Exception:
                    continue
        
        return {
            'total_issues': len(issues),
            'issues': issues
        }
    
    def generate_recommendations(self) -> List[Dict[str, str]]:
        """Генерация рекомендаций по безопасности"""
        recommendations = []
        
        # Рекомендации на основе анализа
        recommendations.extend([
            {
                'priority': 'high',
                'category': 'authentication',
                'title': 'Implement session management',
                'description': 'Add JWT tokens or session management for better security'
            },
            {
                'priority': 'high',
                'category': 'validation',
                'title': 'Increase input validation coverage',
                'description': 'Add validation to all endpoints that process user input'
            },
            {
                'priority': 'medium',
                'category': 'logging',
                'title': 'Implement structured logging',
                'description': 'Use structured logging to avoid sensitive data exposure'
            },
            {
                'priority': 'medium',
                'category': 'crypto',
                'title': 'Add encryption for sensitive data',
                'description': 'Encrypt sensitive data at rest and in transit'
            },
            {
                'priority': 'low',
                'category': 'monitoring',
                'title': 'Implement security monitoring',
                'description': 'Add real-time monitoring for security events'
            }
        ])
        
        return recommendations
    
    def run_analysis(self):
        """Запуск полного анализа безопасности"""
        print("🔍 Запуск расширенного анализа безопасности...")
        print("=" * 60)
        
        # Выполняем все анализы
        analyses = {
            'code_quality': self.analyze_code_quality(),
            'dependencies': self.analyze_dependencies(),
            'authentication': self.analyze_authentication_flow(),
            'data_validation': self.analyze_data_validation(),
            'error_handling': self.analyze_error_handling(),
            'logging_security': self.analyze_logging_security(),
            'crypto_usage': self.analyze_crypto_usage(),
            'file_permissions': self.analyze_file_permissions()
        }
        
        # Собираем все находки
        for analysis_name, analysis_result in analyses.items():
            if 'issues' in analysis_result:
                for issue in analysis_result['issues']:
                    severity = issue.get('severity', 'info')
                    self.results['findings'][severity].append({
                        'analysis': analysis_name,
                        **issue
                    })
        
        # Добавляем метрики
        self.results['metrics'] = {
            'total_analyses': len(analyses),
            'findings_by_severity': {
                severity: len(findings) 
                for severity, findings in self.results['findings'].items()
            }
        }
        
        # Генерируем рекомендации
        self.results['recommendations'] = self.generate_recommendations()
        
        # Выводим результаты
        self.print_results()
        self.save_report()
    
    def print_results(self):
        """Вывод результатов анализа"""
        print("\n📊 РЕЗУЛЬТАТЫ РАСШИРЕННОГО АНАЛИЗА")
        print("=" * 60)
        
        findings = self.results['findings']
        
        for severity in ['critical', 'high', 'medium', 'low', 'info']:
            count = len(findings[severity])
            if count > 0:
                emoji = {'critical': '🚨', 'high': '🔴', 'medium': '🟡', 'low': '🟢', 'info': 'ℹ️'}[severity]
                print(f"{emoji} {severity.upper()}: {count} находок")
                
                for finding in findings[severity][:5]:  # Показываем первые 5
                    print(f"   • {finding.get('issue', 'Unknown issue')}")
                    if finding.get('file'):
                        print(f"     Файл: {finding['file']}")
                    if finding.get('description'):
                        print(f"     Описание: {finding['description']}")
                    print()
        
        # Показываем рекомендации
        print("\n💡 РЕКОМЕНДАЦИИ")
        print("=" * 60)
        for rec in self.results['recommendations'][:10]:
            priority_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}[rec['priority']]
            print(f"{priority_emoji} {rec['title']}")
            print(f"   Категория: {rec['category']}")
            print(f"   Описание: {rec['description']}")
            print()
    
    def save_report(self):
        """Сохранение отчета"""
        report_file = self.project_root / 'advanced_security_report.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        print(f"📄 Расширенный отчет сохранен в: {report_file}")


def main():
    """Основная функция"""
    analyzer = AdvancedSecurityAnalyzer()
    analyzer.run_analysis()


if __name__ == "__main__":
    main()
