import math
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings
from ..models import User, Plan, Subscription, Transaction

def get_user_language(user: User) -> str:
    """Get user's preferred language"""
    return user.language if user.language in ['en', 'fa'] else 'en'

def format_bytes(bytes: int) -> str:
    """Format bytes to human readable format"""
    if bytes == 0:
        return "0 B"
        
    size_name = ("B", "KB", "MB", "GB", "TB", "PB")
    i = int(math.floor(math.log(bytes, 1024)))
    p = math.pow(1024, i)
    s = round(bytes / p, 2)
    
    return f"{s} {size_name[i]}"

def format_duration(days: int, language: str = 'en') -> str:
    """Format duration in days to human readable format"""
    if language == 'fa':
        if days == 30:
            return "۱ ماه"
        elif days == 90:
            return "۳ ماه"
        elif days == 180:
            return "۶ ماه"
        elif days == 365:
            return "۱ سال"
        else:
            return f"{days} روز"
    else:
        if days == 30:
            return "1 Month"
        elif days == 90:
            return "3 Months"
        elif days == 180:
            return "6 Months"
        elif days == 365:
            return "1 Year"
        else:
            return f"{days} Days"

def format_price(amount: float, language: str = 'en') -> str:
    """Format price based on language"""
    if language == 'fa':
        return f"{amount:,} تومان"
    else:
        return f"${amount:,.2f}"

def format_date(date: datetime, language: str = 'en') -> str:
    """Format date based on language"""
    if language == 'fa':
        # TODO: Implement Persian date formatting
        return date.strftime("%Y-%m-%d %H:%M")
    else:
        return date.strftime("%Y-%m-%d %H:%M")

def get_subscription_status_text(
    subscription: Subscription,
    language: str = 'en'
) -> str:
    """Get formatted subscription status text"""
    if language == 'fa':
        status_map = {
            'active': '✅ فعال',
            'expired': '❌ منقضی شده',
            'cancelled': '🚫 لغو شده',
            'suspended': '⏸ معلق'
        }
    else:
        status_map = {
            'active': '✅ Active',
            'expired': '❌ Expired',
            'cancelled': '🚫 Cancelled',
            'suspended': '⏸ Suspended'
        }
    
    return status_map.get(subscription.status, subscription.status)

def get_transaction_status_text(
    transaction: Transaction,
    language: str = 'en'
) -> str:
    """Get formatted transaction status text"""
    if language == 'fa':
        status_map = {
            'pending': '⏳ در انتظار پرداخت',
            'completed': '✅ پرداخت شده',
            'failed': '❌ ناموفق',
            'cancelled': '🚫 لغو شده'
        }
    else:
        status_map = {
            'pending': '⏳ Pending',
            'completed': '✅ Completed',
            'failed': '❌ Failed',
            'cancelled': '🚫 Cancelled'
        }
    
    return status_map.get(transaction.status, transaction.status)

def get_plan_details_text(
    plan: Plan,
    language: str = 'en'
) -> str:
    """Get formatted plan details text"""
    if language == 'fa':
        text = (
            f"📦 نام پلن: {plan.name}\n"
            f"💰 قیمت: {format_price(plan.price, language)}\n"
            f"⏱ مدت: {format_duration(plan.duration_days, language)}\n"
            f"🌐 ترافیک: {format_bytes(plan.traffic_limit)}\n"
            f"👥 حداکثر اتصال همزمان: {plan.max_connections}\n\n"
            f"✨ ویژگی‌ها:\n"
        )
        
        for feature in plan.features:
            text += f"• {feature}\n"
            
    else:
        text = (
            f"📦 Plan: {plan.name}\n"
            f"💰 Price: {format_price(plan.price, language)}\n"
            f"⏱ Duration: {format_duration(plan.duration_days, language)}\n"
            f"🌐 Traffic: {format_bytes(plan.traffic_limit)}\n"
            f"👥 Max Connections: {plan.max_connections}\n\n"
            f"✨ Features:\n"
        )
        
        for feature in plan.features:
            text += f"• {feature}\n"
    
    return text

