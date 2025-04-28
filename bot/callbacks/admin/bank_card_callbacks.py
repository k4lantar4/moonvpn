"""
هندلرهای کالبک مدیریت کارت‌های بانکی برای ادمین
"""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from core.services.bank_card_service import BankCardService
from core.services.user_service import UserService
from db.models.bank_card import RotationPolicy
from bot.states.admin_states import BankCardStates
from bot.buttons.admin.bank_card_buttons import (
    get_bank_cards_keyboard, 
    get_bank_card_manage_buttons,
    get_bank_card_rotation_policy_keyboard,
    get_confirm_delete_bank_card_keyboard
)

logger = logging.getLogger(__name__)

def register_admin_bank_card_callbacks(router: Router) -> None:
    """ثبت کالبک‌های مدیریت کارت‌های بانکی برای ادمین"""
    
    @router.callback_query(F.data == "admin:bank_card:list")
    async def bank_card_list(callback: CallbackQuery, session: AsyncSession) -> None:
        """
        نمایش لیست کارت‌های بانکی
        
        Args:
            callback (CallbackQuery): کالبک تلگرام
            session (AsyncSession): نشست دیتابیس
        """
        try:
            # بررسی دسترسی ادمین
            user_service = UserService(session)
            user = await user_service.get_user_by_telegram_id(callback.from_user.id)
            
            if not user or user.role not in ["admin", "superadmin"]:
                await callback.answer("⛔️ دسترسی غیرمجاز!", show_alert=True)
                return
            
            # دریافت لیست کارت‌های بانکی
            bank_card_service = BankCardService(session)
            cards = await bank_card_service.get_all_cards()
            
            # ساخت متن پیام
            text = "💳 <b>مدیریت کارت‌های بانکی</b>\n\n"
            if not cards:
                text += "هیچ کارت بانکی ثبت نشده است."
            else:
                text += f"تعداد کارت‌ها: {len(cards)}\n\n"
                text += "لطفاً کارت مورد نظر را انتخاب کنید:"
            
            # نمایش کیبورد کارت‌ها
            keyboard = get_bank_cards_keyboard(cards)
            
            await callback.message.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            
        except Exception as e:
            logger.error(f"خطا در نمایش لیست کارت‌های بانکی: {e}", exc_info=True)
            await callback.answer("⚠️ خطا در بارگذاری لیست کارت‌ها", show_alert=True)
    
    @router.callback_query(F.data.startswith("admin:bank_card:manage:"))
    async def bank_card_manage(callback: CallbackQuery, session: AsyncSession) -> None:
        """
        نمایش منوی مدیریت برای یک کارت بانکی خاص
        
        Args:
            callback (CallbackQuery): کالبک تلگرام
            session (AsyncSession): نشست دیتابیس
        """
        try:
            # دریافت شناسه کارت بانکی
            card_id = int(callback.data.split(":")[3])
            
            # بررسی دسترسی ادمین
            user_service = UserService(session)
            user = await user_service.get_user_by_telegram_id(callback.from_user.id)
            
            if not user or user.role not in ["admin", "superadmin"]:
                await callback.answer("⛔️ دسترسی غیرمجاز!", show_alert=True)
                return
            
            # دریافت اطلاعات کارت بانکی
            bank_card_service = BankCardService(session)
            card = await bank_card_service.get_card_by_id(card_id)
            
            if not card:
                await callback.answer("❌ کارت بانکی مورد نظر یافت نشد.", show_alert=True)
                return
            
            # ساخت متن پیام
            rotation_text = "دستی" if card.rotation_policy == RotationPolicy.MANUAL else "زمانی" if card.rotation_policy == RotationPolicy.INTERVAL else "توزیع بار"
            status_text = "فعال" if card.is_active else "غیرفعال"
            status_emoji = "✅" if card.is_active else "❌"
            
            text = (
                f"💳 <b>کارت بانکی #{card.id}</b>\n\n"
                f"🔢 شماره کارت: <code>{card.card_number}</code>\n"
                f"👤 به نام: {card.holder_name}\n"
                f"🏦 بانک: {card.bank_name}\n"
                f"📊 وضعیت: {status_text} {status_emoji}\n"
                f"🔄 سیاست چرخش: {rotation_text}\n"
            )
            
            if card.rotation_policy == RotationPolicy.INTERVAL and card.rotation_interval_minutes:
                text += f"⏱ بازه چرخش: {card.rotation_interval_minutes} دقیقه\n"
            
            if card.telegram_channel_id:
                text += f"📢 کانال تلگرام: <code>{card.telegram_channel_id}</code>\n"
            
            text += f"🕒 تاریخ ثبت: {card.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            text += "🔧 عملیات کارت:"
            
            # نمایش کیبورد عملیات کارت بانکی
            keyboard = get_bank_card_manage_buttons(card.id)
            
            await callback.message.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            
        except ValueError:
            logger.error(f"خطا در تبدیل شناسه کارت بانکی: {callback.data}")
            await callback.answer("⚠️ خطا در شناسه کارت بانکی", show_alert=True)
        except Exception as e:
            logger.error(f"خطا در نمایش مدیریت کارت بانکی: {e}", exc_info=True)
            await callback.answer("⚠️ خطا در بارگذاری مدیریت کارت بانکی", show_alert=True)
    
    @router.callback_query(F.data == "admin:bank_card:add")
    async def bank_card_add_start(callback: CallbackQuery, state: FSMContext) -> None:
        """
        شروع فرآیند افزودن کارت بانکی جدید
        
        Args:
            callback (CallbackQuery): کالبک تلگرام
            state (FSMContext): وضعیت FSM
        """
        await callback.answer()
        
        try:
            # تنظیم وضعیت و درخواست ورود شماره کارت
            await state.set_state(BankCardStates.add_card_number)
            await callback.message.edit_text(
                "💳 <b>افزودن کارت بانکی جدید</b>\n\n"
                "لطفاً شماره کارت را بدون فاصله وارد کنید (16 رقم):",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"خطا در شروع فرآیند افزودن کارت بانکی: {e}", exc_info=True)
            await callback.answer("⚠️ خطا در شروع فرآیند افزودن کارت بانکی", show_alert=True)
    
    @router.message(BankCardStates.add_card_number)
    async def process_card_number(message: Message, state: FSMContext) -> None:
        """
        پردازش شماره کارت وارد شده
        
        Args:
            message (Message): پیام تلگرام
            state (FSMContext): وضعیت FSM
        """
        try:
            # بررسی صحت شماره کارت
            card_number = message.text.strip()
            
            if not card_number.isdigit() or len(card_number) != 16:
                await message.reply(
                    "❌ شماره کارت نامعتبر است. لطفاً یک شماره 16 رقمی بدون فاصله وارد کنید."
                )
                return
            
            # ذخیره شماره کارت در استیت
            await state.update_data(card_number=card_number)
            
            # درخواست نام صاحب کارت
            await state.set_state(BankCardStates.add_holder_name)
            await message.reply("👤 لطفاً نام و نام خانوادگی صاحب کارت را وارد کنید:")
            
        except Exception as e:
            logger.error(f"خطا در پردازش شماره کارت: {e}", exc_info=True)
            await message.reply("⚠️ خطای داخلی در پردازش شماره کارت. لطفاً دوباره تلاش کنید.")
            await state.clear()
    
    @router.message(BankCardStates.add_holder_name)
    async def process_holder_name(message: Message, state: FSMContext) -> None:
        """
        پردازش نام صاحب کارت وارد شده
        
        Args:
            message (Message): پیام تلگرام
            state (FSMContext): وضعیت FSM
        """
        try:
            # بررسی صحت نام صاحب کارت
            holder_name = message.text.strip()
            
            if len(holder_name) < 3 or len(holder_name) > 50:
                await message.reply(
                    "❌ نام وارد شده نامعتبر است. لطفاً نام و نام خانوادگی صحیح را وارد کنید."
                )
                return
            
            # ذخیره نام صاحب کارت در استیت
            await state.update_data(holder_name=holder_name)
            
            # درخواست نام بانک
            await state.set_state(BankCardStates.add_bank_name)
            await message.reply("🏦 لطفاً نام بانک را وارد کنید:")
            
        except Exception as e:
            logger.error(f"خطا در پردازش نام صاحب کارت: {e}", exc_info=True)
            await message.reply("⚠️ خطای داخلی در پردازش نام صاحب کارت. لطفاً دوباره تلاش کنید.")
            await state.clear()
    
    @router.message(BankCardStates.add_bank_name)
    async def process_bank_name(message: Message, state: FSMContext) -> None:
        """
        پردازش نام بانک وارد شده
        
        Args:
            message (Message): پیام تلگرام
            state (FSMContext): وضعیت FSM
        """
        try:
            # بررسی صحت نام بانک
            bank_name = message.text.strip()
            
            if len(bank_name) < 2 or len(bank_name) > 30:
                await message.reply(
                    "❌ نام بانک نامعتبر است. لطفاً نام بانک صحیح را وارد کنید."
                )
                return
            
            # ذخیره نام بانک در استیت
            await state.update_data(bank_name=bank_name)
            
            # درخواست انتخاب سیاست چرخش
            await state.set_state(BankCardStates.add_rotation_policy)
            
            # ساخت کیبورد انتخاب سیاست چرخش
            keyboard = get_bank_card_rotation_policy_keyboard()
            
            await message.reply(
                "🔄 لطفاً سیاست چرخش کارت را انتخاب کنید:",
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"خطا در پردازش نام بانک: {e}", exc_info=True)
            await message.reply("⚠️ خطای داخلی در پردازش نام بانک. لطفاً دوباره تلاش کنید.")
            await state.clear()
    
    @router.callback_query(F.data.startswith("admin:bank_card:policy:"))
    async def process_rotation_policy(callback: CallbackQuery, state: FSMContext) -> None:
        """
        پردازش سیاست چرخش انتخاب شده
        
        Args:
            callback (CallbackQuery): کالبک تلگرام
            state (FSMContext): وضعیت FSM
        """
        await callback.answer()
        
        try:
            # دریافت سیاست چرخش
            policy_value = callback.data.split(":")[-1]
            policy = RotationPolicy(policy_value)
            
            # ذخیره سیاست چرخش در استیت
            await state.update_data(rotation_policy=policy_value)
            
            # اگر سیاست چرخش زمانی است، درخواست بازه زمانی
            if policy == RotationPolicy.INTERVAL:
                await state.set_state(BankCardStates.add_rotation_interval)
                await callback.message.edit_text(
                    "⏱ لطفاً بازه زمانی چرخش را به دقیقه وارد کنید (عدد):"
                )
            else:
                # در غیر این صورت، به مرحله تایید نهایی برو
                await show_bank_card_confirmation(callback.message, state)
            
        except ValueError:
            logger.error(f"خطا در پردازش سیاست چرخش: {callback.data}")
            await callback.message.edit_text(
                "❌ سیاست چرخش نامعتبر است. لطفاً دوباره تلاش کنید."
            )
            await state.clear()
        except Exception as e:
            logger.error(f"خطا در پردازش سیاست چرخش: {e}", exc_info=True)
            await callback.message.edit_text(
                "⚠️ خطای داخلی در پردازش سیاست چرخش. لطفاً دوباره تلاش کنید."
            )
            await state.clear()
    
    @router.message(BankCardStates.add_rotation_interval)
    async def process_rotation_interval(message: Message, state: FSMContext) -> None:
        """
        پردازش بازه زمانی چرخش وارد شده
        
        Args:
            message (Message): پیام تلگرام
            state (FSMContext): وضعیت FSM
        """
        try:
            # بررسی صحت بازه زمانی
            try:
                interval = int(message.text.strip())
                if interval <= 0:
                    raise ValueError("بازه زمانی باید مثبت باشد")
            except ValueError:
                await message.reply(
                    "❌ بازه زمانی نامعتبر است. لطفاً یک عدد مثبت وارد کنید."
                )
                return
            
            # ذخیره بازه زمانی در استیت
            await state.update_data(rotation_interval=interval)
            
            # نمایش تایید نهایی
            await show_bank_card_confirmation(message, state)
            
        except Exception as e:
            logger.error(f"خطا در پردازش بازه زمانی چرخش: {e}", exc_info=True)
            await message.reply("⚠️ خطای داخلی در پردازش بازه زمانی چرخش. لطفاً دوباره تلاش کنید.")
            await state.clear()
    
    async def show_bank_card_confirmation(message: Message, state: FSMContext) -> None:
        """
        نمایش اطلاعات وارد شده برای تایید نهایی
        
        Args:
            message (Message): پیام تلگرام
            state (FSMContext): وضعیت FSM
        """
        try:
            # دریافت داده‌های استیت
            data = await state.get_data()
            
            # اطلاعات کارت
            card_number = data.get("card_number")
            holder_name = data.get("holder_name")
            bank_name = data.get("bank_name")
            rotation_policy_value = data.get("rotation_policy")
            rotation_interval = data.get("rotation_interval")
            
            # تبدیل سیاست چرخش به متن
            policy_text = ""
            if rotation_policy_value == RotationPolicy.MANUAL.value:
                policy_text = "دستی"
            elif rotation_policy_value == RotationPolicy.INTERVAL.value:
                policy_text = f"زمانی (هر {rotation_interval} دقیقه)"
            elif rotation_policy_value == RotationPolicy.LOAD_BALANCE.value:
                policy_text = "توزیع بار"
            
            # ساخت متن تایید
            confirmation_text = (
                "✅ <b>تایید اطلاعات کارت</b>\n\n"
                f"🔢 شماره کارت: <code>{card_number}</code>\n"
                f"👤 به نام: {holder_name}\n"
                f"🏦 بانک: {bank_name}\n"
                f"🔄 سیاست چرخش: {policy_text}\n\n"
                "آیا اطلاعات فوق صحیح است؟"
            )
            
            # ساخت کیبورد تایید
            keyboard = InlineKeyboardBuilder()
            keyboard.button(text="✅ تایید و ذخیره", callback_data="admin:bank_card:confirm")
            keyboard.button(text="❌ انصراف", callback_data="admin:bank_card:add:cancel")
            keyboard.adjust(1)
            
            # تنظیم وضعیت
            await state.set_state(BankCardStates.add_confirmation)
            
            # ارسال پیام
            reply_method = message.edit_text if hasattr(message, 'edit_text') else message.reply
            await reply_method(
                confirmation_text,
                reply_markup=keyboard.as_markup(),
                parse_mode="HTML"
            )
            
        except Exception as e:
            logger.error(f"خطا در نمایش تایید کارت بانکی: {e}", exc_info=True)
            reply_method = message.edit_text if hasattr(message, 'edit_text') else message.reply
            await reply_method("⚠️ خطای داخلی در نمایش اطلاعات کارت. لطفاً دوباره تلاش کنید.")
            await state.clear()
            
    @router.callback_query(F.data == "admin:bank_card:confirm")
    async def confirm_bank_card(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
        """
        تایید و ذخیره کارت بانکی جدید
        
        Args:
            callback (CallbackQuery): کالبک تلگرام
            state (FSMContext): وضعیت FSM
            session (AsyncSession): نشست دیتابیس
        """
        await callback.answer()
        
        try:
            # دریافت داده‌های استیت
            data = await state.get_data()
            
            # اطلاعات کارت
            card_number = data.get("card_number")
            holder_name = data.get("holder_name")
            bank_name = data.get("bank_name")
            rotation_policy_value = data.get("rotation_policy")
            rotation_interval = data.get("rotation_interval")
            
            # تبدیل سیاست چرخش
            rotation_policy = RotationPolicy(rotation_policy_value)
            
            # دریافت شناسه ادمین
            user_service = UserService(session)
            user = await user_service.get_user_by_telegram_id(callback.from_user.id)
            
            if not user or user.role not in ["admin", "superadmin"]:
                await callback.message.edit_text("⛔️ دسترسی غیرمجاز!")
                await state.clear()
                return
            
            # ثبت کارت بانکی
            bank_card_service = BankCardService(session)
            new_card = await bank_card_service.create_card(
                card_number=card_number,
                holder_name=holder_name,
                bank_name=bank_name,
                rotation_policy=rotation_policy,
                admin_user_id=user.id,
                rotation_interval_minutes=rotation_interval if rotation_policy == RotationPolicy.INTERVAL else None
            )
            
            if not new_card:
                await callback.message.edit_text("❌ خطا در ثبت کارت بانکی. لطفاً دوباره تلاش کنید.")
                await state.clear()
                return
            
            # پاسخ موفقیت
            await callback.message.edit_text(
                f"✅ کارت بانکی با موفقیت ثبت شد!\n\n"
                f"🆔 شناسه: {new_card.id}\n"
                f"🔢 شماره کارت: <code>{new_card.card_number}</code>\n"
                f"👤 به نام: {new_card.holder_name}\n"
                f"🏦 بانک: {new_card.bank_name}\n\n"
                f"برای مدیریت کارت‌های بانکی روی دکمه زیر کلیک کنید:",
                reply_markup=InlineKeyboardBuilder().button(
                    text="🔙 بازگشت به لیست کارت‌ها",
                    callback_data="admin:bank_card:list"
                ).as_markup(),
                parse_mode="HTML"
            )
            
            # پاک کردن وضعیت
            await state.clear()
            
            logger.info(f"Bank card {new_card.id} created successfully by admin {user.id}")
            
        except Exception as e:
            logger.error(f"خطا در تایید و ذخیره کارت بانکی: {e}", exc_info=True)
            await callback.message.edit_text("⚠️ خطای داخلی در ثبت کارت بانکی. لطفاً دوباره تلاش کنید.")
            await state.clear()
    
    @router.callback_query(F.data == "admin:bank_card:add:cancel")
    async def cancel_add_bank_card(callback: CallbackQuery, state: FSMContext) -> None:
        """
        لغو فرآیند افزودن کارت بانکی
        
        Args:
            callback (CallbackQuery): کالبک تلگرام
            state (FSMContext): وضعیت FSM
        """
        await callback.answer()
        
        try:
            # پاک کردن وضعیت
            await state.clear()
            
            # بازگشت به لیست کارت‌های بانکی
            await callback.message.edit_text(
                "❌ افزودن کارت بانکی لغو شد.\n\n"
                "برای بازگشت به لیست کارت‌های بانکی روی دکمه زیر کلیک کنید:",
                reply_markup=InlineKeyboardBuilder().button(
                    text="🔙 بازگشت به لیست کارت‌ها",
                    callback_data="admin:bank_card:list"
                ).as_markup()
            )
            
        except Exception as e:
            logger.error(f"خطا در لغو افزودن کارت بانکی: {e}", exc_info=True)
            await callback.message.edit_text("⚠️ خطای داخلی. لطفاً دوباره تلاش کنید.")
            await state.clear()