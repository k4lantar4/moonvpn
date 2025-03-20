"""
Validation utilities for MoonVPN Telegram bot.

This module provides functions for validating various inputs used in the bot's
command handlers and services.
"""

import re
from typing import List, Optional, Set, Tuple
from datetime import datetime
from app.core.database.models.admin import AdminGroupType, NotificationLevel

def validate_group_type(group_type: str) -> Tuple[bool, Optional[str]]:
    """
    Validate if the given group type is valid.
    
    Args:
        group_type: The group type to validate
        
    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    try:
        AdminGroupType(group_type.lower())
        return True, None
    except ValueError:
        return False, (
            "❌ نوع گروه نامعتبر است. لطفاً یکی از انواع زیر را انتخاب کنید:\n"
            "🔗 Invalid group type. Please select one of the following types:\n"
            f"{', '.join(t.value for t in AdminGroupType)}"
        )

def validate_notification_level(level: str) -> Tuple[bool, Optional[str]]:
    """
    Validate if the given notification level is valid.
    
    Args:
        level: The notification level to validate
        
    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    try:
        NotificationLevel(level.lower())
        return True, None
    except ValueError:
        return False, (
            "❌ سطح اعلان نامعتبر است. لطفاً یکی از سطوح زیر را انتخاب کنید:\n"
            "🔗 Invalid notification level. Please select one of the following levels:\n"
            f"{', '.join(l.value for l in NotificationLevel)}"
        )

def validate_group_name(name: str) -> Tuple[bool, Optional[str]]:
    """
    Validate if the given group name is valid.
    
    Args:
        name: The group name to validate
        
    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    if not name:
        return False, (
            "❌ نام گروه نمی‌تواند خالی باشد.\n"
            "🔗 Group name cannot be empty."
        )
        
    if len(name) < 3:
        return False, (
            "❌ نام گروه باید حداقل 3 کاراکتر باشد.\n"
            "🔗 Group name must be at least 3 characters long."
        )
        
    if len(name) > 50:
        return False, (
            "❌ نام گروه نمی‌تواند بیشتر از 50 کاراکتر باشد.\n"
            "🔗 Group name cannot be more than 50 characters long."
        )
        
    # Allow letters, numbers, spaces, hyphens, and underscores
    pattern = r'^[a-zA-Z0-9\s\-_]+$'
    if not re.match(pattern, name):
        return False, (
            "❌ نام گروه فقط می‌تواند شامل حروف، اعداد، فاصله، خط تیره و زیرخط باشد.\n"
            "🔗 Group name can only contain letters, numbers, spaces, hyphens, and underscores."
        )
    
    return True, None

def validate_group_description(description: str) -> Tuple[bool, Optional[str]]:
    """
    Validate if the given group description is valid.
    
    Args:
        description: The group description to validate
        
    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    if not description:
        return True, None  # Description is optional
        
    if len(description) > 500:
        return False, (
            "❌ توضیحات گروه نمی‌تواند بیشتر از 500 کاراکتر باشد.\n"
            "🔗 Group description cannot be more than 500 characters long."
        )
        
    # Allow letters, numbers, spaces, hyphens, underscores, and basic punctuation
    pattern = r'^[a-zA-Z0-9\s\-_.,!?()]+$'
    if not re.match(pattern, description):
        return False, (
            "❌ توضیحات گروه فقط می‌تواند شامل حروف، اعداد، فاصله، خط تیره، زیرخط و علائم نگارشی پایه باشد.\n"
            "🔗 Group description can only contain letters, numbers, spaces, hyphens, underscores, and basic punctuation."
        )
    
    return True, None

