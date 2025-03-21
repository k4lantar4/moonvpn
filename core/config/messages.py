"""
Message formatting utilities for MoonVPN Telegram bot.

This module provides functions for formatting various messages used in the bot's
command handlers and services.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from app.core.database.models.admin import AdminGroup, AdminGroupMember, AdminGroupType, NotificationLevel

def format_admin_group_info(group: AdminGroup) -> str:
    """
    Format admin group information into a readable message.
    
    Args:
        group: The admin group to format
        
    Returns:
        str: Formatted message with HTML formatting
    """
    # Status emoji
    status_emoji = "🟢" if group.is_active else "🔴"
    
    # Type-specific emoji
    type_emoji = {
        AdminGroupType.MANAGE: "🛡️",
        AdminGroupType.REPORTS: "📊",
        AdminGroupType.LOGS: "📄",
        AdminGroupType.TRANSACTIONS: "💰",
        AdminGroupType.OUTAGES: "⚠️",
        AdminGroupType.SELLERS: "👥",
        AdminGroupType.BACKUPS: "💾"
    }.get(group.type, "📌")
    
    # Notification level emoji
    level_emoji = {
        NotificationLevel.LOW: "🔵",
        NotificationLevel.NORMAL: "🟡",
        NotificationLevel.HIGH: "🔴"
    }.get(group.notification_level, "⚪")
    
    # Format timestamps
    created_at = group.created_at.strftime("%Y-%m-%d %H:%M:%S")
    updated_at = group.updated_at.strftime("%Y-%m-%d %H:%M:%S")
    
    # Format notification types
    notification_types = ", ".join(group.notification_types) if group.notification_types else "None"
    
    # Build message
    message = (
        f"{type_emoji} <b>اطلاعات گروه ادمین / Admin Group Info</b>\n\n"
        f"{status_emoji} <b>وضعیت / Status:</b> {'فعال / Active' if group.is_active else 'غیرفعال / Inactive'}\n"
        f"📝 <b>نام / Name:</b> {group.name}\n"
        f"🏷️ <b>نوع / Type:</b> {group.type.value}\n"
        f"{level_emoji} <b>سطح اعلان / Notification Level:</b> {group.notification_level.value}\n"
        f"🔔 <b>انواع اعلان / Notification Types:</b> {notification_types}\n"
        f"📅 <b>تاریخ ایجاد / Created At:</b> {created_at}\n"
        f"🔄 <b>تاریخ بروزرسانی / Updated At:</b> {updated_at}\n"
    )
    
    # Add description if available
    if group.description:
        message += f"\n📄 <b>توضیحات / Description:</b>\n{group.description}"
    
    return message

def format_admin_group_member_info(member: AdminGroupMember) -> str:
    """
    Format admin group member information into a readable message.
    
    Args:
        member: The admin group member to format
        
    Returns:
        str: Formatted message with HTML formatting
    """
    # Status emoji
    status_emoji = "🟢" if member.is_active else "🔴"
    
    # Format timestamps
    created_at = member.created_at.strftime("%Y-%m-%d %H:%M:%S")
    updated_at = member.updated_at.strftime("%Y-%m-%d %H:%M:%S")
    
    # Format added by info
    added_by = member.added_by.get("user_id", "Unknown") if member.added_by else "Unknown"
    
    # Build message
    message = (
        f"👤 <b>اطلاعات عضو گروه / Group Member Info</b>\n\n"
        f"{status_emoji} <b>وضعیت / Status:</b> {'فعال / Active' if member.is_active else 'غیرفعال / Inactive'}\n"
        f"🆔 <b>شناسه کاربر / User ID:</b> {member.user_id}\n"
        f"👥 <b>نقش / Role:</b> {member.role}\n"
        f"📅 <b>تاریخ عضویت / Joined At:</b> {created_at}\n"
        f"🔄 <b>تاریخ بروزرسانی / Updated At:</b> {updated_at}\n"
        f"➕ <b>افزوده شده توسط / Added By:</b> {added_by}\n"
    )
    
    # Add notes if available
    if member.notes:
        message += f"\n📝 <b>یادداشت‌ها / Notes:</b>\n{member.notes}"
    
    return message

def format_admin_group_list(groups: List[AdminGroup]) -> str:
    """
    Format a list of admin groups into a readable message.
    
    Args:
        groups: List of admin groups to format
        
    Returns:
        str: Formatted message with HTML formatting
    """
    if not groups:
        return (
            "❌ هیچ گروه ادمینی یافت نشد.\n"
            "No admin groups found."
        )
    
    # Group type emojis
    type_emojis = {
        AdminGroupType.MANAGE: "🛡️",
        AdminGroupType.REPORTS: "📊",
        AdminGroupType.LOGS: "📄",
        AdminGroupType.TRANSACTIONS: "💰",
        AdminGroupType.OUTAGES: "⚠️",
        AdminGroupType.SELLERS: "👥",
        AdminGroupType.BACKUPS: "💾"
    }
    
    # Build message
    message = "📋 <b>لیست گروه‌های ادمین / Admin Groups List</b>\n\n"
    
    for group in groups:
        status_emoji = "🟢" if group.is_active else "🔴"
        type_emoji = type_emojis.get(group.type, "📌")
        
        message += (
            f"{type_emoji} <b>{group.name}</b>\n"
            f"{status_emoji} {group.type.value}\n"
            f"👥 {len(group.members)} عضو / members\n"
            f"🔔 {len(group.notification_types)} نوع اعلان / notification types\n\n"
        )
    
    return message

def format_admin_group_member_list(members: List[AdminGroupMember]) -> str:
    """
    Format a list of admin group members into a readable message.
    
    Args:
        members: List of admin group members to format
        
    Returns:
        str: Formatted message with HTML formatting
    """
    if not members:
        return (
            "❌ هیچ عضوی در این گروه یافت نشد.\n"
            "No members found in this group."
        )
    
    # Build message
    message = "👥 <b>لیست اعضای گروه / Group Members List</b>\n\n"
    
    for member in members:
        status_emoji = "🟢" if member.is_active else "🔴"
        
        message += (
            f"{status_emoji} <b>User ID:</b> {member.user_id}\n"
            f"👤 <b>نقش / Role:</b> {member.role}\n"
            f"📅 <b>تاریخ عضویت / Joined:</b> {member.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        )
    
    return message

def format_error_message(error: Exception) -> str:
    """
    Format an error message.
    
    Args:
        error: The error exception to format
        
    Returns:
        str: Formatted error message with HTML formatting
    """
    return (
        "❌ <b>خطا / Error:</b>\n"
        f"{str(error)}"
    )

def format_success_message(message: str) -> str:
    """
    Format a success message.
    
    Args:
        message: The success message to format
        
    Returns:
        str: Formatted success message with HTML formatting
    """
    return (
        "✅ <b>موفقیت / Success:</b>\n"
        f"{message}"
    )

def format_warning_message(message: str) -> str:
    """
    Format a warning message.
    
    Args:
        message: The warning message to format
        
    Returns:
        str: Formatted warning message with HTML formatting
    """
    return (
        "⚠️ <b>هشدار / Warning:</b>\n"
        f"{message}"
    )

def format_info_message(message: str) -> str:
    """
    Format an info message.
    
    Args:
        message: The info message to format
        
    Returns:
        str: Formatted info message with HTML formatting
    """
    return (
        "ℹ️ <b>اطلاعات / Info:</b>\n"
        f"{message}"
    ) 