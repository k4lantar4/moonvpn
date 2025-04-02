from typing import Optional
from decimal import Decimal
from sqlalchemy.orm import Session

from app import crud, models
from app.core.config import settings
from app.models.affiliate import AffiliateCommission, CommissionType, CommissionStatus


class AffiliateHandler:
    """
    Handler class to manage affiliate-related functionality throughout the application.
    This class is used to handle creation of commissions when orders are placed,
    track referrals, and manage the affiliate program.
    """
    
    @staticmethod
    def process_order_commission(
        db: Session, 
        order: models.Order
    ) -> Optional[AffiliateCommission]:
        """
        Process a commission for an order if the user was referred by an affiliate.
        This should be called after an order is created.
        
        Args:
            db: Database session
            order: The order that was created
            
        Returns:
            The created commission object or None if no commission was created
        """
        if not order or not order.user_id:
            return None
        
        # Check if affiliate program is enabled
        affiliate_settings = crud.affiliate.get_settings(db)
        if not affiliate_settings or not affiliate_settings.is_enabled:
            return None
        
        # Check if user was referred
        user = db.query(models.User).filter(models.User.id == order.user_id).first()
        if not user or not user.referrer_id:
            return None
        
        # Check if referrer is eligible
        referrer = db.query(models.User).filter(models.User.id == user.referrer_id).first()
        if not referrer or not referrer.is_affiliate_enabled:
            return None
        
        # Calculate commission
        commission_percentage = affiliate_settings.commission_percentage
        commission_amount = (Decimal(order.total_amount) * commission_percentage) / Decimal(100)
        
        # Skip if amount is too small
        if commission_amount <= Decimal('0'):
            return None
        
        # Create commission record
        commission_data = {
            "user_id": referrer.id,
            "referrer_id": user.id,
            "order_id": order.id,
            "amount": commission_amount,
            "percentage": commission_percentage,
            "commission_type": CommissionType.ORDER.value,
            "status": CommissionStatus.PENDING.value,
            "description": f"Commission for order #{order.id} (₽{order.total_amount})"
        }
        
        commission = AffiliateCommission(**commission_data)
        db.add(commission)
        db.commit()
        db.refresh(commission)
        
        # Update referrer's affiliate balance
        crud.affiliate._update_user_balance(db, referrer.id)
        
        return commission
    
    @staticmethod
    def process_signup_bonus(
        db: Session, 
        referrer_id: int,
        referred_id: int,
        bonus_amount: Optional[Decimal] = None
    ) -> Optional[AffiliateCommission]:
        """
        Process a signup bonus for a referrer when a new user signs up using their referral link.
        This should be called after a new user is created with a referrer.
        
        Args:
            db: Database session
            referrer_id: The ID of the referrer user
            referred_id: The ID of the newly registered user
            bonus_amount: Optional custom bonus amount, otherwise uses the default from settings
            
        Returns:
            The created commission object or None if no commission was created
        """
        # Check if affiliate program is enabled
        affiliate_settings = crud.affiliate.get_settings(db)
        if not affiliate_settings or not affiliate_settings.is_enabled:
            return None
        
        # Only process signup bonuses if they're enabled in the settings
        # (This feature can be implemented when needed)
        if not getattr(affiliate_settings, 'signup_bonus_enabled', False):
            return None
        
        # Check if referrer is eligible
        referrer = db.query(models.User).filter(models.User.id == referrer_id).first()
        if not referrer or not referrer.is_affiliate_enabled:
            return None
        
        # Check if referred user exists
        referred = db.query(models.User).filter(models.User.id == referred_id).first()
        if not referred:
            return None
        
        # Use provided bonus amount or get from settings
        amount = bonus_amount if bonus_amount is not None else getattr(
            affiliate_settings, 'signup_bonus_amount', Decimal('0')
        )
        
        # Skip if amount is too small
        if amount <= Decimal('0'):
            return None
        
        # Create commission record
        commission_data = {
            "user_id": referrer.id,
            "referrer_id": referred.id,
            "amount": amount,
            "percentage": Decimal('0'),  # Not percentage-based
            "commission_type": CommissionType.SIGNUP.value,
            "status": CommissionStatus.PENDING.value,
            "description": f"Signup bonus for referring user {referred.username or referred.id}"
        }
        
        commission = AffiliateCommission(**commission_data)
        db.add(commission)
        db.commit()
        db.refresh(commission)
        
        # Update referrer's affiliate balance
        crud.affiliate._update_user_balance(db, referrer.id)
        
        return commission
    
    @staticmethod
    def track_referral(
        db: Session, 
        referrer_code: str, 
        user_id: int
    ) -> bool:
        """
        Track a referral relationship between users.
        This should be called during the registration process if a referral code is provided.
        
        Args:
            db: Database session
            referrer_code: The affiliate code of the referrer
            user_id: The ID of the newly registered user
            
        Returns:
            True if the referral was tracked successfully, False otherwise
        """
        # Check if affiliate program is enabled
        affiliate_settings = crud.affiliate.get_settings(db)
        if not affiliate_settings or not affiliate_settings.is_enabled:
            return False
        
        # Get the referrer by affiliate code
        referrer = crud.affiliate.get_user_by_affiliate_code(db, referrer_code)
        if not referrer or not referrer.is_affiliate_enabled:
            return False
        
        # Get the new user
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            return False
        
        # Set the referrer_id
        user.referrer_id = referrer.id
        db.commit()
        
        # Process signup bonus if enabled
        AffiliateHandler.process_signup_bonus(db, referrer.id, user.id)
        
        return True 