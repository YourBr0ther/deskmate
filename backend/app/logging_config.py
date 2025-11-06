"""Enhanced logging configuration for DeskMate with structured error monitoring.

Provides:
- Structured logging with correlation IDs
- Error categorization and severity-based routing
- Performance monitoring
- Context-aware logging for better debugging
"""

import logging
import logging.config
import json
import time
from typing import Dict, Any, Optional
from datetime import datetime
import os

from app.exceptions import ErrorCategory, ErrorSeverity


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        # Create base log entry
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add standard fields
        if hasattr(record, "correlation_id"):
            log_entry["correlation_id"] = record.correlation_id

        if hasattr(record, "error_code"):
            log_entry["error_code"] = record.error_code

        if hasattr(record, "category"):
            log_entry["category"] = record.category

        if hasattr(record, "severity"):
            log_entry["severity"] = record.severity

        if hasattr(record, "details"):
            log_entry["details"] = record.details

        # Add context information
        if hasattr(record, "endpoint"):
            log_entry["endpoint"] = record.endpoint

        if hasattr(record, "user_id"):
            log_entry["user_id"] = record.user_id

        if hasattr(record, "operation"):
            log_entry["operation"] = record.operation

        # Add performance metrics
        if hasattr(record, "duration_ms"):
            log_entry["duration_ms"] = record.duration_ms

        # Add exception information
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info) if record.exc_info else None
            }

        return json.dumps(log_entry, ensure_ascii=False)


class PerformanceFilter(logging.Filter):
    """Filter for performance-related log entries."""

    def filter(self, record: logging.LogRecord) -> bool:
        return hasattr(record, "duration_ms") or "performance" in record.getMessage().lower()


class ErrorFilter(logging.Filter):
    """Filter for error-related log entries."""

    def filter(self, record: logging.LogRecord) -> bool:
        return (
            record.levelno >= logging.WARNING or
            hasattr(record, "error_code") or
            hasattr(record, "category")
        )


class SecurityFilter(logging.Filter):
    """Filter for security-related log entries."""

    def filter(self, record: logging.LogRecord) -> bool:
        security_keywords = ["auth", "security", "unauthorized", "forbidden", "token"]
        message = record.getMessage().lower()
        return any(keyword in message for keyword in security_keywords)


def setup_logging(
    log_level: str = "INFO",
    log_format: str = "structured",
    log_file: Optional[str] = None
) -> None:
    """Setup enhanced logging configuration.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Format type ("structured" or "simple")
        log_file: Optional log file path
    """

    # Determine log level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Base configuration
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "structured": {
                "()": StructuredFormatter,
            },
            "simple": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            }
        },
        "filters": {
            "performance": {
                "()": PerformanceFilter,
            },
            "error": {
                "()": ErrorFilter,
            },
            "security": {
                "()": SecurityFilter,
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": numeric_level,
                "formatter": log_format,
                "stream": "ext://sys.stdout"
            },
            "error_console": {
                "class": "logging.StreamHandler",
                "level": "WARNING",
                "formatter": log_format,
                "stream": "ext://sys.stderr",
                "filters": ["error"]
            }
        },
        "loggers": {
            # DeskMate application loggers
            "app": {
                "level": numeric_level,
                "handlers": ["console"],
                "propagate": False
            },
            "app.exceptions": {
                "level": "DEBUG",
                "handlers": ["console", "error_console"],
                "propagate": False
            },
            "app.performance": {
                "level": "INFO",
                "handlers": ["console"],
                "filters": ["performance"],
                "propagate": False
            },
            "app.security": {
                "level": "INFO",
                "handlers": ["console"],
                "filters": ["security"],
                "propagate": False
            },
            # External library loggers
            "sqlalchemy.engine": {
                "level": "WARNING",  # Reduce SQL query noise
                "handlers": ["console"],
                "propagate": False
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "fastapi": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            }
        },
        "root": {
            "level": numeric_level,
            "handlers": ["console"]
        }
    }

    # Add file logging if specified
    if log_file:
        config["handlers"]["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": numeric_level,
            "formatter": log_format,
            "filename": log_file,
            "maxBytes": 10 * 1024 * 1024,  # 10 MB
            "backupCount": 5,
            "encoding": "utf-8"
        }

        config["handlers"]["error_file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "WARNING",
            "formatter": log_format,
            "filename": log_file.replace(".log", "_errors.log"),
            "maxBytes": 10 * 1024 * 1024,  # 10 MB
            "backupCount": 10,
            "encoding": "utf-8",
            "filters": ["error"]
        }

        # Add file handlers to all loggers
        for logger_name in config["loggers"]:
            config["loggers"][logger_name]["handlers"].extend(["file"])
            if logger_name in ["app.exceptions", "app.security"]:
                config["loggers"][logger_name]["handlers"].append("error_file")

    # Apply configuration
    logging.config.dictConfig(config)


