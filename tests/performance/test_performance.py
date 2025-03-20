"""
Performance tests for the application.
"""
import pytest
import asyncio
import time
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.vpn import VPNServer, VPNAccount
from app.models.subscription import Subscription, SubscriptionPlan
from app.models.payment import Payment, PaymentTransaction
from app.models.telegram import TelegramUser, TelegramChat
from app.services.user_service import UserService
from app.services.vpn_service import VPNService
from app.services.subscription_service import SubscriptionService
from app.services.payment_service import PaymentService
from app.services.telegram_bot_service import TelegramBotService

pytestmark = pytest.mark.asyncio

class TestUserServicePerformance:
    """Performance test cases for UserService."""

    async def test_user_creation_performance(
        self,
        db_session: AsyncSession
    ):
        """Test performance of creating multiple users."""
        user_service = UserService(db_session)
        start_time = time.time()
        num_users = 100

        # Create users concurrently
        tasks = []
        for i in range(num_users):
            user_data = {
                "phone": f"+9891234567{i:03d}",
                "password": "test_password123",
                "email": f"test{i:03d}@example.com",
                "full_name": f"Test User {i:03d}"
            }
            tasks.append(user_service.create_user(user_data))

        await asyncio.gather(*tasks)
        end_time = time.time()
        duration = end_time - start_time

        # Assert performance metrics
        assert duration < 5.0  # Should complete within 5 seconds
        print(f"Created {num_users} users in {duration:.2f} seconds")

    async def test_user_query_performance(
        self,
        db_session: AsyncSession,
        test_users: list[User]
    ):
        """Test performance of querying multiple users."""
        user_service = UserService(db_session)
        start_time = time.time()
        num_queries = 1000

        # Query users concurrently
        tasks = []
        for _ in range(num_queries):
            user_id = test_users[0].id
            tasks.append(user_service.get_user_by_id(user_id))

        await asyncio.gather(*tasks)
        end_time = time.time()
        duration = end_time - start_time

        # Assert performance metrics
        assert duration < 2.0  # Should complete within 2 seconds
        print(f"Performed {num_queries} user queries in {duration:.2f} seconds")

class TestVPNServicePerformance:
    """Performance test cases for VPNService."""

    async def test_vpn_account_creation_performance(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_vpn_server: VPNServer
    ):
        """Test performance of creating multiple VPN accounts."""
        vpn_service = VPNService(db_session)
        start_time = time.time()
        num_accounts = 50

        # Create VPN accounts concurrently
        tasks = []
        for i in range(num_accounts):
            account_data = {
                "user_id": test_user.id,
                "server_id": test_vpn_server.id,
                "username": f"test_vpn_user_{i:03d}",
                "password": "test_password123"
            }
            tasks.append(vpn_service.create_account(account_data))

        await asyncio.gather(*tasks)
        end_time = time.time()
        duration = end_time - start_time

        # Assert performance metrics
        assert duration < 3.0  # Should complete within 3 seconds
        print(f"Created {num_accounts} VPN accounts in {duration:.2f} seconds")

    async def test_vpn_account_query_performance(
        self,
        db_session: AsyncSession,
        test_vpn_accounts: list[VPNAccount]
    ):
        """Test performance of querying multiple VPN accounts."""
        vpn_service = VPNService(db_session)
        start_time = time.time()
        num_queries = 1000

        # Query VPN accounts concurrently
        tasks = []
        for _ in range(num_queries):
            account_id = test_vpn_accounts[0].id
            tasks.append(vpn_service.get_account(account_id))

        await asyncio.gather(*tasks)
        end_time = time.time()
        duration = end_time - start_time

        # Assert performance metrics
        assert duration < 2.0  # Should complete within 2 seconds
        print(f"Performed {num_queries} VPN account queries in {duration:.2f} seconds")

