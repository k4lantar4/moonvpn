"""
کال‌بک‌های مربوط به فرایند خرید و دریافت کانفیگ
"""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.orm import Session
from datetime import datetime

from core.services.panel_service import PanelService
from core.services.plan_service import PlanService
from core.services.account_service import AccountService
from core.services.user_service import UserService
from core.services.order_service import OrderService
from db.models.order import Order, OrderStatus

from bot.buttons.buy_buttons import get_locations_keyboard, get_inbounds_keyboard, get_confirm_purchase_keyboard
from bot.buttons.plan_buttons import get_plans_keyboard

# تنظیم لاگر
logger = logging.getLogger(__name__)

def register_buy_callbacks(router: Router, session_pool):
    """ثبت callback handler های مربوط به فرایند خرید"""
    
    @router.callback_query(F.data.startswith("select_location:"))
    async def select_location_callback(callback: CallbackQuery):
        """انتخاب لوکیشن سرور"""
        session = None
        try:
            panel_id = int(callback.data.split(":")[-1])
            # ذخیره plan_id در متادیتا (اگر وجود داشته باشد)
            plan_id = None
            
            # استخراج شناسه پلن از پیام قبلی اگر وجود داشته باشد
            if hasattr(callback, "message") and callback.message and callback.message.reply_markup:
                for row in callback.message.reply_markup.inline_keyboard:
                    for button in row:
                        if button.callback_data.startswith("back_to_inbounds:"):
                            plan_id = int(button.callback_data.split(":")[-1])
                            break
            
            if not plan_id:
                await callback.answer("خطا: شناسه پلن یافت نشد!", show_alert=True)
                return
                
            logger.info(f"User {callback.from_user.id} selected location (panel ID): {panel_id} for plan {plan_id}")
            
            session = session_pool()
            panel_service = PanelService(session)
            panel = panel_service.get_panel_by_id(panel_id)
            
            if not panel:
                await callback.answer("لوکیشن مورد نظر یافت نشد!", show_alert=True)
                return
                
            # دریافت لیست inbound های این پنل
            inbounds = session.query(panel_service.get_inbounds_by_panel(panel_id)).all()
            
            if not inbounds:
                await callback.answer("هیچ سرویسی در این لوکیشن فعال نیست!", show_alert=True)
                return
                
            await callback.message.edit_text(
                text=f"🌐 لوکیشن انتخابی: {panel.flag_emoji} {panel.location}\n\n"
                     f"لطفاً نوع پروتکل مورد نظر خود را انتخاب کنید:",
                reply_markup=get_inbounds_keyboard(inbounds, plan_id)
            )
            
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error in select_location_callback: {e}", exc_info=True)
            await callback.answer("خطایی رخ داد. لطفاً دوباره تلاش کنید.", show_alert=True)
        finally:
            if session:
                session.close()
                logger.debug("Database session closed in select_location_callback")
    
    @router.callback_query(F.data.startswith("select_inbound:"))
    async def select_inbound_callback(callback: CallbackQuery):
        """انتخاب inbound (پروتکل)"""
        session = None
        try:
            # استخراج plan_id و inbound_id از callback_data
            parts = callback.data.split(":")
            plan_id = int(parts[1])
            inbound_id = int(parts[2])
            
            logger.info(f"User {callback.from_user.id} selected inbound ID: {inbound_id} for plan {plan_id}")
            
            session = session_pool()
            plan_service = PlanService(session)
            plan = plan_service.get_plan_by_id(plan_id)
            
            if not plan:
                await callback.answer("پلن مورد نظر یافت نشد!", show_alert=True)
                return
                
            # سرویس پنل برای دریافت اطلاعات inbound
            panel_service = PanelService(session)
            inbound = panel_service.get_inbound_by_id(inbound_id)
            
            if not inbound:
                await callback.answer("سرویس مورد نظر یافت نشد!", show_alert=True)
                return
                
            # دریافت اطلاعات پنل برای نمایش لوکیشن
            panel = panel_service.get_panel_by_id(inbound.panel_id)
            
            # نمایش خلاصه سفارش و درخواست تأیید نهایی
            summary = (
                f"📝 خلاصه سفارش:\n\n"
                f"🔹 پلن: {plan.name}\n"
                f"🔹 حجم: {plan.traffic} گیگابایت\n"
                f"🔹 مدت: {plan.duration_days} روز\n"
                f"🔹 لوکیشن: {panel.flag_emoji} {panel.location}\n"
                f"🔹 پروتکل: {inbound.protocol.upper()}\n"
                f"🔹 قیمت: {int(plan.price):,} تومان\n\n"
                f"آیا از خرید اطمینان دارید؟"
            )
            
            await callback.message.edit_text(
                text=summary,
                reply_markup=get_confirm_purchase_keyboard(plan_id, inbound_id)
            )
            
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error in select_inbound_callback: {e}", exc_info=True)
            await callback.answer("خطایی رخ داد. لطفاً دوباره تلاش کنید.", show_alert=True)
        finally:
            if session:
                session.close()
                logger.debug("Database session closed in select_inbound_callback")
    
    @router.callback_query(F.data.startswith("confirm_purchase:"))
    async def confirm_purchase_callback(callback: CallbackQuery):
        """تأیید نهایی خرید و ایجاد اکانت"""
        session = None
        try:
            # استخراج plan_id و inbound_id از callback_data
            parts = callback.data.split(":")
            plan_id = int(parts[1])
            inbound_id = int(parts[2])
            telegram_user_id = callback.from_user.id
            
            logger.info(f"User {telegram_user_id} confirmed purchase of plan {plan_id} with inbound {inbound_id}")
            
            # پیام موقت برای نشان دادن وضعیت پردازش
            process_message = await callback.message.edit_text(
                "⏳ در حال ثبت سفارش شما...\n"
                "لطفاً چند لحظه صبر کنید."
            )
            
            session = session_pool()
            
            # دریافت اطلاعات کاربر
            user_service = UserService(session)
            db_user = user_service.get_user_by_telegram_id(telegram_user_id)
            
            if not db_user:
                logger.error(f"User with telegram_id {telegram_user_id} not found in database.")
                await callback.answer("کاربر شما در سیستم یافت نشد! لطفاً ابتدا /start را بزنید.", show_alert=True)
                return
            
            # دریافت اطلاعات پلن
            plan_service = PlanService(session)
            plan = plan_service.get_plan_by_id(plan_id)
            
            if not plan:
                await callback.answer("پلن مورد نظر یافت نشد!", show_alert=True)
                return
            
            # ایجاد سفارش جدید
            new_order = Order(
                user_id=db_user.id,
                plan_id=plan_id,
                amount=plan.price,
                status=OrderStatus.PENDING,
                created_at=datetime.utcnow()
            )
            
            session.add(new_order)
            session.commit()
            logger.info(f"Created new order ID: {new_order.id} for user {telegram_user_id} (DB ID: {db_user.id})")
            
            # نمایش پیام موفقیت‌آمیز ثبت سفارش با گزینه‌های پرداخت
            order_created_message = (
                f"✅ سفارش شما با موفقیت ثبت شد!\n\n"
                f"🔹 شناسه سفارش: {new_order.id}\n"
                f"🔹 نام پلن: {plan.name}\n"
                f"🔹 مبلغ: {int(plan.price):,} تومان\n\n"
                f"سفارش شما در انتظار پرداخت است. لطفاً روش پرداخت را انتخاب کنید."
            )
            
            # ایجاد دکمه‌های پرداخت
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            payment_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💰 پرداخت با کیف پول", callback_data=f"pay_with_balance:{new_order.id}:{inbound_id}")],
                [InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_plans")]
            ])
            
            await process_message.edit_text(
                order_created_message,
                reply_markup=payment_keyboard
            )
            
        except Exception as e:
            logger.error(f"Error in confirm_purchase_callback: {e}", exc_info=True)
            await callback.answer("خطایی رخ داد. لطفاً دوباره تلاش کنید.", show_alert=True)
        finally:
            if session:
                session.close()
                logger.debug("Database session closed in confirm_purchase_callback")
    
    @router.callback_query(F.data.startswith("pay_with_balance:"))
    async def pay_with_balance_callback(callback: CallbackQuery):
        """پرداخت سفارش با استفاده از موجودی کیف پول"""
        session = None
        try:
            # استخراج order_id و inbound_id از callback_data
            parts = callback.data.split(":")
            order_id = int(parts[1])
            inbound_id = int(parts[2])
            telegram_user_id = callback.from_user.id
            
            logger.info(f"User {telegram_user_id} is paying order {order_id} with wallet balance")
            
            # پیام موقت برای نشان دادن وضعیت پردازش
            process_message = await callback.message.edit_text(
                "⏳ در حال پردازش پرداخت...\n"
                "لطفاً چند لحظه صبر کنید."
            )
            
            session = session_pool()
            
            # دریافت اطلاعات کاربر
            user_service = UserService(session)
            db_user = user_service.get_user_by_telegram_id(telegram_user_id)
            
            if not db_user:
                logger.error(f"User with telegram_id {telegram_user_id} not found in database.")
                await callback.answer("کاربر شما در سیستم یافت نشد! لطفاً ابتدا /start را بزنید.", show_alert=True)
                return
            
            # پرداخت با کیف پول
            order_service = OrderService(session)
            success, message = order_service.pay_with_balance(order_id)
            
            if not success:
                # دریافت اطلاعات سفارش برای نمایش مبلغ مورد نیاز
                order = order_service.get_order_by_id(order_id)
                
                # اگر موجودی کافی نیست، پیغام مناسب ارسال می‌شود
                await process_message.edit_text(
                    f"❌ {message}\n\n"
                    f"موجودی فعلی: {int(db_user.balance):,} تومان\n"
                    f"مبلغ لازم: {int(order.amount):,} تومان\n\n"
                    "لطفاً ابتدا کیف پول خود را شارژ کنید."
                )
                return
            
            # اگر پرداخت موفقیت‌آمیز بود، اکانت VPN ایجاد کنیم
            # دریافت اطلاعات سفارش
            order = order_service.get_order_by_id(order_id)
            
            # ایجاد اکانت VPN جدید
            account_service = AccountService(session)
            
            try:
                # ساخت اکانت VPN با استفاده از سرویس مربوطه
                client_account = account_service.provision_account(
                    user_id=db_user.id,
                    plan_id=order.plan_id,
                    inbound_id=inbound_id
                )
                
                # ارسال پیام موفقیت و لینک کانفیگ
                panel_service = PanelService(session)
                inbound = panel_service.get_inbound_by_id(inbound_id)
                panel = panel_service.get_panel_by_id(inbound.panel_id)
                
                # بروزرسانی وضعیت سفارش به انجام شده
                order.status = OrderStatus.DONE
                order.processed_at = datetime.utcnow()
                session.commit()
                
                success_message = (
                    f"🎉 اکانت VPN شما با موفقیت ایجاد شد!\n\n"
                    f"📋 اطلاعات اکانت:\n"
                    f"🔹 حجم: {order.plan.traffic} گیگابایت\n"
                    f"🔹 مدت: {order.plan.duration_days} روز\n"
                    f"🔹 لوکیشن: {panel.flag_emoji} {panel.location}\n"
                    f"🔹 پروتکل: {inbound.protocol.upper()}\n\n"
                    f"🔗 لینک اتصال:\n"
                    f"<code>{client_account.vmess_config_url}</code>\n\n"
                    f"⚡️ می‌توانید با کپی لینک بالا در اپلیکیشن V2Ray به اینترنت آزاد متصل شوید."
                )
                
                await process_message.edit_text(
                    success_message,
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"Error creating account for user {telegram_user_id}: {e}", exc_info=True)
                await process_message.edit_text(
                    f"❌ خطا در ایجاد اکانت: {str(e)}\n\n"
                    "لطفاً با پشتیبانی تماس بگیرید."
                )
        except Exception as e:
            logger.error(f"Error in pay_with_balance_callback: {e}", exc_info=True)
            await callback.answer("خطایی رخ داد. لطفاً دوباره تلاش کنید.", show_alert=True)
        finally:
            if session:
                session.close()
                logger.debug("Database session closed in pay_with_balance_callback")
    
    @router.callback_query(F.data == "back_to_locations")
    async def back_to_locations_callback(callback: CallbackQuery):
        """بازگشت به لیست لوکیشن‌ها"""
        session = None
        try:
            # استخراج شناسه پلن از پیام قبلی اگر وجود داشته باشد
            plan_id = None
            if hasattr(callback, "message") and callback.message and callback.message.reply_markup:
                for row in callback.message.reply_markup.inline_keyboard:
                    for button in row:
                        if button.callback_data.startswith("select_inbound:"):
                            plan_id = int(button.callback_data.split(":")[1])
                            break
                        elif button.callback_data.startswith("back_to_inbounds:"):
                            plan_id = int(button.callback_data.split(":")[-1])
                            break
            
            if not plan_id:
                await callback.answer("خطا: شناسه پلن یافت نشد!", show_alert=True)
                return
            
            session = session_pool()
            panel_service = PanelService(session)
            panels = panel_service.get_all_panels(active_only=True)
            
            await callback.message.edit_text(
                text="🌍 لطفاً لوکیشن مورد نظر خود را انتخاب کنید:",
                reply_markup=get_locations_keyboard(panels)
            )
            
            await callback.answer()
        except Exception as e:
            logger.error(f"Error in back_to_locations_callback: {e}", exc_info=True)
            await callback.answer("خطایی رخ داد. لطفاً دوباره تلاش کنید.", show_alert=True)
        finally:
            if session:
                session.close()
                logger.debug("Database session closed in back_to_locations_callback")
    
    @router.callback_query(F.data.startswith("back_to_inbounds:"))
    async def back_to_inbounds_callback(callback: CallbackQuery):
        """بازگشت به لیست پروتکل‌ها (inbound‌ها)"""
        session = None
        try:
            plan_id = int(callback.data.split(":")[-1])
            
            # استخراج panel_id از پیام قبلی
            panel_id = None
            if hasattr(callback, "message") and callback.message and callback.message.text:
                # استخراج لوکیشن از متن پیام
                message_text = callback.message.text
                location_line = None
                for line in message_text.split("\n"):
                    if "لوکیشن:" in line:
                        location_line = line
                        break
                
                if location_line:
                    session = session_pool()
                    panel_service = PanelService(session)
                    panels = panel_service.get_all_panels()
                    
                    # یافتن پنل با استفاده از emoji و نام لوکیشن در متن
                    for panel in panels:
                        if panel.flag_emoji in location_line and panel.location in location_line:
                            panel_id = panel.id
                            break
            
            if not panel_id:
                await callback.answer("خطا: پنل مورد نظر یافت نشد!", show_alert=True)
                return
            
            session = session_pool() if not session else session
            panel_service = PanelService(session)
            panel = panel_service.get_panel_by_id(panel_id)
            
            # دریافت لیست inbound های این پنل
            inbounds = session.query(panel_service.get_inbounds_by_panel(panel_id)).all()
            
            await callback.message.edit_text(
                text=f"🌐 لوکیشن انتخابی: {panel.flag_emoji} {panel.location}\n\n"
                     f"لطفاً نوع پروتکل مورد نظر خود را انتخاب کنید:",
                reply_markup=get_inbounds_keyboard(inbounds, plan_id)
            )
            
            await callback.answer()
        except Exception as e:
            logger.error(f"Error in back_to_inbounds_callback: {e}", exc_info=True)
            await callback.answer("خطایی رخ داد. لطفاً دوباره تلاش کنید.", show_alert=True)
        finally:
            if session:
                session.close()
                logger.debug("Database session closed in back_to_inbounds_callback")
    
    @router.callback_query(F.data == "back_to_plans")
    async def back_to_plans_callback(callback: CallbackQuery):
        """بازگشت به لیست پلن‌ها"""
        session = None
        try:
            session = session_pool()
            plan_service = PlanService(session)
            plans = plan_service.get_all_active_plans()
            
            await callback.message.edit_text(
                text="📱 لطفاً پلن مورد نظر خود را انتخاب کنید:",
                reply_markup=get_plans_keyboard(plans)
            )
            
            await callback.answer()
        except Exception as e:
            logger.error(f"Error in back_to_plans_callback: {e}", exc_info=True)
            await callback.answer("خطایی رخ داد. لطفاً دوباره تلاش کنید.", show_alert=True)
        finally:
            if session:
                session.close()
                logger.debug("Database session closed in back_to_plans_callback") 