"""
دستورات ادمین مثل اضافه کردن پنل
"""

import logging
from aiogram import types, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import async_sessionmaker

from bot.states import AddPanel
from bot.keyboards import get_main_keyboard
from core.services.panel_service import PanelService
from core.services.user_service import UserService

# تنظیم لاگینگ
logger = logging.getLogger(__name__)

# متغیر سراسری برای دسترسی به session_maker
_session_maker = None


async def add_panel_start(message: types.Message, state: FSMContext):
    """
    شروع فرایند اضافه کردن پنل جدید با دستور /addpanel
    """
    # لاگ کردن شروع اجرای دستور 
    logger.info(f"Starting /addpanel command for user {message.from_user.id}")
    
    # بررسی دسترسی ادمین
    session = _session_maker()
    try:
        user_service = UserService(session)
        logger.info(f"Checking admin permission for user {message.from_user.id}")
        is_admin = user_service.is_admin(message.from_user.id)
        logger.info(f"User {message.from_user.id} is admin: {is_admin}")
        
        if not is_admin:
            logger.warning(f"User {message.from_user.id} denied access to /addpanel command")
            await message.answer("شما دسترسی لازم برای این عملیات را ندارید.")
            return
        
        # شروع روند اضافه کردن پنل
        await state.set_state(AddPanel.name)
        logger.info(f"Set state to AddPanel.name for user {message.from_user.id}")
        
        # کیبورد برای انصراف
        cancel_keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="❌ انصراف")]],
            resize_keyboard=True
        )
        
        await message.answer(
            "📋 افزودن پنل جدید - مرحله 1/7:\n\n"
            "لطفاً نام پنل را وارد کنید (مثلاً France-1):", 
            reply_markup=cancel_keyboard
        )
        logger.info(f"Sent first step message to user {message.from_user.id}")
    except Exception as e:
        logger.error(f"Error in add_panel_start: {str(e)}")
        await message.answer(f"خطا در اجرای دستور: {str(e)}")
    finally:
        session.close()


async def process_panel_name(message: types.Message, state: FSMContext):
    """
    دریافت نام پنل
    """
    if message.text == "❌ انصراف":
        await cancel_add_panel(message, state)
        return
    
    await state.update_data(name=message.text)
    await state.set_state(AddPanel.location)
    
    await message.answer(
        "📋 افزودن پنل جدید - مرحله 2/7:\n\n"
        "لطفاً موقعیت (کشور) پنل را وارد کنید (مثلاً France):"
    )


async def process_panel_location(message: types.Message, state: FSMContext):
    """
    دریافت موقعیت پنل
    """
    if message.text == "❌ انصراف":
        await cancel_add_panel(message, state)
        return
    
    await state.update_data(location=message.text)
    await state.set_state(AddPanel.flag_emoji)
    
    await message.answer(
        "📋 افزودن پنل جدید - مرحله 3/7:\n\n"
        "لطفاً ایموجی پرچم کشور را وارد کنید (مثلاً 🇫🇷):"
    )


async def process_panel_flag_emoji(message: types.Message, state: FSMContext):
    """
    دریافت ایموجی پرچم
    """
    if message.text == "❌ انصراف":
        await cancel_add_panel(message, state)
        return
    
    await state.update_data(flag_emoji=message.text)
    await state.set_state(AddPanel.url)
    
    await message.answer(
        "📋 افزودن پنل جدید - مرحله 4/7:\n\n"
        "لطفاً آدرس پنل را وارد کنید (مثلاً https://panel.domain.com:443):"
    )


async def process_panel_url(message: types.Message, state: FSMContext):
    """
    دریافت آدرس پنل
    """
    if message.text == "❌ انصراف":
        await cancel_add_panel(message, state)
        return
    
    await state.update_data(url=message.text)
    await state.set_state(AddPanel.username)
    
    await message.answer(
        "📋 افزودن پنل جدید - مرحله 5/7:\n\n"
        "لطفاً نام کاربری پنل را وارد کنید:"
    )


async def process_panel_username(message: types.Message, state: FSMContext):
    """
    دریافت نام کاربری پنل
    """
    if message.text == "❌ انصراف":
        await cancel_add_panel(message, state)
        return
    
    await state.update_data(username=message.text)
    await state.set_state(AddPanel.password)
    
    await message.answer(
        "📋 افزودن پنل جدید - مرحله 6/7:\n\n"
        "لطفاً رمز عبور پنل را وارد کنید:"
    )


async def process_panel_password(message: types.Message, state: FSMContext):
    """
    دریافت رمز عبور پنل
    """
    if message.text == "❌ انصراف":
        await cancel_add_panel(message, state)
        return
    
    await state.update_data(password=message.text)
    await state.set_state(AddPanel.default_label)
    
    await message.answer(
        "📋 افزودن پنل جدید - مرحله 7/7:\n\n"
        "لطفاً پیشوند نام اکانت پیش‌فرض را وارد کنید (مثلاً FR-MoonVPN):"
    )


