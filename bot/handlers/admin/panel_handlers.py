"""Handlers for managing Panels (Admin only)."""

import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.filters.command import CommandObject
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.services.panel_service import PanelService
from core.database.models.panel import PanelType # Import enum for validation
from core.exceptions import NotFoundError, ServiceError
# Import admin role filter
from bot.filters.role import IsAdminFilter # Import the filter
from bot.services.location_service import LocationService # Import LocationService

logger = logging.getLogger(__name__)
router = Router(name="admin-panel-handlers")

# --- Add Panel --- 
# Simple version without FSM
@router.message(Command("addpanel"), IsAdminFilter()) # Apply the filter
async def handle_add_panel(message: Message, session: AsyncSession):
    """Handles /addpanel. Usage: /addpanel <n> <type> <url> <loc_id> <user> <pass>"""
    args = message.text.split(maxsplit=6)
    if len(args) != 7:
        await message.reply("❌ **خطا:** فرمت دستور صحیح نیست.\n"
                          "استفاده صحیح: `/addpanel <نام> <نوع> <آدرس_کامل> <آیدی_لوکیشن> <نام_کاربری> <رمزعبور>`\n"
                          "نوع پنل معتبر: `xui`\n"
                          "مثال: `/addpanel Panel1 xui http://domain.com:54321/path 1 admin pass123`")
        return

    command, name, panel_type_str, url, location_id_str, username, password = args

    # Validate Panel Type
    try:
        panel_type = PanelType[panel_type_str.upper()]
    except KeyError:
        await message.reply(f"❌ **خطا:** نوع پنل نامعتبر: `{panel_type_str}`. نوع معتبر: `xui`")
        return
    
    # Validate Location ID
    try:
        location_id = int(location_id_str)
    except ValueError:
         await message.reply(f"❌ **خطا:** آیدی لوکیشن نامعتبر: `{location_id_str}`. باید عدد باشد.")
         return

    # Instantiate services with session
    panel_service = PanelService(session)
    location_service = LocationService(session)

    try:
        # Check if location exists
        location = await location_service.get_location_by_id(location_id)
        if not location:
            await message.reply(f"❌ **خطا:** لوکیشن با آیدی {location_id} یافت نشد.")
            return
            
        # Create panel without need to pass session explicitly
        new_panel = await panel_service.create_panel(
            name=name, 
            panel_type=panel_type, 
            url=url, 
            location_id=location_id, 
            username=username, 
            password=password, 
            is_active=True
        )
        # Commit after successful creation
        await session.commit()
        await message.reply(f"✅ پنل '{new_panel.name}' ({new_panel.url}) با موفقیت برای لوکیشن ID {location_id} اضافه شد (ID: \`{new_panel.id}\`)\.", parse_mode='MarkdownV2')
        logger.info(f"Admin {message.from_user.id} added panel '{name}'")
    except NotFoundError as e:
        await session.rollback()
        await message.reply(f"⚠️ **خطا:** {e}") # Location not found
    except ValueError as e:
        await session.rollback()
        await message.reply(f"⚠️ **خطا در افزودن:** {e}") # URL exists or other validation
    except Exception as e:
        await session.rollback()
        logger.error(f"Error adding panel '{name}': {e}", exc_info=True)
        await message.reply("❌ متاسفانه مشکلی در افزودن پنل پیش آمد. لطفا لاگ‌ها را بررسی کنید.")

# --- List Panels --- 
@router.message(Command("listpanels"), IsAdminFilter()) # Apply the filter
async def handle_list_panels(message: Message, session: AsyncSession):
    """Handles the /listpanels command."""
    panel_service = PanelService(session)
    try:
        # Pass session to service method
        panels = await panel_service.get_all_panels()
        if not panels:
            await message.reply("ℹ️ هیچ پنلی یافت نشد.")
            return

        response_text = "🖥️ **لیست پنل‌ها:**\n\n"
        for p in panels:
            status = "فعال ✅" if p.is_active else "غیرفعال ❌"
            health = "سالم ✅" if p.is_healthy else "ناسالم ❌" if p.is_healthy is False else "نامشخص ❓"
            loc_name = p.location.name if p.location else "[حذف شده]"
            loc_flag = p.location.flag if p.location else "🏴‍☠️"
            response_text += (
                f"- **ID:** `{p.id}` | **{p.name}** ({p.panel_type.name})\n"
                f"  آدرس: `{p.url}`\n"
                f"  لوکیشن: {loc_flag} {loc_name} (ID: {p.location_id})\n"
                f"  وضعیت: {status} | سلامت: {health}\n"
                f"---\n"
            )
        
        await message.reply(response_text)
    except Exception as e:
        logger.error(f"Error listing panels: {e}", exc_info=True)
        await message.reply("❌ خطایی در دریافت لیست پنل‌ها رخ داد.")

