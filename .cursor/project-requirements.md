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