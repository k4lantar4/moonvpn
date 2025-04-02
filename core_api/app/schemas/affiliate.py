from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, validator, AnyHttpUrl

# ---- Affiliate Commission Schemas ----

class AffiliateCommissionBase(BaseModel):
    """Base schema for affiliate commission data."""
    amount: Decimal = Field(..., description="Commission amount")
    percentage: Decimal = Field(..., description="Commission percentage used for calculation")
    status: str = Field(..., description="Commission status (pending, approved, paid, rejected)")
    commission_type: str = Field(..., description="Commission type (order, signup, bonus)")
    description: Optional[str] = Field(None, description="Optional description for the commission")


class AffiliateCommissionCreate(BaseModel):
    """Schema for creating a new commission record."""
    user_id: int = Field(..., description="User ID who earned the commission")
    referrer_id: Optional[int] = Field(None, description="User ID who was referred (optional)")
    order_id: Optional[int] = Field(None, description="Associated order ID (optional)")
    amount: Decimal = Field(..., description="Commission amount")
    percentage: Decimal = Field(..., description="Commission percentage used for calculation")
    commission_type: str = Field(..., description="Commission type (order, signup, bonus)")
    description: Optional[str] = Field(None, description="Optional description for the commission")
    
    @validator('commission_type')
    def validate_commission_type(cls, v):
        allowed_types = ['order', 'signup', 'bonus']
        if v not in allowed_types:
            raise ValueError(f"Commission type must be one of {allowed_types}")
        return v


class AffiliateCommissionUpdate(BaseModel):
    """Schema for updating a commission record."""
    status: Optional[str] = Field(None, description="Commission status")
    description: Optional[str] = Field(None, description="Optional description")
    
    @validator('status')
    def validate_status(cls, v):
        if v is not None:
            allowed_statuses = ['pending', 'approved', 'paid', 'rejected']
            if v not in allowed_statuses:
                raise ValueError(f"Status must be one of {allowed_statuses}")
        return v


class AffiliateCommissionInDB(AffiliateCommissionBase):
    """Schema for a commission record as stored in the database."""
    id: int
    user_id: int
    referrer_id: Optional[int] = None
    order_id: Optional[int] = None
    created_at: datetime
    paid_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: str(v)
        }


class AffiliateCommissionResponse(AffiliateCommissionInDB):
    """Schema for commission responses, including related user info."""
    user_name: Optional[str] = None
    referrer_name: Optional[str] = None
    order_info: Optional[str] = None


# ---- Affiliate Settings Schemas ----

class AffiliateSettingsBase(BaseModel):
    """Base schema for affiliate program settings."""
    commission_percentage: Decimal = Field(..., description="Default commission percentage")
    min_withdrawal_amount: Decimal = Field(..., description="Minimum amount for withdrawal")
    code_length: int = Field(..., description="Length of generated affiliate codes")
    is_enabled: bool = Field(..., description="Whether the affiliate program is enabled")


class AffiliateSettingsCreate(AffiliateSettingsBase):
    """Schema for creating affiliate settings."""
    pass


class AffiliateSettingsUpdate(BaseModel):
    """Schema for updating affiliate settings."""
    commission_percentage: Optional[Decimal] = Field(None, description="Default commission percentage")
    min_withdrawal_amount: Optional[Decimal] = Field(None, description="Minimum amount for withdrawal")
    code_length: Optional[int] = Field(None, description="Length of generated affiliate codes")
    is_enabled: Optional[bool] = Field(None, description="Whether the affiliate program is enabled")
    
    @validator('code_length')
    def validate_code_length(cls, v):
        if v is not None and (v < 4 or v > 16):
            raise ValueError("Code length must be between 4 and 16 characters")
        return v


class AffiliateSettingsInDB(AffiliateSettingsBase):
    """Schema for affiliate settings as stored in the database."""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: str(v)
        }


# ---- Affiliate Withdrawal Schemas ----

