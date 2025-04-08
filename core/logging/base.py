import logging
import logging.handlers
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Optional
import json
import asyncio
from functools import partial
from logging import LogRecord

from core.config import get_settings

settings = get_settings()

# --- Custom Log Formatter / فرمت‌دهنده سفارشی لاگ ---
class CustomFormatter(logging.Formatter):
    """Custom formatter with color support and extra fields."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[41m',  # Red background
        'RESET': '\033[0m'      # Reset
    }
    
    def __init__(self, use_colors: bool = True):
        super().__init__()
        self.use_colors = use_colors and sys.stdout.isatty()  # Use colors only if terminal supports it
    
    def format(self, record: LogRecord) -> str:
        # Add timestamp with milliseconds
        record.created_fmt = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        
        # Add environment info
        record.environment = settings.ENVIRONMENT
        
        # Add process and thread info if not main
        record.proc_info = ""
        if record.processName != "MainProcess":
            record.proc_info = f"[Process:{record.processName}]"
        if record.threadName != "MainThread":
            record.proc_info += f"[Thread:{record.threadName}]"
        
        # Format the message
        if self.use_colors:
            level_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
            fmt = (
                f"{level_color}[{record.created_fmt}] "
                f"[{record.environment.upper()}] "
                f"[{record.levelname}]{self.COLORS['RESET']} "
                f"{record.proc_info} "
                f"{record.name}: {record.getMessage()}"
            )
        else:
            fmt = (
                f"[{record.created_fmt}] "
                f"[{record.environment.upper()}] "
                f"[{record.levelname}] "
                f"{record.proc_info} "
                f"{record.name}: {record.getMessage()}"
            )
        
        # Add exception info if present
        if record.exc_info:
            if self.use_colors:
                fmt += f"\n{self.COLORS['ERROR']}"
            fmt += self.formatException(record.exc_info)
            if self.use_colors:
                fmt += self.COLORS['RESET']
        
        return fmt

# --- Telegram Handler / هندلر تلگرام ---
class TelegramHandler(logging.Handler):
    """Custom handler that sends critical logs to Telegram channel."""
    
    def __init__(self, bot_token: str, channel_id: str):
        super().__init__()
        self.bot_token = bot_token
        self.channel_id = channel_id
        self._queue = asyncio.Queue()
        self._task = None
        
    def emit(self, record: LogRecord):
        try:
            msg = self.format(record)
            asyncio.create_task(self._send_to_telegram(msg))
        except Exception as e:
            print(f"Error in TelegramHandler: {e}", file=sys.stderr)
    
    async def _send_to_telegram(self, message: str):
        if not self.bot_token or not self.channel_id:
            return
        
        import aiohttp
        
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        data = {
            "chat_id": self.channel_id,
            "text": f"🚨 *ALERT*\n```\n{message}\n```",
            "parse_mode": "Markdown"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data) as response:
                    if response.status != 200:
                        print(f"Failed to send log to Telegram: {response.status}", file=sys.stderr)
        except Exception as e:
            print(f"Error sending to Telegram: {e}", file=sys.stderr)

# --- Logging Setup / راه‌اندازی لاگینگ ---
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
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
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
    if settings.is_production() and settings.LOG_CHANNEL_ID:
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
        f"level={settings.LOG_LEVEL}, "
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

# --- Log Directory Setup / تنظیم دایرکتوری لاگ ---
def get_log_dir() -> str:
    """Returns the appropriate log directory based on the environment."""
    if settings.is_development():
        return "logs/dev"
    elif settings.is_testing():
        return "logs/test"
    else:
        return "/var/log/moonvpn"  # Production logs in standard location
