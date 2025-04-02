from typing import Any, List, Optional
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Request
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.core.config import settings
from app.utils.url import get_base_url

router = APIRouter()


@router.post("/settings", response_model=schemas.AffiliateSettingsInDB)
def create_affiliate_settings(
    *,
    db: Session = Depends(deps.get_db),
    settings_in: schemas.AffiliateSettingsCreate,
    current_user: models.User = Depends(deps.get_current_admin_user),
) -> Any:
    """
    Create new affiliate program settings.
    """
    # Check if settings already exist
    existing_settings = crud.affiliate.get_settings(db)
    if existing_settings:
        raise HTTPException(
            status_code=400,
            detail="Affiliate settings already exist. Use the update endpoint instead.",
        )
    
    # Create new settings
    settings = crud.affiliate.create_settings(db, obj_in=settings_in)
    return settings


@router.get("/settings", response_model=schemas.AffiliateSettingsInDB)
def get_affiliate_settings(
    *,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Get current affiliate program settings.
    """
    settings = crud.affiliate.get_settings(db)
    if not settings:
        raise HTTPException(
            status_code=404,
            detail="Affiliate settings not found. An admin needs to create them first.",
        )
    return settings


@router.put("/settings/{settings_id}", response_model=schemas.AffiliateSettingsInDB)
def update_affiliate_settings(
    *,
    db: Session = Depends(deps.get_db),
    settings_id: int = Path(..., title="The ID of the settings to update"),
    settings_in: schemas.AffiliateSettingsUpdate,
    current_user: models.User = Depends(deps.get_current_admin_user),
) -> Any:
    """
    Update affiliate program settings.
    """
    settings = crud.affiliate.update_settings(db, settings_id=settings_id, obj_in=settings_in)
    if not settings:
        raise HTTPException(
            status_code=404,
            detail="Affiliate settings not found",
        )
    return settings


@router.post("/code", response_model=dict)
def generate_affiliate_code(
    *,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Generate or retrieve a user's affiliate code and full referral URL.
    """
    # Check if affiliate program is enabled
    settings = crud.affiliate.get_settings(db)
    if not settings or not settings.is_enabled:
        raise HTTPException(
            status_code=400,
            detail="Affiliate program is not enabled",
        )
    
    # Check if user is allowed to participate
    if not current_user.is_affiliate_enabled:
        raise HTTPException(
            status_code=403,
            detail="Your account is not eligible for the affiliate program",
        )
    
    # Generate or get existing code
    code = crud.affiliate.assign_affiliate_code(db, current_user.id)
    if not code:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate affiliate code",
        )
    
    # Construct referral URL
    base_url = settings.FRONTEND_BASE_URL  # From app settings
    referral_url = f"{base_url}/register?ref={code}"
    
    return {
        "code": code,
        "referral_url": referral_url
    }


