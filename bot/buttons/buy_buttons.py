"""
دکمه‌های مربوط به فرآیند خرید اشتراک
This file contains buttons and keyboards used in the purchase process.
"""

import logging
from typing import List, Dict, Any, Optional
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from db.models import Plan, Panel, Inbound

logger = logging.getLogger(__name__)

# استاندارد کالبک‌های خرید
BUY_CB = {
    "SELECT_PLAN": "buy:plan:{}",       # buy:plan:plan_id
    "SELECT_LOCATION": "buy:loc:{}",    # buy:loc:panel_id
    "SELECT_INBOUND": "buy:inb:{}:{}:{}", # buy:inb:plan_id:panel_id:inbound_id
    "CONFIRM_PURCHASE": "buy:confirm:{}:{}:{}", # buy:confirm:plan_id:panel_id:inbound_id
    "PAYMENT_METHOD": "buy:pay:{}:{}", # buy:pay:method:payment_id
    "REFRESH_PLANS": "buy:refresh:plans",
    "BACK_TO_PLANS": "buy:back:plans",
    "BACK_TO_LOCATIONS": "buy:back:loc:{}",  # buy:back:loc:plan_id
    "BACK_TO_INBOUNDS": "buy:back:inb:{}:{}", # buy:back:inb:plan_id:panel_id
    "CANCEL_PAYMENT": "buy:cancel:payment"
}

def get_plans_keyboard(plans: List[Plan] = None) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد انتخاب پلن
    
    Args:
        plans (List[Plan], optional): لیست پلن‌ها.
        
    Returns:
        InlineKeyboardMarkup: کیبورد ساخته شده
    """
    builder = InlineKeyboardBuilder()
    logger.debug(f"ساخت کیبورد انتخاب پلن. تعداد پلن‌ها: {len(plans) if plans else 0}. (Building plans keyboard. Plan count: {len(plans) if plans else 0}.)")
    
    # اضافه کردن دکمه برای هر پلن، اگر لیست پلن‌ها ارائه شده باشد
    if plans:
        for plan in plans:
            try:
                # قالب‌بندی نمایش قیمت پلن
                price_display = f"{int(plan.price):,} تومان" if plan.price else "رایگان"
                
                # ساخت متن دکمه
                if hasattr(plan, 'duration_days') and hasattr(plan, 'traffic_gb'):
                    traffic_gb = getattr(plan, 'traffic_gb', None)
                    duration_days = getattr(plan, 'duration_days', None)
                    if duration_days and traffic_gb:
                        button_text = f"🔹 {plan.name} ({traffic_gb} GB | {duration_days} روز) - {price_display}"
                    elif duration_days:
                        button_text = f"🔹 {plan.name} ({duration_days} روز) - {price_display}"
                    elif traffic_gb:
                        button_text = f"🔹 {plan.name} ({traffic_gb} GB) - {price_display}"
                    else:
                        button_text = f"🔹 {plan.name} - {price_display}"
                else:
                    button_text = f"🔹 {plan.name} - {price_display}"
                    
                builder.button(
                    text=button_text,
                    callback_data=BUY_CB["SELECT_PLAN"].format(plan.id)
                )
            except Exception as e:
                logger.error(f"خطا در ساخت دکمه برای پلن {getattr(plan, 'id', 'unknown')}: {e}")
                # دکمه خطا که به صفحه پلن‌ها برمی‌گردد
                builder.button(
                    text=f"❌ خطای نمایش پلن",
                    callback_data=BUY_CB["REFRESH_PLANS"]
                )
    
    # دکمه بروزرسانی لیست
    builder.button(text="🔄 بروزرسانی لیست", callback_data=BUY_CB["REFRESH_PLANS"])
    
    # دکمه بازگشت به منوی اصلی
    builder.button(text="🏠 منوی اصلی", callback_data="start")
    
    # تنظیم چیدمان: یک دکمه در هر ردیف
    builder.adjust(1)
    
    return builder.as_markup()


def get_location_selection_keyboard(locations: List[Panel]) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد انتخاب لوکیشن با استفاده از سرویس لوکیشن
    
    Args:
        locations (List[Panel]): لیست پنل‌ها (لوکیشن‌ها)
        
    Returns:
        InlineKeyboardMarkup: کیبورد ساخته شده
    """
    builder = InlineKeyboardBuilder()
    logger.debug(f"ساخت کیبورد انتخاب لوکیشن. تعداد لوکیشن‌ها: {len(locations)}. (Building location keyboard. Location count: {len(locations)}.)")
    
    try:
        # گروه‌بندی پنل‌ها بر اساس لوکیشن برای جلوگیری از تکرار
        location_map = {}
        for panel in locations:
            if panel.location not in location_map:
                location_map[panel.location] = {
                    "emoji": getattr(panel, "flag_emoji", "🏴"),
                    "id": panel.id
                }
                
        # اضافه کردن دکمه برای هر لوکیشن
        for location, data in location_map.items():
            builder.button(
                text=f"{data['emoji']} {location}",
                callback_data=BUY_CB["SELECT_LOCATION"].format(data['id'])
            )
    except Exception as e:
        logger.error(f"خطا در ساخت کیبورد لوکیشن‌ها: {e}")
        # دکمه خطا
        builder.button(
            text=f"❌ خطای نمایش لوکیشن",
            callback_data=BUY_CB["BACK_TO_PLANS"]
        )
    
    # چینش دکمه‌ها در دو ستون
    builder.adjust(2)
    
    # دکمه بازگشت
    builder.row(InlineKeyboardButton(
        text="🔙 بازگشت به لیست پلن‌ها",
        callback_data=BUY_CB["BACK_TO_PLANS"]
    ))
    
    return builder.as_markup()


