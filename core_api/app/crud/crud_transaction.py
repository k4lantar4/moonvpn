from typing import List, Optional, Dict, Any, Union, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from datetime import datetime, timedelta
from decimal import Decimal

from app.crud.base import CRUDBase
from app.models.transaction import Transaction, TransactionType, TransactionStatus
from app.schemas.transaction import TransactionCreate, TransactionUpdate
from app.models.user import User
from app.models.order import Order


class CRUDTransaction(CRUDBase[Transaction, TransactionCreate, TransactionUpdate]):
    """CRUD operations for Transaction model"""
    
    def get_by_user(
        self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Transaction]:
        """Get all transactions for a specific user"""
        return (
            db.query(self.model)
            .filter(self.model.user_id == user_id)
            .order_by(desc(self.model.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_by_type(
        self, db: Session, *, type: TransactionType, skip: int = 0, limit: int = 100
    ) -> List[Transaction]:
        """Get all transactions of a specific type"""
        return (
            db.query(self.model)
            .filter(self.model.type == type)
            .order_by(desc(self.model.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_by_status(
        self, db: Session, *, status: TransactionStatus, skip: int = 0, limit: int = 100
    ) -> List[Transaction]:
        """Get all transactions with a specific status"""
        return (
            db.query(self.model)
            .filter(self.model.status == status)
            .order_by(desc(self.model.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_by_transaction_id(
        self, db: Session, *, transaction_id: str
    ) -> Optional[Transaction]:
        """Get a transaction by its external ID"""
        return db.query(self.model).filter(self.model.transaction_id == transaction_id).first()
    
    def get_by_order_id(
        self, db: Session, *, order_id: int
    ) -> List[Transaction]:
        """Get all transactions associated with an order"""
        return (
            db.query(self.model)
            .filter(self.model.order_id == order_id)
            .order_by(desc(self.model.created_at))
            .all()
        )
    
    def get_user_balance(
        self, db: Session, *, user_id: int
    ) -> Decimal:
        """Get the current balance for a user"""
        # Find the most recent transaction to get the latest balance
        latest_transaction = (
            db.query(self.model)
            .filter(self.model.user_id == user_id)
            .order_by(desc(self.model.created_at))
            .first()
        )
        
        if latest_transaction:
            return Decimal(str(latest_transaction.balance_after))
        else:
            return Decimal('0.00')
    
    def get_deposits(
        self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Transaction]:
        """Get all deposits for a user"""
        return (
            db.query(self.model)
            .filter(
                and_(
                    self.model.user_id == user_id,
                    self.model.type == TransactionType.DEPOSIT
                )
            )
            .order_by(desc(self.model.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_withdrawals(
        self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Transaction]:
        """Get all withdrawals for a user"""
        return (
            db.query(self.model)
            .filter(
                and_(
                    self.model.user_id == user_id,
                    self.model.type == TransactionType.WITHDRAW
                )
            )
            .order_by(desc(self.model.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_payments(
        self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Transaction]:
        """Get all order payments for a user"""
        return (
            db.query(self.model)
            .filter(
                and_(
                    self.model.user_id == user_id,
                    self.model.type == TransactionType.ORDER_PAYMENT
                )
            )
            .order_by(desc(self.model.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def complete_transaction(
        self, db: Session, *, transaction_id: int, admin_id: Optional[int] = None, admin_note: Optional[str] = None
    ) -> Transaction:
        """Mark a transaction as completed"""
        transaction = self.get(db, id=transaction_id)
        if not transaction:
            raise ValueError(f"Transaction with ID {transaction_id} not found")
        
        # Create update data
        transaction_update = TransactionUpdate(
            status=TransactionStatus.COMPLETED,
            admin_id=admin_id,
            admin_note=admin_note
        )
        
        # Update the transaction
        return self.update(db, db_obj=transaction, obj_in=transaction_update)
    
    def fail_transaction(
        self, db: Session, *, transaction_id: int, admin_id: Optional[int] = None, admin_note: Optional[str] = None
    ) -> Transaction:
        """Mark a transaction as failed"""
        transaction = self.get(db, id=transaction_id)
        if not transaction:
            raise ValueError(f"Transaction with ID {transaction_id} not found")
        
        # Create update data
        transaction_update = TransactionUpdate(
            status=TransactionStatus.FAILED,
            admin_id=admin_id,
            admin_note=admin_note
        )
        
        # Update the transaction
        return self.update(db, db_obj=transaction, obj_in=transaction_update)
    
    def get_pending_deposits(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[Transaction]:
        """Get all pending deposits that need admin review"""
        return (
            db.query(self.model)
            .filter(
                and_(
                    self.model.type == TransactionType.DEPOSIT,
                    self.model.status == TransactionStatus.PENDING
                )
            )
            .order_by(desc(self.model.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_user_transactions_summary(
        self, db: Session, *, user_id: int
    ) -> Dict[str, Any]:
        """Get summary of user's transaction history"""
        # Get total deposits
        deposits_query = (
            db.query(func.sum(self.model.amount))
            .filter(
                and_(
                    self.model.user_id == user_id,
                    self.model.type == TransactionType.DEPOSIT,
                    self.model.status == TransactionStatus.COMPLETED
                )
            )
        )
        total_deposits = deposits_query.scalar() or 0
        
        # Get total withdrawals
        withdrawals_query = (
            db.query(func.sum(self.model.amount))
            .filter(
                and_(
                    self.model.user_id == user_id,
                    self.model.type == TransactionType.WITHDRAW,
                    self.model.status == TransactionStatus.COMPLETED
                )
            )
        )
        total_withdrawals = withdrawals_query.scalar() or 0
        
        # Get total payments
        payments_query = (
            db.query(func.sum(self.model.amount))
            .filter(
                and_(
                    self.model.user_id == user_id,
                    self.model.type == TransactionType.ORDER_PAYMENT,
                    self.model.status == TransactionStatus.COMPLETED
                )
            )
        )
        total_payments = payments_query.scalar() or 0
        
        # Get total refunds
        refunds_query = (
            db.query(func.sum(self.model.amount))
            .filter(
                and_(
                    self.model.user_id == user_id,
                    self.model.type == TransactionType.REFUND,
                    self.model.status == TransactionStatus.COMPLETED
                )
            )
        )
        total_refunds = refunds_query.scalar() or 0
        
        # Get current balance
        current_balance = self.get_user_balance(db, user_id=user_id)
        
        # Construct summary
        return {
            "user_id": user_id,
            "total_deposits": Decimal(str(total_deposits)),
            "total_withdrawals": Decimal(str(total_withdrawals)),
            "total_payments": Decimal(str(total_payments)),
            "total_refunds": Decimal(str(total_refunds)),
            "current_balance": current_balance
        }

    def create(self, db: Session, *, obj_in: TransactionCreate) -> Transaction:
        """
        Create a new transaction record.
        
        Args:
            db: Database session
            obj_in: Transaction data to create
            
        Returns:
            Created transaction object
        """
        db_obj = Transaction(
            user_id=obj_in.user_id,
            amount=obj_in.amount,
            transaction_type=obj_in.transaction_type,
            status=obj_in.status,
            description=obj_in.description,
            payment_method=obj_in.payment_method,
            payment_reference=obj_in.payment_reference,
            admin_id=obj_in.admin_id,
            admin_note=obj_in.admin_note,
            order_id=obj_in.order_id
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, id: int) -> Optional[Transaction]:
        """
        Get a transaction by ID.
        
        Args:
            db: Database session
            id: Transaction ID
            
        Returns:
            Transaction object if found, None otherwise
        """
        return db.query(Transaction).filter(Transaction.id == id).first()

    def get_transaction_count_by_user(self, db: Session, *, user_id: int) -> int:
        """
        Get the total count of transactions for a user.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Number of transactions for the user
        """
        return db.query(Transaction).filter(Transaction.user_id == user_id).count()

    def get_user_transaction_summary(self, db: Session, *, user_id: int) -> Dict[str, Decimal]:
        """
        Get transaction summary for a user including totals by transaction type.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Dictionary with summary of transactions
        """
        # Get deposits (confirmed only)
        deposits = db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.transaction_type == TransactionType.DEPOSIT,
            Transaction.status == TransactionStatus.COMPLETED
        ).scalar() or Decimal('0')
        
        # Get withdrawals (confirmed only)
        withdrawals = db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.transaction_type == TransactionType.WITHDRAWAL,
            Transaction.status == TransactionStatus.COMPLETED
        ).scalar() or Decimal('0')
        
        # Get purchases (order payments)
        purchases = db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.transaction_type == TransactionType.PAYMENT,
            Transaction.status == TransactionStatus.COMPLETED
        ).scalar() or Decimal('0')
        
        # Get refunds
        refunds = db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.transaction_type == TransactionType.REFUND,
            Transaction.status == TransactionStatus.COMPLETED
        ).scalar() or Decimal('0')
        
        # Get adjustments (both positive and negative)
        adjustments = db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.transaction_type == TransactionType.ADJUSTMENT,
            Transaction.status == TransactionStatus.COMPLETED
        ).scalar() or Decimal('0')
        
        return {
            "total_deposits": deposits,
            "total_withdrawals": withdrawals,
            "total_purchases": purchases,
            "total_refunds": refunds,
            "total_adjustments": adjustments
        }

    def update(
        self, db: Session, *, db_obj: Transaction, obj_in: Union[TransactionUpdate, Dict[str, Any]]
    ) -> Transaction:
        """
        Update a transaction.
        
        Args:
            db: Database session
            db_obj: Existing transaction object
            obj_in: New data to update
            
        Returns:
            Updated transaction object
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        
        for field in update_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
                
        # When updating status to completed, set completed_at
        if 'status' in update_data and update_data['status'] == TransactionStatus.COMPLETED:
            db_obj.completed_at = datetime.utcnow()
                
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_pending_deposits(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[Transaction]:
        """
        Get all pending deposit transactions that need admin approval.
        
        Args:
            db: Database session
            skip: Number of records to skip for pagination
            limit: Maximum number of records to return
            
        Returns:
            List of pending deposit transactions
        """
        return (
            db.query(Transaction)
            .filter(
                Transaction.transaction_type == TransactionType.DEPOSIT,
                Transaction.status == TransactionStatus.PENDING
            )
            .order_by(desc(Transaction.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
        
    def get_by_order(self, db: Session, *, order_id: int) -> List[Transaction]:
        """
        Get all transactions for a specific order.
        
        Args:
            db: Database session
            order_id: Order ID to filter by
            
        Returns:
            List of transactions for the specified order
        """
        return (
            db.query(Transaction)
            .filter(Transaction.order_id == order_id)
            .order_by(desc(Transaction.created_at))
            .all()
        )
        
    def get_user_balance(self, db: Session, *, user_id: int) -> Decimal:
        """
        Calculate the current balance for a user based on all completed transactions.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Current balance as Decimal
        """
        # Deposits and positive adjustments (add to balance)
        income = db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.status == TransactionStatus.COMPLETED,
            or_(
                Transaction.transaction_type == TransactionType.DEPOSIT,
                Transaction.transaction_type == TransactionType.REFUND,
                and_(
                    Transaction.transaction_type == TransactionType.ADJUSTMENT,
                    Transaction.amount > 0
                )
            )
        ).scalar() or Decimal('0')
        
        # Withdrawals, payments, and negative adjustments (subtract from balance)
        expenses = db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.status == TransactionStatus.COMPLETED,
            or_(
                Transaction.transaction_type == TransactionType.WITHDRAWAL,
                Transaction.transaction_type == TransactionType.PAYMENT,
                and_(
                    Transaction.transaction_type == TransactionType.ADJUSTMENT,
                    Transaction.amount < 0
                )
            )
        ).scalar() or Decimal('0')
        
        # Return the balance (income - expenses)
        # For negative adjustments (where amount is already negative), we use addition
        return income - expenses


# Create a singleton instance for use across the app
transaction = CRUDTransaction(Transaction) 