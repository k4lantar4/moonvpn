import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.payment import PaymentService
from app.models.user import User
from app.models.order import Order
from app.models.transaction import Transaction
from app.core.config import settings

@pytest.fixture
def payment_service():
    """Create a payment service instance."""
    return PaymentService()

@pytest.fixture
def test_user(db):
    """Create a test user."""
    user = User(
        telegram_id=123456789,
        username="testuser",
        email="test@example.com",
        phone_number="989123456789",
        is_active=True,
        is_verified=True,
        wallet_balance=1000
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def test_order(db, test_user):
    """Create a test order."""
    order = Order(
        user_id=test_user.id,
        amount=100,
        currency="USD",
        status="pending",
        payment_method="wallet"
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order

@pytest.mark.asyncio
async def test_create_order(payment_service, test_user):
    """Test creating a payment order."""
    order = await payment_service.create_order(
        user=test_user,
        amount=100,
        currency="USD",
        payment_method="wallet"
    )
    assert order is not None
    assert order.user_id == test_user.id
    assert order.amount == 100
    assert order.currency == "USD"
    assert order.status == "pending"
    assert order.payment_method == "wallet"

@pytest.mark.asyncio
async def test_process_wallet_payment(payment_service, test_user, test_order):
    """Test processing wallet payment."""
    with patch("app.services.payment.PaymentService._check_wallet_balance") as mock_check:
        mock_check.return_value = True
        with patch("app.services.payment.PaymentService._deduct_wallet_balance") as mock_deduct:
            mock_deduct.return_value = True
            result = await payment_service.process_wallet_payment(test_order)
            assert result is True
            assert test_order.status == "completed"
            mock_deduct.assert_called_once()

@pytest.mark.asyncio
async def test_process_zarinpal_payment(payment_service, test_order):
    """Test processing ZarinPal payment."""
    with patch("app.services.payment.PaymentService._initiate_zarinpal_payment") as mock_init:
        mock_init.return_value = {
            "status": "success",
            "authority": "test_authority",
            "payment_url": "https://test.zarinpal.com/payment"
        }
        result = await payment_service.process_zarinpal_payment(test_order)
        assert result["status"] == "success"
        assert "authority" in result
        assert "payment_url" in result
        mock_init.assert_called_once()

@pytest.mark.asyncio
async def test_process_bank_transfer(payment_service, test_order):
    """Test processing bank transfer."""
    with patch("app.services.payment.PaymentService._generate_bank_receipt") as mock_receipt:
        mock_receipt.return_value = {
            "status": "success",
            "receipt_number": "123456",
            "bank_details": {
                "account_number": "1234567890",
                "bank_name": "Test Bank"
            }
        }
        result = await payment_service.process_bank_transfer(test_order)
        assert result["status"] == "success"
        assert "receipt_number" in result
        assert "bank_details" in result
        mock_receipt.assert_called_once()

@pytest.mark.asyncio
async def test_verify_payment(payment_service, test_order):
    """Test payment verification."""
    with patch("app.services.payment.PaymentService._verify_transaction") as mock_verify:
        mock_verify.return_value = True
        result = await payment_service.verify_payment(test_order)
        assert result is True
        assert test_order.status == "completed"
        mock_verify.assert_called_once()

@pytest.mark.asyncio
async def test_get_transaction_status(payment_service, test_order):
    """Test getting transaction status."""
    with patch("app.services.payment.PaymentService._check_transaction_status") as mock_check:
        mock_check.return_value = {
            "status": "completed",
            "amount": 100,
            "currency": "USD",
            "timestamp": "2024-01-01T00:00:00Z"
        }
        status = await payment_service.get_transaction_status(test_order)
        assert status["status"] == "completed"
        assert status["amount"] == 100
        assert status["currency"] == "USD"
        assert "timestamp" in status
        mock_check.assert_called_once()

@pytest.mark.asyncio
async def test_get_payment_history(payment_service, test_user):
    """Test getting payment history."""
    with patch("app.services.payment.PaymentService._get_user_transactions") as mock_get:
        mock_get.return_value = [
            {
                "id": 1,
                "amount": 100,
                "currency": "USD",
                "status": "completed",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        ]
        history = await payment_service.get_payment_history(test_user)
        assert isinstance(history, list)
        assert len(history) == 1
        assert history[0]["amount"] == 100
        assert history[0]["status"] == "completed"
        mock_get.assert_called_once()

@pytest.mark.asyncio
async def test_refund_payment(payment_service, test_order):
    """Test payment refund."""
    with patch("app.services.payment.PaymentService._process_refund") as mock_refund:
        mock_refund.return_value = {
            "status": "success",
            "refund_id": "123456",
            "amount": 100,
            "currency": "USD"
        }
        result = await payment_service.refund_payment(test_order)
        assert result["status"] == "success"
        assert "refund_id" in result
        assert result["amount"] == 100
        mock_refund.assert_called_once()

@pytest.mark.asyncio
async def test_error_handling(payment_service, test_order):
    """Test error handling in payment service."""
    # Test insufficient wallet balance
    with patch("app.services.payment.PaymentService._check_wallet_balance") as mock_check:
        mock_check.return_value = False
        with pytest.raises(Exception) as exc_info:
            await payment_service.process_wallet_payment(test_order)
        assert "Insufficient balance" in str(exc_info.value)

    # Test payment verification failure
    with patch("app.services.payment.PaymentService._verify_transaction") as mock_verify:
        mock_verify.side_effect = Exception("Verification failed")
        with pytest.raises(Exception) as exc_info:
            await payment_service.verify_payment(test_order)
        assert "Verification failed" in str(exc_info.value)

@pytest.mark.asyncio
async def test_payment_method_validation(payment_service, test_user):
    """Test payment method validation."""
    # Test invalid payment method
    with pytest.raises(ValueError) as exc_info:
        await payment_service.create_order(
            user=test_user,
            amount=100,
            currency="USD",
            payment_method="invalid_method"
        )
    assert "Invalid payment method" in str(exc_info.value)

    # Test unsupported currency
    with pytest.raises(ValueError) as exc_info:
        await payment_service.create_order(
            user=test_user,
            amount=100,
            currency="INVALID",
            payment_method="wallet"
        )
    assert "Unsupported currency" in str(exc_info.value) 