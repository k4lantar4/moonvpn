from contextlib import contextmanager, asynccontextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker
import logging

from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Create sync database connection string
DB_URI = f"mysql+mysqlconnector://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}"

# Create SQLAlchemy engine with optimized settings
engine = create_engine(
    DB_URI,
    pool_pre_ping=True,  # Enable connection health checks
    pool_size=10,  # Default connection pool size
    max_overflow=20,  # Allow up to 20 connections over pool_size
    pool_recycle=3600,  # Recycle connections after 1 hour
    pool_timeout=30,  # Connection timeout after 30 seconds
    echo=settings.DEBUG,  # Log SQL in development mode
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for SQLAlchemy models
Base = declarative_base()

# --- MySQL Event Listeners / رویدادهای MySQL ---

@event.listens_for(Engine, "connect")
def set_mysql_timezone(dbapi_connection, connection_record):
    """Set timezone to UTC for each new connection."""
    cursor = dbapi_connection.cursor()
    cursor.execute("SET time_zone = '+00:00'")
    cursor.close()

@event.listens_for(Engine, "connect")
def set_mysql_strict_mode(dbapi_connection, connection_record):
    """Enable strict mode for MySQL."""
    cursor = dbapi_connection.cursor()
    cursor.execute("SET SESSION sql_mode='STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION'")
    cursor.close()

# --- Database Session Management / مدیریت نشست پایگاه داده ---

def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for database sessions.
    
    Yields:
        Session: SQLAlchemy session for database operations.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """Context manager for database sessions.
    
    Usage:
        with get_db_context() as db:
            db.query(...)
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error: {str(e)}")
        raise
    finally:
        db.close()

async def get_db_session():
    """
    Get a synchronous database session.
    Used mainly for the bot as python-telegram-bot doesn't fully support asynchronous SQLAlchemy.
    
    Returns:
        Session: A SQLAlchemy session
    """
    try:
        # Create engine and session
        sync_engine = create_engine(DB_URI)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)
        db = SessionLocal()
        return db
    except Exception as e:
        logger.error(f"Error creating synchronous database session: {str(e)}")
        raise 