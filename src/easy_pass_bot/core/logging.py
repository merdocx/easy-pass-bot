"""
Centralized logging system for Easy Pass Bot
"""
import logging
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import traceback

from .settings import settings


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process_id": record.process,
            "thread_id": record.thread,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields
        if hasattr(record, 'user_id'):
            log_entry["user_id"] = record.user_id
        if hasattr(record, 'action'):
            log_entry["action"] = record.action
        if hasattr(record, 'duration'):
            log_entry["duration"] = record.duration
        if hasattr(record, 'status_code'):
            log_entry["status_code"] = record.status_code
        if hasattr(record, 'request_id'):
            log_entry["request_id"] = record.request_id
        
        return json.dumps(log_entry, ensure_ascii=False, default=str)


class TextFormatter(logging.Formatter):
    """Custom text formatter for human-readable logs"""
    
    def __init__(self):
        super().__init__(
            fmt='%(asctime)s | %(levelname)-8s | %(name)-20s | %(funcName)-15s:%(lineno)-4d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as text with extra context"""
        # Add extra context to message
        extra_parts = []
        if hasattr(record, 'user_id'):
            extra_parts.append(f"user_id={record.user_id}")
        if hasattr(record, 'action'):
            extra_parts.append(f"action={record.action}")
        if hasattr(record, 'duration'):
            extra_parts.append(f"duration={record.duration:.3f}s")
        if hasattr(record, 'status_code'):
            extra_parts.append(f"status={record.status_code}")
        
        if extra_parts:
            record.msg = f"{record.msg} | {' | '.join(extra_parts)}"
        
        return super().format(record)


class BotLogger:
    """Centralized logger for Easy Pass Bot"""
    
    def __init__(self):
        self._loggers: Dict[str, logging.Logger] = {}
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging configuration"""
        # Create logs directory
        log_file = Path(settings.log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Choose formatter
        if settings.log_format == "json":
            formatter = JSONFormatter()
        else:
            formatter = TextFormatter()
        
        # Setup root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, settings.log_level))
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, settings.log_level))
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        
        # File handler with rotation
        if settings.log_rotation == "daily":
            file_handler = TimedRotatingFileHandler(
                log_file,
                when='midnight',
                interval=1,
                backupCount=settings.log_retention_days,
                encoding='utf-8'
            )
        elif settings.log_rotation == "weekly":
            file_handler = TimedRotatingFileHandler(
                log_file,
                when='W0',
                interval=1,
                backupCount=settings.log_retention_days,
                encoding='utf-8'
            )
        elif settings.log_rotation == "monthly":
            file_handler = TimedRotatingFileHandler(
                log_file,
                when='M0',
                interval=1,
                backupCount=settings.log_retention_days,
                encoding='utf-8'
            )
        else:  # size-based rotation
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=settings.log_retention_days,
                encoding='utf-8'
            )
        
        file_handler.setLevel(getattr(logging, settings.log_level))
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        
        # Security audit logger
        self._setup_security_logger()
        
        # Performance metrics logger
        self._setup_metrics_logger()
    
    def _setup_security_logger(self):
        """Setup security audit logger"""
        security_logger = logging.getLogger('security_audit')
        security_logger.setLevel(logging.INFO)
        
        # Don't propagate to root logger
        security_logger.propagate = False
        
        # Security log file
        security_log_file = Path("logs/security_audit.log")
        security_log_file.parent.mkdir(parents=True, exist_ok=True)
        
        security_handler = TimedRotatingFileHandler(
            security_log_file,
            when='midnight',
            interval=1,
            backupCount=90,  # Keep security logs for 90 days
            encoding='utf-8'
        )
        
        if settings.log_format == "json":
            security_handler.setFormatter(JSONFormatter())
        else:
            security_handler.setFormatter(TextFormatter())
        
        security_logger.addHandler(security_handler)
    
    def _setup_metrics_logger(self):
        """Setup performance metrics logger"""
        metrics_logger = logging.getLogger('metrics')
        metrics_logger.setLevel(logging.INFO)
        
        # Don't propagate to root logger
        metrics_logger.propagate = False
        
        # Metrics log file
        metrics_log_file = Path("logs/metrics.log")
        metrics_log_file.parent.mkdir(parents=True, exist_ok=True)
        
        metrics_handler = TimedRotatingFileHandler(
            metrics_log_file,
            when='midnight',
            interval=1,
            backupCount=30,  # Keep metrics for 30 days
            encoding='utf-8'
        )
        
        if settings.log_format == "json":
            metrics_handler.setFormatter(JSONFormatter())
        else:
            metrics_handler.setFormatter(TextFormatter())
        
        metrics_logger.addHandler(metrics_handler)
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get logger instance"""
        if name not in self._loggers:
            self._loggers[name] = logging.getLogger(name)
        return self._loggers[name]
    
    def get_security_logger(self) -> logging.Logger:
        """Get security audit logger"""
        return logging.getLogger('security_audit')
    
    def get_metrics_logger(self) -> logging.Logger:
        """Get performance metrics logger"""
        return logging.getLogger('metrics')


# Global logger instance
bot_logger = BotLogger()


def get_logger(name: str) -> logging.Logger:
    """Get logger instance"""
    return bot_logger.get_logger(name)


def get_security_logger() -> logging.Logger:
    """Get security audit logger"""
    return bot_logger.get_security_logger()


def get_metrics_logger() -> logging.Logger:
    """Get performance metrics logger"""
    return bot_logger.get_metrics_logger()


# Convenience functions for common logging patterns
def log_user_action(logger: logging.Logger, user_id: int, action: str, **kwargs):
    """Log user action with context"""
    logger.info(f"User action: {action}", extra={
        'user_id': user_id,
        'action': action,
        **kwargs
    })


def log_performance(logger: logging.Logger, operation: str, duration: float, **kwargs):
    """Log performance metrics"""
    logger.info(f"Performance: {operation}", extra={
        'action': 'performance',
        'operation': operation,
        'duration': duration,
        **kwargs
    })


def log_security_event(event_type: str, user_id: Optional[int] = None, **kwargs):
    """Log security event"""
    security_logger = get_security_logger()
    security_logger.warning(f"Security event: {event_type}", extra={
        'action': 'security_event',
        'event_type': event_type,
        'user_id': user_id,
        **kwargs
    })


def log_error(logger: logging.Logger, error: Exception, context: Optional[Dict[str, Any]] = None):
    """Log error with context"""
    logger.error(f"Error: {str(error)}", extra={
        'action': 'error',
        'error_type': type(error).__name__,
        'error_message': str(error),
        **(context or {})
    }, exc_info=True)
