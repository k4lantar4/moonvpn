"""
Admin panel callback handlers
"""

import logging
from aiogram import Router, F
<<<<<<< HEAD
from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from aiogram import types
from aiogram.fsm.context import FSMContext
import re

from core.services.panel_service import PanelService, PanelConnectionError
from core.services.user_service import UserService
from bot.keyboards.admin_keyboard import get_admin_panel_keyboard
from db.models.panel import PanelStatus
from core.services.client_renewal_log_service import ClientRenewalLogService
from db import get_async_db
from bot.states.admin_states import RegisterPanelStates
=======
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.services.panel_service import PanelService
from core.services.user_service import UserService
from bot.keyboards.admin_keyboard import get_admin_panel_keyboard
from db.models.panel import PanelStatus
>>>>>>> 644afe0cd616ac99872ebfb4b1bd13f07cdc62c2

logger = logging.getLogger(__name__)

def register_admin_callbacks(router: Router, session_pool: async_sessionmaker[AsyncSession]) -> None:
    """Register admin panel callback handlers"""
    
    @router.callback_query(F.data == "admin_panel")
    async def admin_panel(callback: CallbackQuery, session: AsyncSession) -> None:
        """Handle admin panel button click"""
        user_id = callback.from_user.id
        
        try:
            # Check if user is admin
            user_service = UserService(session)
            user = await user_service.get_user_by_telegram_id(user_id)
            
            if not user or user.role not in ["admin", "superadmin"]:
                await callback.answer("⛔️ Access denied!", show_alert=True)
                return
            
            # Get admin panel stats
            panel_service = PanelService(session)
            active_panels = await panel_service.get_active_panels()
            
            admin_text = (
<<<<<<< HEAD
                "🎛 <b>پنل مدیریت</b>\n\n"
                f"📊 پنل‌های فعال: {len(active_panels)}\n"
                "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:"
=======
                "🎛 <b>Admin Panel</b>\n\n"
                f"📊 Active Panels: {len(active_panels)}\n"
                "Select an option below:"
>>>>>>> 644afe0cd616ac99872ebfb4b1bd13f07cdc62c2
            )
            
            await callback.message.edit_text(
                admin_text,
<<<<<<< HEAD
                reply_markup=get_admin_panel_keyboard(),
                parse_mode="HTML"
=======
                reply_markup=get_admin_panel_keyboard()
>>>>>>> 644afe0cd616ac99872ebfb4b1bd13f07cdc62c2
            )
            
        except Exception as e:
            logger.error(f"Error in admin panel callback: {e}", exc_info=True)
            await callback.answer("⚠️ Error loading admin panel", show_alert=True)
    
<<<<<<< HEAD
    @router.callback_query(F.data == "admin_users")
    async def admin_users(callback: CallbackQuery, session: AsyncSession) -> None:
        """Handle admin users button click (placeholder)"""
        try:
            # Check admin permission
            user_service = UserService(session)
            user = await user_service.get_user_by_telegram_id(callback.from_user.id)
            
            if not user or user.role not in ["admin", "superadmin"]:
                await callback.answer("⛔️ دسترسی غیرمجاز!", show_alert=True)
                return
            
            # Create placeholder message with back button
            keyboard = InlineKeyboardBuilder()
            keyboard.button(text="🔙 بازگشت", callback_data="admin_panel")
            
            await callback.message.edit_text(
                "👥 <b>مدیریت کاربران</b>\n\n"
                "🚧 این بخش در حال توسعه است...\n\n"
                "قابلیت‌های آینده:\n"
                "• مشاهده لیست کاربران\n"
                "• جستجوی کاربر\n"
                "• مدیریت دسترسی‌ها\n"
                "• مسدودسازی کاربر\n"
                "• مشاهده آمار کاربر",
                reply_markup=keyboard.as_markup(),
                parse_mode="HTML"
            )
            
        except Exception as e:
            logger.error(f"Error in admin users callback: {e}", exc_info=True)
            await callback.answer("⚠️ خطا در اجرای درخواست", show_alert=True)
    
    @router.callback_query(F.data == "admin_plans")
    async def admin_plans(callback: CallbackQuery, session: AsyncSession) -> None:
        """Handle admin plans button click (placeholder)"""
        try:
            # Check admin permission
            user_service = UserService(session)
            user = await user_service.get_user_by_telegram_id(callback.from_user.id)
            
            if not user or user.role not in ["admin", "superadmin"]:
                await callback.answer("⛔️ دسترسی غیرمجاز!", show_alert=True)
                return
            
            # Placeholder response
            await callback.answer("🚧 این بخش در حال توسعه است...", show_alert=True)
            
        except Exception as e:
            logger.error(f"Error in admin plans callback: {e}", exc_info=True)
            await callback.answer("⚠️ خطا در اجرای درخواست", show_alert=True)
    
    @router.callback_query(F.data == "admin_transactions")
    async def admin_transactions(callback: CallbackQuery, session: AsyncSession) -> None:
        """Handle admin transactions button click (placeholder)"""
        try:
            # Check admin permission
            user_service = UserService(session)
            user = await user_service.get_user_by_telegram_id(callback.from_user.id)
            
            if not user or user.role not in ["admin", "superadmin"]:
                await callback.answer("⛔️ دسترسی غیرمجاز!", show_alert=True)
                return
            
            # Placeholder response
            await callback.answer("🚧 این بخش در حال توسعه است...", show_alert=True)
            
        except Exception as e:
            logger.error(f"Error in admin transactions callback: {e}", exc_info=True)
            await callback.answer("⚠️ خطا در اجرای درخواست", show_alert=True)
    
    @router.callback_query(F.data == "admin_settings")
    async def admin_settings(callback: CallbackQuery, session: AsyncSession) -> None:
        """Handle admin settings button click (placeholder)"""
        try:
            # Check admin permission
            user_service = UserService(session)
            user = await user_service.get_user_by_telegram_id(callback.from_user.id)
            
            if not user or user.role not in ["admin", "superadmin"]:
                await callback.answer("⛔️ دسترسی غیرمجاز!", show_alert=True)
                return
            
            # Placeholder response
            await callback.answer("🚧 این بخش در حال توسعه است...", show_alert=True)
            
        except Exception as e:
            logger.error(f"Error in admin settings callback: {e}", exc_info=True)
            await callback.answer("⚠️ خطا در اجرای درخواست", show_alert=True)

    # Keep existing callbacks below this line
