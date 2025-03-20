"""
Main Telegram bot application for MoonVPN.

This module contains the main bot application class that handles all bot functionality,
including command handlers, conversation handlers, and callback handlers.
"""

import logging
from typing import Optional, Dict, Any, List
from telegram import Update, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)
from telegram.error import TelegramError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import verify_telegram_request
from app.models.user import User
from app.services.vpn import VPNService
from app.services.payment import PaymentService
from app.services.notification import NotificationService
from app.bot.handlers.admin.group_handlers import AdminGroupHandlers
from app.bot.handlers.admin.register_handlers import register_admin_handlers

# Setup logging
logger = logging.getLogger(__name__)

# Conversation states
(
    REGISTER,
    PURCHASE_PLAN,
    PURCHASE_PAYMENT,
    SUPPORT_TICKET,
    ADMIN_BROADCAST,
    ADMIN_USER_MANAGEMENT,
) = range(6)

class MoonVPNBot:
    """Main bot application class."""
    
    def __init__(self, token: str, db: Session):
        """Initialize the bot application."""
        self.token = token
        self.db = db
        self.application = Application.builder().token(token).build()
        self.application.bot_data["db"] = db
        self.vpn_service = VPNService()
        self.payment_service = PaymentService()
        self.notification_service = NotificationService()
        
        # Setup handlers
        self._setup_handlers()
        
        # Setup error handler
        self.application.add_error_handler(self._error_handler)
    
    def _setup_handlers(self) -> None:
        """Setup all command and conversation handlers."""
        # Register admin group handlers
        admin_group_handlers = AdminGroupHandlers(self.db)
        for handler in admin_group_handlers.get_handlers():
            self.application.add_handler(handler)

        # Register other admin handlers
        register_admin_handlers(self.application)
        
        # Command handlers
        self.application.add_handler(CommandHandler("start", self._start_command))
        self.application.add_handler(CommandHandler("help", self._help_command))
        self.application.add_handler(CommandHandler("status", self._status_command))
        self.application.add_handler(CommandHandler("register", self._register_command))
        self.application.add_handler(CommandHandler("purchase", self._purchase_command))
        self.application.add_handler(CommandHandler("support", self._support_command))
        
        # Conversation handlers
        self.application.add_handler(
            ConversationHandler(
                entry_points=[CommandHandler("register", self._register_command)],
                states={
                    REGISTER: [
                        MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_register)
                    ]
                },
                fallbacks=[CommandHandler("cancel", self._cancel_command)]
            )
        )
        
        self.application.add_handler(
            ConversationHandler(
                entry_points=[CommandHandler("purchase", self._purchase_command)],
                states={
                    PURCHASE_PLAN: [
                        CallbackQueryHandler(self._handle_purchase_plan)
                    ],
                    PURCHASE_PAYMENT: [
                        CallbackQueryHandler(self._handle_purchase_payment)
                    ]
                },
                fallbacks=[CommandHandler("cancel", self._cancel_command)]
            )
        )
        
        self.application.add_handler(
            ConversationHandler(
                entry_points=[CommandHandler("support", self._support_command)],
                states={
                    SUPPORT_TICKET: [
                        MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_support_ticket)
                    ]
                },
                fallbacks=[CommandHandler("cancel", self._cancel_command)]
            )
        )
        
        # Callback query handlers
        self.application.add_handler(CallbackQueryHandler(self._handle_callback_query))
    
    def _update_bot_commands(self) -> None:
        """Update the bot's command list."""
        commands = [
            # Basic user commands
            ("start", "Start the bot"),
            ("help", "Show help information"),
            ("settings", "Configure your settings"),
            
            # Admin group management commands
            ("create_group", "Create a new admin group"),
            ("list_groups", "List all admin groups"),
            ("group_info", "Get information about a specific group"),
            ("add_member", "Add a member to an admin group"),
            ("remove_member", "Remove a member from an admin group"),
            ("list_members", "List all members of a group"),
            ("update_group", "Update an admin group's information"),
            ("delete_group", "Delete an admin group"),
            
            # Other admin commands
            ("admin", "Access admin panel"),
            ("broadcast", "Send a broadcast message"),
            ("users", "Manage users"),
            ("server_status", "Check server status"),
            ("system_health", "Check system health"),
            ("admin_stats", "View admin statistics"),
            ("daily_report", "Get daily report"),
            ("performance_report", "Get performance report"),
            ("usage_report", "Get usage report"),
            ("error_logs", "View error logs"),
            ("user_logs", "View user logs"),
            ("system_logs", "View system logs"),
            ("transaction_stats", "View transaction statistics"),
            ("payment_report", "Get payment report"),
            ("refund_requests", "View refund requests"),
            ("outage_status", "Check outage status"),
            ("maintenance_schedule", "View maintenance schedule"),
            ("incident_report", "Get incident report"),
            ("seller_stats", "View seller statistics"),
            ("commission_report", "Get commission report"),
            ("partner_status", "Check partner status"),
            ("backup_status", "Check backup status"),
            ("backup_schedule", "View backup schedule"),
            ("restore_points", "View restore points")
        ]
        
        self.application.bot.set_my_commands(commands)
    
    async def _start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /start command."""
        user = update.effective_user
        await update.message.reply_text(
            f"Welcome to MoonVPN, {user.first_name}! 🚀\n\n"
            "I'm here to help you manage your VPN subscription and provide support.\n"
            "Use /help to see available commands."
        )
    
    async def _help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /help command."""
        help_text = (
            "Available commands:\n\n"
            "/start - Start the bot\n"
            "/help - Show this help message\n"
            "/status - Check your VPN status\n"
            "/register - Register a new account\n"
            "/purchase - Purchase a VPN subscription\n"
            "/support - Get support\n"
            "/cancel - Cancel current operation\n\n"
            "Admin commands:\n"
            "/admin - Admin panel\n"
            "/broadcast - Send broadcast message\n"
            "/users - User management"
        )
        await update.message.reply_text(help_text)
    
    async def _status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /status command."""
        user = update.effective_user
        try:
            status = await self.vpn_service.get_user_status(user.id)
            await update.message.reply_text(
                f"Your VPN Status:\n\n"
                f"Subscription: {status['subscription']}\n"
                f"Expires: {status['expires']}\n"
                f"Active: {status['active']}\n"
                f"Data Used: {status['data_used']}"
            )
        except Exception as e:
            logger.error(f"Error getting status for user {user.id}: {e}")
            await update.message.reply_text(
                "Sorry, I couldn't get your VPN status at the moment. "
                "Please try again later or contact support."
            )
    
    async def _register_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle the /register command."""
        user = update.effective_user
        await update.message.reply_text(
            "Please enter your email address to complete registration:"
        )
        return REGISTER
    
    async def _handle_register(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle registration email input."""
        user = update.effective_user
        email = update.message.text
        
        try:
            await self.vpn_service.register_user(user.id, email)
            await update.message.reply_text(
                "Registration successful! 🎉\n"
                "You can now use /purchase to get a VPN subscription."
            )
            return ConversationHandler.END
        except Exception as e:
            logger.error(f"Error registering user {user.id}: {e}")
            await update.message.reply_text(
                "Sorry, there was an error during registration. "
                "Please try again or contact support."
            )
            return ConversationHandler.END
    
    async def _purchase_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle the /purchase command."""
        keyboard = [
            [
                InlineKeyboardButton("1 Month - $9.99", callback_data="plan_1"),
                InlineKeyboardButton("3 Months - $24.99", callback_data="plan_3")
            ],
            [
                InlineKeyboardButton("6 Months - $44.99", callback_data="plan_6"),
                InlineKeyboardButton("12 Months - $79.99", callback_data="plan_12")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "Select a subscription plan:",
            reply_markup=reply_markup
        )
        return PURCHASE_PLAN
    
    async def _handle_purchase_plan(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle plan selection."""
        query = update.callback_query
        await query.answer()
        
        plan_id = query.data.split("_")[1]
        context.user_data["selected_plan"] = plan_id
        
        keyboard = [
            [InlineKeyboardButton("Pay with Zarinpal", callback_data="payment_zarinpal")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "Select payment method:",
            reply_markup=reply_markup
        )
        return PURCHASE_PAYMENT
    
    async def _handle_purchase_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle payment method selection."""
        query = update.callback_query
        await query.answer()
        
        user = update.effective_user
        plan_id = context.user_data["selected_plan"]
        
        try:
            payment_url = await self.payment_service.create_payment(user.id, plan_id)
            await query.edit_message_text(
                f"Please click the link below to complete your payment:\n\n{payment_url}"
            )
            return ConversationHandler.END
        except Exception as e:
            logger.error(f"Error creating payment for user {user.id}: {e}")
            await query.edit_message_text(
                "Sorry, there was an error creating your payment. "
                "Please try again or contact support."
            )
            return ConversationHandler.END
    
    async def _support_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle the /support command."""
        await update.message.reply_text(
            "Please describe your issue or question:"
        )
        return SUPPORT_TICKET
    
    async def _handle_support_ticket(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle support ticket creation."""
        user = update.effective_user
        message = update.message.text
        
        try:
            ticket_id = await self.notification_service.create_support_ticket(user.id, message)
            await update.message.reply_text(
                f"Support ticket created successfully! 🎫\n"
                f"Ticket ID: {ticket_id}\n"
                "Our support team will get back to you soon."
            )
            return ConversationHandler.END
        except Exception as e:
            logger.error(f"Error creating support ticket for user {user.id}: {e}")
            await update.message.reply_text(
                "Sorry, there was an error creating your support ticket. "
                "Please try again or contact support directly."
            )
            return ConversationHandler.END
    
    async def _handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle callback queries."""
        query = update.callback_query
        await query.answer()
        
        if query.data.startswith("admin_"):
            await self._handle_admin_callback(query)
    
    async def _handle_admin_callback(self, query: CallbackQuery) -> None:
        """Handle admin panel callback queries."""
        user = query.from_user
        if user.id not in settings.TELEGRAM_BOT_ADMIN_IDS:
            await query.edit_message_text("Sorry, you don't have access to this feature.")
            return
        
        action = query.data.split("_")[1]
        
        if action == "broadcast":
            await query.edit_message_text(
                "Please enter the message you want to broadcast:"
            )
            return ADMIN_BROADCAST
        elif action == "users":
            await self._users_command(update, context)
        elif action == "status":
            status = await self.vpn_service.get_system_status()
            await query.edit_message_text(
                f"System Status:\n\n"
                f"Active Users: {status['active_users']}\n"
                f"Total Users: {status['total_users']}\n"
                f"System Load: {status['system_load']}\n"
                f"Uptime: {status['uptime']}"
            )
        elif action == "stats":
            stats = await self.vpn_service.get_system_stats()
            await query.edit_message_text(
                f"System Statistics:\n\n"
                f"Total Traffic: {stats['total_traffic']}\n"
                f"Active Connections: {stats['active_connections']}\n"
                f"Revenue: ${stats['revenue']}\n"
                f"New Users Today: {stats['new_users_today']}"
            )
    
    async def _error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle errors in the bot."""
        logger.error(f"Update {update} caused error: {context.error}")
        
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "Sorry, something went wrong. Please try again later or contact support."
            )
    
    async def start(self) -> None:
        """Start the bot."""
        self._setup_handlers()
        await self._update_bot_commands()
        await self.application.initialize()
        await self.application.start()
        await self.application.run_polling()
    
    async def stop(self) -> None:
        """Stop the bot."""
        await self.application.stop()
        await self.application.shutdown()

    async def _users_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /users command."""
        user = update.effective_user
        if user.id not in settings.TELEGRAM_BOT_ADMIN_IDS:
            await update.message.reply_text("Sorry, you don't have access to this command.")
            return
        
        try:
            users = await self.vpn_service.get_all_users()
            message = "User List:\n\n"
            for user in users:
                message += f"ID: {user.id}\n"
                message += f"Username: @{user.username}\n"
                message += f"Status: {user.status}\n"
                message += f"Expires: {user.expires}\n\n"
            
            await update.message.reply_text(message)
        except Exception as e:
            logger.error(f"Error getting users list: {e}")
            await update.message.reply_text(
                "Sorry, there was an error getting the users list. "
                "Please try again later."
            ) 