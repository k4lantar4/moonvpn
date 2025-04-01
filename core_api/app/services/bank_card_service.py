from typing import List, Optional, Dict, Any, Union
from fastapi import HTTPException, status

from sqlalchemy.orm import Session
from app import crud, models, schemas
from app.core.logger import get_logger

logger = get_logger(__name__)


class BankCardService:
    """Business logic for bank card operations"""
    
    @staticmethod
    def get_bank_cards_for_payment(db: Session, skip: int = 0, limit: int = 5) -> List[models.BankCard]:
        """
        Get active bank cards for payment purposes, ordered by priority.
        
        This method returns a list of active bank cards that can be used for making payments.
        The cards are ordered by priority (descending).
        
        Args:
            db: Database session
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            
        Returns:
            List of BankCard models
        """
        try:
            return crud.bank_card.get_active_cards(db=db, skip=skip, limit=limit)
        except Exception as e:
            logger.error(f"Error getting active bank cards: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving active bank cards"
            )
    
    @staticmethod
    def get_bank_card_details(db: Session, bank_card_id: int) -> schemas.BankCardDetail:
        """
        Get detailed information about a bank card.
        
        This method returns detailed information about a bank card, including
        the user name and creator name.
        
        Args:
            db: Database session
            bank_card_id: ID of the bank card
            
        Returns:
            BankCardDetail schema
        """
        bank_card = crud.bank_card.get(db=db, id=bank_card_id)
        if bank_card is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bank card not found"
            )
        
        # Create a BankCardDetail object with basic bank card information
        bank_card_detail = schemas.BankCardDetail.from_orm(bank_card)
        
        # Add user name if available
        if bank_card.user_id is not None:
            user = crud.user.get(db=db, id=bank_card.user_id)
            if user:
                bank_card_detail.user_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or f"User #{user.id}"
        
        # Add creator name if available
        if bank_card.created_by is not None:
            creator = crud.user.get(db=db, id=bank_card.created_by)
            if creator:
                bank_card_detail.creator_name = f"{creator.first_name or ''} {creator.last_name or ''}".strip() or f"User #{creator.id}"
        
        return bank_card_detail
    
    @staticmethod
    def toggle_card_status(db: Session, bank_card_id: int, current_user_id: int) -> models.BankCard:
        """
        Toggle the active status of a bank card.
        
        This method toggles the is_active status of a bank card.
        Users can only toggle their own cards, admins can toggle any card.
        
        Args:
            db: Database session
            bank_card_id: ID of the bank card
            current_user_id: ID of the current user
            
        Returns:
            Updated BankCard model
        """
        bank_card = crud.bank_card.get(db=db, id=bank_card_id)
        if bank_card is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bank card not found"
            )
        
        # Get the current user
        current_user = crud.user.get(db=db, id=current_user_id)
        if current_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if user has permission to toggle this card
        has_permission = bank_card.user_id == current_user_id
        if not has_permission:
            # Check if user has admin permission
            admin_permission = any(
                permission.permission_name == "admin:bank_card:update"
                for role in current_user.roles
                for permission in role.permissions
            )
            if not admin_permission:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not enough permissions to toggle this bank card"
                )
        
        # Toggle the is_active status
        update_data = {"is_active": not bank_card.is_active}
        return crud.bank_card.update(db=db, db_obj=bank_card, obj_in=update_data)
    
    @staticmethod
    def update_card_priority(db: Session, bank_card_id: int, priority: int, current_user_id: int) -> models.BankCard:
        """
        Update the priority of a bank card.
        
        This method updates the priority of a bank card.
        Only users with admin permission can update priorities.
        
        Args:
            db: Database session
            bank_card_id: ID of the bank card
            priority: New priority value
            current_user_id: ID of the current user
            
        Returns:
            Updated BankCard model
        """
        bank_card = crud.bank_card.get(db=db, id=bank_card_id)
        if bank_card is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bank card not found"
            )
        
        # Get the current user
        current_user = crud.user.get(db=db, id=current_user_id)
        if current_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if user has admin permission
        admin_permission = any(
            permission.permission_name == "admin:bank_card:update"
            for role in current_user.roles
            for permission in role.permissions
        )
        if not admin_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to update bank card priority"
            )
        
        # Update the priority
        update_data = {"priority": priority}
        return crud.bank_card.update(db=db, db_obj=bank_card, obj_in=update_data)


# Create a singleton instance
bank_card_service = BankCardService() 