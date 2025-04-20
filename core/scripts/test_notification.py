#!/usr/bin/env python
"""
اسکریپت تست سیستم نوتیفیکیشن در حالت CLI

Usage:
    python -m core.scripts.test_notification --user_id TELEGRAM_ID --message "پیام تست"
"""

import argparse
import sys
import os
import logging
from contextlib import contextmanager

from db import get_db
from core.services.notification_service import NotificationService

# تنظیم لاگر
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


def parse_args():
    """آماده‌سازی آرگومان‌های خط فرمان"""
    parser = argparse.ArgumentParser(description="ارسال نوتیفیکیشن تست به کاربر")
    
    parser.add_argument("--user_id", type=int, required=True, help="شناسه تلگرام کاربر برای ارسال پیام")
    parser.add_argument("--message", type=str, default="🔔 پیام تست از سیستم نوتیفیکیشن MoonVPN", 
                        help="متن پیام (اختیاری)")
    parser.add_argument("--admin", action="store_true", help="ارسال به همه ادمین‌ها")
    parser.add_argument("--channel", action="store_true", help="ارسال به کانال")
    
    return parser.parse_args()


@contextmanager
def get_session():
    """ایجاد یک جلسه دیتابیس با استفاده از context manager"""
    session = next(get_db())
    try:
        yield session
    finally:
        session.close()


def send_notification(user_id=None, message=None, send_to_admin=False, send_to_channel=False):
    """پیاده‌سازی منطق ارسال نوتیفیکیشن"""
    with get_session() as session:
        notification_service = NotificationService(session)
        
        if user_id and not (send_to_admin or send_to_channel):
            # ارسال به کاربر مشخص
            logger.info(f"Sending notification to user {user_id}")
            result = notification_service.notify_user(user_id, message)
            if result:
                print(f"✅ پیام با موفقیت به کاربر {user_id} ارسال شد (حالت CLI)")
                print(f"📝 متن پیام: {message}")
                return True
            else:
                print(f"❌ خطا در ارسال پیام به کاربر {user_id}")
                return False
        
        if send_to_admin:
            # ارسال به همه ادمین‌ها
            logger.info("Sending notification to all admins")
            result = notification_service.notify_admin(message)
            if result:
                print("✅ پیام با موفقیت به همه ادمین‌ها ارسال شد (حالت CLI)")
                print(f"📝 متن پیام: {message}")
                return True
            else:
                print("❌ خطا در ارسال پیام به ادمین‌ها")
                return False
                
        if send_to_channel:
            # ارسال به کانال
            logger.info("Sending notification to channel")
            result = notification_service.notify_channel(message)
            if result:
                print("✅ پیام با موفقیت به کانال ارسال شد (حالت CLI)")
                print(f"📝 متن پیام: {message}")
                return True
            else:
                print("❌ خطا در ارسال پیام به کانال")
                return False


def main():
    """نقطه ورود اسکریپت"""
    args = parse_args()
    
    success = False
    if args.admin:
        success = send_notification(message=args.message, send_to_admin=True)
    elif args.channel:
        success = send_notification(message=args.message, send_to_channel=True)
    else:
        success = send_notification(user_id=args.user_id, message=args.message)
    
    # خروج با کد مناسب
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 