"""
User Management for MoonVPN Telegram Bot Admin Panel.

This module provides the user management functionality,
allowing administrators to view, edit, and manage users.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, CommandHandler, ConversationHandler, MessageHandler, filters
from telegram.constants import ParseMode

from core.utils.i18n import get_text, format_number
from core.utils.helpers import require_admin
from models import User, VPNAccount, Transaction
from django.db.models import Sum, Count, Q

logger = logging.getLogger(__name__)

# Callback data prefixes
ADMIN_PREFIX = "admin"
USERS = f"{ADMIN_PREFIX}_users"
USER_VIEW = f"{USERS}_view"
USER_SEARCH = f"{USERS}_search"
USER_EDIT = f"{USERS}_edit"
USER_BAN = f"{USERS}_ban"
USER_UNBAN = f"{USERS}_unban"
USER_MAKE_ADMIN = f"{USERS}_make_admin"
USER_REMOVE_ADMIN = f"{USERS}_remove_admin"
DASHBOARD = f"{ADMIN_PREFIX}_dashboard"

# Conversation states
(
    WAITING_FOR_SEARCH,
    VIEWING_USER,
    EDITING_USER,
) = range(3)

@require_admin
async def user_management(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Display user management options and statistics."""
    user = update.effective_user
    user_id = user.id
    language_code = context.user_data.get("language", "en")
    
    logger.info(f"Admin {user_id} ({user.username}) accessed user management")
    
    # Get user statistics
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    banned_users = User.objects.filter(is_banned=True).count()
    admin_users = User.objects.filter(is_admin=True).count()
    
    # Get recently joined users (last 7 days)
    one_week_ago = datetime.datetime.now() - datetime.timedelta(days=7)
    new_users = User.objects.filter(created_at__gte=one_week_ago).count()
    
    # Create message
    message = f"👥 **{get_text('user_management', language_code)}**\n\n"
    message += f"📊 **{get_text('user_statistics', language_code)}**:\n"
    message += f"• {get_text('total_users', language_code)}: {total_users}\n"
    message += f"• {get_text('active_users', language_code)}: {active_users}\n"
    message += f"• {get_text('banned_users', language_code)}: {banned_users}\n"
    message += f"• {get_text('admin_users', language_code)}: {admin_users}\n"
    message += f"• {get_text('new_users_week', language_code)}: {new_users}\n\n"
    message += f"🔍 {get_text('select_action', language_code)}:"
    
    # Create keyboard
    keyboard = [
        [
            InlineKeyboardButton(
                f"🔍 {get_text('search_users', language_code)}",
                callback_data=USER_SEARCH
            ),
            InlineKeyboardButton(
                f"📋 {get_text('list_users', language_code)}",
                callback_data=f"{USERS}_list:1"
            )
        ],
        [
            InlineKeyboardButton(
                f"⭐ {get_text('top_users', language_code)}",
                callback_data=f"{USERS}_top"
            ),
            InlineKeyboardButton(
                f"🚫 {get_text('banned_users', language_code)}",
                callback_data=f"{USERS}_banned:1"
            )
        ],
        [
            InlineKeyboardButton(
                f"🔙 {get_text('back_to_dashboard', language_code)}",
                callback_data=DASHBOARD
            )
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send or edit message based on update type
    if update.callback_query:
        await update.callback_query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    return WAITING_FOR_SEARCH

async def handle_user_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle user search by ID or username."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    language_code = context.user_data.get("language", "en")
    
    # Create search message
    message = f"🔍 **{get_text('search_users', language_code)}**\n\n"
    message += get_text('search_user_instructions', language_code)
    
    # Create keyboard
    keyboard = [
        [
            InlineKeyboardButton(
                f"🔙 {get_text('back', language_code)}",
                callback_data=USERS
            )
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    
    return WAITING_FOR_SEARCH

async def process_user_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process user search by ID or username."""
    user = update.effective_user
    language_code = context.user_data.get("language", "en")
    
    # Get search query
    search_query = update.message.text.strip()
    
    try:
        # Try to search by ID first
        try:
            user_id = int(search_query)
            db_user = User.objects.filter(user_id=user_id).first()
        except ValueError:
            # If not an integer, search by username
            db_user = User.objects.filter(username__icontains=search_query).first()
        
        if not db_user:
            await update.message.reply_text(
                get_text('user_not_found', language_code),
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Return to user management
            return await user_management(update, context)
        
        # View user details
        return await view_user(update, context, db_user.id)
    
    except Exception as e:
        logger.error(f"Error searching user: {e}")
        await update.message.reply_text(
            get_text('error_general', language_code),
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Return to user management
        return await user_management(update, context)

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """List users with pagination."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    language_code = context.user_data.get("language", "en")
    
    # Get page number from callback data
    callback_data = query.data
    page = int(callback_data.split(":")[-1])
    
    # Users per page
    users_per_page = 10
    
    # Get users for current page
    start_idx = (page - 1) * users_per_page
    end_idx = start_idx + users_per_page
    
    users = User.objects.all().order_by('-created_at')[start_idx:end_idx]
    
    # Get total number of users
    total_users = User.objects.count()
    total_pages = (total_users + users_per_page - 1) // users_per_page
    
    # Create message
    message = f"👥 **{get_text('user_list', language_code)}**\n"
    message += f"{get_text('page', language_code)} {page}/{total_pages}\n\n"
    
    for idx, user in enumerate(users, start=1):
        account_count = VPNAccount.objects.filter(user=user, is_active=True).count()
        status = "🔴" if user.is_banned else "🟢"
        admin_badge = "👑 " if user.is_admin else ""
        
        message += f"{status} {admin_badge}*{user.first_name or 'User'}* (@{user.username or 'no_username'})\n"
        message += f"  • ID: `{user.user_id}`\n"
        message += f"  • {get_text('active_accounts', language_code)}: {account_count}\n"
        message += f"  • {get_text('joined', language_code)}: {user.created_at.strftime('%Y-%m-%d')}\n\n"
    
    # Create keyboard with pagination
    keyboard = []
    
    # Add pagination buttons
    pagination_row = []
    
    if page > 1:
        pagination_row.append(
            InlineKeyboardButton(
                "◀️",
                callback_data=f"{USERS}_list:{page-1}"
            )
        )
    
    if page < total_pages:
        pagination_row.append(
            InlineKeyboardButton(
                "▶️",
                callback_data=f"{USERS}_list:{page+1}"
            )
        )
    
    if pagination_row:
        keyboard.append(pagination_row)
    
    # Add back button
    keyboard.append([
        InlineKeyboardButton(
            f"🔙 {get_text('back', language_code)}",
            callback_data=USERS
        )
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    
    return WAITING_FOR_SEARCH

async def list_banned_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """List banned users with pagination."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    language_code = context.user_data.get("language", "en")
    
    # Get page number from callback data
    callback_data = query.data
    page = int(callback_data.split(":")[-1])
    
    # Users per page
    users_per_page = 10
    
    # Get banned users for current page
    start_idx = (page - 1) * users_per_page
    end_idx = start_idx + users_per_page
    
    banned_users = User.objects.filter(is_banned=True).order_by('-banned_at')[start_idx:end_idx]
    
    # Get total number of banned users
    total_banned = User.objects.filter(is_banned=True).count()
    total_pages = (total_banned + users_per_page - 1) // users_per_page
    
    # Create message
    message = f"🚫 **{get_text('banned_users', language_code)}**\n"
    
    if total_banned == 0:
        message += get_text('no_banned_users', language_code)
    else:
        message += f"{get_text('page', language_code)} {page}/{total_pages}\n\n"
        
        for idx, user in enumerate(banned_users, start=1):
            ban_date = user.banned_at.strftime('%Y-%m-%d') if user.banned_at else "Unknown"
            ban_reason = user.ban_reason or get_text('no_reason', language_code)
            
            message += f"🔴 *{user.first_name or 'User'}* (@{user.username or 'no_username'})\n"
            message += f"  • ID: `{user.user_id}`\n"
            message += f"  • {get_text('banned_on', language_code)}: {ban_date}\n"
            message += f"  • {get_text('reason', language_code)}: {ban_reason}\n\n"
    
    # Create keyboard with pagination
    keyboard = []
    
    # Add pagination buttons
    if total_banned > 0:
        pagination_row = []
        
        if page > 1:
            pagination_row.append(
                InlineKeyboardButton(
                    "◀️",
                    callback_data=f"{USERS}_banned:{page-1}"
                )
            )
        
        if page < total_pages:
            pagination_row.append(
                InlineKeyboardButton(
                    "▶️",
                    callback_data=f"{USERS}_banned:{page+1}"
                )
            )
        
        if pagination_row:
            keyboard.append(pagination_row)
    
    # Add back button
    keyboard.append([
        InlineKeyboardButton(
            f"🔙 {get_text('back', language_code)}",
            callback_data=USERS
        )
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    
    return WAITING_FOR_SEARCH

async def view_top_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """View top users by spending and accounts."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    language_code = context.user_data.get("language", "en")
    
    # Get top users by spending
    top_spenders = User.objects.annotate(
        total_spent=Sum('transaction__amount', filter=Q(transaction__status='completed'))
    ).filter(total_spent__gt=0).order_by('-total_spent')[:5]
    
    # Get top users by account count
    top_account_users = User.objects.annotate(
        account_count=Count('vpnaccount', filter=Q(vpnaccount__is_active=True))
    ).filter(account_count__gt=0).order_by('-account_count')[:5]
    
    # Create message
    message = f"⭐ **{get_text('top_users', language_code)}**\n\n"
    
    # Top spenders
    message += f"💰 **{get_text('top_spenders', language_code)}**:\n\n"
    
    if top_spenders:
        for idx, user in enumerate(top_spenders, start=1):
            spent = user.total_spent or 0
            message += f"{idx}. *{user.first_name or 'User'}* (@{user.username or 'no_username'})\n"
            message += f"   {format_number(spent)} {get_text('currency', language_code)}\n\n"
    else:
        message += get_text('no_data_available', language_code) + "\n\n"
    
    # Top account users
    message += f"🔑 **{get_text('top_account_users', language_code)}**:\n\n"
    
    if top_account_users:
        for idx, user in enumerate(top_account_users, start=1):
            account_count = user.account_count or 0
            message += f"{idx}. *{user.first_name or 'User'}* (@{user.username or 'no_username'})\n"
            message += f"   {account_count} {get_text('accounts', language_code)}\n\n"
    else:
        message += get_text('no_data_available', language_code) + "\n\n"
    
    # Create keyboard
    keyboard = [
        [
            InlineKeyboardButton(
                f"🔙 {get_text('back', language_code)}",
                callback_data=USERS
            )
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    
    return WAITING_FOR_SEARCH

async def view_user(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: Optional[int] = None) -> int:
    """View detailed information about a user."""
    language_code = context.user_data.get("language", "en")
    
    try:
        # Determine if we're coming from a callback query or direct function call
        if user_id is None:
            query = update.callback_query
            await query.answer()
            
            # Extract user ID from callback data
            callback_data = query.data
            user_id = int(callback_data.split(":")[-1])
        
        # Get user from database
        db_user = User.objects.get(id=user_id)
        
        # Get user statistics
        account_count = VPNAccount.objects.filter(user=db_user).count()
        active_account_count = VPNAccount.objects.filter(user=db_user, is_active=True).count()
        
        # Get transaction information
        total_spent = Transaction.objects.filter(
            user=db_user, 
            status='completed'
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        transaction_count = Transaction.objects.filter(user=db_user).count()
        
        # Create message
        message = f"👤 **{get_text('user_profile', language_code)}**\n\n"
        
        # User information
        admin_badge = "👑 " if db_user.is_admin else ""
        status = "🔴 " if db_user.is_banned else "🟢 "
        
        message += f"{status}{admin_badge}**{db_user.first_name or 'User'}** (@{db_user.username or 'no_username'})\n"
        message += f"🆔 ID: `{db_user.user_id}`\n"
        message += f"📅 {get_text('joined', language_code)}: {db_user.created_at.strftime('%Y-%m-%d')}\n"
        
        if db_user.is_banned:
            ban_date = db_user.banned_at.strftime('%Y-%m-%d') if db_user.banned_at else "Unknown"
            ban_reason = db_user.ban_reason or get_text('no_reason', language_code)
            message += f"🚫 {get_text('banned_on', language_code)}: {ban_date}\n"
            message += f"🚫 {get_text('reason', language_code)}: {ban_reason}\n"
        
        message += "\n"
        
        # Account information
        message += f"🔑 **{get_text('account_info', language_code)}**:\n"
        message += f"• {get_text('total_accounts', language_code)}: {account_count}\n"
        message += f"• {get_text('active_accounts', language_code)}: {active_account_count}\n\n"
        
        # Payment information
        message += f"💰 **{get_text('payment_info', language_code)}**:\n"
        message += f"• {get_text('total_spent', language_code)}: {format_number(total_spent)} {get_text('currency', language_code)}\n"
        message += f"• {get_text('transaction_count', language_code)}: {transaction_count}\n"
        
        # Create keyboard
        keyboard = []
        
        # Add user management buttons
        if db_user.is_banned:
            keyboard.append([
                InlineKeyboardButton(
                    f"✅ {get_text('unban_user', language_code)}",
                    callback_data=f"{USER_UNBAN}:{db_user.id}"
                )
            ])
        else:
            keyboard.append([
                InlineKeyboardButton(
                    f"🚫 {get_text('ban_user', language_code)}",
                    callback_data=f"{USER_BAN}:{db_user.id}"
                )
            ])
        
        if db_user.is_admin:
            keyboard.append([
                InlineKeyboardButton(
                    f"👑 {get_text('remove_admin', language_code)}",
                    callback_data=f"{USER_REMOVE_ADMIN}:{db_user.id}"
                )
            ])
        else:
            keyboard.append([
                InlineKeyboardButton(
                    f"👑 {get_text('make_admin', language_code)}",
                    callback_data=f"{USER_MAKE_ADMIN}:{db_user.id}"
                )
            ])
        
        # Add view account button if user has accounts
        if account_count > 0:
            keyboard.append([
                InlineKeyboardButton(
                    f"🔑 {get_text('view_user_accounts', language_code)}",
                    callback_data=f"{USERS}_accounts:{db_user.id}"
                )
            ])
        
        # Add back button
        keyboard.append([
            InlineKeyboardButton(
                f"🔙 {get_text('back', language_code)}",
                callback_data=USERS
            )
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send or edit message based on update type
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(
                message,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text(
                message,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
        
        return VIEWING_USER
    
    except User.DoesNotExist:
        # User not found
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(
                get_text('user_not_found', language_code),
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                            f"🔙 {get_text('back', language_code)}",
                            callback_data=USERS
                        )
                    ]
                ]),
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text(
                get_text('user_not_found', language_code),
                parse_mode=ParseMode.MARKDOWN
            )
        
        return WAITING_FOR_SEARCH
    
    except Exception as e:
        logger.error(f"Error viewing user: {e}")
        
        # Handle error
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(
                get_text('error_general', language_code),
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                            f"🔙 {get_text('back', language_code)}",
                            callback_data=USERS
                        )
                    ]
                ]),
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text(
                get_text('error_general', language_code),
                parse_mode=ParseMode.MARKDOWN
            )
        
        return WAITING_FOR_SEARCH

async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ban a user."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    language_code = context.user_data.get("language", "en")
    
    # Extract user ID from callback data
    callback_data = query.data
    user_id = int(callback_data.split(":")[-1])
    
    try:
        # Get user from database
        db_user = User.objects.get(id=user_id)
        
        # Check if user is already banned
        if db_user.is_banned:
            await query.answer(
                get_text('user_already_banned', language_code),
                show_alert=True
            )
            return await view_user(update, context, user_id)
        
        # Ban user
        db_user.is_banned = True
        db_user.banned_at = datetime.datetime.now()
        db_user.ban_reason = "Administrative action"
        db_user.save()
        
        # Log action
        logger.info(f"Admin {user.id} ({user.username}) banned user {db_user.user_id} ({db_user.username})")
        
        # Show success message
        await query.answer(
            get_text('user_banned_success', language_code),
            show_alert=True
        )
        
        # View updated user profile
        return await view_user(update, context, user_id)
    
    except User.DoesNotExist:
        await query.answer(
            get_text('user_not_found', language_code),
            show_alert=True
        )
        return WAITING_FOR_SEARCH
    
    except Exception as e:
        logger.error(f"Error banning user: {e}")
        await query.answer(
            get_text('error_general', language_code),
            show_alert=True
        )
        return WAITING_FOR_SEARCH

async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Unban a user."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    language_code = context.user_data.get("language", "en")
    
    # Extract user ID from callback data
    callback_data = query.data
    user_id = int(callback_data.split(":")[-1])
    
    try:
        # Get user from database
        db_user = User.objects.get(id=user_id)
        
        # Check if user is already unbanned
        if not db_user.is_banned:
            await query.answer(
                get_text('user_not_banned', language_code),
                show_alert=True
            )
            return await view_user(update, context, user_id)
        
        # Unban user
        db_user.is_banned = False
        db_user.banned_at = None
        db_user.ban_reason = None
        db_user.save()
        
        # Log action
        logger.info(f"Admin {user.id} ({user.username}) unbanned user {db_user.user_id} ({db_user.username})")
        
        # Show success message
        await query.answer(
            get_text('user_unbanned_success', language_code),
            show_alert=True
        )
        
        # View updated user profile
        return await view_user(update, context, user_id)
    
    except User.DoesNotExist:
        await query.answer(
            get_text('user_not_found', language_code),
            show_alert=True
        )
        return WAITING_FOR_SEARCH
    
    except Exception as e:
        logger.error(f"Error unbanning user: {e}")
        await query.answer(
            get_text('error_general', language_code),
            show_alert=True
        )
        return WAITING_FOR_SEARCH

async def make_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Make a user an admin."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    language_code = context.user_data.get("language", "en")
    
    # Extract user ID from callback data
    callback_data = query.data
    user_id = int(callback_data.split(":")[-1])
    
    try:
        # Get user from database
        db_user = User.objects.get(id=user_id)
        
        # Check if user is already an admin
        if db_user.is_admin:
            await query.answer(
                get_text('user_already_admin', language_code),
                show_alert=True
            )
            return await view_user(update, context, user_id)
        
        # Make user an admin
        db_user.is_admin = True
        db_user.save()
        
        # Log action
        logger.info(f"Admin {user.id} ({user.username}) made user {db_user.user_id} ({db_user.username}) an admin")
        
        # Show success message
        await query.answer(
            get_text('user_admin_success', language_code),
            show_alert=True
        )
        
        # View updated user profile
        return await view_user(update, context, user_id)
    
    except User.DoesNotExist:
        await query.answer(
            get_text('user_not_found', language_code),
            show_alert=True
        )
        return WAITING_FOR_SEARCH
    
    except Exception as e:
        logger.error(f"Error making user admin: {e}")
        await query.answer(
            get_text('error_general', language_code),
            show_alert=True
        )
        return WAITING_FOR_SEARCH

async def remove_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Remove admin status from a user."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    language_code = context.user_data.get("language", "en")
    
    # Extract user ID from callback data
    callback_data = query.data
    user_id = int(callback_data.split(":")[-1])
    
    try:
        # Get user from database
        db_user = User.objects.get(id=user_id)
        
        # Check if user is not an admin
        if not db_user.is_admin:
            await query.answer(
                get_text('user_not_admin', language_code),
                show_alert=True
            )
            return await view_user(update, context, user_id)
        
        # Remove admin status
        db_user.is_admin = False
        db_user.save()
        
        # Log action
        logger.info(f"Admin {user.id} ({user.username}) removed admin status from user {db_user.user_id} ({db_user.username})")
        
        # Show success message
        await query.answer(
            get_text('user_admin_removed_success', language_code),
            show_alert=True
        )
        
        # View updated user profile
        return await view_user(update, context, user_id)
    
    except User.DoesNotExist:
        await query.answer(
            get_text('user_not_found', language_code),
            show_alert=True
        )
        return WAITING_FOR_SEARCH
    
    except Exception as e:
        logger.error(f"Error removing admin status: {e}")
        await query.answer(
            get_text('error_general', language_code),
            show_alert=True
        )
        return WAITING_FOR_SEARCH

def get_user_management_handlers() -> List:
    """Get handlers for user management."""
    return [
        CallbackQueryHandler(user_management, pattern=f"^{USERS}$"),
        CallbackQueryHandler(handle_user_search, pattern=f"^{USER_SEARCH}$"),
        CallbackQueryHandler(list_users, pattern=f"^{USERS}_list:"),
        CallbackQueryHandler(list_banned_users, pattern=f"^{USERS}_banned:"),
        CallbackQueryHandler(view_top_users, pattern=f"^{USERS}_top$"),
        CallbackQueryHandler(view_user, pattern=f"^{USER_VIEW}:"),
        CallbackQueryHandler(ban_user, pattern=f"^{USER_BAN}:"),
        CallbackQueryHandler(unban_user, pattern=f"^{USER_UNBAN}:"),
        CallbackQueryHandler(make_admin, pattern=f"^{USER_MAKE_ADMIN}:"),
        CallbackQueryHandler(remove_admin, pattern=f"^{USER_REMOVE_ADMIN}:"),
        MessageHandler(filters.TEXT & ~filters.COMMAND, process_user_search),
    ] 