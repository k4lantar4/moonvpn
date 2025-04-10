"""Service for managing orders."""

import logging
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession

from core.database.models.order import Order, OrderStatus
from core.database.repositories import OrderRepository, DiscountCodeRepository
from core.schemas.order import OrderCreate, OrderUpdate, OrderRead, OrderWithRelations
from core.exceptions import NotFoundError, ValidationError, ServiceError
from bot.services.discount_code_service import DiscountCodeService

logger = logging.getLogger(__name__)

class OrderService:
    """Service for managing orders."""
    
    def __init__(self):
        self.order_repo = OrderRepository()
        self.discount_code_repo = DiscountCodeRepository()
        self.discount_code_service = DiscountCodeService()
    
    async def create_order(
        self, 
        db: AsyncSession, 
        order_data: OrderCreate
    ) -> OrderRead:
        """
        Create a new order.
        
        Args:
            db: Database session
            order_data: Data for creating the order
            
        Returns:
            The created order
            
        Raises:
            ValidationError: If there's an error validating the data
            ServiceError: If there's an error creating the order
        """
        try:
            logger.info(f"Creating order for user ID: {order_data.user_id}, plan ID: {order_data.plan_id}")
            
            # Apply discount code if provided
            if order_data.discount_code_id:
                # Verify discount code exists and is valid
                discount_code = await self.discount_code_repo.get(db, id=order_data.discount_code_id)
                if not discount_code:
                    logger.warning(f"Discount code with ID {order_data.discount_code_id} not found")
                    raise ValidationError("کد تخفیف نامعتبر است")
                
                # Validate the discount code
                discount_validation = await self.discount_code_service.validate_discount_code(
                    db, 
                    code=discount_code.code, 
                    original_amount=order_data.amount
                )
                
                if not discount_validation.is_valid:
                    logger.warning(f"Invalid discount code: {discount_code.code}")
                    raise ValidationError(discount_validation.message)
                
                # Set discount amount
                order_data.discount_amount = discount_validation.discount_amount
            
            # Create the order
            order = await self.order_repo.create(db, obj_in=order_data)
            
            # Increment discount code usage if used
            if order.discount_code_id:
                await self.discount_code_service.increment_discount_code_usage(
                    db, discount_code_id=order.discount_code_id
                )
            
            await db.commit()
            
            logger.info(f"Successfully created order with ID: {order.id}")
            return OrderRead.model_validate(order)
        
        except ValidationError:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating order: {e}", exc_info=True)
            raise ServiceError("خطا در ایجاد سفارش")
    
    async def update_order_status(
        self, 
        db: AsyncSession, 
        order_id: int, 
        status: OrderStatus
    ) -> OrderRead:
        """
        Update the status of an order.
        
        Args:
            db: Database session
            order_id: ID of the order to update
            status: New status for the order
            
        Returns:
            The updated order
            
        Raises:
            NotFoundError: If the order doesn't exist
            ServiceError: If there's an error updating the order
        """
        try:
            logger.info(f"Updating status of order ID: {order_id} to {status}")
            
            # Get the order
            order = await self.order_repo.get(db, id=order_id)
            if not order:
                logger.warning(f"Order with ID {order_id} not found")
                raise NotFoundError(f"سفارش با شناسه {order_id} یافت نشد")
            
            # Update status and timestamp
            update_data = {
                "status": status,
                "updated_at": datetime.now()
            }
            
            updated_order = await self.order_repo.update(
                db, db_obj=order, obj_in=update_data
            )
            await db.commit()
            
            logger.info(f"Successfully updated status of order ID: {order_id} to {status}")
            return OrderRead.model_validate(updated_order)
        
        except NotFoundError:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating order status: {e}", exc_info=True)
            raise ServiceError("خطا در بروزرسانی وضعیت سفارش")
    
    async def get_order(
        self, 
        db: AsyncSession, 
        order_id: int, 
        with_relations: bool = False
    ) -> OrderRead | OrderWithRelations:
        """
        Get an order by ID.
        
        Args:
            db: Database session
            order_id: ID of the order to retrieve
            with_relations: Whether to load related entities
            
        Returns:
            The order
            
        Raises:
            NotFoundError: If the order doesn't exist
        """
        logger.info(f"Getting order with ID: {order_id}, with_relations: {with_relations}")
        
        if with_relations:
            order = await self.order_repo.get_by_id_with_relations(
                db,
                order_id=order_id,
                load_user=True,
                load_plan=True,
                load_discount_code=True,
                load_payments=True
            )
        else:
            order = await self.order_repo.get(db, id=order_id)
        
        if not order:
            logger.warning(f"Order with ID {order_id} not found")
            raise NotFoundError(f"سفارش با شناسه {order_id} یافت نشد")
        
        if with_relations:
            return OrderWithRelations.model_validate(order)
        else:
            return OrderRead.model_validate(order)
    
    async def get_user_orders(
        self, 
        db: AsyncSession, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 10
    ) -> List[OrderRead]:
        """
        Get orders for a specific user.
        
        Args:
            db: Database session
            user_id: ID of the user
            skip: Number of records to skip
            limit: Maximum number of records to retrieve
            
        Returns:
            List of orders
        """
        logger.info(f"Getting orders for user ID: {user_id} (skip={skip}, limit={limit})")
        
        orders = await self.order_repo.get_orders_by_user(
            db, user_id=user_id, skip=skip, limit=limit
        )
        
        return [OrderRead.model_validate(order) for order in orders]
    
    async def get_orders_by_status(
        self, 
        db: AsyncSession, 
        status: OrderStatus, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[OrderRead]:
        """
        Get orders with a specific status.
        
        Args:
            db: Database session
            status: Status of the orders to retrieve
            skip: Number of records to skip
            limit: Maximum number of records to retrieve
            
        Returns:
            List of orders
        """
        logger.info(f"Getting orders with status: {status} (skip={skip}, limit={limit})")
        
        orders = await self.order_repo.get_orders_by_status(
            db, status=status, skip=skip, limit=limit
        )
        
        return [OrderRead.model_validate(order) for order in orders]
    
    async def apply_discount_to_order(
        self, 
        db: AsyncSession, 
        order_id: int, 
        discount_code: str
    ) -> OrderRead:
        """
        Apply a discount code to an existing order.
        
        Args:
            db: Database session
            order_id: ID of the order
            discount_code: Discount code to apply
            
        Returns:
            The updated order
            
        Raises:
            NotFoundError: If the order doesn't exist
            ValidationError: If the discount code is invalid
            ServiceError: If there's an error applying the discount
        """
        try:
            logger.info(f"Applying discount code '{discount_code}' to order ID: {order_id}")
            
            # Get the order
            order = await self.order_repo.get(db, id=order_id)
            if not order:
                logger.warning(f"Order with ID {order_id} not found")
                raise NotFoundError(f"سفارش با شناسه {order_id} یافت نشد")
            
            # Check if order already has a discount
            if order.discount_code_id:
                logger.warning(f"Order {order_id} already has a discount applied")
                raise ValidationError("این سفارش قبلاً از کد تخفیف استفاده کرده است")
            
            # Validate the discount code
            discount_validation = await self.discount_code_service.validate_discount_code(
                db, code=discount_code, original_amount=order.amount
            )
            
            if not discount_validation.is_valid:
                logger.warning(f"Invalid discount code: {discount_code}")
                raise ValidationError(discount_validation.message)
            
            # Get the discount code entity
            discount_code_entity = await self.discount_code_repo.get_by_code(
                db, code=discount_code
            )
            
            # Update the order with the discount
            update_data = {
                "discount_code_id": discount_code_entity.id,
                "discount_amount": discount_validation.discount_amount,
                "final_amount": order.amount - discount_validation.discount_amount,
                "updated_at": datetime.now()
            }
            
            updated_order = await self.order_repo.update(
                db, db_obj=order, obj_in=update_data
            )
            
            # Increment discount code usage
            await self.discount_code_service.increment_discount_code_usage(
                db, discount_code_id=discount_code_entity.id
            )
            
            await db.commit()
            
            logger.info(f"Successfully applied discount code to order ID: {order_id}")
            return OrderRead.model_validate(updated_order)
        
        except (NotFoundError, ValidationError):
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Error applying discount code: {e}", exc_info=True)
            raise ServiceError("خطا در اعمال کد تخفیف")
    
    async def get_orders_dashboard_stats(self, db: AsyncSession) -> Dict[str, Any]:
        """
        Get dashboard statistics for orders.
        
        Args:
            db: Database session
            
        Returns:
            A dictionary with order statistics
        """
        logger.info("Getting order dashboard statistics")
        
        try:
            # Get orders count by status
            status_counts = await self.order_repo.count_orders_by_status(db)
            
            # Format the counts as a dictionary
            result = {
                "total_orders": sum(status_counts.values()),
                "pending_orders": status_counts.get(OrderStatus.PENDING, 0),
                "completed_orders": status_counts.get(OrderStatus.COMPLETED, 0),
                "failed_orders": status_counts.get(OrderStatus.FAILED, 0),
                "cancelled_orders": status_counts.get(OrderStatus.CANCELLED, 0),
                "status_breakdown": {
                    status.value: count for status, count in status_counts.items()
                }
            }
            
            return result
        except Exception as e:
            logger.error(f"Error getting order dashboard statistics: {e}", exc_info=True)
            return {
                "total_orders": 0,
                "pending_orders": 0,
                "completed_orders": 0,
                "failed_orders": 0,
                "cancelled_orders": 0,
                "status_breakdown": {}
            } 