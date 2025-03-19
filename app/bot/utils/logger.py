"""
Logger utility for MoonVPN Telegram Bot.

This module provides a consistent logging setup for the bot application.
"""

import logging
import sys
from typing import Optional

def setup_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """
    Setup a logger with consistent formatting and handlers.
    
    Args:
        name: The name of the logger
        level: Optional logging level (defaults to INFO)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    
    # Set level
    logger.setLevel(level or logging.INFO)
    
    # Create handlers
    console_handler = logging.StreamHandler(sys.stdout)
    file_handler = logging.FileHandler(f"logs/{name}.log")
    
    # Create formatters and add it to handlers
    log_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(log_format)
    file_handler.setFormatter(log_format)
    
    # Add handlers to the logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger 