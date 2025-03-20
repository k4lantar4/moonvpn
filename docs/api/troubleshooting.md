# 🔧 راهنمای عیب‌یابی moonvpn

در این راهنما، روش‌های رفع مشکلات رایج هنگام نصب و اجرای moonvpn توضیح داده شده است.

## 📋 فهرست مطالب

1. [مشکلات دسترسی](#مشکلات-دسترسی)
2. [مشکلات اتصال به پایگاه داده](#مشکلات-اتصال-به-پایگاه-داده)
3. [مشکلات بات تلگرام](#مشکلات-بات-تلگرام)
4. [مشکلات بک‌اند](#مشکلات-بک-اند)
5. [مشکلات فرانت‌اند](#مشکلات-فرانت-اند)
6. [مشکلات Docker](#مشکلات-docker)

## مشکلات دسترسی

### خطای دسترسی به entrypoint.sh

اگر با خطای زیر مواجه شدید:
```
ERROR: for moonvpn_bot Cannot start service bot: failed to create task for container: failed to create shim task: OCI runtime create failed: runc create failed: unable to start container process: error during container init: exec: "/app/entrypoint.sh": permission denied: unknown
```

این خطا به دلیل نداشتن دسترسی اجرایی روی فایل `entrypoint.sh` است. برای حل این مشکل:

1. **استفاده از اسکریپت رفع مشکل دسترسی‌ها**:
   ```bash
   cd /opt/moonvpn
   sudo ./fix_permissions.sh
   ```

2. **بروزرسانی Dockerfile‌ها**:
   ```bash
   cd /opt/moonvpn
   sudo ./update_dockerfiles.sh
   ```

3. **بازسازی و راه‌اندازی مجدد سرویس‌ها**:
   ```bash
   cd /opt/moonvpn
   sudo docker-compose build --no-cache
   sudo docker-compose up -d
   ```

## مشکلات اتصال به پایگاه داده

### خطای اتصال به PostgreSQL

اگر بات یا بک‌اند نمی‌توانند به پایگاه داده متصل شوند:

1. **بررسی وضعیت سرویس PostgreSQL**:
   ```bash
   sudo docker ps | grep postgres
   ```

2. **بررسی لاگ‌های PostgreSQL**:
   ```bash
   sudo docker logs moonvpn_postgres
   ```

3. **بررسی تنظیمات اتصال**:
   - بررسی کنید که متغیرهای محیطی `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER` و `DB_PASSWORD` در `docker-compose.yml` به درستی تنظیم شده باشند.

4. **راه‌اندازی مجدد سرویس PostgreSQL**:
   ```bash
   sudo docker-compose restart postgres
   ```

## مشکلات بات تلگرام

### بات شروع به کار نمی‌کند

اگر بات تلگرام شروع به کار نمی‌کند:

1. **بررسی لاگ‌های بات**:
   ```bash
   sudo docker logs moonvpn_bot
   ```

2. **اطمینان از تنظیم توکن بات تلگرام**:
   - بررسی کنید که متغیر محیطی `TELEGRAM_BOT_TOKEN` در `docker-compose.yml` یا `.env` به درستی تنظیم شده باشد.

3. **بررسی دسترسی به اینترنت**:
   ```bash
   sudo docker exec -it moonvpn_bot curl -I https://api.telegram.org
   ```

4. **راه‌اندازی مجدد بات**:
   ```bash
   sudo moonvpn restart bot
   ```

## مشکلات بک‌اند

### بک‌اند اجرا نمی‌شود یا خطا می‌دهد

اگر بک‌اند اجرا نمی‌شود یا خطا می‌دهد:

1. **بررسی لاگ‌های بک‌اند**:
   ```bash
   sudo docker logs moonvpn_backend
   ```

2. **بررسی وضعیت وابستگی‌ها**:
   ```bash
   sudo docker exec -it moonvpn_backend pip list
   ```

3. **اجرای دستی مایگریشن‌ها**:
   ```bash
   sudo docker exec -it moonvpn_backend python manage.py migrate
   ```

4. **راه‌اندازی مجدد بک‌اند**:
   ```bash
   sudo moonvpn restart backend
   ```

## مشکلات فرانت‌اند

### صفحه وب نمایش داده نمی‌شود

اگر رابط کاربری وب نمایش داده نمی‌شود:

1. **بررسی لاگ‌های فرانت‌اند**:
   ```bash
   sudo docker logs moonvpn_frontend
   ```

2. **بررسی وضعیت Nginx**:
   ```bash
   sudo docker logs moonvpn_nginx
   ```

3. **راه‌اندازی مجدد سرویس‌های فرانت‌اند و Nginx**:
   ```bash
   sudo moonvpn restart frontend nginx
   ```

## مشکلات Docker

### مشکلات مربوط به Docker

اگر با مشکلات Docker مواجه شدید:

1. **بررسی وضعیت سرویس Docker**:
   ```bash
   sudo systemctl status docker
   ```

2. **راه‌اندازی مجدد Docker**:
   ```bash
   sudo systemctl restart docker
   ```

3. **بررسی فضای دیسک**:
   ```bash
   df -h
   ```

4. **پاکسازی کانتینرها و تصاویر استفاده نشده**:
   ```bash
   sudo docker system prune -a
   ```

5. **بروزرسانی Docker و Docker Compose**:
   ```bash
   sudo apt update && sudo apt upgrade docker-ce docker-compose-plugin
   ```

## 🆘 کمک بیشتر

اگر مشکل شما با روش‌های بالا حل نشد، می‌توانید:

1. **بررسی کامل لاگ‌ها**:
   ```bash
   sudo moonvpn logs -f
   ```

2. **بررسی وضعیت سیستم**:
   ```bash
   sudo moonvpn status
   ```

3. **تماس با پشتیبانی**:
   - از طریق بات تلگرام به آدرس [@moonvpnSupport_Bot](https://t.me/moonvpnSupport_Bot) با پشتیبانی تماس بگیرید.
   - یا به گروه پشتیبانی در تلگرام به آدرس [@moonvpnSupportGroup](https://t.me/moonvpnSupportGroup) مراجعه کنید.

4. **نصب مجدد**:
   در صورت نیاز، می‌توانید از اسکریپت نصب مجدد استفاده کنید:
   ```bash
   cd /opt
   sudo rm -rf /opt/moonvpn.bak
   sudo mv /opt/moonvpn /opt/moonvpn.bak
   curl -fsSL https://moonvpn.com/install.sh | sudo bash
   ``` 