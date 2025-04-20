"""
تنظیمات و پیکربندی اتصال به پایگاه داده
"""

import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from db.models import Base

# خواندن رشته اتصال از متغیرهای محیطی
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+aiomysql://user:password@db:3306/moonvpn")

# اگر URL حاوی pymysql است، آن را با aiomysql جایگزین کنیم
if "pymysql" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("pymysql", "aiomysql")

# ایجاد موتور AsyncSQL
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # در محیط توسعه True باشد
    future=True,
    poolclass=NullPool,
)

# ایجاد کننده جلسه برای دسترسی به دیتابیس
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    ایجاد یک جلسه دیتابیس و مدیریت آن در یک context manager
    """
    session = async_session_maker()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


# متدهای کمکی برای مدیریت دیتابیس
async def init_database() -> None:
    """
    ایجاد تمام جداول در زمان اجرا
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_database() -> None:
    """
    حذف تمام جداول (فقط برای تست)
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all) 