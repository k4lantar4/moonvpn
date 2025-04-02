from datetime import datetime, timedelta
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from app.keyboards.admin_keyboards import get_admin_main_keyboard, get_admin_reports_keyboard, get_report_date_range_keyboard, get_payment_admin_management_keyboard
from app.api.api_client import (
    get_payment_admin_reports, get_payment_admin_assignments, 
    get_payment_admin_assignment, create_payment_admin_assignment,
    update_payment_admin_assignment, delete_payment_admin_assignment,
    get_users_available_for_payment_admin, get_bank_cards_for_payment
)
from app.utils.auth import admin_only, superuser_only
from app.handlers.error_handler import handle_error

# Set up logging
logger = logging.getLogger(__name__)

# Define conversation states
(
    REPORTS_MENU,
    REPORT_DATE_SELECTION,
    VIEWING_REPORT,
    PAYMENT_ADMIN_MENU,
    SELECTING_ADMIN_ACTION,
    ADDING_PAYMENT_ADMIN,
    SELECTING_USER,
    SELECTING_BANK_CARD,
    ENTERING_TELEGRAM_GROUP,
    VIEWING_PAYMENT_ADMINS,
    SELECTING_ADMIN_TO_UPDATE,
    SELECTING_UPDATE_FIELD,
    UPDATING_CARD,
    UPDATING_GROUP,
    CONFIRMING_DELETE,
) = range(15)

