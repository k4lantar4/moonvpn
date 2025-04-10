"""Async SQLAlchemy session management."""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from typing import AsyncGenerator

from core.config import settings

# Create the async engine based on the DATABASE_URL from settings
async_engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Check connections before use
    # echo=True,         # Uncomment for debugging SQL queries
)

# Create a configured "Session" class
# expire_on_commit=False prevents attributes from being expired
# after commit, which is useful in async contexts.
async_session_factory = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base class for declarative models
# All models should inherit from this class
class Base(DeclarativeBase):
    pass

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency provider that yields an async database session.
    Ensures the session is closed after use.
    """
    async with async_session_factory() as session:
        try:
            yield session
            # Optional: commit if everything went well (often handled in repositories)
            # await session.commit()
        except Exception:
            await session.rollback() # Rollback in case of errors
            raise
        finally:
            await session.close() # Ensure session is closed
