"""
Admin panel callback handlers
"""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
import re

from core.services.panel_service import PanelService, PanelConnectionError, PanelSyncError
from core.services.inbound_service import InboundService
from core.services.user_service import UserService
from bot.keyboards.admin_keyboard import get_admin_panel_keyboard
from db.models.panel import PanelStatus, PanelType
from core.services.client_renewal_log_service import ClientRenewalLogService
from db import get_async_db
from bot.states.admin_states import RegisterPanelStates
from core.integrations.xui_client import XuiAuthenticationError, XuiConnectionError

# Import necessary button functions
from bot.buttons.inbound_buttons import get_panel_inbounds_keyboard, get_inbound_manage_buttons
from bot.buttons.admin_buttons import get_panel_list_keyboard

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
                "🎛 <b>پنل مدیریت</b>\n\n"
                f"📊 پنل‌های فعال: {len(active_panels)}\n"
                "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:"
            )
            
            await callback.message.edit_text(
                admin_text,
                reply_markup=get_admin_panel_keyboard(),
                parse_mode="HTML"
            )
            
        except Exception as e:
            logger.error(f"Error in admin panel callback: {e}", exc_info=True)
            await callback.answer("⚠️ Error loading admin panel", show_alert=True)
    
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
    @router.callback_query(F.data == "sync_panels")
    async def sync_panels(callback: CallbackQuery, session: AsyncSession) -> None:
        """
        Handle panel sync button click to synchronize all panels with their backend
        همگام‌سازی تمام پنل‌ها با سرور مربوطه
        """
        user_id = callback.from_user.id
        
        try:
            # Check if user is admin
            user_service = UserService(session)
            user = await user_service.get_user_by_telegram_id(user_id)
            
            if not user or user.role not in ["admin", "superadmin"]:
                await callback.answer("⛔️ Access denied!", show_alert=True)
                return
            
            # Inform user that sync is in progress
            await callback.answer("⏳ در حال همگام‌سازی... (Syncing panels...)", show_alert=False)
            
            # Sync panels using PanelService
            logger.info(f"شروع همگام‌سازی تمام پنل‌ها توسط ادمین {user_id} (Starting synchronization of all panels by admin {user_id})")
            panel_service = PanelService(session)
            sync_results = await panel_service.sync_all_panels_inbounds()
            
            success_count = len(sync_results)
            
            logger.info(f"همگام‌سازی {success_count} پنل با موفقیت انجام شد (Successfully synced {success_count} panels)")
            await callback.answer(
                f"✅ همگام‌سازی {success_count} پنل با موفقیت انجام شد! (Successfully synced {success_count} panels!)",
                show_alert=True
            )
            
        except Exception as e:
            logger.error(f"خطا در همگام‌سازی پنل‌ها: {e} (Error in sync panels callback: {e})", exc_info=True)
            await callback.answer("⚠️ خطا در همگام‌سازی پنل‌ها (Error syncing panels)", show_alert=True)
    
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
                
            status_text = "فعال" if panel.status == PanelStatus.ACTIVE else "غیرفعال" if panel.status == PanelStatus.INACTIVE else "خطا" if panel.status == PanelStatus.ERROR else str(panel.status)
            status_emoji = "✅" if panel.status == PanelStatus.ACTIVE else "⚠️" if panel.status == PanelStatus.INACTIVE else "❌" if panel.status == PanelStatus.ERROR else "❓"
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
            await callback.answer("⚠️ خطایی در نمایش منو رخ داد.", show_alert=True)

    @router.callback_query(F.data.startswith("panel_inbounds:"))
    async def panel_inbounds_list(callback: CallbackQuery, session: AsyncSession):
        """
        نمایش لیست اینباندهای یک پنل خاص با دکمه‌های مدیریت.
        Display the list of inbounds for a specific panel with management buttons.
        """
        await callback.answer()
        try:
            # Extract panel_id from callback_data (e.g., "panel_inbounds:123")
            match = re.match(r"panel_inbounds:(\d+)", callback.data)
            if not match:
                logger.warning(f"فرمت نامعتبر callback_data برای panel_inbounds: {callback.data} (Invalid callback_data format for panel_inbounds: {callback.data})")
                await callback.message.answer("خطای داخلی: شناسه پنل نامعتبر است.")
                return
            
            panel_id = int(match.group(1))
            logger.info(f"در حال دریافت لیست اینباندها برای پنل {panel_id} (Fetching inbound list for panel {panel_id})")

            # Check admin permission
            user_service = UserService(session)
            user = await user_service.get_user_by_telegram_id(callback.from_user.id)
            if not user or user.role not in ["admin", "superadmin"]:
                await callback.answer("⛔️ دسترسی غیرمجاز!", show_alert=True)
                return

            # Use InboundService instead of direct PanelService for inbounds
            inbound_service = InboundService(session)
            panel_service = PanelService(session)
            
            # Fetch the panel itself to show its name
            panel = await panel_service.get_panel_by_id(panel_id)
            if not panel:
                await callback.message.edit_text(f"❌ پنل با شناسه {panel_id} یافت نشد. (Panel with ID {panel_id} not found.)")
                return

            # Fetch inbounds using InboundService (not directly from PanelService)
            inbounds = await inbound_service.get_inbounds_by_panel_id(panel_id)
            logger.debug(f"تعداد {len(inbounds)} اینباند برای پنل {panel_id} یافت شد. ({len(inbounds)} inbounds found for panel {panel_id})")

            # Build keyboard
            keyboard = get_panel_inbounds_keyboard(inbounds, panel_id)

            # Add standard back button
            from aiogram.utils.keyboard import InlineKeyboardBuilder
            builder = InlineKeyboardBuilder.from_markup(keyboard)
            builder.row(InlineKeyboardButton(text="🔙 بازگشت", callback_data=f"panel_manage:{panel_id}"))
            keyboard = builder.as_markup()

            # Prepare message text
            text = f"⚙️ <b>مدیریت اینباندهای پنل:</b> {panel.name} ({panel.location_name})\n\n"
            if not inbounds:
                text += "⚠️ هیچ اینباندی برای این پنل یافت نشد. (No inbounds found for this panel.)"
            else:
                text += "لطفاً اینباند مورد نظر برای مدیریت را انتخاب کنید: (Please select an inbound to manage:)"
            
            await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")

        except ValueError:
            logger.warning(f"خطا در تبدیل شناسه پنل به عدد در panel_inbounds_list: {callback.data} (Error converting panel ID to int in panel_inbounds_list: {callback.data})")
            await callback.message.answer("خطای داخلی: شناسه پنل نامعتبر است.")
        except Exception as e:
            logger.error(f"خطا در کالبک panel_inbounds_list: {e} (Error in panel_inbounds_list callback: {e})", exc_info=True)
            await callback.answer("⚠️ خطا در دریافت لیست اینباندها. (Error getting inbound list)", show_alert=True)

    @router.callback_query(F.data.startswith("inbound_details:"))
    async def inbound_details(callback: CallbackQuery, session: AsyncSession):
        """
        نمایش جزئیات و دکمه‌های عملیاتی برای یک اینباند خاص.
        Display details and action buttons for a specific inbound.
        """
        await callback.answer()
        try:
            # Extract panel_id and remote_inbound_id from callback_data (e.g., "inbound_details:123:456")
            match = re.match(r"inbound_details:(\d+):(\d+)", callback.data)
            if not match:
                logger.warning(f"فرمت نامعتبر callback_data برای inbound_details: {callback.data}. (Invalid callback_data format for inbound_details)")
                await callback.message.answer("خطای داخلی: شناسه‌ها نامعتبر هستند.")
                return

            panel_id = int(match.group(1))
            remote_inbound_id = int(match.group(2))
            logger.info(f"در حال دریافت جزئیات اینباند با شناسه پنل {panel_id} و شناسه ریموت {remote_inbound_id}. (Fetching details for inbound with panel ID {panel_id} and remote ID {remote_inbound_id}).")
            
             # Check admin permission
            user_service = UserService(session)
            user = await user_service.get_user_by_telegram_id(callback.from_user.id)
            if not user or user.role not in ["admin", "superadmin"]:
                await callback.answer("⛔️ دسترسی غیرمجاز!", show_alert=True)
                return

            # TODO: Fetch specific inbound details from PanelService (if needed)
            # panel_service = PanelService(session)
            # inbound_info = await panel_service.get_inbound_details(panel_id, remote_inbound_id) 
            # For now, just display a placeholder message and the management keyboard.

            # Build the management keyboard using the remote_inbound_id
            keyboard = get_inbound_manage_buttons(panel_id, remote_inbound_id)
            
            # Placeholder text (replace with actual inbound details later)
            # You might want to retrieve the inbound's tag/remark from the database or panel here.
            text = (
                f"⚙️ <b>مدیریت اینباند (ID در پنل: {remote_inbound_id})</b>\n\n"
                f"پنل ID: {panel_id}\n\n"
                "🚧 جزئیات بیشتر به زودی... (More details coming soon...)\n\n"
                "لطفاً عملیات مورد نظر را انتخاب کنید: (Please select an action:)"
            )

            await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")

        except ValueError:
            logger.warning(f"خطا در تبدیل شناسه‌ها به عدد در inbound_details: {callback.data}. (Error converting IDs to int)")
            await callback.message.answer("خطای داخلی: شناسه‌ها نامعتبر هستند.")
        except Exception as e:
            logger.error(f"خطا در کالبک inbound_details برای پنل {panel_id} و اینباند {remote_inbound_id}: {e}. (Error in inbound_details callback for panel {panel_id} and inbound {remote_inbound_id}: {e}).", exc_info=True)
            await callback.answer("⚠️ خطا در نمایش جزئیات اینباند.", show_alert=True)

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
            
            error_message = f"❌ خطا در اتصال به پنل: {str(conn_err)}" # Default message
            # Check the underlying cause if available
            if conn_err.__cause__:
                if isinstance(conn_err.__cause__, XuiAuthenticationError):
                    error_message = f"❌ خطای احراز هویت: نام کاربری یا رمز عبور پنل اشتباه است. لطفا مجددا تلاش کنید."
                    logger.warning(f"Panel registration failed due to authentication error for {panel_url}")
                elif isinstance(conn_err.__cause__, XuiConnectionError):
                    error_message = f"❌ خطای اتصال به پنل: {str(conn_err.__cause__)}" # Use the more detailed message from XuiConnectionError
                    logger.warning(f"Panel registration failed due to connection error for {panel_url}: {conn_err.__cause__}")
                else:
                    # If the cause is something else, use the original PanelConnectionError message
                    error_message = f"❌ خطا در ارتباط با پنل: {str(conn_err)}" 
                    logger.warning(f"Panel registration failed due to PanelConnectionError with cause {type(conn_err.__cause__).__name__}: {conn_err}")
            else:
                 logger.warning(f"Panel registration failed due to PanelConnectionError (no specific cause): {conn_err}")

            await message.answer(error_message) # Show the more specific user-friendly message
        except ValueError as val_err:
            # Catch potential validation errors from service or database issues
            logger.error(f"Validation or DB error during panel registration for {panel_url}: {val_err}", exc_info=True)
            await message.answer(f"❌ خطا در ثبت اطلاعات پنل: {str(val_err)}")
        except Exception as e:
            # Catch any other unexpected errors
            logger.error(f"Unexpected error registering panel {panel_url}: {e}", exc_info=True)
            await message.answer(f"❌ خطای پیش‌بینی نشده در ثبت پنل رخ داد. لطفاً لاگ‌ها را بررسی کنید.")

        await state.clear()

    @router.callback_query(F.data.startswith("panel:test_connection:"))
    async def panel_connection_test(callback: CallbackQuery, session: AsyncSession):
        """
        تست اتصال به یک پنل خاص و اعلام نتیجه
        Test connection to a specific panel and report the result
        """
        try:
            # Correctly extract panel ID
            panel_id_str = callback.data.split(":")[2]
            panel_id = int(panel_id_str)
            logger.info(f"شروع تست اتصال به پنل {panel_id} توسط کاربر {callback.from_user.id} (Initiating connection test for panel ID: {panel_id} by user {callback.from_user.id})")

            # Check admin permission
            user_service = UserService(session)
            user = await user_service.get_user_by_telegram_id(callback.from_user.id)
            if not user or user.role not in ["admin", "superadmin"]:
                await callback.answer("⛔️ دسترسی غیرمجاز!", show_alert=True)
                return

            # Show initial feedback
            await callback.answer("⏳ در حال تست اتصال... (Testing connection...)", show_alert=False) 

            # Use PanelService for connection test
            panel_service = PanelService(session)
            success, error_message = await panel_service.test_panel_connection(panel_id)

            if success:
                logger.info(f"تست اتصال به پنل {panel_id} موفقیت‌آمیز بود (Panel ID: {panel_id} connection test successful)")
                await callback.answer("✅ اتصال به پنل با موفقیت برقرار شد. (Connection to panel successful)", show_alert=True)
                
                # Update panel status to ACTIVE if test is successful
                update_success = await panel_service.update_panel_status(panel_id, PanelStatus.ACTIVE)
                if update_success:
                    logger.info(f"وضعیت پنل {panel_id} پس از تست موفق به ACTIVE تغییر یافت (Panel {panel_id} status updated to ACTIVE after successful test)")
                    
                    # Refresh the panel management menu to show updated status
                    await callback.message.delete()
                    panel = await panel_service.get_panel_by_id(panel_id)
                    if panel:
                        from bot.buttons.panel_buttons import get_panel_management_keyboard
                        status_text = "فعال" if panel.status == PanelStatus.ACTIVE else "غیرفعال" if panel.status == PanelStatus.INACTIVE else "خطا"
                        status_emoji = "✅" if panel.status == PanelStatus.ACTIVE else "⚠️" if panel.status == PanelStatus.INACTIVE else "❌"
                        text = (
                            f"📟 پنل #{panel.id} – {panel.flag_emoji} {panel.location_name}\n"
                            f"وضعیت: {status_text} {status_emoji}\n"
                            f"آدرس: {panel.url}\n"
                            f"نوع: {panel.type.value}\n"
                            f"یادداشت: {panel.notes or '-'}\n\n"
                            "🔧 عملیات پنل:"  
                        )
                        await callback.message.answer(text, reply_markup=get_panel_management_keyboard(panel.id))
                else:
                    logger.error(f"خطا در به‌روزرسانی وضعیت پنل {panel_id} به ACTIVE پس از تست موفق (Failed to update panel {panel_id} status to ACTIVE after successful test)")
            else:
                logger.warning(f"تست اتصال به پنل {panel_id} با خطا مواجه شد: {error_message} (Panel ID: {panel_id} connection test failed: {error_message})")
                
                # Simplify the alert message for user
                simplified_error = error_message.split(":", 1)[-1].strip() if error_message else "خطای نامشخص"
                if not simplified_error or len(simplified_error) > 150:
                    simplified_error = "خطا در اتصال یا احراز هویت پنل."
                    
                await callback.answer(f"❌ تست اتصال ناموفق: {simplified_error} (Connection test failed)", show_alert=True)
                
                # Update panel status to ERROR
                update_success = await panel_service.update_panel_status(panel_id, PanelStatus.ERROR)
                if update_success:
                    logger.info(f"وضعیت پنل {panel_id} پس از تست ناموفق به ERROR تغییر یافت (Panel {panel_id} status updated to ERROR after failed test)")

        except ValueError:
            logger.error(f"شناسه پنل نامعتبر در داده کالبک: {callback.data} (Invalid panel ID received in callback data: {callback.data})")
            await callback.answer("⚠️ خطای داخلی: شناسه پنل نامعتبر است. (Internal error: Invalid panel ID)", show_alert=True)
        except Exception as e:
            logger.error(f"خطای پیش‌بینی نشده در تست اتصال پنل: {e} (Unexpected error during panel connection test: {e})", exc_info=True)
            await callback.answer("⚠️ خطای پیش‌بینی نشده در هنگام تست اتصال پنل. (Unexpected error during panel connection test)", show_alert=True)

    @router.callback_query(F.data.startswith("panel_manage_inbounds:"))
    async def panel_manage_inbounds_menu(callback: CallbackQuery, session: AsyncSession):
        """
        نمایش منوی مدیریت اینباندها برای یک پنل خاص
        Display the inbound management menu for a specific panel
        """
        await callback.answer()
        try:
            # Extract panel_id from callback_data
            panel_id = int(callback.data.split(":")[1])
            logger.info(f"در حال نمایش منوی مدیریت اینباندها برای پنل {panel_id} (Displaying inbound management menu for panel {panel_id})")
            
            # Check admin permission
            user_service = UserService(session)
            user = await user_service.get_user_by_telegram_id(callback.from_user.id)
            if not user or user.role not in ["admin", "superadmin"]:
                await callback.answer("⛔️ دسترسی غیرمجاز!", show_alert=True)
                return
                
            # Get panel details using PanelService
            panel_service = PanelService(session)
            panel = await panel_service.get_panel_by_id(panel_id)
            if not panel:
                await callback.message.edit_text(f"❌ پنل با شناسه {panel_id} یافت نشد. (Panel with ID {panel_id} not found.)")
                return
                
            # Build keyboard for inbound management
            keyboard = InlineKeyboardBuilder()
            keyboard.button(text="📋 مشاهده اینباندها", callback_data=f"panel_inbounds:{panel_id}")
            keyboard.button(text="🔄 همگام‌سازی اینباندها", callback_data=f"panel_sync_inbounds:{panel_id}")
            keyboard.button(text="➕ افزودن اینباند جدید", callback_data=f"panel_add_inbound:{panel_id}")
            keyboard.button(text="🔙 بازگشت", callback_data=f"panel_manage:{panel_id}")
            keyboard.adjust(1)
            
            # Prepare message text
            text = (
                f"🛠 <b>مدیریت اینباندهای پنل:</b> {panel.name} ({panel.location_name})\n\n"
                "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:"
            )
            
            await callback.message.edit_text(text, reply_markup=keyboard.as_markup(), parse_mode="HTML")
            
        except ValueError:
            logger.warning(f"خطا در تبدیل شناسه پنل به عدد در panel_manage_inbounds_menu: {callback.data} (Error converting panel ID to int in panel_manage_inbounds_menu: {callback.data})")
            await callback.message.answer("خطای داخلی: شناسه پنل نامعتبر است.")
        except Exception as e:
            logger.error(f"خطا در کالبک panel_manage_inbounds_menu: {e} (Error in panel_manage_inbounds_menu callback: {e})", exc_info=True)
            await callback.answer("⚠️ خطا در نمایش منوی مدیریت اینباندها. (Error displaying inbound management menu)", show_alert=True)

    @router.callback_query(F.data.startswith("panel_sync_inbounds:"))
    async def panel_sync_inbounds(callback: CallbackQuery, session: AsyncSession):
        """
        همگام‌سازی اینباندهای یک پنل خاص با سرور
        Synchronize inbounds of a specific panel with the server
        """
        try:
            # Extract panel_id from callback_data
            panel_id = int(callback.data.split(":")[1])
            logger.info(f"شروع همگام‌سازی اینباندهای پنل {panel_id} توسط کاربر {callback.from_user.id} (Starting inbound sync for panel {panel_id} by user {callback.from_user.id})")
            
            # Check admin permission
            user_service = UserService(session)
            user = await user_service.get_user_by_telegram_id(callback.from_user.id)
            if not user or user.role not in ["admin", "superadmin"]:
                await callback.answer("⛔️ دسترسی غیرمجاز!", show_alert=True)
                return
                
            # Show sync in progress message
            await callback.answer("⏳ در حال همگام‌سازی اینباندها... (Syncing inbounds...)", show_alert=False)
            
            # Use PanelService for sync
            panel_service = PanelService(session)
            
            # Get panel first to validate it exists
            panel = await panel_service.get_panel_by_id(panel_id)
            if not panel:
                await callback.message.edit_text(f"❌ پنل با شناسه {panel_id} یافت نشد. (Panel with ID {panel_id} not found.)")
                return
                
            # Sync panel inbounds
            try:
                await panel_service.sync_panel_inbounds(panel_id)
                logger.info(f"همگام‌سازی اینباندهای پنل {panel_id} با موفقیت انجام شد (Successfully synced inbounds for panel {panel_id})")
                await callback.answer("✅ همگام‌سازی اینباندها با موفقیت انجام شد. (Inbounds synced successfully)", show_alert=True)
                
                # Return to inbound management menu
                try:
                    await panel_manage_inbounds_menu(callback, session)
                except TelegramBadRequest as e:
                    # Handle "message is not modified" error gracefully - it's not a real error
                    if "message is not modified" in str(e):
                        logger.info(f"پیام تغییر نکرده است، نیازی به به‌روزرسانی نیست. (Message not modified, no need to update.)")
                    else:
                        # Rethrow other Telegram API errors
                        raise
                
            except PanelSyncError as e:
                logger.error(f"خطا در همگام‌سازی اینباندهای پنل {panel_id}: {e} (Error syncing inbounds for panel {panel_id}: {e})", exc_info=True)
                await callback.answer(f"❌ خطا در همگام‌سازی اینباندها: {e} (Error syncing inbounds)", show_alert=True)
                
                # Update panel status to ERROR
                await panel_service.update_panel_status(panel_id, PanelStatus.ERROR)
                
        except ValueError:
            logger.warning(f"خطا در تبدیل شناسه پنل به عدد در panel_sync_inbounds: {callback.data} (Error converting panel ID to int in panel_sync_inbounds: {callback.data})")
            await callback.message.answer("خطای داخلی: شناسه پنل نامعتبر است.")
        except Exception as e:
            logger.error(f"خطای پیش‌بینی نشده در همگام‌سازی اینباندها: {e} (Unexpected error in panel_sync_inbounds: {e})", exc_info=True)
            await callback.answer("⚠️ خطای پیش‌بینی نشده در همگام‌سازی اینباندها. (Unexpected error syncing inbounds)", show_alert=True)
            
    @router.callback_query(F.data.startswith("panel_toggle_status:"))
    async def panel_toggle_status(callback: CallbackQuery, session: AsyncSession):
        """
        تغییر وضعیت پنل بین فعال و غیرفعال
        Toggle panel status between active and inactive
        """
        try:
            # Extract panel_id from callback_data
            panel_id = int(callback.data.split(":")[1])
            logger.info(f"درخواست تغییر وضعیت پنل {panel_id} توسط کاربر {callback.from_user.id} (Panel status toggle request for panel {panel_id} by user {callback.from_user.id})")
            
            # Check admin permission
            user_service = UserService(session)
            user = await user_service.get_user_by_telegram_id(callback.from_user.id)
            if not user or user.role not in ["admin", "superadmin"]:
                await callback.answer("⛔️ دسترسی غیرمجاز!", show_alert=True)
                return
                
            # Get current panel status
            panel_service = PanelService(session)
            panel = await panel_service.get_panel_by_id(panel_id)
            if not panel:
                await callback.message.edit_text(f"❌ پنل با شناسه {panel_id} یافت نشد. (Panel with ID {panel_id} not found.)")
                return
                
            # Toggle status
            new_status = PanelStatus.INACTIVE if panel.status == PanelStatus.ACTIVE else PanelStatus.ACTIVE
            status_text = "غیرفعال" if new_status == PanelStatus.INACTIVE else "فعال"
            
            # Update panel status
            update_success = await panel_service.update_panel_status(panel_id, new_status)
            if update_success:
                logger.info(f"وضعیت پنل {panel_id} به {new_status.value} تغییر یافت (Panel {panel_id} status changed to {new_status.value})")
                await callback.answer(f"✅ وضعیت پنل به {status_text} تغییر یافت. (Panel status changed to {status_text})", show_alert=True)
                
                # Refresh panel management view to show updated status
                from bot.buttons.panel_buttons import get_panel_management_keyboard
                panel = await panel_service.get_panel_by_id(panel_id)  # Refresh panel data
                
                status_emoji = "✅" if panel.status == PanelStatus.ACTIVE else "⚠️" if panel.status == PanelStatus.INACTIVE else "❌"
                text = (
                    f"📟 پنل #{panel.id} – {panel.flag_emoji} {panel.location_name}\n"
                    f"وضعیت: {status_text} {status_emoji}\n"
                    f"آدرس: {panel.url}\n"
                    f"نوع: {panel.type.value}\n"
                    f"یادداشت: {panel.notes or '-'}\n\n"
                    "🔧 عملیات پنل:"  
                )
                
                try:
                    await callback.message.edit_text(text, reply_markup=get_panel_management_keyboard(panel.id))
                except TelegramBadRequest as e:
                    # Handle "message is not modified" error gracefully - it's not a real error
                    if "message is not modified" in str(e):
                        logger.info(f"پیام تغییر نکرده است، نیازی به به‌روزرسانی نیست. (Message not modified, no need to update.)")
                    else:
                        # Rethrow other Telegram API errors
                        raise
            else:
                logger.error(f"خطا در تغییر وضعیت پنل {panel_id} (Error changing panel {panel_id} status)")
                await callback.answer("❌ خطا در تغییر وضعیت پنل. (Error changing panel status)", show_alert=True)
                
        except ValueError:
            logger.warning(f"خطا در تبدیل شناسه پنل به عدد در panel_toggle_status: {callback.data} (Error converting panel ID to int in panel_toggle_status: {callback.data})")
            await callback.message.answer("خطای داخلی: شناسه پنل نامعتبر است.")
        except Exception as e:
            logger.error(f"خطای پیش‌بینی نشده در تغییر وضعیت پنل: {e} (Unexpected error in panel_toggle_status: {e})", exc_info=True)
            await callback.answer("⚠️ خطای پیش‌بینی نشده در تغییر وضعیت پنل. (Unexpected error toggling panel status)", show_alert=True)

    @router.callback_query(F.data.startswith("panel:sync:"))
    async def panel_sync(callback: CallbackQuery, session: AsyncSession):
        """
        همگام‌سازی یک پنل خاص با سرور و به‌روزرسانی اینباندهای آن
        Synchronize a specific panel with the server and update its inbounds
        """
        try:
            # Extract panel_id from callback_data
            panel_id = int(callback.data.split(":")[2])
            logger.info(f"شروع همگام‌سازی پنل {panel_id} توسط کاربر {callback.from_user.id} (Starting sync for panel {panel_id} by user {callback.from_user.id})")
            
            # Check admin permission
            user_service = UserService(session)
            user = await user_service.get_user_by_telegram_id(callback.from_user.id)
            if not user or user.role not in ["admin", "superadmin"]:
                await callback.answer("⛔️ دسترسی غیرمجاز!", show_alert=True)
                return
                
            # Show sync in progress message
            await callback.answer("⏳ در حال همگام‌سازی پنل... (Syncing panel...)", show_alert=False)
            
            # Use PanelService for sync
            panel_service = PanelService(session)
            
            # Get panel first to validate it exists
            panel = await panel_service.get_panel_by_id(panel_id)
            if not panel:
                await callback.answer(f"❌ پنل با شناسه {panel_id} یافت نشد.", show_alert=True)
                return
                
            # Perform sync operation
            try:
                await panel_service.sync_panel_inbounds(panel_id)
                logger.info(f"همگام‌سازی پنل {panel_id} با موفقیت انجام شد. (Panel {panel_id} synced successfully)")
                await callback.answer("✅ همگام‌سازی پنل با موفقیت انجام شد.", show_alert=True)
                
                # Refresh the management view to show updated panel
                from bot.buttons.panel_buttons import get_panel_management_keyboard
                panel = await panel_service.get_panel_by_id(panel_id)  # Get fresh panel data
                
                status_text = "فعال" if panel.status == PanelStatus.ACTIVE else "غیرفعال" if panel.status == PanelStatus.INACTIVE else "خطا"
                status_emoji = "✅" if panel.status == PanelStatus.ACTIVE else "⚠️" if panel.status == PanelStatus.INACTIVE else "❌"
                text = (
                    f"📟 پنل #{panel.id} – {panel.flag_emoji} {panel.location_name}\n"
                    f"وضعیت: {status_text} {status_emoji}\n"
                    f"آدرس: {panel.url}\n"
                    f"نوع: {panel.type.value}\n"
                    f"یادداشت: {panel.notes or '-'}\n\n"
                    "🔧 عملیات پنل:"  
                )
                
                try:
                    await callback.message.edit_text(text, reply_markup=get_panel_management_keyboard(panel.id))
                except TelegramBadRequest as e:
                    # Handle "message is not modified" error gracefully - it's not a real error
                    if "message is not modified" in str(e):
                        logger.info(f"پیام تغییر نکرده است، نیازی به به‌روزرسانی نیست. (Message not modified, no need to update.)")
                    else:
                        # Rethrow other Telegram API errors
                        raise
                
            except PanelConnectionError:
                logger.error(f"خطای اتصال به پنل {panel_id} هنگام همگام‌سازی (Connection error to panel {panel_id} during sync)")
                await callback.answer("❌ خطا در اتصال به پنل. لطفاً ابتدا اتصال را تست کنید.", show_alert=True)
            except PanelSyncError as sync_err:
                logger.error(f"خطای همگام‌سازی پنل {panel_id}: {sync_err} (Panel {panel_id} sync error: {sync_err})")
                await callback.answer(f"❌ خطا در همگام‌سازی: {sync_err}", show_alert=True)
                
        except ValueError:
            logger.warning(f"شناسه پنل نامعتبر در داده کالبک: {callback.data} (Invalid panel ID in callback data: {callback.data})")
            await callback.answer("⚠️ خطای داخلی: شناسه پنل نامعتبر است.", show_alert=True)
        except Exception as e:
            logger.error(f"خطای پیش‌بینی نشده در همگام‌سازی پنل: {e} (Unexpected error in panel sync: {e})", exc_info=True)
            await callback.answer("⚠️ خطای ناشناخته در همگام‌سازی پنل.", show_alert=True)

    @router.callback_query(F.data == "manage_panels")
    async def manage_panels(callback: CallbackQuery, session: AsyncSession) -> None:
        """
        نمایش لیست پنل‌ها برای مدیریت
        Display list of panels for management
        """
        user_id = callback.from_user.id
        
        try:
            # Check if user is admin
            user_service = UserService(session)
            user = await user_service.get_user_by_telegram_id(user_id)
            
            if not user or user.role not in ["admin", "superadmin"]:
                await callback.answer("⛔️ دسترسی غیرمجاز!", show_alert=True)
                return
            
            # Get all panels from PanelService
            panel_service = PanelService(session)
            panels = await panel_service.get_all_panels()
            
            # Sort panels by ID in descending order (newest first)
            if panels:
                panels.sort(key=lambda p: p.id, reverse=True)
            
            # Use our new button function to create keyboard
            keyboard = get_panel_list_keyboard(panels)
            
            # Create the message text
            if panels:
                panel_count = len(panels)
                active_count = sum(1 for p in panels if p.status == PanelStatus.ACTIVE)
                text = (
                    f"📋 <b>لیست پنل‌های سیستم</b>\n\n"
                    f"📊 تعداد کل پنل‌ها: {panel_count}\n"
                    f"✅ پنل‌های فعال: {active_count}\n"
                    f"⚠️ پنل‌های غیرفعال: {panel_count - active_count}\n\n"
                    "لطفاً یک پنل را برای مدیریت انتخاب کنید:"
                )
            else:
                text = (
                    "📋 <b>لیست پنل‌های سیستم</b>\n\n"
                    "❌ هیچ پنلی در سیستم ثبت نشده است.\n"
                    "با استفاده از دکمه زیر می‌توانید پنل جدیدی ثبت کنید:"
                )
            
            # Edit message with panels list
            await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
            logger.info(f"لیست پنل‌ها برای کاربر {user_id} نمایش داده شد. (Panels list shown to user {user_id}.)")
            
        except Exception as e:
            logger.error(f"خطا در مدیریت پنل‌ها: {e} (Error in manage_panels callback: {e})", exc_info=True)
            await callback.answer("⚠️ خطا در نمایش لیست پنل‌ها", show_alert=True)
