# MoonVPN API Documentation

This document provides information about the MoonVPN API endpoints, authentication, and usage examples.

## Base URL

All API endpoints are relative to the base URL:

```
https://your-domain.com/api/v1/
```

## Authentication

Most API endpoints require authentication. MoonVPN uses JWT (JSON Web Token) for authentication.

### Obtaining a Token

To obtain a token, send a POST request to the `/api/v1/auth/token/` endpoint:

```bash
curl -X POST https://your-domain.com/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "your-username", "password": "your-password"}'
```

Response:

```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Using the Token

Include the token in the Authorization header for all authenticated requests:

```bash
curl -X GET https://your-domain.com/api/v1/users/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

### Refreshing a Token

To refresh an expired token, send a POST request to the `/api/v1/auth/token/refresh/` endpoint:

```bash
curl -X POST https://your-domain.com/api/v1/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."}'
```

## API Endpoints

### Users

#### List Users

```
GET /api/v1/users/
```

Response:

```json
[
  {
    "id": 1,
    "username": "user1",
    "email": "user1@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "is_active": true,
    "date_joined": "2023-01-01T00:00:00Z"
  },
  ...
]
```

#### Get User Details

```
GET /api/v1/users/{id}/
```

Response:

```json
{
  "id": 1,
  "username": "user1",
  "email": "user1@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "is_active": true,
  "date_joined": "2023-01-01T00:00:00Z"
}
```

#### Create User

```
POST /api/v1/users/
```

Request:

```json
{
  "username": "newuser",
  "email": "newuser@example.com",
  "password": "securepassword",
  "first_name": "Jane",
  "last_name": "Smith"
}
```

#### Update User

```
PUT /api/v1/users/{id}/
```

Request:

```json
{
  "email": "updated@example.com",
  "first_name": "Updated",
  "last_name": "Name"
}
```

#### Delete User

```
DELETE /api/v1/users/{id}/
```

### VPN Accounts

#### List VPN Accounts

```
GET /api/v1/vpn-accounts/
```

Response:

```json
[
  {
    "id": 1,
    "user": 1,
    "protocol": "vmess",
    "server": "server1",
    "port": 443,
    "uuid": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "created_at": "2023-01-01T00:00:00Z",
    "expires_at": "2023-02-01T00:00:00Z",
    "traffic_limit": 100000000000,
    "traffic_used": 1000000000,
    "is_active": true
  },
  ...
]
```

#### Get VPN Account Details

```
GET /api/v1/vpn-accounts/{id}/
```

Response:

```json
{
  "id": 1,
  "user": 1,
  "protocol": "vmess",
  "server": "server1",
  "port": 443,
  "uuid": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "created_at": "2023-01-01T00:00:00Z",
  "expires_at": "2023-02-01T00:00:00Z",
  "traffic_limit": 100000000000,
  "traffic_used": 1000000000,
  "is_active": true
}
```

#### Create VPN Account

```
POST /api/v1/vpn-accounts/
```

Request:

```json
{
  "user": 1,
  "protocol": "vmess",
  "server": "server1",
  "traffic_limit": 100000000000,
  "expires_at": "2023-02-01T00:00:00Z"
}
```

#### Update VPN Account

```
PUT /api/v1/vpn-accounts/{id}/
```

Request:

```json
{
  "traffic_limit": 200000000000,
  "expires_at": "2023-03-01T00:00:00Z",
  "is_active": true
}
```

#### Delete VPN Account

```
DELETE /api/v1/vpn-accounts/{id}/
```

### Payments

#### List Payments

```
GET /api/v1/payments/
```

Response:

```json
[
  {
    "id": 1,
    "user": 1,
    "amount": 10000,
    "currency": "IRR",
    "payment_method": "zarinpal",
    "status": "completed",
    "created_at": "2023-01-01T00:00:00Z",
    "updated_at": "2023-01-01T00:01:00Z",
    "transaction_id": "12345678"
  },
  ...
]
```

