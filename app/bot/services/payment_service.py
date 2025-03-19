"""
Payment Service for MoonVPN Telegram Bot.

This module handles payment processing for different payment methods
including credit card, wallet, bank transfer, and ZarinPal.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import HTTPException

from app.core.config import settings
from app.bot.utils.logger import setup_logger
from app.core.database.models import Transaction, Wallet, Order
from app.core.database.session import get_db

# Initialize logger
logger = setup_logger(__name__)

class PaymentService:
    """Service for handling payment processing."""
    
    async def process_payment(
        self,
        user_id: int,
        amount: float,
        payment_method: str,
        order_id: str,
        db: Any
    ) -> Dict[str, Any]:
        """Process payment for an order."""
        try:
            # Get user's wallet
            wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()
            
            # Process based on payment method
            if payment_method == "wallet":
                return await self._process_wallet_payment(wallet, amount, order_id, db)
            elif payment_method == "card":
                return await self._process_card_payment(user_id, amount, order_id, db)
            elif payment_method == "bank":
                return await self._process_bank_payment(user_id, amount, order_id, db)
            elif payment_method == "zarinpal":
                return await self._process_zarinpal_payment(user_id, amount, order_id, db)
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported payment method: {payment_method}"
                )
                
        except Exception as e:
            logger.error(f"Error processing payment: {str(e)}")
            raise
    
    async def _process_wallet_payment(
        self,
        wallet: Wallet,
        amount: float,
        order_id: str,
        db: Any
    ) -> Dict[str, Any]:
        """Process payment using user's wallet."""
        try:
            if not wallet or wallet.balance < amount:
                raise HTTPException(
                    status_code=400,
                    detail="Insufficient wallet balance"
                )
            
            # Create transaction
            transaction = Transaction(
                id=order_id,
                user_id=wallet.user_id,
                amount=amount,
                type="debit",
                status="completed",
                payment_method="wallet",
                created_at=datetime.utcnow()
            )
            
            # Update wallet balance
            wallet.balance -= amount
            
            db.add(transaction)
            db.commit()
            
            logger.info(f"Processed wallet payment for order {order_id}")
            return {
                "success": True,
                "transaction_id": transaction.id,
                "payment_method": "wallet"
            }
            
        except Exception as e:
            logger.error(f"Error processing wallet payment: {str(e)}")
            raise
    
    async def _process_card_payment(
        self,
        user_id: int,
        amount: float,
        order_id: str,
        db: Any
    ) -> Dict[str, Any]:
        """Process payment using credit card."""
        try:
            # TODO: Integrate with payment gateway
            # For now, simulate successful payment
            transaction = Transaction(
                id=order_id,
                user_id=user_id,
                amount=amount,
                type="debit",
                status="completed",
                payment_method="card",
                created_at=datetime.utcnow()
            )
            
            db.add(transaction)
            db.commit()
            
            logger.info(f"Processed card payment for order {order_id}")
            return {
                "success": True,
                "transaction_id": transaction.id,
                "payment_method": "card"
            }
            
        except Exception as e:
            logger.error(f"Error processing card payment: {str(e)}")
            raise
    
    async def _process_bank_payment(
        self,
        user_id: int,
        amount: float,
        order_id: str,
        db: Any
    ) -> Dict[str, Any]:
        """Process payment using bank transfer."""
        try:
            # Create pending transaction
            transaction = Transaction(
                id=order_id,
                user_id=user_id,
                amount=amount,
                type="debit",
                status="pending",
                payment_method="bank",
                created_at=datetime.utcnow()
            )
            
            db.add(transaction)
            db.commit()
            
            # Generate bank transfer details
            bank_details = {
                "bank_name": "Bank Melli Iran",
                "account_number": "1234567890",
                "account_holder": "MoonVPN",
                "description": f"Order {order_id}"
            }
            
            logger.info(f"Created bank transfer for order {order_id}")
            return {
                "success": True,
                "transaction_id": transaction.id,
                "payment_method": "bank",
                "bank_details": bank_details
            }
            
        except Exception as e:
            logger.error(f"Error processing bank payment: {str(e)}")
            raise
    
    async def _process_zarinpal_payment(
        self,
        user_id: int,
        amount: float,
        order_id: str,
        db: Any
    ) -> Dict[str, Any]:
        """Process payment using ZarinPal."""
        try:
            if not settings.ZARINPAL_MERCHANT:
                raise HTTPException(
                    status_code=500,
                    detail="ZarinPal merchant ID not configured"
                )
            
            # Create pending transaction
            transaction = Transaction(
                id=order_id,
                user_id=user_id,
                amount=amount,
                type="debit",
                status="pending",
                payment_method="zarinpal",
                created_at=datetime.utcnow()
            )
            
            db.add(transaction)
            db.commit()
            
            # Generate ZarinPal payment URL
            payment_url = f"https://www.zarinpal.com/pg/StartPay/{order_id}"
            
            logger.info(f"Created ZarinPal payment for order {order_id}")
            return {
                "success": True,
                "transaction_id": transaction.id,
                "payment_method": "zarinpal",
                "payment_url": payment_url
            }
            
        except Exception as e:
            logger.error(f"Error processing ZarinPal payment: {str(e)}")
            raise
    
    async def verify_payment(
        self,
        transaction_id: str,
        db: Any
    ) -> bool:
        """Verify payment status and update transaction."""
        try:
            transaction = db.query(Transaction).filter(
                Transaction.id == transaction_id
            ).first()
            
            if not transaction:
                raise HTTPException(
                    status_code=404,
                    detail="Transaction not found"
                )
            
            # TODO: Verify with payment gateway
            # For now, mark as completed
            transaction.status = "completed"
            db.commit()
            
            logger.info(f"Verified payment for transaction {transaction_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error verifying payment: {str(e)}")
            raise 