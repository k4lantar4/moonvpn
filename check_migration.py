from core.database import get_db, SessionLocal
from sqlalchemy import text
import asyncio

async def check_migration():
    # استفاده مستقیم از SessionLocal
    session = SessionLocal()
    
    try:
        # بررسی جدول‌ها
        result = await session.execute(text('SHOW TABLES'))
        tables = [r[0] for r in result]
        print("Tables in database:", tables)
        
        # بررسی ساختار جدول client_migrations
        if 'client_migrations' in tables:
            result = await session.execute(text('DESCRIBE client_migrations'))
            columns = [{'Field': r[0], 'Type': r[1]} for r in result]
            print("\nStructure of client_migrations table:")
            for col in columns:
                print(f"  {col['Field']}: {col['Type']}")
        else:
            print("\nTable client_migrations not found!")
        
        # بررسی فیلدهای جدید در جدول clients
        result = await session.execute(text('DESCRIBE clients'))
        client_columns = [r[0] for r in result]
        migration_fields = [
            'original_location_id', 'original_remark', 'custom_name', 
            'previous_panel_id', 'migration_count', 'last_location_change',
            'location_changes_today', 'location_changes_reset_date', 'migration_history'
        ]
        
        print("\nMigration fields in clients table:")
        for field in migration_fields:
            print(f"  {field}: {'✅ Added' if field in client_columns else '❌ Missing'}")
        
        # بررسی فیلدهای جدید در جدول locations
        result = await session.execute(text('DESCRIBE locations'))
        location_columns = [r[0] for r in result]
        location_fields = ['default_remark_prefix', 'remark_pattern', 'migration_remark_pattern']
        
        print("\nMigration fields in locations table:")
        for field in location_fields:
            print(f"  {field}: {'✅ Added' if field in location_columns else '❌ Missing'}")
        
        # بررسی تنظیمات
        result = await session.execute(text("SELECT * FROM settings WHERE `key` = 'MAX_LOCATION_CHANGES_PER_DAY'"))
        setting = result.fetchone()
        
        print("\nSettings for location changes:")
        if setting:
            print(f"  MAX_LOCATION_CHANGES_PER_DAY: ✅ Added (value: {setting[1]})")
        else:
            print("  MAX_LOCATION_CHANGES_PER_DAY: ❌ Missing")
    finally:
        await session.close()

if __name__ == "__main__":
    asyncio.run(check_migration()) 