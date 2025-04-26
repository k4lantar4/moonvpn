"""
Repository for DiscountCode model operations
"""

from typing import List, Optional, Dict, Any
from sqlalchemy import select, update, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from db.models.discount_code import DiscountCode

class DiscountCodeRepository:
    """Repository for discount code operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, discount_id: int) -> Optional[DiscountCode]:
        """
        Get a discount code by ID
        
        Args:
            discount_id: ID of the discount code
            
        Returns:
            DiscountCode object if found, None otherwise
        """
        result = await self.session.execute(
            select(DiscountCode).where(DiscountCode.id == discount_id)
        )
        return result.scalars().first()
    
    async def get_by_code(self, code: str) -> Optional[DiscountCode]:
        """
        Get a discount code by its code string
        
        Args:
            code: The discount code string
            
        Returns:
            DiscountCode object if found, None otherwise
        """
        result = await self.session.execute(
            select(DiscountCode).where(DiscountCode.code == code)
        )
        return result.scalars().first()
    
    async def get_active_codes(self, user_id: Optional[int] = None, plan_id: Optional[int] = None) -> List[DiscountCode]:
        """
        Get all active discount codes (not expired and not reached max uses)
        Optionally filter by user_id or plan_id
        
        Args:
            user_id: Optional user ID to filter codes for specific user
            plan_id: Optional plan ID to filter codes for specific plan
            
        Returns:
            List of active DiscountCode objects
        """
        # Base query
        query = select(DiscountCode).where(
            (DiscountCode.expires_at > datetime.utcnow()) | (DiscountCode.expires_at.is_(None))
        )
        
        # Add user filter if provided
        if user_id is not None:
            query = query.where(
                (DiscountCode.user_id.is_(None)) | (DiscountCode.user_id == user_id)
            )
        
        # Add plan filter if provided
        if plan_id is not None:
            # This is a simplistic approach - in reality you would need to handle
            # the plan_ids field according to your actual implementation
            query = query.where(
                (DiscountCode.plan_ids.is_(None)) | 
                (DiscountCode.plan_ids == "") | 
                (DiscountCode.plan_ids.like(f"%{plan_id}%"))
            )
            
        # Exclude codes that have reached their max uses
        query = query.where(
            (DiscountCode.max_uses.is_(None)) | 
            (DiscountCode.use_count < DiscountCode.max_uses)
        )
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def create(self, data: Dict[str, Any]) -> DiscountCode:
        """
        Create a new discount code
        
        Args:
            data: Dictionary with discount code data
            
        Returns:
            Created DiscountCode object
        """
        discount = DiscountCode(**data)
        self.session.add(discount)
        await self.session.flush()
        return discount
    
    async def update(self, discount_id: int, data: Dict[str, Any]) -> Optional[DiscountCode]:
        """
        Update a discount code
        
        Args:
            discount_id: ID of the discount code to update
            data: Dictionary with updated data
            
        Returns:
            Updated DiscountCode object if found, None otherwise
        """
        await self.session.execute(
            update(DiscountCode)
            .where(DiscountCode.id == discount_id)
            .values(**data)
        )
        
        result = await self.session.execute(
            select(DiscountCode).where(DiscountCode.id == discount_id)
        )
        return result.scalars().first()
    
    async def increment_use_count(self, discount_id: int) -> Optional[DiscountCode]:
        """
        Increment the use count of a discount code
        
        Args:
            discount_id: ID of the discount code
            
        Returns:
            Updated DiscountCode object if found, None otherwise
        """
        await self.session.execute(
            update(DiscountCode)
            .where(DiscountCode.id == discount_id)
            .values(use_count=DiscountCode.use_count + 1)
        )
        
        result = await self.session.execute(
            select(DiscountCode).where(DiscountCode.id == discount_id)
        )
        return result.scalars().first()
    
    async def delete(self, discount_id: int) -> bool:
        """
        Delete a discount code
        
        Args:
            discount_id: ID of the discount code to delete
            
        Returns:
            True if deleted, False if not found
        """
        discount = await self.get_by_id(discount_id)
        if not discount:
            return False
            
        await self.session.delete(discount)
        return True 