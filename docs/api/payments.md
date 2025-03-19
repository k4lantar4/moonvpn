# Payment System Documentation

## Overview

The MoonVPN payment system provides a flexible and secure way to handle subscription payments through multiple payment gateways. Currently supported payment methods include:

- ZarinPal (Iranian payment gateway)
- Internal Wallet System

## API Endpoints

### 1. Create Subscription Payment

Creates a new subscription payment and returns payment details.

```http
POST /api/subscriptions/
Content-Type: application/json
Authorization: Bearer <token>

{
    "plan": 1,
    "payment_method": "zarinpal",
    "auto_renew": false
}
```

#### Response (200 OK)
```json
{
    "transaction_id": "123",
    "payment_id": "A00000000000000000000000000456789",
    "payment_url": "https://zarinpal.com/pg/StartPay/A00000000000000000000000000456789",
    "amount": 100000,
    "status": "pending"
}
```

### 2. Renew Subscription

Renews an existing subscription by creating a new payment.

```http
POST /api/subscriptions/{id}/renew/
Content-Type: application/json
Authorization: Bearer <token>

{
    "payment_method": "zarinpal"
}
```

### 3. View Transaction History

Retrieves user's transaction history.

```http
GET /api/transactions/
Authorization: Bearer <token>
```

#### Response (200 OK)
```json
{
    "count": 10,
    "next": "http://api.example.com/transactions/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "subscription": {
                "id": 1,
                "plan": {
                    "name": "Premium Plan",
                    "price": 100000
                },
                "status": "active"
            },
            "transaction_type": "new",
            "status": "completed",
            "amount": 100000,
            "payment_method": "zarinpal",
            "payment_id": "A00000000000000000000000000456789",
            "created_at": "2024-03-14T12:00:00Z"
        }
    ]
}
```

### 4. Payment Callback

Handles payment gateway callbacks. This endpoint is called by the payment gateway after payment completion.

```http
GET/POST /api/payment/callback/
```

Query Parameters:
- `Authority`: Payment ID from ZarinPal
- `Status`: Payment status from ZarinPal

## Models

### Plan
```python
class Plan(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    duration_type = models.CharField(max_length=20)
    duration_days = models.IntegerField()
    traffic_limit = models.BigIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    max_connections = models.IntegerField()
    status = models.CharField(max_length=20)
    features = models.JSONField()
```

### Subscription
```python
class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)
    status = models.CharField(max_length=20)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    last_renewal = models.DateTimeField(null=True)
    auto_renew = models.BooleanField(default=False)
```

### Transaction
```python
class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True)
    transaction_type = models.CharField(max_length=20)
    status = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50)
    payment_id = models.CharField(max_length=100)
```

## Payment Flow

1. **Create Subscription**
   - User selects a plan
   - Frontend calls `/api/subscriptions/` with plan and payment details
   - Backend creates pending subscription and transaction
   - Returns payment URL for redirection

2. **Payment Process**
   - User is redirected to payment gateway
   - User completes payment
   - Gateway redirects back to callback URL

3. **Payment Verification**
   - Backend verifies payment with gateway
   - If successful:
     - Transaction is marked as completed
     - Subscription is activated
     - User is redirected to success page
   - If failed:
     - Transaction is marked as failed
     - User is redirected to failure page

4. **Subscription Renewal**
   - For auto-renewing subscriptions:
     - System checks for expiring subscriptions daily
     - Creates renewal payment automatically
     - Notifies user of payment requirement
   - For manual renewals:
     - User initiates renewal through API
     - Follows same payment flow as new subscriptions

## Error Handling

All API endpoints follow consistent error response format:

```json
{
    "error": "Detailed error message"
}
```

Common HTTP Status Codes:
- 200: Success
- 201: Created
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 500: Internal Server Error

## Security Considerations

1. **Authentication**
   - All endpoints except callback require JWT authentication
   - Tokens expire after 24 hours
   - Refresh tokens valid for 7 days

2. **Payment Data**
   - Payment details never stored directly
   - Only transaction IDs and statuses are stored
   - All communication with payment gateways over HTTPS

3. **Rate Limiting**
   - API endpoints are rate-limited
   - Maximum 100 requests per minute per user
   - Callback endpoints have separate rate limiting

## Environment Configuration

Required environment variables:
```bash
ZARINPAL_MERCHANT_ID=your_merchant_id
ZARINPAL_SANDBOX=true  # Set to false in production
ZARINPAL_CALLBACK_URL=https://your-domain.com/api/payment/callback/
PAYMENT_SUCCESS_URL=https://your-domain.com/payment/success
PAYMENT_FAILURE_URL=https://your-domain.com/payment/failure
```

## Testing

Test cards for ZarinPal sandbox:
- Card Number: 5022-2910-0000-0008
- CVV2: Any 3 or 4 digits
- Expiry Date: Any future date
- OTP Code: 12345

## Troubleshooting

Common issues and solutions:

1. **Payment Not Verified**
   - Check payment gateway logs
   - Verify merchant ID and callback URL
   - Ensure correct amount in verification request

2. **Callback Not Received**
   - Check gateway whitelist settings
   - Verify SSL certificate
   - Check server firewall rules

3. **Transaction Stuck in Pending**
   - Run verification check manually
   - Check for failed callbacks
   - Contact payment gateway support 