"""
Admin Dashboard for MoonVPN Telegram Bot.

This module provides the admin dashboard functionality,
allowing administrators to manage and control all aspects of the bot.
"""

import logging
from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime, timedelta

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram.ext import ContextTypes, CallbackQueryHandler, CommandHandler, MessageHandler
from telegram.constants import ParseMode

from core.utils.i18n import get_text
from core.utils.helpers import require_admin
from core.config import settings
from core.database import get_db
from core.models.feature_flag import FeatureFlag
from core.models.system_config import SystemConfig
from core.models.user import User
from core.models.vpn_account import VPNAccount
from core.models.transaction import Transaction
from core.database import get_system_stats
from core.utils.helpers import get_all_servers_health
from core.models.server import Server

logger = logging.getLogger(__name__)

# Callback data prefixes
ADMIN_PREFIX = "admin"
DASHBOARD = f"{ADMIN_PREFIX}_dashboard"
FEATURES = f"{ADMIN_PREFIX}_features"
USERS = f"{ADMIN_PREFIX}_users"
SERVERS = f"{ADMIN_PREFIX}_servers"
PAYMENTS = f"{ADMIN_PREFIX}_payments"
SETTINGS = f"{ADMIN_PREFIX}_settings"
REPORTS = f"{ADMIN_PREFIX}_reports"
BACK = f"{ADMIN_PREFIX}_back"

