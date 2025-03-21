"""
Unit tests for the payment service.
"""
import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.payment import Payment, PaymentTransaction
from app.services.payment_service import PaymentService
from app.schemas.payment import PaymentCreate, PaymentTransactionCreate
from app.models.subscription import SubscriptionPlan

pytestmark = pytest.mark.asyncio

class TestPaymentService:
    """Test cases for PaymentService."""

    async def test_create_payment(self, db_session: AsyncSession, test_user, test_subscription_plan):
        """Test creating a new payment."""
        # Arrange
        payment_data = PaymentCreate(
            user_id=test_user.id,
            plan_id=test_subscription_plan.id,
            amount=test_subscription_plan.price,
            currency="USD",
            payment_method="credit_card",
            status="pending"
        )
        payment_service = PaymentService(db_session)

        # Act
        payment = await payment_service.create_payment(payment_data)

        # Assert
        assert payment.user_id == test_user.id
        assert payment.plan_id == test_subscription_plan.id
        assert payment.amount == test_subscription_plan.price
        assert payment.currency == payment_data.currency
        assert payment.payment_method == payment_data.payment_method
        assert payment.status == payment_data.status

    async def test_create_payment_transaction(self, db_session: AsyncSession, test_payment):
        """Test creating a new payment transaction."""
        # Arrange
        transaction_data = PaymentTransactionCreate(
            payment_id=test_payment.id,
            transaction_id="test_transaction_123",
            amount=test_payment.amount,
            currency=test_payment.currency,
            status="completed",
            payment_method=test_payment.payment_method,
            payment_date=datetime.utcnow()
        )
        payment_service = PaymentService(db_session)

        # Act
        transaction = await payment_service.create_transaction(transaction_data)

        # Assert
        assert transaction.payment_id == test_payment.id
        assert transaction.transaction_id == transaction_data.transaction_id
        assert transaction.amount == transaction_data.amount
        assert transaction.currency == transaction_data.currency
        assert transaction.status == transaction_data.status
        assert transaction.payment_method == transaction_data.payment_method

    async def test_get_payment(self, db_session: AsyncSession, test_payment):
        """Test retrieving a payment."""
        # Arrange
        payment_service = PaymentService(db_session)

        # Act
        payment = await payment_service.get_payment(test_payment.id)

        # Assert
        assert payment is not None
        assert payment.id == test_payment.id
        assert payment.user_id == test_payment.user_id
        assert payment.plan_id == test_payment.plan_id

    async def test_get_user_payments(self, db_session: AsyncSession, test_user, test_payment):
        """Test retrieving all payments for a user."""
        # Arrange
        payment_service = PaymentService(db_session)

        # Act
        payments = await payment_service.get_user_payments(test_user.id)

        # Assert
        assert len(payments) > 0
        assert any(payment.id == test_payment.id for payment in payments)

    async def test_update_payment_status(self, db_session: AsyncSession, test_payment):
        """Test updating payment status."""
        # Arrange
        payment_service = PaymentService(db_session)

        # Act
        await payment_service.update_payment_status(test_payment.id, "completed")

        # Assert
        updated_payment = await payment_service.get_payment(test_payment.id)
        assert updated_payment.status == "completed"

    async def test_get_payment_transactions(self, db_session: AsyncSession, test_payment, test_payment_transaction):
        """Test retrieving payment transactions."""
        # Arrange
        payment_service = PaymentService(db_session)

        # Act
        transactions = await payment_service.get_payment_transactions(test_payment.id)

        # Assert
        assert len(transactions) > 0
        assert any(transaction.id == test_payment_transaction.id for transaction in transactions)

    async def test_process_payment(self, db_session: AsyncSession, test_payment):
        """Test processing a payment."""
        # Arrange
        payment_service = PaymentService(db_session)
        transaction_id = "test_transaction_123"

        # Act
        processed_payment = await payment_service.process_payment(
            test_payment.id,
            transaction_id,
            "completed"
        )

        # Assert
        assert processed_payment.status == "completed"
        assert processed_payment.transaction_id == transaction_id
        assert processed_payment.payment_date is not None

    async def test_refund_payment(self, db_session: AsyncSession, test_payment):
        """Test refunding a payment."""
        # Arrange
        payment_service = PaymentService(db_session)
        refund_reason = "Customer request"

        # Act
        refunded_payment = await payment_service.refund_payment(
            test_payment.id,
            refund_reason
        )

        # Assert
        assert refunded_payment.status == "refunded"
        assert refunded_payment.refund_reason == refund_reason
        assert refunded_payment.refund_date is not None

    async def test_validate_payment(self, db_session: AsyncSession, test_payment):
        """Test validating a payment."""
        # Arrange
        payment_service = PaymentService(db_session)

        # Act
        is_valid = await payment_service.validate_payment(test_payment.id)

        # Assert
        assert is_valid is True 