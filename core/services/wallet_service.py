"""
Wallet service for managing user wallet operations
"""

from typing import Optional, List, Dict, Tuple, Union
from decimal import Decimal
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from db.repositories.wallet_repo import WalletRepository
from db.repositories.user_repo import UserRepository
from db.repositories.transaction_repo import TransactionRepository
from db.models.transaction import Transaction, TransactionType, TransactionStatus
from db.models.wallet import Wallet

class WalletService:
    """Service for managing wallet operations"""
    
    def __init__(self, session: Union[AsyncSession, Session]):
        self.session = session
        self.wallet_repo = WalletRepository(session)
        self.user_repo = UserRepository(session)
        self.transaction_repo = TransactionRepository(session)
        self._is_async = isinstance(session, AsyncSession)
    
    def get_balance(self, user_id: int) -> Optional[Decimal]:
        """
        Get user's current wallet balance
        
        Args:
            user_id: شناسه کاربر
        
        Returns:
            موجودی کیف پول (Decimal) یا None در صورت عدم وجود کیف پول
        """
        # Handle both sync and async cases
        if self._is_async:
            return self._get_balance_async(user_id)
        else:
            # Synchronous version
            # First check wallet table if exists
            wallet_balance = self.wallet_repo.get_user_balance(user_id)
            if wallet_balance is not None:
                return wallet_balance
                
            # Fall back to user's balance field
            user = self.user_repo.get_by_id(user_id)
            return user.balance if user else None
    
    async def _get_balance_async(self, user_id: int) -> Optional[Decimal]:
        """Async version of get_balance"""
        # First check wallet table if exists
        wallet_balance = await self.wallet_repo.get_user_balance(user_id)
        if wallet_balance is not None:
            return wallet_balance
            
        # Fall back to user's balance field
        user = await self.user_repo.get_by_id(user_id)
        return user.balance if user else None
    
    def adjust_balance(self, user_id: int, amount: Decimal) -> bool:
        """
        Adjust user's wallet balance by a specific amount (positive or negative)
        
        Args:
            user_id: شناسه کاربر
            amount: مبلغ تغییر (مثبت برای افزایش، منفی برای کاهش)
            
        Returns:
            موفقیت عملیات (بولین)
        """
        # Handle both sync and async cases
        if self._is_async:
            return self._adjust_balance_async(user_id, amount)
        else:
            # Synchronous version
            # Ensure amount is a Decimal
            if not isinstance(amount, Decimal):
                amount = Decimal(str(amount))
                
            # First try to update wallet if exists
            wallet = self.wallet_repo.get_by_user_id(user_id)
            if wallet:
                updated_wallet = self.wallet_repo.adjust_balance(wallet.id, amount)
                return updated_wallet is not None
            
            # If no wallet, try to create one
            wallet = self.wallet_repo.create_wallet(user_id)
            if wallet:
                updated_wallet = self.wallet_repo.adjust_balance(wallet.id, amount)
                return updated_wallet is not None
                
            # Finally, fall back to user's balance field
            user = self.user_repo.get_by_id(user_id)
            if not user:
                return False
                
            # Check if subtraction would result in negative balance
            if amount < 0 and user.balance + amount < 0:
                return False
                
            return self.user_repo.update_balance(user_id, user.balance + amount)
            
    async def _adjust_balance_async(self, user_id: int, amount: Decimal) -> bool:
        """Async version of adjust_balance"""
        # Ensure amount is a Decimal
        if not isinstance(amount, Decimal):
            amount = Decimal(str(amount))
            
        # First try to update wallet if exists
        wallet = await self.wallet_repo.get_by_user_id(user_id)
        if wallet:
            updated_wallet = await self.wallet_repo.adjust_balance(wallet.id, amount)
            return updated_wallet is not None
        
        # If no wallet, try to create one
        wallet = await self.wallet_repo.create_wallet(user_id)
        if wallet:
            updated_wallet = await self.wallet_repo.adjust_balance(wallet.id, amount)
            return updated_wallet is not None
            
        # Finally, fall back to user's balance field
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return False
            
        # Check if subtraction would result in negative balance
        if amount < 0 and user.balance + amount < 0:
            return False
            
        return await self.user_repo.update_balance(user_id, user.balance + amount)
    
    def top_up_wallet(self, user_id: int, amount: Decimal, reference: str = None) -> Tuple[bool, Optional[Transaction]]:
        """
        Add funds to user's wallet and create a deposit transaction
        
        Args:
            user_id: شناسه کاربر
            amount: مبلغ افزایش
            reference: شناسه مرجع تراکنش (اختیاری)
            
        Returns:
            Tuple[bool, Optional[Transaction]]: موفقیت عملیات و تراکنش ایجاد شده
        """
        # Handle both sync and async cases
        if self._is_async:
            return self._top_up_wallet_async(user_id, amount, reference)
        else:
            # Synchronous version
            # Ensure amount is positive
            if amount <= 0:
                return False, None
                
            # Create transaction record
            transaction_data = {
                "user_id": user_id,
                "amount": amount,
                "type": TransactionType.DEPOSIT,
                "status": TransactionStatus.PENDING,
                "reference": reference,
                "created_at": datetime.utcnow()
            }
            
            # Add to transaction repository
            transaction = self.transaction_repo.create_transaction(transaction_data)
            if not transaction:
                return False, None
                
            # Update wallet balance
            success = self.adjust_balance(user_id, amount)
            if success:
                # Update transaction status to success
                transaction.status = TransactionStatus.SUCCESS
                return True, transaction
            else:
                # Update transaction status to failed
                transaction.status = TransactionStatus.FAILED
                return False, transaction
    
    async def _top_up_wallet_async(self, user_id: int, amount: Decimal, reference: str = None) -> Tuple[bool, Optional[Transaction]]:
        """Async version of top_up_wallet"""
        # Ensure amount is positive
        if amount <= 0:
            return False, None
            
        # Create transaction record
        transaction_data = {
            "user_id": user_id,
            "amount": amount,
            "type": TransactionType.DEPOSIT,
            "status": TransactionStatus.PENDING,
            "reference": reference,
            "created_at": datetime.utcnow()
        }
        
        # Add to transaction repository
        transaction = await self.transaction_repo.create_transaction(transaction_data)
        if not transaction:
            return False, None
            
        # Update wallet balance
        success = await self.adjust_balance(user_id, amount)
        if success:
            # Update transaction status to success
            transaction.status = TransactionStatus.SUCCESS
            return True, transaction
        else:
            # Update transaction status to failed
            transaction.status = TransactionStatus.FAILED
            return False, transaction
            
    def withdraw_from_wallet(self, user_id: int, amount: Decimal, order_id: int = None) -> Tuple[bool, Optional[Transaction]]:
        """
        Withdraw funds from user's wallet for a purchase and create a purchase transaction
        
        Args:
            user_id: شناسه کاربر
            amount: مبلغ برداشت
            order_id: شناسه سفارش مرتبط (اختیاری)
            
        Returns:
            Tuple[bool, Optional[Transaction]]: موفقیت عملیات و تراکنش ایجاد شده
        """
        # Handle both sync and async cases
        if self._is_async:
            return self._withdraw_from_wallet_async(user_id, amount, order_id)
        else:
            # Synchronous version
            # Ensure amount is positive
            if amount <= 0:
                return False, None
                
            # Check balance first
            balance = self.get_balance(user_id)
            if balance is None or balance < amount:
                return False, None
                
            # Create transaction record
            transaction_data = {
                "user_id": user_id,
                "related_order_id": order_id,
                "amount": -amount,  # Negative for withdrawal
                "type": TransactionType.PURCHASE,
                "status": TransactionStatus.PENDING,
                "created_at": datetime.utcnow()
            }
            
            # Add to transaction repository
            transaction = self.transaction_repo.create_transaction(transaction_data)
            if not transaction:
                return False, None
                
            # Update wallet balance
            success = self.adjust_balance(user_id, -amount)  # Negative for withdrawal
            if success:
                # Update transaction status to success
                transaction.status = TransactionStatus.SUCCESS
                return True, transaction
            else:
                # Update transaction status to failed
                transaction.status = TransactionStatus.FAILED
                return False, transaction
    
    async def _withdraw_from_wallet_async(self, user_id: int, amount: Decimal, order_id: int = None) -> Tuple[bool, Optional[Transaction]]:
        """Async version of withdraw_from_wallet"""
        # Ensure amount is positive
        if amount <= 0:
            return False, None
            
        # Check balance first
        balance = await self.get_balance(user_id)
        if balance is None or balance < amount:
            return False, None
            
        # Create transaction record
        transaction_data = {
            "user_id": user_id,
            "related_order_id": order_id,
            "amount": -amount,  # Negative for withdrawal
            "type": TransactionType.PURCHASE,
            "status": TransactionStatus.PENDING,
            "created_at": datetime.utcnow()
        }
        
        # Add to transaction repository
        transaction = await self.transaction_repo.create_transaction(transaction_data)
        if not transaction:
            return False, None
            
        # Update wallet balance
        success = await self.adjust_balance(user_id, -amount)  # Negative for withdrawal
        if success:
            # Update transaction status to success
            transaction.status = TransactionStatus.SUCCESS
            return True, transaction
        else:
            # Update transaction status to failed
            transaction.status = TransactionStatus.FAILED
            return False, transaction
            
    def get_wallet_history(self, user_id: int, limit: int = 10) -> List[Transaction]:
        """
        Get user's wallet transaction history
        
        Args:
            user_id: شناسه کاربر
            limit: محدودیت تعداد تراکنش‌ها (پیش‌فرض: 10)
            
        Returns:
            لیست تراکنش‌های کاربر
        """
        # Handle both sync and async cases
        if self._is_async:
            return self._get_wallet_history_async(user_id, limit)
        else:
            # Synchronous version
            return self.transaction_repo.get_user_transactions(user_id, limit)
    
    async def _get_wallet_history_async(self, user_id: int, limit: int = 10) -> List[Transaction]:
        """Async version of get_wallet_history"""
        return await self.transaction_repo.get_user_transactions(user_id, limit) 