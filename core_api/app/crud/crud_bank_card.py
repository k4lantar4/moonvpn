from typing import List, Optional, Dict, Any, Union

from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.crud.base import CRUDBase
from app.models.bank_card import BankCard
from app.schemas.bank_card import BankCardCreate, BankCardUpdate


class CRUDBankCard(CRUDBase[BankCard, BankCardCreate, BankCardUpdate]):
    """CRUD operations for BankCard model"""
    
    def create_with_owner(
        self, db: Session, *, obj_in: BankCardCreate, created_by: int
    ) -> BankCard:
        """Create a new bank card with owner information"""
        db_obj = BankCard(
            bank_name=obj_in.bank_name,
            card_number=obj_in.card_number,
            card_holder_name=obj_in.card_holder_name,
            account_number=obj_in.account_number,
            sheba_number=obj_in.sheba_number,
            is_active=obj_in.is_active,
            priority=obj_in.priority,
            description=obj_in.description,
            user_id=obj_in.user_id,
            created_by=created_by
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get_multi_by_owner(
        self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[BankCard]:
        """Get bank cards for a specific owner"""
        stmt = select(self.model).where(self.model.user_id == user_id).offset(skip).limit(limit)
        return list(db.scalars(stmt).all())
    
    def get_active_cards(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[BankCard]:
        """Get active bank cards ordered by priority"""
        stmt = (
            select(self.model)
            .where(self.model.is_active == True)
            .order_by(self.model.priority.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(db.scalars(stmt).all())
    
    def count(self, db: Session, *, user_id: Optional[int] = None) -> int:
        """Count the number of bank cards, optionally filtered by user_id"""
        query = select(func.count()).select_from(self.model)
        if user_id is not None:
            query = query.where(self.model.user_id == user_id)
        return db.scalar(query)


# Create an instance of the CRUD class
bank_card = CRUDBankCard(BankCard) 