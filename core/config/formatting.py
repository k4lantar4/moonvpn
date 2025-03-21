"""
MoonVPN Telegram Bot - Formatting Utilities.

This module provides formatting utilities for the MoonVPN Telegram bot.
"""

import re
import math
from datetime import datetime
from typing import Union, Optional

def format_number(number: Union[int, float], decimal_places: int = 0) -> str:
    """
    Format a number with thousands separator.
    
    Args:
        number: The number to format.
        decimal_places: The number of decimal places to include.
        
    Returns:
        A formatted string representation of the number.
    """
    if decimal_places > 0:
        return f"{number:,.{decimal_places}f}"
    return f"{number:,.0f}"

def format_currency(amount: Union[int, float], currency: str = "تومان") -> str:
    """
    Format a currency amount.
    
    Args:
        amount: The amount to format.
        currency: The currency symbol or name.
        
    Returns:
        A formatted string representation of the currency amount.
    """
    formatted_amount = format_number(amount)
    return f"{formatted_amount} {currency}"

def format_bytes(bytes_value: Union[int, float]) -> str:
    """
    Format a byte value into a human-readable string.
    
    Args:
        bytes_value: The byte value to format.
        
    Returns:
        A formatted string representation of the byte value.
    """
    if bytes_value == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]
    i = int(math.floor(math.log(bytes_value, 1024)))
    p = math.pow(1024, i)
    s = round(bytes_value / p, 2)
    
    return f"{s} {size_names[i]}"

def format_date(date_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format a date string into a human-readable string.
    
    Args:
        date_str: The date string to format.
        format_str: The format string to use.
        
    Returns:
        A formatted string representation of the date.
    """
    try:
        # Parse the date string
        if "T" in date_str:
            # ISO format
            date_obj = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        else:
            # Standard format
            date_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        
        # Format the date in Persian style
        persian_months = {
            1: "فروردین",
            2: "اردیبهشت",
            3: "خرداد",
            4: "تیر",
            5: "مرداد",
            6: "شهریور",
            7: "مهر",
            8: "آبان",
            9: "آذر",
            10: "دی",
            11: "بهمن",
            12: "اسفند"
        }
        
        # Format the date
        day = date_obj.day
        month = persian_months.get(date_obj.month, str(date_obj.month))
        year = date_obj.year
        hour = date_obj.hour
        minute = date_obj.minute
        
        return f"{day} {month} {year} - {hour:02d}:{minute:02d}"
    except Exception as e:
        # Return the original string if parsing fails
        return date_str

def format_duration(seconds: int) -> str:
    """
    Format a duration in seconds into a human-readable string.
    
    Args:
        seconds: The duration in seconds.
        
    Returns:
        A formatted string representation of the duration.
    """
    if seconds < 60:
        return f"{seconds} ثانیه"
    
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes} دقیقه"
    
    hours = minutes // 60
    if hours < 24:
        remaining_minutes = minutes % 60
        if remaining_minutes > 0:
            return f"{hours} ساعت و {remaining_minutes} دقیقه"
        return f"{hours} ساعت"
    
    days = hours // 24
    if days < 30:
        remaining_hours = hours % 24
        if remaining_hours > 0:
            return f"{days} روز و {remaining_hours} ساعت"
        return f"{days} روز"
    
    months = days // 30
    if months < 12:
        remaining_days = days % 30
        if remaining_days > 0:
            return f"{months} ماه و {remaining_days} روز"
        return f"{months} ماه"
    
    years = months // 12
    remaining_months = months % 12
    if remaining_months > 0:
        return f"{years} سال و {remaining_months} ماه"
    return f"{years} سال"

def format_phone_number(phone: str) -> str:
    """
    Format a phone number.
    
    Args:
        phone: The phone number to format.
        
    Returns:
        A formatted string representation of the phone number.
    """
    # Remove any non-digit characters
    phone = re.sub(r'\D', '', phone)
    
    # Format based on length
    if len(phone) == 10:
        # Format as 0XXX-XXX-XXXX
        return f"0{phone[0:3]}-{phone[3:6]}-{phone[6:10]}"
    elif len(phone) == 11 and phone.startswith('0'):
        # Format as 0XXX-XXX-XXXX
        return f"{phone[0:4]}-{phone[4:7]}-{phone[7:11]}"
    elif len(phone) == 12 and phone.startswith('98'):
        # Format as +98-XXX-XXX-XXXX
        return f"+98-{phone[2:5]}-{phone[5:8]}-{phone[8:12]}"
    else:
        # Return as is
        return phone

def format_file_size(size_in_bytes: int) -> str:
    """
    Format a file size in bytes into a human-readable string.
    
    Args:
        size_in_bytes: The file size in bytes.
        
    Returns:
        A formatted string representation of the file size.
    """
    return format_bytes(size_in_bytes) 