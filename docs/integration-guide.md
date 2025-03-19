# MoonVPN - 3x-UI Panel Integration Guide

## Overview

This document details the integration between MoonVPN and external 3x-UI panels for VPN account management. The 3x-UI panel is a web interface for managing V2Ray/XRay servers, and MoonVPN communicates with it to create, update, and monitor VPN accounts.

## Configuration

Integration with the 3x-UI panel requires the following configuration:

```
PANEL_HOST=vpn-panel.example.com
PANEL_PORT=2053
PANEL_USERNAME=admin
PANEL_PASSWORD=secure_password
PANEL_BASE_PATH=/
```

These settings should be configured in the `.env` file.

## API Client

The integration is handled primarily through the `bot/api_client.py` file, which implements a PanelClient class for communicating with the 3x-UI panel API. The client handles:

1. Authentication and session management
2. Client creation and configuration
3. Traffic monitoring and reporting
4. Server status checking

## Authentication Flow

1. The PanelClient logs in to the 3x-UI panel using the configured credentials
2. It maintains a session cookie for subsequent requests
3. If a session expires, it automatically re-authenticates

## Account Management

The integration supports the following operations:

### Creating Accounts

```python
await panel_client.create_client(
    email=user_email,
    uuid=unique_id,
    subscription_days=30,
    traffic_limit=100
)
```

### Checking Account Status

```python
status = await panel_client.get_client_status(email=user_email)
```

### Updating Traffic Limits

```python
await panel_client.update_client_traffic(
    email=user_email,
    new_traffic_limit=200
)
```

### Renewing Accounts

```python
await panel_client.renew_client(
    email=user_email,
    additional_days=30
)
```

### Retrieving Traffic Usage

```python
usage = await panel_client.get_client_traffic(email=user_email)
```

## Error Handling

The API client implements comprehensive error handling:

1. Connection errors with automatic retry
2. Authentication failures with re-authentication
3. Rate limiting detection and backoff
4. Validation errors with detailed reporting

## Security Considerations

1. All communications use HTTPS
2. Credentials are stored in environment variables, not in code
3. Session cookies are stored securely
4. Requests are rate-limited to prevent abuse

## Troubleshooting

Common issues and their solutions:

1. **Connection Refused** - Check firewall settings and panel availability
2. **Authentication Failed** - Verify username and password
3. **Account Not Found** - Ensure the email is correctly formatted
4. **Rate Limiting** - Reduce request frequency

## Testing

A test script is available at `scripts/test_panel.py` to verify panel connectivity and API functionality. 