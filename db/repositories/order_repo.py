import logging
from typing import List, Optional, Any, Dict
from datetime import datetime # Added datetime

from sqlalchemy import update, delete # Added update, delete
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Order, OrderStatus # Import OrderStatus from db.models
from db.repositories.base_repository import BaseRepository
from db.schemas.order import OrderCreate, OrderUpdate # Assuming these exist and match

logger = logging.getLogger(__name__) # Added logger

class OrderRepository(BaseRepository[Order]): # Inherit from BaseRepository[Order]
    def __init__(self, session: AsyncSession):
        super().__init__(session, Order)

    # BaseRepository provides get_by_id, get_all, delete
    
    async def create(self, order_data: Dict[str, Any]) -> Order:
        """ Creates a new order using BaseRepository create method """
        # Validate data if using OrderCreate schema later
        # try:
        #     create_data = OrderCreate(**order_data).dict(exclude_unset=True)
        # except ValidationError as e:
        #     logger.error(f"Order validation failed: {e}")
        #     raise
        # return await super().create(create_data)
        # For now, use the dictionary directly
        return await super().create(order_data)

    async def update_status(self, order_id: int, status: OrderStatus, fulfilled_at: Optional[datetime] = None) -> Optional[Order]:
        """ Updates the status of an order using BaseRepository update method """
        update_data = {"status": status, "updated_at": datetime.utcnow()}
        if status == OrderStatus.COMPLETED and fulfilled_at:
             update_data["fulfilled_at"] = fulfilled_at
        elif status == OrderStatus.COMPLETED and not fulfilled_at: # Auto-set fulfilled_at if COMPLETED
             update_data["fulfilled_at"] = datetime.utcnow()
             
        return await super().update(order_id, update_data)

    async def set_fulfilled_at(self, order_id: int, fulfilled_time: datetime) -> Optional[Order]:
        """ Sets the fulfilled_at timestamp for an order """
        return await super().update(order_id, {"fulfilled_at": fulfilled_time, "updated_at": datetime.utcnow()})
        
    async def get_by_user_id(
        self, 
        user_id: int, 
        limit: int = 10, 
        offset: int = 0,
        order_by: Optional[List[Any]] = None # Example: [Order.created_at.desc()]
    ) -> List[Order]:
        """ Fetches orders by user ID with pagination and ordering """
        query = select(self.model).where(self.model.user_id == user_id)
        if order_by is not None:
            query = query.order_by(*order_by)
        else:
            query = query.order_by(self.model.created_at.desc()) # Default ordering
            
        query = query.offset(offset).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())
        
    async def get_pending_orders(self) -> List[Order]:
        """ Fetches all orders with PENDING status """
        query = select(self.model).where(self.model.status == OrderStatus.PENDING)
        result = await self.session.execute(query)
        return list(result.scalars().all())

# Remove placeholder code below 