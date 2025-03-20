import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from .connection import get_db_context
from .models.user import User
from .models.payments import (
    PaymentMethod,
    PaymentPlan,
    DiscountCode,
    CardOwner
)

# Configure logging
logger = logging.getLogger(__name__)


def seed_payment_methods(db: Session) -> None:
    """Seed initial payment methods."""
    payment_methods = [
        PaymentMethod(
            name="Card to Card",
            code="CARD",
            is_active=True,
            config={
                "min_amount": 10000,
                "max_amount": 1000000,
                "supported_banks": ["Melli", "Saderat", "Parsian"]
            }
        ),
        PaymentMethod(
            name="Zarinpal",
            code="ZARINPAL",
            is_active=True,
            config={
                "min_amount": 1000,
                "max_amount": 1000000,
                "sandbox": True
            }
        )
    ]
    
    for method in payment_methods:
        if not db.query(PaymentMethod).filter_by(code=method.code).first():
            db.add(method)
    
    db.commit()
    logger.info("Payment methods seeded successfully")


def seed_payment_plans(db: Session) -> None:
    """Seed initial payment plans."""
    payment_plans = [
        PaymentPlan(
            name="Basic",
            description="Basic VPN plan with standard features",
            price=99000,
            duration_days=30,
            is_active=True
        ),
        PaymentPlan(
            name="Premium",
            description="Premium VPN plan with advanced features",
            price=199000,
            duration_days=30,
            is_active=True
        ),
        PaymentPlan(
            name="Business",
            description="Business VPN plan with all features",
            price=399000,
            duration_days=30,
            is_active=True
        )
    ]
    
    for plan in payment_plans:
        if not db.query(PaymentPlan).filter_by(name=plan.name).first():
            db.add(plan)
    
    db.commit()
    logger.info("Payment plans seeded successfully")


def seed_discount_codes(db: Session) -> None:
    """Seed initial discount codes."""
    discount_codes = [
        DiscountCode(
            code="WELCOME10",
            discount_percent=10,
            max_uses=100,
            expires_at=datetime.utcnow() + timedelta(days=30),
            is_active=True
        ),
        DiscountCode(
            code="SPECIAL20",
            discount_percent=20,
            max_uses=50,
            expires_at=datetime.utcnow() + timedelta(days=15),
            is_active=True
        )
    ]
    
    for code in discount_codes:
        if not db.query(DiscountCode).filter_by(code=code.code).first():
            db.add(code)
    
    db.commit()
    logger.info("Discount codes seeded successfully")


def seed_card_owners(db: Session) -> None:
    """Seed initial card owners."""
    card_owners = [
        CardOwner(
            name="Support Team",
            card_number="6037991123456789",
            bank_name="Melli",
            is_verified=True
        ),
        CardOwner(
            name="Support Team",
            card_number="6037991987654321",
            bank_name="Saderat",
            is_verified=True
        )
    ]
    
    for owner in card_owners:
        if not db.query(CardOwner).filter_by(card_number=owner.card_number).first():
            db.add(owner)
    
    db.commit()
    logger.info("Card owners seeded successfully")


def seed_database() -> None:
    """Seed database with initial data."""
    try:
        with get_db_context() as db:
            # Seed payment methods
            seed_payment_methods(db)
            
            # Seed payment plans
            seed_payment_plans(db)
            
            # Seed discount codes
            seed_discount_codes(db)
            
            # Seed card owners
            seed_card_owners(db)
            
            logger.info("Database seeding completed successfully")
    except Exception as e:
        logger.error(f"Database seeding failed: {str(e)}")
        raise


if __name__ == "__main__":
    seed_database() 