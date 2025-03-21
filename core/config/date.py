import datetime
import jdatetime
from typing import Optional

def format_date(date_str: Optional[str] = None, language_code: str = "fa") -> str:
    """
    Format date string according to user's language preference.
    
    Args:
        date_str: ISO format date string or None
        language_code: User's language code ('fa' for Persian, 'en' for English)
        
    Returns:
        Formatted date string
    """
    if not date_str:
        return "N/A"
    
    try:
        # Parse ISO format date
        if isinstance(date_str, str):
            # Handle different ISO formats
            if 'T' in date_str:
                dt = datetime.datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        elif isinstance(date_str, datetime.datetime):
            dt = date_str
        else:
            return str(date_str)
        
        # Format based on language
        if language_code == "fa":
            # Convert to Persian date
            jdt = jdatetime.datetime.fromgregorian(datetime=dt)
            return jdt.strftime("%Y/%m/%d %H:%M")
        else:
            # English format
            return dt.strftime("%Y-%m-%d %H:%M")
            
    except Exception as e:
        # Return the original if we can't parse it
        return str(date_str)

def format_number(number: float, language_code: str = "fa") -> str:
    """
    Format numbers according to user's language preference.
    
    Args:
        number: Number to format
        language_code: User's language code ('fa' for Persian, 'en' for English)
        
    Returns:
        Formatted number string
    """
    if language_code == "fa":
        # Format with Persian separators and numbers
        formatted = "{:,}".format(number)
        # Convert to Persian digits
        persian_digits = {
            '0': '۰',
            '1': '۱',
            '2': '۲',
            '3': '۳',
            '4': '۴',
            '5': '۵',
            '6': '۶',
            '7': '۷',
            '8': '۸',
            '9': '۹',
            ',': '،'
        }
        
        for en, fa in persian_digits.items():
            formatted = formatted.replace(en, fa)
            
        return formatted
    else:
        # Format with English separators
        return "{:,}".format(number) 