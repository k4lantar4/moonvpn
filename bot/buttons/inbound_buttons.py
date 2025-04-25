"""
دکمه‌های مربوط به انتخاب inbound در فرایند خرید
"""

from typing import List, Dict, Any
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import json

from db.models.panel import Panel
from db.models.inbound import Inbound


def get_panel_locations_keyboard(panels: List[Panel]) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد انتخاب لوکیشن پنل‌ها
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
    """
    keyboard = []
    
    # دکمه‌های انتخاب inbound
    for inbound in inbounds:
        # نمایش تعداد کاربران در صورت وجود محدودیت
        client_info = ""
        if inbound.max_clients:
            client_info = f" ({inbound.client_count}/{inbound.max_clients})"
        
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


# افزودن تابع برای ساخت کیبورد مدیریت اینباندهای یک پنل
def get_panel_inbounds_keyboard(inbounds: List[Dict[str, Any]], panel_id: int) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد دکمه‌های مدیریت برای اینباندهای یک پنل (دکمه کلی مدیریت)
    """
    builder = InlineKeyboardBuilder()
    for inb in inbounds:
        inbound_id = inb.get('id')
        tag = inb.get('remark', f'Inbound {inbound_id}')
        builder.button(
            text=f"⚙️ مدیریت {tag} ({inbound_id})",
            callback_data=f"inbound_details:{panel_id}:{inbound_id}" # Changed callback to show details first
        )
    # دکمه بازگشت به منوی پنل
    builder.button(
        text="🔙 بازگشت",
        callback_data=f"panel_manage:{panel_id}"
    )
    builder.adjust(1) # Adjust to show one button per row
    return builder.as_markup()


def get_inbound_management_keyboard(panel_id: int, inbound_id: int) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد دکمه‌های عملیاتی برای یک اینباند خاص.
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="👥 مشاهده کلاینت‌ها", callback_data=f"inbound_clients:{panel_id}:{inbound_id}")
    builder.button(text="🔧 ویرایش", callback_data=f"inbound_edit:{panel_id}:{inbound_id}")
    builder.button(text="🗑 حذف", callback_data=f"inbound_delete:{panel_id}:{inbound_id}")
    builder.button(text="🔄 ریست", callback_data=f"inbound_reset:{panel_id}:{inbound_id}")
    builder.button(text="📊 آمار", callback_data=f"inbound_stats:{panel_id}:{inbound_id}")
    # دکمه بازگشت به لیست اینباندها
    builder.button(text="🔙 بازگشت به لیست", callback_data=f"panel_inbounds:{panel_id}")
    # Adjust layout: 2 buttons per row for actions, 1 for back
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup()

# Helper function to format inbound details (optional, can be in callback)
def format_inbound_details(inbound_data: Dict[str, Any]) -> str:
    """Formats inbound details dictionary into a readable string."""
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
    details.append(f"⏳ <b>Expiry Time:</b> {inbound_data.get('expiryTime', 'N/A')}") # Assuming 'expiryTime' field exists

    # Safely format nested JSON fields
    def format_json(data):
        try:
            return json.dumps(data, indent=2, ensure_ascii=False)
        except Exception:
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
    """
    builder = InlineKeyboardBuilder()

    for client_data in clients:
        client_uuid = client_data.get("uuid") # Assuming 'id' from panel is mapped to 'uuid'
        client_email = client_data.get("email", "بدون ایمیل")

        if not client_uuid:
            # Skip clients without a valid identifier for callbacks
            continue

        # Add client identifier as a plain text row (optional, but good for context)
        # builder.button(text=f"👤 {client_email}", callback_data="ignore") # Optional: add client name row

        # Add action buttons for the client
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

        # Adjust layout for client action buttons (e.g., 2x2)
        builder.adjust(2, 2)

    # Add a back button at the end
    builder.button(
        text="🔙 بازگشت به اینباند",
        callback_data=f"inbound_details:{panel_id}:{inbound_id}"
    )

    # Adjust the last row (back button) separately
    builder.adjust(4, repeat=True)
    builder.adjust(1)

    return builder.as_markup() 