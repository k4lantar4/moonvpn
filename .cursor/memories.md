# MoonVPN Project Memories

- [v1.0.0] Development: Initialized project memories based on the provided project specifications from the previous role - MoonVPN is a Telegram bot and web dashboard for selling and managing VPN accounts built with Python, Django, React, Docker, and Redis, featuring comprehensive management capabilities including user commands (/start, /buy, /status, /change_location), API endpoints, admin dashboard with analytics, and secure integration with 3x-UI panel. The system uses a PostgreSQL database, has a modular architecture, and requires secure communication with external VPN panel for synchronizing accounts and managing server configurations. Previous implementation includes a Telegram bot interface for customers, Django-based backend API, React dashboard, Docker configuration, and security features like JWT authentication.

- [v1.0.1] Development: Created documentation for the project architecture, 3x-UI panel integration, and database schema. The architecture is based on a three-tier model with Telegram bot for user interaction, Django backend for business logic, and React dashboard for administration. The 3x-UI panel integration is handled through a custom PanelClient class that manages session cookies for persistent authentication. The database schema supports flexible server management and user migration, with models for users, servers, locations, VPN accounts, subscription plans, wallets, transactions, orders, and vouchers.

- [v1.0.2] Development: Analyzed requirements for dynamic server management and 3x-UI panel integration with session cookie handling. Identified that the 3x-UI panels use session-based authentication with cookies that must be persisted in the database. This approach allows for automatic re-authentication when sessions expire and provides a reliable mechanism for maintaining connections to multiple VPN panels simultaneously. The design supports dynamic server allocation based on location preferences and load factors, allowing for easy migration of users between servers when needed.

- [v1.0.3] Implementation: Implemented the core Django models following a database-driven approach for maximum flexibility. Created User, Server, Location, VPNAccount, Wallet, Transaction, Order, and Voucher models with appropriate relationships and business logic methods. Implemented PanelClient for 3x-UI panel integration with robust session cookie management, authentication, and error handling. Set up the Django project structure with settings, URLs, and configurations. Updated the Telegram bot to use Django models and created placeholder handlers for core commands. Set up Docker environment with containers for backend, bot, frontend, and nginx with proper networking and volume mounting.

### Project Context and Requirements [v1.0.0]
- Project Type: VPN Account Management & Sales System
- Core Components: Telegram Bot, Backend API, Frontend Panel, 3x-ui Panel Integration
- Main Features:
  1. Customer Features:
     - Service Purchase (Plans, Categories, Locations)
     - Service Management (Subscription Control)
     - Free Trial Account (One-time per user)
     - Free Telegram Proxy
     - Support Communication
     - Reseller Application
     - Connection Guides
     - Referral System
  2. Admin Features:
     - Dedicated Management Telegram Groups with bot admin:
       * MANAGE (🛡️): Critical notifications
       * REPORTS (📊): System statistics
       * LOGS (📄): User activities
       * TRANSACTIONS (💰): Payment tracking
       * OUTAGES (⚠️): Service issues
       * SELLERS (👥): Reseller management
       * BACKUPS (💾): Backup notifications
  3. Technical Requirements:
     - Phone Number Validation (+98)
     - Unique ID System for Subscriptions
     - Location Change Support
     - Multi-Payment Gateway
     - Credit System for Resellers
     - Automated Trial System

### Integration Notes [v1.0.0]
- 3x-ui Panel API Integration:
  * Base URL: /panel/api/inbounds
  * Key Endpoints: list, add, update, delete, client management
  * Traffic Management: resetClientTraffic, resetAllTraffics
  * Client Operations: addClient, updateClient, delClient
  * Monitoring: clientIps, onlines

### Development Approach [v1.0.0]
1. Clean up existing codebase
2. Implement core backend services
3. Enhance bot functionality
4. Develop admin management system
5. Implement payment integration
6. Add reseller functionality
7. Setup monitoring and backup systems

