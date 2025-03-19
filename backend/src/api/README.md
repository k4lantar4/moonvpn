# V2Ray Management API

This document provides an overview of the API endpoints available for managing V2Ray accounts, servers, and payments.

## Authentication

The API uses token-based authentication. To obtain a token, send a POST request to:

```
POST /api-token-auth/
```

With the following JSON body:
```json
{
  "username": "your_username",
  "password": "your_password"
}
```

The response will contain your token:
```json
{
  "token": "your_auth_token"
}
```

Include this token in the Authorization header for all subsequent requests:
```
Authorization: Token your_auth_token
```

## API Endpoints

### Users

- `GET /api/users/` - List all users (admin only)
- `POST /api/users/` - Create a new user (admin only)
- `GET /api/users/{id}/` - Get user details (admin only)
- `PUT /api/users/{id}/` - Update user (admin only)
- `DELETE /api/users/{id}/` - Delete user (admin only)
- `POST /api/users/{id}/add_balance/` - Add balance to user wallet (admin only)
- `POST /api/users/{id}/deduct_balance/` - Deduct balance from user wallet (admin only)
- `GET /api/users/me/` - Get current user details

### Servers

- `GET /api/servers/` - List all servers (admin only)
- `POST /api/servers/` - Create a new server (admin only)
- `GET /api/servers/{id}/` - Get server details (admin only)
- `PUT /api/servers/{id}/` - Update server (admin only)
- `DELETE /api/servers/{id}/` - Delete server (admin only)
- `POST /api/servers/{id}/sync/` - Sync server with 3x-UI panel (admin only)
- `GET /api/servers/{id}/inbounds/` - Get server inbounds (admin only)
- `GET /api/servers/{id}/sync_logs/` - Get server sync logs (admin only)

### Subscription Plans

- `GET /api/subscription-plans/` - List all subscription plans (admin only)
- `POST /api/subscription-plans/` - Create a new subscription plan (admin only)
- `GET /api/subscription-plans/{id}/` - Get subscription plan details (admin only)
- `PUT /api/subscription-plans/{id}/` - Update subscription plan (admin only)
- `DELETE /api/subscription-plans/{id}/` - Delete subscription plan (admin only)

### Subscriptions

- `GET /api/subscriptions/` - List all subscriptions (admin only)
- `POST /api/subscriptions/` - Create a new subscription (admin only)
- `GET /api/subscriptions/{id}/` - Get subscription details (admin only)
- `PUT /api/subscriptions/{id}/` - Update subscription (admin only)
- `DELETE /api/subscriptions/{id}/` - Delete subscription (admin only)
- `POST /api/subscriptions/{id}/create_client/` - Create client in 3x-UI panel (admin only)
- `POST /api/subscriptions/{id}/delete_client/` - Delete client from 3x-UI panel (admin only)
- `POST /api/subscriptions/{id}/update_traffic/` - Update client traffic limit (admin only)
- `POST /api/subscriptions/{id}/update_expiry/` - Update client expiry time (admin only)
- `POST /api/subscriptions/{id}/reset_traffic/` - Reset client traffic usage (admin only)

### Inbounds (Read-only)

- `GET /api/inbounds/` - List all inbounds (admin only)
- `GET /api/inbounds/{id}/` - Get inbound details (admin only)
- `GET /api/inbounds/{id}/clients/` - Get inbound clients (admin only)

### Clients (Read-only)

- `GET /api/clients/` - List all clients (admin only)
- `GET /api/clients/{id}/` - Get client details (admin only)
- `GET /api/clients/{id}/config/` - Get client config (admin only)

### Transactions

- `GET /api/transactions/` - List all transactions (admin only)
- `POST /api/transactions/` - Create a new transaction (admin only)
- `GET /api/transactions/{id}/` - Get transaction details (admin only)
- `PUT /api/transactions/{id}/` - Update transaction (admin only)
- `DELETE /api/transactions/{id}/` - Delete transaction (admin only)

### Card Payments

- `GET /api/card-payments/` - List all card payments (admin only)
- `POST /api/card-payments/` - Create a new card payment (admin only)
- `GET /api/card-payments/{id}/` - Get card payment details (admin only)
- `PUT /api/card-payments/{id}/` - Update card payment (admin only)
- `DELETE /api/card-payments/{id}/` - Delete card payment (admin only)
- `POST /api/card-payments/{id}/verify/` - Verify a card payment (admin only)
- `POST /api/card-payments/{id}/reject/` - Reject a card payment (admin only)
- `GET /api/card-payments/pending/` - Get pending card payments (admin only)
- `POST /api/card-payments/expire_old/` - Expire old pending card payments (admin only)

### Zarinpal Payments (Read-only)

- `GET /api/zarinpal-payments/` - List all Zarinpal payments (admin only)
- `GET /api/zarinpal-payments/{id}/` - Get Zarinpal payment details (admin only)

### Payment Methods

- `GET /api/payment-methods/` - List all payment methods (admin only)
- `POST /api/payment-methods/` - Create a new payment method (admin only)
- `GET /api/payment-methods/{id}/` - Get payment method details (admin only)
- `PUT /api/payment-methods/{id}/` - Update payment method (admin only)
- `DELETE /api/payment-methods/{id}/` - Delete payment method (admin only)

### Discounts

- `GET /api/discounts/` - List all discounts (admin only)
- `POST /api/discounts/` - Create a new discount (admin only)
- `GET /api/discounts/{id}/` - Get discount details (admin only)
- `PUT /api/discounts/{id}/` - Update discount (admin only)
- `DELETE /api/discounts/{id}/` - Delete discount (admin only)
- `GET /api/discounts/{id}/validate/` - Validate a discount code (admin only)

### Telegram Messages

- `GET /api/telegram-messages/` - List all Telegram messages (admin only)
- `POST /api/telegram-messages/` - Create a new Telegram message (admin only)
- `GET /api/telegram-messages/{id}/` - Get Telegram message details (admin only)
- `PUT /api/telegram-messages/{id}/` - Update Telegram message (admin only)
- `DELETE /api/telegram-messages/{id}/` - Delete Telegram message (admin only)

### Telegram Notifications

- `GET /api/telegram-notifications/` - List all Telegram notifications (admin only)
- `POST /api/telegram-notifications/` - Create a new Telegram notification (admin only)
- `GET /api/telegram-notifications/{id}/` - Get Telegram notification details (admin only)
- `PUT /api/telegram-notifications/{id}/` - Update Telegram notification (admin only)
- `DELETE /api/telegram-notifications/{id}/` - Delete Telegram notification (admin only)

## Filtering, Searching, and Ordering

Most endpoints support filtering, searching, and ordering:

- **Filtering**: Use query parameters matching model fields (e.g., `?status=active`)
- **Searching**: Use the `search` parameter (e.g., `?search=keyword`)
- **Ordering**: Use the `ordering` parameter (e.g., `?ordering=created_at` or `?ordering=-created_at` for descending order)

## Pagination

API responses are paginated with 20 items per page by default. The response includes:

```json
{
  "count": 100,
  "next": "http://example.com/api/resource/?page=2",
  "previous": null,
  "results": [
    // items
  ]
}
```

Use the `page` parameter to navigate between pages (e.g., `?page=2`). 