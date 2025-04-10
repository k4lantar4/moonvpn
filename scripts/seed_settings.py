import asyncio
import logging
import sys
import os

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database.session import async_session_factory
from core.database.models.setting import Setting

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define initial settings
INITIAL_SETTINGS = [
    {
        "key": "DEFAULT_REMARK_PATTERN",
        "value": "{prefix}-{id}-{custom}",
        "description": "الگوی پیش‌فرض برای نام کاربری (Remark) مشتریان جدید",
        "is_public": False,
        "group": "system",
    },
    {
        "key": "MIGRATION_REMARK_PATTERN",
        "value": "{original}-M{count}",
        "description": "الگوی نام کاربری (Remark) برای مشتریان منتقل شده",
        "is_public": False,
        "group": "system",
    },
    {
        "key": "ALLOW_CUSTOM_REMARKS",
        "value": "true", # Use lowercase 'true'/'false' for boolean strings
        "description": "اجازه به کاربران برای تنظیم نام دلخواه برای اکانت",
        "is_public": True,
        "group": "feature",
    },
    {
        "key": "MAX_MIGRATIONS_PER_DAY",
        "value": "3",
        "description": "حداکثر تعداد مجاز انتقال اکانت در روز برای هر کاربر",
        "is_public": False,
        "group": "limit",
    },
    # Add more settings as needed
]

async def seed_settings(session: AsyncSession):
    """Seeds the database with initial system settings."""
    logger.info("Seeding initial system settings...")
    
    settings_added = 0
    for setting_data in INITIAL_SETTINGS:
        setting_key = setting_data["key"]
        # Check if setting already exists by key
        stmt = select(Setting).where(Setting.key == setting_key)
        result = await session.execute(stmt)
        existing_setting = result.scalar_one_or_none()

        if existing_setting is None:
            try:
                # Convert boolean value to string if necessary (or adjust model/DB)
                if isinstance(setting_data.get("value"), bool):
                     setting_data["value"] = str(setting_data["value"]).lower()
                 
                new_setting = Setting(**setting_data)
                session.add(new_setting)
                await session.flush() # Flush early
                logger.info(f"➕ Added setting: {setting_key}")
                settings_added += 1
            except Exception as e:
                 logger.error(f"❌ Error adding setting '{setting_key}': {e}", exc_info=True)
                 raise # Reraise to trigger rollback in seed_all
        else:
            logger.info(f"🟡 Setting '{setting_key}' already exists, skipping.")
            # Optional: Update existing setting value?
            # if existing_setting.value != setting_data["value"]:
            #     existing_setting.value = setting_data["value"]
            #     logger.info(f"Updating value for setting '{setting_key}'")

    if settings_added > 0:
        # REMOVED COMMIT
        logger.info(f"✅ Successfully processed {settings_added} new setting(s) for addition.")
    else:
        logger.info("✅ No new settings needed to be added.")


async def main():
    """Main function to run the seeding process independently (for testing)."""
    logger.info("--- Starting Settings Seeding (Independent Run) --- ")
    async with async_session_factory() as session:
        try:
            await seed_settings(session)
            await session.commit() # Commit only if running independently
            logger.info("Independent run committed.")
        except Exception as e:
            logger.error(f"❌ An error occurred during independent settings seeding: {e}", exc_info=True)
            await session.rollback()
            logger.info("Independent run rolled back.")
        finally:
            logger.info("--- Settings Seeding (Independent Run) Finished --- ")

if __name__ == "__main__":
    asyncio.run(main()) 