[2024-03-19 15:30] Development: Established core project architecture for MoonVPN with focus on 3x-ui panel integration. Created three main components: PanelManager for direct panel interaction with session/cookie management, ServerManager for centralized server control, and comprehensive data models (Server, ServerStatus, Client) for efficient data management and monitoring.

[2024-03-19 15:35] Architecture: Key project characteristics - No local VPN panels installed, all VPN operations handled through remote 3x-ui panel APIs. Each server has unique ID for database relations, system focuses on plan management and client account creation through API integration.

[2024-03-19 15:40] Technical: Implemented core service classes:
1. PanelManager: Handles authentication, system status, client management
2. ServerManager: Manages server fleet, status updates, load balancing
3. Data Models: Server, ServerStatus, Client with comprehensive metrics

[2024-03-19 15:45] Integration: Established connection pattern with 3x-ui panels:
- Authentication via username/password
- Session cookie management
- System metrics collection
- Client account operations
- Traffic monitoring

[2024-03-19 16:30] Analysis: Conducted comprehensive codebase analysis - identified duplicate implementations of core managers (TrafficManager, SecurityEnhancer, AnalyticsManager, BackupManager), redundant directory structures, and incomplete test files. Created optimization plan for restructuring project architecture and removing redundancies while maintaining functionality. Key findings: duplicate service implementations in bot/services and .cursor/scratchpad.md, multiple config directories, fragmented models, and unnecessary test files.

[2024-03-19 16:45] Refactoring: Completed comprehensive project analysis and created detailed refactoring plan - Identified and documented all duplicate code, redundant directories, and unnecessary files. Created new optimized project structure with clear separation of concerns, centralized services, and improved organization. Documented all changes in REFACTORING.md and updated project tracking in @scratchpad.md. Next phase will involve implementing the planned changes following the documented structure.

- [v1.0.4] Development: Started migration project from Django to FastAPI. Created project structure, Pydantic schemas, SQLAlchemy models, and Docker configuration. Set up key components including authentication system, user models, and base configuration. Created comprehensive requirements.txt with categorized dependencies for FastAPI, database libraries, authentication packages, and utility tools. Generated .env.example file with environment variables for application settings, security, database configuration, Redis, Telegram bot, and 3x-UI panel integration. Current migration progress includes completed project setup and core models/schemas with next steps focusing on API endpoints implementation, Telegram bot integration, and database migrations using Alembic.

- [v1.0.5] Development: Updated project-requirements.md to reflect the ongoing Django to FastAPI migration by modifying the tech stack section to replace Django with FastAPI and related technologies (SQLAlchemy, Pydantic, Alembic), updating the project overview to highlight modern API design patterns, enhancing the Backend API description to include FastAPI-specific features (OpenAPI documentation, async support, type validation, dependency injection), improving the Performance section to emphasize FastAPI benefits (async endpoints, background tasks), and restructuring the roadmap to include a dedicated Framework Migration phase while adjusting phase numbering. These changes provide a clear technical direction for the migration effort and establish documentation alignment with the actual implementation progress tracked in the scratchpad.md file.

- [v1.0.6] Development: Created detailed implementation plan for the FastAPI migration with specific tasks and dependencies to guide the development process. Established seven key implementation areas: (1) Database Models for Server, VPN Account, Transaction, Location, and Subscription Plan entities with all necessary relationships and attributes; (2) API Endpoints for authentication, user management, server management, VPN accounts, and payment processing; (3) Alembic Migrations with version control and upgrade/downgrade paths; (4) Telegram Bot integration with command handlers and conversation flows; (5) OpenAPI Documentation with comprehensive endpoint descriptions and examples; (6) Docker Configuration updates for FastAPI and Uvicorn; and (7) Testing Framework with pytest for unit and integration tests. The plan follows a logical dependency order with database models as the foundation, followed by API endpoints, then other components. Each task includes detailed subtasks and acceptance criteria to ensure proper implementation tracking.

