# Security Documentation

## Overview

This document provides comprehensive documentation for the security features implemented in the MoonVPN system. The security system includes multiple layers of protection to ensure the safety and integrity of the application.

## Core Components

### 1. Security Monitoring Service

The Security Monitoring Service provides real-time monitoring of security events and suspicious activities.

#### Features:
- Failed login attempt monitoring
- API error rate monitoring
- Suspicious IP detection
- Critical event monitoring
- Alert generation and management

#### Configuration:
```python
MONITORING_ENABLED = True
MONITORING_INTERVAL_SECONDS = 60
ALERT_THRESHOLDS = {
    "failed_login": 5,
    "api_errors": 10,
    "suspicious_ip": 3,
    "critical_events": 1
}
```

### 2. Notification Service

The Notification Service handles security alert distribution through multiple channels.

#### Supported Channels:
- Email notifications
- Webhook notifications
- SMS notifications (placeholder)
- Telegram notifications

#### Configuration:
```python
EMAIL_CONFIG = {
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
    "smtp_user": "",
    "smtp_password": "",
    "from_email": "security@moonvpn.com",
    "to_email": "admin@moonvpn.com"
}

WEBHOOK_CONFIG = {
    "url": "",
    "headers": {
        "Content-Type": "application/json"
    }
}

TELEGRAM_CONFIG = {
    "bot_token": "",
    "chat_id": "",
    "parse_mode": "HTML"
}
```

### 3. Security Middleware

The Security Middleware provides request-level security features.

#### Features:
- Rate limiting
- Security headers
- Suspicious request detection
- Request logging
- IP blocking

#### Configuration:
```python
RATE_LIMIT_ENABLED = True
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX_REQUESTS = 100
RATE_LIMIT_BLOCK_DURATION = 300  # seconds

SECURITY_HEADERS = {
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": "default-src 'self'",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
}
```

### 4. Authentication & Authorization

#### Features:
- JWT-based authentication
- Two-factor authentication
- Role-based access control
- Session management

#### Configuration:
```python
JWT_SECRET_KEY = "your-secret-key"
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30
JWT_REFRESH_TOKEN_EXPIRE_DAYS = 7

TWO_FACTOR_ENABLED = True
TWO_FACTOR_ISSUER = "MoonVPN"
TWO_FACTOR_ALGORITHM = "SHA1"
TWO_FACTOR_DIGITS = 6
TWO_FACTOR_PERIOD = 30
```

### 5. Data Protection

#### Features:
- Data encryption
- Key rotation
- Secure storage
- Data validation

#### Configuration:
```python
ENCRYPTION_KEY_ROTATION_DAYS = 30
ENCRYPTION_ALGORITHM = "AES-256-GCM"
ENCRYPTION_KEY_LENGTH = 32
ENCRYPTION_IV_LENGTH = 12
```

## Usage

### 1. Initializing Security Services

```python
from core.security.init import init_security

# Initialize security for your FastAPI app
init_security(app)
```

### 2. Monitoring Security Events

```python
from core.services.security_monitoring import SecurityMonitoringService

# Create monitoring service instance
monitoring_service = SecurityMonitoringService(db)

# Start monitoring
await monitoring_service.start_monitoring()

# Create security alert
await monitoring_service._create_alert(
    severity="high",
    message="Security breach detected",
    details={"event_type": "breach", "details": "..."}
)
```

### 3. Sending Security Notifications

```python
from core.services.notification import NotificationService

# Create notification service instance
notification_service = NotificationService()

# Send alert through multiple channels
await notification_service.send_alert(
    severity="high",
    message="Security alert",
    details={"event": "..."},
    channels=["email", "webhook", "telegram"]
)

# Send to admin group
await notification_service.send_to_admin_group(
    group_id="SECURITY",
    message="Admin notification",
    channels=["email", "telegram"]
)
```

### 4. Using Security Middleware

The security middleware is automatically added to your FastAPI application when you initialize security services. It provides:

- Rate limiting
- Security headers
- Suspicious request detection
- Request logging

No additional configuration is required.

## Best Practices

1. **Configuration Management**
   - Store sensitive configuration in environment variables
   - Use secure secret management
   - Regularly rotate secrets and keys

2. **Monitoring**
   - Monitor security events regularly
   - Set up alerts for critical events
   - Review security logs periodically

3. **Access Control**
   - Implement least privilege principle
   - Use strong passwords
   - Enable two-factor authentication
   - Regular access review

4. **Data Protection**
   - Encrypt sensitive data
   - Regular key rotation
   - Secure data storage
   - Data validation

5. **Network Security**
   - Use HTTPS
   - Implement rate limiting
   - Block suspicious IPs
   - Regular security updates

## Troubleshooting

### Common Issues

1. **Rate Limiting Issues**
   - Check rate limit configuration
   - Verify IP address detection
   - Review rate limit logs

2. **Notification Failures**
   - Verify notification service configuration
   - Check network connectivity
   - Review service logs

3. **Authentication Problems**
   - Verify JWT configuration
   - Check token expiration
   - Review authentication logs

4. **Monitoring Issues**
   - Verify monitoring service status
   - Check database connectivity
   - Review monitoring logs

### Logging

Security events are logged with the following levels:
- INFO: Normal security events
- WARNING: Suspicious activities
- ERROR: Security violations
- CRITICAL: Critical security events

Logs can be found in:
- Application logs
- Security event logs
- Audit logs

## Security Checklist

### Initial Setup
- [ ] Configure security settings
- [ ] Set up monitoring service
- [ ] Configure notification channels
- [ ] Enable security middleware
- [ ] Set up authentication
- [ ] Configure data encryption

### Regular Maintenance
- [ ] Review security logs
- [ ] Update security configurations
- [ ] Rotate encryption keys
- [ ] Update dependencies
- [ ] Review access controls
- [ ] Test security features

### Incident Response
- [ ] Monitor security events
- [ ] Investigate suspicious activities
- [ ] Block malicious IPs
- [ ] Update security rules
- [ ] Document security incidents
- [ ] Review security measures

## Support

For security-related issues or questions:
1. Contact the security team
2. Review security documentation
3. Check security logs
4. Follow incident response procedures 