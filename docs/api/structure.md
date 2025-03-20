# Directory Structure Documentation

## English

### Project Structure
```
moonvpn/
├── core/                      # Core functionality
│   ├── config/               # Configuration management
│   ├── database/            # Database models and migrations
│   ├── services/           # Business logic services
│   └── utils/              # Utility functions and helpers
├── api/                      # API endpoints and handlers
│   ├── v1/                 # Version 1 API endpoints
│   └── middleware/         # API middleware
├── web/                      # Web interface
│   ├── components/         # Reusable UI components
│   ├── pages/             # Page components
│   └── utils/             # Frontend utilities
├── tests/                    # Test suite
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── e2e/              # End-to-end tests
├── scripts/                  # Maintenance and utility scripts
├── docs/                     # Documentation
│   ├── api/               # API documentation
│   ├── maintenance/       # Maintenance guides
│   └── user/             # User guides
└── tools/                    # Development tools and utilities
```

### Directory Descriptions

#### Core
- **config/**: Configuration management and settings
- **database/**: Database models, migrations, and schemas
- **services/**: Core business logic and services
- **utils/**: Helper functions and utilities

#### API
- **v1/**: Version 1 API endpoints and handlers
- **middleware/**: API middleware for authentication, logging, etc.

#### Web
- **components/**: Reusable UI components
- **pages/**: Page-specific components and layouts
- **utils/**: Frontend utility functions

#### Tests
- **unit/**: Unit tests for individual components
- **integration/**: Integration tests for service interactions
- **e2e/**: End-to-end tests for complete workflows

#### Scripts
Maintenance and utility scripts for deployment, backup, etc.

#### Documentation
- **api/**: API documentation and specifications
- **maintenance/**: System maintenance guides
- **user/**: End-user documentation

#### Tools
Development tools and utilities for the project

### Best Practices
1. Keep related files together
2. Use clear, descriptive names
3. Maintain separation of concerns
4. Follow consistent naming conventions
5. Document directory purposes
6. Keep directory depth manageable

## Persian (فارسی)

### ساختار پروژه
```
moonvpn/
├── core/                      # عملکرد اصلی
│   ├── config/               # مدیریت پیکربندی
│   ├── database/            # مدل‌ها و مهاجرت‌های پایگاه داده
│   ├── services/           # سرویس‌های منطق کسب و کار
│   └── utils/              # توابع و کمک‌کننده‌های مفید
├── api/                      # نقاط پایانی و مدیریت‌کننده‌های API
│   ├── v1/                 # نقاط پایانی نسخه 1 API
│   └── middleware/         # میان‌افزار API
├── web/                      # رابط کاربری وب
│   ├── components/         # اجزای قابل استفاده مجدد UI
│   ├── pages/             # اجزای صفحه
│   └── utils/             # ابزارهای فرانت‌اند
├── tests/                    # مجموعه تست
│   ├── unit/              # تست‌های واحد
│   ├── integration/       # تست‌های یکپارچه‌سازی
│   └── e2e/              # تست‌های انتها به انتها
├── scripts/                  # اسکریپت‌های نگهداری و مفید
├── docs/                     # مستندات
│   ├── api/               # مستندات API
│   ├── maintenance/       # راهنمای نگهداری
│   └── user/             # راهنمای کاربر
└── tools/                    # ابزارهای توسعه و مفید
```

### توضیحات دایرکتوری

#### هسته (core)
- **config/**: مدیریت پیکربندی و تنظیمات
- **database/**: مدل‌ها، مهاجرت‌ها و طرح‌های پایگاه داده
- **services/**: منطق کسب و کار اصلی و سرویس‌ها
- **utils/**: توابع کمکی و ابزارها

#### API
- **v1/**: نقاط پایانی و مدیریت‌کننده‌های نسخه 1 API
- **middleware/**: میان‌افزار API برای احراز هویت، ثبت وقایع و غیره

#### وب (web)
- **components/**: اجزای قابل استفاده مجدد UI
- **pages/**: اجزا و طرح‌بندی‌های مخصوص صفحه
- **utils/**: توابع مفید فرانت‌اند

#### تست‌ها (tests)
- **unit/**: تست‌های واحد برای اجزای جداگانه
- **integration/**: تست‌های یکپارچه‌سازی برای تعاملات سرویس
- **e2e/**: تست‌های انتها به انتها برای گردش کارهای کامل

#### اسکریپت‌ها (scripts)
اسکریپت‌های نگهداری و مفید برای استقرار، پشتیبان‌گیری و غیره

#### مستندات (docs)
- **api/**: مستندات و مشخصات API
- **maintenance/**: راهنماهای نگهداری سیستم
- **user/**: مستندات کاربر نهایی

#### ابزارها (tools)
ابزارها و برنامه‌های مفید توسعه برای پروژه

### بهترین شیوه‌ها
1. فایل‌های مرتبط را کنار هم نگه دارید
2. از نام‌های واضح و توصیفی استفاده کنید
3. جداسازی دغدغه‌ها را حفظ کنید
4. از قراردادهای نام‌گذاری یکسان پیروی کنید
5. اهداف دایرکتوری را مستند کنید
6. عمق دایرکتوری را قابل مدیریت نگه دارید 