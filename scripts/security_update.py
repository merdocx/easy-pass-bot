#!/usr/bin/env python3
"""
Автоматическое обновление безопасности Easy Pass Bot
"""
import os
import sys
import subprocess
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

class SecurityUpdater:
    """Автоматическое обновление компонентов безопасности"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.venv_path = self.project_root / 'venv'
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'updates': [],
            'errors': [],
            'vulnerabilities_found': 0,
            'vulnerabilities_fixed': 0
        }
    
    def run_safety_check(self) -> Dict[str, Any]:
        """Запуск проверки безопасности зависимостей"""
        print("🔍 Проверка уязвимостей зависимостей...")
        
        try:
            # Активируем виртуальное окружение и запускаем safety
            cmd = [
                'bash', '-c',
                f'source {self.venv_path}/bin/activate && safety check --json'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                print("✅ Уязвимости не найдены")
                return {'vulnerabilities': [], 'status': 'clean'}
            else:
                try:
                    # Парсим JSON вывод
                    safety_data = json.loads(result.stdout)
                    vulnerabilities = safety_data.get('vulnerabilities', [])
                    
                    print(f"⚠️  Найдено {len(vulnerabilities)} уязвимостей")
                    return {
                        'vulnerabilities': vulnerabilities,
                        'status': 'vulnerabilities_found'
                    }
                except json.JSONDecodeError:
                    # Если JSON не парсится, анализируем текстовый вывод
                    vulnerabilities = []
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if 'Vulnerability found' in line:
                            vulnerabilities.append({'raw_line': line})
                    
                    return {
                        'vulnerabilities': vulnerabilities,
                        'status': 'vulnerabilities_found'
                    }
                    
        except Exception as e:
            error_msg = f"Ошибка при проверке безопасности: {e}"
            print(f"❌ {error_msg}")
            self.results['errors'].append(error_msg)
            return {'vulnerabilities': [], 'status': 'error'}
    
    def update_packages(self, vulnerabilities: List[Dict[str, Any]]) -> List[str]:
        """Обновление пакетов с уязвимостями"""
        updates = []
        
        if not vulnerabilities:
            return updates
        
        print("🔧 Обновление пакетов...")
        
        # Список пакетов для обновления
        packages_to_update = []
        
        for vuln in vulnerabilities:
            if 'package' in vuln:
                package = vuln['package']
                if package not in packages_to_update:
                    packages_to_update.append(package)
            elif 'raw_line' in vuln:
                # Парсим из текстового вывода
                line = vuln['raw_line']
                if 'in' in line and 'version' in line:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == 'in' and i + 1 < len(parts):
                            package = parts[i + 1]
                            if package not in packages_to_update:
                                packages_to_update.append(package)
                            break
        
        # Обновляем пакеты
        for package in packages_to_update:
            try:
                print(f"   Обновление {package}...")
                
                cmd = [
                    'bash', '-c',
                    f'source {self.venv_path}/bin/activate && pip install --upgrade {package}'
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
                
                if result.returncode == 0:
                    updates.append(f"✅ {package} обновлен успешно")
                    print(f"   ✅ {package} обновлен")
                else:
                    error_msg = f"❌ Ошибка обновления {package}: {result.stderr}"
                    updates.append(error_msg)
                    print(f"   {error_msg}")
                    self.results['errors'].append(error_msg)
                    
            except Exception as e:
                error_msg = f"❌ Исключение при обновлении {package}: {e}"
                updates.append(error_msg)
                print(f"   {error_msg}")
                self.results['errors'].append(error_msg)
        
        return updates
    
    def update_requirements(self):
        """Обновление файла requirements.txt"""
        print("📝 Обновление requirements.txt...")
        
        try:
            cmd = [
                'bash', '-c',
                f'source {self.venv_path}/bin/activate && pip freeze > requirements.txt'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                print("✅ requirements.txt обновлен")
                self.results['updates'].append("requirements.txt обновлен")
            else:
                error_msg = f"❌ Ошибка обновления requirements.txt: {result.stderr}"
                print(error_msg)
                self.results['errors'].append(error_msg)
                
        except Exception as e:
            error_msg = f"❌ Исключение при обновлении requirements.txt: {e}"
            print(error_msg)
            self.results['errors'].append(error_msg)
    
    def run_security_tests(self):
        """Запуск тестов безопасности"""
        print("🧪 Запуск тестов безопасности...")
        
        try:
            cmd = [
                'bash', '-c',
                f'source {self.venv_path}/bin/activate && python -m pytest tests/unit/security/ -v'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                print("✅ Тесты безопасности прошли успешно")
                self.results['updates'].append("Тесты безопасности пройдены")
            else:
                print(f"⚠️  Некоторые тесты не прошли: {result.stdout}")
                self.results['updates'].append("Тесты безопасности: частично пройдены")
                
        except Exception as e:
            error_msg = f"❌ Ошибка запуска тестов: {e}"
            print(error_msg)
            self.results['errors'].append(error_msg)
    
    def generate_security_report(self):
        """Генерация отчета о безопасности"""
        print("📊 Генерация отчета о безопасности...")
        
        # Запускаем полную проверку безопасности
        cmd = [
            'bash', '-c',
            f'source {self.venv_path}/bin/activate && python scripts/security_check.py'
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                print("✅ Отчет о безопасности сгенерирован")
                self.results['updates'].append("Отчет о безопасности сгенерирован")
            else:
                print(f"⚠️  Ошибка генерации отчета: {result.stderr}")
                
        except Exception as e:
            error_msg = f"❌ Ошибка генерации отчета: {e}"
            print(error_msg)
            self.results['errors'].append(error_msg)
    
    def run_full_update(self):
        """Запуск полного обновления безопасности"""
        print("🛡️  ЗАПУСК ПОЛНОГО ОБНОВЛЕНИЯ БЕЗОПАСНОСТИ")
        print("=" * 60)
        
        # 1. Проверка уязвимостей
        safety_result = self.run_safety_check()
        vulnerabilities = safety_result.get('vulnerabilities', [])
        self.results['vulnerabilities_found'] = len(vulnerabilities)
        
        # 2. Обновление пакетов
        if vulnerabilities:
            updates = self.update_packages(vulnerabilities)
            self.results['updates'].extend(updates)
            self.results['vulnerabilities_fixed'] = len([u for u in updates if u.startswith('✅')])
        
        # 3. Обновление requirements.txt
        self.update_requirements()
        
        # 4. Запуск тестов
        self.run_security_tests()
        
        # 5. Генерация отчета
        self.generate_security_report()
        
        # 6. Сохранение результатов
        self.save_results()
        
        # 7. Вывод итогов
        self.print_summary()
    
    def save_results(self):
        """Сохранение результатов обновления"""
        report_file = self.project_root / 'security_update_report.json'
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        print(f"📄 Отчет обновления сохранен в: {report_file}")
    
    def print_summary(self):
        """Вывод итоговой сводки"""
        print("\n📊 ИТОГОВАЯ СВОДКА ОБНОВЛЕНИЯ")
        print("=" * 60)
        
        print(f"🔍 Найдено уязвимостей: {self.results['vulnerabilities_found']}")
        print(f"🔧 Исправлено уязвимостей: {self.results['vulnerabilities_fixed']}")
        print(f"✅ Успешных обновлений: {len([u for u in self.results['updates'] if u.startswith('✅')])}")
        print(f"❌ Ошибок: {len(self.results['errors'])}")
        
        if self.results['errors']:
            print("\n🚨 ОШИБКИ:")
            for error in self.results['errors']:
                print(f"   {error}")
        
        if self.results['updates']:
            print("\n✅ ОБНОВЛЕНИЯ:")
            for update in self.results['updates']:
                print(f"   {update}")


def main():
    """Основная функция"""
    updater = SecurityUpdater()
    updater.run_full_update()


if __name__ == "__main__":
    main()
