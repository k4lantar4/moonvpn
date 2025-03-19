"""Database configuration."""
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

from ..config import settings

# Create async engine
async_engine = create_async_engine(
    str(settings.SQLALCHEMY_DATABASE_URI),
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
    echo=False,
)

# Create sync engine
engine = create_engine(
    str(settings.SQLALCHEMY_DATABASE_URI).replace("+asyncpg", ""),
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
    echo=False,
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Create sync session factory
SessionLocal = sessionmaker(
    engine,
    class_=Session,
    expire_on_commit=False,
)

async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

def get_db() -> Generator[Session, None, None]:
    """Get sync database session."""
    with SessionLocal() as session:
        try:
            yield session
        finally:
            session.close()

async def init_async_db() -> None:
    """Initialize async database."""
    from .models import Base
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

def init_db() -> None:
    """Initialize sync database."""
    from .models import Base
    Base.metadata.create_all(bind=engine) 