- [v1.0.7] Development: Analyzed the existing FastAPI implementation and discovered significant progress already made - the project structure follows best practices with clear separation of concerns (models, schemas, services, API) and many core components are already implemented. Found complete implementations of Server, Location, and VPNAccount models with proper relationships, comprehensive PanelClient service for 3x-UI integration with session cookie management and authentication, and VPNService for account management. The existing code is well-documented with docstrings and follows modern FastAPI patterns including dependency injection, Pydantic validation, and async operations. This progress means the migration is further along than initially expected, allowing us to focus on remaining components like implementing API endpoints, Telegram bot integration, and setting up Alembic migrations rather than starting from scratch.

- [v1.0.8] Development: Implemented the server management API endpoints following RESTful principles and FastAPI best practices. Created comprehensive CRUD operations for server and location management including proper validation and error handling. Key endpoints include: (1) GET /servers with filtering by activity status and location; (2) POST /servers for creating new VPN servers with validation; (3) GET/PUT/DELETE /servers/{id} for retrieving, updating and deleting specific servers; (4) GET /servers/{id}/status for checking server status with optional refresh from 3x-UI panel; (5) POST /servers/{id}/toggle for enabling/disabling servers; and (6) GET/POST /servers/locations for location management. Enhanced the server_schema.py file with proper Pydantic models for request/response validation and added comprehensive docstrings for API documentation. Updated the main API router to include these server endpoints. Each endpoint includes appropriate authorization via dependency injection, ensuring only admin users can modify server configurations while regular users can view server information.

- [v1.0.9] Development: Conducted comprehensive project analysis and created prioritized implementation plan. Identified four main priority areas requiring completion: (1) Database Model Cleanup - Consolidating duplicate model files, standardizing naming, and establishing proper relationships; (2) API Endpoints Implementation - Creating comprehensive RESTful endpoints for authentication, user management, VPN accounts, payments, and analytics; (3) Telegram Bot Integration - Updating handlers for FastAPI, implementing conversation flows, and adding proper error handling; (4) Testing Framework - Setting up pytest configuration, creating test fixtures, and implementing comprehensive test coverage. Current focus is on Database Model Cleanup as it forms the foundation for other components. Key findings include duplicate model files in core/database/models, incomplete API endpoints, and insufficient test coverage. Next steps involve systematically addressing each priority area while maintaining documentation and code quality standards.

### Current Project Analysis [v1.0.9]
- Project Structure:
  * Core components properly organized
  * Duplicate implementations identified
  * Clear separation of concerns established
- Implementation Status:
  * FastAPI migration in progress
  * Core services implemented
  * Server management API completed
- Technical Debt:
  * Duplicate model files
  * Incomplete API endpoints
  * Insufficient test coverage
  * Redundant directory structures

### Implementation Priorities [v1.0.9]
1. Database Model Cleanup:
   - Consolidate duplicate models
   - Standardize naming conventions
   - Update import statements
   - Create proper relationships
   - Add comprehensive docstrings

2. API Endpoints Implementation:
   - Authentication endpoints
   - User management endpoints
   - VPN account endpoints
   - Payment processing endpoints
   - Server management endpoints
   - Notification endpoints
   - Analytics endpoints

3. Telegram Bot Integration:
   - Update handlers for FastAPI
   - Implement conversation flows
   - Add proper error handling
   - Create command handlers
   - Implement inline keyboards
   - Add user state management

4. Testing Framework:
   - Set up pytest configuration
   - Create test fixtures
   - Implement unit tests
   - Add integration tests
   - Create API tests
   - Add bot command tests

