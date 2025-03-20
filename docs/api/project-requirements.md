# MoonVPN Project Requirements

## Project Information

- **Project Name**: MoonVPN
- **Description**: A comprehensive Telegram bot and web dashboard for selling and managing VPN accounts
- **Goals**: 
  - Create an intuitive interface for users to purchase and manage VPN accounts via Telegram
  - Develop an advanced admin dashboard for monitoring and managing the VPN service
  - Ensure secure integration with external 3x-UI panel for VPN account synchronization
  - Build a scalable and maintainable system architecture
- **Overview**: MoonVPN consists of a Telegram bot for user interactions, a FastAPI backend API, and a React frontend dashboard. The system integrates with external 3x-UI panels for VPN account management. The architecture follows modern API design with dependency injection, async operations, and type validation.

## List of Project Requirements

### Tech Stack
- **Backend**: 
  - Python 3.9+
  - FastAPI
  - SQLAlchemy ORM
  - Pydantic for data validation
  - Alembic for migrations
  - Python-telegram-bot v20+
  - PostgreSQL
  - Redis for caching
- **Frontend**: 
  - React 18.x
  - Modern UI libraries
  - Responsive design
- **Deployment**: 
  - Docker and Docker Compose
  - Nginx for reverse proxy
  - SSL/TLS encryption

### Functionality
- **Telegram Bot**:
  - User registration and authentication
  - VPN account purchase flow
  - Status checking and management
  - Server location selection
  - Support request handling
  - Admin commands for system management
- **Backend API**:
  - RESTful endpoints with automatic OpenAPI documentation
  - Async API support for improved performance
  - Type-validated request/response with Pydantic
  - Dependency injection for services
  - Integration with 3x-UI panel
  - SQLAlchemy models for users, accounts, servers
  - Payment processing
  - Monitoring and analytics
- **Admin Dashboard**:
  - Real-time analytics
  - User management
  - Server monitoring
  - Transaction logs
  - Discount management
  - Financial reporting
  - Bulk messaging

### Security
- JWT authentication for API
- HTTPS for all communications
- Encrypted storage for sensitive data
- Role-based access control
- Rate limiting and brute force protection

### Performance
- Asynchronous API endpoints for improved concurrency
- Optimized database queries with SQLAlchemy
- Redis caching for frequently accessed data
- Background tasks for long-running operations
- Dependency injection for optimized service instantiation
- Monitoring and logging for performance bottlenecks

### Integration
- 3x-UI Panel integration via API
- Payment gateways (card-to-card, optional Zarinpal)
- Notification systems (email, Telegram)

## Roadmap

### Phase 1: Foundation Setup (Completed)
- Project structure organization
- Database schema design
- Docker configuration
- Basic backend API endpoints
- Authentication system

### Phase 2: Framework Migration (Current)
- Migrate from Django to FastAPI
- Implement SQLAlchemy models
- Create Pydantic schemas
- Setup Alembic migrations
- Ensure API compatibility

### Phase 3: Core Bot Functionality
- Implement essential bot commands
- Create user flows for account purchase
- Integrate with 3x-UI panel
- Build payment processing

### Phase 4: Admin Dashboard
- Develop frontend interface
- Create analytics components
- Implement user management features
- Build server monitoring views

### Phase 5: Advanced Features
- Implement discount system
- Add bulk messaging
- Create detailed reporting
- Enhance security features

### Phase 6: Testing & Deployment
- Comprehensive testing
- Documentation completion
- Production deployment setup
- Monitoring and alerting configuration 

