"""
Server monitoring handler for the V2Ray Telegram bot.

This module implements handlers for server monitoring operations including:
- Server health checks
- Traffic statistics
- System resource monitoring
- Server status updates
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
)
from telegram.constants import ParseMode

from core.utils.i18n import get_text, format_number, format_date
from core.database import get_user, get_all_servers, get_server_health
from core.services.panel.api import XUIClient
from core.utils.helpers import require_admin
from core.utils.api import get_server_stats, get_server_history

logger = logging.getLogger(__name__)

# Conversation states
SELECTING_ACTION = 0
SELECTING_SERVER = 1
SELECTING_TIME_RANGE = 2

# Callback data patterns
MONITORING_CB = "monitoring"
SERVER_STATUS = f"{MONITORING_CB}_status"
TRAFFIC_STATS = f"{MONITORING_CB}_traffic"
SYSTEM_STATS = f"{MONITORING_CB}_system"
NETWORK_STATS = f"{MONITORING_CB}_network"
HISTORY = f"{MONITORING_CB}_history"
REFRESH_STATS = f"{MONITORING_CB}_refresh"
BACK_TO_MONITORING = f"{MONITORING_CB}_back"

@require_admin
async def monitoring_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show the monitoring menu."""
    query = update.callback_query
    await query.answer()
    
    language_code = context.user_data.get("language", "en")
    
    text = get_text("monitoring_menu_info", language_code)
    keyboard = [
        [
            InlineKeyboardButton(
                get_text("server_status", language_code),
                callback_data=SERVER_STATUS
            )
        ],
        [
            InlineKeyboardButton(
                get_text("traffic_stats", language_code),
                callback_data=TRAFFIC_STATS
            )
        ],
        [
            InlineKeyboardButton(
                get_text("system_stats", language_code),
                callback_data=SYSTEM_STATS
            )
        ],
        [
            InlineKeyboardButton(
                get_text("network_stats", language_code),
                callback_data=NETWORK_STATS
            )
        ],
        [
            InlineKeyboardButton(
                get_text("history", language_code),
                callback_data=HISTORY
            )
        ],
        [
            InlineKeyboardButton(
                get_text("back_to_menu", language_code),
                callback_data="menu"
            )
        ],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=text, reply_markup=reply_markup)
    
    return SELECTING_ACTION

@require_admin
async def server_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show server status information."""
    query = update.callback_query
    await query.answer()
    
    language_code = context.user_data.get("language", "en")
    
    # Get all servers
    servers = get_all_servers()
    
    if not servers:
        text = get_text("no_servers", language_code)
    else:
        text = get_text("server_status_header", language_code) + "\n\n"
        
        for server in servers:
            # Get server health
            health = get_server_health(server["id"])
            
            if not health:
                text += get_text("server_status_error", language_code).format(
                    name=server["name"],
                    error="No data available"
                )
                continue
            
            # Get health status emoji
            status_emoji = {
                "healthy": "🟢",
                "warning": "🟡",
                "critical": "🔴",
                "offline": "⚫"
            }.get(health["health_status"], "⚫")
            
            text += get_text("server_status_item", language_code).format(
                name=server["name"],
                status=status_emoji,
                cpu=format_number(health["cpu_usage"], language_code),
                memory=format_number(health["memory_usage"], language_code),
                disk=format_number(health["disk_usage"], language_code),
                connections=health["active_connections"],
                uptime=format_number(health["uptime_days"], language_code)
            )
    
    keyboard = [
        [
            InlineKeyboardButton(
                get_text("refresh", language_code),
                callback_data=REFRESH_STATS
            )
        ],
        [
            InlineKeyboardButton(
                get_text("back_to_monitoring", language_code),
                callback_data=BACK_TO_MONITORING
            )
        ],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=text, reply_markup=reply_markup)
    
    return SELECTING_ACTION

@require_admin
async def traffic_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show traffic statistics."""
    query = update.callback_query
    await query.answer()
    
    language_code = context.user_data.get("language", "en")
    
    # Get all servers
    servers = get_all_servers()
    
    if not servers:
        text = get_text("no_servers", language_code)
    else:
        text = get_text("traffic_stats_header", language_code) + "\n\n"
        total_up = 0
        total_down = 0
        
        for server in servers:
            try:
                stats = get_server_stats(server["id"])
                
                if not stats:
                    text += get_text("server_traffic_error", language_code).format(
                        name=server["name"],
                        error="No data available"
                    )
                    continue
                
                network = stats["network"]
                total_up += network["total_usage_gb"]
                total_down += network["total_usage_gb"]
                
                text += get_text("server_traffic_item", language_code).format(
                    name=server["name"],
                    up=format_number(network["total_usage_gb"], language_code),
                    down=format_number(network["total_usage_gb"], language_code),
                    speed=format_number(network["current_speed_mbps"][1], language_code)
                )
            except Exception as e:
                logger.error(f"Error getting traffic stats for server {server['name']}: {e}")
                text += get_text("server_traffic_error", language_code).format(
                    name=server["name"],
                    error=str(e)
                )
        
        # Add total traffic stats
        text += "\n" + get_text("total_traffic_stats", language_code).format(
            up=format_number(total_up, language_code),
            down=format_number(total_down, language_code),
            total=format_number(total_up + total_down, language_code)
        )
    
    keyboard = [
        [
            InlineKeyboardButton(
                get_text("refresh", language_code),
                callback_data=REFRESH_STATS
            )
        ],
        [
            InlineKeyboardButton(
                get_text("back_to_monitoring", language_code),
                callback_data=BACK_TO_MONITORING
            )
        ],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=text, reply_markup=reply_markup)
    
    return SELECTING_ACTION

