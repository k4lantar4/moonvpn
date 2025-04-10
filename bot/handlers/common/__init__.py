"""Common handlers for basic bot interactions."""

from aiogram import Router

from .start import router as start_router
from .language import router as language_router # Import language router
# from .help import router as help_router # Assuming we will add help.py

# Rename router to common_router for clarity and consistency with main.py import
common_router = Router(name="common-handlers")

# Include sub-routers
common_router.include_router(start_router)
common_router.include_router(language_router) # Include language router
# common_router.include_router(help_router) # Keep commented if help.py doesn't exist yet
