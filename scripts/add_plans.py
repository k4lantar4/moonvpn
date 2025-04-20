"""
اسکریپت افزودن پلن‌های نمونه به دیتابیس
"""

import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# اضافه کردن مسیر اصلی پروژه به sys.path
sys.path.append('/app')

from db.models.plan import Plan

# تنظیمات دیتابیس
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:password@db:3306/moonvpn")

# ایجاد اتصال به دیتابیس
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ایجاد یک جلسه دیتابیس
session = SessionLocal()

# بررسی وجود پلن
plan_count = session.query(Plan).count()
print(f"تعداد پلن‌های موجود: {plan_count}")

if plan_count > 0:
    print("پلن‌ها قبلاً در دیتابیس وجود دارند.")
    # حذف پلن‌های موجود برای تست مجدد
    session.query(Plan).delete()
    session.commit()
    print("پلن‌های موجود حذف شدند.")

# ایجاد چند پلن نمونه
plans = [
    Plan(
        name="پلن برنزی",
        traffic=30,
        duration_days=30,
        price=50000,
        available_locations=["FR", "NL", "DE"],
        is_trial=False
    ),
    Plan(
        name="پلن نقره‌ای",
        traffic=60,
        duration_days=30,
        price=80000,
        available_locations=["FR", "NL", "DE", "UK"],
        is_trial=False
    ),
    Plan(
        name="پلن طلایی",
        traffic=100,
        duration_days=30,
        price=120000,
        available_locations=None,  # تمام لوکیشن‌ها
        is_trial=False
    ),
    Plan(
        name="پلن تست",
        traffic=5,
        duration_days=1,
        price=0,
        available_locations=["FR"],
        is_trial=True
    )
]

# افزودن پلن‌ها به دیتابیس
for plan in plans:
    session.add(plan)

# ذخیره تغییرات
session.commit()
print(f"{len(plans)} پلن با موفقیت به دیتابیس اضافه شد:")
for p in session.query(Plan).all():
    print(f"- {p.name}: {int(p.price)} تومان، {p.traffic} گیگابایت، {p.duration_days} روز")

# بستن جلسه
session.close() 