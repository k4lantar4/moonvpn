"""
دکمه‌های مربوط به فرآیند خرید اشتراک
This file contains buttons and keyboards used in the purchase process.
"""

import logging
from typing import List, Dict, Any, Optional, Union
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

def create_safe_callback(callback_template: str, *args) -> str:
    """
    ایجاد کالبک‌دیتای استاندارد با امکان fail-safe
    
    Args:
        callback_template: قالب کالبک از BUY_CB
        *args: پارامترهای مورد نیاز برای قالب
        
    Returns:
        str: کالبک‌دیتای نهایی
    """
    try:
        # تلاش برای ایجاد کالبک با پارامترها
        return callback_template.format(*args)
    except Exception as e:
        # در صورت خطا، مقدار پیش‌فرض برگردانده می‌شود
        logger.error(f"Error creating callback data with template {callback_template} and args {args}: {e}")
        return BUY_CB["BACK_TO_PLANS"]

def get_plans_keyboard(plans: List[Plan] = None) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد انتخاب پلن با استفاده از سرویس پلن
    
    Args:
        plans (List[Plan], optional): لیست پلن‌ها از PlanService
        
    Returns:
        InlineKeyboardMarkup: کیبورد ساخته شده
    """
    builder = InlineKeyboardBuilder()
    logger.debug(f"ساخت کیبورد انتخاب پلن. تعداد پلن‌ها: {len(plans) if plans else 0}. (Building plans keyboard. Plan count: {len(plans) if plans else 0}.)")
    
    # اضافه کردن دکمه برای هر پلن، اگر لیست پلن‌ها ارائه شده باشد
    if plans and isinstance(plans, list):
        for plan in plans:
            try:
                # بررسی معتبر بودن آبجکت پلن
                if not hasattr(plan, 'id') or not hasattr(plan, 'name'):
                    logger.warning(f"Invalid plan object encountered: {plan}")
                    continue
                
                # قالب‌بندی نمایش قیمت پلن
                price_display = f"{int(plan.price):,} تومان" if hasattr(plan, 'price') and plan.price else "رایگان"
                
                # ساخت متن دکمه
                traffic_gb = getattr(plan, 'traffic_gb', None)
                duration_days = getattr(plan, 'duration_days', None)
                
                # ایجاد متن دکمه با اطلاعات پلن
                button_text_parts = [f"🔹 {plan.name}"]
                
                # اضافه کردن اطلاعات تکمیلی
                details = []
                if traffic_gb:
                    details.append(f"{traffic_gb} GB")
                if duration_days:
                    details.append(f"{duration_days} روز")
                
                if details:
                    button_text_parts.append(f"({' | '.join(details)})")
                
                # اضافه کردن قیمت
                button_text_parts.append(f"- {price_display}")
                
                # ساختن متن کامل دکمه
                button_text = " ".join(button_text_parts)
                
                # ایجاد کالبک‌دیتای امن
                callback_data = create_safe_callback(BUY_CB["SELECT_PLAN"], plan.id)
                
                # اضافه کردن دکمه به کیبورد
                builder.button(
                    text=button_text,
                    callback_data=callback_data
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


def get_location_selection_keyboard(locations: List[Panel] = None) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد انتخاب لوکیشن با استفاده از سرویس لوکیشن
    
    Args:
        locations (List[Panel], optional): لیست پنل‌ها (لوکیشن‌ها) از LocationService
        
    Returns:
        InlineKeyboardMarkup: کیبورد ساخته شده
    """
    builder = InlineKeyboardBuilder()
    logger.debug(f"ساخت کیبورد انتخاب لوکیشن. تعداد لوکیشن‌ها: {len(locations) if locations else 0}. (Building location keyboard. Location count: {len(locations) if locations else 0}.)")
    
    try:
        if locations and isinstance(locations, list):
            # گروه‌بندی پنل‌ها بر اساس لوکیشن برای جلوگیری از تکرار
            location_map = {}
            for panel in locations:
                # بررسی معتبر بودن آبجکت پنل
                if not hasattr(panel, 'id') or not hasattr(panel, 'location'):
                    logger.warning(f"Invalid panel object encountered: {panel}")
                    continue
                
                if panel.location not in location_map:
                    location_map[panel.location] = {
                        "emoji": getattr(panel, "flag_emoji", "🏴"),
                        "id": panel.id
                    }
                    
            # اضافه کردن دکمه برای هر لوکیشن
            for location, data in location_map.items():
                # ایجاد کالبک‌دیتای امن
                callback_data = create_safe_callback(BUY_CB["SELECT_LOCATION"], data['id'])
                
                builder.button(
                    text=f"{data['emoji']} {location}",
                    callback_data=callback_data
                )
        else:
            # اگر لیست لوکیشن‌ها خالی باشد
            builder.button(
                text="⚠️ لوکیشنی یافت نشد",
                callback_data=BUY_CB["BACK_TO_PLANS"]
            )
    except Exception as e:
        logger.error(f"خطا در ساخت کیبورد لوکیشن‌ها: {e}")
        # دکمه خطا
        builder.button(
            text=f"❌ خطای نمایش لوکیشن",
            callback_data=BUY_CB["BACK_TO_PLANS"]
        )
    
    # چینش دکمه‌ها در دو ستون (اگر بیش از یک دکمه وجود داشته باشد)
    builder.adjust(2)
    
    # دکمه بازگشت
    builder.row(InlineKeyboardButton(
        text="🔙 بازگشت به لیست پلن‌ها",
        callback_data=BUY_CB["BACK_TO_PLANS"]
    ))
    
    return builder.as_markup()


