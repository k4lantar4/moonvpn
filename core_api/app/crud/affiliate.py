from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
import secrets
import string

from sqlalchemy import func, desc, and_, or_
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder

from app.models.affiliate import (
    AffiliateCommission, 
    AffiliateSettings, 
    AffiliateWithdrawal,
    CommissionStatus,
    CommissionType,
    WithdrawalStatus
)
from app.models.user import User
from app.models.order import Order
from app.schemas.affiliate import (
    AffiliateCommissionCreate,
    AffiliateCommissionUpdate,
    AffiliateSettingsCreate,
    AffiliateSettingsUpdate,
    AffiliateWithdrawalCreate,
    AffiliateWithdrawalUpdate,
    AffiliateReportParams
)


# ----- Commission CRUD Operations -----

def create_commission(db: Session, obj_in: AffiliateCommissionCreate) -> AffiliateCommission:
    """Create a new affiliate commission record."""
    commission_data = obj_in.model_dump(exclude_unset=True)
    commission_data["status"] = CommissionStatus.PENDING.value  # Default status is pending
    
    db_obj = AffiliateCommission(**commission_data)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    
    # Update user's affiliate balance if needed
    _update_user_balance(db, db_obj.user_id)
    
    return db_obj


def get_commission(db: Session, commission_id: int) -> Optional[AffiliateCommission]:
    """Get an affiliate commission by ID."""
    return db.query(AffiliateCommission).filter(AffiliateCommission.id == commission_id).first()


def get_commissions(
    db: Session, 
    user_id: Optional[int] = None,
    status: Optional[str] = None,
    commission_type: Optional[str] = None,
    skip: int = 0, 
    limit: int = 100
) -> List[AffiliateCommission]:
    """Get a list of affiliate commissions with optional filters."""
    query = db.query(AffiliateCommission)
    
    if user_id:
        query = query.filter(AffiliateCommission.user_id == user_id)
    
    if status:
        query = query.filter(AffiliateCommission.status == status)
    
    if commission_type:
        query = query.filter(AffiliateCommission.commission_type == commission_type)
    
    return query.order_by(desc(AffiliateCommission.created_at)).offset(skip).limit(limit).all()


def get_commissions_count(
    db: Session, 
    user_id: Optional[int] = None,
    status: Optional[str] = None,
    commission_type: Optional[str] = None
) -> int:
    """Get the total count of affiliate commissions with optional filters."""
    query = db.query(func.count(AffiliateCommission.id))
    
    if user_id:
        query = query.filter(AffiliateCommission.user_id == user_id)
    
    if status:
        query = query.filter(AffiliateCommission.status == status)
    
    if commission_type:
        query = query.filter(AffiliateCommission.commission_type == commission_type)
    
    return query.scalar()


def update_commission(
    db: Session, 
    commission_id: int, 
    obj_in: AffiliateCommissionUpdate
) -> Optional[AffiliateCommission]:
    """Update an affiliate commission."""
    db_obj = get_commission(db, commission_id)
    if not db_obj:
        return None
    
    update_data = obj_in.model_dump(exclude_unset=True)
    
    # If changing status to PAID, set the paid_at timestamp
    if "status" in update_data and update_data["status"] == CommissionStatus.PAID.value:
        update_data["paid_at"] = datetime.utcnow()
    
    # Apply the updates
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    
    db.commit()
    db.refresh(db_obj)
    
    # Update user's affiliate balance
    _update_user_balance(db, db_obj.user_id)
    
    return db_obj