class PerformanceLogger:
    """Context manager for performance logging."""

    def __init__(self, operation: str, logger: Optional[logging.Logger] = None, **context):
        self.operation = operation
        self.logger = logger or logging.getLogger("app.performance")
        self.context = context
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration_ms = (time.time() - self.start_time) * 1000

            extra = {
                "operation": self.operation,
                "duration_ms": round(duration_ms, 2),
                **self.context
            }

            if exc_type:
                extra["exception_type"] = exc_type.__name__
                self.logger.warning(
                    f"Operation '{self.operation}' failed after {duration_ms:.2f}ms",
                    extra=extra
                )
            elif duration_ms > 1000:  # Slow operation threshold
                self.logger.warning(
                    f"Slow operation '{self.operation}' completed in {duration_ms:.2f}ms",
                    extra=extra
                )
            else:
                self.logger.info(
                    f"Operation '{self.operation}' completed in {duration_ms:.2f}ms",
                    extra=extra
                )


class ErrorMetrics:
    """Simple in-memory error metrics collector."""

    def __init__(self):
        self.error_counts: Dict[str, int] = {}
        self.error_rates: Dict[str, float] = {}
        self.last_reset = time.time()
        self.reset_interval = 300  # 5 minutes

    def record_error(self, category: ErrorCategory, severity: ErrorSeverity):
        """Record an error occurrence."""
        key = f"{category.value}_{severity.value}"
        self.error_counts[key] = self.error_counts.get(key, 0) + 1

        # Reset counters periodically
        if time.time() - self.last_reset > self.reset_interval:
            self._calculate_rates()
            self.error_counts.clear()
            self.last_reset = time.time()

    def _calculate_rates(self):
        """Calculate error rates."""
        total_errors = sum(self.error_counts.values())
        for key, count in self.error_counts.items():
            self.error_rates[key] = count / total_errors if total_errors > 0 else 0.0

    def get_metrics(self) -> Dict[str, Any]:
        """Get current error metrics."""
        return {
            "error_counts": self.error_counts.copy(),
            "error_rates": self.error_rates.copy(),
            "last_reset": self.last_reset,
            "reset_interval": self.reset_interval
        }


# Global instances
error_metrics = ErrorMetrics()


def log_error_metrics(category: ErrorCategory, severity: ErrorSeverity):
    """Log error metrics."""
    error_metrics.record_error(category, severity)


def get_error_metrics() -> Dict[str, Any]:
    """Get current error metrics."""
    return error_metrics.get_metrics()


# Initialize logging configuration
def init_logging():
    """Initialize logging configuration based on environment."""
    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_format = "structured" if os.getenv("ENVIRONMENT") == "production" else "simple"
    log_file = os.getenv("LOG_FILE")

    setup_logging(log_level, log_format, log_file)

    logger = logging.getLogger("app.logging")
    logger.info("Logging system initialized", extra={
        "log_level": log_level,
        "log_format": log_format,
        "log_file": log_file
    })