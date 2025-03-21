"""
Test utilities for the application.
"""
import asyncio
from typing import Any, Dict, Generator, Optional
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.main import app
from app.models.user import User
from app.models.vpn import VPNServer, VPNAccount
from app.models.subscription import Subscription, SubscriptionPlan
from app.models.payment import Payment, PaymentTransaction
from app.models.telegram import TelegramUser, TelegramChat
from app.schemas.user import UserCreate
from app.schemas.vpn import VPNServerCreate, VPNAccountCreate
from app.schemas.subscription import SubscriptionCreate, SubscriptionPlanCreate
from app.schemas.payment import PaymentCreate, PaymentTransactionCreate
from app.schemas.telegram import TelegramUserCreate, TelegramChatCreate

from tests.conftest.base_test import BaseTestCase

class TestUtils(BaseTestCase):
    """Test utilities class."""

    @pytest.fixture
    async def client(self) -> Generator[AsyncClient, None, None]:
        """Fixture for creating an async HTTP client."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client

    async def make_request(
        self,
        client: AsyncClient,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        expected_status: int = 200
    ) -> Dict[str, Any]:
        """Make an HTTP request and check the response status."""
        response = await client.request(
            method=method,
            url=url,
            headers=headers,
            json=json,
            params=params
        )
        assert response.status_code == expected_status
        return response.json()

    async def create_test_data(
        self,
        db_session: AsyncSession,
        user_data: Optional[Dict[str, Any]] = None,
        server_data: Optional[Dict[str, Any]] = None,
        account_data: Optional[Dict[str, Any]] = None,
        plan_data: Optional[Dict[str, Any]] = None,
        subscription_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create test data for all models."""
        from app.services.user import UserService
        from app.services.vpn import VPNService
        from app.services.subscription import SubscriptionService
        from app.services.payment import PaymentService
        from app.services.telegram import TelegramBotService

        user_service = UserService(db_session)
        vpn_service = VPNService(db_session)
        subscription_service = SubscriptionService(db_session)
        payment_service = PaymentService(db_session)
        telegram_service = TelegramBotService(db_session)

        # Create test user
        if user_data is None:
            user_data = {
                "phone": "+989123456789",
                "password": "test_password123",
                "email": "test@example.com",
                "full_name": "Test User"
            }
        user = await user_service.create_user(UserCreate(**user_data))

        # Create test VPN server
        if server_data is None:
            server_data = {
                "host": "test.vpn.example.com",
                "port": 443,
                "protocol": "tls",
                "bandwidth_limit": 1000,
                "location": "US",
                "is_active": True
            }
        server = await vpn_service.create_server(VPNServerCreate(**server_data))

        # Create test VPN account
        if account_data is None:
            account_data = {
                "user_id": user.id,
                "server_id": server.id,
                "username": "test_vpn_user",
                "password": "test_password123"
            }
        account = await vpn_service.create_account(VPNAccountCreate(**account_data))

        # Create test subscription plan
        if plan_data is None:
            plan_data = {
                "name": "Premium",
                "description": "Premium VPN plan",
                "price": 9.99,
                "duration_days": 30,
                "features": ["Unlimited bandwidth", "All locations", "Priority support"],
                "is_active": True
            }
        plan = await subscription_service.create_plan(SubscriptionPlanCreate(**plan_data))

        # Create test subscription
        if subscription_data is None:
            subscription_data = {
                "user_id": user.id,
                "plan_id": plan.id,
                "start_date": datetime.utcnow(),
                "end_date": datetime.utcnow() + timedelta(days=30),
                "is_active": True
            }
        """Create test data with optional overrides."""
        from app.models.user import User
        from app.models.server import Server
        from app.models.vpn_account import VPNAccount
        from app.models.subscription import SubscriptionPlan, Subscription
        from app.core.security import get_password_hash
        
        # Create user
        if user_data is None:
            user_data = {
                "phone": self.settings.TEST_USER_PHONE,
                "email": self.settings.TEST_USER_EMAIL,
                "hashed_password": get_password_hash(self.settings.TEST_USER_PASSWORD),
                "is_active": True,
                "is_superuser": False,
            }
        
        user = User(**user_data)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        
        # Create server
        if server_data is None:
            server_data = {
                "host": self.settings.TEST_SERVER_HOST,
                "port": self.settings.TEST_SERVER_PORT,
                "protocol": self.settings.TEST_SERVER_PROTOCOL,
                "is_active": True,
                "location": "IR",
                "load": 0,
                "max_users": 1000,
                "current_users": 0,
                "bandwidth_limit": 1000000,  # 1TB
                "traffic_used": 0,
                "last_check": None,
            }
        
        server = Server(**server_data)
        session.add(server)
        await session.commit()
        await session.refresh(server)
        
        # Create VPN account
        if account_data is None:
            account_data = {
                "user_id": user.id,
                "server_id": server.id,
                "username": f"test_user_{user.id}",
                "password": "test_password",
                "is_active": True,
                "expires_at": None,
                "traffic_limit": 100000,  # 100GB
                "traffic_used": 0,
                "last_connection": None,
            }
        
        account = VPNAccount(**account_data)
        session.add(account)
        await session.commit()
        await session.refresh(account)
        
        # Create subscription plan
        if plan_data is None:
            plan_data = {
                "name": "Test Plan",
                "description": "Test subscription plan",
                "price": 1000,
                "duration_days": 30,
                "traffic_limit": 100000,  # 100GB
                "is_active": True,
                "features": ["feature1", "feature2"],
            }
        
        plan = SubscriptionPlan(**plan_data)
        session.add(plan)
        await session.commit()
        await session.refresh(plan)
        
        # Create subscription
        if subscription_data is None:
            subscription_data = {
                "user_id": user.id,
                "plan_id": plan.id,
                "start_date": None,
                "end_date": None,
                "is_active": False,
                "auto_renew": False,
                "payment_status": "pending",
            }
        
        subscription = Subscription(**subscription_data)
        session.add(subscription)
        await session.commit()
        await session.refresh(subscription)
        
        return {
            "user": user,
            "server": server,
            "account": account,
            "plan": plan,
            "subscription": subscription,
        }
    
    async def wait_for_condition(
        self,
        condition_func: callable,
        timeout: float = 5.0,
        interval: float = 0.1,
    ) -> bool:
        """Wait for a condition to be met."""
        start_time = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start_time < timeout:
            if await condition_func():
                return True
            await asyncio.sleep(interval)
        return False 