"""
کالبک‌های مربوط به نمایش لیست اینباندهای پنل برای ادمین
"""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.services.user_service import UserService
from core.services.panel_service import PanelService
from core.integrations.xui_client import XuiAuthenticationError, XuiConnectionError # Assuming these exist
from bot.buttons.panel_buttons import get_panel_management_keyboard
from bot.buttons.inbound_buttons import (
    get_panel_inbounds_keyboard,
    get_inbound_manage_buttons,
    format_inbound_details
)

logger = logging.getLogger(__name__)


def register_panel_callbacks(router: Router, session_pool: async_sessionmaker[AsyncSession]) -> None:
    """ثبت کال‌بک‌های نمایش لیست اینباندهای پنل"""
    
    @router.callback_query(F.data.startswith("panel_inbounds:"))
    async def panel_inbounds_list(callback: CallbackQuery, session: AsyncSession) -> None:
        """نمایش لیست اینباندهای پنل برای ادمین (فقط دکمه‌ها)"""
        await callback.answer()
        try:
            panel_id_str = callback.data.split(":")[1]
            if not panel_id_str.isdigit():
                raise ValueError("Invalid Panel ID format")
            panel_id = int(panel_id_str)

            # کنترل دسترسی ادمین
            user_service = UserService(session)
            user = await user_service.get_user_by_telegram_id(callback.from_user.id)
            if not user or user.role not in ["admin", "superadmin"]:
                await callback.answer("⛔️ دسترسی غیرمجاز!", show_alert=True)
                return

            # دریافت اینباندها از سرویس پنل
            panel_service = PanelService(session)
            inbounds = await panel_service.get_inbounds_by_panel_id(panel_id)

            # اگر اینباندی وجود نداشت
            if not inbounds:
                # Use the panel management keyboard if no inbounds
                keyboard = get_panel_management_keyboard(panel_id)
                await callback.message.edit_text(
                    f"⚠️ هیچ اینباندی در پنل #{panel_id} وجود ندارد.",
                    reply_markup=keyboard
                )
                return

            # نمایش لیست اینباندها با دکمه برای هر کدام
            text = f"📋 <b>اینباندهای پنل #{panel_id}</b>\\n\\n" \
                   f"لطفا اینباند مورد نظر برای مشاهده جزئیات و مدیریت را انتخاب کنید:"
            keyboard = get_panel_inbounds_keyboard(inbounds, panel_id)
            await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")

        except ValueError as e:
            logger.warning(f"Value error in panel_inbounds_list handler: {e}")
            await callback.answer(f"خطا: {e}", show_alert=True)
        except Exception as e:
            logger.error(f"Error in panel_inbounds_list handler: {e}", exc_info=True)
            await callback.answer("⚠️ خطایی در دریافت لیست اینباندها رخ داد.", show_alert=True)


    @router.callback_query(F.data.startswith("inbound_details:"))
    async def show_inbound_details(callback: CallbackQuery, session: AsyncSession) -> None:
        """نمایش جزئیات کامل یک اینباند خاص و دکمه‌های مدیریت آن"""
        await callback.answer()
        try:
            parts = callback.data.split(":")
            if len(parts) != 3 or not parts[1].isdigit() or not parts[2].isdigit():
                 raise ValueError("Invalid callback data format for inbound_details")
            panel_id = int(parts[1])
            inbound_id = int(parts[2])

            # کنترل دسترسی ادمین (دوباره چک شود برای امنیت)
            user_service = UserService(session)
            user = await user_service.get_user_by_telegram_id(callback.from_user.id)
            if not user or user.role not in ["admin", "superadmin"]:
                await callback.answer("⛔️ دسترسی غیرمجاز!", show_alert=True)
                return

            # دریافت مجدد لیست اینباندها
            panel_service = PanelService(session)
            all_inbounds = await panel_service.get_inbounds_by_panel_id(panel_id)

            # پیدا کردن اینباند مورد نظر
            selected_inbound = next((inb for inb in all_inbounds if inb.get("id") == inbound_id), None)

            if not selected_inbound:
                await callback.answer("❌ اینباند مورد نظر یافت نشد یا از پنل حذف شده است.", show_alert=True)
                # Optionally, refresh the list
                # Attempt to go back to the list view by calling the other handler's logic.
                # Create a new callback object or modify the existing one if necessary.
                # This part might need careful handling depending on aiogram's behavior.
                # For simplicity, let's just inform the user.
                await callback.message.edit_text(f"لیست اینباندهای پنل #{panel_id} نیاز به بروزرسانی دارد.",
                                                 reply_markup=get_panel_management_keyboard(panel_id)) # Go back to panel menu
                return

            # فرمت کردن جزئیات و ساخت کیبورد مدیریت
            details_text = format_inbound_details(selected_inbound)
            management_keyboard = get_inbound_manage_buttons(panel_id, inbound_id)

            # ویرایش پیام برای نمایش جزئیات و کیبورد
            await callback.message.edit_text(
                f"⚙️ <b>جزئیات اینباند {selected_inbound.get('remark', '')} ({inbound_id})</b>\\n\\n{details_text}",
                reply_markup=management_keyboard,
                parse_mode="HTML"
            )

        except ValueError as e:
             logger.warning(f"Value error in show_inbound_details handler: {e}")
             await callback.answer(f"خطا: {e}", show_alert=True)
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                logger.info("Message not modified, likely duplicate button press.")
                await callback.answer() # Silently answer if message not modified
            else:
                logger.error(f"Telegram API error in show_inbound_details: {e}", exc_info=True)
                await callback.answer("⚠️ خطایی در نمایش جزئیات رخ داد.", show_alert=True)
        except Exception as e:
            logger.error(f"Error in show_inbound_details handler: {e}", exc_info=True)
            await callback.answer("⚠️ خطایی در پردازش درخواست رخ داد.", show_alert=True)

    @router.callback_query(F.data.startswith("panel:test_connection:"))
    async def test_panel_connection_handler(callback: CallbackQuery, session: AsyncSession) -> None:
        """هندلر تست اتصال به پنل"""
        await callback.answer("⏳ در حال تست اتصال...")
        try:
            panel_id_str = callback.data.split(":")[-1]
            if not panel_id_str.isdigit():
                raise ValueError("Invalid Panel ID format")
            panel_id = int(panel_id_str)

            # کنترل دسترسی ادمین
            user_service = UserService(session)
            user = await user_service.get_user_by_telegram_id(callback.from_user.id)
            if not user or user.role not in ["admin", "superadmin"]:
                await callback.answer("⛔️ دسترسی غیرمجاز!", show_alert=True)
                return

            # تست اتصال از طریق سرویس
            panel_service = PanelService(session)
            success, error_message = await panel_service.test_panel_connection(panel_id)
            logger.info(f"Test connection result for panel {panel_id}: Success={success}, Error='{error_message}'")

            if success:
                await callback.answer("✅ اتصال به پنل برقرار شد.", show_alert=True)
            else:
                await callback.answer(f"❌ اتصال به پنل با خطا مواجه شد: {error_message}", show_alert=True)

        except ValueError as e:
            logger.warning(f"Value error in test_panel_connection_handler: {e}")
            await callback.answer(f"خطا در فرمت شناسه پنل: {e}", show_alert=True)
        except Exception as e:
            logger.error(f"Error in test_panel_connection_handler: {e}", exc_info=True)
            # Provide a more generic error if the specific service error wasn't caught
            await callback.answer("⚠️ خطای ناشناخته در تست اتصال رخ داد.", show_alert=True) 