def get_plan_selection_keyboard(inbounds: List[Inbound], panel_id: int, plan_id: int) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد انتخاب اینباند/پروتکل
    
    Args:
        inbounds (List[Inbound]): لیست اینباندها
        panel_id (int): شناسه پنل
        plan_id (int): شناسه پلن
        
    Returns:
        InlineKeyboardMarkup: کیبورد ساخته شده
    """
    builder = InlineKeyboardBuilder()
    logger.debug(f"ساخت کیبورد انتخاب اینباند. تعداد اینباندها: {len(inbounds)}. پنل: {panel_id}، پلن: {plan_id}. (Building inbounds keyboard. Inbound count: {len(inbounds)}. Panel: {panel_id}, Plan: {plan_id}.)")
    
    try:
        # اضافه کردن دکمه برای هر اینباند
        for inbound in inbounds:
            # نمایش پروتکل و پورت با امکان بازیابی امن اطلاعات
            protocol = getattr(inbound, 'protocol', 'UNKNOWN').upper()
            port = getattr(inbound, 'port', 'N/A')
            remark = getattr(inbound, 'remark', '') or getattr(inbound, 'tag', '') or f"Inbound_{inbound.id}"
            
            builder.button(
                text=f"📡 {protocol}@{port} - {remark}",
                callback_data=BUY_CB["SELECT_INBOUND"].format(plan_id, panel_id, inbound.id)
            )
    except Exception as e:
        logger.error(f"خطا در ساخت کیبورد اینباندها: {e}")
        # دکمه خطا
        builder.button(
            text=f"❌ خطای نمایش پروتکل",
            callback_data=BUY_CB["BACK_TO_LOCATIONS"].format(plan_id)
        )
    
    # چینش دکمه‌ها در یک ستون
    builder.adjust(1)
    
    # دکمه بازگشت
    builder.row(InlineKeyboardButton(
        text="🔙 بازگشت به انتخاب لوکیشن",
        callback_data=BUY_CB["BACK_TO_LOCATIONS"].format(plan_id)
    ))
    
    return builder.as_markup()


def confirm_purchase_buttons(plan_id: int, panel_id: int, inbound_id: int) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد تایید نهایی خرید
    
    Args:
        plan_id (int): شناسه پلن
        panel_id (int): شناسه پنل
        inbound_id (int): شناسه اینباند
        
    Returns:
        InlineKeyboardMarkup: کیبورد ساخته شده
    """
    builder = InlineKeyboardBuilder()
    logger.debug(f"ساخت کیبورد تایید خرید. پلن: {plan_id}، پنل: {panel_id}، اینباند: {inbound_id}. (Building purchase confirmation keyboard. Plan: {plan_id}, Panel: {panel_id}, Inbound: {inbound_id}.)")
    
    try:
        # دکمه تایید
        builder.button(
            text="✅ تایید و پرداخت",
            callback_data=BUY_CB["CONFIRM_PURCHASE"].format(plan_id, panel_id, inbound_id)
        )
        
        # دکمه بازگشت
        builder.row(InlineKeyboardButton(
            text="🔙 بازگشت به انتخاب پروتکل",
            callback_data=BUY_CB["BACK_TO_INBOUNDS"].format(plan_id, panel_id)
        ))
    except Exception as e:
        logger.error(f"خطا در ساخت کیبورد تایید خرید: {e}")
        # دکمه بازگشت به انتخاب پلن
        builder.button(
            text="❌ خطا در تایید - بازگشت به پلن‌ها",
            callback_data=BUY_CB["BACK_TO_PLANS"]
        )
    
    return builder.as_markup()


def get_payment_keyboard(payment_id: str) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد پرداخت با امکان fail-safe
    
    Args:
        payment_id (str): شناسه پرداخت
        
    Returns:
        InlineKeyboardMarkup: کیبورد ساخته شده
    """
    builder = InlineKeyboardBuilder()
    logger.debug(f"ساخت کیبورد پرداخت برای سفارش {payment_id}. (Building payment keyboard for order {payment_id}.)")
    
    try:
        # دکمه پرداخت
        builder.button(
            text="💳 پرداخت آنلاین",
            callback_data=BUY_CB["PAYMENT_METHOD"].format("online", payment_id)
        )
        
        # دکمه کارت به کارت
        builder.button(
            text="💸 کارت به کارت",
            callback_data=BUY_CB["PAYMENT_METHOD"].format("card", payment_id)
        )
        
        # دکمه پرداخت از کیف پول
        builder.button(
            text="💰 پرداخت از کیف پول",
            callback_data=BUY_CB["PAYMENT_METHOD"].format("wallet", payment_id)
        )
    except Exception as e:
        logger.error(f"خطا در ساخت کیبورد پرداخت: {e}")
        # دکمه خطا
        builder.button(
            text=f"❌ خطا در سیستم پرداخت",
            callback_data=BUY_CB["BACK_TO_PLANS"]
        )
    
    # چینش دکمه‌ها در یک ستون
    builder.adjust(1)
    
    # دکمه بازگشت
    builder.row(InlineKeyboardButton(
        text="🔙 انصراف",
        callback_data=BUY_CB["CANCEL_PAYMENT"]
    ))
    
    return builder.as_markup()

# Aliases for backward compatibility
get_locations_keyboard = get_location_selection_keyboard
get_inbounds_keyboard = get_plan_selection_keyboard
get_confirm_purchase_keyboard = confirm_purchase_buttons 