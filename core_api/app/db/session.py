from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.base_class import Base

# Create the SQLAlchemy engine
engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True # Checks connections for liveness before borrowing
    # You might add other engine options like pool_size, max_overflow later
)

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency to get DB session (used in API endpoints)
def get_db():
    """Dependency that provides a SQLAlchemy database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
