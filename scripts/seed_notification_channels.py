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
from dotenv import load_dotenv

from core.database.session import async_session_factory
from core.database.models.notification_channel import NotificationChannel

# Load environment variables
load_dotenv()

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define initial notification channels (fetches IDs from environment variables)
INITIAL_CHANNELS = [
    {
        "name": "ADMIN",
        "channel_id_env": "NOTIFICATION_CHANNEL_ADMIN", # Match env var name from core/config.py
        "description": "کانال اطلاع‌رسانی‌های عمومی ادمین 📢",
        "is_active": True,
    },
    {
        "name": "PAYMENT",
        "channel_id_env": "NOTIFICATION_CHANNEL_PAYMENT",
        "description": "کانال درخواست‌های تایید پرداخت 💳",
        "is_active": True,
    },
    {
        "name": "BACKUP",
        "channel_id_env": "NOTIFICATION_CHANNEL_BACKUP",
        "description": "کانال گزارش وضعیت بکاپ پایگاه داده 💾",
        "is_active": True,
    },
    {
        "name": "CRITICAL",
        "channel_id_env": "NOTIFICATION_CHANNEL_CRITICAL",
        "description": "کانال خطاهای حیاتی سیستم 🚨",
        "is_active": True,
    },
    {
        "name": "USER_REGISTRATION",
        "channel_id_env": "NOTIFICATION_CHANNEL_USER_REGISTRATION",
        "description": "کانال ثبت نام کاربران جدید 👋",
        "is_active": True,
    },
]

async def seed_notification_channels(session: AsyncSession):
    """Seeds the database with initial notification channels."""
    logger.info("Seeding initial notification channels...")

    channels_processed = 0 # Count both added and updated
    for channel_data in INITIAL_CHANNELS:
        channel_name = channel_data["name"]
        channel_id_env_var = channel_data.pop("channel_id_env")
        # Use strip() to remove potential whitespace from env var
        channel_id = os.getenv(channel_id_env_var, "").strip()

        if not channel_id:
            logger.warning(f"⚠️ Environment variable '{channel_id_env_var}' not set for channel '{channel_name}'. Skipping.")
            continue

        # Ensure channel_id is a valid integer (Telegram IDs are usually numbers)
        try:
             # Telegram IDs can be negative for channels/supergroups
             channel_id_int = int(channel_id)
        except ValueError:
             logger.error(f"❌ Invalid non-integer channel ID '{channel_id}' found in env var '{channel_id_env_var}' for channel '{channel_name}'. Skipping.")
             continue

        channel_data["channel_id"] = str(channel_id_int) # Store as string in DB if model expects string

        # Check if channel already exists by name
        stmt = select(NotificationChannel).where(NotificationChannel.name == channel_name)
        result = await session.execute(stmt)
        existing_channel = result.scalar_one_or_none()

        if existing_channel is None:
            try:
                new_channel = NotificationChannel(**channel_data)
                session.add(new_channel)
                await session.flush() # Flush early
                logger.info(f"➕ Added notification channel: {channel_name} -> {channel_id}")
                channels_processed += 1
            except Exception as e:
                 logger.error(f"❌ Error adding notification channel '{channel_name}': {e}", exc_info=True)
                 raise # Reraise to trigger rollback
        elif existing_channel.channel_id != str(channel_id_int):
             try:
                 logger.info(f"🔄 Updating channel ID for '{channel_name}' from {existing_channel.channel_id} to {channel_id_int}")
                 existing_channel.channel_id = str(channel_id_int)
                 # Optionally update other fields like description or is_active if needed
                 # existing_channel.description = channel_data["description"]
                 # existing_channel.is_active = channel_data["is_active"]
                 session.add(existing_channel) # Mark for update
                 await session.flush() # Flush early
                 channels_processed += 1 # Count as an update
             except Exception as e:
                  logger.error(f"❌ Error updating notification channel '{channel_name}': {e}", exc_info=True)
                  raise # Reraise to trigger rollback
        else:
            logger.info(f"🟡 Notification channel '{channel_name}' already exists with correct ID, skipping.")

    if channels_processed > 0:
        # REMOVED COMMIT
        logger.info(f"✅ Successfully processed {channels_processed} notification channel(s) for addition/update.")
    else:
        logger.info("✅ No new/updated notification channels needed.")


async def main():
    """Main function to run the seeding process independently (for testing)."""
    logger.info("--- Starting Notification Channel Seeding (Independent Run) --- ")
    async with async_session_factory() as session:
        try:
            await seed_notification_channels(session)
            await session.commit() # Commit only if running independently
            logger.info("Independent run committed.")
        except Exception as e:
            logger.error(f"❌ An error occurred during independent notification channel seeding: {e}", exc_info=True)
            await session.rollback()
            logger.info("Independent run rolled back.")
        finally:
            logger.info("--- Notification Channel Seeding (Independent Run) Finished --- ")

if __name__ == "__main__":
    asyncio.run(main()) 