"""
Payment service for MoonVPN.

This module handles payment processing for different payment methods
including ZarinPal, wallet, bank transfer, and credit card.
"""

import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.database.models.payment import (
    Transaction,
    TransactionStatus,
    TransactionType,
    PaymentMethod,
    Wallet,
    Order
)
from app.core.schemas.payment import (
    PaymentResponse,
    Transaction as TransactionSchema,
    Wallet as WalletSchema,
    Order as OrderSchema
)
from app.core.config import settings
from app.core.exceptions import PaymentError, InsufficientBalanceError, TransactionNotFoundError

logger = logging.getLogger(__name__)

class PaymentService:
    """Service for handling payment operations."""

    def __init__(self, db: Session):
        self.db = db

    @retry(
        stop=stop_after_attempt(settings.MAX_RETRY_ATTEMPTS),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def process_payment(
        self,
        user_id: int,
        order_id: str,
        amount: float,
        payment_method: PaymentMethod,
        callback_url: str
    ) -> PaymentResponse:
        """Process a payment based on the selected payment method."""
        try:
            # Validate amount
            if amount <= 0:
                raise PaymentError("Invalid payment amount")

            # Check for existing transaction
            existing_transaction = self.db.query(Transaction).filter(
                Transaction.order_id == order_id,
                Transaction.status.in_([TransactionStatus.PENDING, TransactionStatus.COMPLETED])
            ).first()
            
            if existing_transaction:
                if existing_transaction.status == TransactionStatus.COMPLETED:
                    return PaymentResponse(
                        success=True,
                        message="Payment already completed",
                        transaction_id=existing_transaction.id
                    )
                return PaymentResponse(
                    success=True,
                    message="Payment already initiated",
                    transaction_id=existing_transaction.id,
                    payment_url=existing_transaction.transaction_data.get("payment_url") if existing_transaction.transaction_data else None
                )

            if payment_method == PaymentMethod.WALLET:
                return await self._process_wallet_payment(user_id, order_id, amount)
            elif payment_method == PaymentMethod.CARD:
                return await self._process_card_payment(user_id, order_id, amount, callback_url)
            elif payment_method == PaymentMethod.BANK:
                return await self._process_bank_payment(user_id, order_id, amount)
            elif payment_method == PaymentMethod.ZARINPAL:
                return await self._process_zarinpal_payment(user_id, order_id, amount, callback_url)
            else:
                raise PaymentError("Unsupported payment method")
        except Exception as e:
            logger.error(f"Payment processing error: {str(e)}")
            raise PaymentError(f"Payment processing failed: {str(e)}")

    async def _process_wallet_payment(
        self,
        user_id: int,
        order_id: str,
        amount: float
    ) -> PaymentResponse:
        """Process payment using user's wallet."""
        wallet = self.db.query(Wallet).filter(Wallet.user_id == user_id).first()
        if not wallet or wallet.balance < amount:
            raise InsufficientBalanceError("Insufficient wallet balance")

        try:
            transaction = Transaction(
                user_id=user_id,
                amount=amount,
                type=TransactionType.PURCHASE,
                payment_method=PaymentMethod.WALLET,
                order_id=order_id,
                status=TransactionStatus.COMPLETED,
                transaction_data={"payment_method": "wallet"}
            )
            self.db.add(transaction)
            
            wallet.balance -= amount
            self.db.commit()

            return PaymentResponse(
                success=True,
                message="Payment processed successfully",
                transaction_id=transaction.id
            )
        except Exception as e:
            self.db.rollback()
            raise PaymentError(f"Wallet payment failed: {str(e)}")

    async def _process_card_payment(
        self,
        user_id: int,
        order_id: str,
        amount: float,
        callback_url: str
    ) -> PaymentResponse:
        """Process payment using credit card."""
        try:
            transaction = Transaction(
                user_id=user_id,
                amount=amount,
                type=TransactionType.PURCHASE,
                payment_method=PaymentMethod.CARD,
                order_id=order_id,
                status=TransactionStatus.PENDING,
                transaction_data={
                    "payment_method": "card",
                    "callback_url": callback_url
                }
            )
            self.db.add(transaction)
            self.db.commit()

            # Here you would integrate with your credit card payment gateway
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
            raise PaymentError(f"Card payment failed: {str(e)}")

    async def _process_bank_payment(
        self,
        user_id: int,
        order_id: str,
        amount: float
    ) -> PaymentResponse:
        """Process payment using bank transfer."""
        try:
            transaction = Transaction(
                user_id=user_id,
                amount=amount,
                type=TransactionType.PURCHASE,
                payment_method=PaymentMethod.BANK,
                order_id=order_id,
                status=TransactionStatus.PENDING,
                transaction_data={
                    "payment_method": "bank",
                    "bank_details": {
                        "account_number": settings.BANK_ACCOUNT,
                        "bank_name": settings.BANK_NAME,
                        "account_holder": settings.BANK_HOLDER,
                        "amount": amount,
                        "reference": f"TRX{transaction.id}"
                    }
                }
            )
            self.db.add(transaction)
            self.db.commit()

            return PaymentResponse(
                success=True,
                message="Bank transfer details",
                transaction_id=transaction.id,
                transaction_data=transaction.transaction_data["bank_details"]
            )
        except Exception as e:
            self.db.rollback()
            raise PaymentError(f"Bank payment failed: {str(e)}")

    async def _process_zarinpal_payment(
        self,
        user_id: int,
        order_id: str,
        amount: float,
        callback_url: str
    ) -> PaymentResponse:
        """Process payment using ZarinPal."""
        try:
            transaction = Transaction(
                user_id=user_id,
                amount=amount,
                type=TransactionType.PURCHASE,
                payment_method=PaymentMethod.ZARINPAL,
                order_id=order_id,
                status=TransactionStatus.PENDING,
                transaction_data={
                    "payment_method": "zarinpal",
                    "callback_url": callback_url
                }
            )
            self.db.add(transaction)
            self.db.commit()

            # Here you would integrate with ZarinPal API
            # For now, we'll return a mock payment URL
            payment_url = f"https://zarinpal.com/pg/StartPay/{transaction.id}"
            authority = str(transaction.id)  # Mock authority
            
            # Update transaction with payment URL and authority
            transaction.transaction_data["payment_url"] = payment_url
            transaction.authority = authority
            self.db.commit()

            return PaymentResponse(
                success=True,
                message="Redirect to ZarinPal payment page",
                payment_url=payment_url,
                transaction_id=transaction.id,
                authority=authority
            )
        except Exception as e:
            self.db.rollback()
            raise PaymentError(f"ZarinPal payment failed: {str(e)}")

    @retry(
        stop=stop_after_attempt(settings.MAX_RETRY_ATTEMPTS),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def verify_payment(
        self,
        authority: str,
        status: str,
        ref_id: Optional[str] = None
    ) -> PaymentResponse:
        """Verify payment with the payment gateway."""
        transaction = self.db.query(Transaction).filter(
            Transaction.authority == authority
        ).first()
        
        if not transaction:
            raise TransactionNotFoundError("Transaction not found")

        try:
            if status == "OK":
                transaction.status = TransactionStatus.COMPLETED
                transaction.ref_id = ref_id
                transaction.transaction_data["verification_status"] = "success"
                transaction.transaction_data["ref_id"] = ref_id
                self.db.commit()

                return PaymentResponse(
                    success=True,
                    message="Payment verified successfully",
                    transaction_id=transaction.id
                )
            else:
                transaction.status = TransactionStatus.FAILED
                transaction.transaction_data["verification_status"] = "failed"
                transaction.transaction_data["error_message"] = status
                self.db.commit()

                return PaymentResponse(
                    success=False,
                    message="Payment verification failed",
                    transaction_id=transaction.id
                )
        except Exception as e:
            self.db.rollback()
            raise PaymentError(f"Payment verification failed: {str(e)}")

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