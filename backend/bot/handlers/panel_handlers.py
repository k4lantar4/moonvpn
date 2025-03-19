"""
Telegram bot handlers for managing panel configurations.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CommandHandler, CallbackQueryHandler
from django.utils import timezone
import requests

from core.database.models import PanelConfig
from core.bot.decorators import admin_required
from core.bot.utils import build_menu

@admin_required
async def list_panels(update: Update, context: CallbackContext):
    """List all panel configurations."""
    panels = PanelConfig.objects.all()
    
    if not panels:
        await update.message.reply_text("No panel configurations found.")
        return
    
    text = "📋 Panel Configurations:\n\n"
    for panel in panels:
        status = "✅" if panel.is_active else "❌"
        text += f"{status} {panel.name} ({panel.domain}:{panel.port})\n"
        text += f"└ Location: {panel.location}, Last check: {panel.last_check or 'Never'}\n\n"
    
    keyboard = [
        [InlineKeyboardButton("Check All", callback_data="panel_check_all")],
        [InlineKeyboardButton("Add New", callback_data="panel_add")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(text, reply_markup=reply_markup)

@admin_required
async def check_panel(update: Update, context: CallbackContext):
    """Check connection to a specific panel."""
    args = context.args
    if not args:
        await update.message.reply_text("Please provide a panel ID.")
        return
    
    try:
        panel = PanelConfig.objects.get(server_id=args[0])
    except PanelConfig.DoesNotExist:
        await update.message.reply_text("Panel not found.")
        return
    
    try:
        response = requests.get(
            f"{panel.api_url}/status",
            auth=(panel.username, panel.password),
            timeout=10,
            verify=not panel.disable_check
        )
        
        if response.status_code == 200:
            panel.last_check = timezone.now()
            panel.save(update_fields=['last_check'])
            
            data = response.json()
            text = f"✅ Panel {panel.name} is online\n\n"
            text += f"CPU Usage: {data.get('cpu', 'N/A')}%\n"
            text += f"Memory Usage: {data.get('mem', 'N/A')}%\n"
            text += f"Disk Usage: {data.get('disk', 'N/A')}%\n"
            text += f"Active Users: {data.get('users', 'N/A')}\n"
            
            await update.message.reply_text(text)
        else:
            await update.message.reply_text(f"❌ Failed to connect to panel {panel.name}")
            
    except requests.RequestException as e:
        await update.message.reply_text(f"❌ Error connecting to panel {panel.name}: {str(e)}")

@admin_required
async def toggle_panel(update: Update, context: CallbackContext):
    """Toggle panel active status."""
    args = context.args
    if not args:
        await update.message.reply_text("Please provide a panel ID.")
        return
    
    try:
        panel = PanelConfig.objects.get(server_id=args[0])
    except PanelConfig.DoesNotExist:
        await update.message.reply_text("Panel not found.")
        return
    
    panel.is_active = not panel.is_active
    panel.save(update_fields=['is_active', 'updated_at'])
    
    status = "activated" if panel.is_active else "deactivated"
    await update.message.reply_text(f"Panel {panel.name} has been {status}.")

@admin_required
async def sync_panel(update: Update, context: CallbackContext):
    """Sync panel configuration."""
    args = context.args
    if not args:
        await update.message.reply_text("Please provide a panel ID.")
        return
    
    try:
        panel = PanelConfig.objects.get(server_id=args[0])
    except PanelConfig.DoesNotExist:
        await update.message.reply_text("Panel not found.")
        return
    
    try:
        response = requests.get(
            f"{panel.api_url}/config",
            auth=(panel.username, panel.password),
            timeout=10,
            verify=not panel.disable_check
        )
        
        if response.status_code == 200:
            config_data = response.json()
            panel.base_path = config_data.get('base_path', panel.base_path)
            panel.api_path = config_data.get('api_path', panel.api_path)
            panel.last_check = timezone.now()
            panel.save()
            
            await update.message.reply_text(f"✅ Panel {panel.name} configuration synced successfully.")
        else:
            await update.message.reply_text(f"❌ Failed to sync panel {panel.name} configuration.")
            
    except requests.RequestException as e:
        await update.message.reply_text(f"❌ Error syncing panel {panel.name}: {str(e)}")

async def panel_callback(update: Update, context: CallbackContext):
    """Handle panel-related callback queries."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "panel_check_all":
        text = "Checking all panels...\n\n"
        await query.message.edit_text(text)
        
        success = 0
        failed = 0
        
        for panel in PanelConfig.objects.filter(is_active=True):
            try:
                response = requests.get(
                    f"{panel.api_url}/status",
                    auth=(panel.username, panel.password),
                    timeout=10,
                    verify=not panel.disable_check
                )
                
                if response.status_code == 200:
                    panel.last_check = timezone.now()
                    panel.save(update_fields=['last_check'])
                    text += f"✅ {panel.name}: Online\n"
                    success += 1
                else:
                    text += f"❌ {panel.name}: Error {response.status_code}\n"
                    failed += 1
            except requests.RequestException as e:
                text += f"❌ {panel.name}: {str(e)}\n"
                failed += 1
        
        text += f"\nCompleted: {success} successful, {failed} failed"
        await query.message.edit_text(text)
    
    elif query.data == "panel_add":
        text = "To add a new panel, use the following format:\n\n"
        text += "/addpanel <server_id> <name> <domain> <port> <username> <password> <location>"
        await query.message.edit_text(text)

@admin_required
async def add_panel(update: Update, context: CallbackContext):
    """Add a new panel configuration."""
    args = context.args
    if len(args) < 7:
        await update.message.reply_text(
            "Please provide all required parameters:\n"
            "/addpanel <server_id> <name> <domain> <port> <username> <password> <location>"
        )
        return
    
    try:
        server_id = int(args[0])
        port = int(args[3])
    except ValueError:
        await update.message.reply_text("Server ID and port must be numbers.")
        return
    
    panel, created = PanelConfig.objects.update_or_create(
        server_id=server_id,
        defaults={
            'name': args[1],
            'domain': args[2],
            'port': port,
            'username': args[4],
            'password': args[5],
            'location': args[6],
            'is_active': True
        }
    )
    
    action = "created" if created else "updated"
    await update.message.reply_text(f"Panel configuration {action} successfully.")

def register_handlers(application):
    """Register panel management handlers."""
    application.add_handler(CommandHandler("panels", list_panels))
    application.add_handler(CommandHandler("checkpanel", check_panel))
    application.add_handler(CommandHandler("togglepanel", toggle_panel))
    application.add_handler(CommandHandler("syncpanel", sync_panel))
    application.add_handler(CommandHandler("addpanel", add_panel))
    application.add_handler(CallbackQueryHandler(panel_callback, pattern="^panel_")) 