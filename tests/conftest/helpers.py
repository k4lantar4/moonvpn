"""
Test helpers for the application.
"""
import asyncio
from typing import Any, Dict, Generator, Optional, List
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

class TestHelpers(BaseTestCase):
    """Test helpers class."""

    @pytest.fixture
    async def client(self) -> Generator[AsyncClient, None, None]:
        """Fixture for creating an async HTTP client."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client

    async def create_test_user(
        self,
        db_session: AsyncSession,
        user_data: Optional[Dict[str, Any]] = None
    ) -> User:
        """Create a test user."""
        from app.services.user import UserService

        user_service = UserService(db_session)
        if user_data is None:
            user_data = {
                "phone": "+989123456789",
                "password": "test_password123",
                "email": "test@example.com",
                "full_name": "Test User"
            }
        user = await user_service.create_user(UserCreate(**user_data))
        return user

    async def create_test_users(
        self,
        db_session: AsyncSession,
        count: int = 5,
        user_data: Optional[Dict[str, Any]] = None
    ) -> List[User]:
        """Create multiple test users."""
        users = []
        for i in range(count):
            if user_data is None:
                user_data = {
                    "phone": f"+9891234567{i:03d}",
                    "password": "test_password123",
                    "email": f"test{i:03d}@example.com",
                    "full_name": f"Test User {i:03d}"
                }
            user = await self.create_test_user(db_session, user_data)
            users.append(user)
        return users

    async def create_test_vpn_server(
        self,
        db_session: AsyncSession,
        server_data: Optional[Dict[str, Any]] = None
    ) -> VPNServer:
        """Create a test VPN server."""
        from app.services.vpn import VPNService

        vpn_service = VPNService(db_session)
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
        return server

    async def create_test_vpn_servers(
        self,
        db_session: AsyncSession,
        count: int = 5,
        server_data: Optional[Dict[str, Any]] = None
    ) -> List[VPNServer]:
        """Create multiple test VPN servers."""
        servers = []
        for i in range(count):
            if server_data is None:
                server_data = {
                    "host": f"test{i:03d}.vpn.example.com",
                    "port": 443 + i,
                    "protocol": "tls",
                    "bandwidth_limit": 1000,
                    "location": "US",
                    "is_active": True
                }
            server = await self.create_test_vpn_server(db_session, server_data)
            servers.append(server)
        return servers

    async def create_test_vpn_account(
        self,
        db_session: AsyncSession,
        user: User,
        server: VPNServer,
        account_data: Optional[Dict[str, Any]] = None
    ) -> VPNAccount:
        """Create a test VPN account."""
        from app.services.vpn import VPNService

        vpn_service = VPNService(db_session)
        if account_data is None:
            account_data = {
                "user_id": user.id,
                "server_id": server.id,
                "username": "test_vpn_user",
                "password": "test_password123"
            }
        account = await vpn_service.create_account(VPNAccountCreate(**account_data))
        return account

    async def create_test_vpn_accounts(
        self,
        db_session: AsyncSession,
        user: User,
        server: VPNServer,
        count: int = 5,
        account_data: Optional[Dict[str, Any]] = None
    ) -> List[VPNAccount]:
        """Create multiple test VPN accounts."""
        accounts = []
        for i in range(count):
            if account_data is None:
                account_data = {
                    "user_id": user.id,
                    "server_id": server.id,
                    "username": f"test_vpn_user_{i:03d}",
                    "password": "test_password123"
                }
            account = await self.create_test_vpn_account(db_session, user, server, account_data)
            accounts.append(account)
        return accounts

    async def create_test_subscription_plan(
        self,
        db_session: AsyncSession,
        plan_data: Optional[Dict[str, Any]] = None
    ) -> SubscriptionPlan:
        """Create a test subscription plan."""
        from app.services.subscription import SubscriptionService

        subscription_service = SubscriptionService(db_session)
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
        return plan

    async def create_test_subscription_plans(
        self,
        db_session: AsyncSession,
        count: int = 5,
        plan_data: Optional[Dict[str, Any]] = None
    ) -> List[SubscriptionPlan]:
        """Create multiple test subscription plans."""
        plans = []
        for i in range(count):
            if plan_data is None:
                plan_data = {
                    "name": f"Premium {i:03d}",
                    "description": f"Premium VPN plan {i:03d}",
                    "price": 9.99 + i,
                    "duration_days": 30,
                    "features": ["Unlimited bandwidth", "All locations", "Priority support"],
                    "is_active": True
                }
            plan = await self.create_test_subscription_plan(db_session, plan_data)
            plans.append(plan)
        return plans

    async def create_test_subscription(
        self,
        db_session: AsyncSession,
        user: User,
        plan: SubscriptionPlan,
        subscription_data: Optional[Dict[str, Any]] = None
    ) -> Subscription:
        """Create a test subscription."""
        from app.services.subscription import SubscriptionService

        subscription_service = SubscriptionService(db_session)
        if subscription_data is None:
            subscription_data = {
                "user_id": user.id,
                "plan_id": plan.id,
                "start_date": datetime.utcnow(),
                "end_date": datetime.utcnow() + timedelta(days=30),
                "is_active": True
            }
        subscription = await subscription_service.create_subscription(SubscriptionCreate(**subscription_data))
        return subscription

    async def create_test_subscriptions(
        self,
        db_session: AsyncSession,
        user: User,
        plan: SubscriptionPlan,
        count: int = 5,
        subscription_data: Optional[Dict[str, Any]] = None
    ) -> List[Subscription]:
        """Create multiple test subscriptions."""
        subscriptions = []
        for i in range(count):
            if subscription_data is None:
                subscription_data = {
                    "user_id": user.id,
                    "plan_id": plan.id,
                    "start_date": datetime.utcnow(),
                    "end_date": datetime.utcnow() + timedelta(days=30),
                    "is_active": True
                }
            subscription = await self.create_test_subscription(db_session, user, plan, subscription_data)
            subscriptions.append(subscription)
        return subscriptions

    async def create_test_payment(
        self,
        db_session: AsyncSession,
        user: User,
        plan: SubscriptionPlan,
        payment_data: Optional[Dict[str, Any]] = None
    ) -> Payment:
        """Create a test payment."""
        from app.services.payment import PaymentService

        payment_service = PaymentService(db_session)
        if payment_data is None:
            payment_data = {
                "user_id": user.id,
                "plan_id": plan.id,
                "amount": plan.price,
                "currency": "USD",
                "payment_method": "credit_card",
                "status": "pending"
            }
        payment = await payment_service.create_payment(PaymentCreate(**payment_data))
        return payment

    async def create_test_payments(
        self,
        db_session: AsyncSession,
        user: User,
        plan: SubscriptionPlan,
        count: int = 5,
        payment_data: Optional[Dict[str, Any]] = None
    ) -> List[Payment]:
        """Create multiple test payments."""
        payments = []
        for i in range(count):
            if payment_data is None:
                payment_data = {
                    "user_id": user.id,
                    "plan_id": plan.id,
                    "amount": plan.price,
                    "currency": "USD",
                    "payment_method": "credit_card",
                    "status": "pending"
                }
            payment = await self.create_test_payment(db_session, user, plan, payment_data)
            payments.append(payment)
        return payments

    async def create_test_payment_transaction(
        self,
        db_session: AsyncSession,
        payment: Payment,
        transaction_data: Optional[Dict[str, Any]] = None
    ) -> PaymentTransaction:
        """Create a test payment transaction."""
        from app.services.payment import PaymentService

        payment_service = PaymentService(db_session)
        if transaction_data is None:
            transaction_data = {
                "payment_id": payment.id,
                "transaction_id": "test_transaction_123",
                "amount": payment.amount,
                "currency": payment.currency,
                "status": "completed",
                "payment_method": payment.payment_method,
                "payment_date": datetime.utcnow()
            }
        transaction = await payment_service.create_transaction(PaymentTransactionCreate(**transaction_data))
        return transaction

    async def create_test_payment_transactions(
        self,
        db_session: AsyncSession,
        payment: Payment,
        count: int = 5,
        transaction_data: Optional[Dict[str, Any]] = None
    ) -> List[PaymentTransaction]:
        """Create multiple test payment transactions."""
        transactions = []
        for i in range(count):
            if transaction_data is None:
                transaction_data = {
                    "payment_id": payment.id,
                    "transaction_id": f"test_transaction_{i:03d}",
                    "amount": payment.amount,
                    "currency": payment.currency,
                    "status": "completed",
                    "payment_method": payment.payment_method,
                    "payment_date": datetime.utcnow()
                }
            transaction = await self.create_test_payment_transaction(db_session, payment, transaction_data)
            transactions.append(transaction)
        return transactions

    async def create_test_telegram_user(
        self,
        db_session: AsyncSession,
        user: User,
        telegram_user_data: Optional[Dict[str, Any]] = None
    ) -> TelegramUser:
        """Create a test Telegram user."""
        from app.services.telegram import TelegramBotService

        telegram_service = TelegramBotService(db_session)
        if telegram_user_data is None:
            telegram_user_data = {
                "user_id": user.id,
                "telegram_id": 123456789,
                "username": "test_user",
                "first_name": "Test",
                "last_name": "User",
                "language_code": "en",
                "is_active": True
            }
        telegram_user = await telegram_service.create_telegram_user(TelegramUserCreate(**telegram_user_data))
        return telegram_user

    async def create_test_telegram_users(
        self,
        db_session: AsyncSession,
        user: User,
        count: int = 5,
        telegram_user_data: Optional[Dict[str, Any]] = None
    ) -> List[TelegramUser]:
        """Create multiple test Telegram users."""
        telegram_users = []
        for i in range(count):
            if telegram_user_data is None:
                telegram_user_data = {
                    "user_id": user.id,
                    "telegram_id": 123456789 + i,
                    "username": f"test_user_{i:03d}",
                    "first_name": "Test",
                    "last_name": f"User {i:03d}",
                    "language_code": "en",
                    "is_active": True
                }
            telegram_user = await self.create_test_telegram_user(db_session, user, telegram_user_data)
            telegram_users.append(telegram_user)
        return telegram_users

    async def create_test_telegram_chat(
        self,
        db_session: AsyncSession,
        telegram_user: TelegramUser,
        chat_data: Optional[Dict[str, Any]] = None
    ) -> TelegramChat:
        """Create a test Telegram chat."""
        from app.services.telegram import TelegramBotService

        telegram_service = TelegramBotService(db_session)
        if chat_data is None:
            chat_data = {
                "telegram_user_id": telegram_user.id,
                "chat_id": 123456789,
                "chat_type": "private",
                "title": "Test Chat",
                "is_active": True
            }
        chat = await telegram_service.create_chat(TelegramChatCreate(**chat_data))
        return chat

    async def create_test_telegram_chats(
        self,
        db_session: AsyncSession,
        telegram_user: TelegramUser,
        count: int = 5,
        chat_data: Optional[Dict[str, Any]] = None
    ) -> List[TelegramChat]:
        """Create multiple test Telegram chats."""
        chats = []
        for i in range(count):
            if chat_data is None:
                chat_data = {
                    "telegram_user_id": telegram_user.id,
                    "chat_id": 123456789 + i,
                    "chat_type": "private",
                    "title": f"Test Chat {i:03d}",
                    "is_active": True
                }
            chat = await self.create_test_telegram_chat(db_session, telegram_user, chat_data)
            chats.append(chat)
        return chats

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

    async def wait_for_condition(
        self,
        condition_func: callable,
        timeout: float = 5.0,
        interval: float = 0.1
    ) -> bool:
        """Wait for a condition to be met."""
        start_time = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start_time < timeout:
            if await condition_func():
                return True
            await asyncio.sleep(interval)
        return False

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
        user = await self.create_test_user(db_session, user_data)
        server = await self.create_test_vpn_server(db_session, server_data)
        account = await self.create_test_vpn_account(db_session, user, server, account_data)
        plan = await self.create_test_subscription_plan(db_session, plan_data)
        subscription = await self.create_test_subscription(db_session, user, plan, subscription_data)
        payment = await self.create_test_payment(db_session, user, plan)
        transaction = await self.create_test_payment_transaction(db_session, payment)
        telegram_user = await self.create_test_telegram_user(db_session, user)
        chat = await self.create_test_telegram_chat(db_session, telegram_user)

        return {
            "user": user,
            "server": server,
            "account": account,
            "plan": plan,
            "subscription": subscription,
            "payment": payment,
            "transaction": transaction,
            "telegram_user": telegram_user,
            "chat": chat
        } 