#### Get Payment Details

```
GET /api/v1/payments/{id}/
```

Response:

```json
{
  "id": 1,
  "user": 1,
  "amount": 10000,
  "currency": "IRR",
  "payment_method": "zarinpal",
  "status": "completed",
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:01:00Z",
  "transaction_id": "12345678"
}
```

#### Create Payment

```
POST /api/v1/payments/
```

Request:

```json
{
  "user": 1,
  "amount": 10000,
  "currency": "IRR",
  "payment_method": "zarinpal"
}
```

Response:

```json
{
  "id": 1,
  "user": 1,
  "amount": 10000,
  "currency": "IRR",
  "payment_method": "zarinpal",
  "status": "pending",
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z",
  "payment_url": "https://zarinpal.com/pg/StartPay/12345678"
}
```

#### Verify Payment

```
GET /api/v1/payments/verify/?payment_id=1&authority=12345678&status=OK
```

Response:

```json
{
  "id": 1,
  "user": 1,
  "amount": 10000,
  "currency": "IRR",
  "payment_method": "zarinpal",
  "status": "completed",
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:01:00Z",
  "transaction_id": "12345678"
}
```

### Plans

#### List Plans

```
GET /api/v1/plans/
```

Response:

```json
[
  {
    "id": 1,
    "name": "Basic",
    "description": "Basic plan with 30GB traffic",
    "price": 10000,
    "currency": "IRR",
    "duration_days": 30,
    "traffic_limit": 30000000000,
    "is_active": true
  },
  ...
]
```

#### Get Plan Details

```
GET /api/v1/plans/{id}/
```

Response:

```json
{
  "id": 1,
  "name": "Basic",
  "description": "Basic plan with 30GB traffic",
  "price": 10000,
  "currency": "IRR",
  "duration_days": 30,
  "traffic_limit": 30000000000,
  "is_active": true
}
```

### Servers

#### List Servers

```
GET /api/v1/servers/
```

Response:

```json
[
  {
    "id": 1,
    "name": "Server 1",
    "host": "server1.example.com",
    "location": "Netherlands",
    "is_active": true
  },
  ...
]
```

#### Get Server Details

```
GET /api/v1/servers/{id}/
```

Response:

```json
{
  "id": 1,
  "name": "Server 1",
  "host": "server1.example.com",
  "location": "Netherlands",
  "is_active": true
}
```

## Error Handling

The API returns standard HTTP status codes to indicate the success or failure of a request.

### Common Error Codes

- `400 Bad Request`: The request was invalid or cannot be served.
- `401 Unauthorized`: Authentication is required and has failed or has not been provided.
- `403 Forbidden`: The request is understood, but it has been refused or access is not allowed.
- `404 Not Found`: The requested resource could not be found.
- `500 Internal Server Error`: An error occurred on the server.

### Error Response Format

```json
{
  "detail": "Error message"
}
```

or

```json
{
  "field_name": [
    "Error message"
  ]
}
```

## Rate Limiting

The API implements rate limiting to prevent abuse. The current limits are:

- 100 requests per minute for authenticated users
- 20 requests per minute for unauthenticated users

When a rate limit is exceeded, the API returns a `429 Too Many Requests` response with a `Retry-After` header indicating how long to wait before making another request.

## Pagination

List endpoints support pagination using the `limit` and `offset` query parameters:

```
GET /api/v1/users/?limit=10&offset=0
```

Response:

```json
{
  "count": 100,
  "next": "https://your-domain.com/api/v1/users/?limit=10&offset=10",
  "previous": null,
  "results": [
    ...
  ]
}
```

## Filtering

Many list endpoints support filtering using query parameters:

```
GET /api/v1/vpn-accounts/?is_active=true
```

## Sorting

List endpoints support sorting using the `ordering` query parameter:

```
GET /api/v1/payments/?ordering=-created_at
```

Use a minus sign (`-`) to indicate descending order. 