moonvpn/
├── core/                    # Core application components
│   ├── database/           # Database models and migrations
│   ├── services/           # Core services
│   ├── tests/              # Test files
│   ├── config/             # Configuration files
│   └── middlewares/        # Middleware components
├── api/                    # API endpoints
│   ├── v1/                # API version 1
│   │   ├── endpoints/     # API endpoints
│   │   ├── schemas/       # Pydantic schemas
│   │   └── dependencies/  # API dependencies
│   └── docs/              # API documentation
├── frontend/              # Frontend application
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── hooks/        # Custom hooks
│   │   ├── services/     # API services
│   │   ├── store/        # State management
│   │   ├── types/        # TypeScript types
│   │   └── utils/        # Utility functions
│   └── public/           # Static files
├── bot/                   # Telegram bot
│   ├── handlers/         # Command handlers
│   ├── keyboards/        # Inline keyboards
│   └── utils/           # Bot utilities
├── docs/                  # Documentation
├── docker/                # Docker configuration
├── logs/                  # Application logs
└── .cursor/              # Cursor IDE configuration 

## Core Requirements

### 1. VPN Service
- [x] VPN account management
- [x] Server management
- [x] Traffic monitoring
- [x] Subscription handling
- [ ] Automated server health checks
- [ ] Load balancing
- [ ] Failover support

### 2. Payment System
- [x] Multiple payment gateways
- [x] Subscription management
- [x] Invoice generation
- [x] Payment verification
- [ ] Automated refunds
- [ ] Payment dispute handling
- [ ] Tax calculation

### 3. Points System
- [x] Points earning
- [x] Points redemption
- [x] Points history
- [x] Reward rules
- [ ] Points expiration
- [ ] Points transfer
- [ ] Points analytics

### 4. Live Chat
- [x] Real-time messaging
- [x] Operator management
- [x] Chat history
- [x] Rating system
- [ ] File sharing
- [ ] Chat analytics
- [ ] Automated responses

### 5. API System
- [x] API key management
- [x] Rate limiting
- [x] Request logging
- [x] Webhook support
- [ ] API analytics
- [ ] API documentation
- [ ] API versioning

### 6. Enhancement Features
- [x] System health monitoring
- [x] Automated backups
- [x] Notification system
- [x] Reporting system
- [x] System logging
- [x] Configuration management
- [x] System metrics
- [ ] Real-time alerts
- [ ] Performance optimization
- [ ] Resource scaling

### 7. Telegram Bot
- [ ] User authentication
- [ ] Account management
- [ ] Payment processing
- [ ] Support chat
- [ ] Points management
- [ ] System monitoring
- [ ] Admin commands
- [ ] Interactive menus
- [ ] Inline keyboards
- [ ] Command aliases

## Technical Requirements

### 1. Performance
- [x] FastAPI framework
- [x] SQLAlchemy ORM
- [x] Async operations
- [x] Connection pooling
- [ ] Caching system
- [ ] Load balancing
- [ ] CDN integration

### 2. Security
- [x] JWT authentication
- [x] Role-based access
- [x] Rate limiting
- [x] Input validation
- [ ] IP whitelisting
- [ ] DDoS protection
- [ ] SSL/TLS
- [ ] Security headers

### 3. Monitoring
- [x] Health checks
- [x] System metrics
- [x] Error logging
- [x] Audit trails
- [ ] Performance metrics
- [ ] User analytics
- [ ] System alerts

### 4. Development
- [x] Type hints
- [x] Code documentation
- [x] Error handling
- [x] Testing framework
- [ ] CI/CD pipeline
- [ ] Code quality checks
- [ ] Automated testing

## Dependencies

### Core Dependencies
- FastAPI
- SQLAlchemy
- Alembic
- Pydantic
- python-jose
- passlib
- python-multipart
- aiohttp
- python-telegram-bot
- apscheduler
- prometheus-client

### Development Dependencies
- pytest
- pytest-asyncio
- pytest-cov
- black
- isort
- flake8
- mypy
- pre-commit

## Next Steps
1. Implement Telegram bot integration
2. Set up automated monitoring
3. Enhance security features
4. Improve user experience
5. Add caching system
6. Implement CDN integration
7. Set up CI/CD pipeline
8. Add comprehensive testing 