from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from typing import Generator, Optional
import redis
import logging
from contextlib import contextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from contextlib import asynccontextmanager

from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# --- MySQL Configuration / پیکربندی MySQL ---

# Create SQLAlchemy engine with optimized settings
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Enable connection health checks
    pool_size=10,  # Default connection pool size
    max_overflow=20,  # Allow up to 20 connections over pool_size
    pool_recycle=3600,  # Recycle connections after 1 hour
    pool_timeout=30,  # Connection timeout after 30 seconds
    echo=settings.is_development(),  # Log SQL in development mode
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

# --- Redis Configuration / پیکربندی Redis ---

_redis_client: Optional[redis.Redis] = None

def get_redis() -> redis.Redis:
    """Returns a Redis client instance.
    
    The client is created with a connection pool and cached for reuse.
    """
    global _redis_client
    
    if _redis_client is None:
        try:
            # Create connection pool
            pool = redis.ConnectionPool(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                max_connections=settings.REDIS_MAX_CONNECTIONS,
                decode_responses=True,  # Automatically decode responses to strings
                socket_timeout=5,  # Socket timeout in seconds
                socket_connect_timeout=5,  # Connection timeout
                retry_on_timeout=True,  # Retry on timeout
            )
            
            # Create Redis client
            _redis_client = redis.Redis(connection_pool=pool)
            
            # Test connection
            _redis_client.ping()
            logger.info("Successfully connected to Redis")
            
        except redis.RedisError as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            raise
    
    return _redis_client

# --- Database Utilities / ابزارهای پایگاه داده ---

def init_db(drop_all: bool = False) -> None:
    """Initialize the database schema.
    
    Args:
        drop_all: If True, drops all existing tables before creation.
    """
    try:
        if drop_all:
            Base.metadata.drop_all(bind=engine)
            logger.warning("Dropped all database tables")
        
        Base.metadata.create_all(bind=engine)
        logger.info("Successfully initialized database schema")
        
    except SQLAlchemyError as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise

def check_db_connection() -> bool:
    """Check if database connection is working.
    
    Returns:
        bool: True if connection is successful, False otherwise.
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            return True
    except SQLAlchemyError as e:
        logger.error(f"Database connection check failed: {str(e)}")
        return False

def check_redis_connection() -> bool:
    """Check if Redis connection is working.
    
    Returns:
        bool: True if connection is successful, False otherwise.
    """
    try:
        redis_client = get_redis()
        return redis_client.ping()
    except redis.RedisError as e:
        logger.error(f"Redis connection check failed: {str(e)}")
        return False

async def get_db_session():
    """
    Get a synchronous database session.
    Used mainly for the bot as python-telegram-bot doesn't fully support asynchronous SQLAlchemy.
    
    Returns:
        Session: A SQLAlchemy session
    """
    try:
        # Create a database URL for SQLAlchemy (synchronous)
        settings = get_settings()
        DATABASE_URL = f"mysql+mysqlconnector://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}"
        
        # Create engine and session
        sync_engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)
        db = SessionLocal()
        return db
    except Exception as e:
        logger.error(f"Error creating synchronous database session: {str(e)}")
        raise
