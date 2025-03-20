import json
import logging
import sys
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

# Add the parent directory to the Python path
sys.path.insert(0, '/usr/local/lib/python3.11/site-packages')

# Now import from python-telegram-bot
from telegram import Update
from telegram.ext import Application

from .bot import setup_bot

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize the bot application
application = setup_bot()

@csrf_exempt
def telegram_webhook(request):
    """Handle incoming Telegram webhook requests."""
    if request.method == 'POST':
        try:
            # Get the update data from request
            update_data = json.loads(request.body.decode('utf-8'))
            logger.info(f"Received update: {update_data}")
            
            # Convert to Update object
            update = Update.de_json(update_data, application.bot)
            
            # Process update asynchronously
            application.process_update(update)
            
            return JsonResponse({'status': 'ok'})
        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    else:
        return JsonResponse({'status': 'error', 'message': 'Only POST requests are allowed'}, status=405)

def set_webhook():
    """Set the Telegram webhook."""
    webhook_url = settings.TELEGRAM_WEBHOOK_URL
    
    # Set webhook
    webhook_info = application.bot.set_webhook(webhook_url)
    
    if webhook_info:
        logger.info(f"Webhook set to {webhook_url}")
        return True
    else:
        logger.error(f"Failed to set webhook to {webhook_url}")
        return False

def delete_webhook():
    """Delete the Telegram webhook."""
    # Delete webhook
    result = application.bot.delete_webhook()
    
    if result:
        logger.info("Webhook deleted")
        return True
    else:
        logger.error("Failed to delete webhook")
        return False 