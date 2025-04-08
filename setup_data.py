#!/usr/bin/env python
# coding: utf-8

import logging
from datetime import datetime, timedelta
from core.database.session import get_db_context
from api.models import (
    Panel, Plan, Location, PlanCategory, User
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def add_test_panel():
    """Add a test panel to the database."""
    with get_db_context() as db:
        # Check if a panel already exists
        if db.query(Panel).count() > 0:
            logger.info("Panel already exists. Skipping panel creation.")
            return
        
        # Get Germany location (ID: 1)
        location = db.query(Location).filter(Location.id == 1).first()
        if not location:
            logger.error("Germany location not found!")
            return
        
        # Get admin user
        admin = db.query(User).filter(User.role_id == 1).first()
        if not admin:
            logger.error("Admin user not found!")
            return
        
        # Create test panel
        panel = Panel(
            name="Test Panel Germany",
            url="https://example.com:8443",  # این را به یک آدرس معتبر تغییر دهید
            api_path="/panel/api",
            login_path="/login",
            username="admin",
            password="admin123",
            panel_type="3X-UI",
            location_id=location.id,
            server_ip="198.51.100.42",  # یک آی‌پی تست
            server_type="VPS",
            is_active=True,
            is_healthy=True,
            max_clients=200,
            current_clients=0,
            traffic_limit=10000,  # 10TB
            traffic_used=0,
            priority=1,
            created_by=admin.id,
            created_at=datetime.utcnow(),
            geo_location="Frankfurt",
            provider="Hetzner",
            datacenter="FSN1",
            is_premium=True,
            network_speed="1 Gbps",
            server_specs="4 vCPU, 8GB RAM, 100GB SSD"
        )
        
        db.add(panel)
        db.commit()
        logger.info(f"Created test panel: {panel.name} (ID: {panel.id})")

def add_test_plans():
    """Add test plans to the database."""
    with get_db_context() as db:
        # Check if plans already exist
        if db.query(Plan).count() > 0:
            logger.info("Plans already exist. Skipping plan creation.")
            return
        
        # Define plans
        basic_category = db.query(PlanCategory).filter(PlanCategory.name == "Basic").first()
        premium_category = db.query(PlanCategory).filter(PlanCategory.name == "Premium").first()
        business_category = db.query(PlanCategory).filter(PlanCategory.name == "Business").first()
        
        if not all([basic_category, premium_category, business_category]):
            logger.error("One or more plan categories not found!")
            return
        
        # Create basic plans
        basic_plans = [
            Plan(
                name="طرح اقتصادی ۱ ماهه",
                traffic=50,  # 50GB
                days=30,
                price=79000.0,
                description="طرح ارزان قیمت با ترافیک محدود برای استفاده شخصی 🌟",
                features="سرعت مناسب,پشتیبانی ۲۴/۷,بدون محدودیت دستگاه",
                is_active=True,
                is_featured=False,
                max_clients=None,
                protocols="VMESS,VLESS",
                category_id=basic_category.id,
                sorting_order=1,
                created_at=datetime.utcnow()
            ),
            Plan(
                name="طرح اقتصادی ۳ ماهه",
                traffic=150,  # 150GB
                days=90,
                price=199000.0,
                description="طرح اقتصادی با ترافیک مناسب برای ۳ ماه استفاده 🔥",
                features="سرعت مناسب,پشتیبانی ۲۴/۷,بدون محدودیت دستگاه",
                is_active=True,
                is_featured=True,
                max_clients=None,
                protocols="VMESS,VLESS",
                category_id=basic_category.id,
                sorting_order=2,
                created_at=datetime.utcnow()
            ),
        ]
        
        # Create premium plans
        premium_plans = [
            Plan(
                name="طرح حرفه‌ای ۱ ماهه",
                traffic=100,  # 100GB
                days=30,
                price=129000.0,
                description="طرح پرسرعت با ترافیک بالا برای استفاده حرفه‌ای ⚡",
                features="سرعت بالا,پشتیبانی VIP,بدون محدودیت دستگاه,لوکیشن‌های متنوع",
                is_active=True,
                is_featured=True,
                max_clients=None,
                protocols="VMESS,VLESS",
                category_id=premium_category.id,
                sorting_order=1,
                created_at=datetime.utcnow()
            ),
            Plan(
                name="طرح حرفه‌ای ۳ ماهه",
                traffic=300,  # 300GB
                days=90,
                price=299000.0,
                description="طرح پرسرعت با ترافیک بالا برای استفاده حرفه‌ای به مدت ۳ ماه ⭐",
                features="سرعت بالا,پشتیبانی VIP,بدون محدودیت دستگاه,لوکیشن‌های متنوع",
                is_active=True,
                is_featured=True,
                max_clients=None,
                protocols="VMESS,VLESS",
                category_id=premium_category.id,
                sorting_order=2,
                created_at=datetime.utcnow()
            ),
        ]
        
        # Create business plans
        business_plans = [
            Plan(
                name="طرح تجاری ۱ ماهه",
                traffic=200,  # 200GB
                days=30,
                price=249000.0,
                description="طرح فوق سریع با بالاترین کیفیت برای مصارف تجاری و شرکت‌ها 🏆",
                features="بالاترین سرعت,پشتیبانی اختصاصی,بدون محدودیت دستگاه,اولویت ترافیک,لوکیشن‌های ویژه",
                is_active=True,
                is_featured=False,
                max_clients=None,
                protocols="VMESS,VLESS",
                category_id=business_category.id,
                sorting_order=1,
                created_at=datetime.utcnow()
            ),
            Plan(
                name="طرح تجاری ۳ ماهه",
                traffic=600,  # 600GB
                days=90,
                price=649000.0,
                description="طرح فوق سریع با بالاترین کیفیت برای مصارف تجاری و شرکت‌ها به مدت ۳ ماه 💎",
                features="بالاترین سرعت,پشتیبانی اختصاصی,بدون محدودیت دستگاه,اولویت ترافیک,لوکیشن‌های ویژه",
                is_active=True,
                is_featured=True,
                max_clients=None,
                protocols="VMESS,VLESS",
                category_id=business_category.id,
                sorting_order=2,
                created_at=datetime.utcnow()
            ),
        ]
        
        # Add all plans to the database
        db.add_all(basic_plans + premium_plans + business_plans)
        db.commit()
        logger.info(f"Created {len(basic_plans) + len(premium_plans) + len(business_plans)} test plans")

def add_bank_card():
    """Add a bank card for payment."""
    with get_db_context() as db:
        from api.models import BankCard
        
        # Check if bank card already exists
        if db.query(BankCard).count() > 0:
            logger.info("Bank card already exists. Skipping bank card creation.")
            return
        
        # Create bank card
        bank_card = BankCard(
            bank_name="بانک ملت",
            card_number="6104337895624813",
            account_number="9876543210",
            owner_name="محمد حسینی",
            is_active=True,
            rotation_priority=1,
            daily_limit=20000000.0,  # 20 میلیون تومان
            monthly_limit=100000000.0,  # 100 میلیون تومان
            created_at=datetime.utcnow()
        )
        
        db.add(bank_card)
        db.commit()
        logger.info(f"Created bank card: {bank_card.card_number}")

if __name__ == "__main__":
    logger.info("Setting up initial data...")
    add_test_panel()
    add_test_plans()
    add_bank_card()
    logger.info("Initial data setup complete!") 