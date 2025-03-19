import logging
from alembic.config import Config
from alembic import command

from .connection import init_db, close_db
from .models.base import Base
from .models.user import User
from .models.payments import (
    CardOwner,
    Transaction,
    CardPayment,
    ZarinpalPayment,
    PaymentMethod,
    PaymentPlan,
    DiscountCode,
    Payment,
    payment_plan_discount_codes
)

# Configure logging
logger = logging.getLogger(__name__)


def run_migrations() -> None:
    """Run database migrations."""
    try:
        # Create Alembic configuration
        alembic_cfg = Config("alembic.ini")
        
        # Run migrations
        command.upgrade(alembic_cfg, "head")
        logger.info("Database migrations completed successfully")
    except Exception as e:
        logger.error(f"Failed to run database migrations: {str(e)}")
        raise


def init_database() -> None:
    """Initialize database and run migrations."""
    try:
        # Initialize database connection
        init_db()
        
        # Run migrations
        run_migrations()
        
        logger.info("Database initialization completed successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise
    finally:
        # Close database connection
        close_db()


if __name__ == "__main__":
    init_database() 