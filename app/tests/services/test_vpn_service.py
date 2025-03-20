import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.vpn_service import VPNService
from app.models.vpn import VPNConfig, VPNSubscription
from app.tests.utils import create_test_user

@pytest.mark.asyncio
class TestVPNService:
    async def test_create_vpn_config(self, db_session: AsyncSession):
        """Test VPN configuration creation."""
        test_user = await create_test_user(db_session)
        vpn_service = VPNService(db_session)
        
        config = await vpn_service.create_vpn_config(
            user_id=test_user.id,
            server_location="US",
            protocol="wireguard",
            port=51820
        )
        
        assert config.user_id == test_user.id
        assert config.server_location == "US"
        assert config.protocol == "wireguard"
        assert config.port == 51820
        assert config.is_active is True

    async def test_get_user_vpn_config(self, db_session: AsyncSession):
        """Test retrieving user's VPN configuration."""
        test_user = await create_test_user(db_session)
        vpn_service = VPNService(db_session)
        
        # Create a VPN config first
        await vpn_service.create_vpn_config(
            user_id=test_user.id,
            server_location="US",
            protocol="wireguard",
            port=51820
        )
        
        config = await vpn_service.get_user_vpn_config(test_user.id)
        
        assert config is not None
        assert config.user_id == test_user.id
        assert config.server_location == "US"

    async def test_update_vpn_config(self, db_session: AsyncSession):
        """Test updating VPN configuration."""
        test_user = await create_test_user(db_session)
        vpn_service = VPNService(db_session)
        
        # Create initial config
        config = await vpn_service.create_vpn_config(
            user_id=test_user.id,
            server_location="US",
            protocol="wireguard",
            port=51820
        )
        
        # Update config
        updated_config = await vpn_service.update_vpn_config(
            config_id=config.id,
            server_location="UK",
            port=51821
        )
        
        assert updated_config.server_location == "UK"
        assert updated_config.port == 51821
        assert updated_config.protocol == "wireguard"  # Unchanged

    async def test_deactivate_vpn_config(self, db_session: AsyncSession):
        """Test deactivating VPN configuration."""
        test_user = await create_test_user(db_session)
        vpn_service = VPNService(db_session)
        
        config = await vpn_service.create_vpn_config(
            user_id=test_user.id,
            server_location="US",
            protocol="wireguard",
            port=51820
        )
        
        deactivated_config = await vpn_service.deactivate_vpn_config(config.id)
        
        assert deactivated_config.is_active is False

    async def test_create_subscription(self, db_session: AsyncSession):
        """Test VPN subscription creation."""
        test_user = await create_test_user(db_session)
        vpn_service = VPNService(db_session)
        
        subscription = await vpn_service.create_subscription(
            user_id=test_user.id,
            plan_type="premium",
            duration_days=30,
            start_date=datetime.utcnow()
        )
        
        assert subscription.user_id == test_user.id
        assert subscription.plan_type == "premium"
        assert subscription.duration_days == 30
        assert subscription.is_active is True

    async def test_get_active_subscription(self, db_session: AsyncSession):
        """Test retrieving active subscription."""
        test_user = await create_test_user(db_session)
        vpn_service = VPNService(db_session)
        
        # Create a subscription
        await vpn_service.create_subscription(
            user_id=test_user.id,
            plan_type="premium",
            duration_days=30,
            start_date=datetime.utcnow()
        )
        
        subscription = await vpn_service.get_active_subscription(test_user.id)
        
        assert subscription is not None
        assert subscription.user_id == test_user.id
        assert subscription.is_active is True

    async def test_extend_subscription(self, db_session: AsyncSession):
        """Test extending subscription duration."""
        test_user = await create_test_user(db_session)
        vpn_service = VPNService(db_session)
        
        # Create initial subscription
        subscription = await vpn_service.create_subscription(
            user_id=test_user.id,
            plan_type="premium",
            duration_days=30,
            start_date=datetime.utcnow()
        )
        
        # Extend subscription
        extended_subscription = await vpn_service.extend_subscription(
            subscription_id=subscription.id,
            additional_days=30
        )
        
        assert extended_subscription.duration_days == 60

    async def test_cancel_subscription(self, db_session: AsyncSession):
        """Test subscription cancellation."""
        test_user = await create_test_user(db_session)
        vpn_service = VPNService(db_session)
        
        subscription = await vpn_service.create_subscription(
            user_id=test_user.id,
            plan_type="premium",
            duration_days=30,
            start_date=datetime.utcnow()
        )
        
        cancelled_subscription = await vpn_service.cancel_subscription(subscription.id)
        
        assert cancelled_subscription.is_active is False 