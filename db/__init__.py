"""
ماژول دیتابیس - نقطه دسترسی مرکزی به پایگاه داده
"""

import os
from typing import Generator
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool

from db.models import Base

# خواندن رشته اتصال از متغیرهای محیطی
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://user:password@db:3306/moonvpn")

# ایجاد موتور SQL سنکرون برای اسکریپت‌ها
engine = create_engine(
    DATABASE_URL,
    echo=False,  # در محیط توسعه True باشد
    future=True,
    poolclass=NullPool,
)

# ایجاد کننده جلسه برای دسترسی به دیتابیس
session_maker = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    ایجاد یک جلسه دیتابیس سنکرون و مدیریت آن در یک context manager
    این برای استفاده در اسکریپت‌های CLI است.
    
    برای استفاده در ربات، از async_db استفاده کنید.
    """
    session = session_maker()
    try:
        yield session
    finally:
        session.close() 