def get_user_commission_stats(db: Session, user_id: int) -> Dict[str, Any]:
    """Get comprehensive commission statistics for a user."""
    
    # Get total earnings across all statuses
    total_earnings = db.query(
        func.sum(AffiliateCommission.amount)
    ).filter(
        AffiliateCommission.user_id == user_id
    ).scalar() or Decimal('0')
    
    # Get pending earnings
    pending_earnings = db.query(
        func.sum(AffiliateCommission.amount)
    ).filter(
        AffiliateCommission.user_id == user_id,
        AffiliateCommission.status == CommissionStatus.PENDING.value
    ).scalar() or Decimal('0')
    
    # Get approved earnings
    approved_earnings = db.query(
        func.sum(AffiliateCommission.amount)
    ).filter(
        AffiliateCommission.user_id == user_id,
        AffiliateCommission.status == CommissionStatus.APPROVED.value
    ).scalar() or Decimal('0')
    
    # Get paid earnings
    paid_earnings = db.query(
        func.sum(AffiliateCommission.amount)
    ).filter(
        AffiliateCommission.user_id == user_id,
        AffiliateCommission.status == CommissionStatus.PAID.value
    ).scalar() or Decimal('0')
    
    # Get total number of commissions
    total_commissions = db.query(
        func.count(AffiliateCommission.id)
    ).filter(
        AffiliateCommission.user_id == user_id
    ).scalar() or 0
    
    # Get commissions by type
    order_commissions = db.query(
        func.count(AffiliateCommission.id)
    ).filter(
        AffiliateCommission.user_id == user_id,
        AffiliateCommission.commission_type == CommissionType.ORDER.value
    ).scalar() or 0
    
    signup_commissions = db.query(
        func.count(AffiliateCommission.id)
    ).filter(
        AffiliateCommission.user_id == user_id,
        AffiliateCommission.commission_type == CommissionType.SIGNUP.value
    ).scalar() or 0
    
    bonus_commissions = db.query(
        func.count(AffiliateCommission.id)
    ).filter(
        AffiliateCommission.user_id == user_id,
        AffiliateCommission.commission_type == CommissionType.BONUS.value
    ).scalar() or 0
    
    return {
        "total_earnings": total_earnings,
        "pending_earnings": pending_earnings,
        "approved_earnings": approved_earnings,
        "paid_earnings": paid_earnings,
        "current_balance": pending_earnings + approved_earnings,  # Available balance for withdrawal
        "total_commissions": total_commissions,
        "order_commissions": order_commissions,
        "signup_commissions": signup_commissions,
        "bonus_commissions": bonus_commissions
    }


# ----- Settings CRUD Operations -----

def create_settings(db: Session, obj_in: AffiliateSettingsCreate) -> AffiliateSettings:
    """Create affiliate program settings."""
    settings_data = obj_in.model_dump(exclude_unset=True)
    
    db_obj = AffiliateSettings(**settings_data)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    
    return db_obj


def get_settings(db: Session) -> Optional[AffiliateSettings]:
    """Get the current affiliate program settings."""
    return db.query(AffiliateSettings).order_by(desc(AffiliateSettings.created_at)).first()


def update_settings(
    db: Session, 
    settings_id: int, 
    obj_in: AffiliateSettingsUpdate
) -> Optional[AffiliateSettings]:
    """Update affiliate program settings."""
    db_obj = db.query(AffiliateSettings).filter(AffiliateSettings.id == settings_id).first()
    if not db_obj:
        return None
    
    update_data = obj_in.model_dump(exclude_unset=True)
    
    # Apply the updates
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    
    db_obj.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_obj)
    
    return db_obj


# ----- Withdrawal CRUD Operations -----

def create_withdrawal(
    db: Session, 
    user_id: int, 
    obj_in: AffiliateWithdrawalCreate
) -> Tuple[Optional[AffiliateWithdrawal], str]:
    """
    Create a withdrawal request.
    Returns a tuple of (withdrawal_object, message).
    If withdrawal cannot be created, returns (None, error_message).
    """
    # Check if user has sufficient balance
    settings = get_settings(db)
    if not settings:
        return None, "Affiliate program settings not found"
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None, "User not found"
    
    if not user.is_affiliate_enabled:
        return None, "Affiliate program is not enabled for this user"
    
    stats = get_user_commission_stats(db, user_id)
    available_balance = stats["current_balance"]
    
    if obj_in.amount > available_balance:
        return None, f"Insufficient balance. Available: {available_balance}"
    
    if obj_in.amount < settings.min_withdrawal_amount:
        return None, f"Minimum withdrawal amount is {settings.min_withdrawal_amount}"
    
    # Create the withdrawal request
    withdrawal_data = obj_in.model_dump(exclude_unset=True)
    withdrawal_data["user_id"] = user_id
    withdrawal_data["status"] = WithdrawalStatus.PENDING.value
    
    db_obj = AffiliateWithdrawal(**withdrawal_data)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    
    return db_obj, "Withdrawal request created successfully"


def get_withdrawal(db: Session, withdrawal_id: int) -> Optional[AffiliateWithdrawal]:
    """Get a withdrawal request by ID."""
    return db.query(AffiliateWithdrawal).filter(AffiliateWithdrawal.id == withdrawal_id).first()


def get_withdrawals(
    db: Session, 
    user_id: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = 0, 
    limit: int = 100
) -> List[AffiliateWithdrawal]:
    """Get a list of withdrawal requests with optional filters."""
    query = db.query(AffiliateWithdrawal)
    
    if user_id:
        query = query.filter(AffiliateWithdrawal.user_id == user_id)
    
    if status:
        query = query.filter(AffiliateWithdrawal.status == status)
    
    return query.order_by(desc(AffiliateWithdrawal.created_at)).offset(skip).limit(limit).all()


