#!/usr/bin/env python
import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from dotenv import load_dotenv
# from cryptography.fernet import Fernet # No longer needed here
import logging

# Configure logger for this module
logger = logging.getLogger(__name__)

# --- Add project root to sys.path ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path: # Check before inserting
    sys.path.insert(0, PROJECT_ROOT)
# --- End Addition ---

# Load environment variables from .env file
load_dotenv()

# Assuming your core models and session setup are accessible
# Adjust the import paths based on your project structure
from core.config import settings # Now this should work
from core.database.session import async_session_factory, Base # Use factory directly
from core.database.models.panel import Panel, PanelType # Import PanelType too
from core.database.models.location import Location # Import Location model
from core.security import encrypt_data # Assuming you have encryption functions

# Panel details provided by the user (Consider moving to .env or config later)
PANEL_USERNAME = "NXBhg0pS11"
PANEL_PASSWORD = "Tr6FN86IOa"
PANEL_PORT = 30335
PANEL_WEB_BASE_PATH = "k2WVbEsXaJPx11U"
PANEL_ACCESS_URL = f"http://65.109.189.171:{PANEL_PORT}/{PANEL_WEB_BASE_PATH}"
PANEL_NAME = "Initial 3x-UI Panel" # A descriptive name
PANEL_TYPE = PanelType.XUI # Use Enum member directly

# Location details for seeding
# DEFAULT_LOCATION_ID = 1 # No longer needed
DEFAULT_LOCATION_NAME = "Default Location 🇮🇷" # Find by name
DEFAULT_LOCATION_FLAG = "🇮🇷"

# --- SECRET_KEY Handling Simplified ---
# We assume SECRET_KEY is correctly set in .env and loaded via core.config.settings
# encrypt_data should handle fetching and using it.
if not settings.SECRET_KEY or settings.SECRET_KEY == "generate_a_strong_random_secret_key":
     logger.critical("❌ FATAL: SECRET_KEY is not set or is default in your .env file! Cannot proceed with panel seeding.")
     # sys.exit(1) # Exit or raise to stop the seeding process
     raise ValueError("SECRET_KEY is missing or default. Please generate one.")


async def seed_data(session: AsyncSession): # Accept session as argument
    logger.info("Seeding initial panel and ensuring default location...")
    try:
        # --- Ensure Default Location Exists (Find by Name) ---
        stmt_loc = select(Location).where(Location.name == DEFAULT_LOCATION_NAME)
        result_loc = await session.execute(stmt_loc)
        existing_location = result_loc.scalars().first()

        if existing_location:
            logger.info(f"🟡 Location '{DEFAULT_LOCATION_NAME}' already exists. Using it (ID: {existing_location.id}).")
            location_id_to_use = existing_location.id
        else:
            # If location doesn't exist, we should probably stop,
            # as seed_locations should have run first.
            logger.error(f"❌ Default location '{DEFAULT_LOCATION_NAME}' not found. Please ensure seed_locations runs before seed_initial_panel.")
            # Or, optionally create it here if absolutely necessary:
            # logger.info(f"➕ Adding default location: {DEFAULT_LOCATION_NAME}")
            # new_location = Location(name=DEFAULT_LOCATION_NAME, flag=DEFAULT_LOCATION_FLAG, is_active=True)
            # session.add(new_location)
            # await session.flush()
            # location_id_to_use = new_location.id
            # logger.info(f"✅ Location '{DEFAULT_LOCATION_NAME}' added successfully with ID: {location_id_to_use}")
            raise ValueError(f"Default location '{DEFAULT_LOCATION_NAME}' not found.")


        # --- Seed Initial Panel ---
        stmt_panel = select(Panel).where(Panel.url == PANEL_ACCESS_URL)
        result_panel = await session.execute(stmt_panel)
        existing_panel = result_panel.scalars().first()

        if existing_panel:
            logger.info(f"🟡 Panel with URL {PANEL_ACCESS_URL} already exists. Skipping.")
        else:
            logger.info(f"➕ Adding initial panel: {PANEL_NAME}")
            # Encrypt credentials using the key from settings
            try:
                encrypted_username = encrypt_data(PANEL_USERNAME.encode())
                encrypted_password = encrypt_data(PANEL_PASSWORD.encode())
            except Exception as enc_err:
                 logger.error(f"❌ Error encrypting panel credentials: {enc_err}", exc_info=True)
                 raise # Reraise to stop seeding

            if encrypted_username is None or encrypted_password is None:
                # This case should ideally be caught by the exception above, but double-check
                logger.error("❌ Error: Failed to encrypt panel credentials even after trying.")
                raise ValueError("Failed to encrypt panel credentials")

            new_panel = Panel(
                name=PANEL_NAME,
                panel_type=PANEL_TYPE, # Use the Enum member
                url=PANEL_ACCESS_URL,
                username=encrypted_username,
                password=encrypted_password,
                location_id=location_id_to_use, # Use the found/created location ID
                is_healthy=True, # Assume healthy initially
                is_active=True
            )
            session.add(new_panel)
            await session.flush() # Flush to get ID or catch errors
            logger.info(f"✅ Panel '{PANEL_NAME}' processed for addition.") # Changed log slightly

        logger.info("✅ Panel seeding step completed.")

    except Exception as e:
        # Log error but re-raise so seed_all can handle rollback/stop
        logger.error(f"❌ An error occurred during panel/location seeding: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    # This part is now for direct testing only, not used by seed_all
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__) # Initialize logger for direct run

    print("Directly running seed_data for initial Location and Panel...")

    async def run_direct_seed():
        async with async_session_factory() as session:
            try:
                 await seed_data(session)
                 await session.commit() # Commit only for direct run
                 logger.info("✅ Direct seeding finished successfully and committed.")
            except Exception as e:
                logger.error(f"❌ Error during direct seeding: {e}", exc_info=True)
                await session.rollback()
                logger.warning("Direct seeding rolled back due to error.")


    asyncio.run(run_direct_seed()) 