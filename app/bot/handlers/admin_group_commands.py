"""
Command handlers for admin group management in MoonVPN Telegram bot.

This module provides command handlers for managing admin groups and their members
through the Telegram bot interface.
"""

from typing import Dict, Any, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from app.core.database.session import get_db
from app.core.database.models.admin import AdminGroup, AdminGroupMember, AdminGroupType, NotificationLevel
from app.bot.utils.validators import (
    validate_group_type,
    validate_notification_level,
    validate_group_name,
    validate_group_description,
    validate_member_role,
    validate_member_notes,
    validate_user_id,
    validate_chat_id
)
from app.bot.utils.messages import (
    format_admin_group_info,
    format_admin_group_member_info,
    format_admin_group_list,
    format_admin_group_member_list,
    format_error_message,
    format_success_message,
    format_warning_message,
    format_info_message
)

# Conversation states
(
    CREATE_GROUP_NAME,
    CREATE_GROUP_TYPE,
    CREATE_GROUP_NOTIFICATION_LEVEL,
    CREATE_GROUP_DESCRIPTION,
    CREATE_GROUP_CHAT_ID,
    ADD_MEMBER_USER_ID,
    ADD_MEMBER_ROLE,
    ADD_MEMBER_NOTES,
    UPDATE_GROUP_FIELD,
    UPDATE_GROUP_VALUE,
    DELETE_GROUP_CONFIRM
) = range(11)

async def start_create_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the group creation process."""
    await update.message.reply_text(
        "📝 لطفاً نام گروه را وارد کنید:\n"
        "Please enter the group name:"
    )
    return CREATE_GROUP_NAME

async def handle_group_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the group name input."""
    name = update.message.text.strip()
    is_valid, error_msg = validate_group_name(name)
    
    if not is_valid:
        await update.message.reply_text(error_msg)
        return CREATE_GROUP_NAME
    
    context.user_data['group_name'] = name
    
    # Create keyboard for group type selection
    keyboard = [
        [InlineKeyboardButton(t.value, callback_data=f"type_{t.value}")]
        for t in AdminGroupType
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🏷️ لطفاً نوع گروه را انتخاب کنید:\n"
        "Please select the group type:",
        reply_markup=reply_markup
    )
    return CREATE_GROUP_TYPE

async def handle_group_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the group type selection."""
    query = update.callback_query
    await query.answer()
    
    group_type = query.data.split('_')[1]
    is_valid, error_msg = validate_group_type(group_type)
    
    if not is_valid:
        await query.message.reply_text(error_msg)
        return CREATE_GROUP_TYPE
    
    context.user_data['group_type'] = group_type
    
    # Create keyboard for notification level selection
    keyboard = [
        [InlineKeyboardButton(l.value, callback_data=f"level_{l.value}")]
        for l in NotificationLevel
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.reply_text(
        "🔔 لطفاً سطح اعلان را انتخاب کنید:\n"
        "Please select the notification level:",
        reply_markup=reply_markup
    )
    return CREATE_GROUP_NOTIFICATION_LEVEL

async def handle_notification_level(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the notification level selection."""
    query = update.callback_query
    await query.answer()
    
    level = query.data.split('_')[1]
    is_valid, error_msg = validate_notification_level(level)
    
    if not is_valid:
        await query.message.reply_text(error_msg)
        return CREATE_GROUP_NOTIFICATION_LEVEL
    
    context.user_data['notification_level'] = level
    
    await query.message.reply_text(
        "📄 لطفاً توضیحات گروه را وارد کنید (اختیاری):\n"
        "Please enter the group description (optional):"
    )
    return CREATE_GROUP_DESCRIPTION

async def handle_group_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the group description input."""
    description = update.message.text.strip()
    is_valid, error_msg = validate_group_description(description)
    
    if not is_valid:
        await update.message.reply_text(error_msg)
        return CREATE_GROUP_DESCRIPTION
    
    context.user_data['description'] = description
    
    await update.message.reply_text(
        "💬 لطفاً شناسه چت گروه را وارد کنید:\n"
        "Please enter the group chat ID:"
    )
    return CREATE_GROUP_CHAT_ID

async def handle_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the chat ID input and create the group."""
    chat_id = update.message.text.strip()
    is_valid, error_msg = validate_chat_id(chat_id)
    
    if not is_valid:
        await update.message.reply_text(error_msg)
        return CREATE_GROUP_CHAT_ID
    
    try:
        chat_id = int(chat_id)
        db = next(get_db())
        
        # Create the group
        group = AdminGroup(
            name=context.user_data['group_name'],
            type=context.user_data['group_type'],
            notification_level=context.user_data['notification_level'],
            description=context.user_data.get('description'),
            chat_id=chat_id,
            is_active=True
        )
        
        db.add(group)
        db.commit()
        db.refresh(group)
        
        # Format and send success message
        message = format_admin_group_info(group)
        await update.message.reply_text(
            message,
            parse_mode='HTML'
        )
        
        await update.message.reply_text(
            format_success_message(
                "گروه با موفقیت ایجاد شد.\n"
                "Group created successfully."
            ),
            parse_mode='HTML'
        )
        
    except Exception as e:
        await update.message.reply_text(
            format_error_message(e),
            parse_mode='HTML'
        )
    finally:
        db.close()
    
    return ConversationHandler.END

