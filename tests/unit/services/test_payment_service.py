"""Unit tests for payment service."""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.payment import PaymentService
from app.schemas.payment import (
    PaymentCreate,
    PaymentUpdate,
    SubscriptionCreate,
    SubscriptionUpdate
)
from app.models.payment import Payment, Subscription

class TestPayment:
    """Test payment operations."""
    
    @pytest.mark.asyncio
    async def test_create_payment(self, db: AsyncSession):
        """Test creating a new payment."""
        payment_service = PaymentService(db)
        payment_data = PaymentCreate(
            user_id=1,
            amount=10.00,
            currency="USD",
            status="pending",
            payment_method="stripe",
            payment_id="test_payment_id",
            description="Test payment"
        )
        
        payment = await payment_service.create_payment(payment_data)
        
        assert payment.user_id == payment_data.user_id
        assert payment.amount == payment_data.amount
        assert payment.currency == payment_data.currency
        assert payment.status == payment_data.status
        assert payment.payment_method == payment_data.payment_method
        assert payment.payment_id == payment_data.payment_id
        assert payment.description == payment_data.description
        assert payment.id is not None
        assert payment.created_at is not None
    
    @pytest.mark.asyncio
    async def test_get_payments(self, db: AsyncSession):
        """Test getting list of payments."""
        payment_service = PaymentService(db)
        
        # Create multiple payments
        payment_data1 = PaymentCreate(
            user_id=1,
            amount=10.00,
            currency="USD",
            status="completed",
            payment_method="stripe",
            payment_id="test_payment_id_1",
            description="First test payment"
        )
        
        payment_data2 = PaymentCreate(
            user_id=1,
            amount=20.00,
            currency="USD",
            status="pending",
            payment_method="stripe",
            payment_id="test_payment_id_2",
            description="Second test payment"
        )
        
        await payment_service.create_payment(payment_data1)
        await payment_service.create_payment(payment_data2)
        
        payments = await payment_service.get_payments(user_id=1)
        assert len(payments) == 2
        assert any(p.amount == 10.00 for p in payments)
        assert any(p.amount == 20.00 for p in payments)
    
    @pytest.mark.asyncio
    async def test_update_payment(self, db: AsyncSession):
        """Test updating a payment."""
        payment_service = PaymentService(db)
        
        # Create a payment
        payment_data = PaymentCreate(
            user_id=1,
            amount=10.00,
            currency="USD",
            status="pending",
            payment_method="stripe",
            payment_id="test_payment_id",
            description="Test payment"
        )
        
        payment = await payment_service.create_payment(payment_data)
        
        # Update the payment
        update_data = PaymentUpdate(
            status="completed",
            description="Updated payment description"
        )
        
        updated_payment = await payment_service.update_payment(payment.id, update_data)
        
        assert updated_payment.status == update_data.status
        assert updated_payment.description == update_data.description
        assert updated_payment.amount == payment.amount  # Unchanged
        assert updated_payment.currency == payment.currency  # Unchanged
    
    @pytest.mark.asyncio
    async def test_delete_payment(self, db: AsyncSession):
        """Test deleting a payment."""
        payment_service = PaymentService(db)
        
        # Create a payment
        payment_data = PaymentCreate(
            user_id=1,
            amount=10.00,
            currency="USD",
            status="pending",
            payment_method="stripe",
            payment_id="test_payment_id",
            description="Test payment"
        )
        
        payment = await payment_service.create_payment(payment_data)
        
        # Delete the payment
        await payment_service.delete_payment(payment.id)
        
        # Verify payment is deleted
        deleted_payment = await payment_service.get_payment(payment.id)
        assert deleted_payment is None

class TestSubscription:
    """Test subscription operations."""
    
    @pytest.mark.asyncio
    async def test_create_subscription(self, db: AsyncSession):
        """Test creating a new subscription."""
        payment_service = PaymentService(db)
        subscription_data = SubscriptionCreate(
            user_id=1,
            plan_id=1,
            status="active",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=30),
            auto_renew=True,
            payment_id="test_payment_id"
        )
        
        subscription = await payment_service.create_subscription(subscription_data)
        
        assert subscription.user_id == subscription_data.user_id
        assert subscription.plan_id == subscription_data.plan_id
        assert subscription.status == subscription_data.status
        assert subscription.start_date == subscription_data.start_date
        assert subscription.end_date == subscription_data.end_date
        assert subscription.auto_renew == subscription_data.auto_renew
        assert subscription.payment_id == subscription_data.payment_id
        assert subscription.id is not None
    
    @pytest.mark.asyncio
    async def test_get_subscriptions(self, db: AsyncSession):
        """Test getting list of subscriptions."""
        payment_service = PaymentService(db)
        
        # Create multiple subscriptions
        subscription_data1 = SubscriptionCreate(
            user_id=1,
            plan_id=1,
            status="active",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=30),
            auto_renew=True,
            payment_id="test_payment_id_1"
        )
        
        subscription_data2 = SubscriptionCreate(
            user_id=1,
            plan_id=2,
            status="cancelled",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=30),
            auto_renew=False,
            payment_id="test_payment_id_2"
        )
        
        await payment_service.create_subscription(subscription_data1)
        await payment_service.create_subscription(subscription_data2)
        
        subscriptions = await payment_service.get_subscriptions(user_id=1)
        assert len(subscriptions) == 2
        assert any(s.plan_id == 1 for s in subscriptions)
        assert any(s.plan_id == 2 for s in subscriptions)
    
    @pytest.mark.asyncio
    async def test_update_subscription(self, db: AsyncSession):
        """Test updating a subscription."""
        payment_service = PaymentService(db)
        
        # Create a subscription
        subscription_data = SubscriptionCreate(
            user_id=1,
            plan_id=1,
            status="active",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=30),
            auto_renew=True,
            payment_id="test_payment_id"
        )
        
        subscription = await payment_service.create_subscription(subscription_data)
        
        # Update the subscription
        update_data = SubscriptionUpdate(
            status="cancelled",
            auto_renew=False
        )
        
        updated_subscription = await payment_service.update_subscription(subscription.id, update_data)
        
        assert updated_subscription.status == update_data.status
        assert updated_subscription.auto_renew == update_data.auto_renew
        assert updated_subscription.plan_id == subscription.plan_id  # Unchanged
        assert updated_subscription.start_date == subscription.start_date  # Unchanged
    
    @pytest.mark.asyncio
    async def test_delete_subscription(self, db: AsyncSession):
        """Test deleting a subscription."""
        payment_service = PaymentService(db)
        
        # Create a subscription
        subscription_data = SubscriptionCreate(
            user_id=1,
            plan_id=1,
            status="active",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=30),
            auto_renew=True,
            payment_id="test_payment_id"
        )
        
        subscription = await payment_service.create_subscription(subscription_data)
        
        # Delete the subscription
        await payment_service.delete_subscription(subscription.id)
        
        # Verify subscription is deleted
        deleted_subscription = await payment_service.get_subscription(subscription.id)
        assert deleted_subscription is None 