@admin_only
async def handle_admin_reports(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the reports menu for admins."""
    query = update.callback_query
    if query:
        await query.answer()
    
    user_id = update.effective_user.id
    logger.info(f"User {user_id} accessed admin reports menu")
    
    message = "📊 مدیریت گزارشات\n\nلطفا یکی از گزینه‌های زیر را انتخاب کنید:"
    
    if query:
        await query.edit_message_text(
            message,
            reply_markup=get_admin_reports_keyboard()
        )
    else:
        await update.effective_message.reply_text(
            message,
            reply_markup=get_admin_reports_keyboard()
        )
    
    return REPORTS_MENU

@admin_only
async def handle_payment_performance_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the selection of payment admin performance report."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    logger.info(f"User {user_id} selected payment performance report")
    
    # Store the report type in context
    context.user_data['report_type'] = 'payment_performance'
    
    message = "📈 گزارش عملکرد مدیران پرداخت\n\nلطفاً بازه زمانی مورد نظر خود را انتخاب کنید:"
    
    await query.edit_message_text(
        message,
        reply_markup=get_report_date_range_keyboard()
    )
    
    return REPORT_DATE_SELECTION

@admin_only
async def handle_report_date_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the date range selection for reports."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    data = query.data
    
    # Process the selected date range
    today = datetime.now().date()
    
    if data == 'report_today':
        start_date = today.strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')
        date_range_text = "امروز"
    elif data == 'report_week':
        start_date = (today - timedelta(days=7)).strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')
        date_range_text = "هفته اخیر"
    elif data == 'report_month':
        start_date = (today - timedelta(days=30)).strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')
        date_range_text = "ماه اخیر"
    elif data == 'report_all_time':
        start_date = None
        end_date = None
        date_range_text = "همه زمان‌ها"
    elif data == 'admin_back_to_reports':
        return await handle_admin_reports(update, context)
    else:
        logger.warning(f"User {user_id} selected unknown date range option: {data}")
        await query.edit_message_text(
            "❌ گزینه انتخاب شده نامعتبر است. لطفا دوباره تلاش کنید.",
            reply_markup=get_report_date_range_keyboard()
        )
        return REPORT_DATE_SELECTION
    
    # Store date range in context
    context.user_data['report_start_date'] = start_date
    context.user_data['report_end_date'] = end_date
    context.user_data['report_date_range_text'] = date_range_text
    
    logger.info(f"User {user_id} selected date range {date_range_text} for report")
    
    # Handle different report types
    if context.user_data.get('report_type') == 'payment_performance':
        return await generate_payment_admin_report(update, context)
    
    # Default fallback
    await query.edit_message_text(
        "❌ نوع گزارش نامشخص است. لطفا دوباره تلاش کنید.",
        reply_markup=get_admin_reports_keyboard()
    )
    return REPORTS_MENU

@admin_only
async def generate_payment_admin_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Generate and display the payment admin performance report."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Get date range from context
    start_date = context.user_data.get('report_start_date')
    end_date = context.user_data.get('report_end_date')
    date_range_text = context.user_data.get('report_date_range_text')
    
    # If user is not a superuser, restrict to their own data
    admin_id = None if await superuser_only(update, context, silent=True) else user_id
    
    await query.edit_message_text(
        f"🔄 در حال تهیه گزارش عملکرد مدیران پرداخت برای {date_range_text}...\n"
        "لطفا صبر کنید."
    )
    
    try:
        # Fetch report data from API
        report_data = await get_payment_admin_reports(
            start_date=start_date,
            end_date=end_date,
            admin_id=admin_id
        )
        
        if not report_data or not report_data.get('data'):
            await query.edit_message_text(
                f"❌ اطلاعاتی برای نمایش وجود ندارد.\n"
                f"هیچ داده‌ای برای بازه زمانی {date_range_text} یافت نشد.",
                reply_markup=get_report_date_range_keyboard()
            )
            return REPORT_DATE_SELECTION
        
        # Format the report data into a readable message
        report = report_data['data']
        
        if start_date and end_date:
            period_text = f"از {start_date} تا {end_date}"
        else:
            period_text = "کل دوره"
        
        report_message = (
            f"📊 *گزارش عملکرد مدیران پرداخت*\n"
            f"دوره: {period_text}\n\n"
            f"📋 *آمار کلی*:\n"
            f"تعداد کل پرداخت‌ها: {report['total_payments']}\n"
            f"تعداد تایید شده: {report['total_approved']}\n"
            f"تعداد رد شده: {report['total_rejected']}\n"
            f"نرخ تایید کلی: {report['overall_approval_rate']:.1f}%\n\n"
        )
        
        # Add individual admin performance
        report_message += "*🧑‍💼 عملکرد مدیران*:\n"
        
        for i, admin in enumerate(report['admin_metrics'], 1):
            # Create a summary for each admin
            admin_summary = (
                f"{i}. *{admin['admin_name']}*:\n"
                f"  • تعداد کل: {admin['total_processed']}\n"
                f"  • تایید شده: {admin['total_approved']}\n"
                f"  • رد شده: {admin['total_rejected']}\n"
                f"  • نرخ تایید: {admin['avg_approval_rate']:.1f}%\n"
                f"  • میانگین زمان پاسخ: {admin['avg_response_time_seconds']:.1f} ثانیه\n"
            )
            
            # Check if adding this would exceed message length
            if len(report_message + admin_summary) > 4000:
                report_message += "\n...و موارد بیشتر (گزارش بسیار طولانی است)"
                break
                
            report_message += admin_summary + "\n"
        
        # Create a keyboard for returning to reports menu
        keyboard = [
            [{"text": "🔙 بازگشت به منوی گزارشات", "callback_data": "admin_reports"}]
        ]
        
        await query.edit_message_text(
            report_message,
            reply_markup={"inline_keyboard": keyboard},
            parse_mode="Markdown"
        )
        
        return VIEWING_REPORT
        
    except Exception as e:
        logger.error(f"Error generating payment admin report: {e}")
        await query.edit_message_text(
            "❌ خطا در تهیه گزارش. لطفاً دوباره تلاش کنید.",
            reply_markup=get_admin_reports_keyboard()
        )
        return REPORTS_MENU

@superuser_only
async def handle_payment_admin_management(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the payment admin management menu."""
    query = update.callback_query
    if query:
        await query.answer()
    
    user_id = update.effective_user.id
    logger.info(f"User {user_id} accessed payment admin management")
    
    message = "👮‍♂️ مدیریت مدیران پرداخت\n\nلطفا یکی از گزینه‌های زیر را انتخاب کنید:"
    
    if query:
        await query.edit_message_text(
            message,
            reply_markup=get_payment_admin_management_keyboard()
        )
    else:
        await update.effective_message.reply_text(
            message,
            reply_markup=get_payment_admin_management_keyboard()
        )
    
    return PAYMENT_ADMIN_MENU

@superuser_only
async def handle_add_payment_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle adding a new payment admin."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    logger.info(f"User {user_id} selected add payment admin")
    
    # Clear previous data
    if 'new_payment_admin' in context.user_data:
        del context.user_data['new_payment_admin']
    
    # Initialize the new payment admin data
    context.user_data['new_payment_admin'] = {}
    
    # Get available users
    users = await get_users_available_for_payment_admin()
    
    if not users:
        await query.edit_message_text(
            "❌ هیچ کاربری برای افزودن به عنوان مدیر پرداخت یافت نشد یا خطایی رخ داده است.",
            reply_markup=get_payment_admin_management_keyboard()
        )
        return PAYMENT_ADMIN_MENU
    
    # Create a keyboard with user options
    keyboard = []
    for user in users:
        user_button = [InlineKeyboardButton(
            f"{user['first_name']} {user.get('last_name', '')} - @{user.get('username', 'بدون یوزرنیم')}",
            callback_data=f"admin_select_user_{user['id']}"
        )]
        keyboard.append(user_button)
    
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back_to_payment_admin_menu")])
    
    await query.edit_message_text(
        "👮‍♂️ افزودن مدیر پرداخت جدید\n\nلطفا کاربر مورد نظر را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return SELECTING_USER

@superuser_only
async def handle_select_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle user selection for payment admin."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = update.effective_user.id
    
    if data == "admin_back_to_payment_admin_menu":
        return await handle_payment_admin_management(update, context)
    
    # Extract selected user ID
    selected_user_id = int(data.split("_")[-1])
    logger.info(f"User {user_id} selected user ID {selected_user_id} for payment admin")
    
    # Store in context
    context.user_data['new_payment_admin']['user_id'] = selected_user_id
    
    # Now present bank card selection
    bank_cards = await get_bank_cards_for_payment()
    
    if not bank_cards:
        await query.edit_message_text(
            "❌ هیچ کارت بانکی فعالی یافت نشد یا خطایی رخ داده است.",
            reply_markup=get_payment_admin_management_keyboard()
        )
        return PAYMENT_ADMIN_MENU
    
    # Create a keyboard with bank card options
    keyboard = []
    for card in bank_cards:
        # Mask card number
        masked_number = f"**** **** **** {card['card_number'][-4:]}"
        card_button = [InlineKeyboardButton(
            f"{card['bank_name']} - {masked_number}",
            callback_data=f"admin_select_card_{card['id']}"
        )]
        keyboard.append(card_button)
    
    # Option to skip bank card assignment
    keyboard.append([InlineKeyboardButton("🚫 بدون تخصیص کارت", callback_data="admin_no_card")])
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back_to_user_selection")])
    
    await query.edit_message_text(
        "💳 تخصیص کارت به مدیر پرداخت\n\nلطفا کارت بانکی مورد نظر را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return SELECTING_BANK_CARD

@superuser_only
async def handle_select_card(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle bank card selection for payment admin."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = update.effective_user.id
    
    if data == "admin_back_to_user_selection":
        return await handle_add_payment_admin(update, context)
    
    if data == "admin_no_card":
        # No card assigned
        context.user_data['new_payment_admin']['bank_card_id'] = None
    else:
        # Extract selected card ID
        selected_card_id = int(data.split("_")[-1])
        logger.info(f"User {user_id} selected card ID {selected_card_id} for payment admin")
        context.user_data['new_payment_admin']['bank_card_id'] = selected_card_id
    
    # Now ask for Telegram group ID
    await query.edit_message_text(
        "🔖 تخصیص گروه تلگرام\n\n"
        "لطفا آیدی عددی گروه تلگرام را وارد کنید که مدیر پرداخت در آن اعلان‌ها را دریافت خواهد کرد.\n\n"
        "💡 *راهنما*: بات را به گروه اضافه کنید، سپس یک پیام ارسال کرده و آن را به بات فوروارد کنید تا آیدی گروه را ببینید."
        "\n\nبرای رد کردن این مرحله، عبارت 'رد' را وارد کنید.",
        parse_mode="Markdown"
    )
    
    return ENTERING_TELEGRAM_GROUP

@superuser_only
async def handle_telegram_group_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle Telegram group ID input for payment admin."""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    if text.lower() == 'رد' or text.lower() == 'skip':
        # Skip Telegram group assignment
        context.user_data['new_payment_admin']['telegram_group_id'] = None
    else:
        try:
            # Validate and store group ID
            group_id = text
            context.user_data['new_payment_admin']['telegram_group_id'] = group_id
            logger.info(f"User {user_id} entered Telegram group ID {group_id} for payment admin")
        except ValueError:
            await update.message.reply_text(
                "❌ آیدی گروه نامعتبر است. لطفا یک آیدی عددی معتبر وارد کنید یا 'رد' را بنویسید."
            )
            return ENTERING_TELEGRAM_GROUP
    
    # Create the payment admin assignment
    payment_admin_data = context.user_data['new_payment_admin']
    
    try:
        result = await create_payment_admin_assignment(
            user_id=payment_admin_data['user_id'],
            bank_card_id=payment_admin_data.get('bank_card_id'),
            telegram_group_id=payment_admin_data.get('telegram_group_id'),
            is_active=True
        )
        
        if result:
            success_message = (
                "✅ مدیر پرداخت با موفقیت اضافه شد!\n\n"
                f"🧑‍💼 شناسه کاربر: {payment_admin_data['user_id']}\n"
            )
            if payment_admin_data.get('bank_card_id'):
                success_message += f"💳 شناسه کارت: {payment_admin_data['bank_card_id']}\n"
            if payment_admin_data.get('telegram_group_id'):
                success_message += f"👥 آیدی گروه: {payment_admin_data['telegram_group_id']}\n"
            
            # Clear the context data
            del context.user_data['new_payment_admin']
            
            # Show success message with return option
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به مدیریت مدیران پرداخت", callback_data="admin_payment_admins")]
            ])
            
            await update.message.reply_text(success_message, reply_markup=keyboard)
            return PAYMENT_ADMIN_MENU
        else:
            await update.message.reply_text(
                "❌ خطا در ایجاد مدیر پرداخت. لطفا دوباره تلاش کنید.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_payment_admins")]
                ])
            )
            return PAYMENT_ADMIN_MENU
    
    except Exception as e:
        logger.error(f"Error creating payment admin: {e}")
        await update.message.reply_text(
            "❌ خطایی رخ داد. لطفا دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_payment_admins")]
            ])
        )
        return PAYMENT_ADMIN_MENU

@superuser_only
async def handle_list_payment_admins(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle listing payment admins."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    logger.info(f"User {user_id} requested to list payment admins")
    
    await query.edit_message_text(
        "🔄 در حال دریافت لیست مدیران پرداخت...",
    )
    
    # Get payment admin assignments
    assignments = await get_payment_admin_assignments()
    
    if not assignments:
        await query.edit_message_text(
            "❌ هیچ مدیر پرداختی یافت نشد یا خطایی رخ داده است.",
            reply_markup=get_payment_admin_management_keyboard()
        )
        return PAYMENT_ADMIN_MENU
    
    # Format the assignments into a readable message
    message = "📋 *لیست مدیران پرداخت*\n\n"
    
    for i, assignment in enumerate(assignments, 1):
        status = "✅ فعال" if assignment.get('is_active', False) else "❌ غیرفعال"
        admin_info = (
            f"{i}. *{assignment.get('user_name', 'بدون نام')}* - {status}\n"
        )
        
        if assignment.get('bank_card'):
            card = assignment['bank_card']
            masked_number = f"**** **** **** {card['card_number'][-4:]}"
            admin_info += f"   💳 کارت: {card['bank_name']} - {masked_number}\n"
        
        if assignment.get('telegram_group_id'):
            admin_info += f"   👥 گروه: {assignment['telegram_group_id']}\n"
        
        admin_info += "\n"
        
        if len(message + admin_info) > 4000:
            message += "\n...و موارد بیشتر (لیست بسیار طولانی است)"
            break
            
        message += admin_info
    
    # Add options for managing payment admins
    keyboard = [
        [InlineKeyboardButton("🔄 بروزرسانی مدیر", callback_data="admin_update_payment_admin")],
        [InlineKeyboardButton("❌ حذف مدیر", callback_data="admin_remove_payment_admin")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_payment_admins")]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    
    return VIEWING_PAYMENT_ADMINS

@admin_only
async def back_to_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Return to the main admin menu."""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "🏠 منوی اصلی مدیریت",
        reply_markup=get_admin_main_keyboard()
    )
    
    # End the conversation
    return ConversationHandler.END

@superuser_only
async def handle_update_payment_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle updating a payment admin assignment."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    logger.info(f"User {user_id} selected update payment admin")
    
    # Get payment admin assignments
    assignments = await get_payment_admin_assignments()
    
    if not assignments:
        await query.edit_message_text(
            "❌ هیچ مدیر پرداختی یافت نشد یا خطایی رخ داده است.",
            reply_markup=get_payment_admin_management_keyboard()
        )
        return PAYMENT_ADMIN_MENU
    
    # Create a keyboard with admin options
    keyboard = []
    for assignment in assignments:
        assignment_button = [InlineKeyboardButton(
            f"{assignment.get('user_name', 'بدون نام')} - {assignment.get('id')}",
            callback_data=f"admin_select_to_update_{assignment['id']}"
        )]
        keyboard.append(assignment_button)
    
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="admin_payment_admins")])
    
    await query.edit_message_text(
        "🔄 بروزرسانی مدیر پرداخت\n\nلطفا مدیر مورد نظر را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return SELECTING_ADMIN_TO_UPDATE

@superuser_only
async def handle_select_admin_to_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle selection of a payment admin to update."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = update.effective_user.id
    
    if data == "admin_payment_admins":
        return await handle_payment_admin_management(update, context)
    
    # Extract selected assignment ID
    selected_assignment_id = int(data.split("_")[-1])
    logger.info(f"User {user_id} selected assignment ID {selected_assignment_id} to update")
    
    # Store in context
    context.user_data['update_payment_admin'] = {'assignment_id': selected_assignment_id}
    
    # Get details for this assignment
    assignment = await get_payment_admin_assignment(selected_assignment_id)
    
    if not assignment:
        await query.edit_message_text(
            "❌ اطلاعات مدیر پرداخت یافت نشد یا خطایی رخ داده است.",
            reply_markup=get_payment_admin_management_keyboard()
        )
        return PAYMENT_ADMIN_MENU
    
    # Format assignment details
    status = "✅ فعال" if assignment.get('is_active', False) else "❌ غیرفعال"
    message = (
        f"ℹ️ *اطلاعات مدیر پرداخت*\n\n"
        f"👤 نام: {assignment.get('user_name', 'بدون نام')}\n"
        f"🆔 شناسه: {assignment.get('id')}\n"
        f"🔄 وضعیت: {status}\n"
    )
    
    if assignment.get('bank_card'):
        card = assignment['bank_card']
        masked_number = f"**** **** **** {card['card_number'][-4:]}"
        message += f"💳 کارت: {card['bank_name']} - {masked_number}\n"
    else:
        message += "💳 کارت: تعیین نشده\n"
    
    if assignment.get('telegram_group_id'):
        message += f"👥 گروه: {assignment['telegram_group_id']}\n"
    else:
        message += "👥 گروه: تعیین نشده\n"
    
    # Create a keyboard with update options
    keyboard = [
        [InlineKeyboardButton("💳 تغییر کارت", callback_data="admin_update_card")],
        [InlineKeyboardButton("👥 تغییر گروه", callback_data="admin_update_group")],
        [InlineKeyboardButton("🔄 تغییر وضعیت", callback_data="admin_toggle_status")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_payment_admins")]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    
    return SELECTING_UPDATE_FIELD

@superuser_only
async def handle_update_field_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle selection of which field to update for a payment admin."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = update.effective_user.id
    
    if data == "admin_payment_admins":
        return await handle_payment_admin_management(update, context)
    
    assignment_id = context.user_data.get('update_payment_admin', {}).get('assignment_id')
    if not assignment_id:
        await query.edit_message_text(
            "❌ خطا در دریافت اطلاعات. لطفا دوباره تلاش کنید.",
            reply_markup=get_payment_admin_management_keyboard()
        )
        return PAYMENT_ADMIN_MENU
    
    # Handle different field updates
    if data == "admin_update_card":
        # Present bank card selection
        bank_cards = await get_bank_cards_for_payment()
        
        if not bank_cards:
            await query.edit_message_text(
                "❌ هیچ کارت بانکی فعالی یافت نشد یا خطایی رخ داده است.",
                reply_markup=get_payment_admin_management_keyboard()
            )
            return PAYMENT_ADMIN_MENU
        
        # Create a keyboard with bank card options
        keyboard = []
        for card in bank_cards:
            # Mask card number
            masked_number = f"**** **** **** {card['card_number'][-4:]}"
            card_button = [InlineKeyboardButton(
                f"{card['bank_name']} - {masked_number}",
                callback_data=f"admin_update_to_card_{card['id']}"
            )]
            keyboard.append(card_button)
        
        # Option to remove bank card assignment
        keyboard.append([InlineKeyboardButton("🚫 حذف تخصیص کارت", callback_data="admin_remove_card")])
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back_to_update_selection")])
        
        await query.edit_message_text(
            "💳 تغییر کارت مدیر پرداخت\n\nلطفا کارت بانکی جدید را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        return UPDATING_CARD
    
    elif data == "admin_update_group":
        await query.edit_message_text(
            "🔖 تغییر گروه تلگرام\n\n"
            "لطفا آیدی عددی گروه تلگرام جدید را وارد کنید.\n\n"
            "💡 *راهنما*: بات را به گروه اضافه کنید، سپس یک پیام ارسال کرده و آن را به بات فوروارد کنید تا آیدی گروه را ببینید."
            "\n\nبرای حذف گروه فعلی، عبارت 'حذف' را وارد کنید.",
            parse_mode="Markdown"
        )
        
        return UPDATING_GROUP
    
    elif data == "admin_toggle_status":
        try:
            # Toggle the status
            assignment = await get_payment_admin_assignment(assignment_id)
            new_status = not assignment.get('is_active', True)
            
            result = await update_payment_admin_assignment(
                assignment_id=assignment_id,
                is_active=new_status
            )
            
            if result:
                status_text = "فعال" if new_status else "غیرفعال"
                await query.edit_message_text(
                    f"✅ وضعیت مدیر پرداخت با موفقیت به '{status_text}' تغییر یافت.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 بازگشت به مدیریت مدیران پرداخت", callback_data="admin_payment_admins")]
                    ])
                )
            else:
                await query.edit_message_text(
                    "❌ خطا در تغییر وضعیت مدیر پرداخت. لطفا دوباره تلاش کنید.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_payment_admins")]
                    ])
                )
            
            return PAYMENT_ADMIN_MENU
            
        except Exception as e:
            logger.error(f"Error toggling payment admin status: {e}")
            await query.edit_message_text(
                "❌ خطایی رخ داد. لطفا دوباره تلاش کنید.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_payment_admins")]
                ])
            )
            return PAYMENT_ADMIN_MENU
    
    # Default fallback
    return await handle_payment_admin_management(update, context)

