from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator


# Base schemas for PaymentAdminAssignment
class PaymentAdminAssignmentBase(BaseModel):
    user_id: int
    bank_card_id: Optional[int] = None
    telegram_group_id: Optional[str] = None
    is_active: bool = True
    daily_limit: Optional[int] = None


class PaymentAdminAssignmentCreate(PaymentAdminAssignmentBase):
    """Schema for creating a new payment admin assignment"""
    
    @validator('telegram_group_id')
    def validate_telegram_group_id(cls, v):
        if v is not None and not v.startswith('-100'):
            raise ValueError('Telegram group ID should start with -100')
        return v


class PaymentAdminAssignmentUpdate(BaseModel):
    """Schema for updating an existing payment admin assignment"""
    bank_card_id: Optional[int] = None
    telegram_group_id: Optional[str] = None
    is_active: Optional[bool] = None
    daily_limit: Optional[int] = None
    
    @validator('telegram_group_id')
    def validate_telegram_group_id(cls, v):
        if v is not None and not v.startswith('-100'):
            raise ValueError('Telegram group ID should start with -100')
        return v


class PaymentAdminAssignmentInDBBase(PaymentAdminAssignmentBase):
    """Base schema for PaymentAdminAssignment as stored in DB"""
    id: int
    created_at: datetime
    updated_at: datetime
    last_assignment_date: Optional[datetime] = None

    class Config:
        orm_mode = True


class PaymentAdminAssignment(PaymentAdminAssignmentInDBBase):
    """Schema for reading a payment admin assignment"""
    user_name: Optional[str] = None
    bank_card_number: Optional[str] = None
    bank_name: Optional[str] = None


# Base schemas for PaymentAdminMetrics
class PaymentAdminMetricsBase(BaseModel):
    user_id: int
    total_processed: int = 0
    total_approved: int = 0
    total_rejected: int = 0
    avg_response_time_seconds: Optional[float] = None


class PaymentAdminMetricsCreate(PaymentAdminMetricsBase):
    """Schema for creating a new payment admin metrics record"""
    pass


class PaymentAdminMetricsUpdate(BaseModel):
    """Schema for updating an existing payment admin metrics record"""
    total_processed: Optional[int] = None
    total_approved: Optional[int] = None
    total_rejected: Optional[int] = None
    avg_response_time_seconds: Optional[float] = None
    last_processed_at: Optional[datetime] = None


class PaymentAdminMetricsInDBBase(PaymentAdminMetricsBase):
    """Base schema for PaymentAdminMetrics as stored in DB"""
    id: int
    created_at: datetime
    updated_at: datetime
    last_processed_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class PaymentAdminMetrics(PaymentAdminMetricsInDBBase):
    """Schema for reading payment admin metrics"""
    user_name: Optional[str] = None
    
    @property
    def approval_rate(self) -> float:
        """Calculate approval rate as a percentage"""
        if self.total_processed == 0:
            return 0.0
        return (self.total_approved / self.total_processed) * 100


# Additional schemas for operations
class PaymentAdminAssignmentWithMetrics(BaseModel):
    """Schema for reading a payment admin assignment with metrics"""
    assignment: PaymentAdminAssignment
    metrics: Optional[PaymentAdminMetrics] = None


class PaymentAdminStatistics(BaseModel):
    """Schema for returning payment admin statistics"""
    total_admins: int
    total_processed_payments: int
    avg_approval_rate: float
    avg_response_time: Optional[float] = None


class PaymentAdminAssignmentResponse(BaseModel):
    """Schema for response when getting a payment admin assignment."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    detail: Optional[str] = None
    
    class Config:
        orm_mode = True
        from_attributes = True


class PaymentAdminPerformanceMetrics(BaseModel):
    """Schema for detailed payment admin performance metrics."""
    admin_id: int
    admin_name: Optional[str] = None
    total_processed: int
    total_approved: int
    total_rejected: int
    avg_approval_rate: float
    avg_response_time_seconds: Optional[float] = None
    min_response_time_seconds: Optional[float] = None
    max_response_time_seconds: Optional[float] = None
    total_processed_today: int = 0
    total_processed_week: int = 0
    total_processed_month: int = 0
    rejection_reasons: Dict[str, int] = Field(default_factory=dict)
    bank_card_distribution: Dict[str, int] = Field(default_factory=dict)
    
    class Config:
        orm_mode = True
        from_attributes = True


class PaymentAdminReportData(BaseModel):
    """Schema for payment admin report data."""
    admins: List[PaymentAdminPerformanceMetrics]
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    total_payments: int
    total_approved: int
    total_rejected: int
    overall_approval_rate: float
    avg_response_time_seconds: Optional[float] = None
    
    class Config:
        orm_mode = True
        from_attributes = True


class PaymentAdminReportResponse(BaseModel):
    """Schema for payment admin report response."""
    success: bool
    data: Optional[PaymentAdminReportData] = None
    detail: Optional[str] = None
    
    class Config:
        orm_mode = True
        from_attributes = True
