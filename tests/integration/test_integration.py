"""
Integration tests for the application.
"""
import pytest
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

class TestUserSubscriptionFlow:
    """Test cases for user subscription flow."""

    async def test_complete_subscription_flow(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_subscription_plan: SubscriptionPlan
    ):
        """Test complete subscription flow from user registration to VPN access."""
        # Initialize services
        user_service = UserService(db_session)
        subscription_service = SubscriptionService(db_session)
        payment_service = PaymentService(db_session)
        vpn_service = VPNService(db_session)

        # 1. Create subscription
        subscription_data = {
            "user_id": test_user.id,
            "plan_id": test_subscription_plan.id,
            "start_date": datetime.utcnow(),
            "end_date": datetime.utcnow() + timedelta(days=30),
            "is_active": True
        }
        subscription = await subscription_service.create_subscription(subscription_data)
        assert subscription is not None
        assert subscription.user_id == test_user.id
        assert subscription.plan_id == test_subscription_plan.id

        # 2. Create payment
        payment_data = {
            "user_id": test_user.id,
            "plan_id": test_subscription_plan.id,
            "amount": test_subscription_plan.price,
            "currency": "USD",
            "payment_method": "credit_card",
            "status": "pending"
        }
        payment = await payment_service.create_payment(payment_data)
        assert payment is not None
        assert payment.user_id == test_user.id
        assert payment.plan_id == test_subscription_plan.id

        # 3. Process payment
        processed_payment = await payment_service.process_payment(
            payment.id,
            "test_transaction_123",
            "completed"
        )
        assert processed_payment.status == "completed"
        assert processed_payment.transaction_id == "test_transaction_123"

        # 4. Create VPN account
        vpn_server = await vpn_service.get_active_servers()
        assert len(vpn_server) > 0
        server = vpn_server[0]

        account_data = {
            "user_id": test_user.id,
            "server_id": server.id,
            "username": f"test_user_{test_user.id}",
            "password": "test_password123"
        }
        vpn_account = await vpn_service.create_account(account_data)
        assert vpn_account is not None
        assert vpn_account.user_id == test_user.id
        assert vpn_account.server_id == server.id

        # 5. Verify VPN access
        account = await vpn_service.get_account(vpn_account.id)
        assert account is not None
        assert account.is_active is True

class TestTelegramIntegration:
    """Test cases for Telegram integration."""

    async def test_telegram_user_flow(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """Test complete Telegram user flow."""
        # Initialize services
        telegram_service = TelegramBotService(db_session)
        vpn_service = VPNService(db_session)

        # 1. Create Telegram user
        telegram_user_data = {
            "user_id": test_user.id,
            "telegram_id": 123456789,
            "username": "test_user",
            "first_name": "Test",
            "last_name": "User",
            "language_code": "en",
            "is_active": True
        }
        telegram_user = await telegram_service.create_telegram_user(telegram_user_data)
        assert telegram_user is not None
        assert telegram_user.user_id == test_user.id
        assert telegram_user.telegram_id == telegram_user_data["telegram_id"]

        # 2. Create Telegram chat
        chat_data = {
            "telegram_user_id": telegram_user.id,
            "chat_id": 123456789,
            "chat_type": "private",
            "title": "Test Chat",
            "is_active": True
        }
        chat = await telegram_service.create_chat(chat_data)
        assert chat is not None
        assert chat.telegram_user_id == telegram_user.id
        assert chat.chat_id == chat_data["chat_id"]

        # 3. Send test message
        message = "Test VPN status message"
        sent_message = await telegram_service.send_message(chat.chat_id, message)
        assert sent_message is not None
        assert sent_message.chat_id == chat.chat_id
        assert sent_message.text == message

        # 4. Get user's VPN accounts
        vpn_accounts = await vpn_service.get_user_accounts(test_user.id)
        assert isinstance(vpn_accounts, list)

        # 5. Send VPN status message
        if vpn_accounts:
            account = vpn_accounts[0]
            status_message = f"VPN Account Status:\nUsername: {account.username}\nServer: {account.server.host}"
            status_sent = await telegram_service.send_message(chat.chat_id, status_message)
            assert status_sent is not None
            assert status_sent.chat_id == chat.chat_id

class TestPaymentSubscriptionFlow:
    """Test cases for payment and subscription flow."""

    async def test_payment_subscription_flow(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_subscription_plan: SubscriptionPlan
    ):
        """Test complete payment and subscription flow."""
        # Initialize services
        payment_service = PaymentService(db_session)
        subscription_service = SubscriptionService(db_session)

        # 1. Create payment
        payment_data = {
            "user_id": test_user.id,
            "plan_id": test_subscription_plan.id,
            "amount": test_subscription_plan.price,
            "currency": "USD",
            "payment_method": "credit_card",
            "status": "pending"
        }
        payment = await payment_service.create_payment(payment_data)
        assert payment is not None
        assert payment.status == "pending"

        # 2. Create payment transaction
        transaction_data = {
            "payment_id": payment.id,
            "transaction_id": "test_transaction_123",
            "amount": payment.amount,
            "currency": payment.currency,
            "status": "completed",
            "payment_method": payment.payment_method,
            "payment_date": datetime.utcnow()
        }
        transaction = await payment_service.create_transaction(transaction_data)
        assert transaction is not None
        assert transaction.status == "completed"

        # 3. Update payment status
        updated_payment = await payment_service.update_payment_status(payment.id, "completed")
        assert updated_payment.status == "completed"

        # 4. Create subscription
        subscription_data = {
            "user_id": test_user.id,
            "plan_id": test_subscription_plan.id,
            "start_date": datetime.utcnow(),
            "end_date": datetime.utcnow() + timedelta(days=30),
            "is_active": True
        }
        subscription = await subscription_service.create_subscription(subscription_data)
        assert subscription is not None
        assert subscription.is_active is True

        # 5. Verify subscription validity
        is_valid = await subscription_service.check_subscription_validity(subscription.id)
        assert is_valid is True

        # 6. Test subscription renewal
        new_end_date = datetime.utcnow() + timedelta(days=60)
        renewed_subscription = await subscription_service.renew_subscription(
            subscription.id,
            new_end_date
        )
        assert renewed_subscription.end_date == new_end_date
        assert renewed_subscription.is_active is True 