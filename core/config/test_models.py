import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.vpn import VPNConfig, VPNSubscription
from app.models.payment import Payment, PaymentStatus
from app.tests.utils import create_test_user

@pytest.mark.asyncio
class TestUserModel:
    async def test_create_user(self, db_session: AsyncSession):
        """Test user model creation."""
        user = User(
            email="test@example.com",
            full_name="Test User",
            phone="+989123456789",
            hashed_password="hashed_password",
            is_active=True,
            is_admin=False
        )
        
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert user.phone == "+989123456789"
        assert user.is_active is True
        assert user.is_admin is False
        assert user.created_at is not None
        assert user.updated_at is not None

    async def test_update_user(self, db_session: AsyncSession):
        """Test user model update."""
        user = User(
            email="test@example.com",
            full_name="Test User",
            phone="+989123456789",
            hashed_password="hashed_password",
            is_active=True,
            is_admin=False
        )
        
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        # Update user
        user.full_name = "Updated Name"
        user.phone = "+989876543210"
        await db_session.commit()
        await db_session.refresh(user)
        
        assert user.full_name == "Updated Name"
        assert user.phone == "+989876543210"
        assert user.updated_at > user.created_at

    async def test_user_relationships(self, db_session: AsyncSession):
        """Test user model relationships."""
        user = await create_test_user(db_session)
        
        # Create VPN config
        vpn_config = VPNConfig(
            user_id=user.id,
            server_location="US",
            protocol="wireguard",
            port=51820,
            is_active=True
        )
        db_session.add(vpn_config)
        await db_session.commit()
        
        # Create subscription
        subscription = VPNSubscription(
            user_id=user.id,
            plan_type="premium",
            duration_days=30,
            start_date=datetime.utcnow(),
            is_active=True
        )
        db_session.add(subscription)
        await db_session.commit()
        
        # Create payment
        payment = Payment(
            user_id=user.id,
            amount=29.99,
            currency="USD",
            payment_method="crypto",
            status=PaymentStatus.PENDING
        )
        db_session.add(payment)
        await db_session.commit()
        
        # Refresh user to load relationships
        await db_session.refresh(user)
        
        assert len(user.vpn_configs) == 1
        assert len(user.subscriptions) == 1
        assert len(user.payments) == 1

@pytest.mark.asyncio
class TestVPNConfigModel:
    async def test_create_vpn_config(self, db_session: AsyncSession):
        """Test VPN config model creation."""
        user = await create_test_user(db_session)
        
        vpn_config = VPNConfig(
            user_id=user.id,
            server_location="US",
            protocol="wireguard",
            port=51820,
            is_active=True
        )
        
        db_session.add(vpn_config)
        await db_session.commit()
        await db_session.refresh(vpn_config)
        
        assert vpn_config.id is not None
        assert vpn_config.user_id == user.id
        assert vpn_config.server_location == "US"
        assert vpn_config.protocol == "wireguard"
        assert vpn_config.port == 51820
        assert vpn_config.is_active is True
        assert vpn_config.created_at is not None
        assert vpn_config.updated_at is not None

    async def test_update_vpn_config(self, db_session: AsyncSession):
        """Test VPN config model update."""
        user = await create_test_user(db_session)
        
        vpn_config = VPNConfig(
            user_id=user.id,
            server_location="US",
            protocol="wireguard",
            port=51820,
            is_active=True
        )
        
        db_session.add(vpn_config)
        await db_session.commit()
        await db_session.refresh(vpn_config)
        
        # Update config
        vpn_config.server_location = "UK"
        vpn_config.port = 51821
        await db_session.commit()
        await db_session.refresh(vpn_config)
        
        assert vpn_config.server_location == "UK"
        assert vpn_config.port == 51821
        assert vpn_config.protocol == "wireguard"  # Unchanged
        assert vpn_config.updated_at > vpn_config.created_at

@pytest.mark.asyncio
class TestVPNSubscriptionModel:
    async def test_create_subscription(self, db_session: AsyncSession):
        """Test subscription model creation."""
        user = await create_test_user(db_session)
        
        subscription = VPNSubscription(
            user_id=user.id,
            plan_type="premium",
            duration_days=30,
            start_date=datetime.utcnow(),
            is_active=True
        )
        
        db_session.add(subscription)
        await db_session.commit()
        await db_session.refresh(subscription)
        
        assert subscription.id is not None
        assert subscription.user_id == user.id
        assert subscription.plan_type == "premium"
        assert subscription.duration_days == 30
        assert subscription.is_active is True
        assert subscription.created_at is not None
        assert subscription.updated_at is not None

    async def test_subscription_dates(self, db_session: AsyncSession):
        """Test subscription date calculations."""
        user = await create_test_user(db_session)
        start_date = datetime.utcnow()
        
        subscription = VPNSubscription(
            user_id=user.id,
            plan_type="premium",
            duration_days=30,
            start_date=start_date,
            is_active=True
        )
        
        db_session.add(subscription)
        await db_session.commit()
        await db_session.refresh(subscription)
        
        expected_end_date = start_date + timedelta(days=30)
        assert subscription.end_date.date() == expected_end_date.date()
        assert subscription.is_active is True

@pytest.mark.asyncio
class TestPaymentModel:
    async def test_create_payment(self, db_session: AsyncSession):
        """Test payment model creation."""
        user = await create_test_user(db_session)
        
        payment = Payment(
            user_id=user.id,
            amount=29.99,
            currency="USD",
            payment_method="crypto",
            status=PaymentStatus.PENDING
        )
        
        db_session.add(payment)
        await db_session.commit()
        await db_session.refresh(payment)
        
        assert payment.id is not None
        assert payment.user_id == user.id
        assert payment.amount == 29.99
        assert payment.currency == "USD"
        assert payment.payment_method == "crypto"
        assert payment.status == PaymentStatus.PENDING
        assert payment.created_at is not None
        assert payment.updated_at is not None

    async def test_payment_status_transitions(self, db_session: AsyncSession):
        """Test payment status transitions."""
        user = await create_test_user(db_session)
        
        payment = Payment(
            user_id=user.id,
            amount=29.99,
            currency="USD",
            payment_method="crypto",
            status=PaymentStatus.PENDING
        )
        
        db_session.add(payment)
        await db_session.commit()
        await db_session.refresh(payment)
        
        # Update to completed
        payment.status = PaymentStatus.COMPLETED
        payment.completed_at = datetime.utcnow()
        await db_session.commit()
        await db_session.refresh(payment)
        
        assert payment.status == PaymentStatus.COMPLETED
        assert payment.completed_at is not None
        
        # Update to failed
        payment.status = PaymentStatus.FAILED
        payment.failed_at = datetime.utcnow()
        await db_session.commit()
        await db_session.refresh(payment)
        
        assert payment.status == PaymentStatus.FAILED
        assert payment.failed_at is not None 