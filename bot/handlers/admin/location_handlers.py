"""Handlers for managing Locations (Admin only)."""

import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession # For type hinting
from aiogram.fsm.context import FSMContext
from aiogram.filters.command import CommandObject

# Assuming dependency injection or middleware provides the session
from bot.services.location_service import LocationService
# Import admin role filter
from bot.filters.role import IsAdminFilter # Import the filter
# Import exceptions
from core.exceptions import NotFoundError, ServiceError

logger = logging.getLogger(__name__)
router = Router(name="admin-location-handlers")

# --- Add Location --- 
# Simple version without FSM for now
@router.message(Command("addlocation"), IsAdminFilter()) # Removed argument
async def handle_add_location(message: Message, session: AsyncSession): # Assuming session is injected
    """Handles the /addlocation command. Usage: /addlocation <Name> <Flag>"""
    args = message.text.split(maxsplit=2)
    if len(args) != 3:
        await message.reply("❌ **خطا:** فرمت دستور صحیح نیست.\n"
                          "استفاده صحیح: `/addlocation <نام_لوکیشن> <پرچم_ایموجی>`\n"
                          "مثال: `/addlocation Iran 🇮🇷`")
        return

    command, name, flag = args
    # Instantiate service without session
    location_service = LocationService()

    try:
        # Create the schema object first
        from core.schemas.location import LocationCreate
        location_in = LocationCreate(name=name, flag=flag, is_active=True)
        # Pass session to the service method
        new_location = await location_service.create_location(session, location_in=location_in)
        await message.reply(f"✅ لوکیشن '{new_location.name}' {new_location.flag} با موفقیت اضافه شد (ID: {new_location.id}).")
        logger.info(f"Admin {message.from_user.id} added location '{name}'")
    except ValueError as e:
        await message.reply(f"⚠️ **خطا در افزودن:** {e}")
    except Exception as e:
        logger.error(f"Error adding location '{name}': {e}", exc_info=True)
        await message.reply("❌ متاسفانه مشکلی در افزودن لوکیشن پیش آمد. لطفا لاگ‌ها را بررسی کنید.")

# --- List Locations --- 
@router.message(Command("listlocations"), IsAdminFilter()) # Removed argument
async def handle_list_locations(message: Message, session: AsyncSession):
    """Handles the /listlocations command."""
    # Instantiate service without session
    location_service = LocationService()
    try:
        # Pass session to the service method
        locations = await location_service.get_all_locations(session)
        if not locations:
            await message.reply("ℹ️ هیچ لوکیشنی یافت نشد.")
            return

        response_text = "📍 **لیست لوکیشن‌ها:**\n\n"
        for loc in locations:
            status = "فعال ✅" if loc.is_active else "غیرفعال ❌"
            response_text += f"- **ID:** `{loc.id}` | {loc.flag} **{loc.name}** | وضعیت: {status}\n"
        
        await message.reply(response_text)
    except Exception as e:
        logger.error(f"Error listing locations: {e}", exc_info=True)
        await message.reply("❌ خطایی در دریافت لیست لوکیشن‌ها رخ داد.")

# --- Delete Location --- 
@router.message(Command("deletelocation"), IsAdminFilter())
async def handle_delete_location(message: Message, command: CommandObject, session: AsyncSession):
    """Handles the /deletelocation command. Usage: /deletelocation <location_id>"""
    if command.args is None:
        await message.reply("❌ **خطا:** ID لوکیشن مشخص نشده است.\n"
                          "استفاده صحیح: `/deletelocation <ID>`\n"
                          "مثال: `/deletelocation 123`")
        return
    
    try:
        location_id = int(command.args.strip())
    except ValueError:
        await message.reply("❌ **خطا:** ID لوکیشن باید یک عدد صحیح باشد.")
        return

    location_service = LocationService()
    try:
        deleted_location = await location_service.delete_location(session, location_id=location_id)
        # Commit the session explicitly after successful deletion
        await session.commit() 
        await message.reply(f"✅ لوکیشن '{deleted_location.name}' {deleted_location.flag} (ID: {location_id}) با موفقیت حذف شد.")
        logger.info(f"Admin {message.from_user.id} deleted location ID {location_id}")
    except NotFoundError as e:
        # Rollback might be handled by middleware, but being explicit is safe
        await session.rollback() 
        await message.reply(f"⚠️ **خطا در حذف:** لوکیشنی با ID `{location_id}` یافت نشد.")
    except ServiceError as e:
        await session.rollback()
        await message.reply(f"🚫 **عملیات ناموفق:** {e}")
    except Exception as e:
        await session.rollback()
        logger.error(f"Error deleting location ID {location_id}: {e}", exc_info=True)
        await message.reply("❌ متاسفانه مشکلی در حذف لوکیشن پیش آمد.")

# --- Edit Location (Placeholder/TODO) ---
@router.message(Command("editlocation"), IsAdminFilter())
async def edit_location_command(message: Message, command: CommandObject, state: FSMContext):
    """Starts the process of editing a location."""
    # TODO: Implement FSM or inline keyboard flow for editing
    await message.reply("🚧 قابلیت ویرایش لوکیشن در حال ساخت است...")

# Register handlers with the router
@router.message(Command("editlocation"), IsAdminFilter()) # Removed argument
async def edit_location_command(message: Message, command: CommandObject, state: FSMContext):
    """Starts the process of editing a location."""

@router.message(Command("deletelocation"), IsAdminFilter()) # Removed argument
async def delete_location_command(message: Message, command: CommandObject, session: AsyncSession):
    """Handles the /deletelocation command.""" 