def get_plan_selection_keyboard(inbounds: List[Inbound] = None, panel_id: Union[int, str] = None, plan_id: Union[int, str] = None) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد انتخاب اینباند/پروتکل با استفاده از سرویس اینباند
    
    Args:
        inbounds (List[Inbound], optional): لیست اینباندها از InboundService
        panel_id (int, optional): شناسه پنل
        plan_id (int, optional): شناسه پلن
        
    Returns:
        InlineKeyboardMarkup: کیبورد ساخته شده
    """
    builder = InlineKeyboardBuilder()
    logger.debug(f"ساخت کیبورد انتخاب اینباند. تعداد اینباندها: {len(inbounds) if inbounds else 0}. پنل: {panel_id}، پلن: {plan_id}. (Building inbounds keyboard. Inbound count: {len(inbounds) if inbounds else 0}. Panel: {panel_id}, Plan: {plan_id}.)")
    
    try:
        # تبدیل panel_id و plan_id به عدد (در صورت امکان)
        try:
            panel_id = int(panel_id) if panel_id else None
            plan_id = int(plan_id) if plan_id else None
        except (ValueError, TypeError):
            logger.warning(f"Invalid panel_id={panel_id} or plan_id={plan_id}")
            panel_id = None
            plan_id = None
        
        if not all([inbounds, panel_id, plan_id]):
            raise ValueError("Missing required parameters: inbounds, panel_id, plan_id")
        
        # اضافه کردن دکمه برای هر اینباند
        for inbound in inbounds:
            # بررسی معتبر بودن آبجکت اینباند
            if not hasattr(inbound, 'id'):
                logger.warning(f"Invalid inbound object encountered: {inbound}")
                continue
                
            # نمایش پروتکل و پورت با امکان بازیابی امن اطلاعات
            protocol = getattr(inbound, 'protocol', 'UNKNOWN').upper()
            port = getattr(inbound, 'port', 'N/A')
            remark = getattr(inbound, 'remark', '') or getattr(inbound, 'tag', '') or f"Inbound_{inbound.id}"
            
            # ایجاد کالبک‌دیتای امن
            callback_data = create_safe_callback(BUY_CB["SELECT_INBOUND"], plan_id, panel_id, inbound.id)
            
            builder.button(
                text=f"📡 {protocol}@{port} - {remark}",
                callback_data=callback_data
            )
    except Exception as e:
        logger.error(f"خطا در ساخت کیبورد اینباندها: {e}")
        # دکمه خطا با بازگشت امن به مرحله قبل
        back_callback_data = create_safe_callback(BUY_CB["BACK_TO_LOCATIONS"], plan_id) if plan_id else BUY_CB["BACK_TO_PLANS"]
        builder.button(
            text=f"❌ خطای نمایش پروتکل",
            callback_data=back_callback_data
        )
    
    # چینش دکمه‌ها در یک ستون
    builder.adjust(1)
    
    # دکمه بازگشت با کالبک امن
    back_callback_data = create_safe_callback(BUY_CB["BACK_TO_LOCATIONS"], plan_id) if plan_id else BUY_CB["BACK_TO_PLANS"]
    builder.row(InlineKeyboardButton(
        text="🔙 بازگشت به انتخاب لوکیشن",
        callback_data=back_callback_data
    ))
    
    return builder.as_markup()


def confirm_purchase_buttons(plan_id: Union[int, str] = None, panel_id: Union[int, str] = None, inbound_id: Union[int, str] = None) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد تایید نهایی خرید با قابلیت fail-safe
    
    Args:
        plan_id (int, optional): شناسه پلن
        panel_id (int, optional): شناسه پنل
        inbound_id (int, optional): شناسه اینباند
        
    Returns:
        InlineKeyboardMarkup: کیبورد ساخته شده
    """
    builder = InlineKeyboardBuilder()
    logger.debug(f"ساخت کیبورد تایید خرید. پلن: {plan_id}، پنل: {panel_id}، اینباند: {inbound_id}. (Building purchase confirmation keyboard. Plan: {plan_id}, Panel: {panel_id}, Inbound: {inbound_id}.)")
    
    try:
        # تبدیل پارامترها به عدد (در صورت امکان)
        try:
            plan_id = int(plan_id) if plan_id else None
            panel_id = int(panel_id) if panel_id else None
            inbound_id = int(inbound_id) if inbound_id else None
        except (ValueError, TypeError):
            logger.warning(f"Invalid IDs in confirm_purchase_buttons: plan_id={plan_id}, panel_id={panel_id}, inbound_id={inbound_id}")
            raise ValueError("Invalid ID values")
        
        if not all([plan_id, panel_id, inbound_id]):
            raise ValueError("Missing required parameters: plan_id, panel_id, inbound_id")
        
        # دکمه تایید با کالبک امن
        confirm_callback_data = create_safe_callback(
            BUY_CB["CONFIRM_PURCHASE"], plan_id, panel_id, inbound_id
        )
        builder.button(
            text="✅ تایید و پرداخت",
            callback_data=confirm_callback_data
        )
        
        # دکمه بازگشت با کالبک امن
        back_callback_data = create_safe_callback(
            BUY_CB["BACK_TO_INBOUNDS"], plan_id, panel_id
        )
        builder.row(InlineKeyboardButton(
            text="🔙 بازگشت به انتخاب پروتکل",
            callback_data=back_callback_data
        ))
    except Exception as e:
        logger.error(f"خطا در ساخت کیبورد تایید خرید: {e}")
        # دکمه بازگشت به انتخاب پلن در صورت خطا
        builder.button(
            text="❌ خطا در تایید - بازگشت به پلن‌ها",
            callback_data=BUY_CB["BACK_TO_PLANS"]
        )
    
    return builder.as_markup()


