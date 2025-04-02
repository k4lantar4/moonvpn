"""
Helper functions for the Telegram bot.
"""
import re
from typing import Optional

def format_card_number(card_number: str) -> str:
    """
    Format a card number for display, showing only the last 4 digits.
    
    Args:
        card_number: The full card number
        
    Returns:
        Formatted card number string (e.g., "6104 **** **** 1234")
    """
    if not card_number:
        return "نامشخص"
    
    # Remove any non-digit characters
    digits_only = re.sub(r'\D', '', card_number)
    
    if len(digits_only) < 16:
        return card_number  # Return as-is if not a standard 16-digit card
    
    # Get the first 4 and last 4 digits
    first_four = digits_only[:4]
    last_four = digits_only[-4:]
    
    # Format with stars in the middle
    return f"{first_four} **** **** {last_four}"

def format_bytes(bytes_value: int) -> str:
    """
    Format a byte value to human readable format (KB, MB, GB, etc.)
    
    Args:
        bytes_value: The byte value to format
        
    Returns:
        Formatted string with appropriate unit
    """
    if bytes_value < 1024:
        return f"{bytes_value} B"
    elif bytes_value < 1024**2:
        return f"{bytes_value/1024:.1f} KB"
    elif bytes_value < 1024**3:
        return f"{bytes_value/1024**2:.1f} MB"
    else:
        return f"{bytes_value/1024**3:.2f} GB"

def create_progress_bar(current: int, total: int, width: int = 10) -> str:
    """
    Create a text-based progress bar.
    
    Args:
        current: Current value
        total: Total value
        width: Width of the progress bar in characters
        
    Returns:
        Text progress bar (e.g., "▓▓▓▓▓░░░░░")
    """
    if total == 0:
        return "░" * width
        
    # Calculate the ratio of completion
    ratio = min(current / total, 1.0)
    
    # Calculate the number of filled and empty slots
    filled_slots = int(width * ratio)
    empty_slots = width - filled_slots
    
    # Create the progress bar
    return "▓" * filled_slots + "░" * empty_slots

def format_percent(current: int, total: int) -> str:
    """
    Format a percentage value.
    
    Args:
        current: Current value
        total: Total value
        
    Returns:
        Formatted percentage string
    """
    if total == 0:
        return "0%"
    
    ratio = min(current / total, 1.0)
    return f"{ratio*100:.1f}%"

def truncate_text(text: str, max_length: int = 50) -> str:
    """
    Truncate text to a maximum length, adding ellipsis if truncated.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        
    Returns:
        Truncated text with ellipsis if needed
    """
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length-3] + "..." 