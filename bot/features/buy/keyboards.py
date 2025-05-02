"""
کیبوردهای مربوط به فرآیند خرید اشتراک
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
    builder.button(text="🏠 منوی اصلی", callback_data="start") # TODO: Use common callback constant
    
    # تنظیم چیدمان: یک دکمه در هر ردیف
    builder.adjust(1)
    
    return builder.as_markup()


def get_location_selection_keyboard(locations: List[Panel] = None, plan_id: Union[int, str] = None) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد انتخاب لوکیشن با استفاده از سرویس لوکیشن
    
    Args:
        locations (List[Panel], optional): لیست پنل‌ها (لوکیشن‌ها)
        plan_id (Union[int, str], optional): شناسه پلن برای دکمه بازگشت
        
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
                if not hasattr(panel, 'id') or not hasattr(panel, 'location_name'):
                    logger.warning(f"Invalid panel object encountered: {panel}")
                    continue
                
                if panel.location_name not in location_map:
                    location_map[panel.location_name] = {
                        "emoji": getattr(panel, "flag_emoji", "🏴"),
                        "id": panel.id # Note: Using the first panel's ID for the location
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
        inbounds (List[Inbound], optional): لیست اینباندها
        panel_id (Union[int, str], optional): شناسه پنل
        plan_id (Union[int, str], optional): شناسه پلن
        
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
    ساخت کیبورد تایید خرید نهایی با اطلاعات پلن، پنل و اینباند
    
    Args:
        plan_id (Union[int, str]): شناسه پلن
        panel_id (Union[int, str]): شناسه پنل (لوکیشن)
        inbound_id (Union[int, str]): شناسه اینباند
        
    Returns:
        InlineKeyboardMarkup: کیبورد تایید خرید
    """
    builder = InlineKeyboardBuilder()
    logger.debug(f"ساخت کیبورد تایید خرید نهایی. پلن: {plan_id}, پنل: {panel_id}, اینباند: {inbound_id}. (Building confirm purchase keyboard. Plan: {plan_id}, Panel: {panel_id}, Inbound: {inbound_id}.)")
    
    try:
        # تبدیل IDها به عدد در صورت امکان
        plan_id = int(plan_id) if plan_id else None
        panel_id = int(panel_id) if panel_id else None
        inbound_id = int(inbound_id) if inbound_id else None
        
        if not all([plan_id, panel_id, inbound_id]):
            raise ValueError("Missing required parameters: plan_id, panel_id, inbound_id")
            
        # ایجاد کالبک‌دیتای امن برای تایید
        confirm_callback = create_safe_callback(BUY_CB["CONFIRM_PURCHASE"], plan_id, panel_id, inbound_id)
        builder.button(
            text="✅ تایید نهایی و ادامه",
            callback_data=confirm_callback
        )
        
    except Exception as e:
        logger.error(f"خطا در ساخت دکمه تایید خرید: {e}")
        # دکمه خطا
        confirm_callback = create_safe_callback(BUY_CB["BACK_TO_INBOUNDS"], plan_id, panel_id)
        builder.button(
            text="❌ خطا در تایید",
            callback_data=confirm_callback
        )
        
    # دکمه بازگشت با کالبک امن
    back_callback_data = create_safe_callback(BUY_CB["BACK_TO_INBOUNDS"], plan_id, panel_id)
    builder.button(
        text="🔙 بازگشت به انتخاب پروتکل",
        callback_data=back_callback_data
    )
    
    # چینش دکمه‌ها
    builder.adjust(1)
    
    return builder.as_markup()


def get_payment_keyboard(payment_id: str = None) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد انتخاب روش پرداخت
    
    Args:
        payment_id (str, optional): شناسه پرداخت یا سفارش
        
    Returns:
        InlineKeyboardMarkup: کیبورد ساخته شده
    """
    builder = InlineKeyboardBuilder()
    logger.debug(f"ساخت کیبورد انتخاب روش پرداخت. شناسه: {payment_id}. (Building payment keyboard. ID: {payment_id}.)")
    
    # بررسی وجود شناسه پرداخت
    if not payment_id:
        logger.warning("شناسه پرداخت (order_id) برای ساخت کیبورد پرداخت وجود ندارد.")
        # دکمه بازگشت کلی
        builder.button(text="🔙 بازگشت", callback_data=BUY_CB["BACK_TO_PLANS"])
        return builder.as_markup()
        
    try:
        # دکمه پرداخت با درگاه (آینده)
        builder.button(
            text="💳 پرداخت آنلاین (به زودی)",
            # callback_data=f"pay:online:{payment_id}"
            callback_data="pay:online:coming_soon"
        )
        
        # دکمه پرداخت کارت به کارت
        builder.button(
            text="💸 کارت به کارت / ثبت رسید",
            callback_data=f"pay:card:{payment_id}"
        )
        
        # دکمه پرداخت با کیف پول
        builder.button(
            text="💰 پرداخت از کیف پول",
            callback_data=f"pay:wallet:{payment_id}"
        )
        
    except Exception as e:
        logger.error(f"خطا در ساخت دکمه‌های روش پرداخت برای {payment_id}: {e}")
        # دکمه خطا
        builder.button(
            text="❌ خطای نمایش روش پرداخت",
            callback_data=BUY_CB["BACK_TO_PLANS"]
        )
        
    # دکمه انصراف از پرداخت
    builder.button(text="❌ انصراف و بازگشت به پلن‌ها", callback_data=BUY_CB["CANCEL_PAYMENT"])
    
    # چینش دکمه‌ها
    builder.adjust(1)
    
    return builder.as_markup()


def get_payment_status_keyboard(order_id: Union[int, str] = None) -> InlineKeyboardMarkup:
    """
    کیبورد نمایش وضعیت پس از پرداخت (موفق یا ناموفق)
    
    Args:
        order_id (Union[int, str]): شناسه سفارش
        
    Returns:
        InlineKeyboardMarkup: کیبورد وضعیت پرداخت
    """
    builder = InlineKeyboardBuilder()
    logger.debug(f"ساخت کیبورد وضعیت پرداخت برای سفارش {order_id}. (Building payment status keyboard for order {order_id}.)")
    
    # دکمه مشاهده اکانت‌ها
    builder.button(text="📱 مشاهده اکانت‌های من", callback_data="my_accounts")
    
    # دکمه بازگشت به منوی اصلی
    builder.button(text="🏠 بازگشت به منوی اصلی", callback_data="start") # TODO: Use common callback constant
    
    builder.adjust(1)
    return builder.as_markup() 