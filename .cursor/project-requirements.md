# MoonVPN Project Requirements 🚀 (v3 - Bot-Centric Architecture)

**Version:** 0.1.0  
**Last Updated:** 2025-04-10

## 1. Overview

MoonVPN is a comprehensive VPN service management platform operated through Telegram. It enables users to purchase, manage, and use VPN services, while providing administrators with tools to manage panels, inbounds, plans, and track user activity.

## 2. User Roles

1. **User**: Standard users who can register, purchase plans, and manage their VPN accounts.
2. **Admin**: System administrators with full access to all features including panel management, user management, and analytics.
3. **Seller**: (Future) Partners who can sell VPN plans and earn commission.

## 3. Core Functionality

### 3.1. User Management

- User registration and profile management
- User authentication and role-based access control
- User activity tracking
- Balance and payment management

### 3.2. Panel Management

- Add, edit, and remove VPN panels (3x-ui)
- Configure panel settings (server URL, credentials)
- Monitor panel status and health
- Sync inbounds from panels

### 3.3. Client Account Management

- Create VPN client accounts on panels
- Renew, reset, and monitor client accounts
- Generate and distribute configuration files
- Track client usage and expiration

### 3.4. Plan System

- Create and manage subscription plans
- Configure durations, prices, and traffic limits
- Categorize plans by type and features
- Restrict plan availability by location

### 3.5. Payment & Wallet System

- Wallet-based credit system for users
- Process payments via multiple gateways
- Track transactions and payment history
- Handle refunds and adjustments
- Apply discount codes to purchases
- Track discount usage and validate restrictions

### 3.6. Location Management

- Add and manage server locations
- Associate panels with specific locations
- Filter plans and clients by location

### 3.7. Notification System

- Send automated notifications for:
  - Account expiration
  - Traffic limits
  - Successful purchases
  - System announcements
- Configure notification channels and templates

### 3.8. Admin Dashboard

- Monitor system health and statistics
- Track sales and revenue
- User activity reports
- Troubleshoot client issues

### 3.9. Settings Management

- Configure global system settings
- Manage feature flags and toggles
- Control system behavior and defaults
- Configure maintenance mode

### 3.10. Order Management

- Process plan purchases from users
- Track order status (pending, completed, failed)
- Apply discount codes during checkout
- Associate orders with client accounts
- Generate order history and reports

### 3.11. Discount Code System

- Create and manage discount codes
- Support percentage and fixed-amount discounts
- Set validity periods and usage limits
- Track discount code usage
- Enable/disable codes as needed

## 4. Bot Interface

### 4.1. User Commands

- `/start` - Initialize bot and see main menu
- `/help` - Get assistance and command list
- `/register` - Create a new user account
- `/profile` - View and edit profile
- `/plans` - Browse available plans
- `/locations` - See available locations
- `/buy` - Purchase a new VPN account
- `/myaccounts` - Manage existing VPN accounts
- `/extend` - Extend account duration
- `/reset` - Reset account traffic
- `/wallet` - Manage wallet and payments
- `/config` - Get configuration details
- `/settings` - Manage user settings

### 4.2. Admin Commands

- `/admin` - Access admin panel
- `/users` - Manage users
- `/panels` - Manage VPN panels
- `/inbounds` - Manage panel inbounds
- `/adminplans` - Manage subscription plans
- `/adminlocations` - Manage locations
- `/transactions` - View transaction history
- `/stats` - View system statistics
- `/broadcast` - Send announcements
- `/settings` - Configure system settings
- `/discounts` - Manage discount codes
- `/orders` - View and manage orders

## 5. Data Model

### 5.1. Core Entities

1. **User**
   - Basic information (ID, username, name)
   - Role (user, admin, seller)
   - Registration date
   - Status (active, blocked)
   - Wallet balance
   - Settings preferences

2. **Panel**
   - Configuration (URL, username, password)
   - Status (active, inactive, error)
   - Type (3x-ui)
   - Location ID
   - Statistics (load, clients)

3. **PanelInbound**
   - Panel ID
   - Inbound ID (as defined on panel)
   - Protocol (VMess, Trojan, etc.)
   - Tags and metadata
   - Status (active, full, inactive)
   - Traffic allocation