@require_admin
async def system_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show system statistics."""
    query = update.callback_query
    await query.answer()
    
    language_code = context.user_data.get("language", "en")
    
    # Get all servers
    servers = get_all_servers()
    
    if not servers:
        text = get_text("no_servers", language_code)
    else:
        text = get_text("system_stats_header", language_code) + "\n\n"
        
        for server in servers:
            try:
                stats = get_server_stats(server["id"])
                
                if not stats:
                    text += get_text("system_stats_error", language_code).format(
                        name=server["name"],
                        error="No data available"
                    )
                    continue
                
                text += get_text("system_stats_item", language_code).format(
                    name=server["name"],
                    cpu_avg=format_number(stats["cpu"]["avg"], language_code),
                    cpu_max=format_number(stats["cpu"]["max"], language_code),
                    memory_avg=format_number(stats["memory"]["avg"], language_code),
                    memory_max=format_number(stats["memory"]["max"], language_code),
                    disk_avg=format_number(stats["disk"]["avg"], language_code),
                    disk_max=format_number(stats["disk"]["max"], language_code),
                    connections_avg=format_number(stats["connections"]["avg"], language_code),
                    connections_max=format_number(stats["connections"]["max"], language_code),
                    load_1min=format_number(stats["load"]["1min"], language_code),
                    load_5min=format_number(stats["load"]["5min"], language_code),
                    load_15min=format_number(stats["load"]["15min"], language_code)
                )
            except Exception as e:
                logger.error(f"Error getting system stats for server {server['name']}: {e}")
                text += get_text("system_stats_error", language_code).format(
                    name=server["name"],
                    error=str(e)
                )
    
    keyboard = [
        [
            InlineKeyboardButton(
                get_text("refresh", language_code),
                callback_data=REFRESH_STATS
            )
        ],
        [
            InlineKeyboardButton(
                get_text("back_to_monitoring", language_code),
                callback_data=BACK_TO_MONITORING
            )
        ],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=text, reply_markup=reply_markup)
    
    return SELECTING_ACTION

@require_admin
async def network_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show network statistics."""
    query = update.callback_query
    await query.answer()
    
    language_code = context.user_data.get("language", "en")
    
    # Get all servers
    servers = get_all_servers()
    
    if not servers:
        text = get_text("no_servers", language_code)
    else:
        text = get_text("network_stats_header", language_code) + "\n\n"
        
        for server in servers:
            try:
                stats = get_server_stats(server["id"])
                
                if not stats:
                    text += get_text("network_stats_error", language_code).format(
                        name=server["name"],
                        error="No data available"
                    )
                    continue
                
                network = stats["network"]
                io = stats["io"]
                
                text += get_text("network_stats_item", language_code).format(
                    name=server["name"],
                    usage=format_number(network["total_usage_gb"], language_code),
                    speed_in=format_number(network["current_speed_mbps"][0], language_code),
                    speed_out=format_number(network["current_speed_mbps"][1], language_code),
                    io_read=format_number(io["current_speed_mbps"][0], language_code),
                    io_write=format_number(io["current_speed_mbps"][1], language_code)
                )
            except Exception as e:
                logger.error(f"Error getting network stats for server {server['name']}: {e}")
                text += get_text("network_stats_error", language_code).format(
                    name=server["name"],
                    error=str(e)
                )
    
    keyboard = [
        [
            InlineKeyboardButton(
                get_text("refresh", language_code),
                callback_data=REFRESH_STATS
            )
        ],
        [
            InlineKeyboardButton(
                get_text("back_to_monitoring", language_code),
                callback_data=BACK_TO_MONITORING
            )
        ],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=text, reply_markup=reply_markup)
    
    return SELECTING_ACTION

