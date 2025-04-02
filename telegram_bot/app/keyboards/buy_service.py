from typing import List, Dict, Any
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Define callback data prefixes
PLAN_CALLBACK_PREFIX = "plan_"
CATEGORY_CALLBACK_PREFIX = "category_"
BACK_TO_CATEGORIES = "back_to_categories"

def generate_plan_keyboard(plans: List[Dict[str, Any]]) -> List[List[InlineKeyboardButton]]:
    """
    Generate keyboard with plan buttons.
    
    Args:
        plans: List of plan dictionaries
        
    Returns:
        List of InlineKeyboardButton rows
    """
    keyboard = []
    
    # Group plans by category
    categories = {}
    for plan in plans:
        category = plan.get("category", "سایر")
        if category not in categories:
            categories[category] = []
        categories[category].append(plan)
    
    # Add a button for each category
    for category in categories:
        keyboard.append([
            InlineKeyboardButton(
                f"📁 {category}", 
                callback_data=f"{CATEGORY_CALLBACK_PREFIX}{category}"
            )
        ])
    
    # Add cancel button
    keyboard.append([
        InlineKeyboardButton("❌ انصراف", callback_data="cancel")
    ])
    
    return keyboard

def generate_category_plans_keyboard(plans: List[Dict[str, Any]], category: str) -> List[List[InlineKeyboardButton]]:
    """
    Generate keyboard with plans for a specific category.
    
    Args:
        plans: List of plan dictionaries
        category: Category name to filter by
        
    Returns:
        List of InlineKeyboardButton rows
    """
    keyboard = []
    
    # Filter plans by category
    category_plans = [p for p in plans if p.get("category", "سایر") == category]
    
    # Sort plans by duration (shortest first)
    category_plans.sort(key=lambda p: p.get("duration_days", 0))
    
    # Add a button for each plan
    for plan in category_plans:
        plan_id = plan.get("id")
        name = plan.get("name", "نامشخص")
        price = plan.get("price", 0)
        duration = plan.get("duration_days", "?")
        data_limit = plan.get("data_limit_gb", "?")
        
        # Format display text
        formatted_price = f"{int(price):,}" if price else "0"
        button_text = f"{name} - {formatted_price} تومان ({duration} روز)"
        
        keyboard.append([
            InlineKeyboardButton(
                button_text, 
                callback_data=f"{PLAN_CALLBACK_PREFIX}{plan_id}"
            )
        ])
    
    # Add back button
    keyboard.append([
        InlineKeyboardButton("🔙 بازگشت به دسته‌ها", callback_data=BACK_TO_CATEGORIES)
    ])
    
    # Add cancel button
    keyboard.append([
        InlineKeyboardButton("❌ انصراف", callback_data="cancel")
    ])
    
    return keyboard 