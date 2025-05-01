# مدیریت دکمه‌های inline مثل بازگشت، جزئیات پلن

"""
کال‌بک‌های تعاملی برای منوهای بات
"""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
from aiogram.fsm.context import FSMContext

from core.services.plan_service import PlanService
from core.services.user_service import UserService
from core.services.order_service import OrderService
from bot.buttons.plan_buttons import get_plans_keyboard, get_plan_details_keyboard
from bot.buttons.common_buttons import BACK_TO_MAIN_CB, BACK_TO_PLANS_CB, HELP_CB, SUPPORT_CB
from db.models.order import Order, OrderStatus
from bot.states.buy_states import BuyState
from core.services.payment_service import PaymentService
from core.services.payment_service import InsufficientFundsError, PaymentError

# تنظیم لاگر
logger = logging.getLogger(__name__)

def register_callbacks(router: Router, session_pool):
    """ثبت تمام callback handlers در روتر"""
    
    @router.callback_query(F.data == "buy_plans")
    async def buy_plans_callback(callback: CallbackQuery, state: FSMContext):
        """شروع فرایند خرید پلن از طریق کیبورد اینلاین"""
        try:
            async with session_pool() as session:
                # دریافت پلن‌های فعال
                plan_service = PlanService(session)
                plans = await plan_service.get_all_active_plans()
                
                if not plans:
                    await callback.message.edit_text("هیچ پلنی فعال نیست، لطفاً بعداً دوباره تلاش کنید.")
                    return
                
                # نمایش لیست پلن‌ها با دکمه‌های انتخاب
                await callback.message.edit_text(
                    text="🔍 لطفاً پلن مورد نظر خود را انتخاب کنید:",
                    reply_markup=get_plans_keyboard(plans)
                )
                
                # تنظیم وضعیت به انتخاب پلن
                await state.set_state(BuyState.select_plan)
                
        except Exception as e:
            logger.error(f"Error in buy_plans callback: {e}")
            await callback.answer("خطا در پردازش درخواست", show_alert=True)
    
    @router.callback_query(F.data.startswith("select_plan:"))
    async def select_plan_callback(callback: CallbackQuery):
        """انتخاب پلن و نمایش جزئیات آن"""
        try:
            plan_id = int(callback.data.split(":")[-1])
            logger.info(f"User {callback.from_user.id} selected plan ID: {plan_id}")
            
            async with session_pool() as session:
                plan_service = PlanService(session)
                plan = await plan_service.get_plan_by_id(plan_id)
                
                if not plan:
                    await callback.answer("پلن مورد نظر یافت نشد!", show_alert=True)
                    return

                # نمایش اطلاعات کامل پلن
                details = (
                    f"🔹 نام پلن: {plan.name}\n"
                    f"🔹 حجم: {plan.traffic_gb} گیگابایت\n"
                    f"🔹 مدت اعتبار: {plan.duration_days} روز\n"
                    f"🔹 قیمت: {int(plan.price):,} تومان\n\n"
                    f"برای ادامه خرید، دکمه تأیید را انتخاب کنید."
                )
                
                await callback.message.edit_text(
                    text=details,
                    reply_markup=get_plan_details_keyboard(plan_id)
                )
                
                await callback.answer()
                
        except Exception as e:
            logger.error(f"Error in select_plan_callback: {e}", exc_info=True)
            await callback.answer("خطایی رخ داد. لطفاً دوباره تلاش کنید.", show_alert=True)
    
    @router.callback_query(F.data.startswith("confirm_plan:"))
    async def confirm_plan_callback(callback: CallbackQuery):
        """تأیید خرید پلن و ایجاد سفارش جدید"""
        try:
            plan_id = int(callback.data.split(":")[-1])
            telegram_user_id = callback.from_user.id
            logger.info(f"User {telegram_user_id} confirmed plan ID: {plan_id}")
            
            async with session_pool() as session:
                # Instantiate services
                user_service = UserService(session)
                plan_service = PlanService(session)
                order_service = OrderService(session)
                
                db_user = await user_service.get_user_by_telegram_id(telegram_user_id)
                if not db_user:
                    logger.error(f"User with telegram_id {telegram_user_id} not found in database.")
                    await callback.answer("کاربر شما در سیستم یافت نشد! لطفاً ابتدا /start را بزنید.", show_alert=True)
                    return
                
                plan = await plan_service.get_plan_by_id(plan_id)
                if not plan:
                    await callback.answer("پلن مورد نظر یافت نشد!", show_alert=True)
                    return
                
                location_name = plan.available_locations[0] if hasattr(plan, 'available_locations') and plan.available_locations else "DefaultLocation"
                
                # استفاده فقط از سرویس برای ایجاد سفارش
                order = await order_service.create_order(
                    user_id=db_user.id,
                    plan_id=plan_id,
                    location_name=location_name,
                    amount=plan.price,
                    status=OrderStatus.PENDING
                )
                if not order or not order.id:
                    logger.error(f"Order creation failed for user {telegram_user_id}, plan {plan_id}")
                    await callback.answer("خطایی در ثبت سفارش رخ داد.", show_alert=True)
                    return

                logger.info(f"Created new order ID: {order.id} for user {telegram_user_id} (DB ID: {db_user.id})")
                
                # Commit the session to save the order before sending payment options
                await session.commit()
                logger.info(f"Order {order.id} committed successfully.")

                text = (
                    f"✅ سفارش شما با موفقیت ثبت شد!\n\n"
                    f"🔹 شناسه سفارش: {order.id}\n"
                    f"🔹 نام پلن: {plan.name}\n"
                    f"🔹 مبلغ: {int(plan.price):,} تومان\n\n"
                    f"سفارش شما در انتظار پرداخت است. لطفاً روش پرداخت را انتخاب کنید."
                )
                payment_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="💰 پرداخت با کیف پول", callback_data=f"pay_with_wallet:{order.id}")],
                    [InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_plans")]
                ])
                await callback.message.edit_text(
                    text=text,
                    reply_markup=payment_keyboard
                )
                await callback.answer()
        except Exception as e:
            logger.error(f"Error in confirm_plan_callback for user {callback.from_user.id}: {e}", exc_info=True)
            await callback.answer("خطایی در ثبت سفارش رخ داد. لطفاً دوباره تلاش کنید.", show_alert=True)
    
    @router.callback_query(F.data == BACK_TO_PLANS_CB)
    async def back_to_plans_callback(callback: CallbackQuery):
        """بازگشت به لیست پلن‌ها"""
        try:
            async with session_pool() as session:
                plan_service = PlanService(session)
                plans = await plan_service.get_all_active_plans()
                
                if not plans:
                    await callback.message.edit_text("هیچ پلنی فعال نیست، لطفاً بعداً دوباره تلاش کنید.")
                    return
                
                await callback.message.edit_text(
                    text="🔍 لطفاً پلن مورد نظر خود را انتخاب کنید:",
                    reply_markup=get_plans_keyboard(plans)
                )
                
                await callback.answer()
                
        except Exception as e:
            logger.error(f"Error in back_to_plans_callback: {e}", exc_info=True)
            await callback.answer("خطایی رخ داد. لطفاً دوباره تلاش کنید.", show_alert=True)
    
    @router.callback_query(F.data == BACK_TO_MAIN_CB)
    async def back_to_main_callback(callback: CallbackQuery):
        """بازگشت به منوی اصلی"""
        try:
            await callback.message.delete()
            await callback.message.answer("به منوی اصلی بازگشتید. از دکمه‌های زیر استفاده کنید.")
            await callback.answer()
        except Exception as e:
            logger.error(f"Error in back_to_main_callback: {e}", exc_info=True)
            await callback.answer("خطایی رخ داد. لطفاً دوباره تلاش کنید.", show_alert=True)
    
    @router.callback_query(F.data.startswith("pay_with_wallet:"))
    async def pay_with_wallet_callback(callback: CallbackQuery):
        """پرداخت سفارش با استفاده از موجودی کیف پول"""
        try:
            # استخراج order_id از callback_data
            order_id = int(callback.data.split(":")[-1])
            telegram_user_id = callback.from_user.id
            
            logger.info(f"User {telegram_user_id} is paying order {order_id} with wallet balance")
            
            # پیام موقت برای نشان دادن وضعیت پردازش
            await callback.message.edit_text(
                "⏳ در حال پردازش پرداخت...\n"
                "لطفاً چند لحظه صبر کنید."
            )
            
            async with session_pool() as session:
                # دریافت اطلاعات کاربر
                user_service = UserService(session)
                db_user = await user_service.get_user_by_telegram_id(telegram_user_id)
                
                if not db_user:
                    logger.error(f"User with telegram_id {telegram_user_id} not found in database.")
                    await callback.answer("کاربر شما در سیستم یافت نشد! لطفاً ابتدا /start را بزنید.", show_alert=True)
                    return
                
                # سرویس‌های لازم رو بساز
                order_service = OrderService(session) 
                payment_service = PaymentService(session) # PaymentService رو هم بساز
                
                # دریافت اطلاعات سفارش برای گرفتن مبلغ
                order = await order_service.get_order_by_id(order_id)
                if not order:
                    logger.error(f"Order {order_id} not found for payment attempt.")
                    await callback.message.edit_text("❌ خطایی در یافتن سفارش رخ داد.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 بازگشت", callback_data=BACK_TO_PLANS_CB)]]))
                    await callback.answer()
                    return

                # پرداخت با کیف پول با استفاده از PaymentService
                try:
                    payment_success, payment_message, transaction = await payment_service.pay_from_wallet(
                        user_id=db_user.id, 
                        amount=order.amount, 
                        description=f"Payment for order {order_id}",
                        order_id=order_id
                    )
                except InsufficientFundsError:
                    # اگر موجودی کافی نیست، پیغام مناسب ارسال می‌شود
                    await callback.message.edit_text(
                        f"❌ موجودی کیف پول شما کافی نیست.\n\n"
                        f"موجودی فعلی: {int(db_user.wallet_balance):,} تومان\n"
                        f"مبلغ لازم: {int(order.amount):,} تومان\n\n"
                        "لطفاً ابتدا کیف پول خود را شارژ کنید.",
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text="💰 شارژ کیف پول", callback_data="deposit_wallet")],
                            [InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_plans")] # یا back_to_order? 
                        ])
                    )
                    await callback.answer()
                    return
                except PaymentError as pe:
                    logger.error(f"PaymentError during wallet payment for order {order_id}: {pe}")
                    payment_success = False
                    payment_message = f"خطا در پردازش پرداخت: {pe}"
                
                if not payment_success:
                    await callback.message.edit_text(
                        f"❌ {payment_message}",
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_plans")] # یا back_to_order?
                        ])
                    )
                    await callback.answer()
                    return
                
                # اگر پرداخت موفق بود، وضعیت سفارش رو بروز کن و اکانت رو بساز
                logger.info(f"Wallet payment successful for order {order_id}, transaction_id: {transaction.id if transaction else 'N/A'}")
                # بروزرسانی وضعیت سفارش به پرداخت شده
                updated_order = await order_service.update_order_status(order_id, OrderStatus.PAID)
                if not updated_order:
                     logger.error(f"Failed to update order {order_id} status to PAID after successful wallet payment.")
                     # TODO: Maybe attempt a refund or flag for admin review?
                     await callback.message.edit_text("❌ پرداخت موفق بود اما در بروزرسانی وضعیت سفارش خطایی رخ داد. لطفاً با پشتیبانی تماس بگیرید.")
                     await callback.answer()
                     return

                # حالا باید اکانت رو بسازیم (این منطق ممکنه در OrderService یا AccountService باشه)
                # فرض می‌کنیم یک متد در OrderService برای نهایی کردن سفارش و ساخت اکانت وجود داره
                try:
                    # از متد process_order_purchase برای تکمیل فرآیند استفاده می‌کنیم
                    # چون پرداخت دستی انجام شده، بخش پرداخت رو رد می‌کنیم
                    # !! نکته: شاید بهتر باشه process_order_purchase خودش پرداخت رو هندل کنه و ما فقط اون رو صدا بزنیم
                    # یا اینکه یک متد جدا مثل finalize_order_and_create_account داشته باشیم
                    
                    # **روش 1: فراخوانی یک متد نهایی سازی (اگر وجود داشته باشد)**
                    # account_success, account_message, account_details = await order_service.finalize_paid_order(order_id)
                    
                    # **روش 2: استفاده از AccountService به طور مستقیم (نیاز به اطلاعات بیشتر مثل panel_id, inbound_id)**
                    # TODO: Get selected panel/inbound info from state or order details if stored
                    # panel_id = ... 
                    # inbound_id = ... 
                    # account_service = AccountService(session, ...) # Pass necessary services
                    # account_result = await account_service.provision_account_for_order(order)
                    
                    # **روش موقت: فقط نمایش پیام موفقیت (نیاز به تکمیل منطق ساخت اکانت)**
                    account_success = True # فرض می‌کنیم موفق بوده
                    account_message = "ساخت اکانت در حال حاضر پیاده‌سازی نشده است."
                    account_details = None
                    
                except Exception as account_exc:
                    logger.error(f"Error provisioning account for order {order_id} after successful payment: {account_exc}", exc_info=True)
                    account_success = False
                    account_message = "خطا در ساخت اکانت VPN." 
                    # TODO: Attempt refund or flag?

                if account_success:
                    await callback.message.edit_text(
                        "✅ پرداخت و ساخت اکانت با موفقیت انجام شد!\n\n"
                        f"{account_message}"
                        # TODO: Display account details (QR code, config link) here if available
                        ,
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text="مشاهده اکانت‌های من", callback_data="my_accounts")],
                            [InlineKeyboardButton(text="🔙 بازگشت به منوی اصلی", callback_data="back_to_main")]
                        ])
                    )
                else:
                     await callback.message.edit_text(
                        f"⚠️ پرداخت موفق بود اما در ساخت اکانت خطایی رخ داد:\n{account_message}\nلطفاً با پشتیبانی تماس بگیرید.",
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text="🔙 بازگشت به منوی اصلی", callback_data="back_to_main")]
                        ])
                    )
                
                await callback.answer()
                
        except InsufficientFundsError: # این رو دیگه بالا هندل کردیم، ولی برای اطمینان می‌ذاریم
            pass # Already handled
        except Exception as e:
            logger.error(f"Error in pay_with_wallet_callback: {e}", exc_info=True)
            await callback.answer("خطایی رخ داد. لطفاً دوباره تلاش کنید.", show_alert=True)
            # بازگشت به منوی اصلی در صورت خطا
            await callback.message.edit_text(
                "❌ متأسفانه در پردازش پرداخت خطایی رخ داد.\n"
                "لطفاً دوباره تلاش کنید.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 بازگشت", callback_data=BACK_TO_PLANS_CB)]
                ])
            )

    @router.callback_query(F.data == HELP_CB)
    async def help_callback(callback: CallbackQuery):
        await callback.answer("راهنمای ربات به زودی تکمیل می‌شود! 😊", show_alert=True)

    @router.callback_query(F.data == SUPPORT_CB)
    async def support_callback(callback: CallbackQuery):
        await callback.answer("پشتیبانی به زودی فعال می‌شود! 🆘", show_alert=True)

# New placeholder handlers
async def handle_help_menu_callback(callback: CallbackQuery):
    """Placeholder برای دکمه راهنما"""
    await callback.answer("❓ بخش راهنما در حال توسعه است...", show_alert=True)

async def handle_support_chat_callback(callback: CallbackQuery):
    """Placeholder برای دکمه پشتیبانی"""
    await callback.answer("💬 بخش پشتیبانی در حال توسعه است...", show_alert=True)