@superuser_only
async def handle_update_card(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle updating the bank card for a payment admin."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = update.effective_user.id
    
    if data == "admin_back_to_update_selection":
        return await handle_select_admin_to_update(update, context)
    
    assignment_id = context.user_data.get('update_payment_admin', {}).get('assignment_id')
    if not assignment_id:
        await query.edit_message_text(
            "❌ خطا در دریافت اطلاعات. لطفا دوباره تلاش کنید.",
            reply_markup=get_payment_admin_management_keyboard()
        )
        return PAYMENT_ADMIN_MENU
    
    try:
        if data == "admin_remove_card":
            # Remove card assignment
            bank_card_id = None
        else:
            # Extract selected card ID
            bank_card_id = int(data.split("_")[-1])
            logger.info(f"User {user_id} selected card ID {bank_card_id} for payment admin")
        
        # Update the assignment
        result = await update_payment_admin_assignment(
            assignment_id=assignment_id,
            bank_card_id=bank_card_id
        )
        
        if result:
            card_text = "حذف شد" if bank_card_id is None else f"به شناسه {bank_card_id} تغییر یافت"
            await query.edit_message_text(
                f"✅ کارت بانکی مدیر پرداخت با موفقیت {card_text}.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت به مدیریت مدیران پرداخت", callback_data="admin_payment_admins")]
                ])
            )
        else:
            await query.edit_message_text(
                "❌ خطا در بروزرسانی کارت بانکی مدیر پرداخت. لطفا دوباره تلاش کنید.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_payment_admins")]
                ])
            )
        
        return PAYMENT_ADMIN_MENU
        
    except Exception as e:
        logger.error(f"Error updating payment admin card: {e}")
        await query.edit_message_text(
            "❌ خطایی رخ داد. لطفا دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_payment_admins")]
            ])
        )
        return PAYMENT_ADMIN_MENU

