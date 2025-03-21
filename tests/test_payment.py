"""
Payment system tests for MoonVPN.

This module contains tests for the payment system including
payment processing, verification, and webhook handling.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.database.models.payment import (
    Transaction,
    TransactionStatus,
    TransactionType,
    PaymentMethod,
    Wallet,
    Order
)
from app.core.integrations.zarinpal import zarinpal
from app.core.utils.payment import (
    format_amount,
    validate_amount,
    generate_order_id,
    generate_transaction_id,
    calculate_tax,
    calculate_total
)

client = TestClient(app)

@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return AsyncMock(spec=Session)

@pytest.fixture
def mock_zarinpal():
    """Mock ZarinPal API client."""
    with patch("app.core.integrations.zarinpal.zarinpal") as mock:
        yield mock

@pytest.fixture
def sample_transaction():
    """Create a sample transaction."""
    return Transaction(
        id=1,
        user_id=1,
        amount=100.0,
        type=TransactionType.PURCHASE,
        payment_method=PaymentMethod.ZARINPAL,
        status=TransactionStatus.PENDING,
        order_id="ORD123",
        authority="AUTH123",
        ref_id="REF123",
        transaction_data={
            "payment_method": "zarinpal",
            "callback_url": "https://example.com/callback"
        },
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

@pytest.fixture
def sample_wallet():
    """Create a sample wallet."""
    return Wallet(
        id=1,
        user_id=1,
        balance=1000.0,
        currency="USD",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

@pytest.fixture
def sample_order():
    """Create a sample order."""
    return Order(
        id=1,
        user_id=1,
        plan_id=1,
        amount=100.0,
        status="pending",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

def test_format_amount():
    """Test amount formatting."""
    assert format_amount(100.0) == "$100.00"
    assert format_amount(100.0, "EUR") == "€100.00"
    assert format_amount(100.0, "GBP") == "£100.00"
    assert format_amount(100.0, "IRR") == "ریال100.00"

def test_validate_amount():
    """Test amount validation."""
    assert validate_amount(100.0) is True
    assert validate_amount(0.0) is False
    assert validate_amount(-100.0) is False
    assert validate_amount(1001.0) is False  # Exceeds max wallet balance

def test_generate_order_id():
    """Test order ID generation."""
    order_id = generate_order_id()
    assert order_id.startswith("ORD")
    assert len(order_id) > 20  # Timestamp + random string

def test_generate_transaction_id():
    """Test transaction ID generation."""
    transaction_id = generate_transaction_id()
    assert transaction_id.startswith("TRX")
    assert len(transaction_id) > 20  # Timestamp + random string

def test_calculate_tax():
    """Test tax calculation."""
    assert calculate_tax(100.0) == 9.0  # 9% tax rate
    assert calculate_tax(100.0, 0.1) == 10.0  # 10% tax rate
    assert calculate_tax(0.0) == 0.0

def test_calculate_total():
    """Test total amount calculation."""
    assert calculate_total(100.0) == 109.0  # Amount + 9% tax
    assert calculate_total(100.0, 0.1) == 110.0  # Amount + 10% tax
    assert calculate_total(0.0) == 0.0

@pytest.mark.asyncio
async def test_process_payment(mock_db, mock_zarinpal):
    """Test payment processing."""
    # Mock ZarinPal API response
    mock_zarinpal.request_payment.return_value = {
        "success": True,
        "authority": "AUTH123",
        "payment_url": "https://zarinpal.com/pg/StartPay/AUTH123"
    }

    # Create payment request
    payment_request = {
        "user_id": 1,
        "order_id": "ORD123",
        "amount": 100.0,
        "payment_method": "zarinpal",
        "callback_url": "https://example.com/callback"
    }

    # Make API request
    response = client.post("/api/v1/payments/process", json=payment_request)
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert "payment_url" in response.json()

@pytest.mark.asyncio
async def test_verify_payment(mock_db, sample_transaction):
    """Test payment verification."""
    # Mock database query
    mock_db.query.return_value.filter.return_value.first.return_value = sample_transaction

    # Mock ZarinPal API response
    mock_zarinpal.verify_payment.return_value = {
        "success": True,
        "ref_id": "REF123",
        "card_pan": "1234",
        "card_hash": "HASH123",
        "fee": 0,
        "fee_type": "Merchant"
    }

    # Make API request
    response = client.post(
        "/api/v1/payments/verify",
        params={
            "authority": "AUTH123",
            "status": "OK",
            "ref_id": "REF123"
        }
    )
    assert response.status_code == 200
    assert response.json()["success"] is True

@pytest.mark.asyncio
async def test_get_user_transactions(mock_db, sample_transaction):
    """Test getting user transactions."""
    # Mock database query
    mock_db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [sample_transaction]

    # Make API request
    response = client.get("/api/v1/payments/transactions/1")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == sample_transaction.id

@pytest.mark.asyncio
async def test_get_user_wallet(mock_db, sample_wallet):
    """Test getting user wallet."""
    # Mock database query
    mock_db.query.return_value.filter.return_value.first.return_value = sample_wallet

    # Make API request
    response = client.get("/api/v1/payments/wallet/1")
    assert response.status_code == 200
    assert response.json()["id"] == sample_wallet.id
    assert response.json()["balance"] == sample_wallet.balance

@pytest.mark.asyncio
async def test_deposit_to_wallet(mock_db, sample_wallet):
    """Test wallet deposit."""
    # Mock database query
    mock_db.query.return_value.filter.return_value.first.return_value = sample_wallet

    # Mock ZarinPal API response
    mock_zarinpal.request_payment.return_value = {
        "success": True,
        "authority": "AUTH123",
        "payment_url": "https://zarinpal.com/pg/StartPay/AUTH123"
    }

    # Make API request
    response = client.post(
        "/api/v1/payments/wallet/deposit",
        params={
            "user_id": 1,
            "amount": 100.0,
            "payment_method": "zarinpal"
        }
    )
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert "payment_url" in response.json()

@pytest.mark.asyncio
async def test_get_user_orders(mock_db, sample_order):
    """Test getting user orders."""
    # Mock database query
    mock_db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [sample_order]

    # Make API request
    response = client.get("/api/v1/payments/orders/1")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == sample_order.id

@pytest.mark.asyncio
async def test_zarinpal_webhook(mock_db, mock_zarinpal):
    """Test ZarinPal webhook handling."""
    # Mock webhook data
    webhook_data = {
        "Authority": "AUTH123",
        "Status": 100,
        "RefID": "REF123",
        "CardPan": "1234",
        "CardHash": "HASH123",
        "Fee": 0,
        "FeeType": "Merchant"
    }

    # Mock ZarinPal webhook handler
    mock_zarinpal.handle_webhook.return_value = {
        "success": True,
        "authority": "AUTH123",
        "status": 100,
        "ref_id": "REF123"
    }

    # Make API request
    response = client.post(
        "/api/v1/webhooks/payment/zarinpal",
        json=webhook_data,
        headers={"X-ZarinPal-Signature": "SIGNATURE123"}
    )
    assert response.status_code == 200
    assert response.json()["success"] is True

@pytest.mark.asyncio
async def test_bank_transfer_webhook(mock_db):
    """Test bank transfer webhook handling."""
    # Mock webhook data
    webhook_data = {
        "transaction_id": "TRX123",
        "status": "completed",
        "amount": 100.0,
        "reference": "REF123"
    }

    # Make API request
    response = client.post(
        "/api/v1/webhooks/payment/bank-transfer",
        json=webhook_data,
        headers={"X-Bank-Signature": "SIGNATURE123"}
    )
    assert response.status_code == 200
    assert response.json()["success"] is True

@pytest.mark.asyncio
async def test_card_payment_webhook(mock_db):
    """Test card payment webhook handling."""
    # Mock webhook data
    webhook_data = {
        "transaction_id": "TRX123",
        "status": "succeeded",
        "amount": 100.0,
        "card_last4": "1234",
        "payment_intent_id": "PI123"
    }

    # Make API request
    response = client.post(
        "/api/v1/webhooks/payment/card",
        json=webhook_data,
        headers={"X-Card-Signature": "SIGNATURE123"}
    )
    assert response.status_code == 200
    assert response.json()["success"] is True 