"""
Система проверки здоровья приложения
"""
import time
import psutil
import aiosqlite
import logging
from typing import Dict, Any
from pathlib import Path
from datetime import datetime
logger = logging.getLogger(__name__)

class HealthChecker:
    """Проверка здоровья системы"""
    def __init__(self, db_path: str, log_dir: str = "logs"):
        """
        Инициализация проверяющего здоровья
        Args:
            db_path: Путь к базе данных
            log_dir: Директория для логов
        """
        self.db_path = db_path
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        # Пороговые значения для предупреждений
        self.thresholds = {
            'memory_usage_percent': 80,
            'disk_usage_percent': 90,
            'cpu_usage_percent': 90,
            'db_response_time_ms': 1000,
            'log_file_size_mb': 100
        }
    async def check_database(self) -> Dict[str, Any]:
        """
        Проверка состояния базы данных
        Returns:
            Словарь с результатами проверки
        """
        start_time = time.time()
        try:
            # Проверяем подключение к базе данных
            async with aiosqlite.connect(self.db_path) as db:
                # Простой запрос для проверки
                async with db.execute("SELECT 1") as cursor:
                    await cursor.fetchone()
                # Проверяем размер базы данных
                db_size = Path(self.db_path).stat().st_size
                # Проверяем количество записей в основных таблицах
                async with db.execute("SELECT COUNT(*) FROM users") as cursor:
                    users_count = (await cursor.fetchone())[0]
                async with db.execute("SELECT COUNT(*) FROM passes") as cursor:
                    passes_count = (await cursor.fetchone())[0]
                response_time = (time.time() - start_time) * 1000  # в миллисекундах
                status = "healthy"
                if response_time > self.thresholds['db_response_time_ms']:
                    status = "warning"
                return {
                    "status": status,
                    "response_time_ms": round(response_time, 2),
                    "db_size_bytes": db_size,
                    "db_size_mb": round(db_size / 1024 / 1024, 2),
                    "users_count": users_count,
                    "passes_count": passes_count,
                    "message": f"Database responding in {response_time:.2f}ms"
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "response_time_ms": (time.time() - start_time) * 1000,
                "message": f"Database error: {e}"
            }
    def check_memory(self) -> Dict[str, Any]:
        """
        Проверка использования памяти
        Returns:
            Словарь с результатами проверки
        """
        try:
            memory = psutil.virtual_memory()
            status = "healthy"
            if memory.percent > self.thresholds['memory_usage_percent']:
                status = "warning"
            if memory.percent > 95:
                status = "critical"
            return {
                "status": status,
                "usage_percent": memory.percent,
                "available_mb": round(memory.available / 1024 / 1024, 2),
                "total_mb": round(memory.total / 1024 / 1024, 2),
                "used_mb": round(memory.used / 1024 / 1024, 2),
                "message": f"Memory usage: {memory.percent:.1f}%"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": f"Memory check failed: {e}"
            }
    def check_disk(self) -> Dict[str, Any]:
        """
        Проверка использования диска
        Returns:
            Словарь с результатами проверки
        """
        try:
            disk = psutil.disk_usage('/')
            status = "healthy"
            if disk.percent > self.thresholds['disk_usage_percent']:
                status = "warning"
            if disk.percent > 95:
                status = "critical"
            return {
                "status": status,
                "usage_percent": disk.percent,
                "free_gb": round(disk.free / 1024 / 1024 / 1024, 2),
                "total_gb": round(disk.total / 1024 / 1024 / 1024, 2),
                "used_gb": round(disk.used / 1024 / 1024 / 1024, 2),
                "message": f"Disk usage: {disk.percent:.1f}%"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": f"Disk check failed: {e}"
            }
    def check_cpu(self) -> Dict[str, Any]:
        """
        Проверка использования CPU
        Returns:
            Словарь с результатами проверки
        """
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            status = "healthy"
            if cpu_percent > self.thresholds['cpu_usage_percent']:
                status = "warning"
            if cpu_percent > 95:
                status = "critical"
            return {
                "status": status,
                "usage_percent": cpu_percent,
                "cpu_count": psutil.cpu_count(),
                "message": f"CPU usage: {cpu_percent:.1f}%"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": f"CPU check failed: {e}"
            }
    def check_log_files(self) -> Dict[str, Any]:
        """
        Проверка размера лог-файлов
        Returns:
            Словарь с результатами проверки
        """
        try:
            log_files = list(self.log_dir.glob("*.log"))
            total_size = 0
            large_files = []
            for log_file in log_files:
                size_mb = log_file.stat().st_size / 1024 / 1024
                total_size += size_mb
                if size_mb > self.thresholds['log_file_size_mb']:
                    large_files.append({
                        'file': log_file.name,
                        'size_mb': round(size_mb, 2)
                    })
            status = "healthy"
            if large_files:
                status = "warning"
            return {
                "status": status,
                "total_size_mb": round(total_size, 2),
                "files_count": len(log_files),
                "large_files": large_files,
                "message": f"Total log size: {total_size:.2f}MB"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": f"Log files check failed: {e}"
            }
    def check_process(self) -> Dict[str, Any]:
        """
        Проверка состояния процесса бота
        Returns:
            Словарь с результатами проверки
        """
        try:
            process = psutil.Process()
            return {
                "status": "healthy",
                "pid": process.pid,
                "memory_mb": round(process.memory_info().rss / 1024 / 1024, 2),
                "cpu_percent": process.cpu_percent(),
                "create_time": datetime.fromtimestamp(process.create_time()).isoformat(),
                "message": f"Process running (PID: {process.pid})"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": f"Process check failed: {e}"
            }
    async def get_health_status(self) -> Dict[str, Any]:
        """
        Получение общего статуса здоровья системы
        Returns:
            Словарь с общим статусом и результатами всех проверок
        """
        checks = {
            "database": await self.check_database(),
            "memory": self.check_memory(),
            "disk": self.check_disk(),
            "cpu": self.check_cpu(),
            "log_files": self.check_log_files(),
            "process": self.check_process()
        }
        # Определяем общий статус
        statuses = [check["status"] for check in checks.values()]
        if "critical" in statuses or "unhealthy" in statuses:
            overall_status = "critical"
        elif "warning" in statuses:
            overall_status = "warning"
        elif "error" in statuses:
            overall_status = "error"
        else:
            overall_status = "healthy"
        # Подсчитываем количество проверок по статусам
        status_counts = {}
        for status in statuses:
            status_counts[status] = status_counts.get(status, 0) + 1
        return {
            "overall_status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": checks,
            "status_summary": status_counts,
            "uptime_seconds": time.time() - psutil.Process().create_time()
        }
    def get_health_summary(self) -> str:
        """
        Получение краткой сводки о здоровье системы
        Returns:
            Текстовая сводка
        """
        try:
            memory = self.check_memory()
            disk = self.check_disk()
            cpu = self.check_cpu()
            summary = f"System Health Summary:\n"
            summary += f"Memory: {memory['usage_percent']:.1f}% ({memory['status']})\n"
            summary += f"Disk: {disk['usage_percent']:.1f}% ({disk['status']})\n"
            summary += f"CPU: {cpu['usage_percent']:.1f}% ({cpu['status']})\n"
            return summary
        except Exception as e:
            return f"Health check failed: {e}"
# Глобальный экземпляр проверяющего здоровья
health_checker = HealthChecker("database/easy_pass.db")
