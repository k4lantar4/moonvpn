"""
هندلرهای کالبک مدیریت رسیدهای پرداخت برای ادمین
"""

import logging
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from core.services.receipt_service import ReceiptService
from core.services.user_service import UserService
from db.models.receipt_log import ReceiptStatus
from bot.states.receipt_states import ReceiptAdminStates
from bot.buttons.admin.receipt_buttons import get_receipt_list_keyboard, get_receipt_manage_buttons
from core.services.admin_permission_service import AdminPermissionService

logger = logging.getLogger(__name__)

def register_admin_receipt_callbacks(router: Router) -> None:
    """ثبت کالبک‌های مدیریت رسیدها برای ادمین"""
    
    @router.callback_query(F.data == "admin:receipt:pending")
    async def receipt_pending_list(callback: CallbackQuery, session: AsyncSession, bot: Bot) -> None:
        """
        نمایش لیست رسیدهای در انتظار تایید
        
        Args:
            callback (CallbackQuery): کالبک تلگرام
            session (AsyncSession): نشست دیتابیس
            bot (Bot): نمونه ربات تلگرام
        """
        try:
            # بررسی دسترسی ادمین
            user_service = UserService(session)
            user = await user_service.get_user_by_telegram_id(callback.from_user.id)
            
            if not user or user.role not in ["admin", "superadmin"]:
                await callback.answer("⛔️ دسترسی غیرمجاز!", show_alert=True)
                return
            
            # دریافت لیست رسیدهای در انتظار تایید
            receipt_service = ReceiptService(session)
            pending_receipts = await receipt_service.get_pending_receipts(limit=10)
            
            # ساخت متن پیام
            if not pending_receipts:
                text = "🎉 <b>هیچ رسید در انتظار تاییدی وجود ندارد!</b>"
                await callback.message.edit_text(text, parse_mode="HTML")
                return
            
            text = f"🧾 <b>رسیدهای در انتظار تایید</b> ({len(pending_receipts)})\n\n"
            text += "لطفاً روی هر رسید کلیک کنید تا جزئیات آن را مشاهده کنید."
            
            # نمایش کیبورد رسیدها
            keyboard = get_receipt_list_keyboard(pending_receipts)
            
            await callback.message.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            
        except Exception as e:
            logger.error(f"خطا در نمایش لیست رسیدهای در انتظار: {e}", exc_info=True)
            await callback.answer("⚠️ خطا در بارگذاری لیست رسیدها", show_alert=True)
    
    @router.callback_query(F.data.startswith("admin:receipt:manage:"))
    async def receipt_manage(callback: CallbackQuery, session: AsyncSession, bot: Bot) -> None:
        """
        نمایش منوی مدیریت برای یک رسید خاص
        
        Args:
            callback (CallbackQuery): کالبک تلگرام
            session (AsyncSession): نشست دیتابیس
            bot (Bot): نمونه ربات تلگرام
        """
        try:
            # دریافت شناسه رسید
            receipt_id = int(callback.data.split(":")[3])
            
            # بررسی دسترسی ادمین
            user_service = UserService(session)
            user = await user_service.get_user_by_telegram_id(callback.from_user.id)
            
            if not user or user.role not in ["admin", "superadmin"]:
                await callback.answer("⛔️ دسترسی غیرمجاز!", show_alert=True)
                return
            
            # دریافت اطلاعات رسید
            receipt_service = ReceiptService(session)
            receipt = await receipt_service.get_receipt_by_id(receipt_id)
            
            if not receipt:
                await callback.answer("❌ رسید مورد نظر یافت نشد.", show_alert=True)
                return
            
            # اگر رسید تصویر دارد، ارسال تصویر با کپشن
            if receipt.photo_file_id:
                # ساخت متن اطلاعات رسید
                amount_str = f"{receipt.amount:,}" if receipt.amount else "نامشخص"
                caption = (
                    f"📝 <b>رسید شماره {receipt.id}</b>\n\n"
                    f"👤 کاربر: <code>{receipt.user_id}</code>\n"
                    f"💰 مبلغ: {amount_str} تومان\n"
                    f"🕒 تاریخ ارسال: {receipt.submitted_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"🔖 کد پیگیری: <code>{receipt.tracking_code}</code>\n"
                    f"💳 کارت: <code>{receipt.bank_card.card_number}</code> ({receipt.bank_card.bank_name})\n"
                )
                
                if receipt.text_reference:
                    caption += f"\n📌 توضیحات کاربر:\n{receipt.text_reference}\n"
                
                # وضعیت رسید
                status_text = "در انتظار تایید" if receipt.status == ReceiptStatus.PENDING else \
                              "تایید شده" if receipt.status == ReceiptStatus.APPROVED else \
                              "رد شده" if receipt.status == ReceiptStatus.REJECTED else "منقضی شده"
                status_emoji = "⏳" if receipt.status == ReceiptStatus.PENDING else \
                               "✅" if receipt.status == ReceiptStatus.APPROVED else \
                               "❌" if receipt.status == ReceiptStatus.REJECTED else "⌛"
                
                caption += f"\n📊 وضعیت: {status_emoji} {status_text}"
                
                # ارسال عکس با کیبورد مدیریت رسید
                await bot.send_photo(
                    chat_id=callback.from_user.id,
                    photo=receipt.photo_file_id,
                    caption=caption,
                    reply_markup=get_receipt_manage_buttons(receipt_id),
                    parse_mode="HTML"
                )
                
                # پیام قبلی را بدون تغییر نگه می‌داریم
                await callback.answer()
                
            else:
                # اگر رسید تصویر ندارد، اطلاعات را به صورت متنی نمایش می‌دهیم
                amount_str = f"{receipt.amount:,}" if receipt.amount else "نامشخص"
                text = (
                    f"📝 <b>رسید شماره {receipt.id}</b>\n\n"
                    f"👤 کاربر: <code>{receipt.user_id}</code>\n"
                    f"💰 مبلغ: {amount_str} تومان\n"
                    f"🕒 تاریخ ارسال: {receipt.submitted_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"🔖 کد پیگیری: <code>{receipt.tracking_code}</code>\n"
                    f"💳 کارت: <code>{receipt.bank_card.card_number}</code> ({receipt.bank_card.bank_name})\n"
                )
                
                if receipt.text_reference:
                    text += f"\n📌 توضیحات کاربر:\n{receipt.text_reference}\n"
                
                # وضعیت رسید
                status_text = "در انتظار تایید" if receipt.status == ReceiptStatus.PENDING else \
                              "تایید شده" if receipt.status == ReceiptStatus.APPROVED else \
                              "رد شده" if receipt.status == ReceiptStatus.REJECTED else "منقضی شده"
                status_emoji = "⏳" if receipt.status == ReceiptStatus.PENDING else \
                               "✅" if receipt.status == ReceiptStatus.APPROVED else \
                               "❌" if receipt.status == ReceiptStatus.REJECTED else "⌛"
                
                text += f"\n📊 وضعیت: {status_emoji} {status_text}"
                
                # ویرایش پیام قبلی
                await callback.message.edit_text(
                    text,
                    reply_markup=get_receipt_manage_buttons(receipt_id),
                    parse_mode="HTML"
                )
            
        except ValueError:
            logger.error(f"خطا در تبدیل شناسه رسید: {callback.data}")
            await callback.answer("⚠️ خطا در شناسه رسید", show_alert=True)
        except Exception as e:
            logger.error(f"خطا در نمایش مدیریت رسید: {e}", exc_info=True)
            await callback.answer("⚠️ خطا در بارگذاری مدیریت رسید", show_alert=True)
    
    @router.callback_query(F.data.startswith("admin:receipt:approve:"))
    async def receipt_approve(callback: CallbackQuery, session: AsyncSession) -> None:
        """
        تایید یک رسید
        
        Args:
            callback (CallbackQuery): کالبک تلگرام
            session (AsyncSession): نشست دیتابیس
        """
        try:
            # دریافت شناسه رسید
            receipt_id = int(callback.data.split(":")[3])
            admin_id = callback.from_user.id
            admin_mention = callback.from_user.full_name
            
            logger.info(f"Admin {admin_id} attempting to confirm receipt {receipt_id}")
            
            # بررسی دسترسی ادمین (مجوز تایید رسید)
            user_service = UserService(session)
            user = await user_service.get_user_by_telegram_id(admin_id)
            perm_service = AdminPermissionService(session)
            if not user or not await perm_service.has_permission(user, "can_approve_receipt"):
                await callback.answer("⛔️ شما مجوز تایید رسید را ندارید!", show_alert=True)
                return
            
            # تایید رسید
            receipt_service = ReceiptService(session)
            updated_receipt = await receipt_service.approve_receipt(receipt_id, admin_id)
            
            if not updated_receipt:
                await callback.answer("❌ خطا در تایید رسید. لطفاً دوباره تلاش کنید.", show_alert=True)
                logger.error(f"Failed to approve receipt {receipt_id} by admin {admin_id}")
                return
                
            # آپدیت پیام با نمایش وضعیت جدید
            original_text = callback.message.text or callback.message.caption or ""
            updated_text = (
                f"{original_text}\n\n"
                f"✅ <b>تایید شد</b>\n"
                f"👤 توسط: {admin_mention}\n"
                f"🕒 زمان: {updated_receipt.responded_at.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            # آپدیت پیام
            if hasattr(callback.message, 'photo') and callback.message.photo:
                await callback.message.edit_caption(caption=updated_text, reply_markup=None)
            else:
                await callback.message.edit_text(text=updated_text, reply_markup=None)
                
            await callback.answer("✅ رسید با موفقیت تایید شد.")
            logger.info(f"Receipt {receipt_id} approved successfully by admin {admin_id}")
        
        except Exception as e:
            logger.error(f"Error in approve_receipt: {e}", exc_info=True)
            await callback.answer("❌ خطای سیستمی رخ داد. لطفاً دوباره تلاش کنید.", show_alert=True)
    
    @router.callback_query(F.data.startswith("admin:receipt:reject:"))
    async def receipt_reject(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
        """
        رد یک رسید
        
        Args:
            callback (CallbackQuery): کالبک تلگرام
            state (FSMContext): وضعیت FSM
            session (AsyncSession): نشست دیتابیس
        """
        try:
            # دریافت شناسه رسید
            receipt_id = int(callback.data.split(":")[3])
            admin_id = callback.from_user.id
            
            # بررسی دسترسی ادمین (مجوز رد رسید)
            user_service = UserService(session)
            user = await user_service.get_user_by_telegram_id(admin_id)
            perm_service = AdminPermissionService(session)
            if not user or not await perm_service.has_permission(user, "can_reject_receipt"):
                await callback.answer("⛔️ شما مجوز رد رسید را ندارید!", show_alert=True)
                return
            
            # ذخیره شناسه رسید در استیت
            await state.set_state(ReceiptAdminStates.AWAITING_REJECTION_REASON)
            await state.update_data(rejection_receipt_id=receipt_id)
            
            # درخواست دلیل رد از ادمین
            await callback.message.reply(
                "🔍 لطفاً دلیل رد رسید را وارد کنید:\n"
                "برای رد بدون ذکر دلیل، عبارت <code>-</code> را ارسال کنید."
            )
            
            await callback.answer()
            
        except ValueError:
            logger.error(f"خطا در تبدیل شناسه رسید: {callback.data}")
            await callback.answer("⚠️ خطا در شناسه رسید", show_alert=True)
        except Exception as e:
            logger.error(f"خطا در رد رسید: {e}", exc_info=True)
            await callback.answer("⚠️ خطا در پردازش درخواست", show_alert=True)
    
    @router.message(ReceiptAdminStates.AWAITING_REJECTION_REASON)
    async def process_rejection_reason(message: Message, state: FSMContext, session: AsyncSession) -> None:
        """
        پردازش دلیل رد رسید
        
        Args:
            message (Message): پیام تلگرام
            state (FSMContext): وضعیت FSM
            session (AsyncSession): نشست دیتابیس
        """
        try:
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
            
            # بررسی دسترسی ادمین
            user_service = UserService(session)
            user = await user_service.get_user_by_telegram_id(admin_id)
            
            if not user or user.role not in ["admin", "superadmin"]:
                await message.reply("⛔️ دسترسی غیرمجاز!")
                await state.clear()
                return
            
            # رد رسید
            receipt_service = ReceiptService(session)
            updated_receipt = await receipt_service.reject_receipt(receipt_id, admin_id, rejection_reason)
            
            if not updated_receipt:
                await message.reply("❌ خطا در رد رسید. لطفاً دوباره تلاش کنید.")
                logger.error(f"Failed to reject receipt {receipt_id} by admin {admin_id}")
                await state.clear()
                return
            
            # پاسخ به ادمین
            await message.reply(f"✅ رسید شماره {receipt_id} با موفقیت رد شد.")
            
            # آپدیت وضعیت در استیت
            await state.clear()
            logger.info(f"Receipt {receipt_id} rejected successfully by admin {admin_id}")
            
        except Exception as e:
            logger.error(f"Error in process_rejection_reason: {e}", exc_info=True)
            await message.reply("❌ خطای سیستمی رخ داد. لطفاً دوباره تلاش کنید.")
            await state.clear()
    
    @router.callback_query(F.data.startswith("admin:receipt:user_info:"))
    async def receipt_user_info(callback: CallbackQuery, session: AsyncSession) -> None:
        """
        نمایش اطلاعات کاربر ارسال‌کننده رسید
        
        Args:
            callback (CallbackQuery): کالبک تلگرام
            session (AsyncSession): نشست دیتابیس
        """
        try:
            # دریافت شناسه رسید
            receipt_id = int(callback.data.split(":")[3])
            
            # بررسی دسترسی ادمین
            user_service = UserService(session)
            admin = await user_service.get_user_by_telegram_id(callback.from_user.id)
            
            if not admin or admin.role not in ["admin", "superadmin"]:
                await callback.answer("⛔️ دسترسی غیرمجاز!", show_alert=True)
                return
            
            # دریافت اطلاعات رسید
            receipt_service = ReceiptService(session)
            receipt = await receipt_service.get_receipt_by_id(receipt_id)
            
            if not receipt:
                await callback.answer("❌ رسید مورد نظر یافت نشد.", show_alert=True)
                return
            
            # دریافت اطلاعات کاربر
            user = await user_service.get_user_by_id(receipt.user_id)
            
            if not user:
                await callback.answer("❌ اطلاعات کاربر یافت نشد.", show_alert=True)
                return
            
            # نمایش اطلاعات کاربر
            user_info = (
                f"👤 <b>اطلاعات کاربر #{user.id}</b>\n\n"
                f"📱 تلگرام آیدی: <code>{user.telegram_id}</code>\n"
                f"👤 نام: {user.full_name}\n"
                f"🔐 نقش: {user.role}\n"
                f"⏱ تاریخ عضویت: {user.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
            )
            
            # ساخت کیبورد بازگشت
            keyboard = InlineKeyboardBuilder()
            keyboard.button(
                text="🔙 بازگشت به رسید",
                callback_data=f"admin:receipt:manage:{receipt_id}"
            )
            
            await callback.message.edit_text(
                user_info,
                reply_markup=keyboard.as_markup(),
                parse_mode="HTML"
            )
            
        except ValueError:
            logger.error(f"خطا در تبدیل شناسه رسید: {callback.data}")
            await callback.answer("⚠️ خطا در شناسه رسید", show_alert=True)
        except Exception as e:
            logger.error(f"خطا در نمایش اطلاعات کاربر: {e}", exc_info=True)
            await callback.answer("⚠️ خطا در بارگذاری اطلاعات کاربر", show_alert=True)
    
    # فیلترهای مختلف رسیدها
    @router.callback_query(F.data == "admin:receipt:filter:pending")
    async def receipt_filter_pending(callback: CallbackQuery, session: AsyncSession) -> None:
        """نمایش رسیدهای در انتظار"""
        await callback.answer()
        await receipt_pending_list(callback, session, None)
    
    @router.callback_query(F.data == "admin:receipt:filter:approved")
    async def receipt_filter_approved(callback: CallbackQuery, session: AsyncSession) -> None:
        """نمایش رسیدهای تایید شده"""
        try:
            # بررسی دسترسی ادمین (مجوز مشاهده رسیدهای تاییدشده)
            user_service = UserService(session)
            user = await user_service.get_user_by_telegram_id(callback.from_user.id)
            perm_service = AdminPermissionService(session)
            if not user or not await perm_service.has_permission(user, "can_view_approved_receipts"):
                await callback.answer("⛔️ شما مجوز مشاهده لیست رسیدهای تاییدشده را ندارید!", show_alert=True)
                return
            
            # دریافت لیست رسیدهای تایید شده
            receipt_service = ReceiptService(session)
            approved_receipts = await receipt_service.get_receipts_by_status(ReceiptStatus.APPROVED, limit=10)
            
            # ساخت متن پیام
            if not approved_receipts:
                text = "📝 <b>هیچ رسید تایید شده‌ای وجود ندارد!</b>"
                await callback.message.edit_text(text, parse_mode="HTML")
                return
            
            text = f"✅ <b>رسیدهای تایید شده</b> ({len(approved_receipts)})\n\n"
            text += "لطفاً روی هر رسید کلیک کنید تا جزئیات آن را مشاهده کنید."
            
            # نمایش کیبورد رسیدها
            keyboard = get_receipt_list_keyboard(approved_receipts)
            
            await callback.message.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            
        except Exception as e:
            logger.error(f"خطا در نمایش لیست رسیدهای تایید شده: {e}", exc_info=True)
            await callback.answer("⚠️ خطا در بارگذاری لیست رسیدها", show_alert=True)
    
    @router.callback_query(F.data == "admin:receipt:filter:rejected")
    async def receipt_filter_rejected(callback: CallbackQuery, session: AsyncSession) -> None:
        """نمایش رسیدهای رد شده"""
        try:
            # بررسی دسترسی ادمین (مجوز مشاهده رسیدهای ردشده)
            user_service = UserService(session)
            user = await user_service.get_user_by_telegram_id(callback.from_user.id)
            perm_service = AdminPermissionService(session)
            if not user or not await perm_service.has_permission(user, "can_view_rejected_receipts"):
                await callback.answer("⛔️ شما مجوز مشاهده لیست رسیدهای ردشده را ندارید!", show_alert=True)
                return
            
            # دریافت لیست رسیدهای رد شده
            receipt_service = ReceiptService(session)
            rejected_receipts = await receipt_service.get_receipts_by_status(ReceiptStatus.REJECTED, limit=10)
            
            # ساخت متن پیام
            if not rejected_receipts:
                text = "📝 <b>هیچ رسید رد شده‌ای وجود ندارد!</b>"
                await callback.message.edit_text(text, parse_mode="HTML")
                return
            
            text = f"❌ <b>رسیدهای رد شده</b> ({len(rejected_receipts)})\n\n"
            text += "لطفاً روی هر رسید کلیک کنید تا جزئیات آن را مشاهده کنید."
            
            # نمایش کیبورد رسیدها
            keyboard = get_receipt_list_keyboard(rejected_receipts)
            
            await callback.message.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            
        except Exception as e:
            logger.error(f"خطا در نمایش لیست رسیدهای رد شده: {e}", exc_info=True)
            await callback.answer("⚠️ خطا در بارگذاری لیست رسیدها", show_alert=True)
    
    @router.callback_query(F.data == "admin:receipt:filter:all")
    async def receipt_filter_all(callback: CallbackQuery, session: AsyncSession) -> None:
        """نمایش همه رسیدها"""
        try:
            # بررسی دسترسی ادمین (مجوز مشاهده همه رسیدها)
            user_service = UserService(session)
            user = await user_service.get_user_by_telegram_id(callback.from_user.id)
            perm_service = AdminPermissionService(session)
            if not user or not await perm_service.has_permission(user, "can_view_all_receipts"):
                await callback.answer("⛔️ شما مجوز مشاهده همه رسیدها را ندارید!", show_alert=True)
                return
            
            # دریافت لیست همه رسیدها
            receipt_service = ReceiptService(session)
            all_receipts = await receipt_service.get_all_receipts(limit=10)
            
            # ساخت متن پیام
            if not all_receipts:
                text = "📝 <b>هیچ رسیدی وجود ندارد!</b>"
                await callback.message.edit_text(text, parse_mode="HTML")
                return
            
            text = f"📋 <b>همه رسیدها</b> ({len(all_receipts)})\n\n"
            text += "لطفاً روی هر رسید کلیک کنید تا جزئیات آن را مشاهده کنید."
            
            # نمایش کیبورد رسیدها
            keyboard = get_receipt_list_keyboard(all_receipts)
            
            await callback.message.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            
        except Exception as e:
            logger.error(f"خطا در نمایش لیست همه رسیدها: {e}", exc_info=True)
            await callback.answer("⚠️ خطا در بارگذاری لیست رسیدها", show_alert=True) 