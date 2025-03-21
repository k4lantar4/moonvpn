"""
Payment service for handling payment operations.

This module provides a high-level interface for payment processing,
verification, and management across different payment methods.
"""

import logging
from typing import Dict, Optional, Tuple, Any
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.core.config import settings
from app.core.models import Transaction, Wallet, Order
from app.core.schemas.payment import (
    PaymentRequest,
    PaymentResponse,
    PaymentMethod,
    TransactionStatus,
    TransactionType
)
from app.core.exceptions import (
    PaymentError,
    InsufficientBalanceError,
    TransactionNotFoundError,
    PaymentVerificationError,
    PaymentGatewayError,
    InvalidPaymentMethodError,
    PaymentAmountError,
    WalletLimitError
)

logger = logging.getLogger(__name__)

class PaymentService:
    """Service for handling payment operations."""
    
    def __init__(self, db: Session):
        self.db = db
        
    async def process_payment(
        self,
        payment_request: PaymentRequest
    ) -> PaymentResponse:
        """Process a payment request."""
        try:
            # Validate payment method
            if payment_request.payment_method not in PaymentMethod.__members__:
                raise InvalidPaymentMethodError(
                    f"Invalid payment method: {payment_request.payment_method}"
                )
            
            # Validate amount
            if payment_request.amount <= 0:
                raise PaymentAmountError("Payment amount must be greater than 0")
            
            # Process based on payment method
            if payment_request.payment_method == PaymentMethod.WALLET:
                return await self._process_wallet_payment(payment_request)
            elif payment_request.payment_method == PaymentMethod.CARD:
                return await self._process_card_payment(payment_request)
            elif payment_request.payment_method == PaymentMethod.ZARINPAL:
                return await self._process_zarinpal_payment(payment_request)
            else:
                raise InvalidPaymentMethodError(
                    f"Unsupported payment method: {payment_request.payment_method}"
                )
                
        except Exception as e:
            logger.error(f"Error processing payment: {str(e)}")
            raise PaymentError(str(e))
    
    async def verify_payment(
        self,
        payment_id: str,
        payment_method: str,
        verification_data: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify a payment
        
        Args:
            payment_id: Payment identifier
            payment_method: Payment method
            verification_data: Optional verification data
            
        Returns:
            Tuple of (is_verified, error_message)
        """
        try:
            # Get transaction
            transaction = self.db.query(Transaction).filter(
                Transaction.payment_id == payment_id,
                Transaction.status == TransactionStatus.PENDING
            ).first()
            
            if not transaction:
                raise TransactionNotFoundError(
                    "Transaction not found or already processed"
                )
            
            # Verify based on payment method
            if payment_method == PaymentMethod.WALLET:
                return await self._verify_wallet_payment(transaction)
            elif payment_method == PaymentMethod.CARD:
                return await self._verify_card_payment(
                    transaction,
                    verification_data
                )
            elif payment_method == PaymentMethod.ZARINPAL:
                return await self._verify_zarinpal_payment(
                    transaction,
                    verification_data
                )
            else:
                raise InvalidPaymentMethodError(
                    f"Unsupported payment method: {payment_method}"
                )
                
        except Exception as e:
            logger.error(f"Error verifying payment: {str(e)}")
            raise PaymentVerificationError(str(e))
    
    async def _verify_wallet_payment(
        self,
        transaction: Transaction
    ) -> Tuple[bool, Optional[str]]:
        """Verify wallet payment."""
        try:
            # Wallet payments are verified immediately
            transaction.status = TransactionStatus.COMPLETED
            transaction.completed_at = datetime.utcnow()
            self.db.commit()
            
            return True, None
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Wallet payment verification failed: {str(e)}")
            return False, str(e)
    
    async def _verify_card_payment(
        self,
        transaction: Transaction,
        verification_data: Optional[Dict[str, Any]]
    ) -> Tuple[bool, Optional[str]]:
        """Verify card payment."""
        try:
            if not verification_data:
                return False, "Missing verification data"
            
            # Initialize card payment processor
            from app.core.gateways.card import CardPaymentProcessor
            processor = CardPaymentProcessor()
            
            # Verify payment
            is_verified, error = await processor.verify_payment(
                transaction.id,
                verification_data
            )
            
            if is_verified:
                # Update transaction
                transaction.status = TransactionStatus.COMPLETED
                transaction.completed_at = datetime.utcnow()
                transaction.transaction_data.update({
                    "verification_data": verification_data
                })
                self.db.commit()
                
                return True, None
            else:
                return False, error
                
        except Exception as e:
            self.db.rollback()
            logger.error(f"Card payment verification failed: {str(e)}")
            return False, str(e)
    
    async def _verify_zarinpal_payment(
        self,
        transaction: Transaction,
        verification_data: Optional[Dict[str, Any]]
    ) -> Tuple[bool, Optional[str]]:
        """Verify ZarinPal payment."""
        try:
            if not verification_data:
                return False, "Missing verification data"
            
            # Initialize ZarinPal gateway
            from app.core.gateways.zarinpal import ZarinPalGateway
            gateway = ZarinPalGateway()
            
            # Verify payment
            is_verified, error = await gateway.verify_payment(
                transaction.payment_id,
                transaction.amount
            )
            
            if is_verified:
                # Update transaction
                transaction.status = TransactionStatus.COMPLETED
                transaction.completed_at = datetime.utcnow()
                transaction.transaction_data.update({
                    "verification_data": verification_data
                })
                self.db.commit()
                
                return True, None
            else:
                return False, error
                
        except Exception as e:
            self.db.rollback()
            logger.error(f"ZarinPal payment verification failed: {str(e)}")
            return False, str(e)

    async def _process_wallet_payment(
        self,
        payment_request: PaymentRequest
    ) -> PaymentResponse:
        """Process wallet payment."""
        try:
            # Get user's wallet
            wallet = self.db.query(Wallet).filter(
                Wallet.user_id == payment_request.user_id
            ).first()
            
            if not wallet:
                raise PaymentError("User wallet not found")
            
            # Check balance
            if wallet.balance < payment_request.amount:
                raise InsufficientBalanceError("Insufficient wallet balance")
            
            # Create transaction
            transaction = Transaction(
                user_id=payment_request.user_id,
                amount=payment_request.amount,
                type=TransactionType.PURCHASE,
                payment_method=PaymentMethod.WALLET,
                order_id=payment_request.order_id,
                status=TransactionStatus.PENDING
            )
            self.db.add(transaction)
            
            # Update wallet balance
            wallet.balance -= payment_request.amount
            
            # Commit changes
            self.db.commit()
            
            return PaymentResponse(
                success=True,
                message="Payment processed successfully",
                transaction_id=transaction.id
            )
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Wallet payment failed: {str(e)}")
            raise PaymentError(str(e))

    async def _process_card_payment(
        self,
        payment_request: PaymentRequest
    ) -> PaymentResponse:
        """Process card payment."""
        try:
            # Create transaction
            transaction = Transaction(
                user_id=payment_request.user_id,
                amount=payment_request.amount,
                type=TransactionType.PURCHASE,
                payment_method=PaymentMethod.CARD,
                order_id=payment_request.order_id,
                status=TransactionStatus.PENDING,
                transaction_data={
                    "payment_method": "card",
                    "callback_url": payment_request.callback_url
                }
            )
            self.db.add(transaction)
            self.db.commit()
            
            # Generate payment URL
            payment_url = f"{settings.PAYMENT_FORM_URL}/pay/{transaction.id}"
            
            # Update transaction with payment URL
            transaction.transaction_data["payment_url"] = payment_url
            self.db.commit()
            
            return PaymentResponse(
                success=True,
                message="Redirect to payment page",
                payment_url=payment_url,
                transaction_id=transaction.id
            )
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Card payment failed: {str(e)}")
            raise PaymentError(str(e))

    async def _process_zarinpal_payment(
        self,
        payment_request: PaymentRequest
    ) -> PaymentResponse:
        """Process ZarinPal payment."""
        try:
            # Create transaction
            transaction = Transaction(
                user_id=payment_request.user_id,
                amount=payment_request.amount,
                type=TransactionType.PURCHASE,
                payment_method=PaymentMethod.ZARINPAL,
                order_id=payment_request.order_id,
                status=TransactionStatus.PENDING,
                transaction_data={
                    "payment_method": "zarinpal",
                    "callback_url": payment_request.callback_url
                }
            )
            self.db.add(transaction)
            self.db.commit()
            
            # Initialize ZarinPal gateway
            from app.core.gateways.zarinpal import ZarinPalGateway
            gateway = ZarinPalGateway()
            
            # Create payment
            payment_id, payment_url = await gateway.create_payment(
                amount=payment_request.amount,
                description=f"Order {payment_request.order_id}",
                callback_url=payment_request.callback_url
            )
            
            if not payment_id:
                raise PaymentGatewayError("Failed to create ZarinPal payment")
            
            # Update transaction with payment ID
            transaction.payment_id = payment_id
            transaction.transaction_data["payment_url"] = payment_url
            self.db.commit()
            
            return PaymentResponse(
                success=True,
                message="Redirect to ZarinPal",
                payment_url=payment_url,
                transaction_id=transaction.id
            )
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"ZarinPal payment failed: {str(e)}")
            raise PaymentError(str(e))

    async def get_user_transactions(
        self,
        user_id: int,
        limit: int = 10,
        offset: int = 0
    ) -> List[TransactionSchema]:
        """Get all transactions for a user with pagination."""
        transactions = self.db.query(Transaction).filter(
            Transaction.user_id == user_id
        ).order_by(Transaction.created_at.desc()).offset(offset).limit(limit).all()
        return transactions

    async def get_user_wallet(self, user_id: int) -> WalletSchema:
        """Get user's wallet."""
        wallet = self.db.query(Wallet).filter(Wallet.user_id == user_id).first()
        if not wallet:
            # Create wallet if it doesn't exist
            wallet = Wallet(user_id=user_id, balance=0.0)
            self.db.add(wallet)
            self.db.commit()
        return wallet

    async def deposit_to_wallet(
        self,
        user_id: int,
        amount: float,
        payment_method: str
    ) -> PaymentResponse:
        """Deposit money to user's wallet."""
        if amount <= 0:
            raise PaymentError("Invalid deposit amount")

        wallet = await self.get_user_wallet(user_id)
        
        # Check wallet balance limits
        if wallet.balance + amount > settings.MAX_WALLET_BALANCE:
            raise PaymentError(f"Deposit amount exceeds maximum wallet balance of {settings.MAX_WALLET_BALANCE}")

        try:
            # Create a deposit transaction
            transaction = Transaction(
                user_id=user_id,
                amount=amount,
                type=TransactionType.DEPOSIT,
                payment_method=PaymentMethod(payment_method),
                status=TransactionStatus.PENDING,
                transaction_data={"payment_method": payment_method}
            )
            self.db.add(transaction)
            self.db.commit()

            # Process the deposit based on payment method
            if payment_method == PaymentMethod.ZARINPAL:
                return await self._process_zarinpal_payment(
                    user_id=user_id,
                    order_id=f"DEP{transaction.id}",
                    amount=amount,
                    callback_url=f"{settings.BASE_URL}/api/v1/payments/verify"
                )
            else:
                raise PaymentError("Unsupported deposit method")
        except Exception as e:
            self.db.rollback()
            raise PaymentError(f"Wallet deposit failed: {str(e)}")

    async def get_user_orders(
        self,
        user_id: int,
        limit: int = 10,
        offset: int = 0
    ) -> List[OrderSchema]:
        """Get all orders for a user with pagination."""
        orders = self.db.query(Order).filter(
            Order.user_id == user_id
        ).order_by(Order.created_at.desc()).offset(offset).limit(limit).all()
        return orders

    async def create_order(
        self,
        user_id: int,
        plan_id: int,
        amount: float
    ) -> OrderSchema:
        """Create a new order."""
        if amount <= 0:
            raise PaymentError("Invalid order amount")

        try:
            order = Order(
                user_id=user_id,
                plan_id=plan_id,
                amount=amount,
                status="pending"
            )
            self.db.add(order)
            self.db.commit()
            return order
        except Exception as e:
            self.db.rollback()
            raise PaymentError(f"Order creation failed: {str(e)}") 