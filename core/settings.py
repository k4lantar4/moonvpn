"""
تنظیمات ثابت (توکن‌های API، شناسه کانال‌ها، قوانین نام‌گذاری)
"""

import os
from typing import List, Dict, Any

# شناسه‌های ادمین‌ها برای دریافت نوتیفیکیشن‌ها و انجام عملیات مدیریتی
ADMIN_IDS: List[int] = [
    int(os.getenv("ADMIN_ID", "0")),  # ادمین اصلی
]

# لیست آیدی‌های ادمین اضافی از متغیر محیطی (با کاما جدا شده)
if os.getenv("ADDITIONAL_ADMIN_IDS"):
    additional_ids = os.getenv("ADDITIONAL_ADMIN_IDS", "").split(",")
    for admin_id in additional_ids:
        if admin_id.strip() and admin_id.strip().isdigit():
            ADMIN_IDS.append(int(admin_id.strip()))

# کانال تلگرام برای اعلان‌های عمومی
CHANNEL_ID: str = os.getenv("CHANNEL_ID", "@moonvpn_channel")

# توکن دسترسی بات تلگرام
BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")

# قوانین نام‌گذاری اکانت‌ها
ACCOUNT_NAMING_TEMPLATE: str = "{location}-Moonvpn-{id}"

# تنظیمات حساب تست
MAX_TRIAL_ACCOUNTS_PER_USER: int = 1
TRIAL_DURATION_DAYS: int = 1
TRIAL_TRAFFIC_GB: int = 1