class AffiliateWithdrawalBase(BaseModel):
    """Base schema for affiliate withdrawal requests."""
    amount: Decimal = Field(..., description="Withdrawal amount")
    status: str = Field(..., description="Withdrawal status")
    note: Optional[str] = Field(None, description="Optional note for the withdrawal")


class AffiliateWithdrawalCreate(BaseModel):
    """Schema for creating a withdrawal request."""
    amount: Decimal = Field(..., description="Withdrawal amount")
    note: Optional[str] = Field(None, description="Optional note for the withdrawal")
    
    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError("Amount must be positive")
        return v


class AffiliateWithdrawalUpdate(BaseModel):
    """Schema for updating a withdrawal request."""
    status: Optional[str] = Field(None, description="Withdrawal status")
    note: Optional[str] = Field(None, description="Optional admin note")
    
    @validator('status')
    def validate_status(cls, v):
        if v is not None:
            allowed_statuses = ['pending', 'approved', 'completed', 'rejected']
            if v not in allowed_statuses:
                raise ValueError(f"Status must be one of {allowed_statuses}")
        return v


class AffiliateWithdrawalInDB(AffiliateWithdrawalBase):
    """Schema for a withdrawal request as stored in the database."""
    id: int
    user_id: int
    transaction_id: Optional[int] = None
    created_at: datetime
    processed_at: Optional[datetime] = None
    processed_by: Optional[int] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: str(v)
        }


class AffiliateWithdrawalResponse(AffiliateWithdrawalInDB):
    """Schema for withdrawal responses, including related user info."""
    user_name: Optional[str] = None
    processor_name: Optional[str] = None


# ---- User Affiliate Schemas ----

class UserAffiliateStats(BaseModel):
    """Schema for user's affiliate statistics."""
    total_earnings: Decimal = Field(..., description="Total affiliate earnings")
    pending_earnings: Decimal = Field(..., description="Pending affiliate earnings")
    paid_earnings: Decimal = Field(..., description="Paid affiliate earnings")
    current_balance: Decimal = Field(..., description="Current affiliate balance")
    referred_users_count: int = Field(..., description="Number of referred users")
    total_commission_count: int = Field(..., description="Total number of commissions")
    affiliate_code: str = Field(..., description="User's affiliate code")
    affiliate_url: str = Field(..., description="User's affiliate URL")
    is_affiliate_enabled: bool = Field(..., description="Whether the user's affiliate account is enabled")
    can_withdraw: bool = Field(..., description="Whether the user can withdraw their balance")
    min_withdrawal_amount: Decimal = Field(..., description="Minimum amount required for withdrawal")


# ---- Referral Tracking Schemas ----

class ReferralCreate(BaseModel):
    """Schema for tracking a referral."""
    referrer_code: str = Field(..., description="Affiliate code of the referrer")


class AffiliateReportParams(BaseModel):
    """Schema for affiliate report parameters."""
    start_date: Optional[datetime] = Field(None, description="Start date for the report period")
    end_date: Optional[datetime] = Field(None, description="End date for the report period")
    user_id: Optional[int] = Field(None, description="Filter by user ID")
    status: Optional[str] = Field(None, description="Filter by commission status")
    commission_type: Optional[str] = Field(None, description="Filter by commission type")


class AffiliateReport(BaseModel):
    """Schema for affiliate program report."""
    total_commissions: int = Field(..., description="Total number of commissions")
    total_amount: Decimal = Field(..., description="Total commission amount")
    active_affiliates: int = Field(..., description="Number of active affiliates")
    commission_by_status: Dict[str, int] = Field(..., description="Commissions grouped by status")
    commission_by_type: Dict[str, int] = Field(..., description="Commissions grouped by type")
    top_affiliates: List[Dict[str, Any]] = Field(..., description="Top performing affiliates")
    period_stats: Dict[str, Any] = Field(..., description="Stats for the requested period") 