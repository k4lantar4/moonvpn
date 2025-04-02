from typing import Any, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query
from fastapi.encoders import jsonable_encoder
from pydantic.networks import EmailStr
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.core.config import settings
from app.core.affiliate_handler import AffiliateHandler
from app.utils.telegram import send_notification

router = APIRouter()


@router.get("/", response_model=schemas.UserList)
def read_users(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_admin_user),
) -> Any:
    """
    Retrieve users.
    """
    users = crud.user.get_multi(db, skip=skip, limit=limit)
    total = crud.user.count(db)
    return {"users": users, "total": total}


@router.post("/", response_model=schemas.User)
def create_user(
    *,
    db: Session = Depends(deps.get_db),
    user_in: schemas.UserCreate,
    current_user: models.User = Depends(deps.get_current_admin_user),
) -> Any:
    """
    Create new user.
    """
    user = crud.user.get_by_telegram_id(db, telegram_id=user_in.telegram_id)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this telegram ID already exists in the system.",
        )
    user = crud.user.create(db, obj_in=user_in)
    
    # Handle referral tracking if a referral code is provided
    if hasattr(user_in, 'affiliate_code') and user_in.affiliate_code:
        AffiliateHandler.track_referral(db, user_in.affiliate_code, user.id)
    
    return user


@router.post("/register", response_model=schemas.User)
def register_user(
    *,
    db: Session = Depends(deps.get_db),
    user_in: schemas.UserCreate,
    referrer_code: Optional[str] = Query(None, description="Affiliate code of the referrer"),
) -> Any:
    """
    Create new user without the need to be logged in.
    """
    # First check if user exists
    user = crud.user.get_by_telegram_id(db, telegram_id=user_in.telegram_id)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this telegram ID already exists in the system.",
        )
    
    # Create the new user
    user = crud.user.create(db, obj_in=user_in)
    
    # Handle referral tracking if a referral code is provided
    if referrer_code:
        success = AffiliateHandler.track_referral(db, referrer_code, user.id)
        if success:
            # Send notification to both the referrer and the new user
            try:
                # Get the referrer
                referrer = crud.affiliate.get_user_by_affiliate_code(db, referrer_code)
                if referrer and referrer.telegram_id:
                    referrer_message = f"🎉 New referral! User {user.username or user.id} has joined using your affiliate link!"
                    send_notification(int(referrer.telegram_id), referrer_message)
                
                # Notify the new user
                if user.telegram_id:
                    user_message = f"👋 Welcome! You were referred by {referrer.username or referrer.id}. You can earn bonuses by referring others too!"
                    send_notification(int(user.telegram_id), user_message)
            except Exception as e:
                # Just log the error, don't interrupt the registration
                print(f"Error sending referral notifications: {str(e)}")
    
    return user


@router.put("/me", response_model=schemas.User)
def update_user_me(
    *,
    db: Session = Depends(deps.get_db),
    password: Optional[str] = Body(None),
    first_name: Optional[str] = Body(None),
    last_name: Optional[str] = Body(None),
    username: Optional[str] = Body(None),
    language_code: Optional[str] = Body(None),
    email: Optional[EmailStr] = Body(None),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Update own user.
    """
    current_user_data = jsonable_encoder(current_user)
    user_in = schemas.UserUpdate(**current_user_data)
    
    if password is not None:
        user_in.password = password
    if first_name is not None:
        user_in.first_name = first_name
    if last_name is not None:
        user_in.last_name = last_name
    if username is not None:
        user_in.username = username
    if language_code is not None:
        user_in.language_code = language_code
    if email is not None:
        user_in.email = email
    
    user = crud.user.update(db, db_obj=current_user, obj_in=user_in)
    return user


@router.get("/me", response_model=schemas.User)
def read_user_me(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Get current user.
    """
    return current_user


@router.get("/details", response_model=schemas.UserDetail)
def read_user_details(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Get detailed information about the current user, including statistics.
    """
    # Get user details with additional statistics
    user_detail = crud.user.get_user_details(db, user_id=current_user.id)
    
    # If this user was referred, add referrer information
    if current_user.referrer_id:
        referrer = crud.user.get(db, id=current_user.referrer_id)
        if referrer:
            user_detail.referrer = {
                "id": referrer.id,
                "username": referrer.username,
                "first_name": referrer.first_name,
                "last_name": referrer.last_name
            }
    
    return user_detail


@router.get("/{user_id}", response_model=schemas.User)
def read_user_by_id(
    user_id: int = Path(..., title="The ID of the user to get"),
    current_user: models.User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get a specific user by id.
    """
    user = crud.user.get(db, id=user_id)
    if user == current_user:
        return user
    if not crud.user.is_superuser(current_user):
        raise HTTPException(
            status_code=400, detail="The user doesn't have enough privileges"
        )
    return user


@router.put("/{user_id}", response_model=schemas.User)
def update_user(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int = Path(..., title="The ID of the user to update"),
    user_in: schemas.AdminUserUpdate,
    current_user: models.User = Depends(deps.get_current_admin_user),
) -> Any:
    """
    Update a user.
    """
    user = crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this ID does not exist in the system",
        )
    user = crud.user.update(db, db_obj=user, obj_in=user_in)
    return user 