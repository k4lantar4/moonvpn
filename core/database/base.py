from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from datetime import datetime
import logging
from core.database.config import (
    DATABASE_URL,
    DB_POOL_SIZE,
    DB_MAX_OVERFLOW,
    DB_POOL_TIMEOUT,
    DB_POOL_RECYCLE,
    DB_ECHO,
    DB_POOL_PRE_PING,
    LOG_LEVEL,
    LOG_FORMAT,
    LOG_FILE
)

# Configure logging
logging.basicConfig(
    level=LOG_LEVEL,
    format=LOG_FORMAT,
    filename=LOG_FILE
)
logger = logging.getLogger(__name__)

# Create declarative base
Base = declarative_base()

# Create engine with configuration
engine = create_engine(
    DATABASE_URL,
    pool_size=DB_POOL_SIZE,
    max_overflow=DB_MAX_OVERFLOW,
    pool_timeout=DB_POOL_TIMEOUT,
    pool_recycle=DB_POOL_RECYCLE,
    echo=DB_ECHO,
    pool_pre_ping=DB_POOL_PRE_PING
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        raise

class BaseModel(Base):
    """Base model with common functionality"""
    __abstract__ = True

    def save(self, db):
        """Save model to database"""
        try:
            db.add(self)
            db.commit()
            db.refresh(self)
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error saving {self.__class__.__name__}: {str(e)}")
            return False

    def delete(self, db):
        """Delete model from database"""
        try:
            db.delete(self)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting {self.__class__.__name__}: {str(e)}")
            return False

    @classmethod
    def get_by_id(cls, db, id):
        """Get model by ID"""
        try:
            return db.query(cls).filter(cls.id == id).first()
        except Exception as e:
            logger.error(f"Error getting {cls.__name__} by ID: {str(e)}")
            return None

    @classmethod
    def get_all(cls, db):
        """Get all models"""
        try:
            return db.query(cls).all()
        except Exception as e:
            logger.error(f"Error getting all {cls.__name__}: {str(e)}")
            return []

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }

    def update(self, db, **kwargs):
        """Update model attributes"""
        try:
            for key, value in kwargs.items():
                if hasattr(self, key):
                    setattr(self, key, value)
            db.commit()
            db.refresh(self)
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating {self.__class__.__name__}: {str(e)}")
            return False 