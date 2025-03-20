# Payment System Documentation

## Overview

The MoonVPN payment system provides a comprehensive solution for handling various payment methods including:
- Wallet payments
- Credit card payments
- Bank transfers
- ZarinPal integration

## Features

- Multiple payment methods support
- Secure payment processing
- Transaction tracking and history
- Wallet management
- Order management
- Webhook support for payment notifications
- Comprehensive error handling
- Detailed logging
- Tax calculation
- Currency support

## Payment Methods

### 1. Wallet Payments

Users can make payments using their wallet balance. The wallet system supports:
- Deposits
- Balance checks
- Transaction history
- Balance limits

### 2. Credit Card Payments

Credit card payments are processed through a secure payment gateway. Features include:
- Secure card processing
- Payment verification
- Transaction tracking
- Support for multiple currencies

### 3. Bank Transfers

Bank transfer payments provide:
- Bank account details
- Reference number generation
- Transfer verification
- Manual approval process

### 4. ZarinPal Integration

ZarinPal integration offers:
- Direct payment processing
- Payment verification
- Webhook support
- Sandbox environment for testing

## API Endpoints

### Payment Processing

```http
POST /api/v1/payments/process
```

Request body:
```json
{
    "user_id": 1,
    "order_id": "ORD123",
    "amount": 100.0,
    "payment_method": "zarinpal",
    "callback_url": "https://example.com/callback"
}
```

Response:
```json
{
    "success": true,
    "message": "Payment initiated successfully",
    "transaction_id": 1,
    "payment_url": "https://zarinpal.com/pg/StartPay/AUTH123"
}
```

### Payment Verification

```http
POST /api/v1/payments/verify
```

Query parameters:
- `authority`: Payment gateway authority
- `status`: Payment status
- `ref_id`: Payment reference ID

Response:
```json
{
    "success": true,
    "message": "Payment verified successfully",
    "transaction_id": 1
}
```

### Wallet Management

```http
GET /api/v1/payments/wallet/{user_id}
```

Response:
```json
{
    "id": 1,
    "user_id": 1,
    "balance": 1000.0,
    "currency": "USD"
}
```

### Transaction History

```http
GET /api/v1/payments/transactions/{user_id}
```

Query parameters:
- `limit`: Number of transactions to return (default: 10)
- `offset`: Number of transactions to skip (default: 0)

Response:
```json
[
    {
        "id": 1,
        "user_id": 1,
        "amount": 100.0,
        "type": "purchase",
        "payment_method": "zarinpal",
        "status": "completed",
        "created_at": "2024-01-01T00:00:00Z"
    }
]
```

### Order Management

```http
GET /api/v1/payments/orders/{user_id}
```

Query parameters:
- `limit`: Number of orders to return (default: 10)
- `offset`: Number of orders to skip (default: 0)

Response:
```json
[
    {
        "id": 1,
        "user_id": 1,
        "plan_id": 1,
        "amount": 100.0,
        "status": "completed",
        "created_at": "2024-01-01T00:00:00Z"
    }
]
```

## Webhooks

### ZarinPal Webhook

```http
POST /api/v1/webhooks/payment/zarinpal
```

Headers:
- `X-ZarinPal-Signature`: Webhook signature

Request body:
```json
{
    "Authority": "AUTH123",
    "Status": 100,
    "RefID": "REF123",
    "CardPan": "1234",
    "CardHash": "HASH123",
    "Fee": 0,
    "FeeType": "Merchant"
}
```

### Bank Transfer Webhook

```http
POST /api/v1/webhooks/payment/bank-transfer
```

Headers:
- `X-Bank-Signature`: Webhook signature

Request body:
```json
{
    "transaction_id": "TRX123",
    "status": "completed",
    "amount": 100.0,
    "reference": "REF123"
}
```

### Card Payment Webhook

```http
POST /api/v1/webhooks/payment/card
```

Headers:
- `X-Card-Signature`: Webhook signature

Request body:
```json
{
    "transaction_id": "TRX123",
    "status": "succeeded",
    "amount": 100.0,
    "card_last4": "1234",
    "payment_intent_id": "PI123"
}
```

## Error Handling

The payment system uses standard HTTP status codes and provides detailed error messages:

- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server-side error

Error response format:
```json
{
    "detail": "Error message description"
}
```

## Configuration

Payment system configuration is managed through environment variables:

```env
# ZarinPal Settings
ZARINPAL_MERCHANT=your_merchant_id
ZARINPAL_SANDBOX=true
ZARINPAL_CALLBACK_URL=https://your-domain.com/api/v1/payments/verify
ZARINPAL_DESCRIPTION=MoonVPN Subscription

# Bank Transfer Settings
BANK_NAME=Your Bank Name
BANK_ACCOUNT=1234567890
BANK_HOLDER=Your Name
BANK_IBAN=IR123456789012345678901234

# Wallet Settings
MAX_WALLET_BALANCE=1000.0
MIN_WALLET_BALANCE=0.0
DEFAULT_CURRENCY=USD

# Payment Gateway URLs
PAYMENT_FORM_URL=https://payment.your-domain.com
PAYMENT_SUCCESS_URL=https://your-domain.com/payment/success
PAYMENT_FAIL_URL=https://your-domain.com/payment/fail

# Payment Retry Settings
MAX_RETRY_ATTEMPTS=3
RETRY_DELAY_SECONDS=5

# Webhook Settings
WEBHOOK_SECRET=your_webhook_secret
WEBHOOK_TIMEOUT=30

# Payment Logging
PAYMENT_LOG_LEVEL=INFO
PAYMENT_LOG_FILE=payment.log
```

## Security Considerations

1. All payment endpoints require authentication
2. Webhook signatures are validated
3. Sensitive data is encrypted
4. Payment amounts are validated
5. Transaction status changes are logged
6. Wallet balance limits are enforced
7. Payment retries are limited
8. Webhook timeouts are implemented

## Testing

The payment system includes comprehensive tests:

```bash
# Run all payment tests
pytest tests/test_payment.py

# Run specific test
pytest tests/test_payment.py::test_process_payment
```

## Best Practices

1. Always validate payment amounts
2. Implement proper error handling
3. Log all payment events
4. Use webhooks for payment status updates
5. Implement retry mechanisms
6. Monitor payment failures
7. Keep payment credentials secure
8. Use sandbox environments for testing
9. Implement proper transaction isolation
10. Follow PCI DSS guidelines for card payments

## Support

For payment system support:
- Email: support@moonvpn.com
- Documentation: https://docs.moonvpn.com/payment
- API Reference: https://api.moonvpn.com/docs 