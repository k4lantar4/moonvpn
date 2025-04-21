"""
Wallet service for managing user wallet operations (balance only)
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from db.repositories.user_repo import UserRepository
# Assuming a WalletRepository might exist in the future, or balance ops are in UserRepo
# from db.repositories.wallet_repo import WalletRepository

class WalletService:
    """Service focused solely on user balance management"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        # Removed self.transaction_repo
        self.user_repo = UserRepository(session)
        # self.wallet_repo = WalletRepository(session) # Example if WalletRepo exists
    
    async def get_balance(self, user_id: int) -> Optional[float]:
        """Get user's current balance"""
        user = await self.user_repo.get_by_id(user_id)
        return user.balance if user else None
    
    async def adjust_balance(self, user_id: int, amount: float) -> bool:
        """
        Adjust user's balance by a specific amount (positive or negative).
        Returns True if successful, False otherwise.
        Handles checks internally (e.g., sufficient funds for withdrawal).
        """
        # Ideally, this logic resides within the UserRepository or a dedicated WalletRepository
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return False

        if amount < 0 and user.balance < abs(amount):
            # Not enough funds for withdrawal
            return False

        # Assuming UserRepository has an update_balance method
        # This method should handle the actual DB update without commit here
        success = await self.user_repo.update_balance(user_id, user.balance + amount)
        # Removed direct balance modification and session.commit()
        return success

    # Removed get_recent_transactions - moved to TransactionService
    # Removed add_funds - replaced by adjust_balance and creation moved to TransactionService/PaymentService
    # Removed withdraw_funds - replaced by adjust_balance and creation moved to TransactionService/PaymentService
    # Removed get_transaction_by_id - moved to TransactionService
    # Removed update_transaction_status - moved to TransactionService

# Example of how add/withdraw might look if UserRepository handles balance update
# async def add_funds_example(self, user_id: int, amount: float) -> bool:
#     user = await self.user_repo.get_by_id(user_id)
#     if not user:
#         return False
#     return await self.user_repo.update_balance(user_id, user.balance + amount)

# async def withdraw_funds_example(self, user_id: int, amount: float) -> bool:
#     user = await self.user_repo.get_by_id(user_id)
#     if not user or user.balance < amount:
#         return False
#     return await self.user_repo.update_balance(user_id, user.balance - amount) 