# 📚 Bot Structure Report – MoonVPN

## ✅ دستورات موجود (bot/commands)

- `/start` → فایل: `bot/commands/start.py` → توضیح: شروع و ثبت کاربر
- `/buy` → فایل: `bot/commands/buy.py` → توضیح: منطق خرید پلن
- `/admin` → فایل: `bot/commands/admin.py` → توضیح: ورود ادمین
- `/wallet` → فایل: `bot/commands/wallet.py` → توضیح: مدیریت کیف پول
- `/plans` → فایل: `bot/commands/plans.py` → توضیح: نمایش پلن‌های موجود
- `/myaccounts` → فایل: `bot/commands/myaccounts.py` → توضیح: مدیریت اکانت‌های کاربر
- `/profile` → فایل: `bot/commands/profile.py` → توضیح: مشاهده و ویرایش پروفایل

## 🎛️ دکمه‌ها (keyboards & buttons)

### admin_keyboard.py
- 📊 آمار کلی → مسیر: `admin_callbacks.admin_stats`
- ➕ ثبت پنل جدید → مسیر: `admin_callbacks.register_panel`
- 👥 مدیریت کاربران → مسیر: `admin_callbacks.admin_users`
- 📝 مدیریت پلن‌ها → مسیر: `admin_callbacks.admin_plans`
- 💰 تراکنش‌ها → مسیر: `admin_callbacks.admin_transactions`
- ⚙️ تنظیمات → مسیر: `admin_callbacks.admin_settings`

### buy_keyboards.py
- انتخاب پلن → مسیر: `buy_callbacks`
- انتخاب لوکیشن → مسیر: `buy_callbacks`
- انتخاب پروتکل → مسیر: `buy_callbacks`
- پرداخت → مسیر: `buy_callbacks`

### wallet_keyboard.py
- 💰 شارژ کیف پول → مسیر: `wallet_callbacks`
- 📊 گزارش تراکنش‌ها → مسیر: `wallet_callbacks`

### start_keyboard.py
- 🛒 خرید اشتراک → مسیر: `start_buttons`
- 👤 پروفایل من → مسیر: `start_buttons`
- 💼 اکانت‌های من → مسیر: `start_buttons`

### profile_keyboard.py
- 📝 ویرایش نام → ⚠️ فقط پیام تست
- 🔄 تغییر زبان → ⚠️ فقط پیام تست

## 🔄 وضعیت‌های FSM (bot/states)

- `BuyState` → فایل: `bot/states/buy_states.py` → وضعیت‌های مربوط به خرید مرحله‌ای پلن
  - `select_plan` → انتخاب پلن
  - `select_location` → انتخاب لوکیشن
  - `select_inbound` → انتخاب پروتکل
  - `confirm_purchase` → تایید نهایی خرید
  - `payment` → پرداخت

- `RegisterPanelStates` → فایل: `bot/states/admin_states.py` → وضعیت‌های مربوط به ثبت پنل
  - `waiting_for_panel_url` → وارد کردن آدرس پنل
  - `waiting_for_username` → وارد کردن نام کاربری
  - `waiting_for_password` → وارد کردن رمز عبور
  - `waiting_for_location_name` → وارد کردن نام لوکیشن

- `AddPanel` → فایل: `bot/states/admin_states.py` → وضعیت‌های اضافه کردن پنل جدید (legacy)
  - `name` → وارد کردن نام پنل
  - `location` → وارد کردن موقعیت پنل
  - `flag_emoji` → وارد کردن ایموجی پرچم کشور
  - `url` → وارد کردن آدرس پنل
  - `username` → وارد کردن نام کاربری
  - `password` → وارد کردن رمز عبور
  - `default_label` → وارد کردن پیشوند نام اکانت پیش‌فرض
  - `confirmation` → تایید نهایی

- `AddInbound` → فایل: `bot/states/admin_states.py` → وضعیت‌های اضافه کردن اینباند جدید
  - `select_panel` → انتخاب پنل
  - `enter_protocol` → انتخاب پروتکل
  - `enter_port` → وارد کردن پورت
  - `enter_max_clients` → وارد کردن حداکثر تعداد کاربر
  - `confirm` → تایید نهایی

