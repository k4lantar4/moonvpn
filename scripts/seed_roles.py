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
from core.database.models.role import Role, RoleName

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def seed_roles(session: AsyncSession):
    """Seeds the database with initial roles."""
    roles_to_seed = [
        {
            "name": RoleName.ADMIN,
            "description": "کاربر ادمین با دسترسی کامل 👑",
            # Add specific permissions if needed later
        },
        {
            "name": RoleName.SELLER,
            "description": "کاربر فروشنده/نماینده 🛍️",
        },
        {
            "name": RoleName.USER,
            "description": "کاربر عادی مشتری 👤",
        },
    ]

    logger.info("Seeding initial roles...")
    roles_added = 0
    for role_data in roles_to_seed:
        # Check if role already exists
        stmt = select(Role).where(Role.name == role_data["name"])
        result = await session.execute(stmt)
        existing_role = result.scalar_one_or_none()

        if existing_role is None:
            new_role = Role(**role_data)
            session.add(new_role)
            logger.info(f"➕ Added role: {role_data['name'].value}")
            roles_added += 1
        else:
            logger.info(f"🟡 Role {role_data['name'].value} already exists, skipping.")

    if roles_added > 0:
        await session.commit()
        logger.info(f"✅ Successfully added {roles_added} new roles.")
    else:
        logger.info("✅ No new roles needed.")

async def main():
    """Main function to run the seeding process."""
    logger.info("--- Starting Role Seeding --- ")
    async with async_session_factory() as session:
        try:
            await seed_roles(session)
        except Exception as e:
            logger.error(f"❌ An error occurred during role seeding: {e}", exc_info=True)
            await session.rollback()
        finally:
            logger.info("--- Role Seeding Finished --- ")

if __name__ == "__main__":
    asyncio.run(main()) 