"""
Helper functions for MoonVPN Telegram Bot.

This module contains various utility functions used throughout the application.
"""

import datetime
import re
import random
import string
from typing import Optional, Any, Dict, List, Union, Tuple
from jdatetime import datetime as jdatetime
import logging
from django.conf import settings
from django.db import transaction
import uuid
import hashlib
from datetime import timedelta

# Configure logger
logger = logging.getLogger(__name__)

def generate_random_string(length: int = 8) -> str:
    """Generate a random string of letters and numbers.
    
    Args:
        length: Length of the random string.
        
    Returns:
        Random string of specified length.
    """
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def generate_tracking_code() -> str:
    """Generate a unique tracking code for payments.
    
    Returns:
        Tracking code with format: MV-XXXXX-XXXXX
    """
    part1 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    part2 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return f"MV-{part1}-{part2}"

def format_bytes(size: int) -> str:
    """Format bytes to human-readable format.
    
    Args:
        size: Size in bytes.
        
    Returns:
        Formatted string (e.g., "1.5 GB").
    """
    power = 2**10
    n = 0
    power_labels = {0: 'B', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}
    
    while size > power:
        size /= power
        n += 1
        
    return f"{size:.1f} {power_labels[n]}"

def validate_phone_number(phone: str) -> bool:
    """Validate Iranian phone number.
    
    Args:
        phone: Phone number to validate.
        
    Returns:
        True if valid, False otherwise.
    """
    # Check if it starts with +98 or 0
    pattern = r'^(?:\+98|0)?9\d{9}$'
    return bool(re.match(pattern, phone))

def normalize_phone_number(phone: str) -> str:
    """Normalize phone number to +98 format.
    
    Args:
        phone: Phone number to normalize.
        
    Returns:
        Normalized phone number.
    """
    if not phone:
        return ""
        
    # Remove any non-digit characters
    digits = ''.join(char for char in phone if char.isdigit())
    
    # If it starts with 0, remove it and add +98
    if digits.startswith('0'):
        return f"+98{digits[1:]}"
    
    # If it doesn't have country code, add +98
    if len(digits) == 10 and digits.startswith('9'):
        return f"+98{digits}"
        
    # If it already has 98, add +
    if digits.startswith('98'):
        return f"+{digits}"
        
    return phone

def get_formatted_datetime(dt: Optional[datetime.datetime] = None, 
                          format_str: str = "%Y-%m-%d %H:%M:%S",
                          use_jalali: bool = True) -> str:
    """Format datetime to string, optionally using Jalali calendar.
    
    Args:
        dt: Datetime object (uses current time if None).
        format_str: Format string.
        use_jalali: Whether to use Jalali (Persian) calendar.
        
    Returns:
        Formatted datetime string.
    """
    if dt is None:
        dt = datetime.datetime.now()
        
    if use_jalali:
        jdt = jdatetime.fromgregorian(datetime=dt)
        return jdt.strftime(format_str)
    
    return dt.strftime(format_str)

def format_currency(amount: Union[int, float], 
                   currency: str = "تومان",
                   with_comma: bool = True) -> str:
    """Format currency with optional comma separator.
    
    Args:
        amount: Amount to format.
        currency: Currency name.
        with_comma: Whether to add comma separators.
        
    Returns:
        Formatted currency string.
    """
    if with_comma:
        # Add comma separators
        formatted = "{:,}".format(int(amount))
    else:
        formatted = str(int(amount))
        
    return f"{formatted} {currency}"

def extract_user_data(user: Any) -> Dict[str, Any]:
    """Extract relevant user data from telegram User object.
    
    Args:
        user: Telegram User object.
        
    Returns:
        Dictionary with user data.
    """
    return {
        "user_id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "full_name": f"{user.first_name} {user.last_name or ''}".strip(),
        "language_code": getattr(user, 'language_code', 'fa'),
        "is_bot": user.is_bot,
    }

def chunked_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split a list into chunks of specified size.
    
    Args:
        lst: List to split.
        chunk_size: Size of each chunk.
        
    Returns:
        List of chunked lists.
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

def to_persian_numbers(text: str) -> str:
    """Convert Western Arabic numerals to Persian numerals.
    
    Args:
        text: Text containing numbers.
        
    Returns:
        Text with Persian numbers.
    """
    persian_numbers = {
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
    }
    
    for eng, per in persian_numbers.items():
        text = text.replace(eng, per)
        
    return text

