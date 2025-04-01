from typing import Optional
from pydantic import BaseModel, validator

class PaymentProofSubmit(BaseModel):
    """Schema for submitting a payment proof."""
    payment_reference: str
    payment_method: str = "card_to_card"
    notes: Optional[str] = None
    
    @validator("payment_reference")
    def validate_payment_reference(cls, v):
        """Validate payment reference format."""
        if not v or len(v) < 3:
            raise ValueError("Payment reference must be at least 3 characters")
        return v

class PaymentVerification(BaseModel):
    """Schema for verifying a payment proof."""
    is_approved: bool
    rejection_reason: Optional[str] = None
    admin_note: Optional[str] = None
    
    @validator("rejection_reason")
    def validate_rejection_reason(cls, v, values):
        """Ensure rejection reason is provided if payment is not approved."""
        if "is_approved" in values and not values["is_approved"] and not v:
            raise ValueError("Rejection reason is required when payment is not approved")
        return v

class TelegramMessageUpdate(BaseModel):
    """Schema for updating Telegram message ID for a payment proof."""
    telegram_msg_id: int
    telegram_group_id: str
    
    class Config:
        orm_mode = True
        from_attributes = True 