"""
Message templates for the bot.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from core.utils.helpers import (
    format_price,
    format_bytes,
    format_date,
    format_duration,
    format_traffic_usage,
    get_subscription_status
)

logger = logging.getLogger(__name__)

def get_welcome_message(first_name: str) -> str:
    """Get welcome message."""
    return (
        f"👋 سلام {first_name} عزیز\n\n"
        "به ربات MoonVPN خوش آمدید!\n"
        "برای خرید اشتراک و استفاده از خدمات VPN از دکمه‌های زیر استفاده کنید.\n\n"
        "🔰 امکانات:\n"
        "• سرورهای پرسرعت و اختصاصی\n"
        "• پشتیبانی ۲۴/۷\n"
        "• قیمت مناسب و کیفیت عالی\n"
        "• تضمین بازگشت وجه\n\n"
        "📌 برای شروع، از منوی زیر گزینه مورد نظر خود را انتخاب کنید."
    )

def get_subscription_message() -> str:
    """Get subscription plans message."""
    return (
        "🏷 پلن‌های اشتراک:\n\n"
        "لطفاً یکی از پلن‌های زیر را انتخاب کنید:\n\n"
        "✨ ویژگی‌های تمام پلن‌ها:\n"
        "• سرعت نامحدود\n"
        "• پشتیبانی ۲۴/۷\n"
        "• تضمین کیفیت\n"
        "• امکان تغییر سرور\n"
        "• پشتیبانی از تمام دستگاه‌ها"
    )

def get_plan_details(plan: Dict[str, Any]) -> str:
    """Get plan details message."""
    return (
        f"📦 {plan['name']}\n\n"
        f"{plan['description']}\n\n"
        f"💰 قیمت: {format_price(plan['price'])}\n\n"
        "برای خرید این پلن، روش پرداخت را انتخاب کنید:"
    )

def get_payment_success_message(
    plan: Dict[str, Any],
    account: Dict[str, Any]
) -> str:
    """Get payment success message."""
    return (
        "✅ پرداخت با موفقیت انجام شد!\n\n"
        f"🏷 پلن: {plan['name']}\n"
        f"💰 مبلغ پرداختی: {format_price(plan['price'])}\n"
        f"📅 تاریخ انقضا: {format_date(account['expiry_date'])}\n"
        f"📊 حجم: {format_bytes(account['traffic_limit'])}\n\n"
        "🔰 اطلاعات اتصال:\n"
        f"🔗 لینک: {account['link']}\n"
        f"🆔 شناسه: {account['uuid']}\n\n"
        "📱 برای دریافت راهنمای اتصال، دستور /help را ارسال کنید."
    )

def get_payment_failed_message() -> str:
    """Get payment failed message."""
    return (
        "❌ پرداخت ناموفق\n\n"
        "متأسفانه پرداخت شما با مشکل مواجه شد.\n"
        "لطفاً مجدداً تلاش کنید یا با پشتیبانی تماس بگیرید."
    )

def get_account_status_message(account: Dict[str, Any]) -> str:
    """Get account status message."""
    status = get_subscription_status(
        account['expiry_date'],
        account['traffic_used'],
        account['traffic_limit']
    )
    
    remaining = ""
    expiry = datetime.strptime(account['expiry_date'], '%Y-%m-%d')
    if expiry > datetime.now():
        remaining = f"\n⏳ زمان باقیمانده: {format_duration((expiry - datetime.now()).total_seconds())}"
    
    return (
        f"{status} وضعیت اشتراک\n\n"
        f"📅 تاریخ انقضا: {format_date(account['expiry_date'])}{remaining}\n"
        f"📊 مصرف ترافیک: {format_traffic_usage(account['traffic_used'], account['traffic_limit'])}\n\n"
        f"🌍 سرور: {account.get('server_name', 'نامشخص')}\n"
        f"🔗 لینک اتصال: {account['link']}"
    )

def get_server_list_message() -> str:
    """Get server list message."""
    return (
        "🌍 لیست سرورها\n\n"
        "لطفاً سرور مورد نظر خود را انتخاب کنید:"
    )

def get_server_changed_message(server: Dict[str, Any]) -> str:
    """Get server changed message."""
    return (
        f"✅ سرور شما با موفقیت به {server['name']} تغییر کرد.\n\n"
        "🔗 لینک جدید اتصال برای شما ارسال خواهد شد."
    )

def get_help_message() -> str:
    """Get help message."""
    return (
        "📚 راهنمای استفاده\n\n"
        "🔰 دستورات اصلی:\n"
        "/start - شروع مجدد ربات\n"
        "/buy - خرید اشتراک\n"
        "/status - وضعیت سرویس\n"
        "/change - تغییر سرور\n"
        "/help - راهنما\n"
        "/support - پشتیبانی\n\n"
        "📱 راهنمای اتصال:\n"
        "• اندروید: [مشاهده](https://example.com/android)\n"
        "• آیفون: [مشاهده](https://example.com/ios)\n"
        "• ویندوز: [مشاهده](https://example.com/windows)\n"
        "• مک: [مشاهده](https://example.com/mac)\n\n"
        "💬 در صورت نیاز به راهنمایی بیشتر با پشتیبانی تماس بگیرید."
    )

def get_support_message() -> str:
    """Get support message."""
    return (
        "💬 پشتیبانی\n\n"
        "برای ارتباط با پشتیبانی از روش‌های زیر استفاده کنید:\n\n"
        "📱 تلگرام: @moonvpn_support\n"
        "📧 ایمیل: support@moonvpn.ir\n\n"
        "⏰ ساعات پاسخگویی: ۲۴/۷"
    )

def get_admin_welcome_message() -> str:
    """Get admin welcome message."""
    return (
        "🎛 پنل مدیریت\n\n"
        "به پنل مدیریت MoonVPN خوش آمدید.\n"
        "لطفاً بخش مورد نظر خود را انتخاب کنید:"
    )

def get_income_report_message(report: Dict[str, Any]) -> str:
    """Get income report message."""
    return (
        "📊 گزارش درآمد\n\n"
        f"💰 درآمد کل: {format_price(report['total_income'])}\n"
        f"🛒 تعداد سفارش: {report['total_orders']}\n"
        f"📈 میانگین سفارش: {format_price(report['average_order'])}\n\n"
        "🏷 به تفکیک پلن:\n" +
        "\n".join(
            f"• {item['plan']}: {format_price(item['amount'])} "
            f"({item['count']} سفارش)"
            for item in report['breakdown']
        )
    )

def get_traffic_report_message(report: Dict[str, Any]) -> str:
    """Get traffic report message."""
    return (
        "📈 گزارش ترافیک\n\n"
        f"📊 کل ترافیک: {format_bytes(report['total_traffic'])}\n"
        f"👥 کاربران فعال: {report['active_users']}\n"
        f"📈 میانگین مصرف: {format_bytes(report['average_usage'])}\n\n"
        "🌍 به تفکیک سرور:\n" +
        "\n".join(
            f"• {item['server']}: {format_bytes(item['traffic'])} "
            f"({item['users']} کاربر)"
            for item in report['breakdown']
        )
    )

def get_broadcast_message(
    target: str,
    count: int,
    filters: Optional[Dict[str, Any]] = None
) -> str:
    """Get broadcast confirmation message."""
    target_names = {
        'all': 'همه کاربران',
        'active': 'کاربران فعال',
        'inactive': 'کاربران غیرفعال',
        'premium': 'کاربران ویژه'
    }
    
    filter_text = ""
    if filters:
        conditions = []
        if 'min_traffic' in filters:
            conditions.append(f"حداقل مصرف: {format_bytes(filters['min_traffic'])}")
        if 'min_spent' in filters:
            conditions.append(f"حداقل خرید: {format_price(filters['min_spent'])}")
        if conditions:
            filter_text = "\n🔍 فیلترها:\n" + "\n".join(f"• {c}" for c in conditions)
    
    return (
        "📨 ارسال پیام گروهی\n\n"
        f"👥 گروه هدف: {target_names.get(target, target)}\n"
        f"📊 تعداد: {count} کاربر{filter_text}\n\n"
        "✏️ لطفاً متن پیام خود را ارسال کنید:"
    )

def get_broadcast_sent_message(
    sent: int,
    failed: int,
    total: int
) -> str:
    """Get broadcast sent message."""
    return (
        "✅ پیام گروهی ارسال شد\n\n"
        f"📊 نتیجه ارسال:\n"
        f"• موفق: {sent} کاربر\n"
        f"• ناموفق: {failed} کاربر\n"
        f"• کل: {total} کاربر"
    )

def get_user_stats_message(stats: Dict[str, Any]) -> str:
    """Get user statistics message."""
    return (
        "📊 آمار کاربر\n\n"
        f"📈 مصرف کل: {format_bytes(stats['total_traffic'])}\n"
        f"💰 خرید کل: {format_price(stats['total_spent'])}\n"
        f"✅ اشتراک فعال: {stats['active_accounts']}\n"
        f"❌ اشتراک منقضی: {stats['expired_accounts']}"
    )

def get_discount_created_message(discount: Dict[str, Any]) -> str:
    """Get discount created message."""
    return (
        "✅ کد تخفیف با موفقیت ایجاد شد\n\n"
        f"🎫 کد: {discount['code']}\n"
        f"💰 مقدار: {discount['value']}{'%' if discount['type'] == 'percent' else ' تومان'}\n"
        f"📅 تاریخ انقضا: {format_date(discount['expiry_date'])}\n"
        f"📝 توضیحات: {discount['description']}"
    ) 