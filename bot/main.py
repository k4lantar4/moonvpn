"""
ربات تلگرام MoonVPN - نقطه ورود اصلی
"""

import os
import asyncio
import logging
from typing import Any, Dict

from aiogram import Bot, Dispatcher, Router
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from aiogram.client.default import DefaultBotProperties

from core.settings import DATABASE_URL, BOT_TOKEN
from core.services.notification_service import NotificationService
from core.services.panel_service import PanelService
from bot.commands import (
    start_router,
    register_buy_command,
    register_admin_commands,
    register_wallet_command,
    register_plans_command,
    register_profile_command,
    register_myaccounts_command,
)
from bot.callbacks import (
    register_buy_callbacks,
    register_wallet_callbacks,
    register_admin_callbacks,
    register_callbacks,
    register_plan_callbacks,
    register_panel_callbacks,
<<<<<<< HEAD
    register_inbound_callbacks,
    register_account_callbacks,
)
from bot.callbacks.admin_callbacks import register_admin_callbacks
from bot.callbacks.panel_callbacks import register_panel_callbacks
from bot.callbacks.inbound_callbacks import register_inbound_callbacks
=======
    register_account_callbacks,
)
from bot.callbacks.admin_callbacks import register_admin_callbacks
from bot.callbacks.user_callbacks import register_user_callbacks
from bot.callbacks.panel_callbacks import register_panel_callbacks
>>>>>>> 644afe0cd616ac99872ebfb4b1bd13f07cdc62c2
from bot.callbacks.client_callbacks import register_client_callbacks
from bot.middlewares import AuthMiddleware, ErrorMiddleware

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
    # راه‌اندازی storage و dispatcher
    storage = MemoryStorage() # نکته: برای پروداکشن، RediStorage ممکن است بهتر باشد
    dp = Dispatcher(storage=storage)
    
    # ایجاد روتر اصلی
    router = Router(name="main_router")
    
    # ثبت میدلورها
    dp.message.middleware(AuthMiddleware(SessionLocal))
    dp.callback_query.middleware(AuthMiddleware(SessionLocal))
    dp.message.middleware(ErrorMiddleware())
    dp.callback_query.middleware(ErrorMiddleware())
    
    # ثبت هندلرهای دستورات
    register_buy_command(router, SessionLocal)
    register_admin_commands(router, SessionLocal)
    register_wallet_command(router, SessionLocal)
    register_plans_command(router, SessionLocal)
    register_profile_command(router, SessionLocal)
    register_myaccounts_command(router, SessionLocal)
    
    # ثبت هندلرهای callback
    register_buy_callbacks(router, SessionLocal)
    register_wallet_callbacks(router, SessionLocal)
    register_admin_callbacks(router, SessionLocal)
    register_callbacks(router, SessionLocal)
    register_plan_callbacks(router, SessionLocal)
    # register panel callbacks for listing inbounds
    register_panel_callbacks(router, SessionLocal)
<<<<<<< HEAD
    register_inbound_callbacks(router, SessionLocal)
=======
>>>>>>> 644afe0cd616ac99872ebfb4b1bd13f07cdc62c2
    register_account_callbacks(router, SessionLocal)
    
    # افزودن روتر به دیسپچر
    dp.include_router(start_router)
    dp.include_router(router)
    
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
            await notification_service.notify_admins(
                f"🔄 ورودی‌های پنل با موفقیت همگام‌سازی شدند\n"
                f"تعداد پنل‌های همگام‌شده: {len(sync_results)}"
            )
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
        
        # ثبت هندلرهای callback
<<<<<<< HEAD
        # register_admin_callbacks(dp) # حذف شد - تکراری و در setup_dispatcher هست
        # register_user_callbacks(dp) # حذف شد - ماژول وجود ندارد
        # register_panel_callbacks(dp) # حذف شد - تکراری و در setup_dispatcher هست
        # register_inbound_callbacks(dp) # حذف شد - تکراری و در setup_dispatcher هست
        # register_client_callbacks(dp) # حذف شد - تکراری و در setup_dispatcher هست
=======
        register_admin_callbacks(dp)
        register_user_callbacks(dp)
        register_panel_callbacks(dp)
        register_client_callbacks(dp)
>>>>>>> 644afe0cd616ac99872ebfb4b1bd13f07cdc62c2
        
        # شروع polling
        logger.info("ربات MoonVPN آماده است!")
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.critical(f"اجرای ربات با خطا مواجه شد: {e}", exc_info=True)
        raise
    finally:
        if notification_service:
            await notification_service.cleanup()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("ربات متوقف شد!")
    except Exception as e:
        logger.critical(f"خطای مرگبار: {e}", exc_info=True)
