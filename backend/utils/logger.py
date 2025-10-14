#!/usr/bin/env python3
"""
Comprehensive logging utility for Mini-Competition backend
Provides structured logging with request correlation and proper formatting
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from typing import Optional, Dict, Any
import json
import traceback
from functools import wraps
import uuid


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output"""

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",  # Reset
    }

    def format(self, record):
        if hasattr(record, "color") and record.color:
            color = self.COLORS.get(record.levelname, "")
            reset = self.COLORS["RESET"]
            record.levelname = f"{color}{record.levelname}{reset}"
        return super().format(record)


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging"""

    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add request correlation ID if available
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id

        # Add user ID if available
        if hasattr(record, "user_id"):
            log_entry["user_id"] = record.user_id

        # Add custom fields
        if hasattr(record, "custom_fields"):
            log_entry.update(record.custom_fields)

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info),
            }

        return json.dumps(log_entry, ensure_ascii=False)


class RequestLogger:
    """Logger that can be used within request context"""

    def __init__(self, logger_name: str, request_id: str = None, user_id: str = None):
        self.logger = logging.getLogger(logger_name)
        self.request_id = request_id or str(uuid.uuid4())
        self.user_id = user_id

    def _log(self, level: str, message: str, **kwargs):
        """Internal logging method with request context"""
        extra = {"request_id": self.request_id, "user_id": self.user_id, **kwargs}
        getattr(self.logger, level.lower())(message, extra=extra)

    def debug(self, message: str, **kwargs):
        self._log("DEBUG", message, **kwargs)

    def info(self, message: str, **kwargs):
        self._log("INFO", message, **kwargs)

    def warning(self, message: str, **kwargs):
        self._log("WARNING", message, **kwargs)

    def error(self, message: str, **kwargs):
        self._log("ERROR", message, **kwargs)

    def critical(self, message: str, **kwargs):
        self._log("CRITICAL", message, **kwargs)


def setup_logging(
    log_level: str = "INFO",
    log_dir: str = "logs",
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    enable_console: bool = True,
    enable_file: bool = True,
    enable_structured: bool = False,
) -> logging.Logger:
    """
    Set up comprehensive logging configuration

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory to store log files
        max_file_size: Maximum size of log files before rotation
        backup_count: Number of backup files to keep
        enable_console: Enable console logging
        enable_file: Enable file logging
        enable_structured: Enable structured JSON logging
    """

    # Create logs directory if it doesn't exist
    if enable_file and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler with colors
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))

        console_formatter = ColoredFormatter(
            "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

    # File handler with rotation
    if enable_file:
        file_handler = logging.handlers.RotatingFileHandler(
            filename=os.path.join(log_dir, "app.log"),
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(getattr(logging, log_level.upper()))

        file_formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)-20s | %(funcName)-15s:%(lineno)-4d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    # Structured logging handler (for production)
    if enable_structured:
        structured_handler = logging.handlers.RotatingFileHandler(
            filename=os.path.join(log_dir, "structured.log"),
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding="utf-8",
        )
        structured_handler.setLevel(getattr(logging, log_level.upper()))
        structured_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(structured_handler)

    # Error-specific handler
    if enable_file:
        error_handler = logging.handlers.RotatingFileHandler(
            filename=os.path.join(log_dir, "error.log"),
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        root_logger.addHandler(error_handler)

    # Configure specific loggers
    logging.getLogger("werkzeug").setLevel(logging.WARNING)  # Reduce Flask logs
    logging.getLogger("urllib3").setLevel(logging.WARNING)  # Reduce HTTP logs

    return root_logger


def log_function_call(func):
    """Decorator to log function calls with parameters and results"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        func_name = f"{func.__module__}.{func.__name__}"

        # Log function entry
        logger.debug(f"Calling {func_name} with args={args}, kwargs={kwargs}")

        try:
            result = func(*args, **kwargs)
            logger.debug(f"{func_name} completed successfully")
            return result
        except Exception as e:
            logger.error(f"{func_name} failed with error: {str(e)}", exc_info=True)
            raise

    return wrapper


def log_database_operation(operation: str, table: str, record_id: str = None):
    """Log database operations for audit purposes"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger("database")
            logger.info(
                f"Database {operation} on {table}",
                extra={
                    "operation": operation,
                    "table": table,
                    "record_id": record_id,
                    "custom_fields": {"db_operation": True},
                },
            )
            return func(*args, **kwargs)

        return wrapper

    return decorator


def log_api_request(method: str, endpoint: str, user_id: str = None):
    """Log API requests for monitoring"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger("api")
            request_id = str(uuid.uuid4())

            logger.info(
                f"API Request: {method} {endpoint}",
                extra={
                    "request_id": request_id,
                    "user_id": user_id,
                    "method": method,
                    "endpoint": endpoint,
                    "custom_fields": {"api_request": True},
                },
            )

            try:
                result = func(*args, **kwargs)
                logger.info(
                    f"API Response: {method} {endpoint} - Success",
                    extra={
                        "request_id": request_id,
                        "user_id": user_id,
                        "status": "success",
                    },
                )
                return result
            except Exception as e:
                logger.error(
                    f"API Error: {method} {endpoint} - {str(e)}",
                    extra={
                        "request_id": request_id,
                        "user_id": user_id,
                        "status": "error",
                        "error": str(e),
                    },
                    exc_info=True,
                )
                raise

        return wrapper

    return decorator


# Global logger instance
logger = setup_logging()


# Simple wrapper functions for backwards compatibility
def log_info(message: str):
    """Log an info message"""
    logger.info(message)


def log_error(message: str):
    """Log an error message"""
    logger.error(message)


def log_warning(message: str):
    """Log a warning message"""
    logger.warning(message)


def log_debug(message: str):
    """Log a debug message"""
    logger.debug(message)


def log_request(method: str, path: str, status_code: int, duration: int = None):
    """Log an HTTP request"""
    message = f"{method} {path} -> {status_code}"
    if duration:
        message += f" ({duration}ms)"
    logger.info(
        message,
        extra={
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration": duration,
        },
    )


def log_submission(user_id: str, problem_id: str, action: str, details: str = ""):
    """Log a submission event"""
    message = f"User {user_id} | Problem {problem_id} | {action}"
    if details:
        message += f" | {details}"
    logger.info(
        message,
        extra={
            "user_id": user_id,
            "problem_id": problem_id,
            "action": action,
            "details": details,
        },
    )


# Export commonly used functions
__all__ = [
    "setup_logging",
    "RequestLogger",
    "log_function_call",
    "log_database_operation",
    "log_api_request",
    "logger",
    "log_info",
    "log_error",
    "log_warning",
    "log_debug",
    "log_request",
    "log_submission",
]
