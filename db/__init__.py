"""
ماژول دیتابیس - نقطه دسترسی مرکزی به پایگاه داده
"""

import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

from db.models import Base

# خواندن رشته اتصال از متغیرهای محیطی
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+aiomysql://user:password@db:3306/moonvpn")

# ایجاد موتور SQL آسنکرون
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
    autocommit=False,
    autoflush=False
)


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    ایجاد یک جلسه دیتابیس آسنکرون و مدیریت آن در یک context manager
    """
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close() 