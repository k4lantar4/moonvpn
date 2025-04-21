from pydantic import BaseModel
from typing import Optional, Any, Dict
from datetime import datetime
from db.models.enums import TransactionStatus, PaymentMethod

class TransactionBase(BaseModel):
    amount: float
    user_id: int
    order_id: Optional[int] = None
    payment_method: PaymentMethod
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class TransactionCreate(TransactionBase):
    pass

class TransactionUpdate(BaseModel):
    status: Optional[TransactionStatus] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class TransactionSchema(TransactionBase):
    id: int
    status: TransactionStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True # For SQLAlchemy compatibility
        from_attributes=True # Pydantic V2 