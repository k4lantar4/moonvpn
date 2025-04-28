"""
دکمه‌های مدیریت کاربران برای ادمین
"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Optional

from db.models.user import User

def get_user_list_keyboard(users: Optional[List[User]] = None, page: int = 1, total_pages: int = 1) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد نمایش لیست کاربران با دکمه‌های مدیریت
    
    Args:
        users (List[User], optional): لیست کاربران
        page (int): شماره صفحه فعلی
        total_pages (int): تعداد کل صفحات
        
    Returns:
        InlineKeyboardMarkup: کیبورد ساخته شده با دکمه‌های مدیریت کاربران
    """
    builder = InlineKeyboardBuilder()
    
    # اگر لیست کاربران ارائه شده است
    if users:
        # برای هر کاربر یک دکمه مدیریت اضافه می‌کنیم
        for user in users:
            # نمایش اطلاعات کاربر در دکمه
            user_role = "👑 ادمین" if user.role == "admin" else "👤 کاربر" if user.role == "user" else "🌟 سوپر ادمین"
            button_text = f"{user_role} - {user.full_name} - ID: {user.telegram_id}"
            
            builder.button(
                text=button_text,
                callback_data=f"admin:user:manage:{user.id}"
            )
    
    # دکمه‌های پیمایش صفحات
    if total_pages > 1:
        nav_buttons = []
        
        # دکمه صفحه قبل
        if page > 1:
            nav_buttons.append(InlineKeyboardButton(
                text="◀️ صفحه قبل",
                callback_data=f"admin:user:page:{page-1}"
            ))
        
        # نمایش شماره صفحه فعلی
        nav_buttons.append(InlineKeyboardButton(
            text=f"📄 {page} از {total_pages}",
            callback_data="admin:user:current_page"
        ))
        
        # دکمه صفحه بعد
        if page < total_pages:
            nav_buttons.append(InlineKeyboardButton(
                text="▶️ صفحه بعد",
                callback_data=f"admin:user:page:{page+1}"
            ))
            
        # اضافه کردن دکمه‌های پیمایش به کیبورد
        for button in nav_buttons:
            builder.add(button)
    
    # دکمه‌های عملیات کلی
    builder.button(
        text="🔍 جستجوی کاربر",
        callback_data="admin:user:search"
    )
    builder.button(
        text="➕ افزودن ادمین",
        callback_data="admin:user:add_admin"
    )
    builder.button(
        text="🔙 بازگشت به پنل ادمین",
        callback_data="admin:panel"
    )
    
    # تنظیم چیدمان
    if users:
        # یک دکمه در هر ردیف برای کاربران
        # دو دکمه در هر ردیف برای دکمه‌های پیمایش
        # یک دکمه در هر ردیف برای دکمه‌های عملیات کلی
        builder.adjust(1, min(3, total_pages*2-1), 1, 1, 1)
    else:
        # بدون کاربر، فقط نمایش دکمه‌های عملیات
        builder.adjust(1)
    
    return builder.as_markup()

def get_user_manage_buttons(user_id: int) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد دکمه‌های مدیریت برای یک کاربر خاص
    
    Args:
        user_id (int): شناسه کاربر مورد نظر
        
    Returns:
        InlineKeyboardMarkup: کیبورد ساخته شده با دکمه‌های مدیریت کاربر
    """
    builder = InlineKeyboardBuilder()
    
    # دکمه‌های اصلی مدیریت
    builder.button(
        text="🔐 تغییر دسترسی",
        callback_data=f"admin:user:toggle_role:{user_id}"
    )
    builder.button(
        text="💬 ارسال پیام",
        callback_data=f"admin:user:send_message:{user_id}"
    )
    builder.button(
        text="👁️ مشاهده آمار",
        callback_data=f"admin:user:stats:{user_id}"
    )
    builder.button(
        text="📱 مشاهده سرویس‌ها",
        callback_data=f"admin:user:services:{user_id}"
    )
    builder.button(
        text="💰 مشاهده تراکنش‌ها",
        callback_data=f"admin:user:transactions:{user_id}"
    )
    builder.button(
        text="🔒 مسدود کردن",
        callback_data=f"admin:user:block:{user_id}"
    )
    
    # دکمه بازگشت
    builder.button(
        text="🔙 بازگشت به لیست کاربران",
        callback_data="admin:user:list"
    )
    
    # تنظیم چیدمان - ۲ دکمه در هر ردیف، آخرین دکمه در یک ردیف جداگانه
    builder.adjust(2, 2, 2, 1)
    
    return builder.as_markup() 