def get_or_create_user(
    telegram_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    language_code: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get or create a user in the database.
    
    Args:
        telegram_id: User's Telegram ID
        username: User's Telegram username (optional)
        first_name: User's first name (optional)
        last_name: User's last name (optional)
        language_code: User's language code (optional)
        
    Returns:
        User object
    """
    try:
        from backend.users.models import User
        
        # Try to get existing user
        try:
            user = User.objects.get(telegram_id=telegram_id)
            # Update user information
            user.username = username
            user.first_name = first_name
            user.last_name = last_name
            user.language_code = language_code
            user.save()
            return user
        except User.DoesNotExist:
            # Create new user
            with transaction.atomic():
                user = User.objects.create(
                    telegram_id=telegram_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    language_code=language_code
                )
                return user
    except Exception as e:
        logger.error(f"Error in get_or_create_user: {str(e)}")
        # Return a dummy user dictionary if database operation fails
        return {
            "telegram_id": telegram_id,
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "language_code": language_code
        }

def get_user(telegram_id: int) -> Dict[str, Any]:
    """
    Get a user from the database by Telegram ID.
    
    Args:
        telegram_id: User's Telegram ID
        
    Returns:
        User object or None if not found
    """
    try:
        from backend.users.models import User
        return User.objects.get(telegram_id=telegram_id)
    except Exception as e:
        logger.error(f"Error in get_user: {str(e)}")
        return None

def format_number(number: Union[int, float]) -> str:
    """
    Format a number with commas as thousands separators.
    
    Args:
        number: Number to format
        
    Returns:
        Formatted number string
    """
    try:
        return f"{number:,}"
    except (ValueError, TypeError):
        return str(number)

def human_readable_size(size_bytes: Union[int, float]) -> str:
    """
    Convert bytes to human-readable format (KB, MB, GB, etc.).
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Human-readable size string
    """
    if size_bytes == 0:
        return "0 B"
    
    try:
        size_bytes = float(size_bytes)
        size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
        i = 0
        while size_bytes >= 1024 and i < len(size_name) - 1:
            size_bytes /= 1024
            i += 1
            
        if i >= 2:  # MB or higher
            return f"{size_bytes:.2f} {size_name[i]}"
        else:
            return f"{size_bytes:.0f} {size_name[i]}"
    except (ValueError, TypeError):
        return "0 B"

def parse_subscription_link(link: str) -> Tuple[Dict[str, Any], bool]:
    """
    Parse a V2Ray/XRay subscription link to extract configuration.
    
    Args:
        link: V2Ray/XRay subscription link
        
    Returns:
        Tuple of (parsed config dict, success boolean)
    """
    try:
        # Basic validation
        if not link or not isinstance(link, str):
            return {}, False
        
        # Remove whitespace and check if it's a valid link
        link = link.strip()
        if not (link.startswith("vmess://") or link.startswith("vless://") or 
                link.startswith("trojan://") or link.startswith("ss://")):
            return {}, False
        
        # Different parsing based on protocol
        protocol = link.split("://")[0]
        config = {"protocol": protocol}
        
        if protocol == "vmess":
            # VMess links are base64 encoded JSON
            import base64
            import json
            try:
                encoded_part = link.replace("vmess://", "")
                json_str = base64.b64decode(encoded_part + "=" * (-len(encoded_part) % 4)).decode('utf-8')
                vmess_config = json.loads(json_str)
                
                # Extract key information
                config.update({
                    "id": vmess_config.get("id", ""),
                    "address": vmess_config.get("add", ""),
                    "port": vmess_config.get("port", ""),
                    "aid": vmess_config.get("aid", ""),
                    "net": vmess_config.get("net", ""),
                    "type": vmess_config.get("type", ""),
                    "host": vmess_config.get("host", ""),
                    "path": vmess_config.get("path", ""),
                    "tls": vmess_config.get("tls", ""),
                    "sni": vmess_config.get("sni", ""),
                    "remarks": vmess_config.get("ps", "")
                })
                return config, True
            except Exception as e:
                logger.error(f"Error parsing VMess link: {str(e)}")
                return {}, False
                
        elif protocol in ["vless", "trojan"]:
            # VLESS/Trojan links format: protocol://uuid@address:port?param1=value1&param2=value2#remarks
            try:
                main_part = link.split("://")[1]
                if "#" in main_part:
                    main_part, remarks = main_part.split("#", 1)
                    config["remarks"] = remarks
                else:
                    config["remarks"] = ""
                
                # Extract user-address part and parameters
                if "?" in main_part:
                    user_address, params = main_part.split("?", 1)
                else:
                    user_address, params = main_part, ""
                
                # Extract user and address
                id_and_address = user_address.split("@", 1)
                if len(id_and_address) == 2:
                    config["id"] = id_and_address[0]
                    
                    # Extract address and port
                    address_and_port = id_and_address[1].split(":", 1)
                    if len(address_and_port) == 2:
                        config["address"] = address_and_port[0]
                        config["port"] = address_and_port[1]
                
                # Parse parameters
                if params:
                    param_pairs = params.split("&")
                    for pair in param_pairs:
                        if "=" in pair:
                            key, value = pair.split("=", 1)
                            config[key] = value
                
                return config, True
            except Exception as e:
                logger.error(f"Error parsing {protocol.upper()} link: {str(e)}")
                return {}, False
                
        elif protocol == "ss":
            # Shadowsocks links format: ss://base64(method:password)@address:port#remarks
            try:
                import base64
                main_part = link.split("://")[1]
                
                # Extract remarks if present
                if "#" in main_part:
                    main_part, remarks = main_part.split("#", 1)
                    config["remarks"] = remarks
                else:
                    config["remarks"] = ""
                
                # Check if it's the legacy format or SIP002 format
                if "@" in main_part:
                    # SIP002 format
                    cred_b64, address_and_port = main_part.split("@", 1)
                    try:
                        # Try to decode the credential part
                        decoded = base64.b64decode(cred_b64 + "=" * (-len(cred_b64) % 4)).decode('utf-8')
                        if ":" in decoded:
                            config["method"], config["password"] = decoded.split(":", 1)
                    except:
                        # If decoding fails, it might be already decoded
                        if ":" in cred_b64:
                            config["method"], config["password"] = cred_b64.split(":", 1)
                    
                    # Parse address and port
                    if ":" in address_and_port:
                        config["address"], config["port"] = address_and_port.split(":", 1)
                else:
                    # Legacy format - everything is base64 encoded
                    try:
                        decoded = base64.b64decode(main_part + "=" * (-len(main_part) % 4)).decode('utf-8')
                        if "@" in decoded:
                            cred, address_and_port = decoded.split("@", 1)
                            config["method"], config["password"] = cred.split(":", 1)
                            config["address"], config["port"] = address_and_port.split(":", 1)
                    except Exception as e:
                        logger.error(f"Error decoding legacy SS link: {str(e)}")
                        return {}, False
                
                return config, True
            except Exception as e:
                logger.error(f"Error parsing Shadowsocks link: {str(e)}")
                return {}, False
        
        return {}, False
    except Exception as e:
        logger.error(f"Error in parse_subscription_link: {str(e)}")
        return {}, False

def is_valid_url(url: str) -> bool:
    """
    Check if a URL is valid.
    
    Args:
        url: URL to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not url or not isinstance(url, str):
        return False
    
    regex = re.compile(
        r'^(?:http|ftp)s?://'  # http://, https://, ftp://, ftps://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    return re.match(regex, url) is not None 

def format_duration(seconds: int) -> str:
    """Format seconds to human readable duration."""
    try:
        intervals = [
            ('سال', 31536000),
            ('ماه', 2592000),
            ('روز', 86400),
            ('ساعت', 3600),
            ('دقیقه', 60),
            ('ثانیه', 1)
        ]
        
        result = []
        for name, count in intervals:
            value = seconds // count
            if value:
                seconds -= value * count
                if value == 1:
                    result.append(f"{value} {name}")
                else:
                    result.append(f"{value} {name}")
        return ' و '.join(result)
    except Exception as e:
        logger.error("Error formatting duration: %s", str(e))
        return str(seconds)

def format_date(date: Union[str, datetime]) -> str:
    """Format date to human readable format."""
    try:
        if isinstance(date, str):
            date = datetime.strptime(date, '%Y-%m-%d')
        return date.strftime('%Y/%m/%d')
    except Exception as e:
        logger.error("Error formatting date: %s", str(e))
        return str(date)

def format_datetime(dt: Union[str, datetime]) -> str:
    """Format datetime to human readable format."""
    try:
        if isinstance(dt, str):
            dt = datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')
        return dt.strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logger.error("Error formatting datetime: %s", str(e))
        return str(dt)

def format_price(amount: int) -> str:
    """Format price in Tomans with thousand separators."""
    try:
        return f"{format_number(amount)} تومان"
    except Exception as e:
        logger.error("Error formatting price: %s", str(e))
        return str(amount)

def generate_uuid() -> str:
    """Generate a random UUID."""
    try:
        return str(uuid.uuid4())
    except Exception as e:
        logger.error("Error generating UUID: %s", str(e))
        return hashlib.md5(str(datetime.now()).encode()).hexdigest()

def validate_username(username: str) -> bool:
    """Validate Telegram username format."""
    try:
        pattern = r'^[a-zA-Z0-9_]{5,32}$'
        return bool(re.match(pattern, username))
    except Exception as e:
        logger.error("Error validating username: %s", str(e))
        return False

def validate_phone(phone: str) -> bool:
    """Validate Iranian phone number format."""
    try:
        pattern = r'^(\+98|0)?9\d{9}$'
        return bool(re.match(pattern, phone))
    except Exception as e:
        logger.error("Error validating phone: %s", str(e))
        return False

def mask_card_number(card: str) -> str:
    """Mask bank card number."""
    try:
        card = re.sub(r'\D', '', card)
        if len(card) != 16:
            return card
        return f"{card[:4]} **** **** {card[-4:]}"
    except Exception as e:
        logger.error("Error masking card number: %s", str(e))
        return card

def get_remaining_time(expiry_date: Union[str, datetime]) -> Optional[timedelta]:
    """Get remaining time until expiry date."""
    try:
        if isinstance(expiry_date, str):
            expiry_date = datetime.strptime(expiry_date, '%Y-%m-%d')
        now = datetime.now()
        if expiry_date > now:
            return expiry_date - now
        return None
    except Exception as e:
        logger.error("Error getting remaining time: %s", str(e))
        return None

def get_traffic_percentage(used: int, total: int) -> float:
    """Calculate traffic usage percentage."""
    try:
        if total == 0:
            return 0
        return (used / total) * 100
    except Exception as e:
        logger.error("Error calculating traffic percentage: %s", str(e))
        return 0

def format_traffic_usage(used: int, total: int) -> str:
    """Format traffic usage with percentage."""
    try:
        percentage = get_traffic_percentage(used, total)
        return f"{format_bytes(used)} / {format_bytes(total)} ({percentage:.1f}%)"
    except Exception as e:
        logger.error("Error formatting traffic usage: %s", str(e))
        return f"{format_bytes(used)} / {format_bytes(total)}"

def get_subscription_status(expiry_date: Union[str, datetime], traffic_used: int, traffic_limit: int) -> str:
    """Get subscription status emoji."""
    try:
        if isinstance(expiry_date, str):
            expiry_date = datetime.strptime(expiry_date, '%Y-%m-%d')
        
        now = datetime.now()
        
        # Check if expired
        if expiry_date < now:
            return '🔴'
        
        # Check traffic usage
        traffic_percentage = get_traffic_percentage(traffic_used, traffic_limit)
        
        # Less than 50% used
        if traffic_percentage < 50:
            return '🟢'
        
        # Between 50% and 90% used
        if traffic_percentage < 90:
            return '🟡'
        
        # Over 90% used
        return '🟠'
        
    except Exception as e:
        logger.error("Error getting subscription status: %s", str(e))
        return '⚫️'

def format_card_to_card(amount: int, card: str, name: str) -> str:
    """Format card-to-card payment information."""
    try:
        return (
            f"💳 کارت به کارت\n\n"
            f"💰 مبلغ: {format_price(amount)}\n"
            f"🏦 شماره کارت: {mask_card_number(card)}\n"
            f"👤 به نام: {name}\n\n"
            "⚠️ پس از واریز، تصویر رسید را ارسال کنید."
        )
    except Exception as e:
        logger.error("Error formatting card to card: %s", str(e))
        return f"مبلغ: {format_price(amount)}\nکارت: {card}\nنام: {name}" 