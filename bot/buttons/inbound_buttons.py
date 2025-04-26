"""
دکمه‌های مربوط به انتخاب inbound در فرایند خرید و مدیریت اینباندها
"""

from typing import List, Dict, Any, Optional
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import json
import logging

from db.models.panel import Panel
from db.models.inbound import Inbound

logger = logging.getLogger(__name__)

def get_panel_locations_keyboard(panels: List[Panel]) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد انتخاب لوکیشن پنل‌ها
    
    Args:
        panels (List[Panel]): لیست آبجکت‌های پنل
        
    Returns:
        InlineKeyboardMarkup: کیبورد ساخته شده
    """
    keyboard = []
    
    # دکمه‌های انتخاب لوکیشن
    for panel in panels:
        keyboard.append([
            InlineKeyboardButton(
                text=f"{panel.flag_emoji} {panel.location_name}",
                callback_data=f"select_location:{panel.id}"
            )
        ])
    
    # دکمه بازگشت
    keyboard.append([
        InlineKeyboardButton(
            text="🔙 بازگشت به لیست پلن‌ها",
            callback_data="back_to_plans"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_inbounds_keyboard(inbounds: List[Inbound], panel_id: int, plan_id: int) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد انتخاب inbound
    
    Args:
        inbounds (List[Inbound]): لیست آبجکت‌های اینباند
        panel_id (int): شناسه پنل
        plan_id (int): شناسه پلن
        
    Returns:
        InlineKeyboardMarkup: کیبورد ساخته شده
    """
    keyboard = []
    
    # دکمه‌های انتخاب inbound
    for inbound in inbounds:
        # نمایش تعداد کاربران در صورت وجود محدودیت
        client_info = ""
        if inbound.max_clients:
            client_count = len(inbound.client_accounts) if hasattr(inbound, 'client_accounts') else 0
            client_info = f" ({client_count}/{inbound.max_clients})"
        
        keyboard.append([
            InlineKeyboardButton(
                text=f"{inbound.protocol.upper()}@{inbound.port}{client_info}",
                callback_data=f"select_inbound:{plan_id}:{panel_id}:{inbound.id}"
            )
        ])
    
    # دکمه بازگشت
    keyboard.append([
        InlineKeyboardButton(
            text="🔙 بازگشت به لیست لوکیشن‌ها",
            callback_data=f"back_to_locations:{plan_id}"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_panel_inbounds_keyboard(inbounds: List[Inbound], panel_id: int) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد دکمه‌های مدیریت برای اینباندهای یک پنل (دکمه کلی مدیریت)

    Args:
        inbounds (List[Inbound]): لیست آبجکت‌های اینباند مدل SQLAlchemy.
        panel_id (int): شناسه پنلی که اینباندها به آن تعلق دارند.

    Returns:
        InlineKeyboardMarkup: کیبورد ساخته شده.
    """
    builder = InlineKeyboardBuilder()
    logger.debug(f"شروع ساخت کیبورد اینباندها برای پنل {panel_id}. تعداد اینباندها: {len(inbounds)}. (Starting to build inbounds keyboard for panel {panel_id}. Number of inbounds: {len(inbounds)}.)")
    
    for inbound in inbounds:
        try:
            # مطمئن می‌شویم که inbound یک آبجکت واقعی Inbound است
            if not isinstance(inbound, Inbound):
                logger.warning(f"آبجکت inbound از نوع Inbound نیست. نوع: {type(inbound)}. (Inbound object is not of type Inbound. Type: {type(inbound)}.)")
                continue
                
            # دسترسی مستقیم به آتریبیوت‌های آبجکت Inbound
            inbound_id = inbound.id
            remote_id = inbound.remote_id
            
            # استفاده از remark یا tag برای نمایش نام اینباند
            tag = inbound.remark or inbound.tag or f"Inbound_{remote_id or inbound_id}"
            
            if inbound_id is None:
                logger.warning(f"اینباند در پنل {panel_id} با شناسه داخلی None پیدا شد، از آن صرف نظر می‌شود. داده اینباند: {inbound}. (Inbound in panel {panel_id} found with internal ID None, skipping. Inbound data: {inbound}.)")
                continue
                
            # استفاده از remote_id در callback data اگر موجود باشد
            callback_inbound_id = remote_id or inbound_id
            
            builder.button(
                text=f"⚙️ مدیریت {tag} (ID در پنل: {callback_inbound_id})",
                callback_data=f"inbound_details:{panel_id}:{callback_inbound_id}"
            )
        except AttributeError as e:
            logger.error(f"خطا در دسترسی به اتریبیوت‌های آبجکت Inbound در پنل {panel_id}: {e}. آبجکت: {inbound}. (Error accessing attributes of Inbound object in panel {panel_id}: {e}. Object: {inbound}).", exc_info=True)
            continue
        except Exception as e:
            logger.error(f"خطای پیش‌بینی نشده هنگام پردازش اینباند {getattr(inbound, 'id', 'N/A')} در پنل {panel_id}: {e}. (Unexpected error processing inbound {getattr(inbound, 'id', 'N/A')} in panel {panel_id}: {e}).", exc_info=True)
            continue

    # دکمه بازگشت به منوی پنل
    builder.button(
        text="🔙 بازگشت",
        callback_data=f"panel_manage:{panel_id}"
    )
    
    builder.adjust(1)  # یک دکمه در هر ردیف
    logger.debug(f"کیبورد اینباندها برای پنل {panel_id} ساخته شد. (Inbounds keyboard for panel {panel_id} built.)")
    return builder.as_markup()


def get_inbound_manage_buttons(panel_id: int, remote_inbound_id: int) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد دکمه‌های عملیاتی برای یک اینباند خاص.

    Args:
        panel_id (int): شناسه پنل در دیتابیس ما.
        remote_inbound_id (int): شناسه اینباند در پنل راه دور (XUI).
        
    Returns:
        InlineKeyboardMarkup: کیبورد ساخته شده با دکمه‌های مدیریتی.
    """
    builder = InlineKeyboardBuilder()
    logger.debug(f"ساخت کیبورد مدیریت برای اینباند {remote_inbound_id} در پنل {panel_id}. (Building management keyboard for inbound {remote_inbound_id} in panel {panel_id}.)")
    
    # استفاده از remote_inbound_id در callback data
    builder.button(text="👥 مشاهده کلاینت‌ها", callback_data=f"inbound_clients:{panel_id}:{remote_inbound_id}")
    builder.button(text="🔧 ویرایش", callback_data=f"inbound_edit:{panel_id}:{remote_inbound_id}")
    builder.button(text="🗑 حذف", callback_data=f"inbound_delete:{panel_id}:{remote_inbound_id}")
    builder.button(text="🔄 ریست", callback_data=f"inbound_reset:{panel_id}:{remote_inbound_id}")
    builder.button(text="📊 آمار", callback_data=f"inbound_stats:{panel_id}:{remote_inbound_id}")
    
    # دکمه بازگشت به لیست اینباندها
    builder.button(text="🔙 بازگشت به لیست", callback_data=f"panel_inbounds:{panel_id}")
    
    # تنظیم چیدمان: 2 دکمه در هر ردیف برای عملیات، 1 برای بازگشت
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup()


# Function for backward compatibility
def get_inbound_management_keyboard(panel_id: int, remote_inbound_id: int) -> InlineKeyboardMarkup:
    """
    تابع میانجی برای حفظ سازگاری با کد قبلی.
    این تابع فقط get_inbound_manage_buttons را فراخوانی می‌کند.
    
    Args:
        panel_id (int): شناسه پنل
        remote_inbound_id (int): شناسه اینباند در پنل راه دور
        
    Returns:
        InlineKeyboardMarkup: کیبورد ساخته شده
    """
    logger.warning("استفاده از تابع قدیمی get_inbound_management_keyboard. لطفاً از get_inbound_manage_buttons استفاده کنید. (Using deprecated function get_inbound_management_keyboard. Please use get_inbound_manage_buttons.)")
    return get_inbound_manage_buttons(panel_id, remote_inbound_id)


# Helper function to format inbound details (optional, can be in callback)
def format_inbound_details(inbound_data: Dict[str, Any]) -> str:
    """
    تبدیل دیکشنری اطلاعات اینباند به رشته قابل نمایش.
    
    Args:
        inbound_data (Dict[str, Any]): دیکشنری اطلاعات اینباند
        
    Returns:
        str: متن فرمت‌بندی شده برای نمایش
    """
    details = []
    details.append(f"🆔 <b>شناسه:</b> {inbound_data.get('id', 'N/A')}")
    details.append(f"🏷 <b>تگ:</b> {inbound_data.get('remark', '-')}")
    details.append(f"💻 <b>پورت:</b> {inbound_data.get('port', 'N/A')}")
    details.append(f"📜 <b>پروتکل:</b> {inbound_data.get('protocol', 'N/A')}")
    status = "✅ فعال" if inbound_data.get("enable", False) else "❌ غیرفعال"
    details.append(f"🚦 <b>وضعیت:</b> {status}")
    details.append(f"👂 <b>Listen IP:</b> {inbound_data.get('listen', '-')}")
    details.append(f"📈 <b>Up:</b> {round(inbound_data.get('up', 0) / (1024**3), 2)} GB")
    details.append(f"📉 <b>Down:</b> {round(inbound_data.get('down', 0) / (1024**3), 2)} GB")
    details.append(f"⏳ <b>Expiry Time:</b> {inbound_data.get('expiryTime', 'N/A')}")  # Assuming 'expiryTime' field exists

    # Safely format nested JSON fields
    def format_json(data):
        try:
            if data is None:
                return "None"
            return json.dumps(data, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"خطا در تبدیل داده به JSON: {e}. (Error converting data to JSON: {e}.)", exc_info=True)
            return str(data)

    settings = inbound_data.get('settings')
    if settings:
        details.append(f"""🔧 <b>تنظیمات (Settings):</b>
<code>{format_json(settings)}</code>""")

    stream_settings = inbound_data.get('streamSettings')
    if stream_settings:
        details.append(f"""🌊 <b>تنظیمات Stream:</b>
<code>{format_json(stream_settings)}</code>""")

    sniffing = inbound_data.get('sniffing')
    if sniffing:
        details.append(f"""👃 <b>تنظیمات Sniffing:</b>
<code>{format_json(sniffing)}</code>""")

    return "\n".join(details)


def get_inbound_clients_keyboard(clients: List[Dict[str, Any]], panel_id: int, inbound_id: int) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد دکمه‌های عملیاتی برای کلاینت‌های یک اینباند خاص.
    
    Args:
        clients (List[Dict[str, Any]]): لیست دیکشنری‌های اطلاعات کلاینت‌ها
        panel_id (int): شناسه پنل
        inbound_id (int): شناسه اینباند
        
    Returns:
        InlineKeyboardMarkup: کیبورد ساخته شده
    """
    builder = InlineKeyboardBuilder()
    logger.debug(f"ساخت کیبورد کلاینت‌ها برای اینباند {inbound_id} در پنل {panel_id}. تعداد کلاینت‌ها: {len(clients)}. (Building clients keyboard for inbound {inbound_id} in panel {panel_id}. Number of clients: {len(clients)}.)")

    for client_data in clients:
        client_uuid = client_data.get("uuid")  # Assuming 'id' from panel is mapped to 'uuid'
        client_email = client_data.get("email", "بدون ایمیل")

        if not client_uuid:
            logger.warning(f"کلاینت بدون UUID معتبر یافت شد، از آن صرف نظر می‌شود. داده کلاینت: {client_data}. (Client without valid UUID found, skipping. Client data: {client_data}.)")
            continue

        # افزودن دکمه‌های عملیاتی برای کلاینت
        builder.button(
            text="📄 مشاهده جزئیات",
            callback_data=f"client_details:{panel_id}:{inbound_id}:{client_uuid}"
        )
        builder.button(
            text="🔗 دریافت کانفیگ",
            callback_data=f"client_config:{panel_id}:{inbound_id}:{client_uuid}"
        )
        builder.button(
            text="♻️ ریست ترافیک",
            callback_data=f"client_reset:{panel_id}:{inbound_id}:{client_uuid}"
        )
        builder.button(
            text="🗑 حذف کلاینت",
            callback_data=f"client_delete:{panel_id}:{inbound_id}:{client_uuid}"
        )

    # افزودن دکمه بازگشت در انتها
    builder.button(
        text="🔙 بازگشت به اینباند",
        callback_data=f"inbound_details:{panel_id}:{inbound_id}"
    )

    # تنظیم چیدمان: 2 دکمه در هر ردیف برای عملیات کلاینت، 1 برای بازگشت
    num_clients = len(clients)
    adjust_pattern = [2, 2] * num_clients + [1]  # الگوی چیدمان: [2, 2, 2, 2, ..., 1]
    builder.adjust(*adjust_pattern)

    return builder.as_markup()
