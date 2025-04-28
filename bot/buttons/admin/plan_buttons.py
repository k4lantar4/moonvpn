"""
دکمه‌های مدیریت پلن‌ها برای ادمین
"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Optional

from db.models.plan import Plan

def get_plan_list_keyboard(plans: Optional[List[Plan]] = None) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد نمایش لیست پلن‌ها با دکمه‌های مدیریت
    
    Args:
        plans (List[Plan], optional): لیست پلن‌ها
        
    Returns:
        InlineKeyboardMarkup: کیبورد ساخته شده با دکمه‌های مدیریت پلن‌ها
    """
    builder = InlineKeyboardBuilder()
    
    # اگر لیست پلن‌ها ارائه شده است
    if plans:
        # برای هر پلن یک دکمه مدیریت اضافه می‌کنیم
        for plan in plans:
            # نمایش اطلاعات پلن در دکمه
            status_emoji = "✅" if plan.is_active else "❌"
            button_text = f"{status_emoji} {plan.name} - {plan.duration} روز - {plan.data_limit} GB"
            
            builder.button(
                text=button_text,
                callback_data=f"admin:plan:manage:{plan.id}"
            )
    
    # دکمه‌های عملیات کلی
    builder.button(
        text="➕ ایجاد پلن جدید",
        callback_data="admin:plan:create"
    )
    builder.button(
        text="🔙 بازگشت به پنل ادمین",
        callback_data="admin:panel"
    )
    
    # تنظیم چیدمان
    if plans:
        # یک دکمه در هر ردیف برای پلن‌ها
        # یک دکمه در هر ردیف برای دکمه‌های عملیات کلی
        builder.adjust(1)
    else:
        # بدون پلن، فقط نمایش دکمه‌های عملیات
        builder.adjust(1)
    
    return builder.as_markup()

def get_plan_manage_buttons(plan_id: int) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد دکمه‌های مدیریت برای یک پلن خاص
    
    Args:
        plan_id (int): شناسه پلن مورد نظر
        
    Returns:
        InlineKeyboardMarkup: کیبورد ساخته شده با دکمه‌های مدیریت پلن
    """
    builder = InlineKeyboardBuilder()
    
    # دکمه‌های اصلی مدیریت
    builder.button(
        text="⚙️ ویرایش",
        callback_data=f"admin:plan:edit:{plan_id}"
    )
    builder.button(
        text="🔀 تغییر وضعیت",
        callback_data=f"admin:plan:toggle_status:{plan_id}"
    )
    builder.button(
        text="🗑️ حذف",
        callback_data=f"admin:plan:delete:{plan_id}"
    )
    
    # دکمه بازگشت
    builder.button(
        text="🔙 بازگشت به لیست پلن‌ها",
        callback_data="admin:plan:list"
    )
    
    # تنظیم چیدمان - ۲ دکمه در هر ردیف، آخرین دکمه در یک ردیف جداگانه
    builder.adjust(2, 1, 1)
    
    return builder.as_markup() 