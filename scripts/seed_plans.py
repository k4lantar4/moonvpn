import asyncio
import logging
import sys
import os
from decimal import Decimal

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database.session import async_session_factory
from core.database.models.plan import Plan
from core.database.models.plan_category import PlanCategory

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define initial plans (assuming category names exist)
INITIAL_PLANS = [
    {
        "category_name": "عمومی Bronze 🥉",
        "name": "برنزی ۱ ماهه ۵۰ گیگ ✨",
        "traffic": 50 * 1024 * 1024 * 1024, # 50 GB in bytes
        "days": 30,
        "price": Decimal("50000.00"),
        "description": "پلان برنزی اقتصادی یک ماهه با ۵۰ گیگابایت ترافیک.",
        "is_active": True,
        "max_clients": 1, # Example: Allow 1 concurrent connection
        "protocols": "vless,vmess", # Example
        "sorting_order": 10, # Add sorting order if needed
    },
    {
        "category_name": "عمومی Silver 🥈",
        "name": "نقره‌ای ۲ ماهه ۱۰۰ گیگ 🚀",
        "traffic": 100 * 1024 * 1024 * 1024, # 100 GB in bytes
        "days": 60,
        "price": Decimal("95000.00"),
        "description": "پلان نقره‌ای مناسب دو ماهه با ۱۰۰ گیگابایت ترافیک.",
        "is_active": True,
        "max_clients": 2,
        "protocols": "vless,vmess,trojan",
        "sorting_order": 20,
    },
    {
        "category_name": "عمومی Gold 🥇",
        "name": "طلایی ۳ ماهه نامحدود 💎",
        "traffic": 0, # Indicate unlimited (or use a very large number / check model definition)
        "days": 90,
        "price": Decimal("250000.00"),
        "description": "پلان طلایی ویژه سه ماهه با ترافیک نامحدود.",
        "is_active": True,
        "max_clients": 3,
        "protocols": "vless,vmess,trojan,shadowsocks",
        "is_featured": True, # Example: Mark as featured
        "sorting_order": 30,
    },
]

async def seed_plans(session: AsyncSession):
    """Seeds the database with initial plans."""
    logger.info("Seeding initial plans...")

    # Fetch existing category IDs
    category_stmt = select(PlanCategory.id, PlanCategory.name)
    category_result = await session.execute(category_stmt)
    category_map = {name: cat_id for cat_id, name in category_result.all()}
    logger.debug(f"Found categories: {category_map}")

    plans_added = 0
    for plan_data in INITIAL_PLANS:
        plan_name = plan_data["name"]
        category_name = plan_data.pop("category_name", None)
        category_id = category_map.get(category_name)

        if category_id is None:
            logger.warning(f"⚠️ Category '{category_name}' not found for plan '{plan_name}'. Skipping plan.")
            continue

        plan_data["category_id"] = category_id

        # Check if plan already exists by name and category
        stmt = select(Plan).where(Plan.name == plan_name, Plan.category_id == category_id)
        result = await session.execute(stmt)
        existing_plan = result.scalar_one_or_none()

        if existing_plan is None:
            try:
                # Convert traffic to int if it's not already (SQLAlchemy might handle it)
                # Ensure 'traffic' field exists in your Plan model
                if "traffic" in plan_data:
                     plan_data["traffic"] = int(plan_data["traffic"])

                new_plan = Plan(**plan_data)
                session.add(new_plan)
                await session.flush() # Flush early
                logger.info(f"➕ Added plan: {plan_name}")
                plans_added += 1
            except Exception as e:
                logger.error(f"❌ Error adding plan '{plan_name}': {e}", exc_info=True)
                raise # Reraise to trigger rollback in seed_all
        else:
            logger.info(f"🟡 Plan '{plan_name}' already exists, skipping.")
            # Optional: Update existing plan?

    if plans_added > 0:
        # REMOVED COMMIT
        logger.info(f"✅ Successfully processed {plans_added} new plan(s) for addition.")
    else:
        logger.info("✅ No new plans needed to be added.")


async def main():
    """Main function to run the seeding process independently (for testing)."""
    logger.info("--- Starting Plan Seeding (Independent Run) --- ")
    async with async_session_factory() as session:
        try:
            await seed_plans(session)
            await session.commit() # Commit only if running independently
            logger.info("Independent run committed.")
        except Exception as e:
            logger.error(f"❌ An error occurred during independent plan seeding: {e}", exc_info=True)
            await session.rollback()
            logger.info("Independent run rolled back.")
        finally:
            logger.info("--- Plan Seeding (Independent Run) Finished --- ")

if __name__ == "__main__":
    asyncio.run(main()) 