@router.get("/stats", response_model=schemas.UserAffiliateStats)
def get_user_affiliate_stats(
    *,
    db: Session = Depends(deps.get_db),
    request: Request,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Get comprehensive statistics for the current user's affiliate activities.
    """
    # Check if affiliate program is enabled
    settings = crud.affiliate.get_settings(db)
    if not settings:
        raise HTTPException(
            status_code=404,
            detail="Affiliate program settings not found",
        )
    
    # Get detailed commission stats
    stats = crud.affiliate.get_user_commission_stats(db, current_user.id)
    
    # Get count of referred users
    referred_count = crud.affiliate.get_referred_users_count(db, current_user.id)
    
    # Generate or get the affiliate code
    if not current_user.affiliate_code:
        code = crud.affiliate.assign_affiliate_code(db, current_user.id)
    else:
        code = current_user.affiliate_code
    
    # Get base URL for the affiliate link
    base_url = get_base_url(request)
    affiliate_url = f"{base_url}/register?ref={code}"
    
    # Check if user can withdraw
    can_withdraw = (
        current_user.is_affiliate_enabled and 
        stats["current_balance"] >= settings.min_withdrawal_amount
    )
    
    return schemas.UserAffiliateStats(
        total_earnings=stats["total_earnings"],
        pending_earnings=stats["pending_earnings"],
        paid_earnings=stats["paid_earnings"],
        current_balance=stats["current_balance"],
        referred_users_count=referred_count,
        total_commission_count=stats["total_commissions"],
        affiliate_code=code,
        affiliate_url=affiliate_url,
        is_affiliate_enabled=current_user.is_affiliate_enabled,
        can_withdraw=can_withdraw,
        min_withdrawal_amount=settings.min_withdrawal_amount
    )


@router.get("/commissions", response_model=List[schemas.AffiliateCommissionResponse])
def get_user_commissions(
    *,
    db: Session = Depends(deps.get_db),
    status: Optional[str] = Query(None, description="Filter by commission status"),
    commission_type: Optional[str] = Query(None, description="Filter by commission type"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Get a list of the current user's affiliate commissions.
    """
    commissions = crud.affiliate.get_commissions(
        db, 
        user_id=current_user.id,
        status=status,
        commission_type=commission_type,
        skip=skip,
        limit=limit
    )
    
    # Enhance commissions with additional information
    result = []
    for comm in commissions:
        comm_data = schemas.AffiliateCommissionInDB.model_validate(comm)
        
        # Add referred user info if available
        if comm.referrer_id:
            referred_user = db.query(models.User).filter(models.User.id == comm.referrer_id).first()
            if referred_user:
                username = referred_user.username or f"{referred_user.first_name} {referred_user.last_name}".strip() or f"User {referred_user.id}"
                comm_data.referrer_name = username
        
        # Add order info if available
        if comm.order_id:
            order = db.query(models.Order).filter(models.Order.id == comm.order_id).first()
            if order:
                comm_data.order_info = f"Order #{order.id} ({order.total_amount})"
        
        # Add user name
        user = db.query(models.User).filter(models.User.id == comm.user_id).first()
        if user:
            comm_data.user_name = user.username or f"{user.first_name} {user.last_name}".strip() or f"User {user.id}"
        
        result.append(comm_data)
    
    return result


@router.get("/referred-users", response_model=List[schemas.User])
def get_referred_users(
    *,
    db: Session = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Get a list of users referred by the current user.
    """
    users = crud.affiliate.get_referred_users(db, current_user.id, skip=skip, limit=limit)
    return users


@router.post("/withdrawals", response_model=schemas.AffiliateWithdrawalResponse)
def create_withdrawal_request(
    *,
    db: Session = Depends(deps.get_db),
    withdrawal_in: schemas.AffiliateWithdrawalCreate,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Create a new withdrawal request.
    """
    withdrawal, message = crud.affiliate.create_withdrawal(db, current_user.id, withdrawal_in)
    if not withdrawal:
        raise HTTPException(
            status_code=400,
            detail=message,
        )
    
    # Format response with user info
    response = schemas.AffiliateWithdrawalInDB.model_validate(withdrawal)
    response.user_name = current_user.username or f"{current_user.first_name} {current_user.last_name}".strip() or f"User {current_user.id}"
    
    return response


@router.get("/withdrawals", response_model=List[schemas.AffiliateWithdrawalResponse])
def get_user_withdrawals(
    *,
    db: Session = Depends(deps.get_db),
    status: Optional[str] = Query(None, description="Filter by withdrawal status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Get a list of the current user's withdrawal requests.
    """
    withdrawals = crud.affiliate.get_withdrawals(
        db, 
        user_id=current_user.id,
        status=status,
        skip=skip,
        limit=limit
    )
    
    # Enhance withdrawals with additional information
    result = []
    for withdrawal in withdrawals:
        withdrawal_data = schemas.AffiliateWithdrawalInDB.model_validate(withdrawal)
        
        # Add user name
        withdrawal_data.user_name = current_user.username or f"{current_user.first_name} {current_user.last_name}".strip() or f"User {current_user.id}"
        
        # Add processor name if available
        if withdrawal.processed_by:
            processor = db.query(models.User).filter(models.User.id == withdrawal.processed_by).first()
            if processor:
                withdrawal_data.processor_name = processor.username or f"{processor.first_name} {processor.last_name}".strip() or f"Admin {processor.id}"
        
        result.append(withdrawal_data)
    
    return result


# ----- Admin endpoints -----

@router.get("/admin/commissions", response_model=List[schemas.AffiliateCommissionResponse])
def admin_get_all_commissions(
    *,
    db: Session = Depends(deps.get_db),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    status: Optional[str] = Query(None, description="Filter by commission status"),
    commission_type: Optional[str] = Query(None, description="Filter by commission type"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: models.User = Depends(deps.get_current_admin_user),
) -> Any:
    """
    Admin endpoint to get all commissions with optional filters.
    """
    commissions = crud.affiliate.get_commissions(
        db, 
        user_id=user_id,
        status=status,
        commission_type=commission_type,
        skip=skip,
        limit=limit
    )
    
    # Enhance commissions with additional information (same as user endpoint)
    result = []
    for comm in commissions:
        comm_data = schemas.AffiliateCommissionInDB.model_validate(comm)
        
        # Add referred user info if available
        if comm.referrer_id:
            referred_user = db.query(models.User).filter(models.User.id == comm.referrer_id).first()
            if referred_user:
                username = referred_user.username or f"{referred_user.first_name} {referred_user.last_name}".strip() or f"User {referred_user.id}"
                comm_data.referrer_name = username
        
        # Add order info if available
        if comm.order_id:
            order = db.query(models.Order).filter(models.Order.id == comm.order_id).first()
            if order:
                comm_data.order_info = f"Order #{order.id} ({order.total_amount})"
        
        # Add user name
        user = db.query(models.User).filter(models.User.id == comm.user_id).first()
        if user:
            comm_data.user_name = user.username or f"{user.first_name} {user.last_name}".strip() or f"User {user.id}"
        
        result.append(comm_data)
    
    return result


@router.put("/admin/commissions/{commission_id}", response_model=schemas.AffiliateCommissionResponse)
def admin_update_commission(
    *,
    db: Session = Depends(deps.get_db),
    commission_id: int = Path(..., title="The ID of the commission to update"),
    commission_in: schemas.AffiliateCommissionUpdate,
    current_user: models.User = Depends(deps.get_current_admin_user),
) -> Any:
    """
    Admin endpoint to update a commission status and details.
    """
    commission = crud.affiliate.update_commission(db, commission_id=commission_id, obj_in=commission_in)
    if not commission:
        raise HTTPException(
            status_code=404,
            detail="Commission not found",
        )
    
    # Format response with additional info
    response = schemas.AffiliateCommissionInDB.model_validate(commission)
    
    # Add user name
    user = db.query(models.User).filter(models.User.id == commission.user_id).first()
    if user:
        response.user_name = user.username or f"{user.first_name} {user.last_name}".strip() or f"User {user.id}"
    
    # Add referred user info if available
    if commission.referrer_id:
        referred_user = db.query(models.User).filter(models.User.id == commission.referrer_id).first()
        if referred_user:
            username = referred_user.username or f"{referred_user.first_name} {referred_user.last_name}".strip() or f"User {referred_user.id}"
            response.referrer_name = username
    
    # Add order info if available
    if commission.order_id:
        order = db.query(models.Order).filter(models.Order.id == commission.order_id).first()
        if order:
            response.order_info = f"Order #{order.id} ({order.total_amount})"
    
    return response


@router.get("/admin/withdrawals", response_model=List[schemas.AffiliateWithdrawalResponse])
def admin_get_all_withdrawals(
    *,
    db: Session = Depends(deps.get_db),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    status: Optional[str] = Query(None, description="Filter by withdrawal status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: models.User = Depends(deps.get_current_admin_user),
) -> Any:
    """
    Admin endpoint to get all withdrawal requests with optional filters.
    """
    withdrawals = crud.affiliate.get_withdrawals(
        db, 
        user_id=user_id,
        status=status,
        skip=skip,
        limit=limit
    )
    
    # Enhance withdrawals with additional information
    result = []
    for withdrawal in withdrawals:
        withdrawal_data = schemas.AffiliateWithdrawalInDB.model_validate(withdrawal)
        
        # Add user name
        user = db.query(models.User).filter(models.User.id == withdrawal.user_id).first()
        if user:
            withdrawal_data.user_name = user.username or f"{user.first_name} {user.last_name}".strip() or f"User {user.id}"
        
        # Add processor name if available
        if withdrawal.processed_by:
            processor = db.query(models.User).filter(models.User.id == withdrawal.processed_by).first()
            if processor:
                withdrawal_data.processor_name = processor.username or f"{processor.first_name} {processor.last_name}".strip() or f"Admin {processor.id}"
        
        result.append(withdrawal_data)
    
    return result


@router.put("/admin/withdrawals/{withdrawal_id}", response_model=schemas.AffiliateWithdrawalResponse)
def admin_update_withdrawal(
    *,
    db: Session = Depends(deps.get_db),
    withdrawal_id: int = Path(..., title="The ID of the withdrawal to update"),
    withdrawal_in: schemas.AffiliateWithdrawalUpdate,
    current_user: models.User = Depends(deps.get_current_admin_user),
) -> Any:
    """
    Admin endpoint to update a withdrawal request status.
    """
    withdrawal = crud.affiliate.update_withdrawal(
        db, 
        withdrawal_id=withdrawal_id, 
        admin_id=current_user.id,
        obj_in=withdrawal_in
    )
    if not withdrawal:
        raise HTTPException(
            status_code=404,
            detail="Withdrawal request not found",
        )
    
    # Format response with additional info
    response = schemas.AffiliateWithdrawalInDB.model_validate(withdrawal)
    
    # Add user name
    user = db.query(models.User).filter(models.User.id == withdrawal.user_id).first()
    if user:
        response.user_name = user.username or f"{user.first_name} {user.last_name}".strip() or f"User {user.id}"
    
    # Add processor name
    response.processor_name = current_user.username or f"{current_user.first_name} {current_user.last_name}".strip() or f"Admin {current_user.id}"
    
    return response


@router.post("/admin/report", response_model=schemas.AffiliateReport)
def admin_get_affiliate_report(
    *,
    db: Session = Depends(deps.get_db),
    params: schemas.AffiliateReportParams,
    current_user: models.User = Depends(deps.get_current_admin_user),
) -> Any:
    """
    Admin endpoint to generate a comprehensive report on the affiliate program.
    """
    report = crud.affiliate.generate_affiliate_report(db, params)
    return report


@router.post("/register-referral", response_model=dict)
def register_referral(
    *,
    db: Session = Depends(deps.get_db),
    referral_in: schemas.ReferralCreate,
) -> Any:
    """
    Public endpoint to register a referral when a user clicks an affiliate link.
    This is typically called during the registration process.
    """
    # Check if the referrer code is valid
    referrer = crud.affiliate.get_user_by_affiliate_code(db, referral_in.referrer_code)
    if not referrer:
        raise HTTPException(
            status_code=404,
            detail="Invalid referral code",
        )
    
    # Check if the referrer is eligible for the affiliate program
    if not referrer.is_affiliate_enabled:
        raise HTTPException(
            status_code=403,
            detail="This referral code is not valid",
        )
    
    # Check if affiliate program is enabled
    settings = crud.affiliate.get_settings(db)
    if not settings or not settings.is_enabled:
        raise HTTPException(
            status_code=400,
            detail="Affiliate program is not enabled",
        )
    
    return {
        "success": True,
        "referrer_id": referrer.id
    } 