"""
Wallet repository for database operations
"""

from typing import Optional, List, Union
from decimal import Decimal
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from db.models.wallet import Wallet
from db.models.user import User
from .base_repository import BaseRepository


class WalletRepository(BaseRepository):
    """Repository for wallet-related database operations"""
    
    def __init__(self, session: Union[AsyncSession, Session]):
        """مقداردهی اولیه با سشن دیتابیس"""
        super().__init__(session, Wallet)
        self.session = session
        self.model = Wallet
        self._is_async = isinstance(session, AsyncSession)
    
    def get_by_id(self, wallet_id: int) -> Optional[Wallet]:
        """Get wallet by ID"""
        if self._is_async:
            return self._get_by_id_async(wallet_id)
        else:
            return self.session.query(Wallet).filter(Wallet.id == wallet_id).first()
    
    async def _get_by_id_async(self, wallet_id: int) -> Optional[Wallet]:
        """Async version of get_by_id"""
        query = select(Wallet).where(Wallet.id == wallet_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    def get_by_user_id(self, user_id: int) -> Optional[Wallet]:
        """Get wallet by user ID"""
        if self._is_async:
            return self._get_by_user_id_async(user_id)
        else:
            return self.session.query(Wallet).filter(Wallet.user_id == user_id).first()
    
    async def _get_by_user_id_async(self, user_id: int) -> Optional[Wallet]:
        """Async version of get_by_user_id"""
        query = select(Wallet).where(Wallet.user_id == user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    def create_wallet(self, user_id: int, initial_balance: Decimal = Decimal('0')) -> Optional[Wallet]:
        """Create a new wallet for a user"""
        if self._is_async:
            return self._create_wallet_async(user_id, initial_balance)
        else:
            try:
                wallet = Wallet(
                    user_id=user_id,
                    balance=initial_balance
                )
                self.session.add(wallet)
                self.session.flush()
                return wallet
            except SQLAlchemyError:
                self.session.rollback()
                return None
    
    async def _create_wallet_async(self, user_id: int, initial_balance: Decimal = Decimal('0')) -> Optional[Wallet]:
        """Async version of create_wallet"""
        try:
            wallet = Wallet(
                user_id=user_id,
                balance=initial_balance
            )
            self.session.add(wallet)
            await self.session.flush()
            return wallet
        except SQLAlchemyError:
            await self.session.rollback()
            return None
    
    def get_or_create_wallet(self, user_id: int) -> Optional[Wallet]:
        """Get a user's wallet or create it if it doesn't exist"""
        if self._is_async:
            return self._get_or_create_wallet_async(user_id)
        else:
            wallet = self.get_by_user_id(user_id)
            if wallet:
                return wallet
                
            # Create new wallet
            return self.create_wallet(user_id)
    
    async def _get_or_create_wallet_async(self, user_id: int) -> Optional[Wallet]:
        """Async version of get_or_create_wallet"""
        wallet = await self.get_by_user_id(user_id)
        if wallet:
            return wallet
            
        # Create new wallet
        return await self.create_wallet(user_id)
    
    def update_balance(self, wallet_id: int, new_balance: Decimal) -> bool:
        """Update wallet balance"""
        if self._is_async:
            return self._update_balance_async(wallet_id, new_balance)
        else:
            try:
                stmt = update(Wallet).where(Wallet.id == wallet_id).values(balance=new_balance)
                self.session.execute(stmt)
                self.session.flush()
                return True
            except SQLAlchemyError:
                return False
    
    async def _update_balance_async(self, wallet_id: int, new_balance: Decimal) -> bool:
        """Async version of update_balance"""
        try:
            stmt = update(Wallet).where(Wallet.id == wallet_id).values(balance=new_balance)
            await self.session.execute(stmt)
            await self.session.flush()
            return True
        except SQLAlchemyError:
            return False
            
    def adjust_balance(self, wallet_id: int, amount: Decimal) -> Optional[Wallet]:
        """
        Adjust wallet balance by adding the specified amount (can be negative)
        Returns the updated wallet if successful, None if failed
        """
        if self._is_async:
            return self._adjust_balance_async(wallet_id, amount)
        else:
            wallet = self.get_by_id(wallet_id)
            if not wallet:
                return None
                
            try:
                wallet.balance += amount
                self.session.flush()
                return wallet
            except SQLAlchemyError:
                return None
    
    async def _adjust_balance_async(self, wallet_id: int, amount: Decimal) -> Optional[Wallet]:
        """Async version of adjust_balance"""
        wallet = await self.get_by_id(wallet_id)
        if not wallet:
            return None
            
        try:
            wallet.balance += amount
            await self.session.flush()
            return wallet
        except SQLAlchemyError:
            return None
            
    def adjust_balance_by_user_id(self, user_id: int, amount: Decimal) -> Optional[Wallet]:
        """
        Adjust wallet balance by user ID
        Creates the wallet if it doesn't exist
        """
        if self._is_async:
            return self._adjust_balance_by_user_id_async(user_id, amount)
        else:
            wallet = self.get_by_user_id(user_id)
            if not wallet:
                wallet = self.create_wallet(user_id)
                if not wallet:
                    return None
                    
            return self.adjust_balance(wallet.id, amount)
    
    async def _adjust_balance_by_user_id_async(self, user_id: int, amount: Decimal) -> Optional[Wallet]:
        """Async version of adjust_balance_by_user_id"""
        wallet = await self.get_by_user_id(user_id)
        if not wallet:
            wallet = await self.create_wallet(user_id)
            if not wallet:
                return None
                
        return await self.adjust_balance(wallet.id, amount)
        
    def get_user_balance(self, user_id: int) -> Optional[Decimal]:
        """Get user's wallet balance"""
        if self._is_async:
            return self._get_user_balance_async(user_id)
        else:
            wallet = self.get_by_user_id(user_id)
            if wallet:
                return wallet.balance
            return None
    
    async def _get_user_balance_async(self, user_id: int) -> Optional[Decimal]:
        """Async version of get_user_balance"""
        wallet = await self.get_by_user_id(user_id)
        if wallet:
            return wallet.balance
        return None 