# --- Sync Inbounds --- 
@router.message(Command("syncinbounds"), IsAdminFilter())
async def handle_sync_inbounds(message: Message, session: AsyncSession):
    """Handles the /syncinbounds command. Usage: /syncinbounds <panel_id>"""
    args = message.text.split(maxsplit=1)
    if len(args) != 2:
        await message.reply(
            "❌ **خطا در دستور!** \n"
            "فرمت صحیح: `/syncinbounds <آیدی عددی پنل>`\n"
            "*برای پیدا کردن آیدی، از دستور `/listpanels` استفاده کنید.*\n\n"
            "✨ مثال: `/syncinbounds 1`",
            parse_mode='MarkdownV2'
        )
        return

    command, panel_id_str = args
    try:
        panel_id = int(panel_id_str)
    except ValueError:
         await message.reply(f"❌ **آیدی نامعتبر\\!**\nآیدی پنل (`{panel_id_str}`) باید یک عدد باشد.", parse_mode='MarkdownV2')
         return

    # Instantiate service with session
    panel_service = PanelService(session)
    
    # Check if panel exists first
    try:
        # Pass session to service method
        panel = await panel_service.get_panel_by_id(panel_id)
        if not panel:
            await message.reply(f"❌ **پنل یافت نشد\\!**\nمتاسفانه پنلی با آیدی \\`{panel_id}\\` در سیستم ثبت نشده است\\.", parse_mode='MarkdownV2')
            return
        # Check if panel is active before proceeding
        if not panel.is_active:
            await message.reply(f"⚠️ **پنل غیرفعال است\\!**\nپنل '{panel.name}' (ID: \\`{panel_id}\\`) در حال حاضر غیرفعال است و امکان همگام\\-سازی وجود ندارد\\.", parse_mode='MarkdownV2')
            return
            
    except Exception as e:
        logger.error(f"Error fetching panel {panel_id} before sync: {e}", exc_info=True)
        await message.reply(f"❌ **خطای سیستمی\\!**\nهنگام بررسی پنل \\`{panel_id}\\` مشکلی پیش آمد\\. لطفا لاگ\\u200cها را بررسی کنید\\.", parse_mode='MarkdownV2')
        return
        
    # Send a message indicating the start of the process
    processing_msg = await message.reply(
        f"⏳ **در حال شروع همگام‌سازی...**\n"
        f"پنل: **{panel.name}** (ID: \\`{panel_id}\\`)\n"
        f"*این عملیات ممکن است کمی زمان ببرد، لطفا صبور باشید...* ✨",
        parse_mode='MarkdownV2'
    )

    try:
        # Call the service method, no need to pass session explicitly
        fetched_count, added_count = await panel_service.sync_panel_inbounds(panel_id=panel_id)
        
        # Edit the processing message with the result
        await processing_msg.edit_text(
            f"✅ **همگام‌سازی با موفقیت انجام شد\\!** 🎉\n\n"
            f"**پنل:** {panel.name} (ID: \\`{panel_id}\\`)\n"
            f"📊 **تعداد دریافت شده از پنل:** {fetched_count}\n"
            f"💾 **تعداد ذخیره شده در دیتابیس:** {added_count}\n\n"
            f"*برای مشاهده جزئیات بیشتر، به لاگ‌ها مراجعه کنید\\.*",
            parse_mode='MarkdownV2'
        )
        logger.info(f"Admin {message.from_user.id} manually synced inbounds for panel {panel_id}. Fetched: {fetched_count}, Added: {added_count}")

    except NotFoundError:
         # This case should be caught earlier, but handle defensively
         await processing_msg.edit_text(f"❌ **پنل یافت نشد\\!** \\(خطای غیرمنتظره\\)\\nپنلی با آیدی \\`{panel_id}\\` یافت نشد\\.", parse_mode='MarkdownV2')
         logger.warning(f"NotFoundError reached unexpectedly in sync_inbounds handler for panel {panel_id}")

    except ServiceError as e:
        logger.error(f"ServiceError during manual inbound sync for panel {panel_id} triggered by admin {message.from_user.id}: {e}", exc_info=True)
        await processing_msg.edit_text(
             f"❌ **خطا در ارتباط با پنل\\!** 🤯\n\n"
             f"هنگام همگام\\u200cسازی با پنل '{panel.name}' (ID: \\`{panel_id}\\`) مشکلی پیش آمد\\.\n"
             f"**پیام خطا:** `{e}`\n\n"
             f"*لطفا از در دسترس بودن پنل، صحت اطلاعات اتصال و لاگ\\u200cها مطمئن شوید\\.*",
             parse_mode='MarkdownV2'
         )

    except Exception as e:
        logger.error(f"Unexpected error during manual inbound sync for panel {panel_id} triggered by admin {message.from_user.id}: {e}", exc_info=True)
        # Make sure to rollback in case of unexpected error during sync DB operations
        try:
            await session.rollback()
        except Exception as rb_err:
            logger.error(f"Failed to rollback session after unexpected sync error: {rb_err}")
        await processing_msg.edit_text(
            f"❌ **خطای ناشناخته\\!** 🤦\n\n"
            f"یک خطای پیش\\u200cبینی نشده هنگام همگام\\u200cسازی پنل \\`{panel_id}\\` رخ داد\\.\n"
            f"*لطفا لاگ\\u200cهای سیستم را برای جزئیات بیشتر بررسی کنید\\.*",
            parse_mode='MarkdownV2'
        )

