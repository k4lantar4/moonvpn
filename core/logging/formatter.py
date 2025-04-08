import logging
import sys
from datetime import datetime
from logging import LogRecord

from core.config import get_settings

settings = get_settings()

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