def get_withdrawals_count(
    db: Session, 
    user_id: Optional[int] = None,
    status: Optional[str] = None
) -> int:
    """Get the total count of withdrawal requests with optional filters."""
    query = db.query(func.count(AffiliateWithdrawal.id))
    
    if user_id:
        query = query.filter(AffiliateWithdrawal.user_id == user_id)
    
    if status:
        query = query.filter(AffiliateWithdrawal.status == status)
    
    return query.scalar()


def update_withdrawal(
    db: Session, 
    withdrawal_id: int, 
    admin_id: int,
    obj_in: AffiliateWithdrawalUpdate
) -> Optional[AffiliateWithdrawal]:
    """Update a withdrawal request."""
    db_obj = get_withdrawal(db, withdrawal_id)
    if not db_obj:
        return None
    
    update_data = obj_in.model_dump(exclude_unset=True)
    
    # If changing status to approved/completed/rejected, set the processed info
    if "status" in update_data and update_data["status"] in [
        WithdrawalStatus.APPROVED.value,
        WithdrawalStatus.COMPLETED.value,
        WithdrawalStatus.REJECTED.value
    ]:
        update_data["processed_at"] = datetime.utcnow()
        update_data["processed_by"] = admin_id
    
    # Apply the updates
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    
    db.commit()
    db.refresh(db_obj)
    
    return db_obj


# ----- Referral & Affiliate Code Operations -----