def validate_member_role(role: str) -> Tuple[bool, Optional[str]]:
    """
    Validate if the given member role is valid.
    
    Args:
        role: The member role to validate
        
    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    if not role:
        return False, (
            "❌ نقش عضو نمی‌تواند خالی باشد.\n"
            "🔗 Member role cannot be empty."
        )
        
    if len(role) < 2:
        return False, (
            "❌ نقش عضو باید حداقل 2 کاراکتر باشد.\n"
            "🔗 Member role must be at least 2 characters long."
        )
        
    if len(role) > 50:
        return False, (
            "❌ نقش عضو نمی‌تواند بیشتر از 50 کاراکتر باشد.\n"
            "🔗 Member role cannot be more than 50 characters long."
        )
        
    # Allow letters, numbers, spaces, hyphens, and underscores
    pattern = r'^[a-zA-Z0-9\s\-_]+$'
    if not re.match(pattern, role):
        return False, (
            "❌ نقش عضو فقط می‌تواند شامل حروف، اعداد، فاصله، خط تیره و زیرخط باشد.\n"
            "🔗 Member role can only contain letters, numbers, spaces, hyphens, and underscores."
        )
    
    return True, None

def validate_member_notes(notes: str) -> Tuple[bool, Optional[str]]:
    """
    Validate if the given member notes are valid.
    
    Args:
        notes: The member notes to validate
        
    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    if not notes:
        return True, None  # Notes are optional
        
    if len(notes) > 1000:
        return False, (
            "❌ یادداشت‌ها نمی‌توانند بیشتر از 1000 کاراکتر باشند.\n"
            "🔗 Notes cannot be more than 1000 characters long."
        )
        
    # Allow letters, numbers, spaces, hyphens, underscores, and basic punctuation
    pattern = r'^[a-zA-Z0-9\s\-_.,!?()]+$'
    if not re.match(pattern, notes):
        return False, (
            "❌ یادداشت‌ها فقط می‌توانند شامل حروف، اعداد، فاصله، خط تیره، زیرخط و علائم نگارشی پایه باشند.\n"
            "🔗 Notes can only contain letters, numbers, spaces, hyphens, underscores, and basic punctuation."
        )
    
    return True, None

def validate_group_id(group_id: str) -> bool:
    """
    Validate if the given group ID is valid.
    
    Args:
        group_id: The group ID to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        group_id = int(group_id)
        return group_id > 0
    except ValueError:
        return False

def validate_user_id(user_id: str) -> Tuple[bool, Optional[str]]:
    """
    Validate if the given user ID is valid.
    
    Args:
        user_id: The user ID to validate
        
    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    try:
        uid = int(user_id)
        if uid <= 0:
            return False, (
                "❌ شناسه کاربر باید عدد مثبت باشد.\n"
                "🔗 User ID must be a positive number."
            )
        return True, None
    except ValueError:
        return False, (
            "❌ شناسه کاربر باید عدد باشد.\n"
            "🔗 User ID must be a number."
        )

def validate_chat_id(chat_id: str) -> Tuple[bool, Optional[str]]:
    """
    Validate if the given chat ID is valid.
    
    Args:
        chat_id: The chat ID to validate
        
    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    try:
        cid = int(chat_id)
        if cid >= 0:
            return False, (
                "❌ شناسه چت باید عدد منفی باشد.\n"
                "🔗 Chat ID must be a negative number."
            )
        return True, None
    except ValueError:
        return False, (
            "❌ شناسه چت باید عدد باشد.\n"
            "🔗 Chat ID must be a number."
        )

def validate_pagination_params(offset: int, limit: int) -> Tuple[bool, Optional[str]]:
    """
    Validate pagination parameters.
    
    Args:
        offset: The offset value
        limit: The limit value
        
    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    if offset < 0:
        return False, (
            "❌ مقدار offset نمی‌تواند منفی باشد.\n"
            "🔗 Offset cannot be negative."
        )
        
    if limit < 1:
        return False, (
            "❌ مقدار limit باید حداقل 1 باشد.\n"
            "🔗 Limit must be at least 1."
        )
        
    if limit > 100:
        return False, (
            "❌ مقدار limit نمی‌تواند بیشتر از 100 باشد.\n"
            "🔗 Limit cannot be more than 100."
        )
    
    return True, None

