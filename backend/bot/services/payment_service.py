"""
Payment Service

This module provides services for managing payments.
"""

import logging
import uuid
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
from decimal import Decimal
import aiohttp
import asyncio

from core.config import settings
from core.utils.helpers import format_number
from core.database import get_db
from core.models.user import User
from core.models.transaction import Transaction
from core.models.subscription_plan import SubscriptionPlan

logger = logging.getLogger(__name__)

class PaymentService:
    """Service for managing payments."""
    
    def __init__(self):
        """Initialize payment service."""
        self.db = get_db()
    
    @staticmethod
    def get_user_transactions(user_id: int, limit: int = 10) -> List[Transaction]:
        """
        Get transactions for a user.
        
        Args:
            user_id: Telegram user ID
            limit: Maximum number of transactions to return
            
        Returns:
            List of Transaction objects
        """
        conn = None
        try:
            # Use custom query to get limited transactions with ordering
            transactions = Transaction.execute_query(
                f"SELECT * FROM transactions WHERE user_id = %s ORDER BY created_at DESC LIMIT %s",
                [user_id, limit]
            )
            
            if not transactions:
                return []
                
            # Convert to Transaction objects
            return [Transaction(**t) for t in transactions]
        except Exception as e:
            logger.error(f"Error getting user transactions: {e}")
            return []
    
    @staticmethod
    def create_transaction(
        user_id: int,
        amount: int,
        transaction_type: str = "purchase",
        payment_method: str = "wallet",
        description: str = None,
        metadata: Dict[str, Any] = None
    ) -> Optional[Transaction]:
        """
        Create a new transaction.
        
        Args:
            user_id: Telegram user ID
            amount: Transaction amount
            transaction_type: Transaction type (purchase, deposit, etc.)
            payment_method: Payment method (wallet, card, etc.)
            description: Transaction description
            metadata: Additional metadata
            
        Returns:
            Created Transaction object or None if failed
        """
        try:
            # Get user
            user = User.get_by_id(user_id)
            if not user:
                logger.error(f"User {user_id} not found")
                return None
            
            # Create transaction
            transaction = Transaction(
                user_id=user_id,
                amount=amount,
                type=transaction_type,
                status="pending",
                payment_method=payment_method,
                description=description,
                metadata=metadata or {}
            )
            transaction.save()
            
            return transaction
        except Exception as e:
            logger.error(f"Error creating transaction: {e}")
            return None
    
    @staticmethod
    def complete_transaction(transaction_id: int) -> bool:
        """
        Complete a transaction.
        
        Args:
            transaction_id: Transaction ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            transaction = Transaction.get_by_id(transaction_id)
            if not transaction:
                logger.error(f"Transaction {transaction_id} not found")
                return False
            
            # Check if already completed
            if transaction.status == "completed":
                return True
            
            # Update transaction status
            transaction.status = "completed"
            transaction.save()
            
            # Update user balance if it's a deposit
            if transaction.type == "deposit":
                user = User.get_by_id(transaction.user_id)
                if user:
                    user.balance += transaction.amount
                    user.save()
            
            return True
        except Exception as e:
            logger.error(f"Error completing transaction: {e}")
            return False
    
    @staticmethod
    def cancel_transaction(transaction_id: int) -> bool:
        """
        Cancel a transaction.
        
        Args:
            transaction_id: Transaction ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            transaction = Transaction.get_by_id(transaction_id)
            if not transaction:
                logger.error(f"Transaction {transaction_id} not found")
                return False
            
            # Check if already completed
            if transaction.status == "completed":
                logger.error(f"Cannot cancel completed transaction {transaction_id}")
                return False
            
            # Update transaction status
            transaction.status = "cancelled"
            transaction.save()
            
            return True
        except Exception as e:
            logger.error(f"Error cancelling transaction: {e}")
            return False
    
    @staticmethod
    def process_wallet_payment(user_id: int, amount: int, description: str = None) -> Dict[str, Any]:
        """
        Process a payment using wallet balance.
        
        Args:
            user_id: Telegram user ID
            amount: Payment amount
            description: Payment description
            
        Returns:
            Dictionary with payment result
        """
        try:
            # Get user
            user = User.get_by_id(user_id)
            if not user:
                logger.error(f"User {user_id} not found")
                return {"success": False, "error": "User not found"}
            
            # Check if user has enough balance
            if user.balance < amount:
                return {
                    "success": False, 
                    "error": "Insufficient balance",
                    "balance": user.balance,
                    "amount": amount,
                    "missing": amount - user.balance
                }
            
            # Create transaction
            transaction = Transaction(
                user_id=user_id,
                amount=amount,
                type="purchase",
                status="completed",
                payment_method="wallet",
                description=description or "Wallet payment"
            )
            transaction.save()
            
            # Update user balance
            user.balance -= amount
            user.save()
            
            return {
                "success": True,
                "transaction_id": transaction.id,
                "new_balance": user.balance
            }
        except Exception as e:
            logger.error(f"Error processing wallet payment: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def process_card_payment(
        user_id: int,
        amount: int,
        card_number: str = None,
        transaction_id: str = None,
        description: str = None
    ) -> Dict[str, Any]:
        """
        Process a card-to-card payment.
        
        Args:
            user_id: Telegram user ID
            amount: Payment amount
            card_number: Last 4 digits of card number
            transaction_id: Bank transaction ID
            description: Payment description
            
        Returns:
            Dictionary with payment result
        """
        try:
            # Get user
            user = User.get_by_id(user_id)
            if not user:
                logger.error(f"User {user_id} not found")
                return {"success": False, "error": "User not found"}
            
            # Create metadata
            metadata = {
                "card_number": card_number,
                "bank_transaction_id": transaction_id
            }
            
            # Create transaction
            transaction = Transaction(
                user_id=user_id,
                amount=amount,
                type="deposit",
                status="pending",
                payment_method="card",
                description=description or "Card payment",
                metadata=metadata
            )
            transaction.save()
            
            return {
                "success": True,
                "transaction_id": transaction.id,
                "status": "pending",
                "message": "Payment is pending verification"
            }
        except Exception as e:
            logger.error(f"Error processing card payment: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def verify_payment(transaction_id: int) -> bool:
        """
        Verify a pending payment.
        
        Args:
            transaction_id: Transaction ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            transaction = Transaction.get_by_id(transaction_id)
            if not transaction:
                logger.error(f"Transaction {transaction_id} not found")
                return False
            
            # Check if already completed
            if transaction.status == "completed":
                return True
            
            # Update transaction status
            transaction.status = "completed"
            transaction.save()
            
            # Update user balance
            user = User.get_by_id(transaction.user_id)
            if user and transaction.type == "deposit":
                user.balance += transaction.amount
                user.save()
            
            return True
        except Exception as e:
            logger.error(f"Error verifying payment: {e}")
            return False
    
    @staticmethod
    def reject_payment(transaction_id: int) -> bool:
        """
        Reject a pending payment.
        
        Args:
            transaction_id: Transaction ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            transaction = Transaction.get_by_id(transaction_id)
            if not transaction:
                logger.error(f"Transaction {transaction_id} not found")
                return False
            
            # Check if already completed
            if transaction.status == "completed":
                logger.error(f"Cannot reject completed transaction {transaction_id}")
                return False
            
            # Update transaction status
            transaction.status = "rejected"
            transaction.save()
            
            return True
        except Exception as e:
            logger.error(f"Error rejecting payment: {e}")
            return False
    
    @staticmethod
    def get_pending_payments(limit: int = 20) -> List[Transaction]:
        """
        Get pending payments.
        
        Args:
            limit: Maximum number of payments to return
            
        Returns:
            List of Transaction objects
        """
        try:
            # Use custom query to get limited pending transactions
            transactions = Transaction.execute_query(
                f"SELECT * FROM transactions WHERE status = 'pending' ORDER BY created_at DESC LIMIT %s",
                [limit]
            )
            
            if not transactions:
                return []
                
            # Convert to Transaction objects
            return [Transaction(**t) for t in transactions]
        except Exception as e:
            logger.error(f"Error getting pending payments: {e}")
            return []
    
    @staticmethod
    def get_payment_methods() -> List[Dict[str, Any]]:
        """
        Get available payment methods.
        
        Returns:
            List of payment method dictionaries
        """
        # This could be fetched from database in the future
        return [
            {
                "id": "wallet",
                "name": "Wallet",
                "description": "Pay using your wallet balance",
                "enabled": True
            },
            {
                "id": "card",
                "name": "Card to Card",
                "description": "Pay by transferring to our bank card",
                "enabled": True,
                "details": {
                    "card_number": "6037-9975-9874-3219",
                    "holder_name": "MoonVPN Company"
                }
            },
            {
                "id": "zarinpal",
                "name": "Zarinpal",
                "description": "Pay online using Zarinpal",
                "enabled": False
            }
        ]

    async def get_income_reports(self, period: str = 'daily') -> Dict[str, Any]:
        """Get income reports for the specified period."""
        try:
            now = datetime.now()
            
            if period == 'daily':
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = start_date + timedelta(days=1)
            elif period == 'weekly':
                start_date = now - timedelta(days=now.weekday())
                start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = start_date + timedelta(days=7)
            elif period == 'monthly':
                start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                if now.month == 12:
                    end_date = now.replace(year=now.year + 1, month=1, day=1)
                else:
                    end_date = now.replace(month=now.month + 1, day=1)
            else:
                return {
                    'total_income': 0,
                    'total_orders': 0,
                    'average_order': 0
                }
            
            # Get transactions for the period
            transactions = await self.db.transactions.find({
                'status': 'completed',
                'created_at': {
                    '$gte': start_date,
                    '$lt': end_date
                }
            }).to_list(length=None)
            
            # Calculate totals
            total_income = sum(t['amount'] for t in transactions)
            total_orders = len(transactions)
            average_order = total_income / total_orders if total_orders > 0 else 0
            
            # Get breakdown by plan
            plans = {}
            for t in transactions:
                plan = t.get('plan', 'Unknown')
                if plan not in plans:
                    plans[plan] = {'count': 0, 'amount': 0}
                plans[plan]['count'] += 1
                plans[plan]['amount'] += t['amount']
            
            result = {
                'total_income': total_income,
                'total_orders': total_orders,
                'average_order': average_order,
                'breakdown': [
                    {
                        'plan': plan,
                        'count': data['count'],
                        'amount': data['amount']
                    }
                    for plan, data in plans.items()
                ]
            }
            
            # Add period-specific data
            if period == 'daily':
                result['date'] = start_date.strftime('%Y-%m-%d')
            elif period == 'weekly':
                result['start_date'] = start_date.strftime('%Y-%m-%d')
                result['end_date'] = (end_date - timedelta(days=1)).strftime('%Y-%m-%d')
                
                # Add daily breakdown
                daily_stats = {}
                for t in transactions:
                    day = t['created_at'].strftime('%Y-%m-%d')
                    if day not in daily_stats:
                        daily_stats[day] = {'orders': 0, 'amount': 0}
                    daily_stats[day]['orders'] += 1
                    daily_stats[day]['amount'] += t['amount']
                
                result['daily_breakdown'] = [
                    {
                        'day': day,
                        'orders': stats['orders'],
                        'amount': stats['amount']
                    }
                    for day, stats in daily_stats.items()
                ]
            elif period == 'monthly':
                result['month'] = start_date.strftime('%B %Y')
                
                # Add weekly breakdown
                weekly_stats = {}
                for t in transactions:
                    week = (t['created_at'] - start_date).days // 7 + 1
                    if week not in weekly_stats:
                        weekly_stats[week] = {'orders': 0, 'amount': 0}
                    weekly_stats[week]['orders'] += 1
                    weekly_stats[week]['amount'] += t['amount']
                
                result['weekly_breakdown'] = [
                    {
                        'week': f'هفته {week}',
                        'orders': stats['orders'],
                        'amount': stats['amount']
                    }
                    for week, stats in weekly_stats.items()
                ]
            
            return result
            
        except Exception as e:
            logger.error("Error getting income reports: %s", str(e))
            return {
                'total_income': 0,
                'total_orders': 0,
                'average_order': 0
            }

    async def get_discount_codes(self) -> List[Dict[str, Any]]:
        """Get list of all discount codes."""
        try:
            codes = await self.db.discount_codes.find().to_list(length=None)
            return codes
        except Exception as e:
            logger.error("Error getting discount codes: %s", str(e))
            return []
    
    async def validate_discount_code(self, code: str) -> Tuple[bool, Any]:
        """Validate a discount code and return its details if valid."""
        try:
            discount = await self.db.discount_codes.find_one({'code': code})
            if not discount:
                return False, "کد تخفیف نامعتبر است"
            
            # Check if code is active
            if discount['status'] != 'active':
                return False, "این کد تخفیف غیرفعال شده است"
            
            # Check expiry date
            expiry = datetime.strptime(discount['expiry_date'], '%Y-%m-%d')
            if expiry < datetime.now():
                return False, "این کد تخفیف منقضی شده است"
            
            # Check usage limit
            if discount['max_uses'] and discount['current_uses'] >= discount['max_uses']:
                return False, "این کد تخفیف به حداکثر تعداد استفاده رسیده است"
            
            return True, discount
            
        except Exception as e:
            logger.error("Error validating discount code: %s", str(e))
            return False, "خطا در بررسی کد تخفیف"
    
    async def use_discount_code(self, code: str) -> bool:
        """Increment usage count for a discount code."""
        try:
            result = await self.db.discount_codes.update_one(
                {'code': code},
                {'$inc': {'current_uses': 1}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error("Error using discount code: %s", str(e))
            return False

    async def create_discount_code(
        self,
        code: str,
        discount_type: str,
        value: float,
        description: str,
        expiry_date: str,
        max_uses: Optional[int] = None
    ) -> Tuple[bool, Any]:
        """Create a new discount code."""
        try:
            # Validate expiry date
            expiry = datetime.strptime(expiry_date, '%Y-%m-%d')
            if expiry < datetime.now():
                return False, "تاریخ انقضا نمی‌تواند در گذشته باشد"
            
            # Validate discount value
            if discount_type == 'percent' and (value <= 0 or value > 100):
                return False, "درصد تخفیف باید بین 1 تا 100 باشد"
            elif discount_type == 'fixed' and value <= 0:
                return False, "مبلغ تخفیف باید بزرگتر از صفر باشد"
            
            # Check if code already exists
            existing_code = await self.db.discount_codes.find_one({'code': code})
            if existing_code:
                return False, "این کد تخفیف قبلاً ثبت شده است"
            
            # Create discount code
            discount_data = {
                'code': code,
                'type': discount_type,
                'value': value,
                'description': description,
                'expiry_date': expiry_date,
                'max_uses': max_uses,
                'current_uses': 0,
                'status': 'active',
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            await self.db.discount_codes.insert_one(discount_data)
            return True, discount_data
            
        except ValueError as e:
            logger.error("Error creating discount code: %s", str(e))
            return False, "خطا در ایجاد کد تخفیف"

    async def create_transaction(
        self,
        user_id: int,
        amount: int,
        plan: str,
        discount_code: Optional[str] = None
    ) -> Tuple[bool, Any]:
        """Create a new transaction."""
        try:
            # Apply discount if code is provided
            final_amount = amount
            if discount_code:
                success, discount = await self.validate_discount_code(discount_code)
                if success:
                    if discount['type'] == 'percent':
                        discount_amount = int(amount * discount['value'] / 100)
                    else:
                        discount_amount = int(discount['value'])
                    final_amount = max(0, amount - discount_amount)
                    
                    # Use the discount code
                    await self.use_discount_code(discount_code)
            
            # Create transaction
            transaction = {
                'user_id': user_id,
                'amount': amount,
                'final_amount': final_amount,
                'plan': plan,
                'discount_code': discount_code,
                'status': 'pending',
                'created_at': datetime.now()
            }
            
            result = await self.db.transactions.insert_one(transaction)
            transaction['_id'] = result.inserted_id
            
            return True, transaction
            
        except Exception as e:
            logger.error("Error creating transaction: %s", str(e))
            return False, "خطا در ایجاد تراکنش"
    
    async def complete_transaction(self, transaction_id: str) -> bool:
        """Mark a transaction as completed."""
        try:
            result = await self.db.transactions.update_one(
                {'_id': transaction_id},
                {
                    '$set': {
                        'status': 'completed',
                        'completed_at': datetime.now()
                    }
                }
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error("Error completing transaction: %s", str(e))
            return False
    
    async def cancel_transaction(self, transaction_id: str) -> bool:
        """Mark a transaction as cancelled."""
        try:
            result = await self.db.transactions.update_one(
                {'_id': transaction_id},
                {
                    '$set': {
                        'status': 'cancelled',
                        'cancelled_at': datetime.now()
                    }
                }
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error("Error cancelling transaction: %s", str(e))
            return False 