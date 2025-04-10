"""Admin handlers package.

Aggregates all admin-specific routers.
"""

import logging
from aiogram import Router

# Import individual handler routers
from .panel_handlers import router as panel_handlers_router
from .location_handlers import router as location_handlers_router
from .panel_management import admin_panel_router as panel_management_router # Import sync router
# from .main import admin_router as legacy_main_router # Keep if needed temporarily

logger = logging.getLogger(__name__)

# Create the main router for the admin section
# We name it 'router' to be consistent if bot/main.py imports 'router' from here.
router = Router(name="admin-handlers") 

# Include the sub-routers
router.include_router(panel_handlers_router)
router.include_router(location_handlers_router)
router.include_router(panel_management_router) # Include sync router
# router.include_router(legacy_main_router) # Keep if needed temporarily

logger.info("Admin routers included: panel_handlers, location_handlers, panel_management") # Updated log

# Function to register all admin handlers
def register_all_admin_handlers(dp):
    """Register all admin handlers."""
    dp.include_router(router)
    logger.info("All admin handlers registered.")

# TODO: Add an overall admin command (e.g., /admin) to show admin menu
# TODO: Add admin role filter to this router or individual handlers
