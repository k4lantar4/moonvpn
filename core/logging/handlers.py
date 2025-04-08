import logging
from logging import LogRecord
import sys
import asyncio

class TelegramHandler(logging.Handler):
    """Custom handler that sends critical logs to Telegram channel."""
    
    def __init__(self, bot_token: str, channel_id: str):
        super().__init__()
        self.bot_token = bot_token
        self.channel_id = channel_id
        self._queue = asyncio.Queue()
        self._task = None
        
    def emit(self, record: LogRecord):
        try:
            msg = self.format(record)
            asyncio.create_task(self._send_to_telegram(msg))
        except Exception as e:
            print(f"Error in TelegramHandler: {e}", file=sys.stderr)
    
    async def _send_to_telegram(self, message: str):
        if not self.bot_token or not self.channel_id:
            return
        
        import aiohttp
        
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        data = {
            "chat_id": self.channel_id,
            "text": f"🚨 *ALERT*\n```\n{message}\n```",
            "parse_mode": "Markdown"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data) as response:
                    if response.status != 200:
                        print(f"Failed to send log to Telegram: {response.status}", file=sys.stderr)
        except Exception as e:
            print(f"Error sending to Telegram: {e}", file=sys.stderr) 