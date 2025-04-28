"""
هندلرهای کالبک مدیریت پنل‌ها برای ادمین
"""

import logging
import re
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.exceptions import TelegramBadRequest

from core.services.panel_service import PanelService, PanelConnectionError, PanelSyncError
from core.services.inbound_service import InboundService
from core.services.user_service import UserService
from db.models.panel import PanelStatus
from bot.states.admin_states import RegisterPanelStates
from bot.buttons.admin.panel_buttons import get_panel_list_keyboard, get_panel_manage_buttons

logger = logging.getLogger(__name__)

def register_admin_panel_callbacks(router: Router) -> None:
    """ثبت کالبک‌های مدیریت پنل‌ها برای ادمین"""
    
    @router.callback_query(F.data == "admin:panel:list")
    async def panel_list(callback: CallbackQuery, session: AsyncSession) -> None:
        """
        نمایش لیست پنل‌ها
        
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
            
            # دریافت لیست پنل‌ها
            panel_service = PanelService(session)
            panels = await panel_service.get_all_panels()
            
            # ساخت متن پیام
            text = "📡 <b>مدیریت پنل‌ها</b>\n\n"
            if not panels:
                text += "هیچ پنلی ثبت نشده است."
            else:
                text += f"تعداد پنل‌ها: {len(panels)}\n\n"
                text += "لطفاً پنل مورد نظر را انتخاب کنید:"
            
            # نمایش کیبورد پنل‌ها
            keyboard = get_panel_list_keyboard(panels)
            
            await callback.message.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            
        except Exception as e:
            logger.error(f"خطا در نمایش لیست پنل‌ها: {e}", exc_info=True)
            await callback.answer("⚠️ خطا در بارگذاری لیست پنل‌ها", show_alert=True)
    
    @router.callback_query(F.data.startswith("admin:panel:manage:"))
    async def panel_manage(callback: CallbackQuery, session: AsyncSession) -> None:
        """
        نمایش منوی مدیریت برای یک پنل خاص
        
        Args:
            callback (CallbackQuery): کالبک تلگرام
            session (AsyncSession): نشست دیتابیس
        """
        await callback.answer()
        
        try:
            # دریافت شناسه پنل
            panel_id = int(callback.data.split(":")[3])
            
            # بررسی دسترسی ادمین
            user_service = UserService(session)
            user = await user_service.get_user_by_telegram_id(callback.from_user.id)
            
            if not user or user.role not in ["admin", "superadmin"]:
                await callback.answer("⛔️ دسترسی غیرمجاز!", show_alert=True)
                return
            
            # دریافت اطلاعات پنل
            panel_service = PanelService(session)
            panel = await panel_service.get_panel_by_id(panel_id)
            
            if not panel:
                await callback.message.answer("❌ پنل مورد نظر یافت نشد.")
                return
            
            # ساخت متن پیام با وضعیت فارسی
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
            
            # نمایش کیبورد عملیات پنل
            keyboard = get_panel_manage_buttons(panel.id)
            
            await callback.message.edit_text(
                text,
                reply_markup=keyboard
            )
            
        except ValueError:
            logger.error(f"خطا در تبدیل شناسه پنل: {callback.data}")
            await callback.answer("⚠️ خطا در شناسه پنل", show_alert=True)
        except Exception as e:
            logger.error(f"خطا در نمایش مدیریت پنل: {e}", exc_info=True)
            await callback.answer("⚠️ خطا در بارگذاری مدیریت پنل", show_alert=True)
    
    @router.callback_query(F.data == "admin:panel:sync_all")
    async def sync_all_panels(callback: CallbackQuery, session: AsyncSession) -> None:
        """
        همگام‌سازی همه پنل‌ها
        
        Args:
            callback (CallbackQuery): کالبک تلگرام
            session (AsyncSession): نشست دیتابیس
        """
        user_id = callback.from_user.id
        
        try:
            # بررسی دسترسی ادمین
            user_service = UserService(session)
            user = await user_service.get_user_by_telegram_id(user_id)
            
            if not user or user.role not in ["admin", "superadmin"]:
                await callback.answer("⛔️ دسترسی غیرمجاز!", show_alert=True)
                return
            
            # اطلاع‌رسانی به کاربر
            await callback.answer("⏳ در حال همگام‌سازی...", show_alert=False)
            
            # همگام‌سازی پنل‌ها
            logger.info(f"شروع همگام‌سازی تمام پنل‌ها توسط ادمین {user_id}")
            panel_service = PanelService(session)
            sync_results = await panel_service.sync_all_panels_inbounds()
            
            success_count = len(sync_results)
            
            logger.info(f"همگام‌سازی {success_count} پنل با موفقیت انجام شد")
            await callback.answer(
                f"✅ همگام‌سازی {success_count} پنل با موفقیت انجام شد!",
                show_alert=True
            )
            
        except Exception as e:
            logger.error(f"خطا در همگام‌سازی پنل‌ها: {e}", exc_info=True)
            await callback.answer("⚠️ خطا در همگام‌سازی پنل‌ها", show_alert=True)
    
    @router.callback_query(F.data.startswith("admin:panel:sync:"))
    async def sync_panel(callback: CallbackQuery, session: AsyncSession) -> None:
        """
        همگام‌سازی یک پنل خاص
        
        Args:
            callback (CallbackQuery): کالبک تلگرام  
            session (AsyncSession): نشست دیتابیس
        """
        try:
            # دریافت شناسه پنل
            panel_id = int(callback.data.split(":")[3])
            logger.info(f"شروع همگام‌سازی پنل {panel_id} توسط کاربر {callback.from_user.id}")
            
            # بررسی دسترسی ادمین
            user_service = UserService(session)
            user = await user_service.get_user_by_telegram_id(callback.from_user.id)
            
            if not user or user.role not in ["admin", "superadmin"]:
                await callback.answer("⛔️ دسترسی غیرمجاز!", show_alert=True)
                return
            
            # اطلاع‌رسانی به کاربر
            await callback.answer("⏳ در حال همگام‌سازی پنل...", show_alert=False)
            
            # همگام‌سازی پنل
            panel_service = PanelService(session)
            
            # بررسی وجود پنل
            panel = await panel_service.get_panel_by_id(panel_id)
            if not panel:
                await callback.answer(f"❌ پنل با شناسه {panel_id} یافت نشد.", show_alert=True)
                return
            
            # انجام عملیات همگام‌سازی
            try:
                await panel_service.sync_panel_inbounds(panel_id)
                logger.info(f"همگام‌سازی پنل {panel_id} با موفقیت انجام شد.")
                await callback.answer("✅ همگام‌سازی پنل با موفقیت انجام شد.", show_alert=True)
                
                # به‌روزرسانی نمایش پنل
                panel = await panel_service.get_panel_by_id(panel_id)
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
                    await callback.message.edit_text(text, reply_markup=get_panel_manage_buttons(panel.id))
                except TelegramBadRequest as e:
                    if "message is not modified" in str(e):
                        logger.info("پیام تغییر نکرده است، نیازی به به‌روزرسانی نیست.")
                    else:
                        raise
                
            except PanelConnectionError:
                logger.error(f"خطای اتصال به پنل {panel_id} هنگام همگام‌سازی")
                await callback.answer("❌ خطا در اتصال به پنل. لطفاً ابتدا اتصال را تست کنید.", show_alert=True)
            except PanelSyncError as sync_err:
                logger.error(f"خطای همگام‌سازی پنل {panel_id}: {sync_err}")
                await callback.answer(f"❌ خطا در همگام‌سازی: {sync_err}", show_alert=True)
            
        except ValueError:
            logger.warning(f"شناسه پنل نامعتبر در داده کالبک: {callback.data}")
            await callback.answer("⚠️ خطای داخلی: شناسه پنل نامعتبر است.", show_alert=True)
        except Exception as e:
            logger.error(f"خطای پیش‌بینی نشده در همگام‌سازی پنل: {e}", exc_info=True)
            await callback.answer("⚠️ خطای ناشناخته در همگام‌سازی پنل.", show_alert=True)
    
    @router.callback_query(F.data.startswith("admin:panel:test_connection:"))
    async def panel_connection_test(callback: CallbackQuery, session: AsyncSession) -> None:
        """
        تست اتصال به یک پنل خاص
        
        Args:
            callback (CallbackQuery): کالبک تلگرام
            session (AsyncSession): نشست دیتابیس
        """
        try:
            # دریافت شناسه پنل
            panel_id = int(callback.data.split(":")[3])
            logger.info(f"شروع تست اتصال به پنل {panel_id} توسط کاربر {callback.from_user.id}")
            
            # بررسی دسترسی ادمین
            user_service = UserService(session)
            user = await user_service.get_user_by_telegram_id(callback.from_user.id)
            
            if not user or user.role not in ["admin", "superadmin"]:
                await callback.answer("⛔️ دسترسی غیرمجاز!", show_alert=True)
                return
            
            # اطلاع‌رسانی به کاربر
            await callback.answer("⏳ در حال تست اتصال...", show_alert=False)
            
            # تست اتصال پنل
            panel_service = PanelService(session)
            success, error_message = await panel_service.test_panel_connection(panel_id)
            
            if success:
                logger.info(f"تست اتصال به پنل {panel_id} موفقیت‌آمیز بود")
                await callback.answer("✅ اتصال به پنل با موفقیت برقار شد.", show_alert=True)
                
                # به‌روزرسانی وضعیت پنل به ACTIVE
                update_success = await panel_service.update_panel_status(panel_id, PanelStatus.ACTIVE)
                if update_success:
                    logger.info(f"وضعیت پنل {panel_id} پس از تست موفق به ACTIVE تغییر یافت")
                    
                    # به‌روزرسانی نمایش پنل
                    panel = await panel_service.get_panel_by_id(panel_id)
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
                    
                    await callback.message.edit_text(text, reply_markup=get_panel_manage_buttons(panel.id))
                else:
                    logger.error(f"خطا در به‌روزرسانی وضعیت پنل {panel_id} به ACTIVE پس از تست موفق")
            else:
                logger.warning(f"تست اتصال به پنل {panel_id} با خطا مواجه شد: {error_message}")
                
                # ساده‌سازی پیام خطا برای کاربر
                simplified_error = error_message.split(":", 1)[-1].strip() if error_message else "خطای نامشخص"
                if not simplified_error or len(simplified_error) > 150:
                    simplified_error = "خطا در اتصال یا احراز هویت پنل."
                    
                await callback.answer(f"❌ تست اتصال ناموفق: {simplified_error}", show_alert=True)
                
                # به‌روزرسانی وضعیت پنل به ERROR
                update_success = await panel_service.update_panel_status(panel_id, PanelStatus.ERROR)
                if update_success:
                    logger.info(f"وضعیت پنل {panel_id} پس از تست ناموفق به ERROR تغییر یافت")
            
        except ValueError:
            logger.error(f"شناسه پنل نامعتبر در داده کالبک: {callback.data}")
            await callback.answer("⚠️ خطای داخلی: شناسه پنل نامعتبر است.", show_alert=True)
        except Exception as e:
            logger.error(f"خطای پیش‌بینی نشده در تست اتصال پنل: {e}", exc_info=True)
            await callback.answer("⚠️ خطای پیش‌بینی نشده در هنگام تست اتصال پنل.", show_alert=True)
    
    @router.callback_query(F.data.startswith("admin:panel:toggle_status:"))
    async def panel_toggle_status(callback: CallbackQuery, session: AsyncSession) -> None:
        """
        تغییر وضعیت یک پنل بین فعال و غیرفعال
        
        Args:
            callback (CallbackQuery): کالبک تلگرام
            session (AsyncSession): نشست دیتابیس
        """
        try:
            # دریافت شناسه پنل
            panel_id = int(callback.data.split(":")[3])
            logger.info(f"درخواست تغییر وضعیت پنل {panel_id} توسط کاربر {callback.from_user.id}")
            
            # بررسی دسترسی ادمین
            user_service = UserService(session)
            user = await user_service.get_user_by_telegram_id(callback.from_user.id)
            
            if not user or user.role not in ["admin", "superadmin"]:
                await callback.answer("⛔️ دسترسی غیرمجاز!", show_alert=True)
                return
            
            # دریافت وضعیت فعلی پنل
            panel_service = PanelService(session)
            panel = await panel_service.get_panel_by_id(panel_id)
            
            if not panel:
                await callback.message.edit_text(f"❌ پنل با شناسه {panel_id} یافت نشد.")
                return
            
            # تغییر وضعیت پنل
            new_status = PanelStatus.INACTIVE if panel.status == PanelStatus.ACTIVE else PanelStatus.ACTIVE
            status_text = "غیرفعال" if new_status == PanelStatus.INACTIVE else "فعال"
            
            # به‌روزرسانی وضعیت پنل
            update_success = await panel_service.update_panel_status(panel_id, new_status)
            if update_success:
                logger.info(f"وضعیت پنل {panel_id} به {new_status.value} تغییر یافت")
                await callback.answer(f"✅ وضعیت پنل به {status_text} تغییر یافت.", show_alert=True)
                
                # به‌روزرسانی نمایش پنل
                panel = await panel_service.get_panel_by_id(panel_id)
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
                    await callback.message.edit_text(text, reply_markup=get_panel_manage_buttons(panel.id))
                except TelegramBadRequest as e:
                    if "message is not modified" in str(e):
                        logger.info("پیام تغییر نکرده است، نیازی به به‌روزرسانی نیست.")
                    else:
                        raise
            else:
                logger.error(f"خطا در تغییر وضعیت پنل {panel_id}")
                await callback.answer("❌ خطا در تغییر وضعیت پنل.", show_alert=True)
            
        except ValueError:
            logger.warning(f"خطا در تبدیل شناسه پنل به عدد در panel_toggle_status: {callback.data}")
            await callback.message.answer("خطای داخلی: شناسه پنل نامعتبر است.")
        except Exception as e:
            logger.error(f"خطای پیش‌بینی نشده در تغییر وضعیت پنل: {e}", exc_info=True)
            await callback.answer("⚠️ خطای پیش‌بینی نشده در تغییر وضعیت پنل.", show_alert=True)
    
    @router.callback_query(F.data == "admin:panel:register")
    async def register_panel_start(callback: CallbackQuery, state: FSMContext) -> None:
        """
        شروع فرآیند ثبت پنل جدید
        
        Args:
            callback (CallbackQuery): کالبک تلگرام
            state (FSMContext): وضعیت FSM
        """
        await callback.answer()
        
        try:
            await state.set_state(RegisterPanelStates.waiting_for_panel_url)
            await callback.message.answer("لطفا آدرس پنل را وارد کنید (مثال: https://panel.example.com:54321):")
        except Exception as e:
            logger.error(f"خطا در شروع فرآیند ثبت پنل: {e}", exc_info=True)
            await callback.answer("⚠️ خطا در شروع فرآیند ثبت پنل", show_alert=True) 