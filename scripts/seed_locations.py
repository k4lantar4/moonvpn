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
from core.database.models.location import Location

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define the default location data
DEFAULT_LOCATION_NAME = "Default Location 🇮🇷"
DEFAULT_LOCATION_DATA = {
    "name": DEFAULT_LOCATION_NAME,
    "flag": "🇮🇷",
    "is_active": True,
    # Add other fields with defaults or None if needed, matching the model
    "country_code": "IR", # Added country code example
    "description": "لوکیشن پیش فرض برای سرورها در ایران",
    "protocols_supported": "vless,vmess,trojan", # Example
    "inbound_tag_pattern": None,
    "default_remark_prefix": "Moon-IR",
    # remark_pattern and migration_remark_pattern use DB defaults
}

# --- Optional: Add more sample locations ---
SAMPLE_LOCATIONS = [
    {
        "name": "Germany 🇩🇪", "flag": "🇩🇪", "is_active": True, "country_code": "DE",
        "description": "Location in Germany", "protocols_supported": "vless,vmess",
        "default_remark_prefix": "Moon-DE"
    },
    {
        "name": "Netherlands 🇳🇱", "flag": "🇳🇱", "is_active": True, "country_code": "NL",
        "description": "Location in Netherlands", "protocols_supported": "vless,trojan",
        "default_remark_prefix": "Moon-NL"
    },
    # Add more locations as needed
]
# --- End Optional ---


async def seed_locations(session: AsyncSession):
    """Seeds the database with default and sample locations."""
    logger.info("Seeding locations...")

    locations_to_seed = [DEFAULT_LOCATION_DATA] + SAMPLE_LOCATIONS # Combine default and samples
    locations_added = 0

    for loc_data in locations_to_seed:
        loc_name = loc_data["name"]
        # Check if the location already exists by name
        stmt = select(Location).where(Location.name == loc_name)
        result = await session.execute(stmt)
        existing_location = result.scalar_one_or_none()

        if existing_location is None:
            try:
                # Ensure all required fields are present (or have defaults in the model)
                new_location = Location(**loc_data)
                session.add(new_location)
                await session.flush() # Flush to catch potential errors early
                logger.info(f"➕ Added location: {loc_name}")
                locations_added += 1
            except Exception as e:
                 logger.error(f"❌ Error adding location '{loc_name}': {e}", exc_info=True)
                 # Depending on strategy, you might want to raise or continue
                 raise # Reraise to trigger rollback in seed_all
        else:
            logger.info(f"🟡 Location '{loc_name}' already exists, skipping.")
            # Optional: Update existing location if needed?
            # for key, value in loc_data.items():
            #     if getattr(existing_location, key) != value:
            #         setattr(existing_location, key, value)
            #         logger.info(f"Updating {key} for location '{loc_name}'")
            # # No need to add again if updating

    if locations_added > 0:
        logger.info(f"✅ Successfully processed {locations_added} new location(s) for addition.")
    else:
        logger.info("✅ No new locations needed to be added.")
    # REMOVED COMMIT FROM HERE - It will be handled by seed_all


async def main():
    """Main function to run the seeding process independently (for testing)."""
    logger.info("--- Starting Location Seeding (Independent Run) --- ")
    async with async_session_factory() as session:
        try:
            await seed_locations(session)
            await session.commit() # Commit only if running independently
            logger.info("Independent run committed.")
        except Exception as e:
            logger.error(f"❌ An error occurred during independent location seeding: {e}", exc_info=True)
            await session.rollback()
            logger.info("Independent run rolled back.")
        finally:
            logger.info("--- Location Seeding (Independent Run) Finished --- ")

if __name__ == "__main__":
    asyncio.run(main()) 