# --- Delete Panel ---
@router.message(Command("deletepanel"), IsAdminFilter())
async def handle_delete_panel(message: Message, command: CommandObject, session: AsyncSession):
    """Handles the /deletepanel command. Usage: /deletepanel <panel_id>"""
    if command.args is None:
        await message.reply("❌ **خطا:** ID پنل مشخص نشده است.\n"
                          "استفاده صحیح: `/deletepanel <ID>`\n"
                          "مثال: `/deletepanel 1`")
        return
    
    try:
        panel_id = int(command.args.strip())
    except ValueError:
        await message.reply("❌ **خطا:** ID پنل باید یک عدد صحیح باشد.")
        return

    panel_service = PanelService(session)
    try:
        # Get panel name before deleting for the success message
        panel = await panel_service.get_panel_by_id(panel_id)
        if not panel:
            raise NotFoundError(f"Panel with id={panel_id} not found.")
        panel_name_for_msg = panel.name # Store name before potential deletion

        deleted_success = await panel_service.delete_panel(panel_id)
        
        if deleted_success:
            await session.commit() # Commit only if service layer indicated success
            await message.reply(f"✅ پنل '{panel_name_for_msg}' (ID: {panel_id}) با موفقیت حذف شد.")
            logger.info(f"Admin {message.from_user.id} deleted panel ID {panel_id}")
        else:
            # This case might not be reachable if delete_panel raises NotFoundError
            await session.rollback()
            await message.reply(f"⚠️ **خطا:** حذف پنل با ID `{panel_id}` ناموفق بود (ممکن است قبلا حذف شده باشد). ")
            
    except NotFoundError as e:
        await session.rollback()
        await message.reply(f"⚠️ **خطا:** پنلی با ID `{panel_id}` یافت نشد.")
    except ServiceError as e:
        await session.rollback()
        await message.reply(f"🚫 **عملیات ناموفق:** {e}") # E.g., panel has active clients
    except Exception as e:
        await session.rollback()
        logger.error(f"Error deleting panel ID {panel_id}: {e}", exc_info=True)
        await message.reply("❌ متاسفانه مشکلی در حذف پنل پیش آمد.")

# --- Check Panel Health --- 
@router.message(Command("checkpanelhealth"), IsAdminFilter())
async def handle_check_panel_health(message: Message, command: CommandObject, session: AsyncSession):
    """Handles the /checkpanelhealth command. Usage: /checkpanelhealth <panel_id>"""
    if command.args is None:
        await message.reply("❌ **خطا:** ID پنل مشخص نشده است.\n"
                          "استفاده صحیح: `/checkpanelhealth <ID>`\n"
                          "مثال: `/checkpanelhealth 1`")
        return
    
    try:
        panel_id = int(command.args.strip())
    except ValueError:
        await message.reply("❌ **خطا:** ID پنل باید یک عدد صحیح باشد.")
        return

    panel_service = PanelService(session)
    processing_msg = await message.reply(f"🩺 در حال بررسی سلامت پنل با ID `{panel_id}`... لطفاً کمی صبر کنید...")
    
    try:
        panel = await panel_service.get_panel_by_id(panel_id)
        if not panel:
             raise NotFoundError(f"Panel with id={panel_id} not found.")
        if not panel.is_active:
            await processing_msg.edit_text(f"⚠️ پنل '{panel.name}' (ID: `{panel_id}`) غیرفعال است. بررسی سلامت انجام نشد.")
            return

        health_result, error_message = await panel_service.check_panel_health(panel_id)
        # Commit explicitly since check_panel_health might now update panel.is_healthy
        await session.commit()
        
        result_emoji = "✅" if health_result else "❌"
        result_text = "سالم" if health_result else "ناسالم"
        status_message = f"{result_emoji} **وضعیت سلامت پنل '{panel.name}' (ID: `{panel_id}`): {result_text}**"
        
        if error_message and not health_result:
            status_message += f"\n\n⚠️ **علت:** {error_message}"
            
        await processing_msg.edit_text(status_message)
        logger.info(f"Admin {message.from_user.id} checked health for panel {panel_id}. Result: {result_text}")

    except NotFoundError:
        await processing_msg.edit_text(f"⚠️ **خطا:** پنلی با ID `{panel_id}` یافت نشد.")
    except ServiceError as e:
        await processing_msg.edit_text(f"🚫 **خطا در بررسی سلامت:** {e}")
    except Exception as e:
        logger.error(f"Error checking panel health for ID {panel_id}: {e}", exc_info=True)
        await processing_msg.edit_text("❌ متاسفانه مشکلی در بررسی سلامت پنل پیش آمد.")

# TODO: Implement handler for /editpanel