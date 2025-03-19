"""
Database connection manager.
"""

import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure

from core.config import settings

logger = logging.getLogger(__name__)

# Global database connection
_db: Optional[AsyncIOMotorDatabase] = None

async def init_db() -> None:
    """Initialize database connection."""
    global _db
    
    try:
        # Create MongoDB client
        client = AsyncIOMotorClient(
            settings.MONGODB_URI,
            serverSelectionTimeoutMS=5000
        )
        
        # Check connection
        await client.admin.command('ping')
        
        # Get database
        _db = client[settings.MONGODB_DB]
        
        logger.info("Connected to MongoDB: %s", settings.MONGODB_DB)
        
    except ConnectionFailure as e:
        logger.error("Failed to connect to MongoDB: %s", str(e))
        raise
    except Exception as e:
        logger.error("Error initializing database: %s", str(e))
        raise

def get_db() -> AsyncIOMotorDatabase:
    """Get database connection."""
    if _db is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _db

async def close_db() -> None:
    """Close database connection."""
    global _db
    
    if _db is not None:
        client = _db.client
        client.close()
        _db = None
        logger.info("Closed MongoDB connection") 