@require_admin
async def admin_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display the admin dashboard with various management options."""
    user = update.effective_user
    user_id = user.id
    language_code = context.user_data.get("language", "en")
    
    logger.info(f"Admin {user_id} ({user.username}) accessed the dashboard")
    
    # Get system stats
    stats = await get_system_stats()
    user_count = stats.get("user_count", 0)
    active_account_count = stats.get("active_account_count", 0)
    server_count = stats.get("server_count", 0)
    pending_payments = stats.get("pending_payments", 0)
    
    # Create dashboard message
    _ = get_text(language_code)
    
    # Check server health
    server_health = await get_all_servers_health()
    servers_online = server_health["online"]
    servers_total = server_health["total"]
    server_status = "🟢" if servers_online == servers_total else "🟠" if servers_online > 0 else "🔴"
    
    message = _(f"🧰 **Admin Dashboard**\n\n"
                f"👤 Users: {user_count}\n"
                f"🔑 Active Accounts: {active_account_count}\n"
                f"{server_status} Servers: {servers_online}/{servers_total} online\n"
                f"💲 Pending Payments: {pending_payments}\n\n"
                f"Select an option:")
    
    # Create keyboard
    keyboard = [
        [
            InlineKeyboardButton(_("👤 Users"), callback_data=f"{USERS}_list"),
            InlineKeyboardButton(_("🖥️ Servers"), callback_data="server_action_list")
        ],
        [
            InlineKeyboardButton(_("💰 Payments"), callback_data=f"{PAYMENTS}_list"),
            InlineKeyboardButton(_("📊 Reports"), callback_data=REPORTS)
        ],
        [
            InlineKeyboardButton(_("⚙️ Settings"), callback_data=SETTINGS),
            InlineKeyboardButton(_("🎛️ Features"), callback_data=FEATURES)
        ],
        [
            InlineKeyboardButton(_("👥 Groups"), callback_data=f"{ADMIN_PREFIX}_groups"),
            InlineKeyboardButton(_("🔔 Announcements"), callback_data=f"{ADMIN_PREFIX}_announce")
        ]
    ]
    
    # Add maintenance mode button
    maintenance_mode = await SystemConfig.get_value("maintenance_mode", "false") == "true"
    maintenance_btn_text = _("🔴 Exit Maintenance") if maintenance_mode else _("🟠 Enter Maintenance")
    keyboard.append([InlineKeyboardButton(maintenance_btn_text, callback_data=f"{ADMIN_PREFIX}_toggle_maintenance")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send or edit message
    if update.callback_query:
        await update.callback_query.answer()
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

async def handle_feature_management(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display and manage feature toggles."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    language_code = context.user_data.get("language", "en")
    
    # Get all feature flags
    features = FeatureFlag.objects.all()
    if not features.exists():
        # Create default feature flags if none exist
        default_features = [
            {"name": "subscription_purchase", "display_name": "Subscription Purchase", "enabled": True, "description": "Allow users to purchase subscriptions"},
            {"name": "server_change", "display_name": "Server Change", "enabled": True, "description": "Allow users to change server locations"},
            {"name": "support_tickets", "display_name": "Support Tickets", "enabled": True, "description": "Enable support ticket system"},
            {"name": "referral_system", "display_name": "Referral System", "enabled": True, "description": "Enable referral bonus system"},
            {"name": "zarinpal_payment", "display_name": "Zarinpal Payment", "enabled": False, "description": "Enable Zarinpal payment method"},
            {"name": "card_payment", "display_name": "Card Payment", "enabled": True, "description": "Enable card-to-card payment method"},
            {"name": "notification_system", "display_name": "Notification System", "enabled": True, "description": "Enable user notifications"},
            {"name": "theme_customization", "display_name": "Theme Customization", "enabled": True, "description": "Allow users to customize theme"}
        ]
        
        for feature in default_features:
            FeatureFlag.objects.create(
                name=feature["name"],
                display_name=feature["display_name"],
                enabled=feature["enabled"],
                description=feature["description"]
            )
        
        features = FeatureFlag.objects.all()
    
    # Create feature management message
    feature_message = f"⚙️ **{get_text('feature_management', language_code)}**\n\n"
    
    # Create keyboard with feature toggles
    keyboard = []
    
    for feature in features:
        status_emoji = "✅" if feature.enabled else "❌"
        button_text = f"{status_emoji} {feature.display_name}"
        keyboard.append([
            InlineKeyboardButton(
                button_text,
                callback_data=f"{FEATURES}_toggle:{feature.name}"
            )
        ])
    
    # Add back button
    keyboard.append([
        InlineKeyboardButton(
            get_text("back_to_dashboard", language_code),
            callback_data=DASHBOARD
        )
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        feature_message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )

async def toggle_feature(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Toggle a feature flag."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    language_code = context.user_data.get("language", "en")
    
    # Extract feature name from callback data
    callback_data = query.data
    feature_name = callback_data.split(":")[-1]
    
    # Toggle feature
    try:
        feature = FeatureFlag.objects.get(name=feature_name)
        feature.enabled = not feature.enabled
        feature.save()
        
        if feature.enabled:
            await query.answer(f"{feature.display_name} {get_text('enabled', language_code)}", show_alert=True)
        else:
            await query.answer(f"{feature.display_name} {get_text('disabled', language_code)}", show_alert=True)
    except FeatureFlag.DoesNotExist:
        logger.error(f"Feature {feature_name} not found")
        await query.answer(f"{get_text('feature_not_found', language_code)}", show_alert=True)
    
    # Return to feature management
    await handle_feature_management(update, context)

async def handle_server_management(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display and manage servers."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    language_code = context.user_data.get("language", "en")
    
    # Get server info from database
    servers = Server.objects.all()
    
    # Check server health (for active servers)
    server_health = await get_all_servers_health()
    
    # Create server management message
    server_message = f"🖥️ **{get_text('server_management', language_code)}**\n\n"
    
    if not servers.exists():
        server_message += get_text("no_servers", language_code)
    else:
        for server in servers:
            # Get health status
            health = server_health.get(server.id, {})
            
            # Status indicators
            status_emoji = "🟢" if server.is_active else "🔴"
            online_status = "🟢" if health.get("online", False) else "🔴"
            
            server_message += f"{status_emoji} **{server.name}** ({server.location})\n"
            server_message += f"  • IP/Address: `{server.address}`\n"
            server_message += f"  • {get_text('active_accounts', language_code)}: {server.account_set.filter(is_active=True).count()}\n"
            server_message += f"  • {get_text('status', language_code)}: {get_text('active' if server.is_active else 'disabled', language_code)}\n"
            
            # Add health information if server is active
            if server.is_active:
                server_message += f"  • {get_text('online_status', language_code)}: {online_status}\n"
                
                if health.get("online", False):
                    server_message += f"  • {get_text('latency', language_code)}: {health.get('latency', 0)}ms\n"
                    server_message += f"  • CPU: {health.get('cpu_usage', 0)}%\n"
                    server_message += f"  • {get_text('memory', language_code)}: {health.get('memory_usage', 0)}%\n"
                elif health.get("error"):
                    server_message += f"  • {get_text('error', language_code)}: {health.get('error')}\n"
            
            server_message += "\n"
    
    # Create keyboard
    keyboard = [
        [
            InlineKeyboardButton(
                f"➕ {get_text('add_server', language_code)}",
                callback_data=f"{SERVERS}_add"
            ),
            InlineKeyboardButton(
                f"🔄 {get_text('refresh', language_code)}",
                callback_data=f"{SERVERS}_refresh"
            )
        ]
    ]
    
    # Add toggle buttons for each server
    for server in servers:
        action = "disable" if server.is_active else "enable"
        keyboard.append([
            InlineKeyboardButton(
                f"{'🔴' if server.is_active else '🟢'} {get_text(f'{action}_server', language_code)}: {server.name}",
                callback_data=f"{SERVERS}_toggle:{server.id}"
            )
        ])
    
    # Add back button
    keyboard.append([
        InlineKeyboardButton(
            get_text("back_to_dashboard", language_code),
            callback_data=DASHBOARD
        )
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        server_message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )

async def add_server(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle add server request."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    language_code = context.user_data.get("language", "en")
    
    # Save state to mark we're adding a server
    context.user_data["adding_server"] = True
    
    # Create form message
    message = f"➕ **{get_text('add_server', language_code)}**\n\n"
    message += f"{get_text('server_add_instructions', language_code)}\n\n"
    message += f"```\nServer Name\nLocation\nAddress/IP\nPort\nUsername\nPassword\n```\n\n"
    message += f"{get_text('example', language_code)}:\n"
    message += f"```\nGermany VPN\nFrankfurt\n185.162.x.x\n2053\nadmin\npassword123\n```"
    
    # Create keyboard with only back button
    keyboard = [
        [
            InlineKeyboardButton(
                f"🔙 {get_text('back', language_code)}",
                callback_data=f"{SERVERS}"
            )
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send form message
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )

async def process_server_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process server addition from user input."""
    # Check if we're in server adding state
    if not context.user_data.get("adding_server", False):
        return
    
    user = update.effective_user
    language_code = context.user_data.get("language", "en")
    
    # Get server info from text message
    lines = update.message.text.strip().split('\n')
    
    if len(lines) < 3:
        await update.message.reply_text(
            f"❌ {get_text('invalid_server_format', language_code)}",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    try:
        # Extract server details
        name = lines[0].strip()
        location = lines[1].strip()
        address = lines[2].strip()
        
        # Optional fields
        port = lines[3].strip() if len(lines) > 3 else "2053"
        username = lines[4].strip() if len(lines) > 4 else "admin"
        password = lines[5].strip() if len(lines) > 5 else ""
        
        # Create new server
        server = Server.objects.create(
            name=name,
            location=location,
            address=address,
            port=port,
            username=username,
            password=password,
            is_active=True
        )
        
        # Log action
        logger.info(f"Admin {user.id} ({user.username}) added new server: {name}")
        
        # Clear server adding state
        context.user_data.pop("adding_server", None)
        
        # Send success message
        await update.message.reply_text(
            f"✅ **{get_text('server_added_success', language_code)}**\n\n"
            f"{get_text('server_name', language_code)}: {name}\n"
            f"{get_text('server_location', language_code)}: {location}\n"
            f"{get_text('server_address', language_code)}: {address}",
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Redirect back to server management
        query_message = await update.message.reply_text(
            f"🔄 {get_text('redirecting', language_code)}...",
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Create fake callback query to reuse handler
        fake_update = Update(0, callback_query=CallbackQuery(0, user.to_dict(), chat_instance="0", data=SERVERS, message=query_message))
        await handle_server_management(fake_update, context)
        
    except Exception as e:
        logger.error(f"Error adding server: {e}")
        await update.message.reply_text(
            f"❌ {get_text('error_adding_server', language_code)}: {str(e)}",
            parse_mode=ParseMode.MARKDOWN
        )

async def toggle_server(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Toggle a server's active status."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    language_code = context.user_data.get("language", "en")
    
    # Extract server ID from callback data
    callback_data = query.data
    server_id = int(callback_data.split(":")[-1])
    
    # Toggle server
    try:
        server = Server.objects.get(id=server_id)
        server.is_active = not server.is_active
        server.save()
        
        if server.is_active:
            await query.answer(f"{server.name} {get_text('enabled', language_code)}", show_alert=True)
        else:
            await query.answer(f"{server.name} {get_text('disabled', language_code)}", show_alert=True)
    except Server.DoesNotExist:
        logger.error(f"Server {server_id} not found")
        await query.answer(f"{get_text('server_not_found', language_code)}", show_alert=True)
    
    # Return to server management
    await handle_server_management(update, context)

async def handle_payment_management(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display and manage payment settings and pending payments."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    language_code = context.user_data.get("language", "en")
    
    # Get system config
    system_config, created = SystemConfig.objects.get_or_create(id=1)
    
    # Get pending payments
    pending_payments = Transaction.objects.filter(status="pending_verification").count()
    
    # Create payment management message
    payment_message = f"💰 **{get_text('payment_management', language_code)}**\n\n"
    
    # Add payment methods info
    payment_message += f"**{get_text('payment_methods', language_code)}**:\n"
    
    # Card payment
    card_status = get_text("enabled", language_code) if system_config.card_payment_enabled else get_text("disabled", language_code)
    payment_message += f"💳 {get_text('card_payment', language_code)}: {card_status}\n"
    if system_config.card_payment_enabled:
        payment_message += f"  • {get_text('card_number', language_code)}: `{system_config.card_number}`\n"
        payment_message += f"  • {get_text('card_holder', language_code)}: {system_config.card_holder}\n"
        payment_message += f"  • {get_text('min_amount', language_code)}: {system_config.min_payment_amount} {get_text('currency', language_code)}\n"
    
    # Zarinpal payment
    zarinpal_status = get_text("enabled", language_code) if system_config.zarinpal_enabled else get_text("disabled", language_code)
    payment_message += f"🔵 {get_text('zarinpal_payment', language_code)}: {zarinpal_status}\n"
    
    # Pending payments
    payment_message += f"\n**{get_text('pending_payments', language_code)}**: {pending_payments}\n"
    
    # Create keyboard
    keyboard = [
        [
            InlineKeyboardButton(
                f"{'❌' if system_config.card_payment_enabled else '✅'} {get_text('toggle_card_payment', language_code)}",
                callback_data=f"{PAYMENTS}_toggle_card"
            )
        ],
        [
            InlineKeyboardButton(
                f"{'❌' if system_config.zarinpal_enabled else '✅'} {get_text('toggle_zarinpal', language_code)}",
                callback_data=f"{PAYMENTS}_toggle_zarinpal"
            )
        ]
    ]
    
    # Add update card info button if card payment is enabled
    if system_config.card_payment_enabled:
        keyboard.append([
            InlineKeyboardButton(
                f"✏️ {get_text('update_card_info', language_code)}",
                callback_data=f"{PAYMENTS}_update_card"
            )
        ])
    
    # Add view pending payments button if there are pending payments
    if pending_payments > 0:
        keyboard.append([
            InlineKeyboardButton(
                f"👁️ {get_text('view_pending_payments', language_code)} ({pending_payments})",
                callback_data=f"{PAYMENTS}_pending"
            )
        ])
    
    # Add back button
    keyboard.append([
        InlineKeyboardButton(
            get_text("back_to_dashboard", language_code),
            callback_data=DASHBOARD
        )
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        payment_message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )

async def toggle_payment_method(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Toggle a payment method."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    language_code = context.user_data.get("language", "en")
    
    # Extract payment method from callback data
    callback_data = query.data
    payment_method = callback_data.split("_")[-1]
    
    # Toggle payment method
    system_config, created = SystemConfig.objects.get_or_create(id=1)
    
    if payment_method == "card":
        system_config.card_payment_enabled = not system_config.card_payment_enabled
        status_msg = get_text("enabled", language_code) if system_config.card_payment_enabled else get_text("disabled", language_code)
        await query.answer(f"{get_text('card_payment', language_code)} {status_msg}", show_alert=True)
    elif payment_method == "zarinpal":
        system_config.zarinpal_enabled = not system_config.zarinpal_enabled
        status_msg = get_text("enabled", language_code) if system_config.zarinpal_enabled else get_text("disabled", language_code)
        await query.answer(f"{get_text('zarinpal_payment', language_code)} {status_msg}", show_alert=True)
    
    system_config.save()
    
    # Return to payment management
    await handle_payment_management(update, context)

async def handle_bot_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display and manage bot settings."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    language_code = context.user_data.get("language", "en")
    
    # Get system config
    system_config, created = SystemConfig.objects.get_or_create(id=1)
    
    # Create bot settings message
    settings_message = f"📝 **{get_text('bot_settings', language_code)}**\n\n"
    
    # Add settings info
    settings_message += f"**{get_text('general_settings', language_code)}**:\n"
    
    # Maintenance mode
    maintenance_status = get_text("enabled", language_code) if system_config.maintenance_mode else get_text("disabled", language_code)
    settings_message += f"🔧 {get_text('maintenance_mode', language_code)}: {maintenance_status}\n"
    
    # Default language
    default_language = system_config.default_language or "en"
    language_name = get_text(f"language_{default_language}", language_code)
    settings_message += f"🌐 {get_text('default_language', language_code)}: {language_name}\n"
    
    # Support contact
    support_contact = system_config.support_contact or get_text("not_set", language_code)
    settings_message += f"📞 {get_text('support_contact', language_code)}: {support_contact}\n"
    
    # Bot name
    bot_name = system_config.bot_name or "MoonVPN"
    settings_message += f"🤖 {get_text('bot_name', language_code)}: {bot_name}\n"
    
    # Create keyboard
    keyboard = [
        [
            InlineKeyboardButton(
                f"{'❌' if system_config.maintenance_mode else '✅'} {get_text('toggle_maintenance', language_code)}",
                callback_data=f"{SETTINGS}_toggle_maintenance"
            )
        ],
        [
            InlineKeyboardButton(
                f"✏️ {get_text('update_support_contact', language_code)}",
                callback_data=f"{SETTINGS}_update_support"
            ),
            InlineKeyboardButton(
                f"✏️ {get_text('update_bot_name', language_code)}",
                callback_data=f"{SETTINGS}_update_name"
            )
        ],
        [
            InlineKeyboardButton(
                f"🌐 {get_text('set_default_language', language_code)}",
                callback_data=f"{SETTINGS}_set_language"
            )
        ],
        [
            InlineKeyboardButton(
                get_text("back_to_dashboard", language_code),
                callback_data=DASHBOARD
            )
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        settings_message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )

async def toggle_maintenance_mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Toggle maintenance mode."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    language_code = context.user_data.get("language", "en")
    
    # Toggle maintenance mode
    system_config, created = SystemConfig.objects.get_or_create(id=1)
    system_config.maintenance_mode = not system_config.maintenance_mode
    system_config.save()
    
    status_msg = get_text("enabled", language_code) if system_config.maintenance_mode else get_text("disabled", language_code)
    await query.answer(f"{get_text('maintenance_mode', language_code)} {status_msg}", show_alert=True)
    
    # Return to bot settings
    await handle_bot_settings(update, context)

async def handle_reports(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display reports and statistics."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    language_code = context.user_data.get("language", "en")
    
    # Get statistics
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    total_accounts = VPNAccount.objects.count()
    active_accounts = VPNAccount.objects.filter(is_active=True).count()
    expired_accounts = VPNAccount.objects.filter(is_active=False).count()
    
    # Revenue stats
    from django.db.models import Sum
    total_transactions = Transaction.objects.filter(status="completed").count()
    total_revenue = Transaction.objects.filter(status="completed").aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Create reports message
    reports_message = f"📊 **{get_text('reports_and_statistics', language_code)}**\n\n"
    
    # User stats
    reports_message += f"**{get_text('user_statistics', language_code)}**:\n"
    reports_message += f"👥 {get_text('total_users', language_code)}: {total_users}\n"
    reports_message += f"👤 {get_text('active_users', language_code)}: {active_users}\n\n"
    
    # Account stats
    reports_message += f"**{get_text('account_statistics', language_code)}**:\n"
    reports_message += f"🌐 {get_text('total_accounts', language_code)}: {total_accounts}\n"
    reports_message += f"✅ {get_text('active_accounts', language_code)}: {active_accounts}\n"
    reports_message += f"❌ {get_text('expired_accounts', language_code)}: {expired_accounts}\n\n"
    
    # Revenue stats
    reports_message += f"**{get_text('revenue_statistics', language_code)}**:\n"
    reports_message += f"💰 {get_text('total_transactions', language_code)}: {total_transactions}\n"
    reports_message += f"💵 {get_text('total_revenue', language_code)}: {total_revenue} {get_text('currency', language_code)}\n"
    
    # Create keyboard
    keyboard = [
        [
            InlineKeyboardButton(
                f"📥 {get_text('export_user_data', language_code)}",
                callback_data=f"{REPORTS}_export_users"
            ),
            InlineKeyboardButton(
                f"📥 {get_text('export_transactions', language_code)}",
                callback_data=f"{REPORTS}_export_transactions"
            )
        ],
        [
            InlineKeyboardButton(
                get_text("back_to_dashboard", language_code),
                callback_data=DASHBOARD
            )
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        reports_message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )

def get_admin_dashboard_handlers() -> List:
    """Return handlers for admin dashboard."""
    return [
        CommandHandler("admin", admin_dashboard),
        CallbackQueryHandler(admin_dashboard, pattern=f"^{DASHBOARD}$"),
        CallbackQueryHandler(handle_feature_management, pattern=f"^{FEATURES}$"),
        CallbackQueryHandler(toggle_feature, pattern=f"^{FEATURES}_toggle_"),
        CallbackQueryHandler(handle_server_management, pattern=f"^{SERVERS}"),
        CallbackQueryHandler(toggle_server, pattern=f"^{SERVERS}_toggle_"),
        CallbackQueryHandler(handle_payment_management, pattern=f"^{PAYMENTS}"),
        CallbackQueryHandler(toggle_payment_method, pattern=f"^{PAYMENTS}_toggle_"),
        CallbackQueryHandler(handle_bot_settings, pattern=f"^{SETTINGS}$"),
        CallbackQueryHandler(toggle_maintenance_mode, pattern=f"^{ADMIN_PREFIX}_toggle_maintenance$"),
        CallbackQueryHandler(handle_reports, pattern=f"^{REPORTS}$"),
        # Redirect to the server management module
        CallbackQueryHandler(
            lambda u, c: u.callback_query.edit_message_text(
                "Loading server management...",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Please wait...", callback_data="dummy")]
                ])
            ) or asyncio.create_task(
                __redirect_to_server_management(u, c)
            ) or SERVER_LIST,
            pattern=r"^server_action_list$"
        ),
    ]

async def __redirect_to_server_management(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Redirect to server management by creating a fake server command."""
    from handlers.admin.server_management import server_command
    await asyncio.sleep(0.5)  # Small delay for UX
    await server_command(update, context) 