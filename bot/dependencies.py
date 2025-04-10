"""Dependency utilities for the bot."""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from core.database.session import async_session_factory

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get an async database session."""
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            # Session is automatically closed by the context manager
            pass 