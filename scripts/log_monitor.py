#!/usr/bin/env python3
"""
Система мониторинга логов Easy Pass Bot
"""
import os
import sys
import json
import time
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import asyncio
import logging

# Добавляем src в путь для импортов
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

class LogMonitor:
    """Монитор логов для системы безопасности"""
    
    def __init__(self, log_dir: str = "logs", alert_threshold: int = 10):
        self.log_dir = Path(log_dir)
        self.alert_threshold = alert_threshold
        self.monitoring = False
        self.alerts = []
        self.stats = {
            'total_events': 0,
            'security_events': 0,
            'error_events': 0,
            'warning_events': 0,
            'last_check': None
        }
        
        # Паттерны для мониторинга
        self.patterns = {
            'security': [
                r'Rate limit exceeded',
                r'Invalid Telegram ID',
                r'Unauthorized access',
                r'Security violation',
                r'Failed authentication',
                r'SQL injection attempt',
                r'XSS attempt',
                r'Path traversal attempt'
            ],
            'errors': [
                r'ERROR',
                r'CRITICAL',
                r'Exception',
                r'Traceback',
                r'Failed to',
                r'Database error'
            ],
            'warnings': [
                r'WARNING',
                r'Deprecated',
                r'Slow query',
                r'Memory usage high'
            ]
        }
        
        # Настройка логирования монитора
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/log_monitor.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def scan_log_files(self) -> Dict[str, Any]:
        """Сканирование лог-файлов на предмет проблем"""
        results = {
            'security_issues': [],
            'errors': [],
            'warnings': [],
            'stats': self.stats.copy()
        }
        
        if not self.log_dir.exists():
            self.logger.warning(f"Log directory {self.log_dir} does not exist")
            return results
        
        # Сканируем все лог-файлы
        log_files = list(self.log_dir.glob("*.log"))
        
        for log_file in log_files:
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # Анализируем последние 1000 строк
                recent_lines = lines[-1000:] if len(lines) > 1000 else lines
                
                for line_num, line in enumerate(recent_lines, 1):
                    timestamp = self._extract_timestamp(line)
                    if not timestamp:
                        continue
                    
                    # Проверяем на проблемы безопасности
                    for pattern in self.patterns['security']:
                        if re.search(pattern, line, re.IGNORECASE):
                            results['security_issues'].append({
                                'file': log_file.name,
                                'line': line_num,
                                'timestamp': timestamp,
                                'message': line.strip(),
                                'pattern': pattern
                            })
                            self.stats['security_events'] += 1
                    
                    # Проверяем на ошибки
                    for pattern in self.patterns['errors']:
                        if re.search(pattern, line, re.IGNORECASE):
                            results['errors'].append({
                                'file': log_file.name,
                                'line': line_num,
                                'timestamp': timestamp,
                                'message': line.strip(),
                                'pattern': pattern
                            })
                            self.stats['error_events'] += 1
                    
                    # Проверяем на предупреждения
                    for pattern in self.patterns['warnings']:
                        if re.search(pattern, line, re.IGNORECASE):
                            results['warnings'].append({
                                'file': log_file.name,
                                'line': line_num,
                                'timestamp': timestamp,
                                'message': line.strip(),
                                'pattern': pattern
                            })
                            self.stats['warning_events'] += 1
                    
                    self.stats['total_events'] += 1
                
            except Exception as e:
                self.logger.error(f"Error reading log file {log_file}: {e}")
        
        self.stats['last_check'] = datetime.now().isoformat()
        results['stats'] = self.stats.copy()
        
        return results
    
    def _extract_timestamp(self, line: str) -> Optional[str]:
        """Извлечение временной метки из строки лога"""
        # Паттерны для различных форматов временных меток
        patterns = [
            r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})',
            r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})',
            r'(\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                return match.group(1)
        
        return None
    
    def check_security_alerts(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Проверка на критические проблемы безопасности"""
        alerts = []
        
        # Проверяем количество событий безопасности
        security_count = len(results['security_issues'])
        if security_count > self.alert_threshold:
            alerts.append({
                'type': 'high_security_activity',
                'severity': 'high',
                'message': f'High security activity detected: {security_count} events',
                'count': security_count,
                'threshold': self.alert_threshold
            })
        
        # Проверяем на подозрительные паттерны
        suspicious_patterns = [
            'SQL injection attempt',
            'XSS attempt',
            'Path traversal attempt',
            'Unauthorized access'
        ]
        
        for issue in results['security_issues']:
            for pattern in suspicious_patterns:
                if pattern.lower() in issue['message'].lower():
                    alerts.append({
                        'type': 'suspicious_activity',
                        'severity': 'critical',
                        'message': f'Suspicious activity detected: {pattern}',
                        'file': issue['file'],
                        'line': issue['line'],
                        'timestamp': issue['timestamp']
                    })
        
        # Проверяем на множественные ошибки
        error_count = len(results['errors'])
        if error_count > 50:  # Более 50 ошибок за последний период
            alerts.append({
                'type': 'high_error_rate',
                'severity': 'medium',
                'message': f'High error rate detected: {error_count} errors',
                'count': error_count
            })
        
        return alerts
    
    def generate_report(self, results: Dict[str, Any], alerts: List[Dict[str, Any]]) -> str:
        """Генерация отчета о мониторинге"""
        report = f"""
🔍 ОТЧЕТ МОНИТОРИНГА ЛОГОВ
{'=' * 50}
Время проверки: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 СТАТИСТИКА:
• Всего событий: {results['stats']['total_events']}
• События безопасности: {results['stats']['security_events']}
• Ошибки: {results['stats']['error_events']}
• Предупреждения: {results['stats']['warning_events']}

🚨 АЛЕРТЫ ({len(alerts)}):
"""
        
        if alerts:
            for i, alert in enumerate(alerts, 1):
                severity_emoji = {
                    'critical': '🔴',
                    'high': '🟠',
                    'medium': '🟡',
                    'low': '🟢'
                }.get(alert['severity'], '⚪')
                
                report += f"{i}. {severity_emoji} {alert['message']}\n"
                if 'file' in alert:
                    report += f"   Файл: {alert['file']}:{alert.get('line', 'N/A')}\n"
                if 'timestamp' in alert:
                    report += f"   Время: {alert['timestamp']}\n"
                report += "\n"
        else:
            report += "✅ Критических проблем не обнаружено\n"
        
        # Топ проблем безопасности
        if results['security_issues']:
            report += "\n🔒 ТОП ПРОБЛЕМ БЕЗОПАСНОСТИ:\n"
            security_issues = results['security_issues'][-10:]  # Последние 10
            for issue in security_issues:
                report += f"• {issue['timestamp']} - {issue['message'][:100]}...\n"
        
        return report
    
    def save_alerts(self, alerts: List[Dict[str, Any]]):
        """Сохранение алертов в файл"""
        if not alerts:
            return
        
        alert_file = self.log_dir / 'security_alerts.json'
        alert_data = {
            'timestamp': datetime.now().isoformat(),
            'alerts': alerts
        }
        
        # Читаем существующие алерты
        existing_alerts = []
        if alert_file.exists():
            try:
                with open(alert_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    existing_alerts = existing_data.get('alerts', [])
            except Exception as e:
                self.logger.error(f"Error reading existing alerts: {e}")
        
        # Добавляем новые алерты
        all_alerts = existing_alerts + alerts
        
        # Сохраняем только последние 100 алертов
        all_alerts = all_alerts[-100:]
        
        with open(alert_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'alerts': all_alerts
            }, f, ensure_ascii=False, indent=2)
    
    async def start_monitoring(self, interval: int = 300):
        """Запуск непрерывного мониторинга"""
        self.monitoring = True
        self.logger.info(f"Starting log monitoring with {interval}s interval")
        
        while self.monitoring:
            try:
                # Сканируем логи
                results = self.scan_log_files()
                
                # Проверяем на алерты
                alerts = self.check_security_alerts(results)
                
                # Сохраняем алерты
                if alerts:
                    self.save_alerts(alerts)
                    self.logger.warning(f"Generated {len(alerts)} security alerts")
                
                # Генерируем отчет
                report = self.generate_report(results, alerts)
                
                # Сохраняем отчет
                report_file = self.log_dir / f'monitoring_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
                with open(report_file, 'w', encoding='utf-8') as f:
                    f.write(report)
                
                self.logger.info(f"Monitoring cycle completed. Events: {results['stats']['total_events']}")
                
                # Ждем следующий цикл
                await asyncio.sleep(interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring cycle: {e}")
                await asyncio.sleep(60)  # Короткая пауза при ошибке
    
    def stop_monitoring(self):
        """Остановка мониторинга"""
        self.monitoring = False
        self.logger.info("Log monitoring stopped")
    
    def run_single_check(self):
        """Выполнение однократной проверки"""
        print("🔍 Выполнение проверки логов...")
        
        results = self.scan_log_files()
        alerts = self.check_security_alerts(results)
        
        if alerts:
            self.save_alerts(alerts)
            print(f"⚠️  Обнаружено {len(alerts)} алертов безопасности!")
        else:
            print("✅ Критических проблем не обнаружено")
        
        report = self.generate_report(results, alerts)
        print(report)
        
        return results, alerts


def main():
    """Основная функция"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Log Monitor for Easy Pass Bot')
    parser.add_argument('--log-dir', default='logs', help='Log directory path')
    parser.add_argument('--interval', type=int, default=300, help='Monitoring interval in seconds')
    parser.add_argument('--threshold', type=int, default=10, help='Alert threshold for security events')
    parser.add_argument('--once', action='store_true', help='Run single check instead of continuous monitoring')
    
    args = parser.parse_args()
    
    monitor = LogMonitor(log_dir=args.log_dir, alert_threshold=args.threshold)
    
    if args.once:
        monitor.run_single_check()
    else:
        try:
            asyncio.run(monitor.start_monitoring(args.interval))
        except KeyboardInterrupt:
            monitor.stop_monitoring()
            print("\n🛑 Мониторинг остановлен")


if __name__ == "__main__":
    main()

