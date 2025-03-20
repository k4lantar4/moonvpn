import logging
from typing import Optional

from .init_db import init_database
from .seed import seed_database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_database(seed: bool = True) -> None:
    """Set up database with initialization and optional seeding."""
    try:
        # Initialize database
        logger.info("Starting database initialization...")
        init_database()
        
        # Seed database if requested
        if seed:
            logger.info("Starting database seeding...")
            seed_database()
        
        logger.info("Database setup completed successfully")
    except Exception as e:
        logger.error(f"Database setup failed: {str(e)}")
        raise


def main(seed: Optional[bool] = None) -> None:
    """Main function to run database setup."""
    try:
        # If seed is not specified, ask user
        if seed is None:
            while True:
                response = input("Do you want to seed the database with initial data? (y/n): ").lower()
                if response in ['y', 'n']:
                    seed = response == 'y'
                    break
                print("Please enter 'y' or 'n'")
        
        # Run database setup
        setup_database(seed)
    except KeyboardInterrupt:
        logger.info("Database setup interrupted by user")
    except Exception as e:
        logger.error(f"Database setup failed: {str(e)}")
        raise


if __name__ == "__main__":
    main() 