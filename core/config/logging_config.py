"""Logging configuration for the application."""
import os
import logging
import logging.handlers
from pathlib import Path
from typing import Dict, Any

# Create logs directory if it doesn't exist
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

# Log file paths
APP_LOG_FILE = LOGS_DIR / "app.log"
ERROR_LOG_FILE = LOGS_DIR / "error.log"
ACCESS_LOG_FILE = LOGS_DIR / "access.log"
PERFORMANCE_LOG_FILE = LOGS_DIR / "performance.log"

# Log format
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Log rotation settings
MAX_BYTES = 10 * 1024 * 1024  # 10MB
BACKUP_COUNT = 5

def get_logging_config() -> Dict[str, Any]:
    """Get logging configuration dictionary."""
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": LOG_FORMAT,
                "datefmt": DATE_FORMAT,
            },
            "json": {
                "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "standard",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "standard",
                "filename": str(APP_LOG_FILE),
                "maxBytes": MAX_BYTES,
                "backupCount": BACKUP_COUNT,
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "standard",
                "filename": str(ERROR_LOG_FILE),
                "maxBytes": MAX_BYTES,
                "backupCount": BACKUP_COUNT,
            },
            "access_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "json",
                "filename": str(ACCESS_LOG_FILE),
                "maxBytes": MAX_BYTES,
                "backupCount": BACKUP_COUNT,
            },
            "performance_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "json",
                "filename": str(PERFORMANCE_LOG_FILE),
                "maxBytes": MAX_BYTES,
                "backupCount": BACKUP_COUNT,
            },
        },
        "loggers": {
            "": {  # Root logger
                "handlers": ["console", "file", "error_file"],
                "level": "INFO",
                "propagate": True,
            },
            "app": {  # Application logger
                "handlers": ["console", "file", "error_file"],
                "level": "INFO",
                "propagate": False,
            },
            "app.access": {  # Access log logger
                "handlers": ["access_file"],
                "level": "INFO",
                "propagate": False,
            },
            "app.performance": {  # Performance log logger
                "handlers": ["performance_file"],
                "level": "INFO",
                "propagate": False,
            },
            "app.error": {  # Error log logger
                "handlers": ["error_file"],
                "level": "ERROR",
                "propagate": False,
            },
        },
    }

def setup_logging() -> None:
    """Set up logging configuration."""
    config = get_logging_config()
    logging.config.dictConfig(config)
    
    # Create log files with proper permissions
    for log_file in [APP_LOG_FILE, ERROR_LOG_FILE, ACCESS_LOG_FILE, PERFORMANCE_LOG_FILE]:
        if not log_file.exists():
            log_file.touch(mode=0o644) 