## 🔁 کالبک‌ها (bot/callbacks)

- `admin_callbacks.py` → مدیریت کلی ادمین
  - `admin_panel` → پنل اصلی ادمین
  - `admin_users` → مدیریت کاربران
  - `admin_plans` → مدیریت پلن‌ها
  - `admin_transactions` → مشاهده تراکنش‌ها
  - `admin_settings` → تنظیمات

- `buy_callbacks.py` → منطق خرید پلن
  - `select_plan` → انتخاب پلن
  - `select_location` → انتخاب لوکیشن
  - `select_inbound` → انتخاب پروتکل
  - `confirm_purchase` → تایید نهایی خرید
  - `process_payment` → پردازش پرداخت

- `wallet_callbacks.py` → مدیریت کیف پول
  - `charge_wallet` → شارژ کیف پول
  - `transactions_report` → گزارش تراکنش‌ها

- `panel_callbacks.py` → مدیریت پنل‌ها
  - `panel_inbounds_list` → لیست اینباندهای پنل
  - `show_inbound_details` → جزئیات اینباند

- `inbound_callbacks.py` → مدیریت اینباندها
  - `toggle_inbound` → فعال/غیرفعال کردن اینباند
  - `view_clients` → مشاهده کلاینت‌های اینباند
  - `add_client` → اضافه کردن کلاینت جدید

- `client_callbacks.py` → مدیریت کلاینت‌ها
  - `view_client_details` → جزئیات کلاینت
  - `reset_client_traffic` → ریست ترافیک کلاینت
  - `delete_client` → حذف کلاینت

- `common_callbacks.py` → منطق مشترک بین کالبک‌ها
  - `go_back` → بازگشت به منوی قبلی
  - `refresh` → بروزرسانی اطلاعات

- `account_callbacks.py` → مدیریت اکانت‌ها
  - `view_account_details` → جزئیات اکانت
  - `renew_account` → تمدید اکانت

- `plan_callbacks.py` → مدیریت پلن‌ها
  - `select_plan` → انتخاب پلن
  - `view_plan_details` → جزئیات پلن

## 📂 سایر ماژول‌ها

- `middlewares/` → میدلورها
  - `auth.py` → احراز هویت و کنترل دسترسی
  - `error.py` → مدیریت خطاها
  - `throttling.py` → محدودیت تعداد درخواست‌ها

- `receipts/` → مدیریت رسیدها
  - `receipt_states.py` → وضعیت‌های ارسال رسید

- `notifications/` → سیستم اطلاع‌رسانی
  - `dispatcher.py` → ارسال نوتیفیکیشن به کاربران 

# Bot Commands and Callbacks Log

This document lists the registered commands and callback handlers in the bot.

## Commands

*   `/admin` - `bot/commands/admin.py`
*   `/wallet` - `bot/commands/wallet.py`
*   `/profile` - `bot/commands/profile.py`
*   `/myaccounts` - `bot/commands/myaccounts.py`
*   `/plans` - `bot/commands/plans.py`
*   `/buy` - `bot/commands/buy.py`
*   `/start` - `bot/commands/start.py`

## Callbacks

The following files contain callback query handlers. Specific callback data patterns are defined within each file.

*   `admin_callbacks.py` - `bot/callbacks/admin_callbacks.py`
*   `panel_callbacks.py` - `bot/callbacks/panel_callbacks.py`
*   `common_callbacks.py` - `bot/callbacks/common_callbacks.py`
*   `inbound_callbacks.py` - `bot/callbacks/inbound_callbacks.py`
*   `client_callbacks.py` - `bot/callbacks/client_callbacks.py`
*   `wallet_callbacks.py` - `bot/callbacks/wallet_callbacks.py`
*   `account_callbacks.py` - `bot/callbacks/account_callbacks.py`
*   `buy_callbacks.py` - `bot/callbacks/buy_callbacks.py`
*   `plan_callbacks.py` - `bot/callbacks/plan_callbacks.py` 