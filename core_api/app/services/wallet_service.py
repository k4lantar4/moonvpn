import logging
from decimal import Decimal
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.transaction import Transaction, TransactionType, TransactionStatus
from app.models.order import Order, OrderStatus, PaymentMethod
from app import crud

# Configure logger
logger = logging.getLogger(__name__)


class WalletException(Exception):
    """Custom exception for wallet operations"""
    pass


class InsufficientFundsException(WalletException):
    """Exception raised when user has insufficient funds"""
    pass


class InvalidAmountException(WalletException):
    """Exception raised when an invalid amount is provided"""
    pass


class WalletService:
    """
    Service for managing wallet and transaction operations.
    """
    
    @staticmethod
    def get_balance(db: Session, user_id: int) -> Decimal:
        """
        Get the current balance for a user.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Current balance as Decimal
        """
        user = crud.user.get(db, id=user_id)
        if not user:
            raise WalletException(f"User with ID {user_id} not found")
        
        return user.wallet_balance
    
    @staticmethod
    def deposit(
        db: Session,
        user_id: int,
        amount: Decimal,
        payment_method: str,
        payment_reference: Optional[str] = None,
        description: Optional[str] = None,
        admin_id: Optional[int] = None,
        auto_approve: bool = False,
    ) -> Transaction:
        """
        Create a deposit transaction.
        
        Args:
            db: Database session
            user_id: User ID
            amount: Amount to deposit
            payment_method: Payment method used
            payment_reference: Payment reference number
            description: Transaction description
            admin_id: Admin who created the transaction
            auto_approve: Whether to automatically approve and process the deposit
            
        Returns:
            Created Transaction object
            
        Raises:
            WalletException: On validation errors
            InvalidAmountException: If amount is invalid
        """
        # Validate amount
        if amount <= 0:
            raise InvalidAmountException("Deposit amount must be positive")
        
        # Get the user
        user = crud.user.get(db, id=user_id)
        if not user:
            raise WalletException(f"User with ID {user_id} not found")
        
        # Calculate new balance (only changes if auto_approve is True)
        current_balance = user.wallet_balance
        new_balance = current_balance + amount if auto_approve else current_balance
        
        # Create transaction
        transaction_data = {
            "user_id": user_id,
            "amount": amount,
            "balance_after": new_balance,
            "type": TransactionType.DEPOSIT,
            "status": TransactionStatus.COMPLETED if auto_approve else TransactionStatus.PENDING,
            "payment_method": payment_method,
            "payment_reference": payment_reference,
            "description": description or "Wallet deposit",
            "admin_id": admin_id,
        }
        
        # Create the transaction
        transaction = crud.transaction.create(db, obj_in=transaction_data)
        
        # Update user balance if auto-approved
        if auto_approve:
            user.wallet_balance = new_balance
            db.commit()
            logger.info(f"Auto-approved deposit of {amount} for user {user_id}. New balance: {new_balance}")
        
        return transaction
    
    @staticmethod
    def withdraw(
        db: Session,
        user_id: int,
        amount: Decimal,
        description: Optional[str] = None,
        admin_id: Optional[int] = None,
    ) -> Transaction:
        """
        Create a withdrawal transaction.
        
        Args:
            db: Database session
            user_id: User ID
            amount: Amount to withdraw (positive value)
            description: Transaction description
            admin_id: Admin who created the transaction
            
        Returns:
            Created Transaction object
            
        Raises:
            WalletException: On validation errors
            InvalidAmountException: If amount is invalid
            InsufficientFundsException: If user has insufficient funds
        """
        # Validate amount
        if amount <= 0:
            raise InvalidAmountException("Withdrawal amount must be positive")
        
        # Get the user
        user = crud.user.get(db, id=user_id)
        if not user:
            raise WalletException(f"User with ID {user_id} not found")
        
        # Check if user has enough balance
        if user.wallet_balance < amount:
            raise InsufficientFundsException(
                f"Insufficient funds: {user.wallet_balance} available, {amount} requested"
            )
        
        # Calculate new balance
        current_balance = user.wallet_balance
        new_balance = current_balance - amount
        
        # Create transaction
        transaction_data = {
            "user_id": user_id,
            "amount": -amount,  # Negative for withdrawal
            "balance_after": new_balance,
            "type": TransactionType.WITHDRAW,
            "status": TransactionStatus.COMPLETED,  # Withdrawals are always completed immediately
            "description": description or "Wallet withdrawal",
            "admin_id": admin_id,
        }
        
        # Create the transaction
        transaction = crud.transaction.create(db, obj_in=transaction_data)
        
        # Update user balance
        user.wallet_balance = new_balance
        db.commit()
        logger.info(f"Processed withdrawal of {amount} for user {user_id}. New balance: {new_balance}")
        
        return transaction
    
    @staticmethod
    def pay_for_order(
        db: Session,
        user_id: int,
        order_id: int,
        admin_id: Optional[int] = None,
    ) -> Tuple[Transaction, Order]:
        """
        Pay for an order using wallet balance.
        
        Args:
            db: Database session
            user_id: User ID
            order_id: Order ID
            admin_id: Admin who created the transaction
            
        Returns:
            Tuple of (created Transaction, updated Order)
            
        Raises:
            WalletException: On validation errors
            InsufficientFundsException: If user has insufficient funds
        """
        # Get the user
        user = crud.user.get(db, id=user_id)
        if not user:
            raise WalletException(f"User with ID {user_id} not found")
        
        # Get the order
        order = crud.order.get(db, id=order_id)
        if not order:
            raise WalletException(f"Order with ID {order_id} not found")
        
        # Validate that order belongs to user
        if order.user_id != user_id:
            raise WalletException(f"Order {order_id} does not belong to user {user_id}")
        
        # Validate order status
        if order.status != OrderStatus.PENDING:
            raise WalletException(
                f"Order is in state {order.status.value}, expected PENDING"
            )
        
        # Get the amount to pay
        amount = Decimal(str(order.final_amount))
        
        # Check if user has enough balance
        if user.wallet_balance < amount:
            raise InsufficientFundsException(
                f"Insufficient funds: {user.wallet_balance} available, {amount} required"
            )
        
        # Calculate new balance
        current_balance = user.wallet_balance
        new_balance = current_balance - amount
        
        # Create transaction
        transaction_data = {
            "user_id": user_id,
            "order_id": order_id,
            "amount": -amount,  # Negative for payment
            "balance_after": new_balance,
            "type": TransactionType.ORDER_PAYMENT,
            "status": TransactionStatus.COMPLETED,
            "description": f"Payment for order {order.order_id}",
            "admin_id": admin_id,
        }
        
        # Create the transaction
        transaction = crud.transaction.create(db, obj_in=transaction_data)
        
        # Update user balance
        user.wallet_balance = new_balance
        
        # Update order status to PAID
        order_update = {
            "status": OrderStatus.PAID,
            "payment_method": PaymentMethod.WALLET,
            "payment_reference": f"Transaction {transaction.transaction_id}",
            "paid_at": datetime.utcnow(),
        }
        order = crud.order.update(db, db_obj=order, obj_in=order_update)
        
        # Commit changes
        db.commit()
        logger.info(f"Processed payment of {amount} for order {order_id} by user {user_id}. New balance: {new_balance}")
        
        return transaction, order
    
    @staticmethod
    def refund_order(
        db: Session,
        order_id: int,
        amount: Optional[Decimal] = None,
        admin_id: Optional[int] = None,
        admin_note: Optional[str] = None,
    ) -> Tuple[Transaction, Order]:
        """
        Refund an order to the user's wallet.
        
        Args:
            db: Database session
            order_id: Order ID
            amount: Amount to refund (if None, refunds the full order amount)
            admin_id: Admin who created the transaction
            admin_note: Note from admin
            
        Returns:
            Tuple of (created Transaction, updated Order)
            
        Raises:
            WalletException: On validation errors
        """
        # Get the order
        order = crud.order.get(db, id=order_id)
        if not order:
            raise WalletException(f"Order with ID {order_id} not found")
        
        # Validate order status (only paid, confirmed, or failed orders can be refunded)
        valid_statuses = [OrderStatus.PAID, OrderStatus.CONFIRMED, OrderStatus.FAILED]
        if order.status not in valid_statuses:
            raise WalletException(
                f"Order is in state {order.status.value}, cannot refund"
            )
        
        # Get the user
        user = crud.user.get(db, id=order.user_id)
        if not user:
            raise WalletException(f"User with ID {order.user_id} not found")
        
        # Determine refund amount
        if amount is None:
            amount = Decimal(str(order.final_amount))
        else:
            # Validate refund amount
            if amount <= 0:
                raise InvalidAmountException("Refund amount must be positive")
            if amount > Decimal(str(order.final_amount)):
                raise InvalidAmountException(
                    f"Refund amount {amount} exceeds order amount {order.final_amount}"
                )
        
        # Calculate new balance
        current_balance = user.wallet_balance
        new_balance = current_balance + amount
        
        # Create transaction
        transaction_data = {
            "user_id": order.user_id,
            "order_id": order_id,
            "amount": amount,  # Positive for refund
            "balance_after": new_balance,
            "type": TransactionType.REFUND,
            "status": TransactionStatus.COMPLETED,
            "description": f"Refund for order {order.order_id}",
            "admin_note": admin_note,
            "admin_id": admin_id,
        }
        
        # Create the transaction
        transaction = crud.transaction.create(db, obj_in=transaction_data)
        
        # Update user balance
        user.wallet_balance = new_balance
        
        # Update order status to CANCELED if it was a full refund
        if amount == Decimal(str(order.final_amount)):
            order_update = {
                "status": OrderStatus.CANCELED,
                "admin_note": admin_note or "Order refunded and canceled",
                "admin_id": admin_id,
            }
            order = crud.order.update(db, db_obj=order, obj_in=order_update)
        
        # Commit changes
        db.commit()
        logger.info(f"Processed refund of {amount} for order {order_id} to user {order.user_id}. New balance: {new_balance}")
        
        return transaction, order
    
    @staticmethod
    def approve_deposit(
        db: Session,
        transaction_id: int,
        admin_id: Optional[int] = None,
        admin_note: Optional[str] = None,
    ) -> Transaction:
        """
        Approve a pending deposit transaction.
        
        Args:
            db: Database session
            transaction_id: Transaction ID
            admin_id: Admin who approved the transaction
            admin_note: Note from admin
            
        Returns:
            Updated Transaction object
            
        Raises:
            WalletException: On validation errors
        """
        # Get the transaction
        transaction = crud.transaction.get(db, id=transaction_id)
        if not transaction:
            raise WalletException(f"Transaction with ID {transaction_id} not found")
        
        # Validate transaction type and status
        if transaction.type != TransactionType.DEPOSIT:
            raise WalletException(
                f"Transaction is of type {transaction.type.value}, expected DEPOSIT"
            )
        
        if transaction.status != TransactionStatus.PENDING:
            raise WalletException(
                f"Transaction is in state {transaction.status.value}, expected PENDING"
            )
        
        # Get the user
        user = crud.user.get(db, id=transaction.user_id)
        if not user:
            raise WalletException(f"User with ID {transaction.user_id} not found")
        
        # Calculate new balance
        current_balance = user.wallet_balance
        amount = Decimal(str(transaction.amount))
        new_balance = current_balance + amount
        
        # Update transaction
        transaction_update = {
            "status": TransactionStatus.COMPLETED,
            "balance_after": new_balance,
            "admin_id": admin_id,
            "admin_note": admin_note,
        }
        transaction = crud.transaction.update(db, db_obj=transaction, obj_in=transaction_update)
        
        # Update user balance
        user.wallet_balance = new_balance
        
        # Commit changes
        db.commit()
        logger.info(f"Approved deposit of {amount} for user {transaction.user_id}. New balance: {new_balance}")
        
        return transaction
    
    @staticmethod
    def reject_deposit(
        db: Session,
        transaction_id: int,
        admin_id: Optional[int] = None,
        admin_note: Optional[str] = None,
    ) -> Transaction:
        """
        Reject a pending deposit transaction.
        
        Args:
            db: Database session
            transaction_id: Transaction ID
            admin_id: Admin who rejected the transaction
            admin_note: Note from admin
            
        Returns:
            Updated Transaction object
            
        Raises:
            WalletException: On validation errors
        """
        # Get the transaction
        transaction = crud.transaction.get(db, id=transaction_id)
        if not transaction:
            raise WalletException(f"Transaction with ID {transaction_id} not found")
        
        # Validate transaction type and status
        if transaction.type != TransactionType.DEPOSIT:
            raise WalletException(
                f"Transaction is of type {transaction.type.value}, expected DEPOSIT"
            )
        
        if transaction.status != TransactionStatus.PENDING:
            raise WalletException(
                f"Transaction is in state {transaction.status.value}, expected PENDING"
            )
        
        # Update transaction
        transaction_update = {
            "status": TransactionStatus.FAILED,
            "admin_id": admin_id,
            "admin_note": admin_note or "Deposit rejected by admin",
        }
        transaction = crud.transaction.update(db, db_obj=transaction, obj_in=transaction_update)
        
        # Commit changes
        db.commit()
        logger.info(f"Rejected deposit of {transaction.amount} for user {transaction.user_id}")
        
        return transaction
    
    @staticmethod
    def admin_adjustment(
        db: Session,
        user_id: int,
        amount: Decimal,
        description: str,
        admin_id: int,
        admin_note: Optional[str] = None,
    ) -> Transaction:
        """
        Make an admin adjustment to user's wallet.
        
        Args:
            db: Database session
            user_id: User ID
            amount: Amount to adjust (positive to add, negative to deduct)
            description: Transaction description
            admin_id: Admin who created the adjustment
            admin_note: Note from admin
            
        Returns:
            Created Transaction object
            
        Raises:
            WalletException: On validation errors
            InsufficientFundsException: If user has insufficient funds for a negative adjustment
        """
        # Validate amount
        if amount == 0:
            raise InvalidAmountException("Adjustment amount cannot be zero")
        
        # Get the user
        user = crud.user.get(db, id=user_id)
        if not user:
            raise WalletException(f"User with ID {user_id} not found")
        
        # Check if user has enough balance for negative adjustment
        if amount < 0 and user.wallet_balance < abs(amount):
            raise InsufficientFundsException(
                f"Insufficient funds: {user.wallet_balance} available, {abs(amount)} deduction requested"
            )
        
        # Calculate new balance
        current_balance = user.wallet_balance
        new_balance = current_balance + amount
        
        # Create transaction
        transaction_data = {
            "user_id": user_id,
            "amount": amount,
            "balance_after": new_balance,
            "type": TransactionType.ADMIN_ADJUSTMENT,
            "status": TransactionStatus.COMPLETED,
            "description": description,
            "admin_note": admin_note,
            "admin_id": admin_id,
        }
        
        # Create the transaction
        transaction = crud.transaction.create(db, obj_in=transaction_data)
        
        # Update user balance
        user.wallet_balance = new_balance
        
        # Commit changes
        db.commit()
        logger.info(f"Admin adjustment of {amount} for user {user_id} by admin {admin_id}. New balance: {new_balance}")
        
        return transaction
    
    @staticmethod
    def get_transaction_history(
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """
        Get transaction history and summary for a user.
        
        Args:
            db: Database session
            user_id: User ID
            skip: Number of records to skip for pagination
            limit: Maximum number of records to return
            
        Returns:
            Dictionary with transactions and summary
            
        Raises:
            WalletException: If user not found
        """
        # Get the user
        user = crud.user.get(db, id=user_id)
        if not user:
            raise WalletException(f"User with ID {user_id} not found")
        
        # Get transactions
        transactions = crud.transaction.get_by_user(db, user_id=user_id, skip=skip, limit=limit)
        
        # Get summary
        summary = crud.transaction.get_user_transactions_summary(db, user_id=user_id)
        
        return {
            "transactions": transactions,
            "summary": summary,
            "current_page": skip // limit + 1 if limit else 1,
            "total_count": len(transactions),  # This should be improved with proper count query
            "limit": limit,
        }


# Create a singleton instance
wallet_service = WalletService() 