def get_payment_keyboard(payment_id: str = None) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد پرداخت با امکان fail-safe
    
    Args:
        payment_id (str, optional): شناسه پرداخت
        
    Returns:
        InlineKeyboardMarkup: کیبورد ساخته شده
    """
    builder = InlineKeyboardBuilder()
    logger.debug(f"ساخت کیبورد پرداخت برای سفارش {payment_id}. (Building payment keyboard for order {payment_id}.)")
    
    try:
        # بررسی معتبر بودن payment_id
        if not payment_id:
            raise ValueError("Payment ID is required")
        
        # دکمه پرداخت با کیف پول با کالبک امن
        wallet_callback_data = create_safe_callback(BUY_CB["PAYMENT_METHOD"], "wallet", payment_id)
        builder.button(
            text="💰 پرداخت با کیف پول",
            callback_data=wallet_callback_data
        )
        
        # دکمه کارت به کارت با کالبک امن
        card_callback_data = create_safe_callback(BUY_CB["PAYMENT_METHOD"], "card", payment_id)
        builder.button(
            text="💳 کارت به کارت",
            callback_data=card_callback_data
        )
        
        # دکمه انصراف از پرداخت
        builder.row(InlineKeyboardButton(
            text="❌ انصراف از پرداخت",
            callback_data=BUY_CB["CANCEL_PAYMENT"]
        ))
    except Exception as e:
        logger.error(f"خطا در ساخت کیبورد پرداخت: {e}")
        # دکمه بازگشت به منوی اصلی در صورت خطا
        builder.button(
            text="🏠 بازگشت به منوی اصلی",
            callback_data="start"
        )
    
    # چینش دکمه‌ها: یک دکمه در هر ردیف
    builder.adjust(1)
    
    return builder.as_markup()

def get_payment_status_keyboard(order_id: Union[int, str] = None) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد وضعیت پرداخت با امکان fail-safe
    
    Args:
        order_id (Union[int, str], optional): شناسه سفارش
        
    Returns:
        InlineKeyboardMarkup: کیبورد ساخته شده
    """
    builder = InlineKeyboardBuilder()
    logger.debug(f"ساخت کیبورد وضعیت پرداخت برای سفارش {order_id}. (Building payment status keyboard for order {order_id}.)")
    
    try:
        # دکمه بررسی وضعیت پرداخت
        builder.button(
            text="🔄 بررسی وضعیت پرداخت",
            callback_data=f"payment:check:{order_id}" if order_id else "start"
        )
        
        # دکمه بازگشت به منوی اصلی
        builder.button(
            text="🏠 بازگشت به منوی اصلی",
            callback_data="start"
        )
    except Exception as e:
        logger.error(f"خطا در ساخت کیبورد وضعیت پرداخت: {e}")
        # دکمه بازگشت به منوی اصلی در صورت خطا
        builder.button(
            text="🏠 منوی اصلی",
            callback_data="start"
        )
    
    # چینش دکمه‌ها: یک دکمه در هر ردیف
    builder.adjust(1)
    
    return builder.as_markup()

# Aliases for backward compatibility
get_locations_keyboard = get_location_selection_keyboard
get_inbounds_keyboard = get_plan_selection_keyboard
get_confirm_purchase_keyboard = confirm_purchase_buttons 