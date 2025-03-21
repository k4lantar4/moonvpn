# راهنمای توسعه‌دهندگان MoonVPN

این مستند شامل اطلاعات و راهنمایی‌های لازم برای توسعه‌دهندگانی است که روی پروژه MoonVPN کار می‌کنند.

## ساختار پروژه

پروژه MoonVPN از دو بخش اصلی تشکیل شده:

1. **بات تلگرام (bot/)** - بات تلگرام برای تعامل با کاربران
2. **بک‌اند (backend/)** - سرویس API برای مدیریت کاربران، اشتراک‌ها، و ارتباط با پنل 3x-UI

## راه‌اندازی محیط توسعه

### 1. نصب وابستگی‌ها

```bash
pip install -r requirements.txt
```

### 2. تنظیم متغیرهای محیطی

یک فایل `.env` در مسیر اصلی پروژه ایجاد کنید و متغیرهای زیر را تنظیم کنید:

```
TELEGRAM_BOT_TOKEN=your_bot_token
```

برای تنظیمات کامل‌تر، فایل `.env` را در مسیر `backend/` قرار دهید.

### 3. اجرای بات تلگرام

برای اجرای بات به یکی از روش‌های زیر عمل کنید:

#### روش 1: اجرای بات کامل (با Django)

```bash
cd /root/moonvpn/bot
python main.py
```

#### روش 2: اجرای بات حداقلی (بدون Django)

```bash
cd /root/moonvpn
python minimal_bot.py
```

## عیب‌یابی

### عیب‌یابی مشکلات بات تلگرام

1. **مشکل ارتباط با تلگرام**:
   
   اطمینان حاصل کنید که توکن بات صحیح است و اینترنت شما متصل است.

2. **خطای Django**:

   اگر با خطای `Failed to configure Django` مواجه شدید، می‌توانید از نسخه مستقل بات استفاده کنید:

   ```bash
   python minimal_bot.py
   ```

3. **مشکل دسترسی به پایگاه داده**:

   اطمینان حاصل کنید که پایگاه داده PostgreSQL در دسترس است و تنظیمات آن در فایل `.env` صحیح است.

### ارتباط با پنل 3x-UI

برای ارتباط با پنل 3x-UI، از کلاس `ThreeXUIClient` در ماژول `api_client.py` استفاده کنید. این کلاس امکانات زیر را فراهم می‌کند:

- احراز هویت با پنل
- مدیریت کاربران وی‌پی‌ان
- کنترل اشتراک‌ها
- دریافت آمار ترافیک

## راهنمای توسعه‌دهندگان

### افزودن دستورات جدید به بات

1. یک فایل جدید در پوشه `handlers` ایجاد کنید.
2. دستور را تعریف کنید و آن را به `main.py` اضافه کنید.

مثال:

```python
async def new_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the new command."""
    await update.message.reply_text("این دستور جدید است.")

# در فایل main.py
application.add_handler(CommandHandler("new_command", new_command))
```

### کار با پایگاه داده

برای کار با پایگاه داده از ماژول `utils.database` استفاده کنید:

```python
from utils.database import execute_query, execute_insert, execute_update

# اجرای یک کوئری
results = execute_query("SELECT * FROM users WHERE id = %s", (user_id,))

# درج یک رکورد جدید
new_id = execute_insert("INSERT INTO users (name, email) VALUES (%s, %s)", (name, email))

# به‌روزرسانی یک رکورد
success = execute_update("UPDATE users SET name = %s WHERE id = %s", (name, user_id))
```

## روال توسعه

1. **برنچینگ**: برای هر ویژگی یا باگ، یک شاخه جدید ایجاد کنید.
2. **تست**: قبل از ادغام، تغییرات را تست کنید.
3. **مستندات**: تغییرات خود را مستند کنید.
4. **ادغام**: پس از اطمینان از درستی تغییرات، آن‌ها را با شاخه اصلی ادغام کنید.

## منابع مفید

- [مستندات python-telegram-bot](https://python-telegram-bot.readthedocs.io/)
- [مستندات Django](https://docs.djangoproject.com/)
- [آموزش‌های API تلگرام](https://core.telegram.org/bots/api) 