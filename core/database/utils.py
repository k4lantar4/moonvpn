import logging
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text

from core.database.session import engine, Base

logger = logging.getLogger(__name__)

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