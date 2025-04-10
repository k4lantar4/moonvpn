from typing import List, Dict, Any
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from .common_keyboards import get_back_button

def get_my_services_keyboard(services: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """
    Get keyboard listing user's active services (clients).

    Args:
        services: List of user's client account dictionaries.

    Returns:
        InlineKeyboardMarkup: Keyboard listing services.
    """
    builder = InlineKeyboardBuilder()

    if not services:
        builder.button(text="شما سرویس فعالی ندارید.", callback_data="no_services")
    else:
        for service in services:
            service_id = service.get("id")
            remark = service.get("remark", f"Service {service_id}")
            # Maybe add expiry or location info?
            # expiry_date = service.get("expire_date", "N/A")
            builder.button(
                text=f"🔑 {remark}",
                callback_data=f"view_service_{service_id}"
            )

    builder.row(get_back_button(callback_data="main_menu"))
    builder.adjust(1)
    return builder.as_markup()

def get_service_actions_keyboard(service_id: int, can_renew: bool = True, can_freeze: bool = True, is_frozen: bool = False) -> InlineKeyboardMarkup:
    """
    Get keyboard with actions for a specific service.

    Args:
        service_id: The ID of the client service.
        can_renew: Whether the service is eligible for renewal.
        can_freeze: Whether the service can be frozen.
        is_frozen: Whether the service is currently frozen.

    Returns:
        InlineKeyboardMarkup: Service action keyboard.
    """
    builder = InlineKeyboardBuilder()

    builder.button(text="🔗 دریافت لینک", callback_data=f"get_config_{service_id}")
    builder.button(text="📊 مشاهده مصرف", callback_data=f"get_usage_{service_id}")

    if can_renew:
        builder.button(text="🔄 تمدید سرویس", callback_data=f"renew_service_{service_id}")
    # else: # Optionally show disabled button
        # builder.button(text="(تمدید غیرفعال)", callback_data="renew_disabled")

    if is_frozen:
        builder.button(text="▶️ فعالسازی مجدد", callback_data=f"unfreeze_service_{service_id}")
    elif can_freeze:
        builder.button(text="⏸ فریز کردن", callback_data=f"freeze_service_{service_id}")

    builder.button(text="✏️ تغییر نام (بزودی)", callback_data=f"rename_service_{service_id}_soon") # Placeholder
    builder.button(text="🗑 حذف (بزودی)", callback_data=f"delete_service_{service_id}_soon") # Placeholder

    builder.row(get_back_button(callback_data="my_services")) # Back to services list
    builder.adjust(2) # Adjust layout, e.g., 2 columns
    return builder.as_markup() 