=======
>>>>>>> 644afe0cd616ac99872ebfb4b1bd13f07cdc62c2
    @router.callback_query(F.data == "sync_panels")
    async def sync_panels(callback: CallbackQuery, session: AsyncSession) -> None:
        """Handle panel sync button click"""
        user_id = callback.from_user.id
        
        try:
            # Check if user is admin
            user_service = UserService(session)
            user = await user_service.get_user_by_telegram_id(user_id)
            
            if not user or user.role not in ["admin", "superadmin"]:
                await callback.answer("⛔️ Access denied!", show_alert=True)
                return
            
            # Sync panels
            panel_service = PanelService(session)
            sync_results = await panel_service.sync_all_panels_inbounds()
            
            await callback.answer(
                f"✅ Successfully synced {len(sync_results)} panels!",
                show_alert=True
            )
            
        except Exception as e:
            logger.error(f"Error in sync panels callback: {e}", exc_info=True)
            await callback.answer("⚠️ Error syncing panels", show_alert=True)
    
    @router.callback_query(F.data == "admin_stats")
    async def admin_stats(callback: CallbackQuery, session: AsyncSession) -> None:
        """Handle admin stats button click"""
        user_id = callback.from_user.id
        
        try:
            # Check if user is admin
            user_service = UserService(session)
            user = await user_service.get_user_by_telegram_id(user_id)
            
            if not user or user.role not in ["admin", "superadmin"]:
                await callback.answer("⛔️ Access denied!", show_alert=True)
                return
            
            # Get stats
            total_users = len(await user_service.get_all_users())
            admins = len(await user_service.get_users_by_role("admin"))
            
            stats_text = (
                "📈 <b>System Statistics</b>\n\n"
                f"👥 Total Users: {total_users}\n"
                f"👮‍♂️ Admins: {admins}\n"
            )
            
            await callback.message.edit_text(
                stats_text,
                reply_markup=get_admin_panel_keyboard()
            )
            
        except Exception as e:
            logger.error(f"Error in admin stats callback: {e}", exc_info=True)
            await callback.answer("⚠️ Error loading stats", show_alert=True)

    @router.callback_query(F.data.startswith("panel_manage:"))
    async def panel_manage(callback: CallbackQuery, session: AsyncSession):
        """Display management menu for a specific panel"""
        await callback.answer()

        try:
            panel_id = int(callback.data.split(":")[1])
            # Fetch panel data
            panel_service = PanelService(session)
            panel = await panel_service.get_panel_by_id(panel_id)

            if not panel:
                await callback.message.answer("❌ پنل مورد نظر یافت نشد.", show_alert=True)
                return

            # Build panel info text with localized status
<<<<<<< HEAD
            if panel.status == PanelStatus.ACTIVE:
                status_text = "فعال"
                status_emoji = "✅"
            elif panel.status == PanelStatus.INACTIVE:
                status_text = "غیرفعال"
                status_emoji = "⚠️"
            elif panel.status == PanelStatus.ERROR:
                 status_text = "خطا"
                 status_emoji = "❌" 
            else: # Fallback for unexpected statuses
                status_text = str(panel.status)
                status_emoji = "❓"
                
