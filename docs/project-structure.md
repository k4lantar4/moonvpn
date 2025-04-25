# 📂 Project Directory Structure (MoonVPN)

## 📁 Root
- `docker-compose.yml` → تنظیم سرویس‌ها
- `Dockerfile` → بیلد ایمیج اپ
- `scripts/moonvpn.sh` → اسکریپت مدیریت پروژه
- `.env` / `.env.example` → متغیرهای محیطی

## 📁 bot/
- `commands/` → دستورات بات (start, wallet, buy,...)
- `buttons/` → تعریف دکمه‌های تکی
- `keyboards/` → ساخت کیبورد کامل
- `callbacks/` → هندل دکمه‌های inline
- `middlewares/` → auth, throttling
- `notifications/` → ارسال پیام به کانال‌ها
- `receipts/` → مدیریت رسیدهای بانکی
- `states/` → تعریف state های مربوط به فرم‌ها
- `main.py` → نقطه شروع بات

## 📁 core/
- `services/` → منطق سرویس‌ها (UserService, PaymentService,…)
- `integrations/xui_client.py` → ارتباط با پنل 3x-ui
- `scripts/` → اجرای دستی اسکریپت‌ها (seed panel, confirm payment)
- `settings.py` → تنظیمات پروژه از .env

## 📁 db/
- `models/` → مدل‌های SQLAlchemy (user, transaction, inbound,…)
- `schemas/` → pydantic schema برای ورودی/خروجی
- `repositories/` → واسط بین Service و DB
- `migrations/` → مایگریشن‌های alembic
- `config.py` → ساخت session

## 📁 docs/
- `project-requirements.md`
- `project-structure.md`
- `database-structure.md`
- `project-relationships.md`
- `scratchpad.md`

## 📁 tests/
- تست‌های ابتدایی سرویس‌ها

