"""Inline keyboards for the plan purchase flow."""

from typing import List, Optional
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from core.database.models.plan_category import PlanCategory
from core.database.models.plan import Plan
from core.database.models.location import Location

def get_plan_categories_keyboard(categories: List[PlanCategory]) -> InlineKeyboardMarkup:
    """
    Create a keyboard with plan categories.
    
    Args:
        categories: List of PlanCategory objects
        
    Returns:
        InlineKeyboardMarkup with category buttons and an "All Plans" button
    """
    keyboard = []
    
    # Add all plans button at the top
    keyboard.append([
        InlineKeyboardButton(text="🔍 همه پلن‌ها", callback_data="plan_category:all")
    ])
    
    # Add category buttons (2 per row if possible)
    category_buttons = []
    for category in categories:
        category_buttons.append(
            InlineKeyboardButton(
                text=f"📁 {category.name}", 
                callback_data=f"plan_category:{category.id}"
            )
        )
    
    # Arrange buttons in rows of 2
    for i in range(0, len(category_buttons), 2):
        row = category_buttons[i:i+2]
        keyboard.append(row)
    
    # Add back button
    keyboard.append([
        InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_main")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_plans_keyboard(plans: List[Plan]) -> InlineKeyboardMarkup:
    """
    Create a keyboard with available plans.
    
    Args:
        plans: List of Plan objects
        
    Returns:
        InlineKeyboardMarkup with plan buttons
    """
    keyboard = []
    
    # Add plan buttons (1 per row)
    for plan in plans:
        # Format price and details
        price_text = f"{plan.price:,} تومان"
        duration_text = f"{plan.days} روز"
        traffic_text = f"{plan.data_limit} GB" if plan.data_limit else "نامحدود"
        
        button_text = f"{plan.name} | {price_text} | {duration_text} | {traffic_text}"
        
        keyboard.append([
            InlineKeyboardButton(
                text=button_text, 
                callback_data=f"plan:{plan.id}"
            )
        ])
    
    # Add back button
    keyboard.append([
        InlineKeyboardButton(text="🔙 بازگشت به دسته‌بندی‌ها", callback_data="back_to_categories")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_locations_keyboard(locations: List[Location]) -> InlineKeyboardMarkup:
    """
    Create a keyboard with available locations.
    
    Args:
        locations: List of Location objects
        
    Returns:
        InlineKeyboardMarkup with location buttons
    """
    keyboard = []
    
    # Add location buttons (2 per row if possible)
    location_buttons = []
    for location in locations:
        emoji = "🌍"  # Default emoji
        
        # You can customize emojis based on location name or type
        if "آلمان" in location.name or "germany" in location.name.lower():
            emoji = "🇩🇪"
        elif "آمریکا" in location.name or "usa" in location.name.lower() or "united states" in location.name.lower():
            emoji = "🇺🇸"
        elif "هلند" in location.name or "netherlands" in location.name.lower():
            emoji = "🇳🇱"
        elif "فرانسه" in location.name or "france" in location.name.lower():
            emoji = "🇫🇷"
        elif "انگلیس" in location.name or "uk" in location.name.lower() or "united kingdom" in location.name.lower():
            emoji = "🇬🇧"
        elif "کانادا" in location.name or "canada" in location.name.lower():
            emoji = "🇨🇦"
        
        location_buttons.append(
            InlineKeyboardButton(
                text=f"{emoji} {location.name}", 
                callback_data=f"location:{location.id}"
            )
        )
    
    # Arrange buttons in rows of 2
    for i in range(0, len(location_buttons), 2):
        row = location_buttons[i:i+2]
        keyboard.append(row)
    
    # Add back button
    keyboard.append([
        InlineKeyboardButton(text="🔙 بازگشت به انتخاب پلن", callback_data="back_to_plans")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_order_confirmation_keyboard(order_id: int, discount_applied: bool = False) -> InlineKeyboardMarkup:
    """
    Create a keyboard for confirming an order.
    
    Args:
        order_id: The ID of the order
        discount_applied: Whether a discount has already been applied
        
    Returns:
        InlineKeyboardMarkup with confirmation buttons
    """
    keyboard = []
    
    # Add confirm button
    keyboard.append([
        InlineKeyboardButton(text="✅ تأیید و پرداخت", callback_data=f"confirm_order:{order_id}")
    ])
    
    # Add discount button if not already applied
    if not discount_applied:
        keyboard.append([
            InlineKeyboardButton(text="🎁 اعمال کد تخفیف", callback_data=f"apply_discount:{order_id}")
        ])
    
    # Add cancel button
    keyboard.append([
        InlineKeyboardButton(text="❌ انصراف", callback_data="cancel_order")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard) 