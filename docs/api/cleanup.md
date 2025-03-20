# System Cleanup Documentation

## English

### Overview
The MoonVPN system includes a comprehensive cleanup system to manage disk space, database size, and system performance. The cleanup system handles old backups, metrics, logs, and temporary files.

### Components

1. Cleanup Service
   - Manages all cleanup operations
   - Handles backups, metrics, logs, and temp files
   - Provides detailed operation results
   - Integrates with notification system

2. Cleanup Script
   - Command-line interface for cleanup operations
   - Supports individual or combined operations
   - Configurable retention periods
   - Detailed logging and reporting

### Usage

#### Command Line Interface
```bash
# Run all cleanup operations
python scripts/cleanup.py --all

# Clean up old backups (older than 30 days)
python scripts/cleanup.py --backups --backup-days 30

# Clean up old metrics (older than 7 days)
python scripts/cleanup.py --metrics --metrics-days 7

# Clean up old logs (older than 30 days)
python scripts/cleanup.py --logs --logs-days 30

# Clean up temporary files
python scripts/cleanup.py --temp
```

#### Programmatic Usage
```python
from core.services.cleanup import CleanupService

# Initialize service
cleanup_service = CleanupService(db_session)

# Run all cleanup operations
results = await cleanup_service.cleanup_all()

# Clean up specific items
backup_results = await cleanup_service.cleanup_old_backups(retention_days=30)
metrics_results = await cleanup_service.cleanup_old_metrics(retention_days=7)
logs_results = await cleanup_service.cleanup_old_logs(retention_days=30)
temp_results = await cleanup_service.cleanup_temp_files()
```

### Configuration
The cleanup system uses the following settings from `core/config.py`:
- `TEMP_DIR`: Directory for temporary files
- `LOG_LEVEL`: Logging level for cleanup operations
- `LOG_FORMAT`: Format for log messages
- `LOG_FILE`: File for logging cleanup operations

### Best Practices
1. Run cleanup operations during low-usage periods
2. Monitor disk space usage regularly
3. Adjust retention periods based on system needs
4. Keep backup copies of important data
5. Review cleanup logs periodically

### Troubleshooting
1. Check log files for error messages
2. Verify file permissions
3. Monitor database connections
4. Check disk space availability
5. Review cleanup operation results

## Persian (فارسی)

### نمای کلی
سیستم MoonVPN شامل یک سیستم پاکسازی جامع برای مدیریت فضای دیسک، اندازه پایگاه داده و عملکرد سیستم است. سیستم پاکسازی، پشتیبان‌های قدیمی، متریک‌ها، لاگ‌ها و فایل‌های موقت را مدیریت می‌کند.

### اجزا

1. سرویس پاکسازی
   - مدیریت تمام عملیات پاکسازی
   - مدیریت پشتیبان‌ها، متریک‌ها، لاگ‌ها و فایل‌های موقت
   - ارائه نتایج دقیق عملیات
   - یکپارچه‌سازی با سیستم اعلان

2. اسکریپت پاکسازی
   - رابط خط فرمان برای عملیات پاکسازی
   - پشتیبانی از عملیات جداگانه یا ترکیبی
   - دوره نگهداری قابل تنظیم
   - گزارش‌دهی و ثبت وقایع دقیق

### نحوه استفاده

#### رابط خط فرمان
```bash
# اجرای تمام عملیات پاکسازی
python scripts/cleanup.py --all

# پاکسازی پشتیبان‌های قدیمی (قدیمی‌تر از 30 روز)
python scripts/cleanup.py --backups --backup-days 30

# پاکسازی متریک‌های قدیمی (قدیمی‌تر از 7 روز)
python scripts/cleanup.py --metrics --metrics-days 7

# پاکسازی لاگ‌های قدیمی (قدیمی‌تر از 30 روز)
python scripts/cleanup.py --logs --logs-days 30

# پاکسازی فایل‌های موقت
python scripts/cleanup.py --temp
```

#### استفاده برنامه‌نویسی
```python
from core.services.cleanup import CleanupService

# راه‌اندازی سرویس
cleanup_service = CleanupService(db_session)

# اجرای تمام عملیات پاکسازی
results = await cleanup_service.cleanup_all()

# پاکسازی موارد خاص
backup_results = await cleanup_service.cleanup_old_backups(retention_days=30)
metrics_results = await cleanup_service.cleanup_old_metrics(retention_days=7)
logs_results = await cleanup_service.cleanup_old_logs(retention_days=30)
temp_results = await cleanup_service.cleanup_temp_files()
```

### پیکربندی
سیستم پاکسازی از تنظیمات زیر در `core/config.py` استفاده می‌کند:
- `TEMP_DIR`: دایرکتوری برای فایل‌های موقت
- `LOG_LEVEL`: سطح ثبت وقایع برای عملیات پاکسازی
- `LOG_FORMAT`: قالب پیام‌های ثبت وقایع
- `LOG_FILE`: فایل برای ثبت عملیات پاکسازی

### بهترین شیوه‌ها
1. اجرای عملیات پاکسازی در زمان‌های کم استفاده
2. نظارت منظم بر استفاده از فضای دیسک
3. تنظیم دوره‌های نگهداری بر اساس نیازهای سیستم
4. نگهداری نسخه پشتیبان از داده‌های مهم
5. بررسی دوره‌ای لاگ‌های پاکسازی

### عیب‌یابی
1. بررسی فایل‌های لاگ برای پیام‌های خطا
2. تأیید مجوزهای فایل
3. نظارت بر اتصالات پایگاه داده
4. بررسی فضای دیسک موجود
5. بررسی نتایج عملیات پاکسازی 