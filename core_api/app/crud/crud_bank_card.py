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

    def get_next_active_card(
        self, db: Session, *, last_used_id: Optional[int] = None
    ) -> Optional[BankCard]:
        """
        Get the next active bank card for payment based on rotation logic.
        
        This method implements a smarter card rotation algorithm that:
        1. Prioritizes cards based on their priority value (higher priority first)
        2. Within the same priority, rotates through cards to distribute the load
        3. Skips the last used card if specified
        4. Only returns active cards
        
        Args:
            db: Database session
            last_used_id: ID of the last card used (to avoid using the same card twice in a row)
        
        Returns:
            The next BankCard to use, or None if no active cards are available
        """
        # First get all active cards ordered by priority (descending)
        stmt = (
            select(self.model)
            .where(self.model.is_active == True)
            .order_by(self.model.priority.desc())
        )
        
        all_active_cards = list(db.scalars(stmt).all())
        
        if not all_active_cards:
            return None  # No active cards available
        
        # If no last_used_id provided, simply return the highest priority card
        if last_used_id is None:
            return all_active_cards[0]
        
        # Group cards by priority
        priority_groups = {}
        for card in all_active_cards:
            if card.priority not in priority_groups:
                priority_groups[card.priority] = []
            priority_groups[card.priority].append(card)
        
        # Sort priorities in descending order
        sorted_priorities = sorted(priority_groups.keys(), reverse=True)
        
        # Find the last used card's priority group
        last_card_priority = None
        last_card_index = None
        
        for priority in sorted_priorities:
            cards = priority_groups[priority]
            for i, card in enumerate(cards):
                if card.id == last_used_id:
                    last_card_priority = priority
                    last_card_index = i
                    break
            if last_card_priority is not None:
                break
        
        # If last card not found (it might have been deleted or deactivated),
        # start with the highest priority group
        if last_card_priority is None:
            return priority_groups[sorted_priorities[0]][0]
        
        # If last card found, get the next card in the same priority group
        cards_in_group = priority_groups[last_card_priority]
        next_index = (last_card_index + 1) % len(cards_in_group)
        
        # Return the next card in rotation
        return cards_in_group[next_index]


# Create an instance of the CRUD class
bank_card = CRUDBankCard(BankCard) 