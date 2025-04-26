"""
کالبک‌های مربوط به مدیریت اینباندها و کلاینت‌ها
"""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.services.user_service import UserService
from core.services.panel_service import PanelService
from bot.buttons.inbound_buttons import (
    get_inbound_manage_buttons,
    get_inbound_clients_keyboard,
    format_inbound_details
)

logger = logging.getLogger(__name__)


def register_inbound_callbacks(router: Router, session_pool: async_sessionmaker[AsyncSession]) -> None:
    """ثبت کال‌بک‌های مدیریت اینباندها و کلاینت‌ها"""
    
    @router.callback_query(F.data.startswith("inbound_clients:"))
    async def inbound_clients_list(callback: CallbackQuery, session: AsyncSession) -> None:
        """نمایش لیست کلاینت‌های یک اینباند خاص با دکمه‌های عملیاتی"""
        await callback.answer()
        try:
            # استخراج شناسه‌های پنل و اینباند از کال‌بک
            parts = callback.data.split(":")
            if len(parts) != 3 or not parts[1].isdigit() or not parts[2].isdigit():
                raise ValueError("فرمت داده‌های کال‌بک نامعتبر است")
            
            panel_id = int(parts[1])
            inbound_id = int(parts[2])

            # کنترل دسترسی ادمین
            user_service = UserService(session)
            user = await user_service.get_user_by_telegram_id(callback.from_user.id)
            if not user or user.role not in ["admin", "superadmin"]:
                await callback.answer("⛔️ دسترسی غیرمجاز!", show_alert=True)
                return

            # دریافت لیست کلاینت‌ها از سرویس پنل
            panel_service = PanelService(session)
            
            # دریافت اطلاعات اینباند برای نمایش در بالای پیام
            all_inbounds = await panel_service.get_inbounds_by_panel_id(panel_id)
            
            # Check if inbounds are SQLAlchemy model objects or dictionaries and handle accordingly
            if all_inbounds and hasattr(all_inbounds[0], 'remote_id'):
                # SQLAlchemy objects
                inbound_info = next((inb for inb in all_inbounds if inb.remote_id == inbound_id), None)
                
                if not inbound_info:
                    await callback.answer("❌ اینباند مورد نظر یافت نشد یا از پنل حذف شده است.", show_alert=True)
                    return
                
                inbound_tag = inbound_info.tag  # Access as attribute
                inbound_remark = inbound_info.remark if hasattr(inbound_info, 'remark') else f'#{inbound_id}'
            else:
                # Dictionary objects
                inbound_info = next((inb for inb in all_inbounds if inb.get("id") == inbound_id), None)
                
                if not inbound_info:
                    await callback.answer("❌ اینباند مورد نظر یافت نشد یا از پنل حذف شده است.", show_alert=True)
                    return
                
                inbound_tag = inbound_info.get('tag', '')
                inbound_remark = inbound_info.get('remark', f'#{inbound_id}')
            
            # دریافت لیست کلاینت‌های اینباند
            inbound_clients = await panel_service.get_clients_by_inbound(panel_id, inbound_id)
            
            # اگر کلاینتی وجود نداشت
            if not inbound_clients:
                await callback.message.edit_text(
                    f"⚠️ هیچ کلاینتی در اینباند <b>{inbound_remark}</b> وجود ندارد.",
                    reply_markup=get_inbound_manage_buttons(panel_id, inbound_id),
                    parse_mode="HTML"
                )
                return

            # فرمت‌بندی لیست کلاینت‌ها برای نمایش
            clients_text = []
            for idx, client in enumerate(inbound_clients, 1):
                # محاسبه مصرف ترافیک و زمان باقی‌مانده
                total_gb = client.get("totalGB", 0)
                used_traffic = client.get("up", 0) + client.get("down", 0)
                total_gb_formatted = round(total_gb / (1024**3), 2) if total_gb > 0 else "نامحدود"
                used_traffic_formatted = round(used_traffic / (1024**3), 2)
                
                # بررسی وضعیت زمانی
                expiry_time = client.get("expiryTime", 0)
                expiry_status = "نامحدود" if expiry_time == 0 else format_expiry_time(expiry_time)
                
                # نمایش وضعیت فعال/غیرفعال
                status = "✅" if client.get("enable", True) else "❌"
                
                # افزودن به لیست
                clients_text.append(
                    f"{idx}. {status} <b>{client.get('email', 'بدون نام')}</b>\n"
                    f"   ↪️ ترافیک: {used_traffic_formatted}/{total_gb_formatted} GB\n"
                    f"   ↪️ اعتبار: {expiry_status}"
                )

            # ساخت متن کامل پیام
            header = f"👥 <b>لیست کلاینت‌های اینباند {inbound_remark} (#{inbound_id})</b>\n\n"
            message_text = header + "\n\n".join(clients_text)
            
            # ساخت کیبورد با دکمه‌های عملیاتی برای هر کلاینت
            keyboard = get_inbound_clients_keyboard(inbound_clients, panel_id, inbound_id)
            
            # ارسال پیام با کیبورد
            await callback.message.edit_text(
                message_text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )

        except ValueError as e:
            logger.warning(f"خطای مقدار در هندلر inbound_clients_list: {e}")
            await callback.answer(f"خطا: {e}", show_alert=True)
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                logger.info("پیام تغییر نکرده، احتمالاً فشار مجدد دکمه.")
                await callback.answer()  # پاسخ خاموش در صورت عدم تغییر پیام
            else:
                logger.error(f"خطای API تلگرام در inbound_clients_list: {e}", exc_info=True)
                await callback.answer("⚠️ خطایی در نمایش لیست کلاینت‌ها رخ داد.", show_alert=True)
        except Exception as e:
            logger.error(f"خطا در هندلر inbound_clients_list: {e}", exc_info=True)
            await callback.answer("⚠️ خطایی در پردازش درخواست رخ داد.", show_alert=True)


# تابع کمکی برای فرمت‌بندی زمان انقضا
def format_expiry_time(expiry_timestamp: int) -> str:
    """تبدیل timestamp به فرمت خوانا برای نمایش زمان انقضا"""
    from datetime import datetime, timezone
    
    # اگر صفر باشد یعنی نامحدود
    if expiry_timestamp == 0:
        return "نامحدود"
    
    try:
        # تبدیل تایم‌استمپ میلی‌ثانیه‌ای به تاریخ
        expiry_date = datetime.fromtimestamp(expiry_timestamp / 1000, tz=timezone.utc)
        now = datetime.now(timezone.utc)
        
        # محاسبه تفاوت زمانی
        if expiry_date < now:
            return "منقضی شده"
        
        diff = expiry_date - now
        days = diff.days
        
        if days > 30:
            months = days // 30
            return f"{months} ماه"
        elif days > 0:
            return f"{days} روز"
        else:
            hours = diff.seconds // 3600
            return f"{hours} ساعت"
    except Exception:
        return "نامشخص" 