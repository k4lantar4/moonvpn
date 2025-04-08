#!/usr/bin/env python3
"""
Seed Database Script (Direct SQL Version) for MoonVPN

این اسکریپت با استفاده از دستورات SQL مستقیم، داده‌های اولیه را در پایگاه داده وارد می‌کند:
- نقش‌ها (ادمین، فروشنده، کاربر)
- کاربر ادمین
- تنظیمات
- موقعیت‌های سرور
- دسته‌بندی‌های پلن
- پلن‌ها
- پنل‌های نمونه

Usage:
    python seed_db_direct.py [--force]

Notes:
    - این اسکریپت باید پس از مهاجرت‌های پایگاه داده اجرا شود
    - از دستورات SQL خام استفاده می‌کند تا مشکلات ناسازگاری با مدل‌ها را برطرف کند
"""

import logging
import sys
import time
from pathlib import Path
from argparse import ArgumentParser
from typing import Dict, List, Optional
import pymysql
import os
from dotenv import load_dotenv

# Add the parent directory to the path so we can import the API modules
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
sys.path.append(str(project_root))

# Load environment variables
load_dotenv(os.path.join(project_root, '.env'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("seed_db_direct")

# Default admin credentials
DEFAULT_ADMIN_TELEGRAM_ID = 123456789
DEFAULT_ADMIN_USERNAME = "admin"

# دریافت اطلاعات اتصال به دیتابیس از فایل .env
DB_HOST = os.getenv("MYSQL_HOST", "db")
DB_PORT = int(os.getenv("MYSQL_PORT", "3306"))
DB_USER = os.getenv("MYSQL_USER", "root")
DB_PASSWORD = os.getenv("MYSQL_ROOT_PASSWORD", "")
DB_NAME = os.getenv("MYSQL_DATABASE", "moonvpn_db")

def get_db_connection():
    """اتصال به پایگاه داده"""
    try:
        connection = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection
    except Exception as e:
        logger.error(f"خطا در اتصال به پایگاه داده: {e}")
        sys.exit(1)

def seed_roles(conn) -> Dict[str, int]:
    """ایجاد نقش‌های پایه در پایگاه داده"""
    logger.info("در حال ایجاد نقش‌ها...")
    
    roles_data = [
        {"name": "admin", "description": "نقش مدیر سیستم", "is_admin": 1, "is_seller": 0},
        {"name": "seller", "description": "نقش فروشنده", "is_admin": 0, "is_seller": 1},
        {"name": "user", "description": "نقش کاربر عادی", "is_admin": 0, "is_seller": 0}
    ]
    
    roles = {}
    
    with conn.cursor() as cursor:
        for role_data in roles_data:
            # بررسی وجود نقش
            check_sql = "SELECT id FROM roles WHERE name = %s"
            cursor.execute(check_sql, (role_data["name"]))
            existing_role = cursor.fetchone()
            
            if existing_role:
                logger.info(f"نقش '{role_data['name']}' از قبل وجود دارد")
                roles[role_data["name"]] = existing_role["id"]
                continue
            
            # ایجاد نقش جدید
            try:
                sql = """
                INSERT INTO roles (
                    name, description, is_admin, is_seller, 
                    can_manage_panels, can_manage_users, can_manage_plans, can_approve_payments, can_broadcast
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                permissions = {
                    "admin": (1, 1, 1, 1, 1),  # همه دسترسی‌ها برای ادمین
                    "seller": (0, 0, 0, 1, 0),  # فقط دسترسی‌های فروشنده
                    "user": (0, 0, 0, 0, 0)     # بدون دسترسی
                }
                
                cursor.execute(
                    sql, 
                    (
                        role_data["name"], 
                        role_data["description"], 
                        role_data["is_admin"], 
                        role_data["is_seller"],
                        *permissions[role_data["name"]]
                    )
                )
                
                roles[role_data["name"]] = cursor.lastrowid
                logger.info(f"نقش '{role_data['name']}' با موفقیت ایجاد شد")
            except Exception as e:
                logger.error(f"خطا در ایجاد نقش '{role_data['name']}': {e}")
                conn.rollback()
                raise
    
    conn.commit()
    return roles

def seed_admin_user(conn, roles: Dict[str, int]) -> int:
    """ایجاد کاربر ادمین در پایگاه داده"""
    logger.info("در حال ایجاد کاربر ادمین...")
    
    with conn.cursor() as cursor:
        # بررسی وجود ادمین
        check_sql = "SELECT id FROM users WHERE telegram_id = %s"
        cursor.execute(check_sql, (DEFAULT_ADMIN_TELEGRAM_ID))
        existing_admin = cursor.fetchone()
        
        if existing_admin:
            logger.info("کاربر ادمین از قبل وجود دارد")
            return existing_admin["id"]
        
        # ایجاد کاربر ادمین جدید
        try:
            sql = """
            INSERT INTO users (
                telegram_id, username, full_name, role_id, balance, is_active, is_banned, lang
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(
                sql, 
                (
                    DEFAULT_ADMIN_TELEGRAM_ID,
                    DEFAULT_ADMIN_USERNAME,
                    "Admin User",
                    roles["admin"],
                    0.0,  # balance
                    1,    # is_active
                    0,    # is_banned
                    "fa"  # lang
                )
            )
            
            admin_id = cursor.lastrowid
            logger.info("کاربر ادمین با موفقیت ایجاد شد")
            conn.commit()
            return admin_id
        except Exception as e:
            logger.error(f"خطا در ایجاد کاربر ادمین: {e}")
            conn.rollback()
            raise

def seed_locations(conn) -> Dict[str, int]:
    """ایجاد موقعیت‌های سرور در پایگاه داده"""
    logger.info("در حال ایجاد موقعیت‌های سرور...")
    
    locations_data = [
        {"name": "Germany", "country_code": "DE", "flag": "🇩🇪", "is_active": 1},
        {"name": "Netherlands", "country_code": "NL", "flag": "🇳🇱", "is_active": 1},
        {"name": "United States", "country_code": "US", "flag": "🇺🇸", "is_active": 1},
        {"name": "Singapore", "country_code": "SG", "flag": "🇸🇬", "is_active": 1},
        {"name": "United Kingdom", "country_code": "GB", "flag": "🇬🇧", "is_active": 1}
    ]
    
    locations = {}
    
    with conn.cursor() as cursor:
        # بررسی ساختار جدول موقعیت‌ها
        try:
            cursor.execute("DESCRIBE locations")
            columns = [column['Field'] for column in cursor.fetchall()]
            
            for location_data in locations_data:
                # بررسی وجود موقعیت
                check_sql = "SELECT id FROM locations WHERE country_code = %s"
                cursor.execute(check_sql, (location_data["country_code"]))
                existing_location = cursor.fetchone()
                
                if existing_location:
                    logger.info(f"موقعیت '{location_data['name']}' از قبل وجود دارد")
                    locations[location_data["country_code"]] = existing_location["id"]
                    continue
                
                # ایجاد موقعیت جدید - فقط با استفاده از ستون‌های موجود
                try:
                    fields = []
                    values = []
                    params = []
                    
                    for key, value in location_data.items():
                        if key in columns:
                            fields.append(key)
                            values.append("%s")
                            params.append(value)
                    
                    # افزودن description اگر در ستون‌ها وجود دارد
                    if "description" in columns and "description" not in location_data:
                        fields.append("description")
                        values.append("%s")
                        params.append(f"{location_data['name']} servers")
                    
                    sql = f"""
                    INSERT INTO locations ({', '.join(fields)})
                    VALUES ({', '.join(values)})
                    """
                    
                    cursor.execute(sql, params)
                    locations[location_data["country_code"]] = cursor.lastrowid
                    logger.info(f"موقعیت '{location_data['name']}' با موفقیت ایجاد شد")
                except Exception as e:
                    logger.error(f"خطا در ایجاد موقعیت '{location_data['name']}': {e}")
                    conn.rollback()
                    raise
        except Exception as e:
            logger.error(f"خطا در بررسی ساختار جدول موقعیت‌ها: {e}")
            raise
    
    conn.commit()
    return locations

def seed_plan_categories(conn) -> Dict[str, int]:
    """ایجاد دسته‌بندی‌های پلن در پایگاه داده"""
    logger.info("در حال ایجاد دسته‌بندی‌های پلن...")
    
    categories_data = [
        {"name": "Basic", "description": "پلن‌های پایه برای استفاده عادی", "color": "#28a745"},
        {"name": "Premium", "description": "پلن‌های پیشرفته با پهنای باند بیشتر", "color": "#dc3545"},
        {"name": "Business", "description": "پلن‌های تجاری برای استفاده حرفه‌ای", "color": "#007bff"}
    ]
    
    categories = {}
    
    with conn.cursor() as cursor:
        for cat_data in categories_data:
            # بررسی وجود دسته‌بندی
            check_sql = "SELECT id FROM plan_categories WHERE name = %s"
            cursor.execute(check_sql, (cat_data["name"]))
            existing_category = cursor.fetchone()
            
            if existing_category:
                logger.info(f"دسته‌بندی '{cat_data['name']}' از قبل وجود دارد")
                categories[cat_data["name"]] = existing_category["id"]
                continue
            
            # ایجاد دسته‌بندی جدید
            try:
                # بررسی ستون‌های موجود در جدول
                cursor.execute("DESCRIBE plan_categories")
                columns = [column['Field'] for column in cursor.fetchall()]
                
                fields = []
                values = []
                params = []
                
                for key, value in cat_data.items():
                    if key in columns:
                        fields.append(key)
                        values.append("%s")
                        params.append(value)
                
                sql = f"""
                INSERT INTO plan_categories ({', '.join(fields)})
                VALUES ({', '.join(values)})
                """
                
                cursor.execute(sql, params)
                categories[cat_data["name"]] = cursor.lastrowid
                logger.info(f"دسته‌بندی '{cat_data['name']}' با موفقیت ایجاد شد")
            except Exception as e:
                logger.error(f"خطا در ایجاد دسته‌بندی '{cat_data['name']}': {e}")
                conn.rollback()
                raise
    
    conn.commit()
    return categories

def seed_plans(conn, categories: Dict[str, int]) -> None:
    """ایجاد پلن‌ها در پایگاه داده"""
    logger.info("در حال ایجاد پلن‌ها...")
    
    plans_data = [
        {
            "name": "Basic Monthly",
            "description": "پلن ماهانه پایه با 50 گیگابایت ترافیک",
            "price": 10.0,
            "traffic": 50 * 1024 * 1024 * 1024,  # 50GB to bytes
            "duration": 30 * 24 * 60 * 60,  # 30 days to seconds
            "category_id": categories["Basic"],
            "is_active": 1
        },
        {
            "name": "Premium Monthly",
            "description": "پلن ماهانه پیشرفته با 100 گیگابایت ترافیک",
            "price": 20.0,
            "traffic": 100 * 1024 * 1024 * 1024,
            "duration": 30 * 24 * 60 * 60,
            "category_id": categories["Premium"],
            "is_active": 1
        },
        {
            "name": "Business Monthly",
            "description": "پلن ماهانه تجاری با 200 گیگابایت ترافیک",
            "price": 40.0,
            "traffic": 200 * 1024 * 1024 * 1024,
            "duration": 30 * 24 * 60 * 60,
            "category_id": categories["Business"],
            "is_active": 1
        }
    ]
    
    with conn.cursor() as cursor:
        # بررسی ستون‌های موجود در جدول
        cursor.execute("DESCRIBE plans")
        columns = [column['Field'] for column in cursor.fetchall()]
        
        for plan_data in plans_data:
            # بررسی وجود پلن
            check_sql = "SELECT id FROM plans WHERE name = %s"
            cursor.execute(check_sql, (plan_data["name"]))
            existing_plan = cursor.fetchone()
            
            if existing_plan:
                logger.info(f"پلن '{plan_data['name']}' از قبل وجود دارد")
                continue
            
            # ایجاد پلن جدید
            try:
                fields = []
                values = []
                params = []
                
                for key, value in plan_data.items():
                    if key in columns:
                        fields.append(key)
                        values.append("%s")
                        params.append(value)
                
                sql = f"""
                INSERT INTO plans ({', '.join(fields)})
                VALUES ({', '.join(values)})
                """
                
                cursor.execute(sql, params)
                logger.info(f"پلن '{plan_data['name']}' با موفقیت ایجاد شد")
            except Exception as e:
                logger.error(f"خطا در ایجاد پلن '{plan_data['name']}': {e}")
                conn.rollback()
                raise
    
    conn.commit()

def seed_settings(conn) -> None:
    """ایجاد تنظیمات پایه در پایگاه داده"""
    logger.info("در حال ایجاد تنظیمات...")
    
    settings_data = [
        {"key": "site_name", "value": "MoonVPN", "description": "نام سایت", "is_public": 1},
        {"key": "site_url", "value": "https://moonvpn.example.com", "description": "آدرس سایت", "is_public": 1},
        {"key": "default_language", "value": "fa", "description": "زبان پیش‌فرض سایت", "is_public": 1},
        {"key": "maintenance_mode", "value": "false", "description": "حالت تعمیر و نگهداری", "is_public": 0}
    ]
    
    with conn.cursor() as cursor:
        # بررسی وجود جدول تنظیمات
        try:
            for setting_data in settings_data:
                # بررسی وجود تنظیم
                check_sql = "SELECT id FROM settings WHERE `key` = %s"
                cursor.execute(check_sql, (setting_data["key"]))
                existing_setting = cursor.fetchone()
                
                if existing_setting:
                    logger.info(f"تنظیم '{setting_data['key']}' از قبل وجود دارد")
                    continue
                
                # ایجاد تنظیم جدید
                try:
                    cursor.execute("DESCRIBE settings")
                    columns = [column['Field'] for column in cursor.fetchall()]
                    
                    fields = []
                    values = []
                    params = []
                    
                    for key, value in setting_data.items():
                        if key in columns:
                            fields.append(f"`{key}`" if key == "key" or key == "value" or key == "group" else key)
                            values.append("%s")
                            params.append(value)
                    
                    sql = f"""
                    INSERT INTO settings ({', '.join(fields)})
                    VALUES ({', '.join(values)})
                    """
                    
                    cursor.execute(sql, params)
                    logger.info(f"تنظیم '{setting_data['key']}' با موفقیت ایجاد شد")
                except Exception as e:
                    logger.error(f"خطا در ایجاد تنظیم '{setting_data['key']}': {e}")
                    conn.rollback()
                    raise
        except Exception as e:
            logger.error(f"خطا در بررسی جدول تنظیمات: {e}")
            conn.rollback()
    
    conn.commit()

def seed_panels(conn, locations: Dict[str, int]) -> None:
    """ایجاد پنل‌های نمونه در پایگاه داده"""
    logger.info("در حال ایجاد پنل‌های نمونه...")
    
    panels_data = [
        {
            "name": "Germany Panel 1",
            "url": "https://de1.moonvpn.example.com:2053",
            "username": "admin",
            "password": "adminpass",
            "location_id": locations["DE"],
            "is_active": 1
        },
        {
            "name": "Netherlands Panel 1",
            "url": "https://nl1.moonvpn.example.com:2053",
            "username": "admin",
            "password": "adminpass",
            "location_id": locations["NL"],
            "is_active": 1
        }
    ]
    
    with conn.cursor() as cursor:
        # بررسی ستون‌های موجود در جدول
        cursor.execute("DESCRIBE panels")
        columns = [column['Field'] for column in cursor.fetchall()]
        
        for panel_data in panels_data:
            # بررسی وجود پنل
            check_sql = "SELECT id FROM panels WHERE url = %s"
            cursor.execute(check_sql, (panel_data["url"]))
            existing_panel = cursor.fetchone()
            
            if existing_panel:
                logger.info(f"پنل '{panel_data['name']}' از قبل وجود دارد")
                continue
            
            # ایجاد پنل جدید
            try:
                fields = []
                values = []
                params = []
                
                for key, value in panel_data.items():
                    if key in columns:
                        fields.append(key)
                        values.append("%s")
                        params.append(value)
                
                sql = f"""
                INSERT INTO panels ({', '.join(fields)})
                VALUES ({', '.join(values)})
                """
                
                cursor.execute(sql, params)
                logger.info(f"پنل '{panel_data['name']}' با موفقیت ایجاد شد")
            except Exception as e:
                logger.error(f"خطا در ایجاد پنل '{panel_data['name']}': {e}")
                conn.rollback()
                raise
    
    conn.commit()

def main():
    """نقطه ورودی برای وارد کردن داده‌های پایه"""
    argparser = ArgumentParser(description="وارد کردن داده‌های پایه در پایگاه داده")
    argparser.add_argument(
        "-f", "--force", help="ایجاد اجباری داده‌های پایه، حتی اگر از قبل وجود داشته باشند", 
        action="store_true"
    )
    args = argparser.parse_args()
    
    logger.info("شروع فرایند وارد کردن داده‌های پایه...")
    
    # اتصال به پایگاه داده
    try:
        conn = get_db_connection()
        
        # بررسی وجود داده‌های پایه
        with conn.cursor() as cursor:
            try:
                cursor.execute("SELECT COUNT(*) as count FROM users")
                result = cursor.fetchone()
                count = result["count"] if result else 0
                
                if count > 0 and not args.force:
                    logger.info(
                        "پایگاه داده از قبل دارای کاربر است. برای ایجاد اجباری داده‌های پایه، از --force استفاده کنید."
                    )
                    return
                
                if args.force:
                    logger.warning("پرچم force تنظیم شده است. در حال بازآفرینی داده‌های پایه...")
            except Exception as e:
                logger.warning(f"خطا در بررسی وجود داده‌های پایه: {e}")
                logger.warning("ادامه فرایند وارد کردن داده‌های پایه...")
        
        # وارد کردن داده‌های پایه
        try:
            roles = seed_roles(conn)
            seed_admin_user(conn, roles)
            locations = seed_locations(conn)
            categories = seed_plan_categories(conn)
            seed_plans(conn, categories)
            seed_settings(conn)
            seed_panels(conn, locations)
            
            logger.info("فرایند وارد کردن داده‌های پایه با موفقیت انجام شد!")
        except Exception as e:
            logger.error(f"خطا در فرایند وارد کردن داده‌های پایه: {e}")
            conn.rollback()
    except Exception as e:
        logger.error(f"خطا در اتصال به پایگاه داده: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main() 