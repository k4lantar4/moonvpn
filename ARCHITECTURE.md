# MoonVPN System Architecture 🏗️

This document outlines the architecture of the MoonVPN system, describing its components, interactions, and design decisions.

## System Overview

MoonVPN is designed as a modular, service-oriented system that connects Telegram users with V2Ray VPN services through a central management platform. The system integrates with 3x-ui panels for VPN service management while providing user management, payment processing, and administration through a Telegram bot interface.

### Key Components

1. **Telegram Bot** - User-facing interface with different capabilities based on user role
2. **FastAPI Backend** - Core business logic and data management
3. **3x-ui Panel Integration** - Connection to VPN service management panels
4. **MySQL Database** - Persistent data storage
5. **Redis Cache** - Performance optimization and rate limiting

## Component Architecture

### Telegram Bot (`bot/`)

The bot is structured in a modular fashion:

```
bot/
├── main.py              # Bot initialization and webhook setup
├── handlers/            # Command and callback query handlers
│   ├── user.py          # Regular user commands 
│   ├── admin.py         # Admin-specific commands
│   └── seller.py        # Seller-specific commands
├── keyboards.py         # UI keyboard definitions
├── channels.py          # Channel notification management
├── states.py            # Conversation state definitions
└── utils.py             # Helper functions
```

**Design Considerations:**
- Asynchronous implementation using python-telegram-bot v20+
- Conversation handlers for multi-step processes
- Role-based command access control
- Persian language throughout user interface
- Centralized keyboard definitions for consistency

### API Backend (`api/`)

The FastAPI backend handles business logic and provides endpoints:

```
api/
├── main.py              # FastAPI app initialization
├── routes/              # API route definitions
├── models.py            # SQLAlchemy ORM models
├── schemas.py           # Pydantic data validation schemas
├── services/            # Business logic services
└── dependencies.py      # Dependency injection functions
```

**Design Considerations:**
- Asynchronous API design for high performance
- Clean separation of routes and business logic
- Type validation with Pydantic
- Comprehensive API documentation via OpenAPI/Swagger
- JWT-based authentication
- Role-based access control

### Core Components (`core/`)

Shared functionality used across bot and API:

```
core/
├── config.py            # Configuration management
├── database.py          # Database connection and session management
├── security.py          # Authentication and encryption utilities
├── logging.py           # Centralized logging configuration
└── cache.py             # Redis cache integration
```

**Design Considerations:**
- Environment-based configuration with dotenv
- Centralized database session management
- Secure credential storage
- Structured logging with appropriate levels
- Performance optimization through caching

### External Integrations (`integrations/`)

Connections to external services:

```
integrations/
├── panels/              # 3x-ui panel integration
├── payments/            # Payment gateway integration (future)
└── sms.py               # SMS verification service (future)
```

**Design Considerations:**
- Resilient API clients with retry logic
- Connection pooling for performance
- Proper error handling and reporting
- Secure credential management
- Monitoring of external service health

## Data Flow

### User Registration Flow
1. User starts Telegram bot
2. Bot collects user information
3. API creates user record in database
4. Bot confirms registration

### Service Purchase Flow
1. User selects plan via bot
2. User selects payment method
3. For card-to-card:
   a. Bot displays card information
   b. User uploads receipt
   c. Receipt forwarded to admin for verification
   d. On approval, wallet credited
4. User selects location
5. System selects appropriate panel
6. API creates client on panel
7. Bot provides configuration to user

### Admin Panel Management Flow
1. Admin adds panel details via bot
2. API tests connection to panel
3. Panel added to database if connection successful
4. System begins monitoring panel health

## Design Principles

1. **Asynchronous Architecture** - Non-blocking operations for performance
2. **Separation of Concerns** - Modular design with clear responsibilities
3. **Security First** - Proper encryption, authentication, and validation
4. **User Experience Focus** - Intuitive Persian interfaces with helpful feedback
5. **Resilience** - Error handling and recovery mechanisms
6. **Scalability** - Docker-based deployment for easy scaling
7. **Maintainability** - Clean code, documentation, and testing

## Security Considerations

1. **Data Protection**
   - Encrypted panel credentials
   - JWT-based API authentication
   - Sensitive data handling according to best practices

2. **Access Control**
   - Role-based permissions in both bot and API
   - Proper validation of commands and inputs
   - Rate limiting to prevent abuse

3. **Monitoring & Logging**
   - Activity logging for audit purposes
   - Error reporting with appropriate detail level
   - Health checks and alerts

## Performance Considerations

1. **Database Optimization**
   - Proper indexing
   - Async database operations
   - Connection pooling

2. **Caching Strategy**
   - Redis for frequently accessed data
   - User session caching
   - Panel status caching

3. **Efficient API Design**
   - Pagination for large data sets
   - Selective field loading
   - Background processing for time-consuming tasks

## Future Architecture Extensions

1. **Horizontal Scaling**
   - Multiple bot instances behind load balancer
   - API service replication

2. **Service Monitoring**
   - Prometheus metrics collection
   - Grafana dashboards
   - Automated alerting

3. **Advanced Security**
   - Two-factor authentication
   - IP-based access restrictions
   - Advanced threat detection 