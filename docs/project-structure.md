# 📁 Project Structure (Finalized, Strict, and Modular)

```
moonvpn/
├── bot/
│   ├── commands/              # Command handlers: /start, /buy, /profile, etc.
│   │   ├── __init__.py
│   │   ├── start.py           # /start command logic
│   │   ├── profile.py         # /profile and user info
│   │   ├── plans.py           # /plans and plan selection
│   │   └── admin.py           # Admin-only commands like /add_panel
│   │
│   ├── callbacks/             # Callback query handlers for inline buttons
│   │   ├── __init__.py
│   │   └── common.py          # Shared callbacks for menu navigation
│   │
│   ├── keyboards/             # ReplyKeyboardMarkup definitions
│   │   ├── __init__.py
│   │   └── user_keyboard.py   # Keyboards for user navigation
│   │
│   ├── buttons/               # InlineKeyboardMarkup definitions
│   │   ├── __init__.py
│   │   └── plan_buttons.py    # Buttons for plan selection
│   │
│   ├── notifications/         # Notification dispatcher: user, admin, channel
│   │   ├── __init__.py
│   │   └── dispatcher.py      # notify_user(), notify_admin(), notify_channel()
│   │
│   ├── middlewares/           # Middleware for auth, throttling
│   │   ├── __init__.py
│   │   └── auth_middleware.py # Authenticate and role-check
│   │
│   ├── main.py                # Entry point, Dispatcher & Router setup
│   └── __init__.py
│
├── core/
│   ├── integrations/
│   │   └── xui_client.py      # Wrapper for 3x-ui API using py3xui
│   ├── services/
│   │   ├── user_service.py        # User registration, profile, permission logic
│   │   ├── account_service.py     # VPN account creation, renewal, deletion, renaming
│   │   ├── panel_service.py       # Add/edit/remove panels, fetch inbounds, defaults
│   │   ├── payment_service.py     # Wallet and transaction logic
│   │   ├── discount_service.py    # Code validation and application
│   │   ├── notification_service.py# Routing messages (Telegram, admin, channel)
│   │   └── settings_service.py    # Manage and fetch dynamic settings
│   └── settings.py                # Static config (API tokens, channel IDs, naming rules)
│
├── db/
│   ├── models/
│   │   ├── user.py
│   │   ├── panel.py
│   │   ├── inbound.py
│   │   ├── client_account.py
│   │   ├── plan.py
│   │   ├── order.py
│   │   ├── transaction.py
│   │   ├── discount_code.py
│   │   ├── test_account_log.py
│   │   └── account_transfer.py
│   ├── schemas/
│   │   ├── user_schema.py
│   │   └── account_schema.py
│   ├── repositories/
│   │   ├── user_repo.py
│   │   └── account_repo.py
│   └── migrations/              # Alembic migration scripts
│
├── scripts/
│   └── moonvpn                 # CLI tool to manage the project
│
├── tests/
│   ├── test_user.py
│   ├── test_account.py
│   └── __init__.py
│
├── docker-compose.yml         # Compose file for all services
├── Dockerfile                 # App build configuration
├── pyproject.toml             # Poetry project and dependencies
├── .env                       # Environment config for app/docker
└── README.md                  # Project overview and development guide
```

---

## 📦 Explanation of Key Files in `bot/`

- `main.py` → ستاپ ربات، ثبت فرمان‌ها و اتصال به event handlers

### `commands/`
- `start.py` → خوشامدگویی، ثبت‌نام اولیه
- `profile.py` → نمایش اطلاعات و تنظیمات کاربر
- `plans.py` → لیست و انتخاب پلن‌ها
- `admin.py` → دستورات ادمین مثل اضافه کردن پنل

### `callbacks/`
- `common.py` → مدیریت دکمه‌های inline مثل بازگشت، جزئیات پلن

### `keyboards/`
- `user_keyboard.py` → ReplyKeyboardMarkup برای کاربران (مثل منو اصلی)

### `buttons/`
- `plan_buttons.py` → دکمه‌های inline مربوط به پلن‌ها

### `notifications/`
- `dispatcher.py` → تابع‌های `notify_user()`, `notify_admin()`, `notify_channel()` برای ارسال نوتیفیکیشن

### `middlewares/`
- `auth_middleware.py` → اعتبارسنجی و تشخیص نقش کاربر برای مدیریت دسترسی‌ها

---

✅ با مشخص‌کردن دقیق فایل‌ها و وظایف، دستیار هوش مصنوعی هیچ فایلی خارج از این لیست ایجاد نمی‌کند و مسیر توسعه شفاف و قابل پیگیری باقی می‌ماند.

