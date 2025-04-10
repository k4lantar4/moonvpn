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
from core.database.models.user import User
from core.database.models.role import Role, RoleName

# Load environment variables
load_dotenv()

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def seed_admin_user(session: AsyncSession):
    """Seeds the database with the initial admin user from the first ID in ADMIN_IDS."""
    logger.info("Seeding initial admin user from ADMIN_IDS...")

    admin_ids_str = os.getenv("ADMIN_IDS")
    if not admin_ids_str:
        logger.error("❌ Environment variable 'ADMIN_IDS' is not set or is empty. Cannot seed admin user.")
        return

    admin_ids_list = [id_str.strip() for id_str in admin_ids_str.split(',') if id_str.strip()]
    if not admin_ids_list:
        logger.error("❌ 'ADMIN_IDS' is set but contains no valid IDs after stripping whitespace. Cannot seed admin user.")
        return

    first_admin_id_str = admin_ids_list[0]

    try:
        admin_telegram_id = int(first_admin_id_str)
    except ValueError:
        logger.error(f"❌ Invalid first Admin ID in ADMIN_IDS: '{first_admin_id_str}'. Must be an integer.")
        return

    logger.info(f"Attempting to seed admin user with the first ID from ADMIN_IDS: {admin_telegram_id}")

    # Find the ADMIN role
    role_stmt = select(Role).where(Role.name == RoleName.ADMIN)
    role_result = await session.execute(role_stmt)
    admin_role = role_result.scalar_one_or_none()

    if admin_role is None:
        logger.error("❌ ADMIN role not found in the database. Please run role seeder first.")
        return

    # Check if admin user already exists
    user_stmt = select(User).where(User.telegram_id == admin_telegram_id)
    user_result = await session.execute(user_stmt)
    existing_user = user_result.scalar_one_or_none()

    admin_added = 0
    if existing_user is None:
        admin_user_data = {
            "telegram_id": admin_telegram_id,
            "role_id": admin_role.id,
            # Use the telegram_id as a placeholder username initially
            "username": str(admin_telegram_id), 
            "full_name": f"Admin {admin_telegram_id}", # Use a more descriptive default name
            "is_active": True,
            "balance": 0.00, # Initial balance
            # Other fields will use defaults or be None
        }
        new_admin = User(**admin_user_data)
        session.add(new_admin)
        await session.commit() # Commit here for now
        logger.info(f"➕ Added initial admin user with Telegram ID: {admin_telegram_id} (from ADMIN_IDS)")
        admin_added += 1
    elif existing_user.role_id != admin_role.id:
         logger.warning(f"🟡 User {admin_telegram_id} (from ADMIN_IDS) exists but does not have ADMIN role. Updating role.")
         existing_user.role_id = admin_role.id
         session.add(existing_user)
         await session.commit()
         admin_added +=1 # Consider update as added for message
    else:
        logger.info(f"🟡 Admin user with Telegram ID {admin_telegram_id} (from ADMIN_IDS) already exists with the correct role, skipping.")

    if admin_added > 0:
        logger.info(f"✅ Successfully added/updated initial admin user (ID: {admin_telegram_id}).")
    # else:
        # logger.info("✅ No changes needed for admin user.") # Implicitly handled by skipping message

async def main():
    """Main function to run the seeding process."""
    logger.info("--- Starting Admin User Seeding --- ")
    async with async_session_factory() as session:
        try:
            await seed_admin_user(session)
        except Exception as e:
            logger.error(f"❌ An error occurred during admin user seeding: {e}", exc_info=True)
            await session.rollback()
        finally:
            logger.info("--- Admin User Seeding Finished --- ")

if __name__ == "__main__":
    asyncio.run(main()) 