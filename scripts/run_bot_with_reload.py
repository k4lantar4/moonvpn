#!/usr/bin/env python
"""
اسکریپت اجرای بات با قابلیت بارگذاری مجدد خودکار
با استفاده از watchdog برای نظارت بر تغییرات فایل‌ها
"""

import os
import sys
import time
import signal
import logging
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# تنظیمات لاگینگ
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("bot_reloader")

# مسیرهای مورد نظارت برای تغییرات
WATCH_PATHS = ["bot", "core", "db"]
# انواع فایل‌های مورد نظارت
WATCH_EXTENSIONS = [".py", ".yml", ".yaml", ".json"]
# زمان تأخیر بعد از تشخیص تغییر (برای جلوگیری از چندین بارگذاری مجدد همزمان)
RELOAD_DELAY = 3  # seconds

# متغیر کنترل پروسه بات
bot_process = None
last_reload_time = 0


def start_bot():
    """راه‌اندازی بات"""
    global bot_process
    if bot_process:
        stop_bot()
    
    logger.info("شروع اجرای بات...")
    bot_process = subprocess.Popen(
        [sys.executable, "-m", "bot.main"],
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    return bot_process


def stop_bot():
    """توقف بات"""
    global bot_process
    if bot_process:
        logger.info("توقف بات...")
        bot_process.send_signal(signal.SIGTERM)
        try:
            bot_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            bot_process.kill()
        bot_process = None


class BotReloader(FileSystemEventHandler):
    """کلاس مدیریت رویدادهای تغییر فایل‌ها"""
    
    def on_any_event(self, event):
        global last_reload_time
        
        # بررسی نوع رویداد و مسیر فایل
        if event.is_directory:
            return
        
        file_path = event.src_path
        _, file_ext = os.path.splitext(file_path)
        
        # نادیده گرفتن برخی فایل‌ها که مدام تغییر می‌کنند
        ignored_paths = ["db/models/__init__.py", "db/models/__pycache__"]
        for ignored_path in ignored_paths:
            if ignored_path in file_path:
                return
        
        # بررسی پسوند فایل
        if file_ext.lower() not in WATCH_EXTENSIONS:
            return
        
        # بررسی زمان آخرین بارگذاری مجدد برای جلوگیری از بارگذاری‌های مکرر
        current_time = time.time()
        if current_time - last_reload_time < RELOAD_DELAY:
            return
        
        last_reload_time = current_time
        logger.info(f"تغییر در فایل تشخیص داده شد: {file_path}")
        logger.info("بارگذاری مجدد بات...")
        
        # بارگذاری مجدد بات
        stop_bot()
        time.sleep(1)  # تأخیر کوتاه قبل از راه‌اندازی مجدد
        start_bot()


def main():
    """تابع اصلی اجرای بات با قابلیت بارگذاری مجدد"""
    logger.info("شروع سیستم بارگذاری مجدد خودکار بات MoonVPN...")
    
    # راه‌اندازی اولیه بات
    start_bot()
    
    # تنظیم نظارت بر فایل‌ها
    observer = Observer()
    event_handler = BotReloader()
    
    for path in WATCH_PATHS:
        if os.path.exists(path):
            logger.info(f"شروع نظارت بر مسیر: {path}")
            observer.schedule(event_handler, path, recursive=True)
    
    observer.start()
    
    try:
        while True:
            # بررسی وضعیت پروسه بات
            if bot_process and bot_process.poll() is not None:
                logger.warning("بات متوقف شده است. راه‌اندازی مجدد...")
                start_bot()
            
            # بررسی وجود فایل .reload_trigger
            trigger_file = os.path.join("bot", ".reload_trigger")
            if os.path.exists(trigger_file):
                logger.info("درخواست بارگذاری مجدد از طریق فایل trigger دریافت شد")
                os.remove(trigger_file)  # حذف فایل trigger
                stop_bot()
                time.sleep(1)
                start_bot()
            
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("دریافت سیگنال توقف...")
    finally:
        observer.stop()
        stop_bot()
        observer.join()
        logger.info("سیستم بارگذاری مجدد متوقف شد.")


if __name__ == "__main__":
    main() 