async def process_panel_default_label(message: types.Message, state: FSMContext):
    """
    دریافت پیشوند نام اکانت پیش‌فرض
    """
    if message.text == "❌ انصراف":
        await cancel_add_panel(message, state)
        return
    
    await state.update_data(default_label=message.text)
    await state.set_state(AddPanel.confirmation)
    
    # نمایش اطلاعات وارد شده برای تایید نهایی
    data = await state.get_data()
    
    confirmation_message = (
        "📋 <b>خلاصه اطلاعات پنل جدید:</b>\n\n"
        f"🔹 <b>نام:</b> {data['name']}\n"
        f"🔹 <b>موقعیت:</b> {data['location']} {data['flag_emoji']}\n"
        f"🔹 <b>آدرس:</b> {data['url']}\n"
        f"🔹 <b>نام کاربری:</b> {data['username']}\n"
        f"🔹 <b>رمز عبور:</b> {'*' * len(data['password'])}\n"
        f"🔹 <b>پیشوند اکانت:</b> {data['default_label']}\n\n"
        "آیا اطلاعات وارد شده را تایید می‌کنید؟"
    )
    
    # کیبورد برای تایید یا انصراف
    confirmation_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ تایید و ذخیره", callback_data="panel_confirm"),
                InlineKeyboardButton(text="❌ انصراف", callback_data="panel_cancel")
            ]
        ]
    )
    
    await message.answer(
        confirmation_message, 
        reply_markup=confirmation_keyboard,
        parse_mode="HTML"
    )


async def confirm_add_panel(callback_query: types.CallbackQuery, state: FSMContext):
    """
    تایید و ذخیره اطلاعات پنل در دیتابیس
    """
    await callback_query.answer()
    data = await state.get_data()
    
    # ذخیره در دیتابیس
    session = _session_maker()
    try:
        panel_service = PanelService(session)
        panel = panel_service.add_panel(
            name=data['name'],
            location=data['location'],
            flag_emoji=data['flag_emoji'],
            url=data['url'],
            username=data['username'],
            password=data['password'],
            default_label=data['default_label']
        )
        
        await callback_query.message.answer(
            f"✅ پنل <b>{panel.name}</b> با موفقیت به سیستم اضافه شد.\n\n"
            f"اطلاعات پنل با شناسه <code>{panel.id}</code> در سیستم ثبت گردید.",
            reply_markup=get_main_keyboard(),
            parse_mode="HTML"
        )
        
        # شروع همگام‌سازی inbound‌ها
        try:
            await callback_query.message.answer(
                "🔄 در حال دریافت اطلاعات inbound‌ها از پنل...\n"
                "این فرایند ممکن است کمی طول بکشد."
            )
            
            # اجرای همگام‌سازی inbound‌ها به صورت سنکرون
            # چون تابع سنکرون است، آن را مستقیماً فراخوانی می‌کنیم
            inbounds = panel_service.sync_panel_inbounds(panel.id)
            
            if inbounds:
                inbounds_info = "\n".join([f"- {inbound.protocol}: {inbound.tag}" for inbound in inbounds])
                await callback_query.message.answer(
                    f"✅ تعداد {len(inbounds)} inbound با موفقیت از پنل دریافت و همگام‌سازی شد:\n\n{inbounds_info}",
                    parse_mode="HTML"
                )
            else:
                await callback_query.message.answer(
                    "⚠️ هیچ inbound فعالی در پنل یافت نشد. لطفاً پنل را بررسی کنید."
                )
        except Exception as e:
            await callback_query.message.answer(
                f"⚠️ خطا در همگام‌سازی inbound‌ها: {str(e)}\n"
                f"پنل در سیستم ثبت شد، اما باید inbound‌ها را بعداً همگام‌سازی کنید."
            )
        
    except Exception as e:
        await callback_query.message.answer(
            f"❌ خطا در ثبت پنل: {str(e)}",
            reply_markup=get_main_keyboard()
        )
    finally:
        session.close()
    
    # پاکسازی وضعیت
    await state.clear()


async def cancel_add_panel(message: types.Message, state: FSMContext):
    """
    انصراف از فرایند اضافه کردن پنل
    """
    current_state = await state.get_state()
    if current_state is None:
        return
    
    await state.clear()
    await message.answer(
        "❌ فرایند افزودن پنل لغو شد.", 
        reply_markup=get_main_keyboard()
    )


async def cancel_panel_callback(callback_query: types.CallbackQuery, state: FSMContext):
    """
    انصراف از طریق کالبک دکمه
    """
    await callback_query.answer()
    await state.clear()
    await callback_query.message.answer(
        "❌ فرایند افزودن پنل لغو شد.", 
        reply_markup=get_main_keyboard()
    )


def register_admin_commands(dp: Dispatcher, session_maker: sessionmaker):
    """
    ثبت هندلرهای دستورات ادمین در دیسپچر ربات
    """
    global _session_maker
    _session_maker = session_maker
    
    logger.info("Registering admin commands handlers")
    
    # دستور /addpanel
    dp.message.register(add_panel_start, Command("addpanel"))
    
    # هندلرهای FSM برای مراحل اضافه کردن پنل
    dp.message.register(process_panel_name, AddPanel.name)
    dp.message.register(process_panel_location, AddPanel.location)
    dp.message.register(process_panel_flag_emoji, AddPanel.flag_emoji)
    dp.message.register(process_panel_url, AddPanel.url)
    dp.message.register(process_panel_username, AddPanel.username)
    dp.message.register(process_panel_password, AddPanel.password)
    dp.message.register(process_panel_default_label, AddPanel.default_label)
    
    # کالبک‌های تایید یا انصراف
    dp.callback_query.register(confirm_add_panel, F.data == "panel_confirm")
    dp.callback_query.register(cancel_panel_callback, F.data == "panel_cancel")
    
    logger.info("Admin commands handlers registered successfully")
