"""
Support ticket handlers for the V2Ray Telegram bot.

This module implements handlers for support ticket operations including:
- Creating new tickets
- Viewing ticket history
- Replying to tickets
- Managing ticket status
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from telegram.constants import ParseMode

from core.utils.i18n import get_text
from core.database import (
    create_ticket,
    get_ticket,
    update_ticket,
    get_user_tickets,
    get_all_tickets,
)
from core.utils.helpers import require_auth

logger = logging.getLogger(__name__)

# Conversation states
(
    SELECTING_ACTION,
    ENTERING_MESSAGE,
    SELECTING_TICKET,
    ENTERING_REPLY,
) = range(4)

# Callback data patterns
SUPPORT_CB = "support"
NEW_TICKET = f"{SUPPORT_CB}_new"
VIEW_TICKETS = f"{SUPPORT_CB}_view"
TICKET_DETAILS = f"{SUPPORT_CB}_ticket"
REPLY_TICKET = f"{SUPPORT_CB}_reply"
CLOSE_TICKET = f"{SUPPORT_CB}_close"

@require_auth
async def support_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show the support menu."""
    query = update.callback_query
    if query:
        await query.answer()
    
    user_id = update.effective_user.id
    language_code = context.user_data.get("language", "en")
    
    keyboard = [
        [
            InlineKeyboardButton(
                get_text("new_ticket", language_code),
                callback_data=NEW_TICKET
            ),
            InlineKeyboardButton(
                get_text("view_tickets", language_code),
                callback_data=VIEW_TICKETS
            ),
        ],
        [
            InlineKeyboardButton(
                get_text("back_to_menu", language_code),
                callback_data="menu"
            )
        ],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = get_text("support_menu", language_code)
    
    if query:
        await query.edit_message_text(text=text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text=text, reply_markup=reply_markup)
    
    return SELECTING_ACTION

@require_auth
async def new_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start creating a new support ticket."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    language_code = context.user_data.get("language", "en")
    
    text = get_text("enter_ticket_message", language_code)
    keyboard = [
        [
            InlineKeyboardButton(
                get_text("cancel", language_code),
                callback_data=SUPPORT_CB
            )
        ],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=text, reply_markup=reply_markup)
    
    return ENTERING_MESSAGE

@require_auth
async def save_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Save a new support ticket."""
    user_id = update.effective_user.id
    language_code = context.user_data.get("language", "en")
    message = update.message.text
    
    try:
        # Create new ticket
        ticket = create_ticket({
            "user_id": user_id,
            "message": message,
            "status": "open"
        })
        
        text = get_text("ticket_created", language_code).format(
            ticket_id=ticket["id"]
        )
        
        # Notify admins about new ticket
        # TODO: Implement admin notification
        
    except Exception as e:
        logger.error(f"Error creating ticket: {e}")
        text = get_text("ticket_error", language_code)
    
    keyboard = [
        [
            InlineKeyboardButton(
                get_text("back_to_support", language_code),
                callback_data=SUPPORT_CB
            )
        ],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text=text, reply_markup=reply_markup)
    
    return SELECTING_ACTION

@require_auth
async def view_tickets(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show list of user's tickets."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    language_code = context.user_data.get("language", "en")
    
    # Get user's tickets
    tickets = get_user_tickets(user_id)
    
    if not tickets:
        text = get_text("no_tickets", language_code)
    else:
        text = get_text("your_tickets", language_code) + "\n\n"
        keyboard = []
        
        for ticket in tickets:
            keyboard.append([
                InlineKeyboardButton(
                    f"#{ticket['id']} - {ticket['status']}",
                    callback_data=f"{TICKET_DETAILS}_{ticket['id']}"
                )
            ])
    
    keyboard.append([
        InlineKeyboardButton(
            get_text("new_ticket", language_code),
            callback_data=NEW_TICKET
        )
    ])
    keyboard.append([
        InlineKeyboardButton(
            get_text("back", language_code),
            callback_data=SUPPORT_CB
        )
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=text, reply_markup=reply_markup)
    
    return SELECTING_TICKET

@require_auth
async def ticket_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show ticket details and conversation."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    language_code = context.user_data.get("language", "en")
    
    # Extract ticket ID from callback data
    ticket_id = int(query.data.split("_")[-1])
    
    # Get ticket details
    ticket = get_ticket(ticket_id)
    if not ticket:
        text = get_text("ticket_not_found", language_code)
    else:
        text = get_text("ticket_details_template", language_code).format(
            id=ticket["id"],
            status=ticket["status"],
            created_at=ticket["created_at"],
            message=ticket["message"]
        )
        
        # Add conversation history
        if ticket["replies"]:
            text += "\n\n" + get_text("ticket_replies", language_code) + "\n"
            for reply in ticket["replies"]:
                text += get_text("reply_template", language_code).format(
                    sender="Admin" if reply["is_admin"] else "You",
                    message=reply["message"],
                    time=reply["created_at"]
                )
    
    keyboard = []
    if ticket["status"] == "open":
        keyboard.append([
            InlineKeyboardButton(
                get_text("reply", language_code),
                callback_data=f"{REPLY_TICKET}_{ticket_id}"
            )
        ])
        keyboard.append([
            InlineKeyboardButton(
                get_text("close_ticket", language_code),
                callback_data=f"{CLOSE_TICKET}_{ticket_id}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton(
            get_text("back_to_tickets", language_code),
            callback_data=VIEW_TICKETS
        )
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    
    return SELECTING_TICKET

@require_auth
async def reply_to_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start replying to a ticket."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    language_code = context.user_data.get("language", "en")
    
    # Extract ticket ID from callback data
    ticket_id = int(query.data.split("_")[-1])
    context.user_data["reply_to_ticket"] = ticket_id
    
    text = get_text("enter_reply", language_code)
    keyboard = [
        [
            InlineKeyboardButton(
                get_text("cancel", language_code),
                callback_data=f"{TICKET_DETAILS}_{ticket_id}"
            )
        ],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=text, reply_markup=reply_markup)
    
    return ENTERING_REPLY

@require_auth
async def save_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Save a reply to a ticket."""
    user_id = update.effective_user.id
    language_code = context.user_data.get("language", "en")
    message = update.message.text
    
    ticket_id = context.user_data.get("reply_to_ticket")
    if not ticket_id:
        text = get_text("reply_error", language_code)
        return SELECTING_ACTION
    
    try:
        # Add reply to ticket
        ticket = update_ticket(ticket_id, {
            "replies": [{
                "user_id": user_id,
                "message": message,
                "is_admin": False
            }]
        })
        
        text = get_text("reply_sent", language_code)
        
        # Notify admins about new reply
        # TODO: Implement admin notification
        
    except Exception as e:
        logger.error(f"Error saving reply: {e}")
        text = get_text("reply_error", language_code)
    
    keyboard = [
        [
            InlineKeyboardButton(
                get_text("view_ticket", language_code),
                callback_data=f"{TICKET_DETAILS}_{ticket_id}"
            )
        ],
        [
            InlineKeyboardButton(
                get_text("back_to_support", language_code),
                callback_data=SUPPORT_CB
            )
        ],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text=text, reply_markup=reply_markup)
    
    return SELECTING_ACTION

@require_auth
async def close_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Close a support ticket."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    language_code = context.user_data.get("language", "en")
    
    # Extract ticket ID from callback data
    ticket_id = int(query.data.split("_")[-1])
    
    try:
        # Update ticket status
        ticket = update_ticket(ticket_id, {"status": "closed"})
        text = get_text("ticket_closed", language_code)
    except Exception as e:
        logger.error(f"Error closing ticket: {e}")
        text = get_text("close_error", language_code)
    
    keyboard = [
        [
            InlineKeyboardButton(
                get_text("back_to_tickets", language_code),
                callback_data=VIEW_TICKETS
            )
        ],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=text, reply_markup=reply_markup)
    
    return SELECTING_ACTION

def get_support_handler() -> ConversationHandler:
    """Create and return the support conversation handler."""
    return ConversationHandler(
        entry_points=[
            CommandHandler("support", support_menu),
            CallbackQueryHandler(support_menu, pattern=f"^{SUPPORT_CB}$"),
        ],
        states={
            SELECTING_ACTION: [
                CallbackQueryHandler(new_ticket, pattern=f"^{NEW_TICKET}$"),
                CallbackQueryHandler(view_tickets, pattern=f"^{VIEW_TICKETS}$"),
            ],
            ENTERING_MESSAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, save_ticket),
                CallbackQueryHandler(support_menu, pattern=f"^{SUPPORT_CB}$"),
            ],
            SELECTING_TICKET: [
                CallbackQueryHandler(ticket_details, pattern=f"^{TICKET_DETAILS}_[0-9]+$"),
                CallbackQueryHandler(reply_to_ticket, pattern=f"^{REPLY_TICKET}_[0-9]+$"),
                CallbackQueryHandler(close_ticket, pattern=f"^{CLOSE_TICKET}_[0-9]+$"),
                CallbackQueryHandler(view_tickets, pattern=f"^{VIEW_TICKETS}$"),
            ],
            ENTERING_REPLY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, save_reply),
                CallbackQueryHandler(ticket_details, pattern=f"^{TICKET_DETAILS}_[0-9]+$"),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(support_menu, pattern="^menu$"),
        ],
        name="support",
        persistent=False,
        per_message=False
    ) 