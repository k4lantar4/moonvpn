# Legacy Code Management Documentation

## English

### Overview
The MoonVPN Legacy Code Management System provides tools and processes for managing legacy code, planning migrations, and tracking the status of code modernization efforts. The system helps maintain a clear record of legacy code and ensures smooth transitions to new implementations.

### Components

1. Legacy Code Service
   - Archives legacy code with documentation
   - Creates and executes migration plans
   - Tracks migration progress
   - Supports rollback operations
   - Provides status reporting

2. Database Models
   - LegacyCode: Tracks archived legacy code
   - LegacyMigration: Manages migration plans and execution

### Features

1. Code Archiving
   - Preserves original code
   - Maintains documentation
   - Tracks archive locations
   - Records timestamps

2. Migration Planning
   - Step-by-step migration plans
   - Clear documentation
   - Progress tracking
   - Error handling

3. Migration Execution
   - Automated execution
   - Progress monitoring
   - Error handling
   - Rollback support

4. Status Reporting
   - Overall status view
   - Migration progress
   - Success/failure tracking
   - Activity history

### Usage

#### Archiving Legacy Code
```python
from core.services.legacy import LegacyCodeService

# Initialize service
legacy_service = LegacyCodeService(db_session)

# Archive legacy code
legacy_code = await legacy_service.archive_legacy_code(
    code_path="/path/to/legacy/code",
    description="Description of the legacy code"
)
```

#### Creating Migration Plans
```python
# Create migration plan
migration = await legacy_service.create_migration_plan(
    legacy_code_id=legacy_code.id,
    new_implementation="/path/to/new/code",
    steps=[
        {"type": "move", "source": "old.py", "target": "new.py"},
        {"type": "update", "file": "new.py", "changes": []}
    ]
)
```

#### Executing Migrations
```python
# Execute migration
result = await legacy_service.execute_migration(migration.id)

# Check status
status = await legacy_service.get_legacy_code_status()
```

#### Rolling Back Migrations
```python
# Rollback migration
result = await legacy_service.rollback_migration(migration.id)
```

### Best Practices
1. Document legacy code thoroughly before archiving
2. Create detailed migration plans
3. Test migrations in development environment
4. Keep backup copies of legacy code
5. Monitor migration progress
6. Review results after completion

### Troubleshooting
1. Check error messages in logs
2. Verify file permissions
3. Review migration steps
4. Check database connectivity
5. Monitor system resources

## Persian (فارسی)

### نمای کلی
سیستم مدیریت کد قدیمی MoonVPN ابزارها و فرآیندهایی را برای مدیریت کد قدیمی، برنامه‌ریزی مهاجرت و پیگیری وضعیت تلاش‌های مدرن‌سازی کد فراهم می‌کند. این سیستم به حفظ سوابق روشن از کد قدیمی کمک کرده و انتقال روان به پیاده‌سازی‌های جدید را تضمین می‌کند.

### اجزا

1. سرویس کد قدیمی
   - آرشیو کد قدیمی با مستندات
   - ایجاد و اجرای برنامه‌های مهاجرت
   - پیگیری پیشرفت مهاجرت
   - پشتیبانی از عملیات بازگشت
   - ارائه گزارش وضعیت

2. مدل‌های پایگاه داده
   - LegacyCode: پیگیری کد قدیمی آرشیو شده
   - LegacyMigration: مدیریت برنامه‌ها و اجرای مهاجرت

### ویژگی‌ها

1. آرشیو کردن کد
   - حفظ کد اصلی
   - نگهداری مستندات
   - پیگیری مکان‌های آرشیو
   - ثبت زمان‌ها

2. برنامه‌ریزی مهاجرت
   - برنامه‌های مهاجرت گام به گام
   - مستندات روشن
   - پیگیری پیشرفت
   - مدیریت خطا

3. اجرای مهاجرت
   - اجرای خودکار
   - نظارت بر پیشرفت
   - مدیریت خطا
   - پشتیبانی از بازگشت

4. گزارش وضعیت
   - نمای کلی وضعیت
   - پیشرفت مهاجرت
   - پیگیری موفقیت/شکست
   - تاریخچه فعالیت

### نحوه استفاده

#### آرشیو کردن کد قدیمی
```python
from core.services.legacy import LegacyCodeService

# راه‌اندازی سرویس
legacy_service = LegacyCodeService(db_session)

# آرشیو کد قدیمی
legacy_code = await legacy_service.archive_legacy_code(
    code_path="/path/to/legacy/code",
    description="توضیحات کد قدیمی"
)
```

#### ایجاد برنامه‌های مهاجرت
```python
# ایجاد برنامه مهاجرت
migration = await legacy_service.create_migration_plan(
    legacy_code_id=legacy_code.id,
    new_implementation="/path/to/new/code",
    steps=[
        {"type": "move", "source": "old.py", "target": "new.py"},
        {"type": "update", "file": "new.py", "changes": []}
    ]
)
```

#### اجرای مهاجرت
```python
# اجرای مهاجرت
result = await legacy_service.execute_migration(migration.id)

# بررسی وضعیت
status = await legacy_service.get_legacy_code_status()
```

#### بازگشت مهاجرت
```python
# بازگشت مهاجرت
result = await legacy_service.rollback_migration(migration.id)
```

### بهترین شیوه‌ها
1. مستندسازی کامل کد قدیمی قبل از آرشیو
2. ایجاد برنامه‌های مهاجرت دقیق
3. تست مهاجرت در محیط توسعه
4. نگهداری نسخه پشتیبان از کد قدیمی
5. نظارت بر پیشرفت مهاجرت
6. بررسی نتایج پس از تکمیل

### عیب‌یابی
1. بررسی پیام‌های خطا در لاگ‌ها
2. تأیید مجوزهای فایل
3. بررسی مراحل مهاجرت
4. بررسی اتصال پایگاه داده
5. نظارت بر منابع سیستم 