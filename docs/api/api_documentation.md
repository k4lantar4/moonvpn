# API Documentation

This document provides details about the API endpoints available in the V2Ray Account Management System.

## Authentication

Most API endpoints require authentication. Use JWT tokens for authentication.

### Get Token

```
POST /api/v1/auth/token/
```

**Request Body:**

```json
{
  "username": "your_username",
  "password": "your_password"
}
```

**Response:**

```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1..."
}
```

### Refresh Token

```
POST /api/v1/auth/token/refresh/
```

**Request Body:**

```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1..."
}
```

**Response:**

```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1..."
}
```

## User Management

### Get Current User

```
GET /api/v1/users/me/
```

**Response:**

```json
{
  "id": 1,
  "username": "username",
  "email": "user@example.com",
  "first_name": "First",
  "last_name": "Last",
  "telegram_id": "123456789",
  "is_active": true,
  "date_joined": "2024-03-12T10:00:00Z"
}
```

### Update User

```
PATCH /api/v1/users/me/
```

**Request Body:**

```json
{
  "first_name": "New First Name",
  "email": "new_email@example.com"
}
```

## V2Ray Accounts

### List User Accounts

```
GET /api/v1/v2ray/accounts/
```

**Response:**

```json
[
  {
    "id": 1,
    "name": "Account 1",
    "status": "active",
    "created_at": "2024-03-12T10:00:00Z",
    "expires_at": "2024-04-12T10:00:00Z",
    "traffic_limit": 100000000000,
    "traffic_used": 1000000000,
    "config": "vmess://..."
  }
]
```

### Get Account Details

```
GET /api/v1/v2ray/accounts/{id}/
```

**Response:**

```json
{
  "id": 1,
  "name": "Account 1",
  "status": "active",
  "created_at": "2024-03-12T10:00:00Z",
  "expires_at": "2024-04-12T10:00:00Z",
  "traffic_limit": 100000000000,
  "traffic_used": 1000000000,
  "config": "vmess://...",
  "panel": {
    "id": 1,
    "name": "Panel 1",
    "url": "https://panel1.example.com"
  },
  "inbound": {
    "id": 1,
    "protocol": "vmess",
    "tag": "inbound-1"
  }
}
```

## Subscription Plans

### List Available Plans

```
GET /api/v1/plans/
```

**Response:**

```json
[
  {
    "id": 1,
    "name": "Basic Plan",
    "description": "30 days, 50GB traffic",
    "price": 100000,
    "duration_days": 30,
    "traffic_limit": 50000000000,
    "is_active": true
  }
]
```

## Payments

### Create Payment

```
POST /api/v1/payments/
```

**Request Body:**

```json
{
  "amount": 100000,
  "method": "zarinpal",
  "plan_id": 1
}
```

**Response:**

```json
{
  "id": 1,
  "amount": 100000,
  "method": "zarinpal",
  "status": "pending",
  "created_at": "2024-03-12T10:00:00Z",
  "updated_at": "2024-03-12T10:00:00Z",
  "payment_url": "https://zarinpal.com/pg/StartPay/1234567890"
}
```

### Verify Card Payment

```
POST /api/v1/payments/verify-card-payment/
```

**Request Body:**

```json
{
  "payment_id": 1,
  "transaction_id": "123456789",
  "card_number": "6104********1234",
  "amount": 100000
}
```

**Response:**

```json
{
  "success": true,
  "message": "Payment verified successfully",
  "account": {
    "id": 1,
    "name": "Account 1",
    "config": "vmess://..."
  }
}
```

## 3x-UI Panel API

### List Panels

```
GET /api/v1/panels/ (Admin only)
```

**Response:**

```json
[
  {
    "id": 1,
    "name": "Panel 1",
    "url": "https://panel1.example.com",
    "is_active": true,
    "inbounds_count": 5,
    "clients_count": 100
  }
]
```

### Get Panel Status

```
GET /api/v1/panels/{id}/status/ (Admin only)
```

**Response:**

```json
{
  "id": 1,
  "name": "Panel 1",
  "status": "online",
  "uptime": "5 days, 2 hours",
  "cpu_usage": 15.5,
  "memory_usage": 45.2,
  "disk_usage": 32.8,
  "total_clients": 100,
  "active_clients": 75
}
```

## Error Responses

All API endpoints return standard HTTP status codes:

- `200 OK` - Request succeeded
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid input
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

Error responses include a message explaining the error:

```json
{
  "error": "Invalid input",
  "detail": "Field 'username' is required"
}
```

## Rate Limiting

API requests are rate-limited to prevent abuse. The current limits are:

- Anonymous requests: 10 requests per minute
- Authenticated requests: 60 requests per minute

Rate limit headers are included in API responses:

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 59
X-RateLimit-Reset: 1583856240
```

## Webhooks

The system provides webhooks for the Telegram bot and payment notifications. 