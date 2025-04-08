#!/bin/bash

# ============================================================
# MoonVPN Backup Script
# 
# این اسکریپت از دیتابیس و فایل‌های مهم پروژه پشتیبان‌گیری می‌کند
# تاریخ و زمان به نام فایل پشتیبان اضافه می‌شود
# ============================================================

# رنگ‌های متن برای نمایش بهتر خروجی
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# تنظیم مسیر پروژه
PROJECT_ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$PROJECT_ROOT" || { echo -e "${RED}خطا: مسیر پروژه یافت نشد!${NC}"; exit 1; }

# نمایش بنر
echo -e "${BLUE}"
echo -e "  __  __  ___   ___  _  _  _   _ ____  _  _ "
echo -e " |  \/  |/ _ \ / _ \| \| || | | |  _ \| \| |"
echo -e " | |\/| | (_) | (_) | .  || |_| | |_) | .  |"
echo -e " |_|  |_|\___/ \___/|_|\_| \___/|____/|_|\_|"
echo -e "                                            "
echo -e "          Backup System v1.0                "
echo -e "${NC}"

# بررسی وجود دایرکتوری پشتیبان‌ها
BACKUP_DIR="$PROJECT_ROOT/backups"
if [ ! -d "$BACKUP_DIR" ]; then
    echo -e "${YELLOW}دایرکتوری پشتیبان‌ها وجود ندارد. در حال ساخت...${NC}"
    mkdir -p "$BACKUP_DIR"
fi

# تنظیم تاریخ فعلی برای استفاده در نام فایل پشتیبان
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
BACKUP_NAME="moonvpn_backup_$TIMESTAMP"
BACKUP_FILE="$BACKUP_DIR/$BACKUP_NAME.tar.gz"

# بازیابی تنظیمات از فایل .env
if [ -f "$PROJECT_ROOT/.env" ]; then
    source "$PROJECT_ROOT/.env"
else
    echo -e "${RED}خطا: فایل .env یافت نشد!${NC}"
    exit 1
fi

# اعتبارسنجی متغیرهای محیطی
if [ -z "$MYSQL_DATABASE" ] || [ -z "$MYSQL_USER" ] || [ -z "$MYSQL_PASSWORD" ] || [ -z "$MYSQL_HOST" ]; then
    echo -e "${RED}خطا: اطلاعات دیتابیس در فایل .env ناقص است!${NC}"
    exit 1
fi

# ایجاد دایرکتوری موقت برای فایل‌های پشتیبان
TEMP_DIR="$BACKUP_DIR/temp_$TIMESTAMP"
mkdir -p "$TEMP_DIR"

echo -e "${YELLOW}در حال پشتیبان‌گیری از دیتابیس...${NC}"

# پشتیبان‌گیری از دیتابیس
if docker exec moonvpn-db mysqldump -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" > "$TEMP_DIR/$MYSQL_DATABASE.sql"; then
    echo -e "${GREEN}پشتیبان‌گیری از دیتابیس با موفقیت انجام شد.${NC}"
else
    echo -e "${RED}خطا در پشتیبان‌گیری از دیتابیس!${NC}"
    echo -e "${YELLOW}در حال تلاش دوباره با استفاده از mysqldump محلی...${NC}"
    
    # تلاش مستقیم با استفاده از mysqldump
    if mysqldump -h"$MYSQL_HOST" -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" > "$TEMP_DIR/$MYSQL_DATABASE.sql"; then
        echo -e "${GREEN}پشتیبان‌گیری از دیتابیس با موفقیت انجام شد.${NC}"
    else
        echo -e "${RED}پشتیبان‌گیری از دیتابیس ناموفق بود!${NC}"
        rm -rf "$TEMP_DIR"
        exit 1
    fi
fi

echo -e "${YELLOW}در حال پشتیبان‌گیری از فایل‌های تنظیمات...${NC}"

# کپی فایل‌های مهم
mkdir -p "$TEMP_DIR/config"
cp -r "$PROJECT_ROOT/.env" "$TEMP_DIR/config/" 2>/dev/null || echo -e "${YELLOW}فایل .env برای پشتیبان‌گیری یافت نشد${NC}"
cp -r "$PROJECT_ROOT/.env.example" "$TEMP_DIR/config/" 2>/dev/null
cp -r "$PROJECT_ROOT/docker-compose.yml" "$TEMP_DIR/config/" 2>/dev/null
cp -r "$PROJECT_ROOT/docker-compose.override.yml" "$TEMP_DIR/config/" 2>/dev/null

