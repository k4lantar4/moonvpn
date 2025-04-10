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
from core.database.models.plan_category import PlanCategory

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define the initial plan categories
INITIAL_CATEGORIES = [
    {
        "name": "عمومی Bronze 🥉",
        "description": "دسته‌بندی پلان‌های عمومی برنزی",
        "sorting_order": 10,
        "is_active": True,
    },
    {
        "name": "عمومی Silver 🥈",
        "description": "دسته‌بندی پلان‌های عمومی نقره ای",
        "sorting_order": 20,
        "is_active": True,
    },
    {
        "name": "عمومی Gold 🥇",
        "description": "دسته‌بندی پلان‌های عمومی طلایی",
        "sorting_order": 30,
        "is_active": True,
    },
]

async def seed_plan_categories(session: AsyncSession):
    """Seeds the database with initial plan categories."""
    logger.info("Seeding initial plan categories...")
    
    categories_added = 0
    for category_data in INITIAL_CATEGORIES:
        category_name = category_data["name"]
        # Check if category already exists by name
        stmt = select(PlanCategory).where(PlanCategory.name == category_name)
        result = await session.execute(stmt)
        existing_category = result.scalar_one_or_none()

        if existing_category is None:
            try:
                new_category = PlanCategory(**category_data)
                session.add(new_category)
                await session.flush() # Flush early
                logger.info(f"➕ Added plan category: {category_name}")
                categories_added += 1
            except Exception as e:
                logger.error(f"❌ Error adding category '{category_name}': {e}", exc_info=True)
                raise # Reraise to trigger rollback in seed_all
        else:
            logger.info(f"🟡 Plan category '{category_name}' already exists, skipping.")
            # Optional: Update existing?
            # for key, value in category_data.items():
            #     if getattr(existing_category, key) != value:
            #         setattr(existing_category, key, value)
            #         logger.info(f"Updating {key} for category '{category_name}'")

    if categories_added > 0:
        # REMOVED COMMIT
        logger.info(f"✅ Successfully processed {categories_added} new plan categories for addition.")
    else:
        logger.info("✅ No new plan categories needed to be added.")

async def main():
    """Main function to run the seeding process independently (for testing)."""
    logger.info("--- Starting Plan Category Seeding (Independent Run) --- ")
    async with async_session_factory() as session:
        try:
            await seed_plan_categories(session)
            await session.commit() # Commit only if running independently
            logger.info("Independent run committed.")
        except Exception as e:
            logger.error(f"❌ An error occurred during independent plan category seeding: {e}", exc_info=True)
            await session.rollback()
            logger.info("Independent run rolled back.")
        finally:
            logger.info("--- Plan Category Seeding (Independent Run) Finished --- ")

if __name__ == "__main__":
    asyncio.run(main()) 