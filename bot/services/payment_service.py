"""
Service layer for handling payments and wallet interactions.

NOTE: This service is refactored to use SQLAlchemy and Repositories.
The original Tortoise ORM implementation is removed.
Manages Payment records and coordinates with WalletService for balance updates.
"""

import logging
from typing import Optional, Dict, Any, List, Tuple
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

# Import models and schemas (SQLAlchemy based)
from core.database.models.user import User
from core.database.models.payment import Payment, PaymentStatus, PaymentType
from core.database.models.plan import Plan
from core.database.models.bank_card import BankCard
# Assuming WalletService will handle wallet/transaction logic
# from core.database.models.wallet import Wallet 
# from core.database.models.transaction import WalletTransaction, TransactionType

# Import repositories
from core.database.repositories.user_repository import UserRepository
from core.database.repositories.payment_repository import PaymentRepository, PaymentCreate, PaymentUpdate
from core.database.repositories.plan_repository import PlanRepository
from core.database.repositories.bank_card_repository import BankCardRepository
# Import WalletService
from bot.services.wallet_service import WalletService

# Import exceptions
from core.exceptions import NotFoundError, ServiceError, BusinessLogicError

logger = logging.getLogger(__name__)

class PaymentService:
    """Handles payment creation, confirmation, and status updates using SQLAlchemy."""

    def __init__(self):
        # Instantiate repositories
        self.payment_repo = PaymentRepository()
        self.user_repo = UserRepository()
        self.plan_repo = PlanRepository()
        self.bank_card_repo = BankCardRepository()
        # Instantiate WalletService
        self.wallet_service = WalletService()

    async def create_card_payment_request(
        self,
        session: AsyncSession,
        *, 
        user_id: int,
        plan_id: int,
        bank_card_id: int,
        reference_id: Optional[str] = None
    ) -> Payment:
        """
        Creates a PENDING card payment record for plan purchase. 
        Validates input and checks plan price.
        Assumes commit/rollback handled by the caller.

        Raises:
            NotFoundError: If user, plan, or bank card not found.
            ValueError: If plan price is zero or negative.
        """
        logger.info(f"Creating card payment request for user {user_id}, plan {plan_id}, card {bank_card_id}")
        user = await self.user_repo.get(session, id=user_id)
        if not user: raise NotFoundError(entity="User", identifier=user_id)
        
        plan = await self.plan_repo.get(session, id=plan_id)
        if not plan: raise NotFoundError(entity="Plan", identifier=plan_id)
        if not plan.price or plan.price <= 0:
            raise ValueError(f"Plan {plan_id} has an invalid price: {plan.price}")

        bank_card = await self.bank_card_repo.get(session, id=bank_card_id)
        if not bank_card: raise NotFoundError(entity="BankCard", identifier=bank_card_id)

        payment_in = PaymentCreate(
            user_id=user_id,
            plan_id=plan_id,
            amount=plan.price, # Use plan price directly
            payment_type=PaymentType.CARD,
            reference_id=reference_id,
            bank_card_id=bank_card_id,
            status=PaymentStatus.PENDING
        )
        
        payment = await self.payment_repo.create(session, obj_in=payment_in)
        logger.info(f"Card payment request created with ID: {payment.id}, Status: PENDING")
        return payment

    async def create_wallet_charge_request(
        self,
        session: AsyncSession,
        *,
        user_id: int,
        amount: Decimal,
        bank_card_id: int,
        reference_id: Optional[str] = None
    ) -> Payment:
        """
        Creates a PENDING wallet charge payment record. 
        Validates input.
        Assumes commit/rollback handled by the caller.

        Raises:
            NotFoundError: If user or bank card not found.
            ValueError: If amount is zero or negative.
        """
        logger.info(f"Creating wallet charge request for user {user_id}, amount {amount}, card {bank_card_id}")
        if amount <= 0:
            raise ValueError("Charge amount must be positive.")

        user = await self.user_repo.get(session, id=user_id)
        if not user: raise NotFoundError(entity="User", identifier=user_id)
        
        bank_card = await self.bank_card_repo.get(session, id=bank_card_id)
        if not bank_card: raise NotFoundError(entity="BankCard", identifier=bank_card_id)

        payment_in = PaymentCreate(
            user_id=user_id,
            amount=amount,
            payment_type=PaymentType.WALLET_CHARGE,
            reference_id=reference_id,
            bank_card_id=bank_card_id,
            status=PaymentStatus.PENDING
        )
        
        payment = await self.payment_repo.create(session, obj_in=payment_in)
        logger.info(f"Wallet charge request created with ID: {payment.id}, Status: PENDING")
        return payment

    async def process_wallet_payment(
        self,
        session: AsyncSession,
        *,
        user_id: int,
        plan_id: int
    ) -> Payment:
        """
        Processes a plan purchase using the user's wallet balance.
        Creates a CONFIRMED payment record and calls WalletService to deduct balance.
        Assumes commit/rollback handled by the caller (this function performs multiple steps).

        Raises:
            NotFoundError: If user or plan not found.
            ValueError: If plan price is invalid.
            BusinessLogicError: If wallet balance is insufficient.
            ServiceError: If WalletService fails.
        """
        logger.info(f"Processing wallet payment for user {user_id}, plan {plan_id}")
        user = await self.user_repo.get(session, id=user_id)
        if not user: raise NotFoundError(entity="User", identifier=user_id)
        
        plan = await self.plan_repo.get(session, id=plan_id)
        if not plan: raise NotFoundError(entity="Plan", identifier=plan_id)
        if not plan.price or plan.price <= 0:
            raise ValueError(f"Plan {plan_id} has an invalid price: {plan.price}")

        # --- Create Payment Record First ---
        payment_in = PaymentCreate(
            user_id=user_id,
            plan_id=plan_id,
            amount=plan.price,
            payment_type=PaymentType.WALLET,
            status=PaymentStatus.CONFIRMED # Wallet payments are confirmed if balance check passes
        )
        payment = await self.payment_repo.create(session, obj_in=payment_in)
        logger.info(f"Wallet payment record created with ID: {payment.id}")

        # --- Call Wallet Service to Handle Balance & Transaction ---
        try:
            success = await self.wallet_service.record_purchase(
                session=session, 
                user_id=user_id, 
                amount=plan.price, 
                payment_id=payment.id,
                description=f"Purchase of plan: {plan.name}"
            )
            if not success:
                # This indicates an issue within WalletService (e.g., insufficient funds handled there)
                logger.error(f"WalletService failed to record purchase for payment {payment.id}. Rolling back.")
                # We need to signal the caller to rollback. Raising an error is best.
                raise BusinessLogicError("Failed to record wallet purchase (e.g., insufficient funds).")
            
            logger.info(f"WalletService successfully recorded purchase for payment {payment.id}")
            # No commit here, caller handles it.
            return payment

        except Exception as e:
            logger.exception(f"Error calling WalletService for payment {payment.id}: {e}. Need rollback.")
            # Re-raise the exception so the caller knows to rollback
            raise ServiceError(f"Error processing wallet balance: {e}") from e

    async def confirm_pending_payment(
        self,
        session: AsyncSession,
        *,
        payment_id: int,
        admin_id: int,
        transaction_id: Optional[str] = None 
    ) -> Payment:
        """
        Confirms a PENDING payment (Card Purchase or Wallet Charge).
        Updates payment status and calls WalletService for deposits.
        Assumes commit/rollback handled by the caller.
        
        Raises:
            NotFoundError: If payment not found.
            ValueError: If payment is not in PENDING state or is wrong type.
            ServiceError: If WalletService fails.
        """
        logger.info(f"Admin {admin_id} attempting to confirm payment {payment_id}")
        payment = await self.payment_repo.get(session, id=payment_id)
        if not payment: raise NotFoundError(entity="Payment", identifier=payment_id)

        if payment.status != PaymentStatus.PENDING:
            raise ValueError(f"Payment {payment_id} is not PENDING (status: {payment.status}). Cannot confirm.")
            
        if payment.payment_type not in [PaymentType.CARD, PaymentType.WALLET_CHARGE]:
             raise ValueError(f"Payment {payment_id} type ({payment.payment_type}) cannot be manually confirmed.")

        # --- Update Payment Status --- 
        payment_update = PaymentUpdate(
            status=PaymentStatus.CONFIRMED,
            admin_id=admin_id,
            transaction_id=transaction_id
        )
        updated_payment = await self.payment_repo.update(session, db_obj=payment, obj_in=payment_update)
        logger.info(f"Payment {payment_id} status updated to CONFIRMED by admin {admin_id}.")

        # --- If it was a Wallet Charge, call WalletService to add funds ---
        if updated_payment.payment_type == PaymentType.WALLET_CHARGE:
            logger.info(f"Calling WalletService to record deposit for confirmed charge payment {payment_id}")
            try:
                success = await self.wallet_service.record_deposit(
                    session=session,
                    user_id=updated_payment.user_id,
                    amount=updated_payment.amount,
                    payment_id=updated_payment.id,
                    description=f"Wallet charge confirmed by admin {admin_id}"
                )
                if not success:
                    logger.error(f"WalletService failed to record deposit for payment {payment_id}. Rolling back.")
                    raise BusinessLogicError("Failed to record wallet deposit.")
                
                logger.info(f"WalletService successfully recorded deposit for payment {payment_id}")

            except Exception as e:
                logger.exception(f"Error calling WalletService for deposit on payment {payment_id}: {e}. Need rollback.")
                raise ServiceError(f"Error processing wallet deposit: {e}") from e
        
        # No commit here, caller handles it.
        return updated_payment

    async def reject_pending_payment(
        self,
        session: AsyncSession,
        *,
        payment_id: int,
        admin_id: int
        # Add reason later if needed
    ) -> Payment:
        """
        Rejects a PENDING payment (Card Purchase or Wallet Charge).
        Assumes commit/rollback handled by the caller.
        
        Raises:
            NotFoundError: If payment not found.
            ValueError: If payment is not in PENDING state or is wrong type.
        """
        logger.info(f"Admin {admin_id} attempting to reject payment {payment_id}")
        payment = await self.payment_repo.get(session, id=payment_id)
        if not payment: raise NotFoundError(entity="Payment", identifier=payment_id)

        if payment.status != PaymentStatus.PENDING:
            raise ValueError(f"Payment {payment_id} is not PENDING (status: {payment.status}). Cannot reject.")

        if payment.payment_type not in [PaymentType.CARD, PaymentType.WALLET_CHARGE]:
             raise ValueError(f"Payment {payment_id} type ({payment.payment_type}) cannot be manually rejected.")

        payment_update = PaymentUpdate(
            status=PaymentStatus.REJECTED,
            admin_id=admin_id
        )
        updated_payment = await self.payment_repo.update(session, db_obj=payment, obj_in=payment_update)
        logger.info(f"Payment {payment_id} status updated to REJECTED by admin {admin_id}.")
        
        # No commit here, caller handles it.
        return updated_payment

    async def get_user_payments_history(
        self,
        session: AsyncSession,
        *, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Payment]:
        """Gets payment history for a user."""
        logger.debug(f"Fetching payment history for user {user_id}")
        return await self.payment_repo.get_user_payments(session, user_id=user_id, skip=skip, limit=limit)

    async def get_pending_review_payments(self, session: AsyncSession, skip: int = 0, limit: int = 100) -> List[Payment]:
        """Gets payments awaiting admin review."""
        logger.debug("Fetching payments pending review")
        return await self.payment_repo.get_pending_card_payments(session, skip=skip, limit=limit)

    async def get_payment_by_id(self, session: AsyncSession, payment_id: int) -> Optional[Payment]:
         """Gets a single payment by its ID."""
         logger.debug(f"Fetching payment by id={payment_id}")
         return await self.payment_repo.get(session, id=payment_id)

    # --- Zarinpal Integration (Example Placeholder) --- 
    # async def initiate_zarinpal_payment(self, user_id: int, amount: Decimal, description: str, callback_url: str) -> Tuple[Optional[str], Optional[str]]:
    #     """Initiates a payment via Zarinpal and returns the payment URL and authority code."""
    #     logger.info(f"Initiating Zarinpal payment for user {user_id}, amount {amount}")
    #     # 1. Get user email/mobile if needed by Zarinpal
    #     # 2. Instantiate Zarinpal client (from integrations)
    #     # 3. Call Zarinpal API to request payment
    #     # 4. Store the authority code with a pending Payment record (status=INITIATED?)
    #     # 5. Return payment URL and authority
    #     pass

    # async def verify_zarinpal_payment(self, session: AsyncSession, authority: str, status: str) -> Optional[Payment]:
    #     """Verifies a Zarinpal payment callback."""
    #     logger.info(f"Verifying Zarinpal payment with authority {authority}, status {status}")
    #     # 1. Find the pending Payment record using the authority
    #     # 2. If status is 'OK':
    #     #    a. Instantiate Zarinpal client
    #     #    b. Call Zarinpal API to verify the payment, passing amount
    #     #    c. If verification is successful:
    #     #        i. Update Payment record status to CONFIRMED, store ref_id
    #     #        ii. Call WalletService to record deposit
    #     #        iii. Commit transaction (or let caller commit)
    #     #        iv. Return the confirmed Payment object
    #     #    d. If verification fails:
    #     #        i. Update Payment record status to FAILED/REJECTED
    #     #        ii. Commit (or let caller commit)
    #     #        iii. Return None or the failed Payment object
    #     # 3. If status is 'NOK':
    #     #    a. Update Payment record status to FAILED/CANCELED
    #     #    b. Commit (or let caller commit)
    #     #    c. Return None or the failed Payment object
    #     pass 