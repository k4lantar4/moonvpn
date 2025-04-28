"""
bot/callbacks/receipt_callbacks.py

این ماژول کالبک‌های مربوط به مدیریت رسیدها توسط ادمین را پیاده‌سازی می‌کند.
"""
import logging
from typing import Annotated

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from core.services.receipt_service import ReceiptService
from db.models.receipt_log import ReceiptStatus
from core.services.notification_service import NotificationService
from bot.states.receipt_states import ReceiptAdminStates
from bot.keyboards.receipt_keyboards import get_receipt_admin_keyboard, create_admin_undo_keyboard

# Initialize router
receipt_callbacks_router = Router(name="receipt_callbacks_router")
logger = logging.getLogger(__name__)


@receipt_callbacks_router.callback_query(F.data == "admin_pending_receipts")
async def handle_show_pending_receipts(
    call: CallbackQuery,
    session: AsyncSession,
    bot: Bot
):
    """نمایش لیست رسیدهای در انتظار تایید به ادمین"""
    admin_id = call.from_user.id
    
    # ساخت سرویس مدیریت رسید
    receipt_service = ReceiptService(session)
    
    # دریافت لیست رسیدهای در انتظار تایید
    pending_receipts = await receipt_service.get_pending_receipts(limit=10)
    
    if not pending_receipts:
        await call.answer("هیچ رسید در انتظار تاییدی وجود ندارد! 🎉", show_alert=True)
        return
    
    # پاسخ به کاربر با نمایش تعداد رسیدهای در انتظار
    await call.answer(f"{len(pending_receipts)} رسید در انتظار تایید")
    
    # ارسال هر رسید به صورت جداگانه
    for receipt in pending_receipts:
        # ساخت متن پیام
        amount_str = f"{receipt.amount:,}" if receipt.amount else "نامشخص"
        message_text = (
            f"📝 <b>رسید شماره {receipt.id}</b>\n\n"
            f"👤 کاربر: <code>{receipt.user_id}</code>\n"
            f"💰 مبلغ: {amount_str} تومان\n"
            f"🕒 تاریخ ارسال: {receipt.submitted_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"🔖 کد پیگیری: <code>{receipt.tracking_code}</code>\n"
        )
        
        if receipt.text_reference:
            message_text += f"\n📌 توضیحات کاربر:\n{receipt.text_reference}\n"
            
        # اگر عکس دارد، ارسال عکس با کپشن
        if receipt.photo_file_id:
            await bot.send_photo(
                chat_id=admin_id,
                photo=receipt.photo_file_id,
                caption=message_text,
                reply_markup=get_receipt_admin_keyboard(receipt.id)
            )
        else:
            # اگر عکس ندارد، ارسال متن
            await bot.send_message(
                chat_id=admin_id,
                text=message_text,
                reply_markup=get_receipt_admin_keyboard(receipt.id)
            )


