from typing import List, Dict, Any
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.utils.formatters import format_price # Assuming format_price is moved here
from .common_keyboards import get_back_button

def get_plans_keyboard(categories: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """
    Get keyboard for plan categories.

    Args:
        categories: List of category objects

    Returns:
        InlineKeyboardMarkup: Keyboard with category buttons
    """
    builder = InlineKeyboardBuilder()

    # Add category buttons
    for category in categories:
        builder.button(
            text=category.get("name", "Unknown Category"), # Use .get() for safety
            callback_data=f"category_{category.get('id')}"
        )

    builder.row(get_back_button(callback_data="main_menu"))
    builder.adjust(1)
    return builder.as_markup()

def get_plan_list_keyboard(plans: List[Dict[str, Any]], category_id: int) -> InlineKeyboardMarkup:
    """
    Get keyboard for plans in a category.

    Args:
        plans: List of plan objects
        category_id: ID of the current category

    Returns:
        InlineKeyboardMarkup: Keyboard with plan buttons
    """
    builder = InlineKeyboardBuilder()

    # Add plan buttons
    for plan in plans:
        plan_name = plan.get("name", "Unknown Plan")
        price = plan.get("price", 0)
        plan_id = plan.get("id")

        # Add special indicator for featured plans
        display_name = f"⭐ {plan_name}" if plan.get("is_featured") else plan_name

        # Format price
        price_text = format_price(price)

        builder.button(
            text=f"{display_name} - {price_text}",
            callback_data=f"plan_{plan_id}"
        )

    builder.row(get_back_button(callback_data="purchase_plan")) # Callback to go back to categories
    builder.adjust(1)
    return builder.as_markup()

def get_confirm_purchase_keyboard(plan_id: int) -> InlineKeyboardMarkup:
    """
    Get keyboard to confirm plan purchase.

    Args:
        plan_id: The ID of the plan being purchased.

    Returns:
        InlineKeyboardMarkup: Confirmation keyboard.
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ تایید خرید", callback_data=f"confirm_purchase_{plan_id}")
    builder.button(text="❌ لغو", callback_data="cancel_purchase") # Use a specific cancel callback
    builder.adjust(2)
    return builder.as_markup() 