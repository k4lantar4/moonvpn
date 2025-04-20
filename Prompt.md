# 🚀 MoonVPN - Step-by-Step Prompts for Project Setup

> این فایل مجموعه‌ای از پرامپت‌های زنجیره‌ای و فاز‌بندی‌شده است که باید به مدل Claude در Cursor IDE داده شود تا پروژه MoonVPN را به‌صورت دقیق، ایمن، و منظم توسعه دهد. هر پرامپت باید دقیقاً مطابق مستندات رسمی انجام شود و مدل نباید به‌هیچ‌وجه راه‌حل سرخود ارائه دهد. اگر خطایی یا ابهامی در اجرای تسک پیش آمد، باید توقف کرده و از کاربر سؤال بپرسد.

📍 محل اجرای پروژه: `/root/moonvpn`
📄 مستندات مرجع (قبل از اجرای هر تسک مرور شود):
- `docs/project-requirements.md`
- `docs/project-structure.md`
- `docs/database-structure.md`

📌 محیط توسعه Docker و اجرای تمام تست‌ها باید فقط از طریق CLI با دستور `moonvpn` انجام شود.

---

## 🧭 Phase 1: Project Bootstrap & Docker Setup

### 🧩 Task 1.1: Create Project Directory Structure and Files
```
مطابق دقیق فایل `docs/project-structure.md`، تمام دایرکتوری‌ها و فایل‌های اولیه پروژه را در مسیر /root/moonvpn بساز.
در هر فایل فقط یک کامنت توضیحی بنویس تا برای کدنویسی‌های بعدی آماده باشد.
هیچ فایلی خارج از این ساختار نباید ساخته شود.
```

### 🧩 Task 1.2: Initialize the Project with Poetry
```
مطابق `docs/project-requirements.md`، پروژه را با Poetry راه‌اندازی کن. نسخه Python = 3.12
فایل `pyproject.toml` را بساز ولی پکیجی نصب نکن.
فایل‌های پایه `.env`, `README.md`, `.gitignore` را بساز و در `.env` فقط موارد موردنیاز وارد کن (DB, REDIS, BOT_TOKEN).
```

### 🧩 Task 1.3: Create CLI Script - moonvpn
```
در scripts/ فایل اجرایی `moonvpn` بساز با قابلیت کنترل docker-compose برای up/down/logs/migrate/init.
این CLI باید بعداً در همه مراحل توسعه استفاده شود.
```

### 🧩 Task 1.4: Setup Docker & Services
```
فایل‌های `docker-compose.yml` و `Dockerfile` را بساز.
سرویس‌ها: app (با Poetry)، mysql، redis، phpmyadmin.
تنظیمات بر اساس env باشد. هیچ پورتی نباید مستقیماً با host تداخل داشته باشد.
```

---

## 🧭 Phase 2: Database Models & Migrations

### 🧩 Task 2.1: Create Initial Models - users, panels
```
مطابق `docs/database-structure.md`، فایل‌های db/models/user.py و db/models/panel.py را بساز.
مدل‌ها با SQLAlchemy نوشته شوند و در __init__.py ثبت شوند.
```

### 🧩 Task 2.2: Configure Alembic & Create First Migration
```
Alembic را تنظیم و اولین migration را بساز.
دستور `moonvpn migrate` باید جدول‌ها را ایجاد کند.
```

---

## 🧭 Phase 3: Bot & Aiogram Foundation

### 🧩 Task 3.1: Setup Aiogram Main Entry
```
فایل bot/main.py را بساز. Token را از `.env` بخوان.
ساختار فقط شامل Dispatcher و startup باشد.
```

### 🧩 Task 3.2: Create Start Command & User Registration
```
/start باید user را در دیتابیس ثبت کند (در صورت جدید بودن) و از keyboard ساده استفاده کند.
```

### 🧩 Task 3.3: Create /addpanel Command for Admin
```
اطلاعات پنل باید مرحله‌ای گرفته و در جدول panels ذخیره شود.
```

---

## 🧭 Phase 4: Panel Connection & Inbound Sync

### 🧩 Task 4.1: Install and Use py3xui SDK
```
مطابق `docs/project-requirements.md`:
- مخزن `https://github.com/iwatkot/py3xui` را به عنوان submodule یا dependency اضافه کن.
- در مسیر `core/integrations/xui_client.py` کلاسی بنویس که این SDK را wrap کند.
- از متدهای موجود مانند get_inbounds، create_client، delete_client استفاده کن.
نکته مهم: هیچ فایلی از SDK را ویرایش نکن.
اگر در نصب یا استفاده به مشکل برخوردی، از کاربر سؤال بپرس و خودسر مسیر را عوض نکن.
```

### 🧩 Task 4.2: Sync Inbounds to DB
```
در panel_service.py متدی برای گرفتن inbounds از هر پنل و ذخیره در جدول inbounds بنویس.
مدل مربوطه مطابق `docs/database-structure.md` ساخته شود و migration هم انجام گیرد.
```

---

(✅ ادامه دارد: فازهای بعدی شامل تعریف پلن، سفارش، خرید، تحویل کانفیگ، تخفیف، کیف پول و...)