# پشتیبان‌گیری از فایل‌های لاگ
echo -e "${YELLOW}در حال پشتیبان‌گیری از فایل‌های لاگ...${NC}"
if [ -d "$PROJECT_ROOT/logs" ]; then
    mkdir -p "$TEMP_DIR/logs"
    cp -r "$PROJECT_ROOT/logs" "$TEMP_DIR/" 2>/dev/null
    echo -e "${GREEN}پشتیبان‌گیری از لاگ‌ها با موفقیت انجام شد.${NC}"
else
    echo -e "${YELLOW}دایرکتوری لاگ یافت نشد. در حال رد کردن...${NC}"
fi

# پشتیبان‌گیری از داده‌های کاربر
echo -e "${YELLOW}در حال پشتیبان‌گیری از داده‌های کاربر...${NC}"
if [ -d "$PROJECT_ROOT/data" ]; then
    mkdir -p "$TEMP_DIR/data"
    cp -r "$PROJECT_ROOT/data" "$TEMP_DIR/" 2>/dev/null
    echo -e "${GREEN}پشتیبان‌گیری از داده‌های کاربر با موفقیت انجام شد.${NC}"
else
    echo -e "${YELLOW}دایرکتوری داده‌های کاربر یافت نشد. در حال رد کردن...${NC}"
fi

# افزودن فایل اطلاعات پشتیبان
echo "MoonVPN Backup" > "$TEMP_DIR/backup_info.txt"
echo "Created at: $TIMESTAMP" >> "$TEMP_DIR/backup_info.txt"
echo "Version: 1.0" >> "$TEMP_DIR/backup_info.txt"
hostname >> "$TEMP_DIR/backup_info.txt"
echo "---------------------" >> "$TEMP_DIR/backup_info.txt"
echo "Database: $MYSQL_DATABASE" >> "$TEMP_DIR/backup_info.txt"
echo "Files included:" >> "$TEMP_DIR/backup_info.txt"
find "$TEMP_DIR" -type f -not -path "*/\.*" | sort >> "$TEMP_DIR/backup_info.txt"

# فشرده‌سازی همه فایل‌ها
echo -e "${YELLOW}در حال فشرده‌سازی فایل‌های پشتیبان...${NC}"
tar -czf "$BACKUP_FILE" -C "$TEMP_DIR" .

# پاکسازی فایل‌های موقت
rm -rf "$TEMP_DIR"

# اطلاعات در مورد فایل پشتیبان
BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)

echo -e "${GREEN}================================================================${NC}"
echo -e "${GREEN}پشتیبان‌گیری با موفقیت انجام شد!${NC}"
echo -e "${BLUE}نام فایل:${NC} $(basename "$BACKUP_FILE")"
echo -e "${BLUE}مسیر:${NC} $BACKUP_FILE"
echo -e "${BLUE}حجم:${NC} $BACKUP_SIZE"
echo -e "${BLUE}تاریخ:${NC} $TIMESTAMP"
echo -e "${GREEN}================================================================${NC}"

# نگهداری فقط 5 پشتیبان آخر
echo -e "${YELLOW}در حال بررسی پشتیبان‌های قدیمی...${NC}"
BACKUP_COUNT=$(find "$BACKUP_DIR" -maxdepth 1 -name "moonvpn_backup_*.tar.gz" | wc -l)

if [ "$BACKUP_COUNT" -gt 5 ]; then
    BACKUPS_TO_DELETE=$((BACKUP_COUNT - 5))
    echo -e "${YELLOW}حذف $BACKUPS_TO_DELETE پشتیبان قدیمی...${NC}"
    
    find "$BACKUP_DIR" -maxdepth 1 -name "moonvpn_backup_*.tar.gz" -type f -printf "%T@ %p\n" | \
    sort -n | head -n "$BACKUPS_TO_DELETE" | cut -d' ' -f2- | \
    xargs rm -f
    
    echo -e "${GREEN}پشتیبان‌های قدیمی حذف شدند.${NC}"
else
    echo -e "${GREEN}تعداد پشتیبان‌ها کمتر از حد مجاز است. نیازی به حذف نیست.${NC}"
fi

echo -e "${GREEN}عملیات پشتیبان‌گیری به پایان رسید.${NC}"
exit 0
