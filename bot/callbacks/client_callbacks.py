"""
هندلرهای callback مربوط به مدیریت کلاینت‌های VPN (دریافت کانفیگ، ریست ترافیک، حذف)
"""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.services.panel_service import PanelService

logger = logging.getLogger(__name__)

def register_client_callbacks(router: Router, session_pool: async_sessionmaker[AsyncSession]) -> None:
    """
    ثبت هندلرهای callback مربوط به مدیریت کلاینت‌ها
    """
    
    @router.callback_query(F.data.startswith("inbound_client_config:"))
    async def inbound_client_config(callback: CallbackQuery, session: AsyncSession) -> None:
        """دریافت لینک کانفیگ کلاینت"""
        await callback.answer()
        parts = callback.data.split(":")
        if len(parts) != 4 or not parts[1].isdigit() or not parts[2].isdigit():
            await callback.answer("⚠️ فرمت داده نامعتبر است.", show_alert=True)
            return
        panel_id = int(parts[1])
        inbound_id = int(parts[2])
        uuid = parts[3]
        try:
            panel_service = PanelService(session)
            config_url = await panel_service.get_client_config(panel_id, inbound_id, uuid)
            await callback.message.edit_text(
                f"📤 <b>لینک کانفیگ کلاینت</b> (UUID: <code>{uuid}</code>):\n{config_url}",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Error in inbound_client_config: {e}", exc_info=True)
            await callback.answer("⚠️ خطا در دریافت لینک کانفیگ.", show_alert=True)

    @router.callback_query(F.data.startswith("inbound_client_reset:"))
    async def inbound_client_reset(callback: CallbackQuery, session: AsyncSession) -> None:
        """ارسال درخواست تأیید برای ریست ترافیک کلاینت"""
        await callback.answer()
        parts = callback.data.split(":")
        if len(parts) != 4 or not parts[1].isdigit() or not parts[2].isdigit():
            await callback.answer("⚠️ فرمت داده نامعتبر است.", show_alert=True)
            return
        panel_id = int(parts[1])
        inbound_id = int(parts[2])
        uuid = parts[3]
        confirm_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ تأیید", callback_data=f"confirm_client_reset:{panel_id}:{inbound_id}:{uuid}"),
                InlineKeyboardButton(text="❌ لغو", callback_data=f"cancel_client:{panel_id}:{inbound_id}:{uuid}")
            ]
        ])
        await callback.message.edit_text(
            f"⚠️ آیا از ریست ترافیک کلاینت <code>{uuid}</code> مطمئن هستید؟",
            reply_markup=confirm_keyboard,
            parse_mode="HTML"
        )

    @router.callback_query(F.data.startswith("confirm_client_reset:"))
    async def confirm_client_reset(callback: CallbackQuery, session: AsyncSession) -> None:
        """اجرای ریست ترافیک کلاینت پس از تأیید"""
        await callback.answer()
        parts = callback.data.split(":")
        panel_id = int(parts[1])
        inbound_id = int(parts[2])
        uuid = parts[3]
        try:
            panel_service = PanelService(session)
            result = await panel_service.reset_client_traffic(panel_id, uuid)
            if result:
                await callback.message.edit_text(f"✅ ترافیک کلاینت <code>{uuid}</code> با موفقیت ریست شد.", parse_mode="HTML")
            else:
                await callback.message.edit_text(f"❌ ریست ترافیک کلاینت <code>{uuid}</code> ناموفق بود.", parse_mode="HTML")
        except Exception as e:
            logger.error(f"Error in confirm_client_reset: {e}", exc_info=True)
            await callback.answer("⚠️ خطا در ریست ترافیک کلاینت.", show_alert=True)

    @router.callback_query(F.data.startswith("inbound_client_delete:"))
    async def inbound_client_delete(callback: CallbackQuery, session: AsyncSession) -> None:
        """ارسال درخواست تأیید برای حذف کلاینت"""
        await callback.answer()
        parts = callback.data.split(":")
        if len(parts) != 4 or not parts[1].isdigit() or not parts[2].isdigit():
            await callback.answer("⚠️ فرمت داده نامعتبر است.", show_alert=True)
            return
        panel_id = int(parts[1])
        inbound_id = int(parts[2])
        uuid = parts[3]
        confirm_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ تأیید", callback_data=f"confirm_client_delete:{panel_id}:{inbound_id}:{uuid}"),
                InlineKeyboardButton(text="❌ لغو", callback_data=f"cancel_client:{panel_id}:{inbound_id}:{uuid}")
            ]
        ])
        await callback.message.edit_text(
            f"⚠️ آیا از حذف کلاینت <code>{uuid}</code> مطمئن هستید؟",
            reply_markup=confirm_keyboard,
            parse_mode="HTML"
        )

    @router.callback_query(F.data.startswith("confirm_client_delete:"))
    async def confirm_client_delete(callback: CallbackQuery, session: AsyncSession) -> None:
        """حذف کلاینت پس از تأیید"""
        await callback.answer()
        parts = callback.data.split(":")
        panel_id = int(parts[1])
        inbound_id = int(parts[2])
        uuid = parts[3]
        try:
            panel_service = PanelService(session)
            result = await panel_service.delete_client(panel_id, inbound_id, uuid)
            if result:
                await callback.message.edit_text(f"✅ کلاینت <code>{uuid}</code> با موفقیت حذف شد.", parse_mode="HTML")
            else:
                await callback.message.edit_text(f"❌ حذف کلاینت <code>{uuid}</code> ناموفق بود.", parse_mode="HTML")
        except Exception as e:
            logger.error(f"Error in confirm_client_delete: {e}", exc_info=True)
            await callback.answer("⚠️ خطا در حذف کلاینت.", show_alert=True)

    @router.callback_query(F.data.startswith("cancel_client:"))
    async def cancel_client_action(callback: CallbackQuery) -> None:
        """لغو عملیات مدیریت کلاینت"""
        await callback.answer("❌ عملیات لغو شد.", show_alert=True) 