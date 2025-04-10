"""Service for managing discount codes."""

import logging
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Tuple, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession

from core.database.models.discount_code import DiscountCode, DiscountType
from core.database.repositories import DiscountCodeRepository
from core.schemas.discount_code import (
    DiscountCodeCreate, 
    DiscountCodeUpdate, 
    DiscountCodeRead, 
    DiscountCodeValidationResult
)
from core.exceptions import NotFoundError, ValidationError, ServiceError

logger = logging.getLogger(__name__)

class DiscountCodeService:
    """Service for managing discount codes."""
    
    def __init__(self):
        self.discount_code_repo = DiscountCodeRepository()
    
    async def create_discount_code(
        self, 
        db: AsyncSession, 
        discount_code_data: DiscountCodeCreate
    ) -> DiscountCodeRead:
        """
        Create a new discount code.
        
        Args:
            db: Database session
            discount_code_data: Data for creating the discount code
            
        Returns:
            The created discount code
            
        Raises:
            ValidationError: If there's an error validating the data
            ServiceError: If there's an error creating the discount code
        """
        try:
            logger.info(f"Creating discount code with code: {discount_code_data.code}")
            
            # Check if code already exists
            existing_code = await self.discount_code_repo.get_by_code(db, code=discount_code_data.code)
            if existing_code:
                logger.warning(f"Discount code '{discount_code_data.code}' already exists")
                raise ValidationError(f"کد تخفیف '{discount_code_data.code}' قبلاً ثبت شده است")
            
            discount_code = await self.discount_code_repo.create(db, obj_in=discount_code_data)
            await db.commit()
            
            logger.info(f"Successfully created discount code with ID: {discount_code.id}")
            return DiscountCodeRead.model_validate(discount_code)
        
        except ValidationError:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating discount code: {e}", exc_info=True)
            raise ServiceError("خطا در ایجاد کد تخفیف")
    
    async def update_discount_code(
        self, 
        db: AsyncSession, 
        discount_code_id: int, 
        discount_code_data: DiscountCodeUpdate
    ) -> DiscountCodeRead:
        """
        Update an existing discount code.
        
        Args:
            db: Database session
            discount_code_id: ID of the discount code to update
            discount_code_data: Data for updating the discount code
            
        Returns:
            The updated discount code
            
        Raises:
            NotFoundError: If the discount code doesn't exist
            ValidationError: If there's an error validating the data
            ServiceError: If there's an error updating the discount code
        """
        try:
            logger.info(f"Updating discount code with ID: {discount_code_id}")
            
            # Get the existing discount code
            discount_code = await self.discount_code_repo.get(db, id=discount_code_id)
            if not discount_code:
                logger.warning(f"Discount code with ID {discount_code_id} not found")
                raise NotFoundError(f"کد تخفیف با شناسه {discount_code_id} یافت نشد")
            
            # If updating code, check if new code already exists
            if discount_code_data.code is not None and discount_code_data.code != discount_code.code:
                existing_code = await self.discount_code_repo.get_by_code(db, code=discount_code_data.code)
                if existing_code and existing_code.id != discount_code_id:
                    logger.warning(f"Discount code '{discount_code_data.code}' already exists")
                    raise ValidationError(f"کد تخفیف '{discount_code_data.code}' قبلاً ثبت شده است")
            
            # Set updated_at timestamp
            update_dict = discount_code_data.model_dump(exclude_unset=True)
            update_dict["updated_at"] = datetime.now()
            
            updated_discount_code = await self.discount_code_repo.update(
                db, db_obj=discount_code, obj_in=update_dict
            )
            await db.commit()
            
            logger.info(f"Successfully updated discount code with ID: {discount_code_id}")
            return DiscountCodeRead.model_validate(updated_discount_code)
        
        except (NotFoundError, ValidationError):
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating discount code: {e}", exc_info=True)
            raise ServiceError("خطا در بروزرسانی کد تخفیف")
    
    async def delete_discount_code(self, db: AsyncSession, discount_code_id: int) -> DiscountCodeRead:
        """
        Delete a discount code.
        
        Args:
            db: Database session
            discount_code_id: ID of the discount code to delete
            
        Returns:
            The deleted discount code
            
        Raises:
            NotFoundError: If the discount code doesn't exist
            ServiceError: If there's an error deleting the discount code
        """
        try:
            logger.info(f"Deleting discount code with ID: {discount_code_id}")
            
            deleted_code = await self.discount_code_repo.delete(db, id=discount_code_id)
            if not deleted_code:
                logger.warning(f"Discount code with ID {discount_code_id} not found")
                raise NotFoundError(f"کد تخفیف با شناسه {discount_code_id} یافت نشد")
            
            await db.commit()
            logger.info(f"Successfully deleted discount code with ID: {discount_code_id}")
            return DiscountCodeRead.model_validate(deleted_code)
        
        except NotFoundError:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Error deleting discount code: {e}", exc_info=True)
            raise ServiceError("خطا در حذف کد تخفیف")
    
    async def get_discount_code(self, db: AsyncSession, discount_code_id: int) -> DiscountCodeRead:
        """
        Get a discount code by ID.
        
        Args:
            db: Database session
            discount_code_id: ID of the discount code to retrieve
            
        Returns:
            The discount code
            
        Raises:
            NotFoundError: If the discount code doesn't exist
        """
        logger.info(f"Getting discount code with ID: {discount_code_id}")
        
        discount_code = await self.discount_code_repo.get(db, id=discount_code_id)
        if not discount_code:
            logger.warning(f"Discount code with ID {discount_code_id} not found")
            raise NotFoundError(f"کد تخفیف با شناسه {discount_code_id} یافت نشد")
        
        return DiscountCodeRead.model_validate(discount_code)
    
    async def get_all_discount_codes(
        self, 
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[DiscountCodeRead]:
        """
        Get all discount codes with pagination.
        
        Args:
            db: Database session
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to retrieve
            
        Returns:
            List of discount codes
        """
        logger.info(f"Getting all discount codes (skip={skip}, limit={limit})")
        
        discount_codes = await self.discount_code_repo.get_multi(db, skip=skip, limit=limit)
        return [DiscountCodeRead.model_validate(dc) for dc in discount_codes]
    
    async def get_active_discount_codes(
        self, 
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[DiscountCodeRead]:
        """
        Get active discount codes with pagination.
        
        Args:
            db: Database session
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to retrieve
            
        Returns:
            List of active discount codes
        """
        logger.info(f"Getting active discount codes (skip={skip}, limit={limit})")
        
        discount_codes = await self.discount_code_repo.get_active_discount_codes(
            db, skip=skip, limit=limit
        )
        return [DiscountCodeRead.model_validate(dc) for dc in discount_codes]
    
    async def get_discount_code_by_code(
        self, 
        db: AsyncSession, 
        code: str
    ) -> Optional[DiscountCodeRead]:
        """
        Get a discount code by its code value.
        
        Args:
            db: Database session
            code: The discount code to retrieve
            
        Returns:
            The discount code if found, None otherwise
        """
        logger.info(f"Getting discount code by code: {code}")
        
        discount_code = await self.discount_code_repo.get_by_code(db, code=code)
        if not discount_code:
            logger.info(f"Discount code '{code}' not found")
            return None
        
        return DiscountCodeRead.model_validate(discount_code)
    
    async def validate_discount_code(
        self, 
        db: AsyncSession, 
        code: str, 
        original_amount: Decimal
    ) -> DiscountCodeValidationResult:
        """
        Validate a discount code and calculate the discount amount.
        
        Args:
            db: Database session
            code: The discount code to validate
            original_amount: The original amount to apply the discount to
            
        Returns:
            A DiscountCodeValidationResult with validation info and discount amount
        """
        logger.info(f"Validating discount code: {code} for amount {original_amount}")
        
        # Validate the discount code
        discount_code = await self.discount_code_repo.validate_discount_code(db, code=code)
        
        if not discount_code:
            logger.info(f"Discount code '{code}' is invalid or expired")
            return DiscountCodeValidationResult(
                is_valid=False,
                message="کد تخفیف نامعتبر یا منقضی شده است",
                discount_code=None,
                discount_amount=None
            )
        
        # Calculate the discount amount
        discount_amount = self._calculate_discount_amount(
            discount_code.discount_type, 
            discount_code.discount_value, 
            original_amount
        )
        
        logger.info(f"Discount code '{code}' is valid. Applied discount: {discount_amount}")
        return DiscountCodeValidationResult(
            is_valid=True,
            message="کد تخفیف با موفقیت اعمال شد",
            discount_code=DiscountCodeRead.model_validate(discount_code),
            discount_amount=discount_amount
        )
    
    async def increment_discount_code_usage(
        self, 
        db: AsyncSession, 
        discount_code_id: int
    ) -> DiscountCodeRead:
        """
        Increment the usage count for a discount code.
        
        Args:
            db: Database session
            discount_code_id: ID of the discount code
            
        Returns:
            The updated discount code
            
        Raises:
            NotFoundError: If the discount code doesn't exist
            ServiceError: If there's an error updating the usage count
        """
        try:
            logger.info(f"Incrementing usage count for discount code ID: {discount_code_id}")
            
            updated_code = await self.discount_code_repo.increment_used_count(
                db, discount_code_id=discount_code_id
            )
            await db.commit()
            
            logger.info(f"Successfully incremented usage count for discount code ID: {discount_code_id}")
            return DiscountCodeRead.model_validate(updated_code)
        
        except NotFoundError:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Error incrementing discount code usage: {e}", exc_info=True)
            raise ServiceError("خطا در بروزرسانی تعداد استفاده از کد تخفیف")
    
    def _calculate_discount_amount(
        self, 
        discount_type: DiscountType, 
        discount_value: Decimal, 
        original_amount: Decimal
    ) -> Decimal:
        """
        Calculate the discount amount based on discount type and value.
        
        Args:
            discount_type: FIXED or PERCENTAGE
            discount_value: Value of the discount
            original_amount: Original amount before discount
            
        Returns:
            Calculated discount amount
        """
        if discount_type == DiscountType.FIXED:
            # Fixed amount discount
            return min(discount_value, original_amount)
        else:
            # Percentage discount
            percentage = discount_value / Decimal(100)
            return (original_amount * percentage).quantize(Decimal('0.01')) 