def get_subscription_details_text(
    subscription: Subscription,
    language: str = 'en'
) -> str:
    """Get formatted subscription details text"""
    if language == 'fa':
        text = (
            f"📦 پلن: {subscription.plan.name}\n"
            f"📅 تاریخ شروع: {format_date(subscription.start_date, language)}\n"
            f"📅 تاریخ پایان: {format_date(subscription.end_date, language)}\n"
            f"⏱ روزهای باقیمانده: {subscription.get_remaining_days()}\n"
            f"🌐 ترافیک مصرفی: {format_bytes(subscription.used_traffic)}\n"
            f"🌐 ترافیک باقیمانده: {format_bytes(subscription.get_remaining_traffic())}\n"
            f"📊 وضعیت: {get_subscription_status_text(subscription, language)}\n"
        )
    else:
        text = (
            f"📦 Plan: {subscription.plan.name}\n"
            f"📅 Start Date: {format_date(subscription.start_date, language)}\n"
            f"📅 End Date: {format_date(subscription.end_date, language)}\n"
            f"⏱ Days Remaining: {subscription.get_remaining_days()}\n"
            f"🌐 Used Traffic: {format_bytes(subscription.used_traffic)}\n"
            f"🌐 Remaining Traffic: {format_bytes(subscription.get_remaining_traffic())}\n"
            f"📊 Status: {get_subscription_status_text(subscription, language)}\n"
        )
    
    return text

def get_wallet_text(user: User, language: str = 'en') -> str:
    """Get formatted wallet text"""
    if language == 'fa':
        text = (
            f"👛 موجودی کیف پول:\n"
            f"💰 {format_price(user.wallet_balance, language)}\n\n"
            f"📊 آمار:\n"
            f"💵 مجموع تراکنش‌ها: {format_price(user.total_spent, language)}\n"
        )
        
        if user.is_reseller:
            text += (
                f"\n📈 آمار فروش:\n"
                f"💰 درآمد کل: {format_price(user.total_earnings, language)}\n"
                f"👥 تعداد مشتریان: {user.customer_count}\n"
            )
    else:
        text = (
            f"👛 Wallet Balance:\n"
            f"💰 {format_price(user.wallet_balance, language)}\n\n"
            f"📊 Statistics:\n"
            f"💵 Total Spent: {format_price(user.total_spent, language)}\n"
        )
        
        if user.is_reseller:
            text += (
                f"\n📈 Sales Stats:\n"
                f"💰 Total Earnings: {format_price(user.total_earnings, language)}\n"
                f"👥 Customer Count: {user.customer_count}\n"
            )
    
    return text

def get_profile_text(user: User, language: str = 'en') -> str:
    """Get formatted profile text"""
    if language == 'fa':
        text = (
            f"👤 پروفایل شما:\n\n"
            f"🆔 نام کاربری: {user.username}\n"
            f"📧 ایمیل: {user.email or '---'}\n"
            f"📱 تلگرام: @{user.telegram_username or '---'}\n"
            f"💰 موجودی: {format_price(user.wallet_balance, language)}\n\n"
        )
        
        if user.is_reseller:
            text += (
                f"🎁 کد معرف: {user.referral_code}\n"
                f"💰 کمیسیون: {user.commission_rate}%\n"
                f"👥 تعداد مشتریان: {user.customer_count}\n"
            )
            
        text += "\n📦 اشتراک‌های فعال:\n"
        active_subs = user.subscriptions.filter(status='active')
        if active_subs:
            for sub in active_subs:
                text += (
                    f"\n• {sub.plan.name}\n"
                    f"  ⏱ {sub.get_remaining_days()} روز مانده\n"
                    f"  🌐 {format_bytes(sub.get_remaining_traffic())} ترافیک مانده\n"
                )
        else:
            text += "هیچ اشتراک فعالی ندارید\n"
    else:
        text = (
            f"👤 Your Profile:\n\n"
            f"🆔 Username: {user.username}\n"
            f"📧 Email: {user.email or '---'}\n"
            f"📱 Telegram: @{user.telegram_username or '---'}\n"
            f"💰 Balance: {format_price(user.wallet_balance, language)}\n\n"
        )
        
        if user.is_reseller:
            text += (
                f"🎁 Referral Code: {user.referral_code}\n"
                f"💰 Commission Rate: {user.commission_rate}%\n"
                f"👥 Customer Count: {user.customer_count}\n"
            )
            
        text += "\n📦 Active Subscriptions:\n"
        active_subs = user.subscriptions.filter(status='active')
        if active_subs:
            for sub in active_subs:
                text += (
                    f"\n• {sub.plan.name}\n"
                    f"  ⏱ {sub.get_remaining_days()} days remaining\n"
                    f"  🌐 {format_bytes(sub.get_remaining_traffic())} traffic left\n"
                )
        else:
            text += "No active subscriptions\n"
    
    return text

