"""Middleware for providing database sessions to handlers."""

import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

logger = logging.getLogger(__name__)

class DbSessionMiddleware(BaseMiddleware):
    """This middleware creates a new SQLAlchemy session for each update
    and passes it to the handler. It also ensures the session is closed.
    """
    def __init__(self, session_pool: async_sessionmaker[AsyncSession]):
        super().__init__()
        self.session_pool = session_pool
        logger.debug("DbSessionMiddleware initialized.")

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """Execute middleware"""
        logger.debug("DbSessionMiddleware entered.")
        try:
            async with self.session_pool() as session:
                logger.debug("SQLAlchemy session created and added to data.")
                data["session"] = session
                # Proceed to the next middleware or handler
                result = await handler(event, data)
                # Session commit/rollback should ideally happen within services 
                # or explicitly in handlers if needed, not automatically here.
                logger.debug("Handler finished, session will be closed automatically.")
                return result
        except Exception as e:
            # Log exceptions occurring during session management or handler execution
            logger.error(f"Exception in DbSessionMiddleware or handler: {e}", exc_info=True)
            # Depending on the desired behavior, you might want to:
            # - Re-raise the exception: raise
            # - Send an error message to the user (if applicable event type)
            # - Return a specific value
            # For now, let's re-raise to make errors visible
            raise
        finally:
             logger.debug("DbSessionMiddleware exited.") 