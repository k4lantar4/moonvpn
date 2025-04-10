#!/usr/bin/env python
"""Master script to seed the database with all initial data in the correct order."""

import asyncio
import os
import sys
import logging
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession
from core.database.session import async_session_factory
# Import individual seeders
from scripts.seed_roles import seed_roles
from scripts.seed_admin_user import seed_admin_user
from scripts.seed_locations import seed_locations
from scripts.seed_plan_categories import seed_plan_categories
from scripts.seed_plans import seed_plans
from scripts.seed_initial_panel import seed_data as seed_initial_panel_data
from scripts.seed_settings import seed_settings
from scripts.seed_notification_channels import seed_notification_channels
# ... etc

# --- Debugging sys.path ---
current_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(current_dir, '..'))
print(f"[DEBUG] Current directory (__file__): {current_dir}", file=sys.stderr)
print(f"[DEBUG] Calculated project root: {project_root}", file=sys.stderr)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f"[DEBUG] Added {project_root} to sys.path", file=sys.stderr)
else:
    print(f"[DEBUG] {project_root} already in sys.path", file=sys.stderr)
print(f"[DEBUG] Current sys.path: {sys.path}", file=sys.stderr)
# --- End Debugging ---

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def seed_all(session: AsyncSession):
    """
    Seeds all initial data required for the application in a specific order.
    """
    seed_order = [
        ("Roles", seed_roles),
        ("Admin User", seed_admin_user),
        ("Locations", seed_locations),
        ("Plan Categories", seed_plan_categories),
        ("Plans", seed_plans),
        ("Initial Panel", seed_initial_panel_data),
        ("Settings", seed_settings),
        ("Notification Channels", seed_notification_channels),
        # Add other seeders here if needed
    ]

    logger.info("--- Starting Database Seeding ---")
    all_successful = True
    for name, seeder_func in seed_order:
        try:
            logger.info(f"Seeding {name}...")
            await seeder_func(session)
            logger.info(f"✅ Successfully seeded {name}.")
        except ImportError as e:
             logger.error(f"❌ Import error while trying to seed {name}: {e}. Make sure the seeder function exists and is imported correctly.", exc_info=True)
             all_successful = False
             # Decide if you want to stop on import error or continue
             # break
        except Exception as e:
            logger.error(f"❌ Error during seeding {name}: {e}", exc_info=True)
            await session.rollback() # Rollback immediately on error
            logger.warning(f"Rolling back transaction due to error in {name} seeder.")
            all_successful = False
            break # Stop seeding process on error

    if all_successful:
         logger.info("--- Committing Seeded Data ---")
         await session.commit()
         logger.info("✅✅✅ Database seeding completed and committed successfully! ✅✅✅")
    else:
         logger.error("--- Database seeding failed. Transaction rolled back. ---")

async def main():
    logger.info("🚀 Initiating database seeding process...")
    # We handle commit/rollback within seed_all now
    async with async_session_factory() as session:
        await seed_all(session)
    logger.info("🏁 Database seeding process finished.")

if __name__ == "__main__":
    # Ensure project root is in path if running script directly
    current_dir = os.path.dirname(__file__)
    project_root = os.path.abspath(os.path.join(current_dir, '..'))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
        logger.debug(f"Added {project_root} to sys.path for direct script execution.")

    asyncio.run(main()) 