- [v1.0.10] Development: Implemented comprehensive enhancement services and API endpoints for system monitoring and management. Created service classes for SystemHealth, SystemBackup, NotificationTemplate, Report, ReportSchedule, SystemLog, SystemConfiguration, and SystemMetric with full CRUD operations and specialized methods. Each service includes features for bulk operations, search functionality, statistics, export capabilities, webhook handling, and audit logging. Implemented corresponding FastAPI endpoints with proper rate limiting, authentication, and error handling. Key features include:
  1. System Health Monitoring:
     - Health check creation and tracking
     - Component-specific health status
     - Critical health monitoring
     - Health statistics and reporting
  2. Backup Management:
     - Automated backup scheduling
     - Backup status tracking
     - Failed backup monitoring
     - Backup statistics and reporting
  3. Notification System:
     - Template management
     - Multi-channel notifications
     - Active template tracking
     - Notification statistics
  4. Reporting System:
     - Report creation and scheduling
     - Pending report tracking
     - Report statistics
     - Export capabilities
  5. System Logging:
     - Component-specific logging
     - Error log tracking
     - Log search and filtering
     - Log statistics and export
  6. Configuration Management:
     - Key-value configuration
     - Encrypted configuration support
     - Configuration search
     - Configuration statistics
  7. System Metrics:
     - Metric collection and tracking
     - Historical metric data
     - Metric statistics
     - Performance monitoring

Next steps will focus on implementing the Telegram bot integration with these enhancement features and setting up automated monitoring and alerting systems.

- [v1.0.11] Development: Created comprehensive plan for Telegram Bot Integration with FastAPI, breaking down implementation into five key areas: Core Bot Setup (command handlers, conversation flows, callback handling), User Management (registration, authentication, settings), VPN Account Management (creation, monitoring, server selection), Payment Integration (flow, verification, subscriptions), and Admin Commands (system management, monitoring, reporting). The plan follows a logical implementation order starting with core bot functionality and progressing through user management, VPN features, payment processing, and admin capabilities. Each component is designed to integrate with existing services and follows FastAPI best practices for async operations and dependency injection.

Next steps will focus on implementing the Telegram bot integration with these enhancement features and setting up automated monitoring and alerting systems.

- [v1.0.12] Development: Implemented initial Telegram bot structure with core components including bot application setup (app/bot/bot.py), configuration management (app/core/config.py), logging utility (app/bot/utils/logger.py), and basic command handlers (app/bot/handlers/commands.py). The implementation includes proper error handling, logging, and async operations following FastAPI best practices. Created directory structure for handlers, keyboards, services, and utilities. Set up configuration with Pydantic settings for bot token, database, Redis, security, and external service credentials. Implemented basic command handlers for /start, /help, /status, /buy, and /settings with placeholder responses and proper error handling.

- [v1.0.13] Development: Implemented conversation handlers and keyboard layouts for the Telegram bot. Created comprehensive conversation flows for user registration and purchase processes, including state management and error handling. Implemented interactive keyboard layouts for plan selection, server location, payment methods, and user settings. Key features include:
  1. Registration Flow:
     - Phone number validation
     - Verification code handling
     - User profile creation
  2. Purchase Flow:
     - Plan selection
     - Server location selection
     - Payment method selection
     - Order confirmation
  3. Interactive Keyboards:
     - VPN plan selection with pricing
     - Server location selection with country flags
     - Payment method selection with icons
     - User settings management
     - Language selection
     - Notification preferences
     - Auto-renewal settings
     - Privacy controls

Next steps will focus on implementing the VPN service integration for account management and payment processing.

## [v1.0.13] VPN Service Integration
- Implemented VPN service for account management and server interactions
- Created methods for:
  - Account creation with plan and location selection
  - Account status monitoring and updates
  - Configuration retrieval and management
  - Traffic reset functionality
  - Server location changes
  - Available locations listing
- Integrated VPN service with conversation handlers
- Added proper error handling and logging
- Implemented database session management
- Added configuration retrieval in purchase flow

## [v1.0.14] Payment Service Integration
- Implemented comprehensive payment service for handling multiple payment methods
- Created methods for:
  - Wallet payments with balance checking
  - Credit card payment processing (placeholder for gateway integration)
  - Bank transfer with account details generation
  - ZarinPal integration with payment URL generation
- Added payment verification system
- Integrated payment service with conversation handlers
- Implemented proper error handling and logging
- Added transaction tracking and order management
- Created user-friendly payment flow with clear instructions

