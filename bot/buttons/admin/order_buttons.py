"""
دکمه‌های مدیریت سفارش‌ها برای ادمین
"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Optional

from db.models.order import Order

def get_order_list_keyboard(orders: Optional[List[Order]] = None, page: int = 1, total_pages: int = 1) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد نمایش لیست سفارش‌ها با دکمه‌های مدیریت
    
    Args:
        orders (List[Order], optional): لیست سفارش‌ها
        page (int): شماره صفحه فعلی
        total_pages (int): تعداد کل صفحات
        
    Returns:
        InlineKeyboardMarkup: کیبورد ساخته شده با دکمه‌های مدیریت سفارش‌ها
    """
    builder = InlineKeyboardBuilder()
    
    # اگر لیست سفارش‌ها ارائه شده است
    if orders:
        # برای هر سفارش یک دکمه مدیریت اضافه می‌کنیم
        for order in orders:
            # نمایش اطلاعات سفارش در دکمه
            status_emoji = "✅" if order.status == "completed" else "⏳" if order.status == "pending" else "❌"
            button_text = f"{status_emoji} سفارش #{order.id} - {order.amount:,} تومان"
            
            builder.button(
                text=button_text,
                callback_data=f"admin:order:manage:{order.id}"
            )
    
    # دکمه‌های پیمایش صفحات
    if total_pages > 1:
        nav_buttons = []
        
        # دکمه صفحه قبل
        if page > 1:
            nav_buttons.append(InlineKeyboardButton(
                text="◀️ صفحه قبل",
                callback_data=f"admin:order:page:{page-1}"
            ))
        
        # نمایش شماره صفحه فعلی
        nav_buttons.append(InlineKeyboardButton(
            text=f"📄 {page} از {total_pages}",
            callback_data="admin:order:current_page"
        ))
        
        # دکمه صفحه بعد
        if page < total_pages:
            nav_buttons.append(InlineKeyboardButton(
                text="▶️ صفحه بعد",
                callback_data=f"admin:order:page:{page+1}"
            ))
            
        # اضافه کردن دکمه‌های پیمایش به کیبورد
        for button in nav_buttons:
            builder.add(button)
    
    # دکمه‌های فیلتر
    builder.button(
        text="🟢 سفارش‌های تکمیل شده",
        callback_data="admin:order:filter:completed"
    )
    builder.button(
        text="🟡 سفارش‌های در انتظار",
        callback_data="admin:order:filter:pending"
    )
    builder.button(
        text="🔴 سفارش‌های لغو شده",
        callback_data="admin:order:filter:cancelled"
    )
    builder.button(
        text="🔄 همه سفارش‌ها",
        callback_data="admin:order:filter:all"
    )
    
    # دکمه بازگشت
    builder.button(
        text="🔙 بازگشت به پنل ادمین",
        callback_data="admin:panel"
    )
    
    # تنظیم چیدمان
    if orders:
        # یک دکمه در هر ردیف برای سفارش‌ها
        # دو یا سه دکمه در یک ردیف برای دکمه‌های پیمایش
        # دو دکمه در هر ردیف برای فیلترها
        # یک دکمه در ردیف آخر برای بازگشت
        builder.adjust(1, min(3, total_pages*2-1), 2, 2, 1)
    else:
        # بدون سفارش، فقط نمایش دکمه‌های فیلتر و بازگشت
        builder.adjust(2, 2, 1)
    
    return builder.as_markup()

def get_order_manage_buttons(order_id: int) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد دکمه‌های مدیریت برای یک سفارش خاص
    
    Args:
        order_id (int): شناسه سفارش مورد نظر
        
    Returns:
        InlineKeyboardMarkup: کیبورد ساخته شده با دکمه‌های مدیریت سفارش
    """
    builder = InlineKeyboardBuilder()
    
    # دکمه‌های اصلی مدیریت
    builder.button(
        text="✅ تایید سفارش",
        callback_data=f"admin:order:approve:{order_id}"
    )
    builder.button(
        text="❌ رد سفارش",
        callback_data=f"admin:order:reject:{order_id}"
    )
    builder.button(
        text="👤 اطلاعات کاربر",
        callback_data=f"admin:order:user_info:{order_id}"
    )
    builder.button(
        text="💰 جزئیات پرداخت",
        callback_data=f"admin:order:payment_details:{order_id}"
    )
    
    # دکمه بازگشت
    builder.button(
        text="🔙 بازگشت به لیست سفارش‌ها",
        callback_data="admin:order:list"
    )
    
    # تنظیم چیدمان - ۲ دکمه در هر ردیف، آخرین دکمه در یک ردیف جداگانه
    builder.adjust(2, 2, 1)
    
    return builder.as_markup() 