4. **ClientAccount**
   - User ID
   - Plan ID
   - Panel ID
   - Inbound ID
   - Creation date
   - Expiration date
   - Traffic allocation
   - Traffic used
   - Configuration details
   - Status (active, expired, disabled)

5. **Plan**
   - Name and description
   - Duration (days)
   - Traffic allocation (GB)
   - Price
   - Features and limitations
   - Locations (available at)
   - Status (active, inactive)

6. **Location**
   - Name
   - Country
   - Status (active, inactive)
   - Associated panels

7. **Transaction**
   - User ID
   - Amount
   - Type (deposit, purchase, refund)
   - Status (pending, completed, failed)
   - Timestamp
   - Payment gateway details
   - Reference information

8. **Notification**
   - User ID
   - Type
   - Content
   - Status (sent, failed)
   - Timestamp
   - Channel (Telegram, email)

9. **Setting**
   - Key
   - Value
   - Type (string, number, boolean, json)
   - Scope (system, user)
   - Description

10. **Order**
    - User ID
    - Plan ID
    - Location ID
    - Amount
    - Discount amount (if applicable)
    - Final amount
    - Status (pending, processing, completed, failed, cancelled)
    - Related client account ID
    - Timestamps (created, updated, processed)
    - Discount code ID (if used)

11. **DiscountCode**
    - Code (unique identifier)
    - Description
    - Discount type (percentage, fixed amount)
    - Discount value
    - Start date
    - End date
    - Maximum uses
    - Current use count
    - Status (active, inactive)
    - Minimum order amount (if applicable)
    - Maximum discount amount (for percentage discounts)

### 5.2. Entity Relationships

- User 1:N ClientAccount
- User 1:N Transaction
- User 1:N Order
- Panel 1:N PanelInbound
- Panel 1:N ClientAccount
- PanelInbound 1:N ClientAccount
- Plan 1:N ClientAccount
- Plan 1:N Order
- Location 1:N Panel
- DiscountCode 1:N Order

### 5.3. Repositories

For each entity, implement a repository that handles:
- CRUD operations
- Complex queries
- Relationship management
- Data validation
- Transaction handling

## 6. Services

### 6.0. Service Architecture Principles

Services follow these key architectural principles:

1. **Dependency Injection**
   - Database sessions (AsyncSession) are injected into services via constructor
   - Services should never create their own database sessions 
   - Services never use `_get_db()` or similar methods to obtain sessions
   - Services store the session as `self.db` for use in methods

2. **Repository Usage**
   - Services use repositories for data access operations
   - Repositories are initialized in the service constructor
   - Services pass `self.db` to repository methods, not storing sessions in repo instances

3. **Transaction Management**
   - Services assume callers (handlers) are responsible for transaction boundaries
   - Services do not call `await session.commit()` except in background tasks
   - Methods that perform multiple operations needing atomicity use `await self.db.flush()`
   - Background/periodic tasks create dedicated sessions and manage their own transactions

4. **Error Handling**
   - Services convert repository/database errors to service-level exceptions
   - Services use appropriate logging for errors and operations
   - Services document expected exceptions in method docstrings

### 6.1. Core Services

1. **UserService**
   - User registration and authentication
   - Profile management
   - Role and permission handling

2. **PanelService**
   - Panel management and configuration
   - Panel health monitoring
   - Inbound synchronization
   - Panel selection for client provisioning

3. **ClientService**
   - Client account creation
   - Traffic monitoring and renewal
   - Configuration generation
   - Client status management

4. **PlanService**
   - Plan management
   - Plan filtering by location
   - Plan recommendation

5. **PaymentService**
   - Payment processing
   - Wallet management
   - Transaction recording
   - Receipt generation

6. **NotificationService**
   - Send notifications across channels
   - Manage templates
   - Track delivery status

7. **SettingService**
   - Manage system and user settings
   - Validate setting values
   - Apply settings to system behavior

8. **LocationService**
   - Location management
   - Location-based filtering

