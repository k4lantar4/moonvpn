"""
ربات تلگرام MoonVPN - نقطه ورود اصلی
"""

import os
import asyncio
import logging
from typing import Any, Dict

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio.client import Redis
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from aiogram.client.default import DefaultBotProperties

from core.settings import DATABASE_URL, BOT_TOKEN, REDIS_HOST, REDIS_PORT
from core.services.notification_service import NotificationService
from core.services.panel_service import PanelService
from bot.middlewares import AuthMiddleware, ErrorMiddleware
from bot.features.common.handlers import router as common_router
from bot.features.buy.handlers import router as buy_router
from bot.features.wallet.handlers import router as wallet_router
from bot.features.admin.handlers import router as admin_router
from bot.features.profile.handlers import router as profile_router
from bot.features.my_accounts.handlers import router as my_accounts_router
from bot.features.panel_management.handlers import router as panel_management_router

# تنظیمات لاگینگ
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

# تنظیمات دیتابیس
engine = create_async_engine(DATABASE_URL)
SessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# سرویس‌های گلوبال
notification_service: NotificationService | None = None

async def setup_bot() -> Bot:
    """راه‌اندازی و پیکربندی ربات"""
    if not BOT_TOKEN:
        raise ValueError("توکن ربات (BOT_TOKEN) در متغیرهای محیطی یافت نشد!")
    
    return Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

async def setup_dispatcher() -> Dispatcher:
    """راه‌اندازی و پیکربندی دیسپچر"""
    # راه‌اندازی Redis و RedisStorage
    redis_client = Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
    storage = RedisStorage(redis=redis_client)
    dp = Dispatcher(storage=storage)
    
    # ثبت میدلورها
    dp.message.middleware(AuthMiddleware(SessionLocal))
    dp.callback_query.middleware(AuthMiddleware(SessionLocal))
    dp.message.middleware(ErrorMiddleware())
    dp.callback_query.middleware(ErrorMiddleware())
    
    # ثبت روترهای جدید ویژگی‌ها
    dp.include_router(common_router)
    dp.include_router(buy_router)
    dp.include_router(wallet_router)
    dp.include_router(admin_router)
    dp.include_router(profile_router)
    dp.include_router(my_accounts_router)
    dp.include_router(panel_management_router)
    
    return dp

async def init_services():
    """راه‌اندازی سرویس‌های هسته"""
    global notification_service
    
    async with SessionLocal() as session:
        # راه‌اندازی سرویس نوتیفیکیشن
        notification_service = NotificationService(session)
        
        # همگام‌سازی ورودی‌های پنل
        panel_service = PanelService(session)
        try:
            sync_results = await panel_service.sync_all_panels_inbounds()
            logger.info(f"ورودی‌ها برای {len(sync_results)} پنل با موفقیت همگام‌سازی شدند")
        except Exception as e:
            logger.error(f"خطا در همگام‌سازی ورودی‌ها: {e}", exc_info=True)
            await notification_service.notify_admins(
                f"⚠️ خطا در همگام‌سازی ورودی‌ها:\n{str(e)}"
            )

async def main():
    """نقطه ورود اصلی برای ربات"""
    try:
        logger.info("در حال اجرای ربات MoonVPN...")
        
        # راه‌اندازی سرویس‌ها
        await init_services()
        
        # راه‌اندازی ربات و دیسپچر
        bot = await setup_bot()
        dp = await setup_dispatcher()
        
        # تنظیم نمونه ربات برای سرویس نوتیفیکیشن
        if notification_service:
            notification_service.set_bot(bot)
        
        # شروع polling
        logger.info("ربات MoonVPN آماده است!")
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
        
    except Exception as e:
        logger.critical(f"اجرای ربات با خطا مواجه شد: {e}", exc_info=True)
        raise
    finally:
        if 'redis_client' in locals() and redis_client:
            await redis_client.close()
        if notification_service:
            await notification_service.cleanup()

if __name__ == "__main__":
    if not REDIS_HOST or not REDIS_PORT:
        logger.error("متغیرهای محیطی REDIS_HOST یا REDIS_PORT تنظیم نشده‌اند!")
        exit(1)
        
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("ربات متوقف شد!")
    except Exception as e:
        logger.critical(f"خطای مرگبار: {e}", exc_info=True)
