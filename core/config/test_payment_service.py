import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.payment_service import PaymentService
from app.models.payment import Payment, PaymentStatus
from app.tests.utils import create_test_user

@pytest.mark.asyncio
class TestPaymentService:
    async def test_create_payment(self, db_session: AsyncSession):
        """Test payment creation."""
        test_user = await create_test_user(db_session)
        payment_service = PaymentService(db_session)
        
        payment = await payment_service.create_payment(
            user_id=test_user.id,
            amount=29.99,
            currency="USD",
            payment_method="crypto",
            description="Premium VPN Subscription"
        )
        
        assert payment.user_id == test_user.id
        assert payment.amount == 29.99
        assert payment.currency == "USD"
        assert payment.payment_method == "crypto"
        assert payment.status == PaymentStatus.PENDING

    async def test_get_payment_by_id(self, db_session: AsyncSession):
        """Test retrieving payment by ID."""
        test_user = await create_test_user(db_session)
        payment_service = PaymentService(db_session)
        
        # Create a payment first
        payment = await payment_service.create_payment(
            user_id=test_user.id,
            amount=29.99,
            currency="USD",
            payment_method="crypto",
            description="Premium VPN Subscription"
        )
        
        retrieved_payment = await payment_service.get_payment_by_id(payment.id)
        
        assert retrieved_payment is not None
        assert retrieved_payment.id == payment.id
        assert retrieved_payment.user_id == test_user.id

    async def test_get_user_payments(self, db_session: AsyncSession):
        """Test retrieving user's payments."""
        test_user = await create_test_user(db_session)
        payment_service = PaymentService(db_session)
        
        # Create multiple payments
        await payment_service.create_payment(
            user_id=test_user.id,
            amount=29.99,
            currency="USD",
            payment_method="crypto",
            description="Payment 1"
        )
        
        await payment_service.create_payment(
            user_id=test_user.id,
            amount=19.99,
            currency="USD",
            payment_method="crypto",
            description="Payment 2"
        )
        
        payments = await payment_service.get_user_payments(test_user.id)
        
        assert len(payments) >= 2
        assert any(p.amount == 29.99 for p in payments)
        assert any(p.amount == 19.99 for p in payments)

    async def test_update_payment_status(self, db_session: AsyncSession):
        """Test updating payment status."""
        test_user = await create_test_user(db_session)
        payment_service = PaymentService(db_session)
        
        payment = await payment_service.create_payment(
            user_id=test_user.id,
            amount=29.99,
            currency="USD",
            payment_method="crypto",
            description="Premium VPN Subscription"
        )
        
        updated_payment = await payment_service.update_payment_status(
            payment_id=payment.id,
            status=PaymentStatus.COMPLETED,
            transaction_id="test_tx_123"
        )
        
        assert updated_payment.status == PaymentStatus.COMPLETED
        assert updated_payment.transaction_id == "test_tx_123"
        assert updated_payment.completed_at is not None

    async def test_get_pending_payments(self, db_session: AsyncSession):
        """Test retrieving pending payments."""
        test_user = await create_test_user(db_session)
        payment_service = PaymentService(db_session)
        
        # Create payments with different statuses
        await payment_service.create_payment(
            user_id=test_user.id,
            amount=29.99,
            currency="USD",
            payment_method="crypto",
            description="Pending Payment"
        )
        
        payment2 = await payment_service.create_payment(
            user_id=test_user.id,
            amount=19.99,
            currency="USD",
            payment_method="crypto",
            description="Completed Payment"
        )
        
        await payment_service.update_payment_status(
            payment_id=payment2.id,
            status=PaymentStatus.COMPLETED
        )
        
        pending_payments = await payment_service.get_pending_payments()
        
        assert len(pending_payments) >= 1
        assert all(p.status == PaymentStatus.PENDING for p in pending_payments)

    async def test_cancel_payment(self, db_session: AsyncSession):
        """Test payment cancellation."""
        test_user = await create_test_user(db_session)
        payment_service = PaymentService(db_session)
        
        payment = await payment_service.create_payment(
            user_id=test_user.id,
            amount=29.99,
            currency="USD",
            payment_method="crypto",
            description="Premium VPN Subscription"
        )
        
        cancelled_payment = await payment_service.cancel_payment(payment.id)
        
        assert cancelled_payment.status == PaymentStatus.CANCELLED
        assert cancelled_payment.cancelled_at is not None

    async def test_get_payment_statistics(self, db_session: AsyncSession):
        """Test retrieving payment statistics."""
        test_user = await create_test_user(db_session)
        payment_service = PaymentService(db_session)
        
        # Create payments with different statuses
        await payment_service.create_payment(
            user_id=test_user.id,
            amount=29.99,
            currency="USD",
            payment_method="crypto",
            description="Completed Payment"
        )
        
        payment2 = await payment_service.create_payment(
            user_id=test_user.id,
            amount=19.99,
            currency="USD",
            payment_method="crypto",
            description="Failed Payment"
        )
        
        await payment_service.update_payment_status(
            payment_id=payment2.id,
            status=PaymentStatus.FAILED
        )
        
        stats = await payment_service.get_payment_statistics()
        
        assert "total_amount" in stats
        assert "successful_payments" in stats
        assert "failed_payments" in stats
        assert "pending_payments" in stats 