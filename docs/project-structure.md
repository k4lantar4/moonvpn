# 🗂️ MoonVPN - Project Directory Structure

> Updated: 2025-04-21

ساختار دایرکتوری MoonVPN طوری طراحی شده که توسعه‌پذیر، تمیز، و قابل فهم برای هر توسعه‌دهنده یا مدل هوش مصنوعی باشد. تمامی فایل‌ها در محل مشخص و مجاز قرار دارند.

---

## 📁 Root Directory: `/root/moonvpn`

| Path | توضیح |
|------|-------|
| `.env` | تنظیمات محیطی برای کل سیستم |
| `docker-compose.yml` | اجرای تمام سرویس‌ها در داکر |
| `Dockerfile` | تصویر اپلیکیشن اصلی پایتون (poetry) |
| `pyproject.toml` | پیکربندی پویتری و وابستگی‌ها |
| `README.md` | توضیح کلی پروژه |
| `scripts/moonvpn.sh` | CLI مدیریت پروژه با دستورات مثل `moonvpn restart` |

---

## 🤖 bot/

| Path | نقش |
|------|-----|
| `bot/main.py` | اجرای ربات Aiogram |
| `bot/commands/` | دستورات اصلی ربات (start, buy, wallet, etc.) |
| `bot/callbacks/` | هندلرهای دکمه‌های اینلاین |
| `bot/buttons/` | دکمه‌های اینلاین سفارشی برای هر بخش |
| `bot/keyboards/` | دکمه‌های Reply برای ناوبری ربات |
| `bot/states.py` | تعریف Stateهای Form و Multi-step operations |
| `bot/middlewares/` | میدلویرها مانند AuthMiddleware برای نقش‌ها |
| `bot/notifications/` | مدیریت صف نوتیفیکیشن، اطلاع‌رسانی، پیام‌ها |
| `bot/receipts/` | مدیریت دریافت، لاگ و پاسخ رسیدهای کارت به کارت |

---

## 🧠 core/

| Path | نقش |
|------|-----|
| `core/services/` | منطق بیزینسی پروژه (UserService, PaymentService...) |
| `core/integrations/xui_client.py` | ارتباط با پنل 3x-ui با `py3xui.async_api.AsyncApi` |
| `core/scripts/` | ابزارهای جانبی مثل confirm_payment.py، تست‌ها، ابزارهای داخلی |
| `core/settings.py` | تنظیمات پیکربندی پروژه |

---

## 🧩 db/

| Path | نقش |
|------|-----|
| `db/models/` | مدل‌های SQLAlchemy (User, Panel, Inbound, Plan, Receipt, etc.) |
| `db/repositories/` | عملیات DB پیچیده و دسترسی ساده‌تر |
| `db/schemas/` | اسکیماهای Pydantic (در صورت نیاز) |
| `db/migrations/` | ساختار Alembic برای migration دیتابیس |
| `db/config.py` | اتصال به دیتابیس و راه‌اندازی Base ORM |

---

## 🧪 tests/

| Path | توضیح |
|------|------|
| `tests/test_*.py` | تست واحد برای سرویس‌ها و منطق اصلی |

---

## 📜 docs/

| فایل | کاربرد |
|------|--------|
| `project-requirements.md` | نیازمندی‌های پروژه (MVP و آینده) |
| `project-structure.md` | ساختار پوشه‌ها و فایل‌های پروژه |
| `database-structure.md` | مدل داده‌ها، روابط، ویژگی‌ها |
| `project-relationships.md` | جریان اطلاعات و تعامل بین اجزای سیستم |

---

## 🛠 scripts/

| فایل | توضیح |
|------|------|
| `moonvpn.sh` | اجرای دستورات CLI: up, down, restart, migrate, logs |
| `add_plans.py`، `check_code.py` | ابزارهای توسعه و رفع خطا یا داده اولیه |

---

## 📦 سایر موارد

| فایل/پوشه | توضیح |
|------------|------|
| `.cursor/rules/` | رول‌ها برای Cursor AI assistant (مدیریت رفتار مدل) |
| `.vscode/` | تنظیمات توسعه محلی برای VS Code |

---

## ✅ قوانین مهم ساختار

- هیچ فایل یا دایرکتوری خارج از مسیرهای فوق نباید ساخته شود.
- هر ماژول باید فقط وظیفه خودش را انجام دهد (Single Responsibility).
- فایل‌هایی که به بیش از 300 خط برسند باید تفکیک شوند.
- مسیر دسترسی به هر ماژول باید شفاف باشد تا مدل‌های هوش مصنوعی به‌درستی فایل‌ها را شناسایی کنند.
- فایل‌های رسید و پرداخت فقط در `bot/receipts` و `core/services/payment_service.py` باید توسعه یابند.
- ارتباط با پنل فقط از طریق `core/integrations/xui_client.py` مجاز است.

