"""
اسکریپت موقت برای همگام‌سازی تمام پنل‌ها
"""

import asyncio
import logging
import sys
import os

# افزودن مسیر پروژه به sys.path برای import‌های نسبی
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from db import get_async_db
from core.services.panel_service import PanelService

# تنظیم لاگر
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def sync_all_panels():
    """همگام‌سازی تمام پنل‌های فعال"""
    try:
        logger.info("شروع همگام‌سازی دستی پنل‌ها...")
        
        # دریافت session دیتابیس
        session = None
        async for db_session in get_async_db():
            session = db_session
            break
        
        if not session:
            logger.error("امکان دریافت نشست دیتابیس وجود ندارد.")
            return
        
        # ایجاد سرویس پنل و همگام‌سازی
        panel_service = PanelService(session)
        results = await panel_service.sync_all_panels_inbounds()
        
        # کامیت تغییرات
        await session.commit()
        
        # نمایش نتایج
        logger.info(f"نتایج همگام‌سازی: {results}")
        logger.info("همگام‌سازی دستی پنل‌ها با موفقیت انجام شد.")
        
    except Exception as e:
        logger.error(f"خطا در همگام‌سازی دستی پنل‌ها: {e}", exc_info=True)
        if session:
            await session.rollback()
        raise

def main():
    """تابع اصلی برای اجرای همگام‌سازی"""
    asyncio.run(sync_all_panels())

if __name__ == "__main__":
    main() 