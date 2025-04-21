"""
فایل اصلی برای راه‌اندازی بات تلگرام MoonVPN
"""

import os
import asyncio
import logging
import traceback
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from aiogram import Bot, Dispatcher, types, Router
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.filters.command import Command
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# Import database models and session
from db.models import Base  # Importing all models
from bot.commands.start import register_start_command
from bot.commands.admin import register_admin_commands
from bot.commands.plans import register_plans_command
from bot.commands.wallet import register_wallet_command
from bot.commands.buy import register_buy_command
from bot.callbacks import setup_callback_handlers
from core.services.notification_service import NotificationService
from core.services.panel_service import PanelService

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
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+aiomysql://root:password@db:3306/moonvpn")

# ایجاد اتصال به دیتابیس
engine = create_async_engine(DATABASE_URL)
SessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

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
        async with SessionLocal() as session:
            notification_service = NotificationService(session)
            notification_service.set_bot(bot)
            
            # همگام‌سازی inbound‌های تمام پنل‌ها در شروع بات
            logger.info("Syncing all panel inbounds...")
            panel_service = PanelService(session)
            try:
                sync_results = await panel_service.sync_all_panels_inbounds()
                logger.info(f"Successfully synced inbounds for {len(sync_results)} panels")
                # ارسال نوتیفیکیشن به ادمین‌ها
                await notification_service.notify_admins(
                    f"🔄 همگام‌سازی inbound‌ها انجام شد\n"
                    f"تعداد پنل‌های همگام‌سازی شده: {len(sync_results)}"
                )
            except Exception as e:
                logger.error(f"Error syncing inbounds: {e}", exc_info=True)
                await notification_service.notify_admins(
                    f"⚠️ خطا در همگام‌سازی inbound‌ها:\n{str(e)}"
                )
        
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
