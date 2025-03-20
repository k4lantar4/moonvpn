"""
Payment tracking service for card-to-card transactions.

This module handles tracking of card-to-card payments, including:
- Card owner information
- Transaction verification
- Admin confirmation workflow
- Payment history
"""

import logging
import uuid
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class PaymentStatus(Enum):
    """Payment status enumeration."""
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

@dataclass
class CardInfo:
    """Card information data class."""
    id: str
    owner_name: str
    card_number: str
    bank_name: str
    is_verified: bool
    last_used: datetime
    total_transactions: int
    success_rate: float

@dataclass
class PaymentInfo:
    """Payment information data class."""
    id: str
    amount: float
    currency: str
    status: PaymentStatus
    created_at: datetime
    updated_at: datetime
    from_card: CardInfo
    to_card: CardInfo
    description: str
    receipt_image: Optional[str]
    verified_by: Optional[str]
    verified_at: Optional[datetime]
    rejection_reason: Optional[str]
    points_earned: int
    is_points_payment: bool

class PaymentTracker:
    """Tracks card-to-card payments and manages verification workflow."""
    
    def __init__(self):
        self.payments: Dict[str, PaymentInfo] = {}
        self.cards: Dict[str, CardInfo] = {}
    
    async def add_card(
        self,
        owner_name: str,
        card_number: str,
        bank_name: str
    ) -> CardInfo:
        """Add a new card to the tracker."""
        card_id = str(uuid.uuid4())
        card = CardInfo(
            id=card_id,
            owner_name=owner_name,
            card_number=card_number,
            bank_name=bank_name,
            is_verified=False,
            last_used=datetime.now(),
            total_transactions=0,
            success_rate=0.0
        )
        self.cards[card_id] = card
        return card
    
    async def get_card(self, card_id: str) -> Optional[CardInfo]:
        """Get card information by ID."""
        return self.cards.get(card_id)
    
    async def get_cards_by_owner(self, owner_name: str) -> List[CardInfo]:
        """Get all cards owned by a specific person."""
        return [c for c in self.cards.values() if c.owner_name == owner_name]
    
    async def verify_card(self, card_id: str, verified_by: str) -> bool:
        """Mark a card as verified by an admin."""
        card = await self.get_card(card_id)
        if card:
            card.is_verified = True
            return True
        return False
    
    async def create_payment(
        self,
        amount: float,
        currency: str,
        from_card_id: str,
        to_card_id: str,
        description: str,
        receipt_image: Optional[str] = None,
        is_points_payment: bool = False
    ) -> PaymentInfo:
        """Create a new payment transaction."""
        from_card = await self.get_card(from_card_id)
        to_card = await self.get_card(to_card_id)
        
        if not from_card or not to_card:
            raise ValueError("Invalid card IDs")
        
        payment_id = str(uuid.uuid4())
        payment = PaymentInfo(
            id=payment_id,
            amount=amount,
            currency=currency,
            status=PaymentStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            from_card=from_card,
            to_card=to_card,
            description=description,
            receipt_image=receipt_image,
            verified_by=None,
            verified_at=None,
            rejection_reason=None,
            points_earned=0,
            is_points_payment=is_points_payment
        )
        
        self.payments[payment_id] = payment
        return payment
    
    async def get_payment(self, payment_id: str) -> Optional[PaymentInfo]:
        """Get payment information by ID."""
        return self.payments.get(payment_id)
    
    async def get_payments_by_card(self, card_id: str) -> List[PaymentInfo]:
        """Get all payments involving a specific card."""
        return [
            p for p in self.payments.values()
            if p.from_card.id == card_id or p.to_card.id == card_id
        ]
    
    async def get_payments_by_owner(self, owner_name: str) -> List[PaymentInfo]:
        """Get all payments involving cards owned by a specific person."""
        return [
            p for p in self.payments.values()
            if p.from_card.owner_name == owner_name or p.to_card.owner_name == owner_name
        ]
    
    async def verify_payment(
        self,
        payment_id: str,
        verified_by: str,
        points_earned: int = 0
    ) -> bool:
        """Verify a payment by an admin."""
        payment = await self.get_payment(payment_id)
        if not payment:
            return False
        
        payment.status = PaymentStatus.VERIFIED
        payment.verified_by = verified_by
        payment.verified_at = datetime.now()
        payment.points_earned = points_earned
        payment.updated_at = datetime.now()
        
        # Update card statistics
        payment.from_card.total_transactions += 1
        payment.from_card.last_used = datetime.now()
        
        return True
    
    async def reject_payment(
        self,
        payment_id: str,
        verified_by: str,
        reason: str
    ) -> bool:
        """Reject a payment by an admin."""
        payment = await self.get_payment(payment_id)
        if not payment:
            return False
        
        payment.status = PaymentStatus.REJECTED
        payment.verified_by = verified_by
        payment.verified_at = datetime.now()
        payment.rejection_reason = reason
        payment.updated_at = datetime.now()
        
        return True
    
    async def complete_payment(self, payment_id: str) -> bool:
        """Mark a payment as completed."""
        payment = await self.get_payment(payment_id)
        if not payment or payment.status != PaymentStatus.VERIFIED:
            return False
        
        payment.status = PaymentStatus.COMPLETED
        payment.updated_at = datetime.now()
        
        # Update card success rate
        payment.from_card.success_rate = (
            (payment.from_card.success_rate * (payment.from_card.total_transactions - 1) + 1)
            / payment.from_card.total_transactions
        )
        
        return True
    
    async def cancel_payment(self, payment_id: str) -> bool:
        """Cancel a payment."""
        payment = await self.get_payment(payment_id)
        if not payment or payment.status not in [PaymentStatus.PENDING, PaymentStatus.VERIFIED]:
            return False
        
        payment.status = PaymentStatus.CANCELLED
        payment.updated_at = datetime.now()
        return True
    
    async def get_payment_stats(self, card_id: str) -> Dict:
        """Get payment statistics for a card."""
        card = await self.get_card(card_id)
        if not card:
            return None
        
        payments = await self.get_payments_by_card(card_id)
        completed_payments = [p for p in payments if p.status == PaymentStatus.COMPLETED]
        
        return {
            "card": {
                "id": card.id,
                "owner": card.owner_name,
                "bank": card.bank_name,
                "is_verified": card.is_verified,
                "last_used": card.last_used.isoformat(),
                "total_transactions": card.total_transactions,
                "success_rate": card.success_rate
            },
            "payments": {
                "total": len(payments),
                "completed": len(completed_payments),
                "pending": len([p for p in payments if p.status == PaymentStatus.PENDING]),
                "rejected": len([p for p in payments if p.status == PaymentStatus.REJECTED]),
                "cancelled": len([p for p in payments if p.status == PaymentStatus.CANCELLED])
            },
            "amounts": {
                "total_sent": sum(p.amount for p in completed_payments if p.from_card.id == card_id),
                "total_received": sum(p.amount for p in completed_payments if p.to_card.id == card_id)
            }
        } 