def generate_affiliate_code(length: int = 8) -> str:
    """Generate a random affiliate code."""
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def assign_affiliate_code(db: Session, user_id: int) -> Optional[str]:
    """Assign a unique affiliate code to a user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None
    
    # If user already has a code, return it
    if user.affiliate_code:
        return user.affiliate_code
    
    # Get settings to determine code length
    settings = get_settings(db)
    code_length = settings.code_length if settings else 8
    
    # Generate a unique code that doesn't exist yet
    while True:
        code = generate_affiliate_code(code_length)
        exists = db.query(User).filter(User.affiliate_code == code).first()
        if not exists:
            break
    
    # Assign the code to the user
    user.affiliate_code = code
    db.commit()
    
    return code


def get_user_by_affiliate_code(db: Session, code: str) -> Optional[User]:
    """Get a user by their affiliate code."""
    return db.query(User).filter(User.affiliate_code == code).first()


def track_referral(db: Session, referrer_id: int, referred_id: int) -> bool:
    """Track a user referral relationship."""
    referred_user = db.query(User).filter(User.id == referred_id).first()
    if not referred_user:
        return False
    
    # Set the referrer_id
    referred_user.referrer_id = referrer_id
    db.commit()
    
    return True


def create_order_commission(
    db: Session, 
    order_id: int,
    percentage: Optional[Decimal] = None
) -> Optional[AffiliateCommission]:
    """
    Create a commission for an order purchase.
    This is called when an order is created by a referred user.
    """
    # Get the order details
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order or not order.user_id:
        return None
    
    # Get the referred user
    referred_user = db.query(User).filter(User.id == order.user_id).first()
    if not referred_user or not referred_user.referrer_id:
        return None
    
    # Get the referrer (affiliate)
    referrer = db.query(User).filter(User.id == referred_user.referrer_id).first()
    if not referrer or not referrer.is_affiliate_enabled:
        return None
    
    # Get program settings
    settings = get_settings(db)
    if not settings or not settings.is_enabled:
        return None
    
    # Calculate commission amount
    commission_percentage = percentage if percentage is not None else settings.commission_percentage
    commission_amount = (Decimal(order.total_amount) * commission_percentage) / Decimal(100)
    
    if commission_amount <= Decimal(0):
        return None
    
    # Create commission record
    commission_data = {
        "user_id": referrer.id,
        "referrer_id": referred_user.id,
        "order_id": order.id,
        "amount": commission_amount,
        "percentage": commission_percentage,
        "commission_type": CommissionType.ORDER.value,
        "status": CommissionStatus.PENDING.value,
        "description": f"Commission for order #{order.id}"
    }
    
    db_obj = AffiliateCommission(**commission_data)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    
    # Update affiliate balance
    _update_user_balance(db, referrer.id)
    
    return db_obj


def create_signup_commission(
    db: Session, 
    referrer_id: int,
    referred_id: int
) -> Optional[AffiliateCommission]:
    """
    Create a commission for a new user signup through an affiliate link.
    This is a fixed bonus that can be set in the admin settings.
    """
    # Implementation will depend on your business logic for signup bonuses
    # This is just a placeholder function that you can implement later
    return None


def get_referred_users(
    db: Session, 
    user_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[User]:
    """Get a list of users referred by the specified user."""
    return db.query(User).filter(User.referrer_id == user_id).offset(skip).limit(limit).all()


def get_referred_users_count(db: Session, user_id: int) -> int:
    """Get the total count of users referred by the specified user."""
    return db.query(func.count(User.id)).filter(User.referrer_id == user_id).scalar()


# ----- Reports -----

def generate_affiliate_report(
    db: Session, 
    params: AffiliateReportParams
) -> Dict[str, Any]:
    """Generate a report on affiliate program performance."""
    # Time period filtering
    date_filter = []
    if params.start_date:
        date_filter.append(AffiliateCommission.created_at >= params.start_date)
    if params.end_date:
        date_filter.append(AffiliateCommission.created_at <= params.end_date)
    
    # Status filtering
    status_filter = []
    if params.status:
        status_filter.append(AffiliateCommission.status == params.status)
    
    # Type filtering
    type_filter = []
    if params.commission_type:
        type_filter.append(AffiliateCommission.commission_type == params.commission_type)
    
    # User filtering
    user_filter = []
    if params.user_id:
        user_filter.append(AffiliateCommission.user_id == params.user_id)
    
    # Combine all filters
    filters = and_(
        *date_filter,
        *status_filter,
        *type_filter,
        *user_filter
    ) if (date_filter or status_filter or type_filter or user_filter) else True
    
    # Total commissions and amount
    total_query = db.query(
        func.count(AffiliateCommission.id),
        func.sum(AffiliateCommission.amount)
    ).filter(filters)
    
    total_count, total_amount = total_query.first()
    total_count = total_count or 0
    total_amount = total_amount or Decimal('0')
    
    # Active affiliates (users with at least one commission)
    active_affiliates = db.query(
        func.count(func.distinct(AffiliateCommission.user_id))
    ).filter(filters).scalar() or 0
    
    # Group by status
    status_counts = {}
    status_query = db.query(
        AffiliateCommission.status,
        func.count(AffiliateCommission.id)
    ).filter(filters).group_by(AffiliateCommission.status)
    
    for status, count in status_query:
        status_counts[status] = count
    
    # Group by type
    type_counts = {}
    type_query = db.query(
        AffiliateCommission.commission_type,
        func.count(AffiliateCommission.id)
    ).filter(filters).group_by(AffiliateCommission.commission_type)
    
    for commission_type, count in type_query:
        type_counts[commission_type] = count
    
    # Top affiliates
    top_affiliates_query = db.query(
        AffiliateCommission.user_id,
        User.username,
        func.count(AffiliateCommission.id).label('commission_count'),
        func.sum(AffiliateCommission.amount).label('total_earned')
    ).join(
        User, User.id == AffiliateCommission.user_id
    ).filter(
        filters
    ).group_by(
        AffiliateCommission.user_id,
        User.username
    ).order_by(
        desc('total_earned')
    ).limit(10)
    
    top_affiliates = []
    for user_id, username, count, amount in top_affiliates_query:
        top_affiliates.append({
            "user_id": user_id,
            "username": username,
            "commission_count": count,
            "total_earned": amount
        })
    
    # Period stats (for time series)
    period_stats = {}
    # Implementation depends on desired granularity (daily, weekly, monthly)
    # This is a placeholder
    
    return {
        "total_commissions": total_count,
        "total_amount": total_amount,
        "active_affiliates": active_affiliates,
        "commission_by_status": status_counts,
        "commission_by_type": type_counts,
        "top_affiliates": top_affiliates,
        "period_stats": period_stats
    }


# ----- Helper Functions -----

def _update_user_balance(db: Session, user_id: int) -> bool:
    """
    Update a user's affiliate balance based on their pending and approved commissions.
    This is called internally after commissions are created or updated.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False
    
    # Calculate available balance (pending + approved commissions)
    available_balance = db.query(
        func.sum(AffiliateCommission.amount)
    ).filter(
        AffiliateCommission.user_id == user_id,
        AffiliateCommission.status.in_([
            CommissionStatus.PENDING.value,
            CommissionStatus.APPROVED.value
        ])
    ).scalar() or Decimal('0')
    
    # Update the user's balance
    user.affiliate_balance = available_balance
    db.commit()
    
    return True 