@receipt_callbacks_router.callback_query(F.data.startswith("confirm_receipt:"))
async def handle_confirm_receipt(
    call: CallbackQuery,
    session: AsyncSession,
    bot: Bot
):
    """پردازش دکمه تایید رسید توسط ادمین"""
    try:
        receipt_id = int(call.data.split(":")[1])
        admin_id = call.from_user.id
        admin_mention = call.from_user.full_name
        
        logger.info(f"Admin {admin_id} attempting to confirm receipt {receipt_id}")
        
        # ساخت سرویس رسید
        receipt_service = ReceiptService(session)
        
        # تایید رسید
        updated_receipt = await receipt_service.approve_receipt(receipt_id, admin_id)
        
        if not updated_receipt:
            await call.answer("❌ خطا در تایید رسید. لطفاً دوباره تلاش کنید.", show_alert=True)
            logger.error(f"Failed to approve receipt {receipt_id} by admin {admin_id}")
            return
            
        # آپدیت پیام با نمایش وضعیت جدید
        original_text = call.message.text or call.message.caption or ""
        updated_text = (
            f"{original_text}\n\n"
            f"✅ <b>تایید شد</b>\n"
            f"👤 توسط: {admin_mention}\n"
            f"🕒 زمان: {updated_receipt.responded_at.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        # ایجاد دکمه لغو تایید
        undo_keyboard = create_admin_undo_keyboard("confirm", receipt_id)
        
        # آپدیت پیام
        if call.message.photo:
            await call.message.edit_caption(caption=updated_text, reply_markup=undo_keyboard)
        else:
            await call.message.edit_text(text=updated_text, reply_markup=undo_keyboard)
            
        await call.answer("✅ رسید با موفقیت تایید شد.")
        logger.info(f"Receipt {receipt_id} approved successfully by admin {admin_id}")
    
    except Exception as e:
        logger.error(f"Error in handle_confirm_receipt: {e}", exc_info=True)
        await call.answer("❌ خطای سیستمی رخ داد. لطفاً دوباره تلاش کنید.", show_alert=True)


@receipt_callbacks_router.callback_query(F.data.startswith("reject_receipt:"))
async def handle_reject_receipt(
    call: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    bot: Bot
):
    """پردازش دکمه رد رسید توسط ادمین"""
    receipt_id = int(call.data.split(":")[1])
    
    # ذخیره شناسه رسید در استیت
    await state.set_state(ReceiptAdminStates.AWAITING_REJECTION_REASON)
    await state.update_data(rejection_receipt_id=receipt_id)
    
    # درخواست دلیل رد از ادمین
    await call.message.reply(
        "🔍 لطفاً دلیل رد رسید را وارد کنید:\n"
        "برای رد بدون ذکر دلیل، عبارت <code>-</code> را ارسال کنید."
    )
    await call.answer()


@receipt_callbacks_router.message(ReceiptAdminStates.AWAITING_REJECTION_REASON)
async def process_rejection_reason(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    bot: Bot
):
    """پردازش دلیل رد رسید از ادمین"""
    # دریافت داده‌های استیت
    state_data = await state.get_data()
    receipt_id = state_data.get("rejection_receipt_id")
    
    if not receipt_id:
        await message.reply("❌ خطای داخلی: شناسه رسید یافت نشد. لطفاً دوباره تلاش کنید.")
        await state.clear()
        return
    
    admin_id = message.from_user.id
    admin_mention = message.from_user.full_name
    
    # دریافت دلیل رد
    rejection_reason = None if message.text == "-" else message.text
    
    logger.info(f"Admin {admin_id} rejecting receipt {receipt_id} with reason: {rejection_reason}")
    
    # ساخت سرویس رسید
    receipt_service = ReceiptService(session)
    
    # رد رسید
    updated_receipt = await receipt_service.reject_receipt(receipt_id, admin_id, rejection_reason)
    
    if not updated_receipt:
        await message.reply("❌ خطا در رد رسید. لطفاً دوباره تلاش کنید.")
        logger.error(f"Failed to reject receipt {receipt_id} by admin {admin_id}")
        await state.clear()
        return
    
    # پاسخ به ادمین
    await message.reply(f"✅ رسید شماره {receipt_id} با موفقیت رد شد.")
    
    # پیدا کردن پیام اصلی رسید برای آپدیت
    # این قسمت پیچیده است چون باید پیام اصلی را از تاریخچه چت پیدا کنیم
    # برای سادگی، فرض می‌کنیم کاربر با استفاده از دکمه‌های مدیریتی پنل ادمین کار می‌کند
    
    # آپدیت وضعیت در استیت
    await state.clear()
    logger.info(f"Receipt {receipt_id} rejected successfully by admin {admin_id}")


@receipt_callbacks_router.callback_query(F.data.startswith("undo_confirm:"))
async def handle_undo_confirm(
    call: CallbackQuery,
    session: AsyncSession,
    bot: Bot
):
    """پردازش دکمه لغو تایید رسید توسط ادمین"""
    # لغو تایید رسید - این قابلیت می‌تواند در نسخه‌های آینده پیاده‌سازی شود
    receipt_id = int(call.data.split(":")[1])
    admin_id = call.from_user.id
    
    await call.answer("⚠️ این قابلیت در حال حاضر پیاده‌سازی نشده است.", show_alert=True)
    logger.warning(f"Admin {admin_id} attempted to undo confirmation of receipt {receipt_id} - feature not implemented")


@receipt_callbacks_router.callback_query(F.data.startswith("undo_reject:"))
async def handle_undo_reject(
    call: CallbackQuery,
    session: AsyncSession,
    bot: Bot
):
    """پردازش دکمه لغو رد رسید توسط ادمین"""
    # لغو رد رسید - این قابلیت می‌تواند در نسخه‌های آینده پیاده‌سازی شود
    receipt_id = int(call.data.split(":")[1])
    admin_id = call.from_user.id
    
    await call.answer("⚠️ این قابلیت در حال حاضر پیاده‌سازی نشده است.", show_alert=True)
    logger.warning(f"Admin {admin_id} attempted to undo rejection of receipt {receipt_id} - feature not implemented") 