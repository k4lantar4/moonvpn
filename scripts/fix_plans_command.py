"""
اسکریپت حل مشکل دستور /plans
"""

import asyncio
import logging
import os
import sys
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv

# تنظیم لاگینگ
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# بارگذاری متغیرهای محیطی
load_dotenv()

# دریافت توکن بات از محیط
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("No BOT_TOKEN found!")
    sys.exit(1)

# نشان دادن شروع توکن برای اطمینان
logger.info(f"Using bot token: {BOT_TOKEN[:5]}...")

async def set_commands(bot: Bot):
    """تنظیم دستورات قابل نمایش در منوی بات"""
    commands = [
        types.BotCommand(command="start", description="شروع بات"),
        types.BotCommand(command="plans", description="مشاهده پلن‌ها"),
        types.BotCommand(command="profile", description="پروفایل کاربری"),
        types.BotCommand(command="plans_test", description="تست دستور پلن‌ها"),
    ]
    await bot.set_my_commands(commands)
    logger.info("Bot commands set successfully")

async def main():
    """
    تابع اصلی برای تست دستور /plans
    """
    # ایجاد نمونه‌های Bot و Dispatcher
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    
    # ثبت دستورها
    @dp.message(Command("plans_test"))
    async def plans_test_command(message: types.Message):
        logger.info(f"Plans test command received from user {message.from_user.id}")
        await message.answer("✅ تست دستور پلن‌ها موفق بود!")
    
    # تنظیم لیست دستورات قابل نمایش
    await set_commands(bot)
    
    # اعلام تمام شدن اسکریپت
    logger.info("Commands registered and set successfully")
    await bot.close()

if __name__ == "__main__":
    asyncio.run(main())
    print("اسکریپت با موفقیت اجرا شد. حالا امتحان کنید دستور /plans_test را به بات بفرستید.") 