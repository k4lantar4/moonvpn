from typing import List, Dict, Any
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from .common_keyboards import get_back_button

def get_locations_keyboard(locations: List[Dict[str, Any]], back_callback: str = "purchase_plan") -> InlineKeyboardMarkup:
    """
    Get keyboard for locations.

    Args:
        locations: List of location objects
        back_callback: Callback data for the back button.

    Returns:
        InlineKeyboardMarkup: Keyboard with location buttons
    """
    builder = InlineKeyboardBuilder()

    # Add location buttons
    for location in locations:
        flag = location.get("flag", "🌍") # Assuming 'flag' field exists
        name = location.get("name", "Unknown Location")
        loc_id = location.get("id")
        builder.button(
            text=f"{flag} {name}",
            callback_data=f"location_{loc_id}"
        )

    builder.row(get_back_button(callback_data=back_callback))
    builder.adjust(1)
    return builder.as_markup()

def get_protocols_keyboard(protocols: List[str], back_callback: str = "purchase_plan") -> InlineKeyboardMarkup:
    """
    Get keyboard for protocols.

    Args:
        protocols: List of protocol names (strings)
        back_callback: Callback data for the back button.

    Returns:
        InlineKeyboardMarkup: Keyboard with protocol buttons
    """
    builder = InlineKeyboardBuilder()

    # Add protocol buttons
    for protocol in protocols:
        # Assuming protocol is just a string like 'VMESS', 'VLESS'
        builder.button(
            text=protocol,
            callback_data=f"protocol_{protocol}" # Use protocol name in callback
        )

    builder.row(get_back_button(callback_data=back_callback))
    builder.adjust(1)
    return builder.as_markup() 