## [v1.0.12] Initial Bot Structure
- Implemented initial Telegram bot structure with core components including bot application setup (app/bot/bot.py), configuration management (app/core/config.py), logging utility (app/bot/utils/logger.py), and basic command handlers (app/bot/handlers/commands.py). The implementation includes proper error handling, logging, and async operations following FastAPI best practices. Created directory structure for handlers, keyboards, services, and utilities. Set up configuration with Pydantic settings for bot token, database, Redis, security, and external service credentials. Implemented basic command handlers for /start, /help, /status, /buy, and /settings with placeholder responses and proper error handling.

## [v1.0.15] Persian Language Support & UX Enhancement
- Implemented comprehensive Persian language support for all bot interactions
- Enhanced user experience with clear Persian instructions for all flows
- Added emoji-enhanced messages for better visual engagement
- Maintained consistent message formatting across all interactions
- Improved error messages in Persian while keeping technical terms in English
- Updated conversation handlers with bilingual support
- Added language-specific keyboard layouts
- Implemented proper RTL text handling
- Enhanced message formatting for better readability
- Added Persian translations for all system messages

## [v1.0.16] User Profile Management Implementation

Implemented comprehensive user profile management features for the MoonVPN Telegram Bot:

1. **Profile Service**:
   - Created `ProfileService` class for handling user profile operations
   - Implemented methods for profile retrieval, updates, and history tracking
   - Added support for subscription history, transaction history, and points tracking
   - Integrated referral system functionality

2. **User Interface**:
   - Created intuitive keyboard layouts for all profile sections
   - Implemented Persian language support with RTL text handling
   - Added emoji-enhanced messages for better visual engagement
   - Organized settings into logical categories (notifications, language, security, etc.)

3. **Features**:
   - Profile information viewing and editing
   - Subscription history with pagination
   - Transaction history tracking
   - Points system integration
   - Referral program management
   - Notification preferences
   - Language selection (Persian/English)
   - Auto-renewal settings
   - Security settings (password, phone, 2FA, devices)

4. **Security**:
   - Implemented secure profile updates
   - Added two-factor authentication support
   - Device management system
   - Phone number verification
   - Password change functionality

5. **User Experience**:
   - Clear navigation structure
   - Consistent message formatting
   - Helpful error messages in Persian
   - Easy-to-use interface with emoji indicators
   - Smooth transitions between sections

Next steps will focus on implementing the Telegram bot integration with these enhancement features and setting up automated monitoring and alerting systems.

## [v1.0.17] Admin Group Management & Monitoring System

Implemented comprehensive admin group management and monitoring system:

1. **Admin Group Structure**:
   - Created separate Telegram groups for different admin functionalities
   - Each group has unique numeric ID for identification
   - Bot is admin in all groups with specific permissions
   - Groups are categorized by functionality:
     * MANAGE (🛡️): Critical system management
     * REPORTS (📊): System statistics and reports
     * LOGS (📄): User activity logs
     * TRANSACTIONS (💰): Payment tracking
     * OUTAGES (⚠️): Service issues
     * SELLERS (👥): Reseller management
     * BACKUPS (💾): Backup notifications

2. **Bot Access Control**:
   - Main bot instance only shows customer-facing buttons
   - Admin commands only available in designated groups
   - Group-specific command handlers based on group ID
   - Secure admin authentication through group membership

3. **Monitoring System**:
   - Utilizing 3x-ui panel API for monitoring data
   - Key metrics tracked:
     * Server status and load
     * User connections and traffic
     * System health and performance
     * Error rates and issues
   - Real-time notifications to appropriate admin groups
   - Automated status updates and alerts

4. **Group-Specific Features**:
   - MANAGE: System configuration, server management
   - REPORTS: Analytics, usage statistics
   - LOGS: User actions, system events
   - TRANSACTIONS: Payment processing, refunds
   - OUTAGES: Service status, maintenance
   - SELLERS: Reseller management, commissions
   - BACKUPS: System backups, data protection

Next steps will focus on implementing the group-specific command handlers and monitoring integration with the 3x-ui panel API. 