"""Repository for Order model operations."""

from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from core.database.models.order import Order, OrderStatus
from core.schemas.order import OrderCreate, OrderUpdate
from core.database.repositories.base_repo import BaseRepository
from core.exceptions import ServiceError, NotFoundError

logger = logging.getLogger(__name__)

class OrderRepository(BaseRepository[Order, OrderCreate, OrderUpdate]):
    """
    Repository for Order model operations.
    Inherits basic CRUD operations from BaseRepository.
    """
    
    def __init__(self):
        super().__init__(model=Order)
    
    async def get_by_id_with_relations(
        self, 
        db_session: AsyncSession, 
        *, 
        order_id: int,
        load_user: bool = False,
        load_plan: bool = False,
        load_discount_code: bool = False,
        load_payments: bool = False,
        load_client_accounts: bool = False
    ) -> Optional[Order]:
        """
        Get an order by ID with optional related entities.
        
        Args:
            db_session: The database session
            order_id: ID of the order to retrieve
            load_user: Whether to load the related user
            load_plan: Whether to load the related plan
            load_discount_code: Whether to load the related discount code
            load_payments: Whether to load the related payments
            load_client_accounts: Whether to load the related client accounts
            
        Returns:
            The Order if found with requested relations, None otherwise
        """
        try:
            stmt = select(self._model).where(self._model.id == order_id)
            
            if load_user:
                stmt = stmt.options(joinedload(self._model.user))
            
            if load_plan:
                stmt = stmt.options(joinedload(self._model.plan))
            
            if load_discount_code:
                stmt = stmt.options(joinedload(self._model.discount_code))
            
            if load_payments:
                stmt = stmt.options(joinedload(self._model.payments))
            
            if load_client_accounts:
                stmt = stmt.options(joinedload(self._model.client_accounts))
            
            result = await db_session.execute(stmt)
            return result.unique().scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error retrieving order with ID {order_id}: {e}", exc_info=True)
            return None
    
    async def get_orders_by_user(
        self, 
        db_session: AsyncSession, 
        *, 
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Order]:
        """
        Get orders for a specific user with pagination.
        
        Args:
            db_session: The database session
            user_id: ID of the user
            skip: Number of records to skip
            limit: Maximum number of records to retrieve
            
        Returns:
            A list of Order objects
        """
        try:
            stmt = (
                select(self._model)
                .where(self._model.user_id == user_id)
                .order_by(desc(self._model.created_at))
                .offset(skip)
                .limit(limit)
            )
            
            result = await db_session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error retrieving orders for user {user_id}: {e}", exc_info=True)
            return []
    
    async def get_orders_by_status(
        self, 
        db_session: AsyncSession, 
        *, 
        status: OrderStatus,
        skip: int = 0,
        limit: int = 100
    ) -> List[Order]:
        """
        Get orders with a specific status with pagination.
        
        Args:
            db_session: The database session
            status: Status of the orders to retrieve
            skip: Number of records to skip
            limit: Maximum number of records to retrieve
            
        Returns:
            A list of Order objects
        """
        try:
            stmt = (
                select(self._model)
                .where(self._model.status == status)
                .order_by(desc(self._model.created_at))
                .offset(skip)
                .limit(limit)
            )
            
            result = await db_session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error retrieving orders with status {status}: {e}", exc_info=True)
            return []
    
    async def get_orders_with_discount_code(
        self, 
        db_session: AsyncSession, 
        *, 
        discount_code_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Order]:
        """
        Get orders that used a specific discount code.
        
        Args:
            db_session: The database session
            discount_code_id: ID of the discount code
            skip: Number of records to skip
            limit: Maximum number of records to retrieve
            
        Returns:
            A list of Order objects
        """
        try:
            stmt = (
                select(self._model)
                .where(self._model.discount_code_id == discount_code_id)
                .order_by(desc(self._model.created_at))
                .offset(skip)
                .limit(limit)
            )
            
            result = await db_session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error retrieving orders with discount code {discount_code_id}: {e}", exc_info=True)
            return []
    
    async def count_orders_by_status(self, db_session: AsyncSession) -> Dict[OrderStatus, int]:
        """
        Count orders grouped by status.
        
        Args:
            db_session: The database session
            
        Returns:
            A dictionary with status as key and count as value
        """
        try:
            stmt = (
                select(self._model.status, func.count(self._model.id))
                .group_by(self._model.status)
            )
            
            result = await db_session.execute(stmt)
            status_counts = {status: count for status, count in result.all()}
            
            # Ensure all statuses are represented
            for status in OrderStatus:
                if status not in status_counts:
                    status_counts[status] = 0
            
            return status_counts
        except Exception as e:
            logger.error(f"Error counting orders by status: {e}", exc_info=True)
            return {status: 0 for status in OrderStatus} 