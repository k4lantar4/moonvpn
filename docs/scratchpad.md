# بررسی تعامل کاربر با ربات

## فهرست کامندها
- /start
- /profile
- /plans
- /wallet
- /buy
- /myaccounts
- (help) ← از طریق دکمه راهنما (بدون handler)
- (/admin) ← مخصوص مدیران (در این مرحله بررسی نمی‌شود)

## کیبوردهای ReplyKeyboard (کاربران معمولی)
- 🛒 خرید سرویس → /buy
- 💳 کیف پول → /wallet
- 📊 اشتراک‌های من → /myaccounts
- ❓ راهنما → handler ندارد
- 💬 پشتیبانی → handler ندارد
- 👤 حساب کاربری → /profile (F.text handler ندارد)

## InlineKeyboard (get_start_keyboard)
- 🛒 خرید سرویس (callback_data="buy_plans") → handler موجود
- 💳 کیف پول (callback_data="wallet_menu") → handler ندارد
- 📊 اشتراک‌های من (callback_data="my_accounts") → handler ندارد
- ❓ راهنما (callback_data="help_menu") → handler ندارد
- 💬 پشتیبانی (callback_data="support_chat") → handler ندارد

## وضعیت فارسی‌سازی
- پیام‌های `/start`، `/buy`، `/plans` و بخش کیف پول کاملاً فارسی هستند.
- پیام‌ها و دکمه‌های بخش `/profile` به انگلیسی هستند.

## وضعیت هندلرها
- `/start`: ثبت و عملکرد صحیح
- `/profile`: ثبت‌شده اما بدون F.text alias برای دکمه و پیام خطای ابتدایی انگلیسی
- `/plans`: ثبت‌شده با slash، اما هیچ دکمه‌ای در کیبورد برای دسترسی ندارد
- `/wallet`: ثبت‌شده با slash و F.text alias، اما callback برای wallet_menu ندارد
- `/buy`: ثبت‌شده با slash و F.text alias و callback صحیح
- `/myaccounts`: تابع موجود اما ثبت نشده (در __init__ و main.py)
- callback برای `my_accounts`, `help_menu` و `support_chat` تعریف نشده

## لیست مشکلات
1. ثبت نکردن `register_myaccounts_command` در `bot/commands/__init__.py` و `main.py`
2. فقدان handler برای F.text == "👤 حساب کاربری"
3. پیام‌ها و دکمه‌های بخش پروفایل (InlineKeyboard) به زبان انگلیسی هستند
4. عدم تعریف handler برای callback_dataهای `wallet_menu`, `my_accounts`, `help_menu` و `support_chat`
5. عدم تطابق نام دکمه در myaccounts: "🛒 خرید اشتراک" vs "🛒 خرید سرویس"
6. عدم وجود متد `create_transaction` در `PaymentService` که باعث خطا می‌شود