def get_help_text(language: str = 'en') -> str:
    """Get formatted help text"""
    if language == 'fa':
        text = (
            "🌙 راهنمای MoonVPN\n\n"
            "دستورات اصلی:\n"
            "/start - شروع ربات\n"
            "/help - نمایش این راهنما\n"
            "/plans - مشاهده پلن‌ها\n"
            "/profile - مشاهده پروفایل\n"
            "/wallet - مدیریت کیف پول\n"
            "/support - پشتیبانی\n"
            "/settings - تنظیمات\n\n"
            
            "برای خرید اشتراک:\n"
            "1. دستور /plans را بزنید\n"
            "2. پلن مورد نظر را انتخاب کنید\n"
            "3. روش پرداخت را انتخاب کنید\n"
            "4. پرداخت را انجام دهید\n"
            "5. کانفیگ VPN را دریافت کنید\n\n"
            
            "برای شارژ کیف پول:\n"
            "1. دستور /wallet را بزنید\n"
            "2. گزینه «افزایش موجودی» را بزنید\n"
            "3. مبلغ را وارد کنید\n"
            "4. پرداخت را انجام دهید\n\n"
            
            "برای دریافت پشتیبانی:\n"
            "1. دستور /support را بزنید\n"
            "2. پیام خود را ارسال کنید\n"
            "3. منتظر پاسخ پشتیبانی بمانید\n\n"
            
            "📞 تماس با ما:\n"
            f"🌐 وب‌سایت: {settings.SITE_URL}\n"
            f"📧 ایمیل: {settings.SUPPORT_EMAIL}\n"
            f"📱 تلگرام: {settings.TELEGRAM_SUPPORT}\n"
        )
    else:
        text = (
            "🌙 MoonVPN Help\n\n"
            "Main Commands:\n"
            "/start - Start the bot\n"
            "/help - Show this help\n"
            "/plans - View plans\n"
            "/profile - View profile\n"
            "/wallet - Manage wallet\n"
            "/support - Get support\n"
            "/settings - Settings\n\n"
            
            "To Purchase a Plan:\n"
            "1. Use /plans command\n"
            "2. Select a plan\n"
            "3. Choose payment method\n"
            "4. Complete payment\n"
            "5. Get VPN config\n\n"
            
            "To Add Funds:\n"
            "1. Use /wallet command\n"
            "2. Click 'Add Funds'\n"
            "3. Enter amount\n"
            "4. Complete payment\n\n"
            
            "To Get Support:\n"
            "1. Use /support command\n"
            "2. Send your message\n"
            "3. Wait for response\n\n"
            
            "📞 Contact Us:\n"
            f"🌐 Website: {settings.SITE_URL}\n"
            f"📧 Email: {settings.SUPPORT_EMAIL}\n"
            f"📱 Telegram: {settings.TELEGRAM_SUPPORT}\n"
        )
    
    return text 