"""
تنظیمات ثابت (توکن‌های API، شناسه کانال‌ها، قوانین نام‌گذاری)
"""

import os
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

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
BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN", "")

# قوانین نام‌گذاری اکانت‌ها
ACCOUNT_NAMING_TEMPLATE: str = "{location}-Moonvpn-{id}"

# تنظیمات حساب تست
MAX_TRIAL_ACCOUNTS_PER_USER: int = 1
TRIAL_DURATION_DAYS: int = 1
TRIAL_TRAFFIC_GB: int = 1

# تنظیمات دیتابیس
# تعریف URL اتصال به دیتابیس با درایور aiomysql
MYSQL_HOST: str = os.getenv("MYSQL_HOST", "db")
MYSQL_PORT: int = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER: str = os.getenv("MYSQL_USER", "moonvpn_user")
MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "strong_password_here")
MYSQL_DATABASE: str = os.getenv("MYSQL_DATABASE", "moonvpn")

# ساخت URL دیتابیس با استفاده از درایور aiomysql
DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    f"mysql+aiomysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4"
)

# اطمینان از استفاده از درایور aiomysql
if "pymysql" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("pymysql", "aiomysql")
