"""
هندلرهای کالبک پنل ادمین - نسخه بازنویسی شده

این فایل برای حفظ سازگاری با کد قبلی حفظ شده است.
تمام توابع به فایل‌های جداگانه در دایرکتوری admin/ منتقل شده‌اند.
"""

import logging
from aiogram import Router
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.callbacks.admin import register_all_admin_callbacks

logger = logging.getLogger(__name__)

def register_admin_callbacks(router: Router, session_pool: async_sessionmaker[AsyncSession]) -> None:
    """ثبت تمامی کالبک‌های ادمین"""
    logger.info("فراخوانی کالبک‌های ماژولار ادمین")
    register_all_admin_callbacks(router)
