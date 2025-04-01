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
    
    # Get orders with payment proof
    def get_orders_with_payment_proof(
        self, db: Session, *, verified: Optional[bool] = None, skip: int = 0, limit: int = 100
    ) -> List[Order]:
        """
        Get orders with payment proof.
        
        If verified is True, returns orders with verified payment proof.
        If verified is False, returns orders with rejected payment proof.
        If verified is None, returns all orders with payment proof.
        """
        query = db.query(self.model).filter(self.model.payment_proof_img_url.isnot(None))
        
        if verified is True:
            query = query.filter(self.model.payment_verified_at.isnot(None))
            query = query.filter(self.model.status.in_([OrderStatus.PAID, OrderStatus.CONFIRMED]))
        elif verified is False:
            query = query.filter(self.model.payment_verified_at.isnot(None))
            query = query.filter(self.model.status == OrderStatus.REJECTED)
        
        return query.order_by(desc(self.model.payment_proof_submitted_at)).offset(skip).limit(limit).all()
    
    # Get orders pending verification
    def get_orders_pending_verification(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[Order]:
        """Get orders with payment proof that are waiting for verification"""
        return (
            db.query(self.model)
            .filter(self.model.status == OrderStatus.VERIFICATION_PENDING)
            .order_by(desc(self.model.payment_proof_submitted_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    # Get orders verified by admin
    def get_orders_verified_by_admin(
        self, db: Session, *, admin_id: int, skip: int = 0, limit: int = 100
    ) -> List[Order]:
        """Get orders verified by a specific admin"""
        return (
            db.query(self.model)
            .filter(self.model.payment_verification_admin_id == admin_id)
            .order_by(desc(self.model.payment_verified_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    # Get orders verification metrics
    def get_verification_metrics(
        self, db: Session, *, days: int = 30
    ) -> Dict[str, Any]:
        """Get metrics about order verification for the last X days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Total orders with payment proof
        total_with_proof = (
            db.query(func.count(self.model.id))
            .filter(
                and_(
                    self.model.payment_proof_img_url.isnot(None),
                    self.model.payment_proof_submitted_at >= cutoff_date
                )
            )
            .scalar()
        )
        
        # Total verified orders
        total_verified = (
            db.query(func.count(self.model.id))
            .filter(
                and_(
                    self.model.payment_verified_at.isnot(None),
                    self.model.status.in_([OrderStatus.PAID, OrderStatus.CONFIRMED]),
                    self.model.payment_proof_submitted_at >= cutoff_date
                )
            )
            .scalar()
        )
        
        # Total rejected orders
        total_rejected = (
            db.query(func.count(self.model.id))
            .filter(
                and_(
                    self.model.payment_verified_at.isnot(None),
                    self.model.status == OrderStatus.REJECTED,
                    self.model.payment_proof_submitted_at >= cutoff_date
                )
            )
            .scalar()
        )
        
        # Total pending verification
        total_pending = (
            db.query(func.count(self.model.id))
            .filter(
                and_(
                    self.model.status == OrderStatus.VERIFICATION_PENDING,
                    self.model.payment_proof_submitted_at >= cutoff_date
                )
            )
            .scalar()
        )
        
        # Average verification time
        avg_verification_time = 0
        if total_verified + total_rejected > 0:
            verification_times = (
                db.query(
                    func.timestampdiff(
                        func.second,
                        self.model.payment_proof_submitted_at,
                        self.model.payment_verified_at
                    )
                )
                .filter(
                    and_(
                        self.model.payment_proof_submitted_at >= cutoff_date,
                        self.model.payment_verified_at.isnot(None)
                    )
                )
                .all()
            )
            
            if verification_times:
                total_seconds = sum([time[0] or 0 for time in verification_times])
                avg_verification_time = total_seconds / len(verification_times)
        
        return {
            "total_with_proof": total_with_proof,
            "total_verified": total_verified,
            "total_rejected": total_rejected,
            "total_pending": total_pending,
            "avg_verification_time_seconds": avg_verification_time,
            "verification_rate": (total_verified / total_with_proof * 100) if total_with_proof > 0 else 0,
            "rejection_rate": (total_rejected / total_with_proof * 100) if total_with_proof > 0 else 0,
            "period_days": days
        }


# Create a singleton instance for use across the app
order = CRUDOrder(Order)