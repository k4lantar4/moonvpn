from pydantic import BaseModel
from typing import List, Optional


class PaymentRequestResponse(BaseModel):
    """Response schema for payment initiation requests."""
    payment_url: str


class PaymentMethodResponse(BaseModel):
    """Schema for payment method information."""
    method: str
    active: bool
    

# Add other payment-related schemas here if needed in the future 