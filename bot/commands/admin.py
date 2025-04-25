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
from bot.keyboards.admin_keyboard import get_admin_panel_keyboard
from core.services.panel_service import PanelService
from core.services.user_service import UserService
from bot.states.admin_states import RegisterPanelStates

# تنظیم لاگینگ
logger = logging.getLogger(__name__)

# Initialize router for aiogram 3.x style handlers
router = Router()

# متغیر سراسری برای دسترسی به session_maker
_session_maker = None


async def admin_command(message: types.Message):
    """
    دستور /admin برای دسترسی به پنل مدیریت
    """
    logger.info(f"Admin command received from user {message.from_user.id}")
    
    session = _session_maker()
    try:
        user_service = UserService(session)
        is_admin = user_service.is_admin(message.from_user.id)
        
        if not is_admin:
            logger.warning(f"User {message.from_user.id} denied access to admin panel")
            await message.answer("⛔️ شما دسترسی لازم برای این عملیات را ندارید.")
            return
        
        # Get admin panel stats
        panel_service = PanelService(session)
        active_panels = await panel_service.get_active_panels()
        
        admin_text = (
            "🎛 <b>پنل مدیریت</b>\n\n"
            f"📊 پنل‌های فعال: {len(active_panels)}\n"
            "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:"
        )
        
        await message.answer(
            admin_text,
            reply_markup=get_admin_panel_keyboard(),
            parse_mode="HTML"
        )
        logger.info(f"Admin panel displayed for user {message.from_user.id}")
        
    except Exception as e:
        logger.error(f"Error in admin command: {str(e)}")
        await message.answer("⚠️ خطایی در بارگذاری پنل مدیریت رخ داد.")
    finally:
        session.close()


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


@router.callback_query(F.data == "panel_confirm")
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
        panel = await panel_service.add_panel(
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
            
            # اجرای همگام‌سازی inbound‌ها
            await panel_service.sync_panel_inbounds(panel.id)
            
            await callback_query.message.answer("✅ همگام‌سازی inbound‌ها با موفقیت انجام شد.")

        except Exception as e:
            logger.error(f"Error syncing inbounds for panel {panel.id}: {str(e)}", exc_info=True)
            await callback_query.message.answer(
                f"❌ خطا در همگام‌سازی inbound‌های پنل {panel.name}:\n<code>{str(e)}</code>",
                parse_mode="HTML"
            )

        finally:
            # پایان فرایند اضافه کردن پنل و بازگشت به منوی اصلی ادمین
            await state.clear()
            logger.info(f"Add panel process finished for user {callback_query.from_user.id}")
            # Optionally send admin main keyboard again

    except ValueError as e:
        logger.error(f"Value error during add panel confirmation: {str(e)}", exc_info=True)
        await callback_query.message.answer(f"❌ خطا: {str(e)}")
        # Stay in the current state or move to a specific error state if needed
    except SQLAlchemyError as e:
        logger.error(f"Database error during add panel confirmation: {str(e)}", exc_info=True)
        await callback_query.message.answer(f"❌ خطا در پایگاه داده هنگام افزودن پنل: {str(e)}")
        # Stay in the current state or move to a specific error state if needed
    except Exception as e:
        logger.error(f"Unexpected error during add panel confirmation: {str(e)}", exc_info=True)
        await callback_query.message.answer(f"❌ خطای غیرمنتظره: {str(e)}")
        # Stay in the current state or move to a specific error state if needed
    finally:
        session.close()


# New handler for managing panels
@router.callback_query(F.data == "manage_panels")
async def manage_panels_handler(callback_query: types.CallbackQuery):
    """
    هندلر نمایش لیست پنل‌ها به ادمین
    """
    await callback_query.answer()
    user_id = callback_query.from_user.id
    logger.info(f"User {user_id} requested to view panels list.")

    session = _session_maker()
    try:
        user_service = UserService(session)
        is_admin = user_service.is_admin(user_id)

        if not is_admin:
            logger.warning(f"User {user_id} denied access to manage panels.")
            await callback_query.message.answer("شما دسترسی لازم برای این عملیات را ندارید.")
            return

        panel_service = PanelService(session)
        panels = await panel_service.get_all_panels()

        if not panels:
            await callback_query.message.answer("❌ هیچ پنلی در سیستم ثبت نشده است.")
            logger.info(f"No panels found for user {user_id}.")
        else:
            # Sort panels by ID in descending order
            panels.sort(key=lambda p: p.id, reverse=True)

            # Replace combined panel list with manage buttons per panel
            for panel in panels:
                status_emoji = "✅" if panel.status == "ACTIVE" else "❌"
                panel_text = (
                    f"📟 پنل {panel.id} – {panel.location_name} {panel.flag_emoji}\n"
                    f"وضعیت: {status_emoji}"
                )
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔧 مدیریت پنل", callback_data=f"panel_manage:{panel.id}")]
                ])
                await callback_query.message.answer(panel_text, reply_markup=keyboard, parse_mode="HTML")
            logger.info(f"Sent panels list with manage buttons to user {user_id}.")

    except Exception as e:
        logger.error(f"Error in manage_panels_handler for user {user_id}: {str(e)}", exc_info=True)
        await callback_query.message.answer(f"❌ خطایی رخ داد: <code>{str(e)}</code>", parse_mode="HTML")
    finally:
        session.close()


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


@router.callback_query(F.data == "panel_cancel")
async def cancel_panel_callback(callback_query: types.CallbackQuery, state: FSMContext):
    """
    لغو اضافه کردن پنل از طریق دکمه انصراف
    """
    await cancel_add_panel(callback_query.message, state)
    await callback_query.answer()


@router.callback_query(lambda c: c.data == 'register_panel')
async def cmd_register_panel(callback_query: types.CallbackQuery, state: FSMContext):
    await state.set_state(RegisterPanelStates.waiting_for_panel_url)
    await callback_query.message.answer(
        "لطفاً آدرس کامل پنل (به همراه http/https و مسیر مانند /xui/ در صورت وجود) را وارد کنید:\n"
        "مثال: `http://123.123.123.123:54321` یا `https://panel.example.com/xui`"
    )
    await callback_query.answer()


def register_admin_commands(dp: Dispatcher, session_maker: sessionmaker):
    """
    ثبت هندلرهای دستورات ادمین در دیسپچر ربات
    """
    global _session_maker
    _session_maker = session_maker
    
    logger.info("Registering admin commands handlers")
    
    # دستور /admin
    dp.message.register(admin_command, Command("admin"))
    dp.message.register(admin_command, F.text == "⚙️ پنل مدیریت")
    
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
    
    # Include the router in the dispatcher (handles all router callbacks)
    dp.include_router(router)
    
    logger.info("Admin commands handlers registered successfully")