9. **DiscountCodeService**
   - Create, edit, and list discount codes
   - Validate discount codes
   - Apply discounts to purchases
   - Track discount usage
   - Activate/deactivate discount codes

10. **OrderService**
    - Create orders for plan purchases
    - Process payment for orders
    - Apply discount codes during checkout
    - Track order status changes
    - Associate completed orders with client accounts
    - Generate order statistics for admin dashboard

### 6.2. Integration Services

1. **XuiPanelClient**
   - Authenticate with 3x-ui panel
   - Fetch panel statistics
   - Manage inbounds
   - Add/modify/remove clients
   - Monitor client traffic

2. **PaymentGatewayClient**
   - Process payments through external gateways
   - Verify payment status
   - Handle callbacks and webhooks

## 7. Development Phases

### Phase 1: Bot Basics & Panel/Location Management (Completed)
- Set up bot framework and command structure
- Implement user registration and roles
- Develop panel management features
- Create location management system
- Establish database models and repositories

### Phase 2: Full Repository & Service Layer Implementation (Completed)
- Implement all core data models
- Develop repository layer with full CRUD operations
- Create service layer with business logic
- Set up integration clients for panels
- Establish a runnable project structure

### Phase 3: Client Management & Plan System (In Progress)
- Implement plan creation and management
- Develop client account provisioning
- Set up traffic monitoring and renewal
- Create configuration generation and delivery
- Implement location-based filtering

### Phase 4: Payment, Orders & Discount System (Planned)
- Develop wallet and payment system
- Implement transaction tracking
- Create order processing flow
- Develop discount code management
- Integrate payment gateways

### Phase 5: Advanced Features & UI Refinement (Planned)
- Add notifications system
- Implement admin dashboard
- Develop analytics and reporting
- Refine user interface and experience
- Add multi-language support
- Implement seller system and commissions

## 8. Technical Requirements

### 8.1. Core Technologies

- Python 3.10+
- aiogram 3.x (Telegram Bot Framework)
- SQLAlchemy 2.0+ (ORM)
- Alembic (Database Migrations)
- Pydantic 2.0+ (Data Validation)
- aiohttp (HTTP Client)
- Redis (Caching, Session Storage)
- MySQL 8.0+ (Database)
- Docker & Docker Compose (Deployment)

### 8.2. Development Tools

- Git (Version Control)
- GitHub Actions (CI/CD)
- Poetry (Dependency Management)
- Black, isort, flake8 (Code Formatting)
- Pytest (Testing)
- Sentry (Error Tracking)
- Logging (Structured Logging)

## 9. Non-Functional Requirements

### 9.1. Performance

- Response time < 2 seconds for user commands
- Support for at least 1,000 concurrent users
- Handle up to 10,000 active client accounts

### 9.2. Security

- Secure storage of panel credentials
- Role-based access control for all commands
- Rate limiting to prevent abuse
- Input validation and sanitization
- Secure communication with external systems

### 9.3. Reliability

- 99.9% uptime for bot services
- Graceful error handling and recovery
- Regular database backups
- Comprehensive logging for troubleshooting

### 9.4. Usability

- Intuitive command structure
- Clear error messages
- Responsive and informative UI
- Multi-step operations with clear guidance
- Comprehensive help system

### 9.5. Maintainability

- Well-documented code and architecture
- Modular design with clear separation of concerns
- Comprehensive test coverage
- Clear upgrade and migration path
- Easy configuration management

## 10. Deployment & Operations

### 10.1. Deployment Strategy

- Docker-based deployment
- Single-server setup initially
- Environment-based configuration
- Automated database migrations
- Health checks and monitoring

### 10.2. Backup & Recovery

- Daily database backups
- Configuration backups
- Disaster recovery procedures
- Data retention policies

### 10.3. Monitoring & Alerting

- System health monitoring
- Error rate tracking
- Performance metrics
- Admin notifications for critical issues
- Usage statistics and trends

## 11. Conclusion

This requirements document outlines the core functionality, data model, and technical specifications for the MoonVPN project. It serves as a guide for development and a reference for project stakeholders. Requirements will be refined and expanded as development progresses. 