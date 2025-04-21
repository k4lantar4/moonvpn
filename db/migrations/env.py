"""
فایل محیط Alembic برای مدیریت مهاجرت‌های پایگاه داده
"""

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# ایمپورت مدل‌های پایگاه داده
from db.models import Base
from core.settings import DATABASE_URL as ASYNC_DATABASE_URL

# این بخش تنظیمات اصلی Alembic را بارگذاری می‌کند
config = context.config

# این بخش تنظیمات فایل logging.ini را می‌خواند اگر وجود داشته باشد
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# مشخص کردن target برای autogenerate
target_metadata = Base.metadata

# تبدیل URL غیرهمزمان به URL همزمان برای Alembic
DATABASE_URL = ASYNC_DATABASE_URL
if "aiomysql" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("aiomysql", "pymysql")
    print(f"Alembic: درایور از aiomysql به pymysql تغییر یافت: {DATABASE_URL}")

# اگر DB در داکر اجرا می‌شود، باید URL را تغییر دهیم
if "localhost" in DATABASE_URL or "127.0.0.1" in DATABASE_URL:
    docker_host = "db"  # نام سرویس در docker-compose
    DATABASE_URL = DATABASE_URL.replace("localhost", docker_host).replace("127.0.0.1", docker_host)
    print(f"Updated for Docker: {DATABASE_URL}")

config.set_main_option("sqlalchemy.url", DATABASE_URL)


def run_migrations_offline() -> None:
    """
    اجرای مهاجرت‌ها در حالت آفلاین
    
    در این حالت، کانکشن دیتابیس باز نمی‌شود و SQL مستقیماً برای اجرا نوشته می‌شود
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    اجرای مهاجرت‌ها در حالت آنلاین
    
    در این حالت، یک کانکشن به دیتابیس باز می‌شود و مهاجرت‌ها روی آن اجرا می‌شوند
    """
    conf = config.get_section(config.config_ini_section)
    conf["sqlalchemy.url"] = DATABASE_URL

    # ایجاد موتور اتصال به دیتابیس
    engine = engine_from_config(
        conf,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with engine.connect() as connection:
        do_run_migrations(connection)


def do_run_migrations(connection):
    """
    اجرای مهاجرت‌ها با کانکشنی که از قبل ایجاد شده است
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online() 