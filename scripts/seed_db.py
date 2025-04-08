#!/usr/bin/env python3
"""
Seed Database Script for MoonVPN

This script populates the database with initial data such as:
- Roles (Admin, Seller, User)
- Admin user
- Settings
- Locations
- Plan categories
- Plans
- Panels (sample)

Usage:
    python seed_db.py

Notes:
    - This script should be run after the database migrations
    - It will check if data already exists before inserting
"""

import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from argparse import ArgumentParser
from typing import Dict, List, Optional

# Add the parent directory to the path so we can import the API modules
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
sys.path.append(str(project_root))

from sqlalchemy import select, func, text
from sqlalchemy.orm import Session, sessionmaker

from api.models.users import User, Role, RoleName
from api.models.locations import Location
from api.models.panels import Panel
from api.models.plans import Plan, PlanCategory
from api.models.system import Settings
from core.database.session import engine
from core.config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("seed_db")
settings = get_settings()

# Create a sessionmaker for database interactions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Default admin credentials
DEFAULT_ADMIN_TELEGRAM_ID = 123456789
DEFAULT_ADMIN_USERNAME = "admin"

def seed_roles(db: Session) -> Dict[str, Role]:
    """Seed roles into the database."""
    logger.info("Seeding roles...")
    roles = {}
    
    role_names = [
        {"name": RoleName.ADMIN, "is_admin": True, "is_seller": False},
        {"name": RoleName.SELLER, "is_admin": False, "is_seller": True},
        {"name": RoleName.USER, "is_admin": False, "is_seller": False},
    ]
    
    for role_data in role_names:
        # Check if the role already exists
        query = select(Role).where(Role.name == role_data["name"])
        existing_role = db.execute(query).scalars().first()
        
        if existing_role:
            logger.info(f"Role '{role_data['name']}' already exists")
            roles[role_data["name"].value] = existing_role
            continue
        
        # Create new role
        role = Role(
            name=role_data["name"],
            is_admin=role_data["is_admin"],
            is_seller=role_data["is_seller"],
            description=f"{role_data['name'].value} role"
        )
        db.add(role)
        db.flush()
        roles[role_data["name"].value] = role
        logger.info(f"Created role: {role_data['name'].value}")
    
    db.commit()
    return roles

def seed_admin_user(db: Session, roles: Dict[str, Role]) -> User:
    """Seed admin user into the database."""
    logger.info("Seeding admin user...")
    
    # Check if admin user exists
    query = select(User).where(User.telegram_id == DEFAULT_ADMIN_TELEGRAM_ID)
    admin = db.execute(query).scalars().first()
    
    if admin:
        logger.info("Admin user already exists")
        return admin
    
    # Create admin user
    admin = User(
        telegram_id=DEFAULT_ADMIN_TELEGRAM_ID,
        username=DEFAULT_ADMIN_USERNAME,
        full_name="Admin User",
        role_id=roles["admin"].id,
        balance=0,
        is_active=True,
        is_banned=False,
        lang="fa"
    )
    
    db.add(admin)
    db.commit()
    logger.info("Admin user created successfully")
    return admin

def seed_locations(db: Session) -> Dict[str, Location]:
    """Seed server locations into the database."""
    logger.info("Seeding locations...")
    
    locations_data = [
        {"name": "Germany", "country_code": "DE", "flag": "🇩🇪", "is_active": True},
        {"name": "Netherlands", "country_code": "NL", "flag": "🇳🇱", "is_active": True},
        {"name": "United States", "country_code": "US", "flag": "🇺🇸", "is_active": True},
        {"name": "Singapore", "country_code": "SG", "flag": "🇸🇬", "is_active": True},
        {"name": "United Kingdom", "country_code": "GB", "flag": "🇬🇧", "is_active": True}
    ]
    
    locations = {}
    
    for location_data in locations_data:
        # Check if location exists
        query = select(Location).where(Location.country_code == location_data["country_code"])
        existing_location = db.execute(query).scalars().first()
        
        if existing_location:
            logger.info(f"Location '{location_data['name']}' already exists")
            locations[location_data["country_code"]] = existing_location
            continue
        
        # Create new location
        location = Location(
            name=location_data["name"],
            country_code=location_data["country_code"],
            flag=location_data["flag"],
            is_active=location_data["is_active"]
        )
        db.add(location)
        db.flush()
        
        locations[location_data["country_code"]] = location
        logger.info(f"Created location: {location_data['name']}")
    
    db.commit()
    return locations

def seed_plan_categories(db: Session) -> Dict[str, PlanCategory]:
    """Seed plan categories into the database."""
    logger.info("Seeding plan categories...")
    
    categories_data = [
        {"name": "Basic", "description": "Basic plans for regular usage", "color": "#28a745"},
        {"name": "Premium", "description": "Premium plans with more bandwidth", "color": "#dc3545"},
        {"name": "Business", "description": "Business plans for professional use", "color": "#007bff"},
    ]
    
    categories = {}
    
    for cat_data in categories_data:
        # Check if category exists
        query = select(PlanCategory).where(PlanCategory.name == cat_data["name"])
        existing_category = db.execute(query).scalars().first()
        
        if existing_category:
            logger.info(f"Plan category '{cat_data['name']}' already exists")
            categories[cat_data["name"]] = existing_category
            continue
        
        # Create new category
        category = PlanCategory(
            name=cat_data["name"],
            description=cat_data["description"],
            color=cat_data["color"]
        )
        db.add(category)
        db.flush()
        categories[cat_data["name"]] = category
        logger.info(f"Created plan category: {cat_data['name']}")
    
    db.commit()
    return categories