def validate_notification_types(notification_types: List[str]) -> Tuple[bool, Optional[str]]:
    """
    Validate if the given notification types are valid.
    
    Args:
        notification_types: List of notification types to validate
        
    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    if not notification_types:
        return False, (
            "❌ حداقل یک نوع اعلان باید انتخاب شود.\n"
            "🔗 At least one notification type must be selected."
        )
        
    valid_types: Set[str] = {
        'system',
        'security',
        'performance',
        'user',
        'payment',
        'vpn'
    }
    
    invalid_types = [t for t in notification_types if t.strip().lower() not in valid_types]
    if invalid_types:
        return False, (
            "❌ انواع اعلان نامعتبر: {}\n"
            "🔗 Invalid notification types: {}\n\n"
            "انواع معتبر / Valid types:\n"
            f"{', '.join(valid_types)}"
        ).format(', '.join(invalid_types), ', '.join(invalid_types))
    
    return True, None

def validate_group_update_field(field: str) -> Tuple[bool, Optional[str]]:
    """
    Validate if the given group update field is valid.
    
    Args:
        field: The field to validate
        
    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    valid_fields = {
        'name',
        'type',
        'notification_level',
        'description',
        'is_active'
    }
    
    if field.lower() not in valid_fields:
        return False, (
            "❌ فیلد نامعتبر. فیلدهای معتبر:\n"
            "🔗 Invalid field. Valid fields:\n"
            f"{', '.join(valid_fields)}"
        )
    
    return True, None

def validate_group_update_value(field: str, value: str) -> Tuple[bool, Optional[str]]:
    """
    Validate if the given value is valid for the specified group update field.
    
    Args:
        field: The field being updated
        value: The new value
        
    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    field = field.lower()
    
    if field == 'name':
        return validate_group_name(value)
    elif field == 'type':
        return validate_group_type(value)
    elif field == 'notification_level':
        return validate_notification_level(value)
    elif field == 'description':
        return validate_group_description(value)
    elif field == 'is_active':
        if value.lower() not in ('true', 'false'):
            return False, (
                "❌ مقدار نامعتبر. باید true یا false باشد.\n"
                "🔗 Invalid value. Must be true or false."
            )
        return True, None
    else:
        return False, (
            "❌ فیلد نامعتبر.\n"
            "🔗 Invalid field."
        )

def validate_date(date_str: str) -> bool:
    """
    Validate if the given date string is valid.
    
    Args:
        date_str: The date string to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def validate_time(time_str: str) -> bool:
    """
    Validate if the given time string is valid.
    
    Args:
        time_str: The time string to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        datetime.strptime(time_str, '%H:%M:%S')
        return True
    except ValueError:
        return False

def validate_email(email: str) -> bool:
    """
    Validate if the given email address is valid.
    
    Args:
        email: The email address to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_phone_number(phone: str) -> bool:
    """
    Validate if the given phone number is valid.
    
    Args:
        phone: The phone number to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    pattern = r'^\+?[1-9]\d{1,14}$'
    return bool(re.match(pattern, phone))

def validate_url(url: str) -> bool:
    """
    Validate if the given URL is valid.
    
    Args:
        url: The URL to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    pattern = r'^https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&\/=]*)$'
    return bool(re.match(pattern, url))

def validate_ip_address(ip: str) -> bool:
    """
    Validate if the given IP address is valid.
    
    Args:
        ip: The IP address to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    if not re.match(pattern, ip):
        return False
        
    # Validate each octet
    octets = ip.split('.')
    return all(0 <= int(octet) <= 255 for octet in octets)

def validate_mac_address(mac: str) -> bool:
    """
    Validate if the given MAC address is valid.
    
    Args:
        mac: The MAC address to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    pattern = r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$'
    return bool(re.match(pattern, mac))

def validate_port_number(port: str) -> bool:
    """
    Validate if the given port number is valid.
    
    Args:
        port: The port number to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        port_num = int(port)
        return 1 <= port_num <= 65535
    except ValueError:
        return False

def validate_password(password: str) -> bool:
    """
    Validate if the given password is valid.
    
    Args:
        password: The password to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    # At least 8 characters, 1 uppercase, 1 lowercase, 1 number, 1 special character
    pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
    return bool(re.match(pattern, password))

def validate_username(username: str) -> bool:
    """
    Validate if the given username is valid.
    
    Args:
        username: The username to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not username or len(username) < 3 or len(username) > 30:
        return False
        
    # Allow letters, numbers, and underscores
    pattern = r'^[a-zA-Z0-9_]+$'
    return bool(re.match(pattern, username)) 