async def list_groups(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all admin groups."""
    try:
        db = next(get_db())
        groups = db.query(AdminGroup).all()
        
        if not groups:
            await update.message.reply_text(
                format_info_message(
                    "هیچ گروه ادمینی یافت نشد.\n"
                    "No admin groups found."
                ),
                parse_mode='HTML'
            )
            return
        
        message = format_admin_group_list(groups)
        await update.message.reply_text(
            message,
            parse_mode='HTML'
        )
        
    except Exception as e:
        await update.message.reply_text(
            format_error_message(e),
            parse_mode='HTML'
        )
    finally:
        db.close()

async def group_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show information about a specific admin group."""
    try:
        if not context.args:
            await update.message.reply_text(
                format_warning_message(
                    "لطفاً شناسه گروه را وارد کنید.\n"
                    "Please enter the group ID."
                ),
                parse_mode='HTML'
            )
            return
        
        group_id = context.args[0]
        if not group_id.isdigit():
            await update.message.reply_text(
                format_error_message(
                    "شناسه گروه باید عدد باشد.\n"
                    "Group ID must be a number."
                ),
                parse_mode='HTML'
            )
            return
        
        db = next(get_db())
        group = db.query(AdminGroup).filter(AdminGroup.id == int(group_id)).first()
        
        if not group:
            await update.message.reply_text(
                format_warning_message(
                    "گروه مورد نظر یافت نشد.\n"
                    "Group not found."
                ),
                parse_mode='HTML'
            )
            return
        
        message = format_admin_group_info(group)
        await update.message.reply_text(
            message,
            parse_mode='HTML'
        )
        
    except Exception as e:
        await update.message.reply_text(
            format_error_message(e),
            parse_mode='HTML'
        )
    finally:
        db.close()

async def start_add_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the member addition process."""
    try:
        if not context.args:
            await update.message.reply_text(
                format_warning_message(
                    "لطفاً شناسه گروه را وارد کنید.\n"
                    "Please enter the group ID."
                ),
                parse_mode='HTML'
            )
            return ConversationHandler.END
        
        group_id = context.args[0]
        if not group_id.isdigit():
            await update.message.reply_text(
                format_error_message(
                    "شناسه گروه باید عدد باشد.\n"
                    "Group ID must be a number."
                ),
                parse_mode='HTML'
            )
            return ConversationHandler.END
        
        db = next(get_db())
        group = db.query(AdminGroup).filter(AdminGroup.id == int(group_id)).first()
        
        if not group:
            await update.message.reply_text(
                format_warning_message(
                    "گروه مورد نظر یافت نشد.\n"
                    "Group not found."
                ),
                parse_mode='HTML'
            )
            return ConversationHandler.END
        
        context.user_data['group_id'] = group_id
        
        await update.message.reply_text(
            "🆔 لطفاً شناسه کاربر را وارد کنید:\n"
            "Please enter the user ID:"
        )
        return ADD_MEMBER_USER_ID
        
    except Exception as e:
        await update.message.reply_text(
            format_error_message(e),
            parse_mode='HTML'
        )
        return ConversationHandler.END
    finally:
        db.close()

async def handle_member_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the member user ID input."""
    user_id = update.message.text.strip()
    is_valid, error_msg = validate_user_id(user_id)
    
    if not is_valid:
        await update.message.reply_text(error_msg)
        return ADD_MEMBER_USER_ID
    
    context.user_data['user_id'] = user_id
    
    await update.message.reply_text(
        "👥 لطفاً نقش عضو را وارد کنید:\n"
        "Please enter the member role:"
    )
    return ADD_MEMBER_ROLE

async def handle_member_role(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the member role input."""
    role = update.message.text.strip()
    is_valid, error_msg = validate_member_role(role)
    
    if not is_valid:
        await update.message.reply_text(error_msg)
        return ADD_MEMBER_ROLE
    
    context.user_data['role'] = role
    
    await update.message.reply_text(
        "📝 لطفاً یادداشت‌ها را وارد کنید (اختیاری):\n"
        "Please enter the notes (optional):"
    )
    return ADD_MEMBER_NOTES

async def handle_member_notes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the member notes input and add the member."""
    notes = update.message.text.strip()
    is_valid, error_msg = validate_member_notes(notes)
    
    if not is_valid:
        await update.message.reply_text(error_msg)
        return ADD_MEMBER_NOTES
    
    try:
        db = next(get_db())
        
        # Create the member
        member = AdminGroupMember(
            group_id=context.user_data['group_id'],
            user_id=context.user_data['user_id'],
            role=context.user_data['role'],
            notes=notes if notes else None,
            is_active=True,
            added_by={"user_id": update.effective_user.id}
        )
        
        db.add(member)
        db.commit()
        db.refresh(member)
        
        # Format and send success message
        message = format_admin_group_member_info(member)
        await update.message.reply_text(
            message,
            parse_mode='HTML'
        )
        
        await update.message.reply_text(
            format_success_message(
                "عضو با موفقیت به گروه اضافه شد.\n"
                "Member added successfully."
            ),
            parse_mode='HTML'
        )
        
    except Exception as e:
        await update.message.reply_text(
            format_error_message(e),
            parse_mode='HTML'
        )
    finally:
        db.close()
    
    return ConversationHandler.END

async def list_members(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all members of a specific admin group."""
    try:
        if not context.args:
            await update.message.reply_text(
                format_warning_message(
                    "لطفاً شناسه گروه را وارد کنید.\n"
                    "Please enter the group ID."
                ),
                parse_mode='HTML'
            )
            return
        
        group_id = context.args[0]
        if not group_id.isdigit():
            await update.message.reply_text(
                format_error_message(
                    "شناسه گروه باید عدد باشد.\n"
                    "Group ID must be a number."
                ),
                parse_mode='HTML'
            )
            return
        
        db = next(get_db())
        members = db.query(AdminGroupMember).filter(
            AdminGroupMember.group_id == int(group_id)
        ).all()
        
        if not members:
            await update.message.reply_text(
                format_info_message(
                    "هیچ عضوی در این گروه یافت نشد.\n"
                    "No members found in this group."
                ),
                parse_mode='HTML'
            )
            return
        
        message = format_admin_group_member_list(members)
        await update.message.reply_text(
            message,
            parse_mode='HTML'
        )
        
    except Exception as e:
        await update.message.reply_text(
            format_error_message(e),
            parse_mode='HTML'
        )
    finally:
        db.close()

async def remove_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Remove a member from an admin group."""
    try:
        if len(context.args) < 2:
            await update.message.reply_text(
                format_warning_message(
                    "لطفاً شناسه گروه و شناسه کاربر را وارد کنید.\n"
                    "Please enter the group ID and user ID."
                ),
                parse_mode='HTML'
            )
            return
        
        group_id, user_id = context.args[:2]
        if not group_id.isdigit() or not user_id.isdigit():
            await update.message.reply_text(
                format_error_message(
                    "شناسه‌ها باید عدد باشند.\n"
                    "IDs must be numbers."
                ),
                parse_mode='HTML'
            )
            return
        
        db = next(get_db())
        member = db.query(AdminGroupMember).filter(
            AdminGroupMember.group_id == int(group_id),
            AdminGroupMember.user_id == int(user_id)
        ).first()
        
        if not member:
            await update.message.reply_text(
                format_warning_message(
                    "عضو مورد نظر یافت نشد.\n"
                    "Member not found."
                ),
                parse_mode='HTML'
            )
            return
        
        # Delete the member
        db.delete(member)
        db.commit()
        
        await update.message.reply_text(
            format_success_message(
                "عضو با موفقیت از گروه حذف شد.\n"
                "Member removed successfully."
            ),
            parse_mode='HTML'
        )
        
    except Exception as e:
        await update.message.reply_text(
            format_error_message(e),
            parse_mode='HTML'
        )
    finally:
        db.close()

async def start_update_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the group update process."""
    try:
        if not context.args:
            await update.message.reply_text(
                format_warning_message(
                    "لطفاً شناسه گروه را وارد کنید.\n"
                    "Please enter the group ID."
                ),
                parse_mode='HTML'
            )
            return ConversationHandler.END
        
        group_id = context.args[0]
        if not group_id.isdigit():
            await update.message.reply_text(
                format_error_message(
                    "شناسه گروه باید عدد باشد.\n"
                    "Group ID must be a number."
                ),
                parse_mode='HTML'
            )
            return ConversationHandler.END
        
        db = next(get_db())
        group = db.query(AdminGroup).filter(AdminGroup.id == int(group_id)).first()
        
        if not group:
            await update.message.reply_text(
                format_warning_message(
                    "گروه مورد نظر یافت نشد.\n"
                    "Group not found."
                ),
                parse_mode='HTML'
            )
            return ConversationHandler.END
        
        context.user_data['group_id'] = group_id
        
        # Create keyboard for field selection
        keyboard = [
            [InlineKeyboardButton(field, callback_data=f"field_{field}")]
            for field in ['name', 'type', 'notification_level', 'description', 'is_active']
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🔄 لطفاً فیلد مورد نظر برای بروزرسانی را انتخاب کنید:\n"
            "Please select the field to update:",
            reply_markup=reply_markup
        )
        return UPDATE_GROUP_FIELD
        
    except Exception as e:
        await update.message.reply_text(
            format_error_message(e),
            parse_mode='HTML'
        )
        return ConversationHandler.END
    finally:
        db.close()

async def handle_update_field(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the field selection for group update."""
    query = update.callback_query
    await query.answer()
    
    field = query.data.split('_')[1]
    context.user_data['update_field'] = field
    
    if field == 'is_active':
        # Create keyboard for boolean selection
        keyboard = [
            [
                InlineKeyboardButton("فعال / Active", callback_data="value_true"),
                InlineKeyboardButton("غیرفعال / Inactive", callback_data="value_false")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.reply_text(
            "🔄 لطفاً وضعیت جدید را انتخاب کنید:\n"
            "Please select the new status:",
            reply_markup=reply_markup
        )
    else:
        await query.message.reply_text(
            f"📝 لطفاً مقدار جدید را برای فیلد {field} وارد کنید:\n"
            f"Please enter the new value for field {field}:"
        )
    
    return UPDATE_GROUP_VALUE

async def handle_update_value(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the value input for group update."""
    field = context.user_data['update_field']
    
    if field == 'is_active':
        query = update.callback_query
        await query.answer()
        value = query.data.split('_')[1]
    else:
        value = update.message.text.strip()
    
    # Validate the value based on the field
    is_valid, error_msg = validate_group_update_value(field, value)
    
    if not is_valid:
        if field == 'is_active':
            await query.message.reply_text(error_msg)
        else:
            await update.message.reply_text(error_msg)
        return UPDATE_GROUP_VALUE
    
    try:
        db = next(get_db())
        group = db.query(AdminGroup).filter(
            AdminGroup.id == context.user_data['group_id']
        ).first()
        
        if not group:
            if field == 'is_active':
                await query.message.reply_text(
                    format_warning_message(
                        "گروه مورد نظر یافت نشد.\n"
                        "Group not found."
                    ),
                    parse_mode='HTML'
                )
            else:
                await update.message.reply_text(
                    format_warning_message(
                        "گروه مورد نظر یافت نشد.\n"
                        "Group not found."
                    ),
                    parse_mode='HTML'
                )
            return ConversationHandler.END
        
        # Update the field
        if field == 'is_active':
            group.is_active = value == 'true'
        else:
            setattr(group, field, value)
        
        db.commit()
        db.refresh(group)
        
        # Format and send success message
        message = format_admin_group_info(group)
        if field == 'is_active':
            await query.message.reply_text(
                message,
                parse_mode='HTML'
            )
            await query.message.reply_text(
                format_success_message(
                    "گروه با موفقیت بروزرسانی شد.\n"
                    "Group updated successfully."
                ),
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text(
                message,
                parse_mode='HTML'
            )
            await update.message.reply_text(
                format_success_message(
                    "گروه با موفقیت بروزرسانی شد.\n"
                    "Group updated successfully."
                ),
                parse_mode='HTML'
            )
        
    except Exception as e:
        if field == 'is_active':
            await query.message.reply_text(
                format_error_message(e),
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text(
                format_error_message(e),
                parse_mode='HTML'
            )
    finally:
        db.close()
    
    return ConversationHandler.END

async def start_delete_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the group deletion process."""
    try:
        if not context.args:
            await update.message.reply_text(
                format_warning_message(
                    "لطفاً شناسه گروه را وارد کنید.\n"
                    "Please enter the group ID."
                ),
                parse_mode='HTML'
            )
            return ConversationHandler.END
        
        group_id = context.args[0]
        if not group_id.isdigit():
            await update.message.reply_text(
                format_error_message(
                    "شناسه گروه باید عدد باشد.\n"
                    "Group ID must be a number."
                ),
                parse_mode='HTML'
            )
            return ConversationHandler.END
        
        db = next(get_db())
        group = db.query(AdminGroup).filter(AdminGroup.id == int(group_id)).first()
        
        if not group:
            await update.message.reply_text(
                format_warning_message(
                    "گروه مورد نظر یافت نشد.\n"
                    "Group not found."
                ),
                parse_mode='HTML'
            )
            return ConversationHandler.END
        
        context.user_data['group_id'] = group_id
        
        # Create keyboard for confirmation
        keyboard = [
            [
                InlineKeyboardButton("بله / Yes", callback_data="delete_yes"),
                InlineKeyboardButton("خیر / No", callback_data="delete_no")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "⚠️ آیا از حذف این گروه اطمینان دارید؟\n"
            "Are you sure you want to delete this group?",
            reply_markup=reply_markup
        )
        return DELETE_GROUP_CONFIRM
        
    except Exception as e:
        await update.message.reply_text(
            format_error_message(e),
            parse_mode='HTML'
        )
        return ConversationHandler.END
    finally:
        db.close()

async def handle_delete_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the group deletion confirmation."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "delete_no":
        await query.message.reply_text(
            format_info_message(
                "عملیات حذف گروه لغو شد.\n"
                "Group deletion cancelled."
            ),
            parse_mode='HTML'
        )
        return ConversationHandler.END
    
    try:
        db = next(get_db())
        group = db.query(AdminGroup).filter(
            AdminGroup.id == context.user_data['group_id']
        ).first()
        
        if not group:
            await query.message.reply_text(
                format_warning_message(
                    "گروه مورد نظر یافت نشد.\n"
                    "Group not found."
                ),
                parse_mode='HTML'
            )
            return ConversationHandler.END
        
        # Delete the group
        db.delete(group)
        db.commit()
        
        await query.message.reply_text(
            format_success_message(
                "گروه با موفقیت حذف شد.\n"
                "Group deleted successfully."
            ),
            parse_mode='HTML'
        )
        
    except Exception as e:
        await query.message.reply_text(
            format_error_message(e),
            parse_mode='HTML'
        )
    finally:
        db.close()
    
    return ConversationHandler.END

def register_handlers(application) -> None:
    """Register all admin group command handlers."""
    # Create group conversation handler
    create_group_handler = ConversationHandler(
        entry_points=[CommandHandler('creategroup', start_create_group)],
        states={
            CREATE_GROUP_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_group_name)],
            CREATE_GROUP_TYPE: [CallbackQueryHandler(handle_group_type)],
            CREATE_GROUP_NOTIFICATION_LEVEL: [CallbackQueryHandler(handle_notification_level)],
            CREATE_GROUP_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_group_description)],
            CREATE_GROUP_CHAT_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_chat_id)]
        },
        fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)]
    )
    
    # Add member conversation handler
    add_member_handler = ConversationHandler(
        entry_points=[CommandHandler('addmember', start_add_member)],
        states={
            ADD_MEMBER_USER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_member_user_id)],
            ADD_MEMBER_ROLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_member_role)],
            ADD_MEMBER_NOTES: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_member_notes)]
        },
        fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)]
    )
    
    # Update group conversation handler
    update_group_handler = ConversationHandler(
        entry_points=[CommandHandler('updategroup', start_update_group)],
        states={
            UPDATE_GROUP_FIELD: [CallbackQueryHandler(handle_update_field)],
            UPDATE_GROUP_VALUE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_update_value),
                CallbackQueryHandler(handle_update_value)
            ]
        },
        fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)]
    )
    
    # Delete group conversation handler
    delete_group_handler = ConversationHandler(
        entry_points=[CommandHandler('deletegroup', start_delete_group)],
        states={
            DELETE_GROUP_CONFIRM: [CallbackQueryHandler(handle_delete_confirmation)]
        },
        fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)]
    )
    
    # Register all handlers
    application.add_handler(create_group_handler)
    application.add_handler(add_member_handler)
    application.add_handler(update_group_handler)
    application.add_handler(delete_group_handler)
    application.add_handler(CommandHandler('listgroups', list_groups))
    application.add_handler(CommandHandler('groupinfo', group_info))
    application.add_handler(CommandHandler('listmembers', list_members))
    application.add_handler(CommandHandler('removemember', remove_member)) 