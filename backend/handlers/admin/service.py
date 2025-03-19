"""
Service plan management handlers.

This module contains handlers for managing VPN service plans.
"""

from typing import Dict, Any, List

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, CallbackQueryHandler, ConversationHandler

from utils import get_text, format_number, format_date
from decorators import require_admin
from api_client import get_plans, get_plan, update_plan, delete_plan, create_plan
from .constants import SELECTING_SERVICE, ADMIN_MENU, SERVICE_MANAGEMENT

@require_admin
async def service_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show list of service plans."""
    query = update.callback_query
    await query.answer()
    
    language_code = context.user_data.get("language", "en")
    
    # Get service plans
    plans = get_plans()
    
    if not plans:
        message = "🎯 پلن‌های سرویس\n\nهیچ پلن سرویسی یافت نشد."
        keyboard = [
            [
                InlineKeyboardButton(
                    "➕ افزودن پلن",
                    callback_data="service_add"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 بازگشت به پنل مدیریت",
                    callback_data=ADMIN_MENU
                )
            ]
        ]
    else:
        message = "🎯 پلن‌های سرویس\n\n"
        
        # Add plan info to message
        for i, plan in enumerate(plans):
            # Get plan status emoji
            status_emoji = "✅" if plan.get("is_active", True) else "⛔"
            
            # Add plan info
            message += f"{i+1}. {status_emoji} *{plan.get('name')}*\n"
            message += f"   ⏱️ {plan.get('duration')} روز\n"
            message += f"   💾 {format_number(plan.get('data_limit', 0))} GB\n"
            message += f"   💰 {format_number(plan.get('price', 0))} تومان\n\n"
        
        # Create keyboard with plan buttons
        keyboard = []
        for i, plan in enumerate(plans):
            keyboard.append([
                InlineKeyboardButton(
                    f"{i+1}. {plan.get('name')}",
                    callback_data=f"service_details:{plan.get('id')}"
                )
            ])
        
        # Add management buttons
        keyboard.append([
            InlineKeyboardButton(
                "➕ افزودن پلن",
                callback_data="service_add"
            )
        ])
    
        # Add back button
        keyboard.append([
            InlineKeyboardButton(
                "🔙 بازگشت به پنل مدیریت",
                callback_data=ADMIN_MENU
            )
        ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    
    return SELECTING_SERVICE

@require_admin
async def service_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show service plan details."""
    query = update.callback_query
    await query.answer()
    
    # Get plan ID from callback data
    plan_id = int(query.data.split(":")[-1])
    
    # Get plan details
    plan = get_plan(plan_id)
    
    if not plan:
        await query.edit_message_text(
            "❌ پلن سرویس مورد نظر یافت نشد.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به لیست پلن‌ها", callback_data=SERVICE_MANAGEMENT)]
            ])
        )
        return SELECTING_SERVICE
    
    # Format plan details
    name = plan.get("name", "")
    description = plan.get("description", "")
    duration = plan.get("duration", 0)
    data_limit = format_number(plan.get("data_limit", 0))
    price = format_number(plan.get("price", 0))
    discount_price = format_number(plan.get("discount_price", 0))
    server_locations = plan.get("server_locations", [])
    server_locations_str = ", ".join(server_locations) if server_locations else "همه سرورها"
    feature_list = plan.get("features", [])
    features = "\n".join([f"• {feature}" for feature in feature_list]) if feature_list else "بدون ویژگی خاص"
    
    # Status and availability
    is_active = "فعال ✅" if plan.get("is_active", True) else "غیرفعال ❌"
    is_featured = "بله ⭐" if plan.get("is_featured", False) else "خیر"
    
    # Stats
    active_users = plan.get("active_users_count", 0)
    total_sold = plan.get("total_sold", 0)
    
    # Create message
    message = (
        f"🎯 *جزئیات پلن سرویس*\n\n"
        f"📋 *اطلاعات پایه*\n"
        f"• نام: {name}\n"
        f"• توضیحات: {description}\n"
        f"• مدت زمان: {duration} روز\n"
        f"• حجم دیتا: {data_limit} GB\n"
        f"• قیمت: {price} تومان\n"
        f"• قیمت با تخفیف: {discount_price if discount_price != price else 'بدون تخفیف'}\n"
        f"• وضعیت: {is_active}\n"
        f"• ویژه: {is_featured}\n\n"
        f"🌍 *سرورها*\n"
        f"• مکان‌ها: {server_locations_str}\n\n"
        f"✨ *ویژگی‌ها*\n"
        f"{features}\n\n"
        f"📊 *آمار*\n"
        f"• کاربران فعال: {active_users}\n"
        f"• کل فروش: {total_sold}"
    )
    
    # Create keyboard
    keyboard = [
        [
            InlineKeyboardButton(
                "✅ فعال کردن" if not plan.get("is_active", True) else "❌ غیرفعال کردن", 
                callback_data=f"service_toggle:{plan_id}"
            ),
            InlineKeyboardButton(
                "✏️ ویرایش", 
                callback_data=f"service_edit:{plan_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "⭐ ویژه کردن" if not plan.get("is_featured", False) else "❌ حذف ویژه", 
                callback_data=f"service_feature_toggle:{plan_id}"
            ),
            InlineKeyboardButton(
                "❌ حذف پلن", 
                callback_data=f"service_delete:{plan_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 بازگشت به لیست پلن‌ها", 
                callback_data=SERVICE_MANAGEMENT
            )
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    
    return SELECTING_SERVICE

# Define add service plan function
@require_admin
async def service_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start process to add a new service plan."""
    query = update.callback_query
    await query.answer()
    
    # Set state to collect service plan data
    context.user_data["service_plan"] = {
        "step": "name",
        "data": {}
    }
    
    message = (
        "➕ *افزودن پلن سرویس جدید*\n\n"
        "لطفاً نام پلن سرویس را وارد کنید:"
    )
    
    keyboard = [
        [
            InlineKeyboardButton(
                "🔙 انصراف", 
                callback_data=SERVICE_MANAGEMENT
            )
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    
    # Return next conversation state
    return SELECTING_SERVICE

# Placeholder for other service management functions
# These would be implemented similar to the account and payment handlers

# Define handlers list to be imported in __init__.py
handlers = [
    CallbackQueryHandler(service_details, pattern="^service_details:"),
    CallbackQueryHandler(service_add, pattern="^service_add$"),
    CallbackQueryHandler(service_list, pattern="^service_menu$"),
]

# Create a class to hold the handlers for easier import
class service_handlers:
    handlers = handlers
    service_list = service_list 