@require_admin
async def history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show server selection for history."""
    query = update.callback_query
    await query.answer()
    
    language_code = context.user_data.get("language", "en")
    
    # Get all servers
    servers = get_all_servers()
    
    if not servers:
        text = get_text("no_servers", language_code)
        keyboard = [
            [
                InlineKeyboardButton(
                    get_text("back_to_monitoring", language_code),
                    callback_data=BACK_TO_MONITORING
                )
            ]
        ]
    else:
        text = get_text("select_server_history", language_code)
        keyboard = []
        
        for server in servers:
            keyboard.append([
                InlineKeyboardButton(
                    server["name"],
                    callback_data=f"history_{server['id']}"
                )
            ])
        
        keyboard.append([
            InlineKeyboardButton(
                get_text("back_to_monitoring", language_code),
                callback_data=BACK_TO_MONITORING
            )
        ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=text, reply_markup=reply_markup)
    
    return SELECTING_SERVER

@require_admin
async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show server history."""
    query = update.callback_query
    await query.answer()
    
    language_code = context.user_data.get("language", "en")
    server_id = int(query.data.split("_")[1])
    
    # Get server history
    history = get_server_history(server_id)
    
    if not history:
        text = get_text("no_history_data", language_code)
        keyboard = [
            [
                InlineKeyboardButton(
                    get_text("back_to_history", language_code),
                    callback_data=HISTORY
                )
            ]
        ]
    else:
        text = get_text("history_header", language_code) + "\n\n"
        
        for entry in history:
            text += get_text("history_item", language_code).format(
                timestamp=format_date(entry["timestamp"], language_code),
                cpu=format_number(entry["cpu_usage"], language_code),
                memory=format_number(entry["memory_usage"], language_code),
                disk=format_number(entry["disk_usage"], language_code),
                connections=entry["active_connections"]
            )
        
        keyboard = [
            [
                InlineKeyboardButton(
                    get_text("back_to_history", language_code),
                    callback_data=HISTORY
                )
            ]
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=text, reply_markup=reply_markup)
    
    return SELECTING_ACTION

@require_admin
async def refresh_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Refresh monitoring statistics."""
    query = update.callback_query
    await query.answer()
    
    # Get the current view from the callback data
    current_view = query.data.split("_")[0]
    
    # Call the appropriate handler
    if current_view == "status":
        return await server_status(update, context)
    elif current_view == "traffic":
        return await traffic_stats(update, context)
    elif current_view == "system":
        return await system_stats(update, context)
    elif current_view == "network":
        return await network_stats(update, context)
    else:
        return await monitoring_menu(update, context)

def get_monitoring_handler() -> ConversationHandler:
    """Get the monitoring conversation handler."""
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(monitoring_menu, pattern=f"^{MONITORING_CB}$")],
        states={
            SELECTING_ACTION: [
                CallbackQueryHandler(server_status, pattern=f"^{SERVER_STATUS}$"),
                CallbackQueryHandler(traffic_stats, pattern=f"^{TRAFFIC_STATS}$"),
                CallbackQueryHandler(system_stats, pattern=f"^{SYSTEM_STATS}$"),
                CallbackQueryHandler(network_stats, pattern=f"^{NETWORK_STATS}$"),
                CallbackQueryHandler(history, pattern=f"^{HISTORY}$"),
                CallbackQueryHandler(refresh_stats, pattern=f"^{REFRESH_STATS}_.*$"),
                CallbackQueryHandler(monitoring_menu, pattern=f"^{BACK_TO_MONITORING}$"),
            ],
            SELECTING_SERVER: [
                CallbackQueryHandler(show_history, pattern=r"^history_\d+$"),
                CallbackQueryHandler(history, pattern=f"^{BACK_TO_MONITORING}$"),
            ],
        },
        fallbacks=[CallbackQueryHandler(monitoring_menu, pattern=f"^{BACK_TO_MONITORING}$")],
    ) 