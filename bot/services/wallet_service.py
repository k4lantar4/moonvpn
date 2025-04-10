"""
Service layer for handling wallet operations and transactions.

This service manages wallet balances and records financial transactions.
It provides methods for deposits, withdrawals, purchases, and balance checks.
"""

import logging
from typing import Optional, List, Dict, Any, Tuple
from decimal import Decimal
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

# Import models
from core.database.models.wallet import Wallet
from core.database.models.transaction import Transaction, TransactionType

# Import repositories
from core.database.repositories.wallet_repository import WalletRepository
from core.database.repositories.user_repository import UserRepository
from core.database.repositories.transaction_repository import TransactionRepository

# Import exceptions
from core.exceptions import NotFoundError, ServiceError, BusinessLogicError

logger = logging.getLogger(__name__)

class WalletService:
    """Service for managing user wallets and financial transactions."""

    def __init__(self):
        """Initialize repositories."""
        self.wallet_repo = WalletRepository()
        self.user_repo = UserRepository()
        self.transaction_repo = TransactionRepository()

    async def get_user_wallet(self, session: AsyncSession, user_id: int) -> Optional[Wallet]:
        """
        Get a user's wallet, creating one if it doesn't exist.
        
        Args:
            session: Database session
            user_id: User ID
            
        Returns:
            Wallet object
            
        Raises:
            NotFoundError: If user not found
            ServiceError: On database errors
        """
        try:
            # Check user exists
            user = await self.user_repo.get(session, id=user_id)
            if not user:
                raise NotFoundError(entity="User", identifier=user_id)
            
            # Get or create wallet
            wallet = await self.wallet_repo.get_by_user_id(session, user_id=user_id)
            if not wallet:
                logger.info(f"Creating new wallet for user {user_id}")
                wallet = await self.wallet_repo.create(
                    session, 
                    obj_in={"user_id": user_id, "balance": Decimal("0.00")}
                )
            
            return wallet
        except SQLAlchemyError as e:
            logger.exception(f"Database error getting wallet for user {user_id}: {e}")
            raise ServiceError(f"Failed to get wallet: {e}")

    async def get_balance(self, session: AsyncSession, user_id: int) -> Decimal:
        """
        Get a user's current wallet balance.
        
        Args:
            session: Database session
            user_id: User ID
            
        Returns:
            Current balance as Decimal
            
        Raises:
            NotFoundError: If user not found
            ServiceError: On database errors
        """
        wallet = await self.get_user_wallet(session, user_id)
        return wallet.balance

    async def record_transaction(
        self, 
        session: AsyncSession,
        *,
        user_id: int,
        amount: Decimal,
        transaction_type: TransactionType,
        reference_id: Optional[int] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[Transaction, Wallet]:
        """
        Record a financial transaction and update wallet balance.
        
        Args:
            session: Database session
            user_id: User ID
            amount: Transaction amount (positive for all transaction types)
            transaction_type: Type of transaction (DEPOSIT, PURCHASE, etc.)
            reference_id: Optional reference ID (payment_id, order_id)
            description: Optional description
            metadata: Optional additional data
            
        Returns:
            Tuple of (Transaction, updated Wallet)
            
        Raises:
            NotFoundError: If user or wallet not found
            BusinessLogicError: If insufficient funds
            ServiceError: On database errors
        """
        if amount <= 0:
            raise ValueError("Transaction amount must be positive")
        
        try:
            # Get or create wallet
            wallet = await self.get_user_wallet(session, user_id)
            
            # Calculate new balance based on transaction type
            old_balance = wallet.balance
            new_balance = old_balance
            
            if transaction_type == TransactionType.DEPOSIT:
                # Add to balance for deposits
                new_balance = old_balance + amount
            elif transaction_type in [TransactionType.WITHDRAW, TransactionType.PURCHASE]:
                # Check sufficient funds
                if old_balance < amount:
                    raise BusinessLogicError(
                        f"Insufficient funds: {old_balance} < {amount}"
                    )
                # Subtract from balance
                new_balance = old_balance - amount
            
            # Update wallet balance
            updated_wallet = await self.wallet_repo.update(
                session,
                db_obj=wallet,
                obj_in={"balance": new_balance}
            )
            
            # Create transaction record
            transaction = await self.transaction_repo.create(
                session,
                obj_in={
                    "user_id": user_id,
                    "amount": amount,
                    "type": transaction_type,
                    "reference_id": reference_id,
                    "description": description,
                    "balance_after": new_balance,
                    "metadata": metadata
                }
            )
            
            logger.info(
                f"Recorded {transaction_type.value} of {amount} for user {user_id}. "
                f"Balance: {old_balance} → {new_balance}"
            )
            
            return transaction, updated_wallet
            
        except SQLAlchemyError as e:
            logger.exception(f"Database error recording transaction for user {user_id}: {e}")
            raise ServiceError(f"Failed to record transaction: {e}")

    async def record_deposit(
        self, 
        session: AsyncSession,
        user_id: int,
        amount: Decimal,
        payment_id: int,
        description: str
    ) -> bool:
        """
        Record a deposit to a user's wallet.
        Called by PaymentService when confirming deposits.
        
        Args:
            session: Database session
            user_id: User ID
            amount: Deposit amount (positive)
            payment_id: Reference to the payment record
            description: Transaction description
            
        Returns:
            True on success
            
        Raises:
            ValueError: If amount <= 0
            NotFoundError: If user not found
            ServiceError: On database errors
        """
        try:
            await self.record_transaction(
                session,
                user_id=user_id,
                amount=amount,
                transaction_type=TransactionType.DEPOSIT,
                reference_id=payment_id,
                description=description
            )
            return True
        except (ValueError, NotFoundError, BusinessLogicError, ServiceError) as e:
            logger.error(f"Failed to record deposit: {e}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error recording deposit: {e}")
            raise ServiceError(f"Failed to record deposit: {e}")

    async def record_purchase(
        self, 
        session: AsyncSession,
        user_id: int,
        amount: Decimal,
        payment_id: int,
        description: str
    ) -> bool:
        """
        Record a purchase from a user's wallet.
        Called by PaymentService when processing wallet payments.
        
        Args:
            session: Database session
            user_id: User ID
            amount: Purchase amount (positive)
            payment_id: Reference to the payment record
            description: Transaction description
            
        Returns:
            True on success
            
        Raises:
            ValueError: If amount <= 0
            NotFoundError: If user not found
            BusinessLogicError: If insufficient funds
            ServiceError: On database errors
        """
        try:
            await self.record_transaction(
                session,
                user_id=user_id,
                amount=amount,
                transaction_type=TransactionType.PURCHASE,
                reference_id=payment_id,
                description=description
            )
            return True
        except (ValueError, NotFoundError, BusinessLogicError) as e:
            # Let these specific errors pass through
            logger.error(f"Failed to record purchase: {e}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error recording purchase: {e}")
            raise ServiceError(f"Failed to record purchase: {e}")

    async def get_user_transactions(
        self,
        session: AsyncSession,
        *,
        user_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> List[Transaction]:
        """
        Get a user's transaction history.
        
        Args:
            session: Database session
            user_id: User ID
            skip: Number of records to skip
            limit: Max records to return
            
        Returns:
            List of Transaction objects
            
        Raises:
            NotFoundError: If user not found
            ServiceError: On database errors
        """
        try:
            # Verify user exists
            user = await self.user_repo.get(session, id=user_id)
            if not user:
                raise NotFoundError(entity="User", identifier=user_id)
                
            return await self.transaction_repo.get_by_user_id(
                session, 
                user_id=user_id,
                skip=skip,
                limit=limit
            )
        except SQLAlchemyError as e:
            logger.exception(f"Database error getting transactions for user {user_id}: {e}")
            raise ServiceError(f"Failed to get transactions: {e}")

    async def get_user_wallet_with_transactions(
        self,
        session: AsyncSession,
        user_id: int,
        transaction_limit: int = 10
    ) -> Dict[str, Any]:
        """
        Get a user's wallet with recent transactions.
        Useful for wallet summary views.
        
        Args:
            session: Database session
            user_id: User ID
            transaction_limit: Max transactions to include
            
        Returns:
            Dict with wallet and transactions
            
        Raises:
            NotFoundError: If user not found
            ServiceError: On database errors
        """
        try:
            wallet = await self.get_user_wallet(session, user_id)
            transactions = await self.get_user_transactions(
                session, 
                user_id=user_id,
                limit=transaction_limit
            )
            
            return {
                "wallet": wallet,
                "transactions": transactions
            }
        except (NotFoundError, ServiceError) as e:
            # Let these pass through
            raise
        except Exception as e:
            logger.exception(f"Error getting wallet with transactions for user {user_id}: {e}")
            raise ServiceError(f"Failed to get wallet data: {e}")

    async def admin_adjust_balance(
        self,
        session: AsyncSession,
        *,
        user_id: int,
        admin_id: int,
        amount: Decimal,
        description: str
    ) -> Wallet:
        """
        Administrative adjustment of user balance.
        
        Args:
            session: Database session
            user_id: Target user ID
            admin_id: Admin user ID
            amount: Amount to adjust (positive for increase, negative for decrease)
            description: Reason for adjustment
            
        Returns:
            Updated wallet
            
        Raises:
            NotFoundError: If user not found
            BusinessLogicError: If insufficient funds for decrease
            ServiceError: On database errors
        """
        try:
            # Verify user exists
            user = await self.user_repo.get(session, id=user_id)
            if not user:
                raise NotFoundError(entity="User", identifier=user_id)
            
            # Admin user should exist
            admin = await self.user_repo.get(session, id=admin_id)
            if not admin:
                raise NotFoundError(entity="Admin", identifier=admin_id)
            
            # Get wallet
            wallet = await self.get_user_wallet(session, user_id)
            old_balance = wallet.balance
            
            # Determine transaction type and validate
            if amount > 0:
                transaction_type = TransactionType.DEPOSIT
                operation_amount = amount
            else:
                # For negative adjustments
                transaction_type = TransactionType.WITHDRAW
                operation_amount = abs(amount)  # Make positive for the transaction
                
                # Check sufficient funds for decrease
                if old_balance < operation_amount:
                    raise BusinessLogicError(
                        f"Insufficient funds for adjustment: {old_balance} < {operation_amount}"
                    )
            
            # Update wallet balance
            new_balance = old_balance + amount  # amount can be negative
            updated_wallet = await self.wallet_repo.update(
                session,
                db_obj=wallet,
                obj_in={"balance": new_balance}
            )
            
            # Record the transaction with admin metadata
            await self.transaction_repo.create(
                session,
                obj_in={
                    "user_id": user_id,
                    "amount": operation_amount,
                    "type": transaction_type,
                    "description": f"Admin adjustment: {description}",
                    "balance_after": new_balance,
                    "metadata": {
                        "admin_id": admin_id,
                        "admin_username": getattr(admin, "username", "unknown"),
                        "adjustment_type": "manual"
                    }
                }
            )
            
            logger.info(
                f"Admin {admin_id} adjusted user {user_id} balance by {amount}. "
                f"Balance: {old_balance} → {new_balance}. Reason: {description}"
            )
            
            return updated_wallet
            
        except (NotFoundError, BusinessLogicError) as e:
            # Let these pass through
            raise
        except Exception as e:
            logger.exception(f"Error in admin_adjust_balance for user {user_id}: {e}")
            raise ServiceError(f"Failed to adjust balance: {e}") 