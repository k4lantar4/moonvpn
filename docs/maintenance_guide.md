# MoonVPN Maintenance Guide
# راهنمای نگهداری MoonVPN

## Table of Contents | فهرست مطالب
1. [System Architecture | معماری سیستم](#system-architecture)
2. [Server Management | مدیریت سرور](#server-management)
3. [Database Maintenance | نگهداری پایگاه داده](#database-maintenance)
4. [Monitoring & Alerts | نظارت و هشدارها](#monitoring-and-alerts)
5. [Backup & Recovery | پشتیبان‌گیری و بازیابی](#backup-and-recovery)
6. [Security Management | مدیریت امنیت](#security-management)
7. [Troubleshooting | عیب‌یابی](#troubleshooting)

## System Architecture | معماری سیستم

### Components | اجزا
1. FastAPI Backend | بک‌اند FastAPI
2. Telegram Bot | ربات تلگرام
3. PostgreSQL Database | پایگاه داده PostgreSQL
4. Redis Cache | کش Redis
5. 3x-ui VPN Panels | پنل‌های VPN 3x-ui

### Service Dependencies | وابستگی‌های سرویس
- PostgreSQL 13+ | PostgreSQL 13+
- Redis 6+ | Redis 6+
- Python 3.9+ | Python 3.9+
- Docker 20.10+ | Docker 20.10+

## Server Management | مدیریت سرور

### Daily Tasks | وظایف روزانه
1. Check system logs | بررسی لاگ‌های سیستم
2. Monitor resource usage | نظارت بر مصرف منابع
3. Verify service status | تایید وضعیت سرویس‌ها
4. Review error reports | بررسی گزارش‌های خطا

### Weekly Tasks | وظایف هفتگی
1. Update system packages | بروزرسانی پکیج‌های سیستم
2. Review security logs | بررسی لاگ‌های امنیتی
3. Check backup integrity | بررسی صحت پشتیبان‌ها
4. Clean temporary files | پاکسازی فایل‌های موقت

### Monthly Tasks | وظایف ماهانه
1. System performance review | بررسی عملکرد سیستم
2. Security audit | ممیزی امنیتی
3. Database optimization | بهینه‌سازی پایگاه داده
4. SSL certificate check | بررسی گواهینامه SSL

## Database Maintenance | نگهداری پایگاه داده

### Backup Schedule | برنامه پشتیبان‌گیری
- Daily incremental backups | پشتیبان‌گیری افزایشی روزانه
- Weekly full backups | پشتیبان‌گیری کامل هفتگی
- Monthly archive backups | پشتیبان‌گیری آرشیوی ماهانه

### Optimization Tasks | وظایف بهینه‌سازی
1. Vacuum analysis | تحلیل Vacuum
2. Index maintenance | نگهداری ایندکس‌ها
3. Query optimization | بهینه‌سازی کوئری‌ها
4. Storage cleanup | پاکسازی فضای ذخیره‌سازی

## Monitoring and Alerts | نظارت و هشدارها

### System Metrics | معیارهای سیستم
- CPU usage | مصرف CPU
- Memory usage | مصرف حافظه
- Disk usage | مصرف دیسک
- Network traffic | ترافیک شبکه
- Response times | زمان‌های پاسخ
- Error rates | نرخ خطاها

### Alert Thresholds | آستانه‌های هشدار
- CPU > 80% | CPU > ۸۰٪
- Memory > 85% | حافظه > ۸۵٪
- Disk > 90% | دیسک > ۹۰٪
- Response time > 2s | زمان پاسخ > ۲ ثانیه

## Backup and Recovery | پشتیبان‌گیری و بازیابی

### Backup Types | انواع پشتیبان‌گیری
1. Database backups | پشتیبان پایگاه داده
2. Configuration backups | پشتیبان پیکربندی
3. User data backups | پشتیبان داده‌های کاربران
4. System state backups | پشتیبان وضعیت سیستم

### Recovery Procedures | روش‌های بازیابی
1. Database recovery | بازیابی پایگاه داده
2. Service recovery | بازیابی سرویس
3. Configuration recovery | بازیابی پیکربندی
4. Full system recovery | بازیابی کامل سیستم

## Security Management | مدیریت امنیت

### Regular Tasks | وظایف منظم
1. Update security patches | بروزرسانی وصله‌های امنیتی
2. Review access logs | بررسی لاگ‌های دسترسی
3. Check firewall rules | بررسی قوانین فایروال
4. Monitor suspicious activity | نظارت بر فعالیت‌های مشکوک

### Security Policies | سیاست‌های امنیتی
1. Password rotation | چرخش رمز عبور
2. Access control | کنترل دسترسی
3. Data encryption | رمزنگاری داده‌ها
4. Audit logging | ثبت ممیزی

## Troubleshooting | عیب‌یابی

### Common Issues | مشکلات رایج
1. Service not responding | عدم پاسخگویی سرویس
2. Database connection errors | خطاهای اتصال پایگاه داده
3. High resource usage | مصرف بالای منابع
4. Payment processing issues | مشکلات پردازش پرداخت

### Resolution Steps | مراحل رفع مشکل
1. Check system logs | بررسی لاگ‌های سیستم
2. Verify service status | بررسی وضعیت سرویس
3. Review error messages | بررسی پیام‌های خطا
4. Follow recovery procedures | پیروی از روش‌های بازیابی

### Emergency Contacts | تماس‌های اضطراری
- System Administrator | مدیر سیستم
- Database Administrator | مدیر پایگاه داده
- Security Team | تیم امنیت
- Network Team | تیم شبکه

## Command Reference | مرجع دستورات

### System Management | مدیریت سیستم
```bash
# Service status | وضعیت سرویس
systemctl status moonvpn

# View logs | مشاهده لاگ‌ها
journalctl -u moonvpn

# Restart service | راه‌اندازی مجدد سرویس
systemctl restart moonvpn
```

### Database Management | مدیریت پایگاه داده
```bash
# Backup database | پشتیبان‌گیری از پایگاه داده
pg_dump -U moonvpn > backup.sql

# Restore database | بازیابی پایگاه داده
psql -U moonvpn < backup.sql

# Vacuum database | اجرای Vacuum
vacuumdb -U moonvpn -d moonvpn
```

### Docker Management | مدیریت Docker
```bash
# View containers | مشاهده کانتینرها
docker ps

# View logs | مشاهده لاگ‌ها
docker logs moonvpn

# Restart container | راه‌اندازی مجدد کانتینر
docker restart moonvpn
```