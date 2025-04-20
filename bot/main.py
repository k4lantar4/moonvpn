"""
فایل اصلی برای راه‌اندازی بات تلگرام MoonVPN
"""

import os
import asyncio
import logging
import traceback
from sqlalchemy.orm import sessionmaker
from aiogram import Bot, Dispatcher, types, Router
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.filters import Command
from dotenv import load_dotenv
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# Import database models and session
from sqlalchemy import create_engine
from db.models import Base  # Importing all models
from bot.commands.start import register_start_command
from bot.commands.admin import register_admin_commands
from bot.commands.plans import register_plans_command
from bot.commands.wallet import register_wallet_command
from bot.commands.buy import register_buy_command
from bot.callbacks import setup_callback_handlers
from core.services.notification_service import NotificationService

# تنظیمات لاگینگ
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

# بارگذاری متغیرهای محیطی
load_dotenv()

# دریافت توکن بات از محیط
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logger.critical("BOT_TOKEN یافت نشد! لطفاً فایل .env را بررسی کنید.")
    exit(1)

# دریافت آدرس Redis از محیط
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

# تنظیمات دیتابیس
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:password@db:3306/moonvpn")

# ایجاد اتصال به دیتابیس
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# متغیر سراسری برای نگهداری نمونه notification_service
notification_service = None


async def main():
    """
    تابع اصلی راه‌اندازی بات
    """
    logger.info("شروع راه‌اندازی بات MoonVPN...")

    # تنظیم ذخیره‌سازی وضعیت با Redis
    storage = RedisStorage.from_url(REDIS_URL)
    
    # ایجاد نمونه‌های Bot و Dispatcher
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=storage)
    router = Router()

    try:
        # راه‌اندازی سرویس نوتیفیکیشن
        logger.info("Initializing notification service...")
        global notification_service
        session = SessionLocal()
        notification_service = NotificationService(session)
        notification_service.set_bot(bot)
        
        # ثبت روترهای بات
        logger.info("Registering start command...")
        register_start_command(router, SessionLocal)
        
        logger.info("Registering admin commands...")
        register_admin_commands(router, SessionLocal)
        
        logger.info("Registering plans command...")
        register_plans_command(router, SessionLocal)
        
        logger.info("Registering wallet command...")
        register_wallet_command(router, SessionLocal)
        
        logger.info("Registering buy command...")
        register_buy_command(router, SessionLocal)
        
        # ثبت callback handlers
        logger.info("Registering callback handlers...")
        setup_callback_handlers(router, SessionLocal)
        
        # ثبت هندلر مستقیم برای دستور /plans
        @router.message(Command("plans_debug"))
        async def cmd_plans_debug(message: types.Message):
            logger.info(f"Direct plans_debug command received from {message.from_user.id}")
            await message.answer("دستور plans_debug دریافت شد!")
            
        # تست ارسال نوتیفیکیشن
        @router.message(Command("test_notify"))
        async def cmd_test_notify(message: types.Message):
            logger.info(f"Testing notification system for user {message.from_user.id}")
            notification_service.notify_user(
                message.from_user.id, 
                "🔔 سیستم نوتیفیکیشن با موفقیت تست شد!\n\nاین پیام برای آزمایش عملکرد سیستم نوتیفیکیشن است."
            )
            await message.answer("تست نوتیفیکیشن ارسال شد. لطفاً پیام دریافتی را بررسی کنید.")
            
        # افزودن روتر به دیسپچر
        dp.include_router(router)
        
        logger.info("All handlers registered successfully!")
    except Exception as e:
        logger.error(f"Error registering handlers: {str(e)}")
        logger.error(traceback.format_exc())
    
    # پاکسازی وب‌هوک‌های قبلی
    await bot.delete_webhook(drop_pending_updates=True)
    
    # شروع پردازش پیام‌ها با long polling
    logger.info("بات MoonVPN با موفقیت راه‌اندازی شد!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("بات متوقف شد!")
    finally:
        # بستن session در هنگام خروج
        if notification_service and hasattr(notification_service, 'db_session'):
            notification_service.db_session.close()
