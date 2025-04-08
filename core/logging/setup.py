import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional

from core.config import get_settings
from core.logging.formatter import CustomFormatter
from core.logging.handlers import TelegramHandler

settings = get_settings()

def setup_logging(
    log_dir: Optional[str] = None,
    max_size: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5
) -> None:
    """Configures the logging system.
    
    Args:
        log_dir: Directory to store log files. If None, logs only to stdout.
        max_size: Maximum size of each log file before rotation (default: 10MB).
        backup_count: Number of backup files to keep (default: 5).
    """
    # Get log level from settings
    log_level_name = settings.LOG_LEVEL.upper() if hasattr(settings, 'LOG_LEVEL') else "INFO"
    log_level = getattr(logging, log_level_name, logging.INFO)
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create formatters
    console_formatter = CustomFormatter(use_colors=True)
    file_formatter = CustomFormatter(use_colors=False)
    
    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (if log_dir is provided)
    if log_dir:
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Application log file (all levels)
        app_log = log_dir / f"moonvpn_{settings.ENVIRONMENT}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            app_log,
            maxBytes=max_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
        
        # Error log file (ERROR and above)
        error_log = log_dir / f"moonvpn_{settings.ENVIRONMENT}_error.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_log,
            maxBytes=max_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        root_logger.addHandler(error_handler)
    
    # Telegram handler for critical errors in production
    if hasattr(settings, 'is_production') and settings.is_production() and hasattr(settings, 'LOG_CHANNEL_ID') and settings.LOG_CHANNEL_ID:
        telegram_handler = TelegramHandler(
            settings.TELEGRAM_BOT_TOKEN,
            settings.LOG_CHANNEL_ID
        )
        telegram_handler.setLevel(logging.CRITICAL)
        telegram_handler.setFormatter(file_formatter)
        root_logger.addHandler(telegram_handler)
    
    # Adjust third-party loggers
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("aiohttp.access").setLevel(logging.WARNING)
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(
        f"Logging system initialized: "
        f"environment={settings.ENVIRONMENT}, "
        f"level={log_level_name}, "
        f"log_dir={log_dir if log_dir else 'stdout only'}"
    )

def get_logger(name: str) -> logging.Logger:
    """Returns a logger instance with the given name.
    
    This is the preferred way to get a logger in the application.
    
    Args:
        name: Usually __name__ of the module
    
    Returns:
        logging.Logger: Configured logger instance
    
    Example:
        logger = get_logger(__name__)
        logger.info("This is a log message")
    """
    return logging.getLogger(name)

def get_log_dir() -> str:
    """Returns the appropriate log directory based on the environment."""
    if hasattr(settings, 'is_development') and settings.is_development():
        return "logs/dev"
    elif hasattr(settings, 'is_testing') and settings.is_testing():
        return "logs/test"
    else:
        return "/var/log/moonvpn"  # Production logs in standard location 