def seed_plans(db: Session, categories: Dict[str, PlanCategory]) -> None:
    """Seed plans into the database."""
    logger.info("Seeding plans...")
    
    plans_data = [
        {
            "name": "Basic Monthly",
            "description": "Basic monthly plan with 50GB traffic",
            "price": 10.0,
            "traffic": 50,  # in GB
            "duration": 30,  # in days
            "category": "Basic",
            "is_active": True
        },
        {
            "name": "Premium Monthly",
            "description": "Premium monthly plan with 100GB traffic",
            "price": 20.0,
            "traffic": 100,  # in GB
            "duration": 30,  # in days
            "category": "Premium",
            "is_active": True
        },
        {
            "name": "Business Monthly",
            "description": "Business monthly plan with 200GB traffic",
            "price": 40.0,
            "traffic": 200,  # in GB
            "duration": 30,  # in days
            "category": "Business",
            "is_active": True
        }
    ]
    
    for plan_data in plans_data:
        # Check if plan exists
        query = select(Plan).where(Plan.name == plan_data["name"])
        existing_plan = db.execute(query).scalars().first()
        
        if existing_plan:
            logger.info(f"Plan '{plan_data['name']}' already exists")
            continue
        
        # Create new plan
        plan = Plan(
            name=plan_data["name"],
            description=plan_data["description"],
            price=plan_data["price"],
            traffic=plan_data["traffic"] * 1024 * 1024 * 1024,  # Convert GB to bytes
            duration=timedelta(days=plan_data["duration"]),
            category_id=categories[plan_data["category"]].id,
            is_active=plan_data["is_active"]
        )
        db.add(plan)
    
    db.commit()
    logger.info("Plans added successfully")

def seed_settings(db: Session) -> None:
    """Seed basic settings into the database."""
    logger.info("Seeding settings...")
    
    # First check if the Settings table exists and has the expected columns
    try:
        settings_data = [
            {"key": "site_name", "value": "MoonVPN", "description": "Name of the site"},
            {"key": "site_url", "value": "https://moonvpn.example.com", "description": "URL of the site"}
        ]
        
        for setting_data in settings_data:
            # Try a different approach to check if setting exists
            query = text("SELECT id FROM settings WHERE `key` = :key")
            result = db.execute(query, {"key": setting_data["key"]})
            existing = result.scalar() is not None
            
            if existing:
                logger.info(f"Setting '{setting_data['key']}' already exists")
                continue
            
            # Insert setting using a raw SQL command
            insert_query = text(
                "INSERT INTO settings (`key`, value, description, is_public) VALUES (:key, :value, :description, :is_public)"
            )
            db.execute(
                insert_query, 
                {
                    "key": setting_data["key"], 
                    "value": setting_data["value"],
                    "description": setting_data["description"],
                    "is_public": True
                }
            )
        
        db.commit()
        logger.info("Settings added successfully")
    except Exception as e:
        logger.error(f"Error seeding settings: {e}")
        db.rollback()

def seed_panels(db: Session, locations: Dict[str, Location]) -> None:
    """Seed sample panels into the database."""
    logger.info("Seeding sample panels...")
    
    panels_data = [
        {
            "name": "Germany Panel 1",
            "url": "https://de1.moonvpn.example.com:2053",
            "username": "admin",
            "password": "adminpass",
            "location": "DE",
            "is_active": True
        },
        {
            "name": "Netherlands Panel 1",
            "url": "https://nl1.moonvpn.example.com:2053",
            "username": "admin",
            "password": "adminpass",
            "location": "NL",
            "is_active": True
        }
    ]
    
    for panel_data in panels_data:
        # Check if panel exists
        query = select(Panel).where(Panel.url == panel_data["url"])
        existing_panel = db.execute(query).scalars().first()
        
        if existing_panel:
            logger.info(f"Panel '{panel_data['name']}' already exists")
            continue
        
        # Create new panel with minimal fields
        panel = Panel(
            name=panel_data["name"],
            url=panel_data["url"],
            username=panel_data["username"],
            password=panel_data["password"],
            location_id=locations[panel_data["location"]].id,
            is_active=panel_data["is_active"]
        )
        db.add(panel)
    
    db.commit()
    logger.info("Panels added successfully")

def main():
    """Entry point for seeding database."""
    argparser = ArgumentParser(description="Seed database with initial data")
    argparser.add_argument(
        "-f", "--force", help="Force recreation of base data", action="store_true"
    )
    args = argparser.parse_args()
    
    logger.info("Starting database seeding process...")
    
    # Create a session
    db = SessionLocal()
    
    try:
        # Check if DB has been seeded already
        try:
            check = db.execute(select(func.count()).select_from(User))
            count = check.scalar()
            
            if count > 0 and not args.force:
                logger.info(
                    "Database already has users. Use --force to recreate base data."
                )
                return
            
            if args.force:
                logger.warning("Force flag set. Recreating base data...")
        except Exception as e:
            logger.warning(f"Error checking if database is seeded: {e}")
            logger.warning("Continuing with seeding...")
        
        # Seed data
        try:
            roles = seed_roles(db)
            seed_admin_user(db, roles)
            locations = seed_locations(db)
            categories = seed_plan_categories(db)
            seed_plans(db, categories)
            seed_settings(db)
            seed_panels(db, locations)
            
            logger.info("Database seeding completed successfully!")
        except Exception as e:
            logger.error(f"Error during seeding: {e}")
            db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main() 