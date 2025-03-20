import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.user import User
from app.models.transaction import Transaction
from app.models.order import Order
from app.services.payment import PaymentService
from app.services.vpn import VPNService

@pytest.fixture
def test_user(db: Session) -> User:
    """Create a test user for payment flow testing."""
    user = User(
        username="testuser",
        email="test@example.com",
        phone_number="989123456789",
        is_active=True,
        is_verified=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def payment_service(db: Session) -> PaymentService:
    """Create a payment service instance for testing."""
    return PaymentService(db)

@pytest.fixture
def vpn_service(db: Session) -> VPNService:
    """Create a VPN service instance for testing."""
    return VPNService(db)

def test_payment_flow_wallet(
    client: TestClient,
    test_user: User,
    payment_service: PaymentService,
    vpn_service: VPNService,
    db: Session
):
    """Test complete payment flow using wallet payment method."""
    # 1. Create a test order
    order = Order(
        user_id=test_user.id,
        amount=100000,  # 100,000 Rials
        status="pending"
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    # 2. Add wallet balance
    test_user.wallet_balance = 150000  # 150,000 Rials
    db.commit()

    # 3. Process payment
    payment_result = payment_service.process_payment(
        user_id=test_user.id,
        order_id=order.id,
        payment_method="wallet"
    )

    # 4. Verify payment result
    assert payment_result["status"] == "success"
    assert payment_result["transaction"].status == "completed"
    assert payment_result["transaction"].amount == 100000
    assert payment_result["transaction"].payment_method == "wallet"

    # 5. Verify wallet balance
    db.refresh(test_user)
    assert test_user.wallet_balance == 50000  # 150,000 - 100,000

    # 6. Verify order status
    db.refresh(order)
    assert order.status == "completed"

def test_payment_flow_zarinpal(
    client: TestClient,
    test_user: User,
    payment_service: PaymentService,
    vpn_service: VPNService,
    db: Session
):
    """Test complete payment flow using ZarinPal payment method."""
    # 1. Create a test order
    order = Order(
        user_id=test_user.id,
        amount=100000,  # 100,000 Rials
        status="pending"
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    # 2. Initiate ZarinPal payment
    payment_result = payment_service.initiate_zarinpal_payment(
        user_id=test_user.id,
        order_id=order.id,
        amount=100000
    )

    # 3. Verify payment initiation
    assert payment_result["status"] == "success"
    assert "payment_url" in payment_result
    assert payment_result["transaction"].status == "pending"
    assert payment_result["transaction"].payment_method == "zarinpal"

    # 4. Simulate ZarinPal callback
    callback_data = {
        "Authority": "test_authority",
        "Status": "OK",
        "RefID": "test_ref_id"
    }
    
    verification_result = payment_service.verify_zarinpal_payment(
        authority=callback_data["Authority"],
        status=callback_data["Status"]
    )

    # 5. Verify payment verification
    assert verification_result["status"] == "success"
    assert verification_result["transaction"].status == "completed"
    assert verification_result["transaction"].ref_id == callback_data["RefID"]

    # 6. Verify order status
    db.refresh(order)
    assert order.status == "completed"

def test_payment_flow_bank_transfer(
    client: TestClient,
    test_user: User,
    payment_service: PaymentService,
    vpn_service: VPNService,
    db: Session
):
    """Test complete payment flow using bank transfer payment method."""
    # 1. Create a test order
    order = Order(
        user_id=test_user.id,
        amount=100000,  # 100,000 Rials
        status="pending"
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    # 2. Initiate bank transfer
    payment_result = payment_service.initiate_bank_transfer(
        user_id=test_user.id,
        order_id=order.id,
        amount=100000
    )

    # 3. Verify payment initiation
    assert payment_result["status"] == "success"
    assert "bank_details" in payment_result
    assert payment_result["transaction"].status == "pending"
    assert payment_result["transaction"].payment_method == "bank_transfer"

    # 4. Simulate bank transfer verification
    verification_result = payment_service.verify_bank_transfer(
        transaction_id=payment_result["transaction"].id,
        ref_id="test_ref_id"
    )

    # 5. Verify payment verification
    assert verification_result["status"] == "success"
    assert verification_result["transaction"].status == "completed"
    assert verification_result["transaction"].ref_id == "test_ref_id"

    # 6. Verify order status
    db.refresh(order)
    assert order.status == "completed"

def test_payment_flow_error_handling(
    client: TestClient,
    test_user: User,
    payment_service: PaymentService,
    vpn_service: VPNService,
    db: Session
):
    """Test error handling in payment flow."""
    # 1. Create a test order
    order = Order(
        user_id=test_user.id,
        amount=100000,  # 100,000 Rials
        status="pending"
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    # 2. Test insufficient wallet balance
    test_user.wallet_balance = 50000  # 50,000 Rials
    db.commit()

    with pytest.raises(ValueError) as exc_info:
        payment_service.process_payment(
            user_id=test_user.id,
            order_id=order.id,
            payment_method="wallet"
        )
    assert "Insufficient wallet balance" in str(exc_info.value)

    # 3. Test invalid payment method
    with pytest.raises(ValueError) as exc_info:
        payment_service.process_payment(
            user_id=test_user.id,
            order_id=order.id,
            payment_method="invalid_method"
        )
    assert "Invalid payment method" in str(exc_info.value)

    # 4. Test invalid order status
    order.status = "completed"
    db.commit()

    with pytest.raises(ValueError) as exc_info:
        payment_service.process_payment(
            user_id=test_user.id,
            order_id=order.id,
            payment_method="wallet"
        )
    assert "Invalid order status" in str(exc_info.value) 