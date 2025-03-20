"""
Test fixtures for common test data.
"""
from typing import Dict, Any, Generator
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from tests.conftest.base_test import BaseTestCase
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

class TestFixtures(BaseTestCase):
    """Test fixtures for common test data."""
    
    @pytest.fixture
    async def test_user(self, db_session: AsyncSession) -> Dict[str, Any]:
        """Create a test user."""
        return await self.create_test_user(db_session)
    
    @pytest.fixture
    async def test_admin(self, db_session: AsyncSession) -> Dict[str, Any]:
        """Create a test admin user."""
        return await self.create_test_admin(db_session)
    
    @pytest.fixture
    async def test_user_token(self, db_session: AsyncSession, test_user: Dict[str, Any]) -> str:
        """Get test user JWT token."""
        return await self.get_test_token(db_session, test_user)
    
    @pytest.fixture
    async def test_admin_token(self, db_session: AsyncSession, test_admin: Dict[str, Any]) -> str:
        """Get test admin JWT token."""
        return await self.get_test_token(db_session, test_admin)
    
    @pytest.fixture
    async def test_user_headers(self, test_user_token: str) -> Dict[str, str]:
        """Get test user headers."""
        return await self.get_test_headers(test_user_token)
    
    @pytest.fixture
    async def test_admin_headers(self, test_admin_token: str) -> Dict[str, str]:
        """Get test admin headers."""
        return await self.get_test_headers(test_admin_token)
    
    @pytest.fixture
    async def test_vpn_server(self, db_session: AsyncSession) -> Dict[str, Any]:
        """Create a test VPN server."""
        from app.models.server import Server
        
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
        db_session.add(server)
        await db_session.commit()
        await db_session.refresh(server)
        
        return server_data
    
    @pytest.fixture
    async def test_vpn_account(self, db_session: AsyncSession, test_user: Dict[str, Any], test_vpn_server: Dict[str, Any]) -> Dict[str, Any]:
        """Create a test VPN account."""
        from app.models.vpn_account import VPNAccount
        
        account_data = {
            "user_id": test_user["id"],
            "server_id": test_vpn_server["id"],
            "username": f"test_user_{test_user['id']}",
            "password": "test_password",
            "is_active": True,
            "expires_at": None,
            "traffic_limit": 100000,  # 100GB
            "traffic_used": 0,
            "last_connection": None,
        }
        
        account = VPNAccount(**account_data)
        db_session.add(account)
        await db_session.commit()
        await db_session.refresh(account)
        
        return account_data
    
    @pytest.fixture
    async def test_subscription_plan(self, db_session: AsyncSession) -> Dict[str, Any]:
        """Create a test subscription plan."""
        from app.models.subscription import SubscriptionPlan
        
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
        db_session.add(plan)
        await db_session.commit()
        await db_session.refresh(plan)
        
        return plan_data
    
    @pytest.fixture
    async def test_subscription(self, db_session: AsyncSession, test_user: Dict[str, Any], test_subscription_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Create a test subscription."""
        from app.models.subscription import Subscription
        
        subscription_data = {
            "user_id": test_user["id"],
            "plan_id": test_subscription_plan["id"],
            "start_date": None,
            "end_date": None,
            "is_active": False,
            "auto_renew": False,
            "payment_status": "pending",
        }
        
        subscription = Subscription(**subscription_data)
        db_session.add(subscription)
        await db_session.commit()
        await db_session.refresh(subscription)
        
        return subscription_data 