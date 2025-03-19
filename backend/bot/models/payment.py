"""
MoonVPN Telegram Bot - Payment Model

This module provides the Payment model for managing payment transactions.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

from core.database import execute_query, execute_insert, execute_update, execute_delete, cache_get, cache_set, cache_delete

logger = logging.getLogger(__name__)

class Payment:
    """Payment model for managing payment transactions."""
    
    # Payment status constants
    STATUS_PENDING = 'pending'
    STATUS_COMPLETED = 'completed'
    STATUS_FAILED = 'failed'
    STATUS_REFUNDED = 'refunded'
    STATUS_CANCELLED = 'cancelled'
    
    # Payment types
    TYPE_ACCOUNT_PURCHASE = 'account_purchase'
    TYPE_ACCOUNT_RENEWAL = 'account_renewal'
    TYPE_WALLET_DEPOSIT = 'wallet_deposit'
    TYPE_REFUND = 'refund'
    
    # Payment methods
    METHOD_CARD = 'card'
    METHOD_ZARINPAL = 'zarinpal'
    METHOD_WALLET = 'wallet'
    METHOD_ADMIN = 'admin'
    
    def __init__(self, payment_data: Dict[str, Any]):
        """
        Initialize a payment object.
        
        Args:
            payment_data (Dict[str, Any]): Payment data from database
        """
        self.id = payment_data.get('id')
        self.user_id = payment_data.get('user_id')
        self.amount = float(payment_data.get('amount', 0))
        self.description = payment_data.get('description')
        self.status = payment_data.get('status', self.STATUS_PENDING)
        self.payment_type = payment_data.get('payment_type')
        self.payment_method = payment_data.get('payment_method')
        self.transaction_id = payment_data.get('transaction_id')
        self.reference_id = payment_data.get('reference_id')
        self.vpn_account_id = payment_data.get('vpn_account_id')
        self.discount_code = payment_data.get('discount_code')
        self.discount_amount = float(payment_data.get('discount_amount', 0))
        self.admin_id = payment_data.get('admin_id')
        self.receipt_image = payment_data.get('receipt_image')
        self.extra_data = payment_data.get('extra_data', {})
        self.created_at = payment_data.get('created_at')
        self.updated_at = payment_data.get('updated_at')
        
        # Additional data from joins
        self.user_telegram_id = payment_data.get('user_telegram_id')
        self.user_username = payment_data.get('user_username')
        self.user_first_name = payment_data.get('user_first_name')
        self.admin_telegram_id = payment_data.get('admin_telegram_id')
        self.admin_username = payment_data.get('admin_username')
        
    @staticmethod
    def get_by_id(payment_id: int) -> Optional['Payment']:
        """
        Get a payment by ID.
        
        Args:
            payment_id (int): Payment ID
            
        Returns:
            Optional[Payment]: Payment object or None if not found
        """
        # Try to get from cache first
        cached_payment = cache_get(f"payment:id:{payment_id}")
        if cached_payment:
            return Payment(cached_payment)
        
        # Get from database with user info
        query = """
            SELECT p.*, u.telegram_id as user_telegram_id, u.username as user_username, 
                  u.first_name as user_first_name, a.telegram_id as admin_telegram_id,
                  a.username as admin_username
            FROM payments p
            LEFT JOIN users u ON p.user_id = u.id
            LEFT JOIN users a ON p.admin_id = a.id
            WHERE p.id = %s
        """
        result = execute_query(query, (payment_id,), fetch="one")
        
        if result:
            # Cache payment data
            cache_set(f"payment:id:{payment_id}", dict(result), 300)  # Cache for 5 minutes
            return Payment(result)
            
        return None
        
    @staticmethod
    def get_by_transaction_id(transaction_id: str) -> Optional['Payment']:
        """
        Get a payment by transaction ID.
        
        Args:
            transaction_id (str): Transaction ID
            
        Returns:
            Optional[Payment]: Payment object or None if not found
        """
        # Try to get from cache first
        cached_payment = cache_get(f"payment:transaction_id:{transaction_id}")
        if cached_payment:
            return Payment(cached_payment)
        
        # Get from database
        query = """
            SELECT p.*, u.telegram_id as user_telegram_id, u.username as user_username, 
                  u.first_name as user_first_name, a.telegram_id as admin_telegram_id,
                  a.username as admin_username
            FROM payments p
            LEFT JOIN users u ON p.user_id = u.id
            LEFT JOIN users a ON p.admin_id = a.id
            WHERE p.transaction_id = %s
        """
        result = execute_query(query, (transaction_id,), fetch="one")
        
        if result:
            # Cache payment data
            cache_set(f"payment:transaction_id:{transaction_id}", dict(result), 300)
            return Payment(result)
            
        return None
        
    @staticmethod
    def get_by_reference_id(reference_id: str) -> Optional['Payment']:
        """
        Get a payment by reference ID.
        
        Args:
            reference_id (str): Reference ID
            
        Returns:
            Optional[Payment]: Payment object or None if not found
        """
        query = """
            SELECT p.*, u.telegram_id as user_telegram_id, u.username as user_username, 
                  u.first_name as user_first_name, a.telegram_id as admin_telegram_id,
                  a.username as admin_username
            FROM payments p
            LEFT JOIN users u ON p.user_id = u.id
            LEFT JOIN users a ON p.admin_id = a.id
            WHERE p.reference_id = %s
        """
        result = execute_query(query, (reference_id,), fetch="one")
        
        if result:
            return Payment(result)
            
        return None
        
    @staticmethod
    def get_by_user_id(user_id: int, limit: int = 10, offset: int = 0, 
                      status: Optional[str] = None) -> List['Payment']:
        """
        Get payments by user ID.
        
        Args:
            user_id (int): User ID
            limit (int, optional): Limit results. Defaults to 10.
            offset (int, optional): Offset results. Defaults to 0.
            status (Optional[str], optional): Filter by payment status. Defaults to None.
            
        Returns:
            List[Payment]: List of payment objects
        """
        if status:
            query = """
                SELECT p.*, u.telegram_id as user_telegram_id, u.username as user_username, 
                      u.first_name as user_first_name, a.telegram_id as admin_telegram_id,
                      a.username as admin_username
                FROM payments p
                LEFT JOIN users u ON p.user_id = u.id
                LEFT JOIN users a ON p.admin_id = a.id
                WHERE p.user_id = %s AND p.status = %s
                ORDER BY p.created_at DESC
                LIMIT %s OFFSET %s
            """
            results = execute_query(query, (user_id, status, limit, offset))
        else:
            query = """
                SELECT p.*, u.telegram_id as user_telegram_id, u.username as user_username, 
                      u.first_name as user_first_name, a.telegram_id as admin_telegram_id,
                      a.username as admin_username
                FROM payments p
                LEFT JOIN users u ON p.user_id = u.id
                LEFT JOIN users a ON p.admin_id = a.id
                WHERE p.user_id = %s
                ORDER BY p.created_at DESC
                LIMIT %s OFFSET %s
            """
            results = execute_query(query, (user_id, limit, offset))
        
        return [Payment(result) for result in results]
        
    @staticmethod
    def get_by_vpn_account_id(vpn_account_id: int) -> List['Payment']:
        """
        Get payments by VPN account ID.
        
        Args:
            vpn_account_id (int): VPN account ID
            
        Returns:
            List[Payment]: List of payment objects
        """
        query = """
            SELECT p.*, u.telegram_id as user_telegram_id, u.username as user_username, 
                  u.first_name as user_first_name, a.telegram_id as admin_telegram_id,
                  a.username as admin_username
            FROM payments p
            LEFT JOIN users u ON p.user_id = u.id
            LEFT JOIN users a ON p.admin_id = a.id
            WHERE p.vpn_account_id = %s
            ORDER BY p.created_at DESC
        """
        results = execute_query(query, (vpn_account_id,))
        
        return [Payment(result) for result in results]
        
    @staticmethod
    def get_pending_card_payments() -> List['Payment']:
        """
        Get all pending card payments.
        
        Returns:
            List[Payment]: List of pending card payment objects
        """
        query = """
            SELECT p.*, u.telegram_id as user_telegram_id, u.username as user_username, 
                  u.first_name as user_first_name, a.telegram_id as admin_telegram_id,
                  a.username as admin_username
            FROM payments p
            LEFT JOIN users u ON p.user_id = u.id
            LEFT JOIN users a ON p.admin_id = a.id
            WHERE p.status = %s AND p.payment_method = %s
            ORDER BY p.created_at ASC
        """
        results = execute_query(query, (Payment.STATUS_PENDING, Payment.METHOD_CARD))
        
        return [Payment(result) for result in results]
        
    @staticmethod
    def create(user_id: int, amount: float, description: str, payment_type: str,
             payment_method: str, vpn_account_id: Optional[int] = None,
             discount_code: Optional[str] = None, discount_amount: float = 0,
             admin_id: Optional[int] = None, extra_data: Optional[Dict] = None) -> Optional['Payment']:
        """
        Create a new payment.
        
        Args:
            user_id (int): User ID
            amount (float): Payment amount
            description (str): Payment description
            payment_type (str): Payment type (account_purchase, account_renewal, wallet_deposit, refund)
            payment_method (str): Payment method (card, zarinpal, wallet, admin)
            vpn_account_id (Optional[int], optional): VPN account ID. Defaults to None.
            discount_code (Optional[str], optional): Discount code. Defaults to None.
            discount_amount (float, optional): Discount amount. Defaults to 0.
            admin_id (Optional[int], optional): Admin user ID for admin payments. Defaults to None.
            extra_data (Optional[Dict], optional): Extra payment data. Defaults to None.
            
        Returns:
            Optional[Payment]: Payment object or None if creation failed
        """
        # Generate unique transaction ID
        transaction_id = str(uuid.uuid4())
        
        # Insert into database
        query = """
            INSERT INTO payments (
                user_id, amount, description, status, payment_type,
                payment_method, transaction_id, vpn_account_id, discount_code,
                discount_amount, admin_id, extra_data
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """
        
        # Set initial status
        status = Payment.STATUS_PENDING
        if payment_method == Payment.METHOD_WALLET or payment_method == Payment.METHOD_ADMIN:
            status = Payment.STATUS_COMPLETED
        
        payment_id = execute_insert(query, (
            user_id, amount, description, status, payment_type,
            payment_method, transaction_id, vpn_account_id, discount_code,
            discount_amount, admin_id, extra_data
        ))
        
        if payment_id:
            # Return the created payment
            return Payment.get_by_id(payment_id)
            
        return None
        
    def save(self) -> bool:
        """
        Save payment changes to the database.
        
        Returns:
            bool: True if changes were saved, False otherwise
        """
        if not self.id:
            return False
            
        query = """
            UPDATE payments SET
                user_id = %s,
                amount = %s,
                description = %s,
                status = %s,
                payment_type = %s,
                payment_method = %s,
                transaction_id = %s,
                reference_id = %s,
                vpn_account_id = %s,
                discount_code = %s,
                discount_amount = %s,
                admin_id = %s,
                receipt_image = %s,
                extra_data = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        
        success = execute_update(query, (
            self.user_id,
            self.amount,
            self.description,
            self.status,
            self.payment_type,
            self.payment_method,
            self.transaction_id,
            self.reference_id,
            self.vpn_account_id,
            self.discount_code,
            self.discount_amount,
            self.admin_id,
            self.receipt_image,
            self.extra_data,
            self.id
        ))
        
        if success:
            # Clear cache
            cache_delete(f"payment:id:{self.id}")
            if self.transaction_id:
                cache_delete(f"payment:transaction_id:{self.transaction_id}")
            
        return success
        
    def delete(self) -> bool:
        """
        Delete payment from database.
        
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        if not self.id:
            return False
            
        # Delete from database
        query = "DELETE FROM payments WHERE id = %s"
        success = execute_delete(query, (self.id,))
        
        if success:
            # Clear cache
            cache_delete(f"payment:id:{self.id}")
            if self.transaction_id:
                cache_delete(f"payment:transaction_id:{self.transaction_id}")
            
        return success
        
    def complete(self, reference_id: Optional[str] = None) -> bool:
        """
        Mark payment as completed.
        
        Args:
            reference_id (Optional[str], optional): Reference ID for completed payment. Defaults to None.
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        self.status = self.STATUS_COMPLETED
        if reference_id:
            self.reference_id = reference_id
        
        # Update VPN account if this is an account purchase/renewal
        if self.status == self.STATUS_COMPLETED and self.vpn_account_id:
            if self.payment_type == self.TYPE_ACCOUNT_PURCHASE:
                # Activate the account
                from models.vpn_account import VPNAccount
                account = VPNAccount.get_by_id(self.vpn_account_id)
                if account:
                    account.activate()
            elif self.payment_type == self.TYPE_ACCOUNT_RENEWAL:
                # Renew the account
                from models.vpn_account import VPNAccount
                account = VPNAccount.get_by_id(self.vpn_account_id)
                if account:
                    account.renew()
        
        # Add amount to user wallet if this is a wallet deposit
        if self.status == self.STATUS_COMPLETED and self.payment_type == self.TYPE_WALLET_DEPOSIT:
            from models.user import User
            user = User.get_by_id(self.user_id)
            if user:
                user.add_to_wallet(self.amount, f"Wallet deposit: {self.description}")
        
        return self.save()
        
    def fail(self, reason: Optional[str] = None) -> bool:
        """
        Mark payment as failed.
        
        Args:
            reason (Optional[str], optional): Failure reason. Defaults to None.
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        self.status = self.STATUS_FAILED
        if reason:
            if not self.extra_data:
                self.extra_data = {}
            self.extra_data['failure_reason'] = reason
        
        return self.save()
        
    def cancel(self, reason: Optional[str] = None) -> bool:
        """
        Mark payment as cancelled.
        
        Args:
            reason (Optional[str], optional): Cancellation reason. Defaults to None.
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        self.status = self.STATUS_CANCELLED
        if reason:
            if not self.extra_data:
                self.extra_data = {}
            self.extra_data['cancellation_reason'] = reason
        
        return self.save()
        
    def refund(self, amount: Optional[float] = None, reason: Optional[str] = None,
              admin_id: Optional[int] = None) -> bool:
        """
        Mark payment as refunded and create refund record.
        
        Args:
            amount (Optional[float], optional): Refund amount. Defaults to None (full amount).
            reason (Optional[str], optional): Refund reason. Defaults to None.
            admin_id (Optional[int], optional): Admin ID who processed the refund. Defaults to None.
            
        Returns:
            bool: True if refund was successful, False otherwise
        """
        if self.status != self.STATUS_COMPLETED:
            logger.error(f"Cannot refund payment {self.id} with status {self.status}")
            return False
        
        refund_amount = amount if amount is not None else self.amount
        if refund_amount <= 0 or refund_amount > self.amount:
            logger.error(f"Invalid refund amount: {refund_amount}")
            return False
        
        # Mark original payment as refunded
        self.status = self.STATUS_REFUNDED
        if reason:
            if not self.extra_data:
                self.extra_data = {}
            self.extra_data['refund_reason'] = reason
        
        # Create refund payment
        from models.user import User
        user = User.get_by_id(self.user_id)
        if not user:
            logger.error(f"User {self.user_id} not found for refund")
            return False
        
        refund_description = f"Refund for payment #{self.id}"
        if reason:
            refund_description += f": {reason}"
        
        # Create refund transaction
        Payment.create(
            user_id=self.user_id,
            amount=refund_amount,
            description=refund_description,
            payment_type=Payment.TYPE_REFUND,
            payment_method=Payment.METHOD_ADMIN,
            admin_id=admin_id or self.admin_id,
            extra_data={'original_payment_id': self.id}
        )
        
        # Add refund to user wallet
        user.add_to_wallet(refund_amount, refund_description)
        
        return self.save()
        
    def get_user(self):
        """
        Get the user associated with this payment.
        
        Returns:
            Optional[User]: User object or None if not found
        """
        if not self.user_id:
            return None
            
        from models.user import User
        return User.get_by_id(self.user_id)
        
    def get_vpn_account(self):
        """
        Get the VPN account associated with this payment.
        
        Returns:
            Optional[VPNAccount]: VPN account object or None if not found
        """
        if not self.vpn_account_id:
            return None
            
        from models.vpn_account import VPNAccount
        return VPNAccount.get_by_id(self.vpn_account_id)
        
    def get_admin(self):
        """
        Get the admin associated with this payment.
        
        Returns:
            Optional[User]: Admin user object or None if not found
        """
        if not self.admin_id:
            return None
            
        from models.user import User
        return User.get_by_id(self.admin_id)
        
    def get_discount(self):
        """
        Get the discount associated with this payment.
        
        Returns:
            Optional[DiscountCode]: Discount code object or None if not found
        """
        if not self.discount_code:
            return None
            
        from models.discount import DiscountCode
        return DiscountCode.get_by_code(self.discount_code)
        
    def add_receipt_image(self, image_path: str) -> bool:
        """
        Add receipt image to payment.
        
        Args:
            image_path (str): Path to receipt image
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        self.receipt_image = image_path
        return self.save()
        
    @staticmethod
    def get_total_revenue(start_date: Optional[datetime] = None, 
                         end_date: Optional[datetime] = None) -> float:
        """
        Get total revenue from completed payments.
        
        Args:
            start_date (Optional[datetime], optional): Start date filter. Defaults to None.
            end_date (Optional[datetime], optional): End date filter. Defaults to None.
            
        Returns:
            float: Total revenue
        """
        params = [Payment.STATUS_COMPLETED]
        query = """
            SELECT SUM(amount) as total
            FROM payments
            WHERE status = %s
        """
        
        if start_date:
            query += " AND created_at >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND created_at <= %s"
            params.append(end_date)
        
        result = execute_query(query, tuple(params), fetch="one")
        
        return float(result.get('total', 0)) if result and result.get('total') else 0
        
    @staticmethod
    def get_daily_revenue(days: int = 30) -> List[Dict[str, Any]]:
        """
        Get daily revenue for the last N days.
        
        Args:
            days (int, optional): Number of days to retrieve. Defaults to 30.
            
        Returns:
            List[Dict[str, Any]]: List of daily revenue data
        """
        query = """
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as count,
                SUM(amount) as total
            FROM payments
            WHERE status = %s
            AND created_at >= CURRENT_DATE - INTERVAL %s DAY
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        """
        
        return execute_query(query, (Payment.STATUS_COMPLETED, days))
        
    @staticmethod
    def get_revenue_by_payment_type(start_date: Optional[datetime] = None,
                                   end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Get revenue by payment type.
        
        Args:
            start_date (Optional[datetime], optional): Start date filter. Defaults to None.
            end_date (Optional[datetime], optional): End date filter. Defaults to None.
            
        Returns:
            List[Dict[str, Any]]: List of revenue by payment type
        """
        params = [Payment.STATUS_COMPLETED]
        query = """
            SELECT 
                payment_type,
                COUNT(*) as count,
                SUM(amount) as total
            FROM payments
            WHERE status = %s
        """
        
        if start_date:
            query += " AND created_at >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND created_at <= %s"
            params.append(end_date)
        
        query += " GROUP BY payment_type ORDER BY total DESC"
        
        return execute_query(query, tuple(params))
        
    @staticmethod
    def get_payment_method_stats(start_date: Optional[datetime] = None,
                                end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Get statistics by payment method.
        
        Args:
            start_date (Optional[datetime], optional): Start date filter. Defaults to None.
            end_date (Optional[datetime], optional): End date filter. Defaults to None.
            
        Returns:
            List[Dict[str, Any]]: List of statistics by payment method
        """
        params = []
        query = """
            SELECT 
                payment_method,
                COUNT(*) as count,
                SUM(CASE WHEN status = 'completed' THEN amount ELSE 0 END) as completed_amount,
                SUM(CASE WHEN status = 'pending' THEN amount ELSE 0 END) as pending_amount,
                SUM(CASE WHEN status = 'failed' THEN amount ELSE 0 END) as failed_amount,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_count,
                COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_count,
                COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_count
            FROM payments
            WHERE 1=1
        """
        
        if start_date:
            query += " AND created_at >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND created_at <= %s"
            params.append(end_date)
        
        query += " GROUP BY payment_method ORDER BY completed_amount DESC"
        
        return execute_query(query, tuple(params) if params else None)
        
    @staticmethod
    def count_payments_by_status() -> Dict[str, int]:
        """
        Count payments by status.
        
        Returns:
            Dict[str, int]: Dictionary with payment counts by status
        """
        query = """
            SELECT status, COUNT(*) as count
            FROM payments
            GROUP BY status
        """
        results = execute_query(query)
        
        counts = {
            Payment.STATUS_PENDING: 0,
            Payment.STATUS_COMPLETED: 0,
            Payment.STATUS_FAILED: 0,
            Payment.STATUS_REFUNDED: 0,
            Payment.STATUS_CANCELLED: 0
        }
        
        for result in results:
            counts[result['status']] = result['count']
            
        return counts
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert payment to dictionary.
        
        Returns:
            Dict[str, Any]: Payment data as dictionary
        """
        return {
            'id': self.id,
            'user_id': self.user_id,
            'amount': self.amount,
            'description': self.description,
            'status': self.status,
            'payment_type': self.payment_type,
            'payment_method': self.payment_method,
            'transaction_id': self.transaction_id,
            'reference_id': self.reference_id,
            'vpn_account_id': self.vpn_account_id,
            'discount_code': self.discount_code,
            'discount_amount': self.discount_amount,
            'admin_id': self.admin_id,
            'receipt_image': self.receipt_image,
            'extra_data': self.extra_data,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'user_telegram_id': self.user_telegram_id,
            'user_username': self.user_username,
            'user_first_name': self.user_first_name,
            'admin_telegram_id': self.admin_telegram_id,
            'admin_username': self.admin_username
        } 