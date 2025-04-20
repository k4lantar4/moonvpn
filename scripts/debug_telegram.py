import os
import sys
import requests
from dotenv import load_dotenv

# مسیر اصلی پروژه
sys.path.append('/app')

# بارگذاری متغیرهای محیطی
load_dotenv()

# دریافت توکن بات از محیط
BOT_TOKEN = os.getenv("BOT_TOKEN")
print(f"توکن بات: {BOT_TOKEN[:5]}..." if BOT_TOKEN else "توکن بات یافت نشد!")

# تست اتصال به API تلگرام
try:
    print("\nتست ارتباط با تلگرام:")
    resp = requests.get(f'https://api.telegram.org/bot{BOT_TOKEN}/getMe')
    print(f"وضعیت پاسخ: {resp.status_code}")
    print(f"پاسخ: {resp.json()}")
except Exception as e:
    print(f"خطا در ارتباط با تلگرام: {e}")

# تست دسترسی به دیتابیس
try:
    print("\nتست دسترسی به دیتابیس:")
    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import sessionmaker
    from db.models.plan import Plan
    
    # تنظیمات دیتابیس
    DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:password@db:3306/moonvpn")
    print(f"آدرس دیتابیس: {DATABASE_URL}")
    
    # ایجاد اتصال به دیتابیس
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # ایجاد یک جلسه دیتابیس
    session = SessionLocal()
    
    # بررسی تعداد پلن‌ها
    plans = list(session.execute(select(Plan)).scalars().all())
    print(f"تعداد کل پلن‌ها: {len(plans)}")
    
    # نمایش پلن‌های فعال
    active_plans = list(session.execute(select(Plan).where(Plan.is_trial == False)).scalars().all())
    print(f"تعداد پلن‌های فعال: {len(active_plans)}")
    
    # نمایش اطلاعات پلن‌ها
    for plan in active_plans:
        print(f"- {plan.name}: {int(plan.price)} تومان، {plan.traffic} گیگابایت، {plan.duration_days} روز")
    
    # بستن جلسه
    session.close()
except Exception as e:
    print(f"خطا در دسترسی به دیتابیس: {e}")

print("\nاتمام اسکریپت تست") 