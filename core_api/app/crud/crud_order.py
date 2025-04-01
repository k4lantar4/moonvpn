from typing import List, Optional, Dict, Any, Union
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from datetime import datetime, timedelta

from app.crud.base import CRUDBase
from app.models.order import Order, OrderStatus
from app.schemas.order import OrderCreate, OrderUpdate


class CRUDOrder(CRUDBase[Order, OrderCreate, OrderUpdate]):
    """CRUD operations for Order model"""

    # Get orders by user
    def get_by_user(
        self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Order]:
        """Get all orders for a specific user"""
        return (
            db.query(self.model)
            .filter(self.model.user_id == user_id)
            .order_by(desc(self.model.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    # Get orders by status
    def get_by_status(
        self, db: Session, *, status: OrderStatus, skip: int = 0, limit: int = 100
    ) -> List[Order]:
        """Get all orders with a specific status"""
        return (
            db.query(self.model)
            .filter(self.model.status == status)
            .order_by(desc(self.model.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    # Get orders by multiple statuses
    def get_by_statuses(
        self, db: Session, *, statuses: List[OrderStatus], skip: int = 0, limit: int = 100
    ) -> List[Order]:
        """Get all orders with any of the specified statuses"""
        return (
            db.query(self.model)
            .filter(self.model.status.in_(statuses))
            .order_by(desc(self.model.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    # Get by order_id (external ID)
    def get_by_order_id(self, db: Session, *, order_id: str) -> Optional[Order]:
        """Get an order by its UUID (order_id field)"""
        return db.query(self.model).filter(self.model.order_id == order_id).first()
    
    # Process payment
    def process_payment(
        self, 
        db: Session, 
        *, 
        order_id: int, 
        payment_method: str, 
        payment_reference: str,
        admin_id: Optional[int] = None,
        admin_note: Optional[str] = None
    ) -> Order:
        """Mark an order as paid with payment details"""
        order = self.get(db, id=order_id)
        if not order:
            raise ValueError(f"Order with ID {order_id} not found")
        
        order_update = OrderUpdate(
            status=OrderStatus.PAID,
            payment_method=payment_method,
            payment_reference=payment_reference,
            paid_at=datetime.utcnow(),
            admin_id=admin_id,
            admin_note=admin_note
        )
        return self.update(db, db_obj=order, obj_in=order_update)
    
    # Confirm an order (Account created successfully)
    def confirm_order(
        self,
        db: Session,
        *,
        order_id: int,
        panel_id: int,
        inbound_id: int,
        client_uuid: str,
        client_email: str,
        expires_at: datetime,
        admin_id: Optional[int] = None,
        admin_note: Optional[str] = None,
        subscription_id: Optional[int] = None
    ) -> Order:
        """Mark an order as confirmed and store client connection details"""
        order = self.get(db, id=order_id)
        if not order:
            raise ValueError(f"Order with ID {order_id} not found")
        
        order_update = OrderUpdate(
            status=OrderStatus.CONFIRMED,
            panel_id=panel_id,
            inbound_id=inbound_id,
            client_uuid=client_uuid,
            client_email=client_email,
            confirmed_at=datetime.utcnow(),
            expires_at=expires_at,
            admin_id=admin_id,
            admin_note=admin_note,
            subscription_id=subscription_id
        )
        return self.update(db, db_obj=order, obj_in=order_update)
    
    # Reject an order
    def reject_order(
        self,
        db: Session,
        *,
        order_id: int,
        admin_id: Optional[int] = None,
        admin_note: Optional[str] = None
    ) -> Order:
        """Mark an order as rejected"""
        order = self.get(db, id=order_id)
        if not order:
            raise ValueError(f"Order with ID {order_id} not found")
        
        order_update = OrderUpdate(
            status=OrderStatus.REJECTED,
            admin_id=admin_id,
            admin_note=admin_note
        )
        return self.update(db, db_obj=order, obj_in=order_update)
    
    # Cancel an order
    def cancel_order(
        self,
        db: Session,
        *,
        order_id: int,
        admin_id: Optional[int] = None,
        admin_note: Optional[str] = None
    ) -> Order:
        """Mark an order as canceled"""
        order = self.get(db, id=order_id)
        if not order:
            raise ValueError(f"Order with ID {order_id} not found")
        
        order_update = OrderUpdate(
            status=OrderStatus.CANCELED,
            admin_id=admin_id,
            admin_note=admin_note
        )
        return self.update(db, db_obj=order, obj_in=order_update)
    
    # Mark order as failed
    def fail_order(
        self,
        db: Session,
        *,
        order_id: int,
        admin_id: Optional[int] = None,
        admin_note: Optional[str] = None
    ) -> Order:
        """Mark an order as failed (e.g. if account creation failed)"""
        order = self.get(db, id=order_id)
        if not order:
            raise ValueError(f"Order with ID {order_id} not found")
        
        order_update = OrderUpdate(
            status=OrderStatus.FAILED,
            admin_id=admin_id,
            admin_note=admin_note
        )
        return self.update(db, db_obj=order, obj_in=order_update)
    
    # Get orders that need manual processing
    def get_pending_manual_processing(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[Order]:
        """Get orders that need manual processing (paid but not confirmed)"""
        return (
            db.query(self.model)
            .filter(self.model.status == OrderStatus.PAID)
            .order_by(desc(self.model.paid_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    # Get expired orders
    def get_expired_orders(self, db: Session, *, days: int = 7) -> List[Order]:
        """Get orders that have expired in the last X days"""
        expiry_threshold = datetime.utcnow() - timedelta(days=days)
        return (
            db.query(self.model)
            .filter(
                and_(
                    self.model.status == OrderStatus.PENDING,
                    self.model.created_at < expiry_threshold
                )
            )
            .all()
        )
    
    # Mark expired orders
    def mark_expired_orders(self, db: Session, *, days: int = 7) -> int:
        """Mark pending orders older than X days as expired.
        Returns the number of orders marked as expired."""
        expiry_threshold = datetime.utcnow() - timedelta(days=days)
        expired_orders = (
            db.query(self.model)
            .filter(
                and_(
                    self.model.status == OrderStatus.PENDING,
                    self.model.created_at < expiry_threshold
                )
            )
            .all()
        )
        
        for order in expired_orders:
            order.status = OrderStatus.EXPIRED
        
        db.commit()
        return len(expired_orders)


# Create a singleton instance for use across the app
order = CRUDOrder(Order) 