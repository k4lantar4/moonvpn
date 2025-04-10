"""Repository for DiscountCode model operations."""

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Any
from datetime import datetime
import logging

from core.database.models.discount_code import DiscountCode, DiscountType
from core.schemas.discount_code import DiscountCodeCreate, DiscountCodeUpdate
from core.database.repositories.base_repo import BaseRepository
from core.exceptions import ServiceError, NotFoundError

logger = logging.getLogger(__name__)

class DiscountCodeRepository(BaseRepository[DiscountCode, DiscountCodeCreate, DiscountCodeUpdate]):
    """
    Repository for DiscountCode model operations.
    Inherits basic CRUD operations from BaseRepository.
    """
    
    def __init__(self):
        super().__init__(model=DiscountCode)
    
    async def get_by_code(self, db_session: AsyncSession, *, code: str) -> Optional[DiscountCode]:
        """
        Retrieve a discount code by its code value.
        
        Args:
            db_session: The database session
            code: The discount code to find
            
        Returns:
            The DiscountCode if found, None otherwise
        """
        try:
            statement = select(self._model).where(func.lower(self._model.code) == func.lower(code))
            result = await db_session.execute(statement)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error retrieving discount code '{code}': {e}", exc_info=True)
            return None
    
    async def get_active_discount_codes(
        self,
        db_session: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[DiscountCode]:
        """
        Retrieve all active discount codes.
        
        Args:
            db_session: The database session
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to retrieve
            
        Returns:
            A list of active DiscountCode objects
        """
        try:
            now = datetime.now()
            statement = (
                select(self._model)
                .where(
                    and_(
                        self._model.is_active == True,
                        or_(
                            self._model.expires_at == None,
                            self._model.expires_at > now
                        ),
                        or_(
                            self._model.max_uses == None,
                            self._model.used_count < self._model.max_uses
                        )
                    )
                )
                .order_by(self._model.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            result = await db_session.execute(statement)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error retrieving active discount codes: {e}", exc_info=True)
            return []
    
    async def increment_used_count(self, db_session: AsyncSession, *, discount_code_id: int) -> DiscountCode:
        """
        Increment the used_count field for a discount code.
        
        Args:
            db_session: The database session
            discount_code_id: ID of the discount code to update
            
        Returns:
            The updated DiscountCode object
            
        Raises:
            NotFoundError: If the discount code doesn't exist
        """
        try:
            discount_code = await self.get(db_session, id=discount_code_id)
            if not discount_code:
                raise NotFoundError(f"Discount code with ID {discount_code_id} not found")
            
            # Initialize used_count to 0 if it's None
            if discount_code.used_count is None:
                discount_code.used_count = 0
            
            discount_code.used_count += 1
            discount_code.updated_at = datetime.now()
            
            # Just adding to session, commit will be handled by service layer
            db_session.add(discount_code)
            await db_session.flush()
            await db_session.refresh(discount_code)
            
            return discount_code
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error incrementing used count for discount code {discount_code_id}: {e}", exc_info=True)
            raise ServiceError(f"Failed to update discount code usage")
    
    async def validate_discount_code(
        self, 
        db_session: AsyncSession, 
        *, 
        code: str
    ) -> Optional[DiscountCode]:
        """
        Validate if a discount code is active and available for use.
        
        Args:
            db_session: The database session
            code: The discount code to validate
            
        Returns:
            The valid DiscountCode if found and valid, None otherwise
        """
        try:
            now = datetime.now()
            discount_code = await self.get_by_code(db_session, code=code)
            
            if not discount_code:
                return None
            
            # Check if the code is active
            if not discount_code.is_active:
                return None
            
            # Check if the code has expired
            if discount_code.expires_at and discount_code.expires_at < now:
                return None
            
            # Check if the code has reached its maximum usage
            if (discount_code.max_uses is not None and 
                discount_code.used_count is not None and 
                discount_code.used_count >= discount_code.max_uses):
                return None
            
            return discount_code
        except Exception as e:
            logger.error(f"Error validating discount code '{code}': {e}", exc_info=True)
            return None 