#!/usr/bin/env python3
"""
Database Setup Script

This script initializes the database with the necessary tables and data.
It will:
1. Create all tables using SQLAlchemy models
2. Create default roles (admin, seller, user)
3. Create a default admin user if no users exist
"""

import sys
import os
import logging
from datetime import datetime

# Add the project root directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from core.config import get_settings
from api.models import Base, User, Role, RoleName, Location, PlanCategory

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_database():
    """Create database tables and initialize with default data."""
    
    settings = get_settings()
    
    # Database connection URL
    DATABASE_URL = f"mysql+mysqlconnector://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}"
    
    logger.info(f"Connecting to database: {settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}")
    
    try:
        # Create database engine
        engine = create_engine(DATABASE_URL)
        
        # Check if database exists and is accessible
        try:
            connection = engine.connect()
            connection.close()
            logger.info("Database connection successful.")
        except Exception as e:
            logger.error(f"Failed to connect to database: {str(e)}")
            return False
        
        # Create session factory
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Check if tables exist
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        logger.info(f"Existing tables: {existing_tables}")
        
        # Create tables if they don't exist
        if 'users' not in existing_tables:
            logger.info("Creating database tables...")
            Base.metadata.create_all(engine)
            logger.info("Tables created successfully.")
        else:
            logger.info("Tables already exist. Skipping table creation.")
        
        # Create default roles if they don't exist
        if 'roles' in existing_tables:
            # Check if roles exist, create if they don't
            admin_role = session.query(Role).filter_by(name=RoleName.ADMIN).first()
            if not admin_role:
                logger.info("Creating default roles...")
                
                # Create admin role
                admin_role = Role(
                    name=RoleName.ADMIN,
                    description="Administrator with full system access",
                    can_manage_panels=True,
                    can_manage_users=True,
                    can_manage_plans=True,
                    can_approve_payments=True,
                    can_broadcast=True,
                    is_admin=True,
                    is_seller=False
                )
                session.add(admin_role)
                
                # Create seller role
                seller_role = Role(
                    name=RoleName.SELLER,
                    description="Seller with limited access to sell plans",
                    can_manage_panels=False,
                    can_manage_users=False,
                    can_manage_plans=False,
                    can_approve_payments=False,
                    can_broadcast=False,
                    is_admin=False,
                    is_seller=True,
                    discount_percent=10
                )
                session.add(seller_role)
                
                # Create user role
                user_role = Role(
                    name=RoleName.USER,
                    description="Regular user with basic access",
                    can_manage_panels=False,
                    can_manage_users=False,
                    can_manage_plans=False,
                    can_approve_payments=False,
                    can_broadcast=False,
                    is_admin=False,
                    is_seller=False
                )
                session.add(user_role)
                
                session.commit()
                logger.info("Default roles created successfully.")
            else:
                logger.info("Roles already exist. Skipping role creation.")
        
        # Create default admin user if no users exist
        if 'users' in existing_tables:
            user_count = session.query(User).count()
            if user_count == 0 and settings.TELEGRAM_ADMIN_ID:
                # Get admin role
                admin_role = session.query(Role).filter_by(name=RoleName.ADMIN).first()
                
                if admin_role:
                    logger.info(f"Creating default admin user with Telegram ID: {settings.TELEGRAM_ADMIN_ID}")
                    admin_user = User(
                        telegram_id=settings.TELEGRAM_ADMIN_ID,
                        username="admin",
                        full_name="System Administrator",
                        role_id=admin_role.id,
                        is_active=True,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    session.add(admin_user)
                    session.commit()
                    logger.info("Default admin user created successfully.")
                else:
                    logger.error("Admin role not found. Cannot create admin user.")
            else:
                logger.info("Users already exist or admin Telegram ID not set. Skipping admin user creation.")
        
        # Create default locations if they don't exist
        if 'locations' in existing_tables:
            location_count = session.query(Location).count()
            if location_count == 0:
                logger.info("Creating default locations...")
                
                locations = [
                    Location(name="Germany", flag="🇩🇪", country_code="DE", is_active=True),
                    Location(name="Netherlands", flag="🇳🇱", country_code="NL", is_active=True),
                    Location(name="France", flag="🇫🇷", country_code="FR", is_active=True)
                ]
                
                session.bulk_save_objects(locations)
                session.commit()
                logger.info("Default locations created successfully.")
            else:
                logger.info("Locations already exist. Skipping location creation.")
        
        # Create default plan categories if they don't exist
        if 'plan_categories' in existing_tables:
            category_count = session.query(PlanCategory).count()
            if category_count == 0:
                logger.info("Creating default plan categories...")
                
                categories = [
                    PlanCategory(name="Basic", sorting_order=1, is_active=True),
                    PlanCategory(name="Premium", sorting_order=2, is_active=True),
                    PlanCategory(name="Business", sorting_order=3, is_active=True)
                ]
                
                session.bulk_save_objects(categories)
                session.commit()
                logger.info("Default plan categories created successfully.")
            else:
                logger.info("Plan categories already exist. Skipping category creation.")
        
        # Close session
        session.close()
        
        logger.info("Database setup completed successfully.")
        return True
        
    except Exception as e:
        logger.error(f"Error during database setup: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Starting database setup...")
    result = setup_database()
    if result:
        logger.info("Database setup completed successfully.")
        sys.exit(0)
    else:
        logger.error("Database setup failed.")
        sys.exit(1)