=======
            status_text = "فعال" if panel.status == PanelStatus.ACTIVE else "غیرفعال" if panel.status == PanelStatus.DISABLED else "حذف شده"
            status_emoji = "✅" if panel.status == PanelStatus.ACTIVE else "❌"
>>>>>>> 644afe0cd616ac99872ebfb4b1bd13f07cdc62c2
            text = (
                f"📟 پنل #{panel.id} – {panel.flag_emoji} {panel.location_name}\n"
                f"وضعیت: {status_text} {status_emoji}\n"
                f"آدرس: {panel.url}\n"
                f"نوع: {panel.type.value}\n"
                f"یادداشت: {panel.notes or '-'}\n\n"
                "🔧 عملیات پنل:"  
            )

            # Get management buttons
            from bot.buttons.panel_buttons import get_panel_management_keyboard
            keyboard = get_panel_management_keyboard(panel.id)

            # Edit message
            await callback.message.edit_text(text, reply_markup=keyboard)

        except Exception as e:
            logger.error(f"Error in panel_manage handler: {e}", exc_info=True)
<<<<<<< HEAD
            await callback.answer("⚠️ خطایی در نمایش منو رخ داد.", show_alert=True)

    @router.callback_query(F.data == "admin:renewal_log")
    async def handle_renewal_log(callback: CallbackQuery):
        """Handle the renewal log request from admin."""
        try:
            async with get_async_db() as session:
                # Get the last 10 renewal logs
                service = ClientRenewalLogService(session)
                renewal_logs = await service.get_last_logs(limit=10)
                
                # Format the logs into readable text
                log_messages = []
                for log in renewal_logs:
                    operation_type = []
                    if log.time_added:
                        operation_type.append("زمان")
                    if log.data_added:
                        operation_type.append("حجم")
                    
                    operation_str = " و ".join(operation_type)
                    
                    # Format the increases
                    increases = []
                    if log.time_added:
                        increases.append(f"🕒 {log.time_added} روز")
                    if log.data_added:
                        increases.append(f"📊 {log.data_added} گیگابایت")
                    
                    increase_str = " و ".join(increases)
                    
                    log_messages.append(
                        f"👤 کاربر: {log.user.full_name}\n"
                        f"🆔 UUID: {log.client.uuid}\n"
                        f"🔄 نوع عملیات: تمدید {operation_str}\n"
                        f"📈 میزان افزایش: {increase_str}\n"
                        f"📅 تاریخ: {log.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
                        f"➖➖➖➖➖➖➖➖➖➖"
                    )
                
                # Create the final message
                message = "📄 گزارش آخرین تمدیدهای انجام شده:\n\n"
                message += "\n\n".join(log_messages) if log_messages else "هیچ تمدیدی یافت نشد."
                
                # Add back button
                keyboard = InlineKeyboardBuilder()
                keyboard.button(text="🔙 بازگشت", callback_data="admin_panel")
                
                # Send the message
                await callback.message.edit_text(
                    message,
                    reply_markup=keyboard.as_markup()
                )
                
        except Exception as e:
            logger.error(f"Error in renewal log handler: {e}", exc_info=True)
            await callback.answer("⚠️ خطا در دریافت گزارش تمدیدها", show_alert=True)

    @router.message(RegisterPanelStates.waiting_for_panel_url)
    async def process_panel_url(message: types.Message, state: FSMContext):
        panel_url = message.text.strip()
        # Optionally, add URL validation here
        await state.update_data(panel_url=panel_url)
        await message.answer("✅ آدرس پنل دریافت شد.\n\nلطفا نام کاربری پنل را وارد کنید:")
        await state.set_state(RegisterPanelStates.waiting_for_username)

    @router.message(RegisterPanelStates.waiting_for_username)
    async def process_panel_username(message: types.Message, state: FSMContext):
        username = message.text.strip()
        await state.update_data(username=username)
        await message.answer("لطفا رمز عبور پنل را وارد کنید:")
        await state.set_state(RegisterPanelStates.waiting_for_password)

    @router.message(RegisterPanelStates.waiting_for_password)
    async def process_panel_password(message: types.Message, state: FSMContext):
        password = message.text.strip()
        await state.update_data(password=password)
        await message.answer("لطفا نام موقعیت مکانی پنل را به همراه ایموجی پرچم وارد کنید (مثلاً: `آلمان 🇩🇪` یا `هلند 🇳🇱`):")
        await state.set_state(RegisterPanelStates.waiting_for_location_name)

    @router.message(RegisterPanelStates.waiting_for_location_name)
    async def process_panel_location(message: types.Message, state: FSMContext, session: AsyncSession):
        location_name = message.text.strip()
        await state.update_data(location_name=location_name)

        data = await state.get_data()
        panel_url = data.get('panel_url')
        username = data.get('username')
        password = data.get('password')
        location_name = data.get('location_name')

        # Basic validation
        if not all([panel_url, username, password, location_name]):
             await message.answer("❌ اطلاعات پنل ناقص است. لطفاً دوباره فرآیند ثبت را شروع کنید.")
             await state.clear()
             return

        await message.answer("⏳ در حال بررسی و ثبت پنل، لطفاً صبر کنید...") # Inform user

        try:
            panel_service = PanelService(session)
            # Assuming register_panel needs name, location, flag_emoji
            # We need to extract flag_emoji from location_name or ask for it separately
            # For now, let's assume location_name contains both or service handles it.
            # A better approach would be to ask for them separately.
            # Let's use add_panel which we reviewed earlier
            # We need name, location, flag_emoji. Let's use location_name as name for now
            # and extract emoji if possible.
            # TODO: Improve panel info gathering (ask name, location, emoji separately)
            flag_emoji = ""
            clean_location_name = location_name
            # Simple regex to find emoji (might need refinement - using unicode property for flags)
            # Matches Flag emoji like 🇩🇪 by checking for two Regional Indicator symbols
            # Unicode range for Regional Indicator Symbols: U+1F1E6 to U+1F1FF
            match = re.search(r'([\U0001F1E6-\U0001F1FF]{2})', location_name)
            # Also match other single character flags/symbols if used
            # Removed the second regex search using \p{So} as it's unsupported by standard 're'
            # if not match:
            #     match = re.search(r'(\p{So})', location_name) 

            if match:
                flag_emoji = match.group(1)
                # Remove the emoji and surrounding spaces from the name
                clean_location_name = re.sub(r'\s*' + re.escape(flag_emoji) + r'\s*', '', location_name).strip()
            
            if not flag_emoji:
                # Assign a default or raise an error if emoji is mandatory
                flag_emoji = "🏳️" # Default flag
                logger.warning(f"Could not extract flag emoji from location: {location_name}. Using default.")

            # Use the cleaned name and extracted emoji
            panel = await panel_service.add_panel(
                 name=clean_location_name if clean_location_name else location_name, # Use original if cleaning failed
                 location=clean_location_name if clean_location_name else location_name,
                 flag_emoji=flag_emoji,
                 url=panel_url,
                 username=username,
                 password=password
            )

            # Check if panel was created successfully and has an ID
            if not panel or not panel.id:
                 logger.error(f"Failed to register panel (panel object empty or no ID) for {panel_url}. Panel: {panel}")
                 await message.answer("❌ خطا در ثبت پنل در پایگاه داده. لطفاً مجدداً تلاش کنید.")
            # Check if sync failed (status might be ERROR)
            elif panel.status == PanelStatus.ERROR:
                 logger.warning(f"Panel {panel.id} registered but sync failed. Status: {panel.status}")
                 await message.answer(f"⚠️ پنل در دیتابیس ثبت شد، اما همگام‌سازی اولیه با خطا مواجه شد. لطفاً وضعیت پنل را بررسی کنید.")
            else:
                 logger.info(f"✅ Panel registered successfully: ID={panel.id}, Location={panel.location_name}, Status={panel.status}")
                 await message.answer("✅ پنل جدید با موفقیت ثبت و همگام‌سازی شد.")

        except PanelConnectionError as conn_err:
            # Catch the specific connection/auth error from the service
            logger.warning(f"Panel connection failed during registration for {panel_url}: {conn_err}")
            await message.answer(f"❌ خطا در اتصال به پنل:\n{str(conn_err)}") # Show the user-friendly message from the exception
        except ValueError as val_err:
            # Catch potential validation errors from service or database issues
            logger.error(f"Validation or DB error during panel registration for {panel_url}: {val_err}", exc_info=True)
            await message.answer(f"❌ خطا در ثبت اطلاعات پنل: {str(val_err)}")
        except Exception as e:
            # Catch any other unexpected errors
            logger.error(f"Unexpected error registering panel {panel_url}: {e}", exc_info=True)
            await message.answer(f"❌ خطای پیش‌بینی نشده در ثبت پنل رخ داد. لطفاً لاگ‌ها را بررسی کنید.")

        await state.clear()
=======
            await callback.answer("⚠️ خطایی در نمایش منو رخ داد.", show_alert=True) 
>>>>>>> 644afe0cd616ac99872ebfb4b1bd13f07cdc62c2
