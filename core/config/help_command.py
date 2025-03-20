from typing import Optional
from telegram import Update
from telegram.ext import ContextTypes
from ..utils import get_help_text

async def send_help_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    language: str = 'en'
) -> None:
    """Send help message to user"""
    if not update.effective_message:
        return
        
    text = get_help_text(language)
    await update.effective_message.reply_text(text) 