@superuser_only
async def handle_update_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle updating the telegram group for a payment admin."""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    assignment_id = context.user_data.get('update_payment_admin', {}).get('assignment_id')
    if not assignment_id:
        await update.message.reply_text(
            "❌ خطا در دریافت اطلاعات. لطفا دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_payment_admins")]
            ])
        )
        return PAYMENT_ADMIN_MENU
    
    try:
        if text.lower() == 'حذف' or text.lower() == 'remove':
            # Remove group assignment
            telegram_group_id = None
        else:
            # Validate and store group ID
            telegram_group_id = text
            logger.info(f"User {user_id} entered Telegram group ID {telegram_group_id} for payment admin")
        
        # Update the assignment
        result = await update_payment_admin_assignment(
            assignment_id=assignment_id,
            telegram_group_id=telegram_group_id
        )
        
        if result:
            group_text = "حذف شد" if telegram_group_id is None else f"به {telegram_group_id} تغییر یافت"
            await update.message.reply_text(
                f"✅ گروه تلگرام مدیر پرداخت با موفقیت {group_text}.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت به مدیریت مدیران پرداخت", callback_data="admin_payment_admins")]
                ])
            )
        else:
            await update.message.reply_text(
                "❌ خطا در بروزرسانی گروه تلگرام مدیر پرداخت. لطفا دوباره تلاش کنید.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_payment_admins")]
                ])
            )
        
        return PAYMENT_ADMIN_MENU
        
    except Exception as e:
        logger.error(f"Error updating payment admin group: {e}")
        await update.message.reply_text(
            "❌ خطایی رخ داد. لطفا دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_payment_admins")]
            ])
        )
        return PAYMENT_ADMIN_MENU

@superuser_only
async def handle_remove_payment_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle removing a payment admin assignment."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    logger.info(f"User {user_id} selected remove payment admin")
    
    # Get payment admin assignments
    assignments = await get_payment_admin_assignments()
    
    if not assignments:
        await query.edit_message_text(
            "❌ هیچ مدیر پرداختی یافت نشد یا خطایی رخ داده است.",
            reply_markup=get_payment_admin_management_keyboard()
        )
        return PAYMENT_ADMIN_MENU
    
    # Create a keyboard with admin options
    keyboard = []
    for assignment in assignments:
        assignment_button = [InlineKeyboardButton(
            f"{assignment.get('user_name', 'بدون نام')} - {assignment.get('id')}",
            callback_data=f"admin_confirm_delete_{assignment['id']}"
        )]
        keyboard.append(assignment_button)
    
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="admin_payment_admins")])
    
    await query.edit_message_text(
        "❌ حذف مدیر پرداخت\n\nلطفا مدیر مورد نظر برای حذف را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return CONFIRMING_DELETE

@superuser_only
async def handle_confirm_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle confirmation of payment admin deletion."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = update.effective_user.id
    
    if data == "admin_payment_admins":
        return await handle_payment_admin_management(update, context)
    
    # Extract selected assignment ID
    assignment_id = int(data.split("_")[-1])
    logger.info(f"User {user_id} selected assignment ID {assignment_id} to delete")
    
    # Get assignment details
    assignment = await get_payment_admin_assignment(assignment_id)
    
    if not assignment:
        await query.edit_message_text(
            "❌ اطلاعات مدیر پرداخت یافت نشد یا خطایی رخ داده است.",
            reply_markup=get_payment_admin_management_keyboard()
        )
        return PAYMENT_ADMIN_MENU
    
    # Create confirmation keyboard
    keyboard = [
        [InlineKeyboardButton("✅ بله، حذف شود", callback_data=f"admin_delete_{assignment_id}")],
        [InlineKeyboardButton("❌ خیر، انصراف", callback_data="admin_payment_admins")]
    ]
    
    await query.edit_message_text(
        f"⚠️ *تایید حذف مدیر پرداخت*\n\n"
        f"آیا از حذف مدیر پرداخت زیر اطمینان دارید؟\n\n"
        f"👤 نام: {assignment.get('user_name', 'بدون نام')}\n"
        f"🆔 شناسه: {assignment.get('id')}\n\n"
        "این عملیات غیرقابل بازگشت است.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    
    return CONFIRMING_DELETE

@superuser_only
async def handle_delete_payment_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle actual deletion of payment admin."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = update.effective_user.id
    
    if data == "admin_payment_admins":
        return await handle_payment_admin_management(update, context)
    
    # Extract assignment ID to delete
    assignment_id = int(data.split("_")[-1])
    logger.info(f"User {user_id} confirmed deletion of assignment ID {assignment_id}")
    
    try:
        # Delete the assignment
        result = await delete_payment_admin_assignment(assignment_id)
        
        if result:
            await query.edit_message_text(
                "✅ مدیر پرداخت با موفقیت حذف شد.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت به مدیریت مدیران پرداخت", callback_data="admin_payment_admins")]
                ])
            )
        else:
            await query.edit_message_text(
                "❌ خطا در حذف مدیر پرداخت. لطفا دوباره تلاش کنید.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_payment_admins")]
                ])
            )
        
        return PAYMENT_ADMIN_MENU
        
    except Exception as e:
        logger.error(f"Error deleting payment admin: {e}")
        await query.edit_message_text(
            "❌ خطایی رخ داد. لطفا دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_payment_admins")]
            ])
        )
        return PAYMENT_ADMIN_MENU

# Register the admin report handlers
def register_payment_admin_handlers(application):
    """Register all payment admin and report management handlers."""
    
    # Create a conversation handler for admin reports
    reports_conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(handle_admin_reports, pattern='^admin_reports$'),
        ],
        states={
            REPORTS_MENU: [
                CallbackQueryHandler(handle_payment_performance_report, pattern='^admin_payment_performance$'),
                CallbackQueryHandler(back_to_main_menu, pattern='^admin_back_to_main$'),
            ],
            REPORT_DATE_SELECTION: [
                CallbackQueryHandler(handle_report_date_selection, pattern='^report_'),
            ],
            VIEWING_REPORT: [
                CallbackQueryHandler(handle_admin_reports, pattern='^admin_reports$'),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(back_to_main_menu, pattern='^admin_back_to_main$'),
        ],
        name="admin_reports",
    )
    
    # Create a conversation handler for payment admin management
    payment_admin_conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(handle_payment_admin_management, pattern='^admin_payment_admins$'),
        ],
        states={
            PAYMENT_ADMIN_MENU: [
                CallbackQueryHandler(handle_add_payment_admin, pattern='^admin_add_payment_admin$'),
                CallbackQueryHandler(handle_list_payment_admins, pattern='^admin_list_payment_admins$'),
                CallbackQueryHandler(handle_update_payment_admin, pattern='^admin_update_payment_admin$'),
                CallbackQueryHandler(handle_remove_payment_admin, pattern='^admin_remove_payment_admin$'),
                CallbackQueryHandler(back_to_main_menu, pattern='^admin_back_to_main$'),
            ],
            SELECTING_USER: [
                CallbackQueryHandler(handle_select_user, pattern='^admin_select_user_|^admin_back_to_payment_admin_menu$'),
            ],
            SELECTING_BANK_CARD: [
                CallbackQueryHandler(handle_select_card, pattern='^admin_select_card_|^admin_no_card$|^admin_back_to_user_selection$'),
            ],
            ENTERING_TELEGRAM_GROUP: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_telegram_group_input),
            ],
            VIEWING_PAYMENT_ADMINS: [
                CallbackQueryHandler(handle_payment_admin_management, pattern='^admin_payment_admins$'),
                CallbackQueryHandler(handle_update_payment_admin, pattern='^admin_update_payment_admin$'),
                CallbackQueryHandler(handle_remove_payment_admin, pattern='^admin_remove_payment_admin$'),
            ],
            SELECTING_ADMIN_TO_UPDATE: [
                CallbackQueryHandler(handle_select_admin_to_update, pattern='^admin_select_to_update_'),
                CallbackQueryHandler(handle_payment_admin_management, pattern='^admin_payment_admins$'),
            ],
            SELECTING_UPDATE_FIELD: [
                CallbackQueryHandler(handle_update_field_selection, pattern='^admin_update_'),
                CallbackQueryHandler(handle_payment_admin_management, pattern='^admin_payment_admins$'),
            ],
            UPDATING_CARD: [
                CallbackQueryHandler(handle_update_card, pattern='^admin_update_to_card_|^admin_remove_card$|^admin_back_to_update_selection$'),
            ],
            UPDATING_GROUP: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_update_group),
            ],
            CONFIRMING_DELETE: [
                CallbackQueryHandler(handle_confirm_delete, pattern='^admin_confirm_delete_'),
                CallbackQueryHandler(handle_delete_payment_admin, pattern='^admin_delete_'),
                CallbackQueryHandler(handle_payment_admin_management, pattern='^admin_payment_admins$'),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(back_to_main_menu, pattern='^admin_back_to_main$'),
        ],
        name="payment_admin_management",
    )
    
    application.add_handler(reports_conv_handler)
    application.add_handler(payment_admin_conv_handler)

def get_payment_admin_handlers():
    """Return a list of all handlers related to payment admin functionality.
    
    This function is used by main.py to register all payment admin handlers.
    """
    return [
        # For now this is empty as we're registering handlers directly with register_payment_admin_handlers
        # Could add standalone handlers here in the future
    ]