class TestSubscriptionServicePerformance:
    """Performance test cases for SubscriptionService."""

    async def test_subscription_creation_performance(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_subscription_plan: SubscriptionPlan
    ):
        """Test performance of creating multiple subscriptions."""
        subscription_service = SubscriptionService(db_session)
        start_time = time.time()
        num_subscriptions = 50

        # Create subscriptions concurrently
        tasks = []
        for i in range(num_subscriptions):
            subscription_data = {
                "user_id": test_user.id,
                "plan_id": test_subscription_plan.id,
                "start_date": datetime.utcnow(),
                "end_date": datetime.utcnow() + timedelta(days=30),
                "is_active": True
            }
            tasks.append(subscription_service.create_subscription(subscription_data))

        await asyncio.gather(*tasks)
        end_time = time.time()
        duration = end_time - start_time

        # Assert performance metrics
        assert duration < 3.0  # Should complete within 3 seconds
        print(f"Created {num_subscriptions} subscriptions in {duration:.2f} seconds")

    async def test_subscription_query_performance(
        self,
        db_session: AsyncSession,
        test_subscriptions: list[Subscription]
    ):
        """Test performance of querying multiple subscriptions."""
        subscription_service = SubscriptionService(db_session)
        start_time = time.time()
        num_queries = 1000

        # Query subscriptions concurrently
        tasks = []
        for _ in range(num_queries):
            subscription_id = test_subscriptions[0].id
            tasks.append(subscription_service.get_subscription(subscription_id))

        await asyncio.gather(*tasks)
        end_time = time.time()
        duration = end_time - start_time

        # Assert performance metrics
        assert duration < 2.0  # Should complete within 2 seconds
        print(f"Performed {num_queries} subscription queries in {duration:.2f} seconds")

class TestPaymentServicePerformance:
    """Performance test cases for PaymentService."""

    async def test_payment_creation_performance(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_subscription_plan: SubscriptionPlan
    ):
        """Test performance of creating multiple payments."""
        payment_service = PaymentService(db_session)
        start_time = time.time()
        num_payments = 50

        # Create payments concurrently
        tasks = []
        for i in range(num_payments):
            payment_data = {
                "user_id": test_user.id,
                "plan_id": test_subscription_plan.id,
                "amount": test_subscription_plan.price,
                "currency": "USD",
                "payment_method": "credit_card",
                "status": "pending"
            }
            tasks.append(payment_service.create_payment(payment_data))

        await asyncio.gather(*tasks)
        end_time = time.time()
        duration = end_time - start_time

        # Assert performance metrics
        assert duration < 3.0  # Should complete within 3 seconds
        print(f"Created {num_payments} payments in {duration:.2f} seconds")

    async def test_payment_query_performance(
        self,
        db_session: AsyncSession,
        test_payments: list[Payment]
    ):
        """Test performance of querying multiple payments."""
        payment_service = PaymentService(db_session)
        start_time = time.time()
        num_queries = 1000

        # Query payments concurrently
        tasks = []
        for _ in range(num_queries):
            payment_id = test_payments[0].id
            tasks.append(payment_service.get_payment(payment_id))

        await asyncio.gather(*tasks)
        end_time = time.time()
        duration = end_time - start_time

        # Assert performance metrics
        assert duration < 2.0  # Should complete within 2 seconds
        print(f"Performed {num_queries} payment queries in {duration:.2f} seconds")

class TestTelegramServicePerformance:
    """Performance test cases for TelegramBotService."""

    async def test_telegram_message_performance(
        self,
        db_session: AsyncSession,
        test_telegram_chat: TelegramChat
    ):
        """Test performance of sending multiple Telegram messages."""
        telegram_service = TelegramBotService(db_session)
        start_time = time.time()
        num_messages = 50

        # Send messages concurrently
        tasks = []
        for i in range(num_messages):
            message = f"Test message {i:03d}"
            tasks.append(telegram_service.send_message(test_telegram_chat.chat_id, message))

        await asyncio.gather(*tasks)
        end_time = time.time()
        duration = end_time - start_time

        # Assert performance metrics
        assert duration < 5.0  # Should complete within 5 seconds
        print(f"Sent {num_messages} Telegram messages in {duration:.2f} seconds")

    async def test_telegram_user_query_performance(
        self,
        db_session: AsyncSession,
        test_telegram_users: list[TelegramUser]
    ):
        """Test performance of querying multiple Telegram users."""
        telegram_service = TelegramBotService(db_session)
        start_time = time.time()
        num_queries = 1000

        # Query Telegram users concurrently
        tasks = []
        for _ in range(num_queries):
            user_id = test_telegram_users[0].id
            tasks.append(telegram_service.get_telegram_user(user_id))

        await asyncio.gather(*tasks)
        end_time = time.time()
        duration = end_time - start_time

        # Assert performance metrics
        assert duration < 2.0  # Should complete within 2 seconds
        print(f"Performed {num_queries} Telegram user queries in {duration:.2f} seconds") 