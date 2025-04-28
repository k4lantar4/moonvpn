from datetime import datetime
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from db.models.receipt_log import ReceiptLog, ReceiptStatus
from db.repositories.base_repository import BaseRepository

class ReceiptLogRepository(BaseRepository[ReceiptLog]):
    """Repository for ReceiptLog operations"""
    def __init__(self, session: AsyncSession):
        super().__init__(session, ReceiptLog)

    async def create_receipt_log(
        self,
        user_id: int,
        card_id: int,
        amount: float,
        status: ReceiptStatus,
        text_reference: Optional[str],
        photo_file_id: Optional[str],
        order_id: Optional[int] = None,
        transaction_id: Optional[int] = None,
        submitted_at: Optional[datetime] = None,
        tracking_code: Optional[str] = None
    ) -> ReceiptLog:
        """Create a new ReceiptLog entry"""
        receipt = ReceiptLog(
            user_id=user_id,
            card_id=card_id,
            amount=amount,
            status=status,
            text_reference=text_reference,
            photo_file_id=photo_file_id,
            order_id=order_id,
            transaction_id=transaction_id,
            submitted_at=submitted_at,
            tracking_code=tracking_code
        )
        self.session.add(receipt)
        await self.session.flush()
        return receipt

    async def update_status(
        self,
        receipt_id: int,
        status: ReceiptStatus,
        admin_id: int
    ) -> Optional[ReceiptLog]:
        """Update the status and admin info of a ReceiptLog"""
        receipt = await self.get_by_id(receipt_id)
        if not receipt:
            return None
        receipt.status = status
        receipt.admin_id = admin_id
        receipt.responded_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(receipt)
        return receipt

    async def update_telegram_info(
        self,
        receipt_id: int,
        message_id: int,
        channel_id: int
    ) -> Optional[ReceiptLog]:
        """Update the Telegram message ID and channel ID for a receipt log."""
        receipt = await self.get_by_id(receipt_id)
        if not receipt:
            # Log or handle error: receipt not found
            return None
        receipt.telegram_message_id = message_id
        receipt.telegram_channel_id = channel_id
        # Should we commit here? Or rely on the calling service to commit?
        # Let's commit here for simplicity, assuming this update is atomic.
        await self.session.commit()
        await self.session.refresh(receipt)
        return receipt

    async def add_note(
        self,
        receipt_id: int,
        note: str,
        admin_id: int
    ) -> Optional[ReceiptLog]:
        """Add or update note for a ReceiptLog"""
        receipt = await self.get_by_id(receipt_id)
        if not receipt:
            return None
        # Append note or replace
        existing_notes = receipt.notes or ""
        combined_notes = f"{existing_notes}\n{note}" if existing_notes else note
        receipt.notes = combined_notes
        receipt.admin_id = admin_id
        receipt.responded_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(receipt)
        return receipt
        
    async def get_by_status(
        self,
        status: str,
        limit: int = 10
    ) -> List[ReceiptLog]:
        """Get ReceiptLog entries by status, sorted by newest first."""
        query = select(ReceiptLog).where(ReceiptLog.status == status).order_by(desc(ReceiptLog.submitted_at)).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_by_tracking_code(
        self,
        tracking_code: str
    ) -> Optional[ReceiptLog]:
        """Get a receipt by its tracking code."""
        query = select(ReceiptLog).where(ReceiptLog.tracking_code == tracking_code)
        result = await self.session.execute(query)
        return result.scalars().first()
    
    async def get_by_order_id(
        self,
        order_id: int
    ) -> List[ReceiptLog]:
        """Get all receipts for a specific order."""
        query = select(ReceiptLog).where(ReceiptLog.order_id == order_id).order_by(desc(ReceiptLog.submitted_at))
        result = await self.session.execute(query)
        return list(result.scalars().all()) 