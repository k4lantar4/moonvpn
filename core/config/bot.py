"""
FastAPI router for MoonVPN Telegram bot webhook.

This module handles incoming webhook requests from Telegram,
validates them, and processes them through the bot application.
"""

from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import logging
from telegram import Update
from telegram.ext import Application

from app.core.config import settings
from app.bot.bot import MoonVPNBot
from app.core.security import verify_telegram_request

# Setup logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Pydantic model for webhook request validation
class TelegramWebhookRequest(BaseModel):
    """Model for validating Telegram webhook requests."""
    update_id: int
    message: Dict[str, Any] = None
    callback_query: Dict[str, Any] = None
    edited_message: Dict[str, Any] = None
    channel_post: Dict[str, Any] = None
    edited_channel_post: Dict[str, Any] = None
    inline_query: Dict[str, Any] = None
    chosen_inline_result: Dict[str, Any] = None
    shipping_query: Dict[str, Any] = None
    pre_checkout_query: Dict[str, Any] = None
    poll: Dict[str, Any] = None
    poll_answer: Dict[str, Any] = None
    my_chat_member: Dict[str, Any] = None
    chat_member: Dict[str, Any] = None
    chat_join_request: Dict[str, Any] = None

@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    bot: MoonVPNBot = Depends(MoonVPNBot)
) -> JSONResponse:
    """
    Handle incoming Telegram webhook requests.
    
    Args:
        request: The incoming FastAPI request
        bot: The MoonVPNBot instance
        
    Returns:
        JSONResponse: Response indicating success or failure
    """
    try:
        # Get request body
        body = await request.body()
        
        # Verify request is from Telegram
        if not verify_telegram_request(body, request.headers.get("X-Telegram-Bot-Api-Secret-Token")):
            raise HTTPException(status_code=403, detail="Invalid request signature")
        
        # Parse and validate request data
        data = await request.json()
        webhook_request = TelegramWebhookRequest(**data)
        
        # Convert to Update object
        update = Update.de_json(data, bot.application.bot)
        
        # Process update
        await bot.application.process_update(update)
        
        return JSONResponse({"status": "ok"})
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/webhook-info")
async def get_webhook_info(
    bot: MoonVPNBot = Depends(MoonVPNBot)
) -> Dict[str, Any]:
    """
    Get current webhook information.
    
    Args:
        bot: The MoonVPNBot instance
        
    Returns:
        Dict[str, Any]: Webhook information
    """
    try:
        webhook_info = await bot.application.bot.get_webhook_info()
        return webhook_info.to_dict()
    except Exception as e:
        logger.error(f"Error getting webhook info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/set-webhook")
async def set_webhook(
    bot: MoonVPNBot = Depends(MoonVPNBot)
) -> Dict[str, Any]:
    """
    Set up the webhook for the bot.
    
    Args:
        bot: The MoonVPNBot instance
        
    Returns:
        Dict[str, Any]: Result of webhook setup
    """
    try:
        # Set webhook URL
        webhook_url = f"{settings.WEBHOOK_BASE_URL}/webhook"
        await bot.application.bot.set_webhook(
            url=webhook_url,
            allowed_updates=Update.ALL_TYPES
        )
        
        return {"status": "ok", "webhook_url": webhook_url}
    except Exception as e:
        logger.error(f"Error setting webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete-webhook")
async def delete_webhook(
    bot: MoonVPNBot = Depends(MoonVPNBot)
) -> Dict[str, Any]:
    """
    Delete the current webhook.
    
    Args:
        bot: The MoonVPNBot instance
        
    Returns:
        Dict[str, Any]: Result of webhook deletion
    """
    try:
        await bot.application.bot.delete_webhook()
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error deleting webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 