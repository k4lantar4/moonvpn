`Project Requirements rules *@docs/project-requirements.md* You will use tools codebase to know what are the details of the files of this *@docs/project-requirements.md* directory files to check the project requirements and the project standards that you need to follow. This will be the guide for you to make sure you are following the project standards. So make sure to read this when planning and implementing the project to avoid duplications, conflicts, and errors. Don't touch that folder and files, you will only read it. Don't over do it to the point that you are not following the project requirements. DON'T REMOVE THIS LINE 1!!!!`

# MoonVPN Project Requirements 🌙🚀

## 1. Project Overview
MoonVPN aims to be a comprehensive, user-friendly, and robust system for managing and selling V2Ray VPN services, initially integrating with the 3x-ui (Sanai) panel. The system features a Telegram bot interface for clients, sellers, and admins, alongside a powerful FastAPI backend API. The core goal is to automate service delivery, simplify management, and provide a seamless experience for all user types, infused with Persian charm and engaging interactions. ✨

## 2. Core Technologies & Architecture
- **Backend API:** FastAPI (Python 3.10+) - Asynchronous, high-performance, with auto-generated OpenAPI docs.
- **Telegram Bot:** python-telegram-bot (v20+) - Asynchronous, webhook-based.
- **Database:** MySQL 8.0+ - Managed via SQLAlchemy ORM & Alembic for migrations.
- **Database GUI:** phpMyAdmin - To be installed alongside MySQL for visual management.
- **Caching:** Redis - For performance optimization, session management, and rate limiting.
- **Deployment:** Docker & Docker Compose - For containerization, easy setup, and scalability.
- **Installation:** Custom Bash Script (`moonvpn` command) - For Ubuntu 22.04/24.04 LTS, handling dependencies and setup.
- **Monitoring:** Prometheus & Grafana - For system metrics and visualization (Future Phase).

### 2.1 Key Implementation Considerations
- **Asynchronous Architecture**: Use async/await throughout to ensure non-blocking operations, especially for external API calls and database queries.
- **Environment Isolation**: Clearly separate development, testing, and production environments with different configuration values and potential feature flags.
- **Error Handling**: Implement comprehensive error handling with appropriate logging and user-friendly error responses in both API and Bot.
- **Security**: No hardcoded credentials anywhere in the codebase. All sensitive information must be loaded from environment variables.
- **Code Organization**: Keep files under 300 lines when possible to maintain readability. Break larger components into smaller, reusable modules.
- **Versioning**: Use semantic versioning for API endpoints to allow for future changes without breaking existing clients.
- **Performance Optimization**: Implement caching where appropriate, especially for frequently accessed data like user details and panel stats.

### 2.2 Architectural Principles
- **Service-Layer Architecture**: Implement business logic in dedicated service classes, separated from API routes and data models.
- **Dependency Injection**: Use FastAPI's dependency injection system for clean, testable code.
- **Repository Pattern**: Create repository classes to abstract database operations from business logic.
- **Clean Architecture**: Separate concerns between presentation, business logic, and data access layers.
- **Event-Driven Design**: Use events and background tasks for asynchronous processing.

**Improved Project Structure:**
```
moonvpn/
├── api/                  # FastAPI application & business logic
│   ├── models/          # SQLAlchemy ORM models
│   │   ├── __init__.py  # Export all models
│   │   ├── users.py     # User & Role models
│   │   ├── panels.py    # Panel & related models
│   │   ├── clients.py   # Client & service models
│   │   ├── locations.py # Location models
│   │   ├── plans.py     # Plan & category models
│   │   ├── finance.py   # Orders, payments & transactions models
│   │   ├── system.py    # System settings & notification channels
│   │   └── migrations.py # Models for historical migrations
│   │
│   ├── routes/          # API route modules (organized by domain)
│   │   ├── __init__.py  # Router registration
│   │   ├── auth.py      # Authentication routes
│   │   ├── users.py     # User management routes
│   │   ├── panels.py    # Panel management routes
│   │   ├── clients.py   # Client management routes
│   │   ├── plans.py     # Plan management routes
│   │   ├── locations.py # Location management routes
│   │   ├── finance.py   # Payment & transaction routes
│   │   ├── admin.py     # Admin-specific operations
│   │   └── system.py    # System settings & utilities
│   │
│   ├── schemas/         # Pydantic schemas for data validation/serialization
│   │   ├── __init__.py  # Export all schemas
│   │   ├── users.py     # User-related schemas
│   │   ├── panels.py    # Panel-related schemas
│   │   ├── clients.py   # Client-related schemas
│   │   ├── plans.py     # Plan-related schemas
│   │   ├── locations.py # Location-related schemas
│   │   ├── finance.py   # Financial schemas
│   │   └── system.py    # System-related schemas
│   │
│   ├── services/        # Core business logic services (organized by domain)
│   │   ├── __init__.py  # Export all services
│   │   ├── base.py      # Base service class with common functionality
│   │   ├── auth.py      # Authentication service
│   │   ├── user.py      # User management service
│   │   ├── panel.py     # Panel operations service
│   │   ├── client.py    # Client management service
│   │   ├── plan.py      # Plan management service
│   │   ├── location.py  # Location management service
│   │   ├── payment.py   # Payment processing service
│   │   ├── wallet.py    # Wallet operations service
│   │   ├── notification.py # Notification service
│   │   ├── security.py  # Security operations
│   │   ├── backup.py    # Backup/restore operations
│   │   └── monitoring.py # Health monitoring service
│   │
│   ├── repositories/    # Data access layer
│   │   ├── __init__.py  # Export all repositories
│   │   ├── base.py      # Base repository with common CRUD operations
│   │   ├── users.py     # User data access
│   │   ├── panels.py    # Panel data access
│   │   ├── clients.py   # Client data access
│   │   ├── plans.py     # Plan data access
│   │   ├── locations.py # Location data access
│   │   ├── finance.py   # Financial data access
│   │   └── system.py    # System settings access
│   │
│   ├── dependencies.py  # FastAPI dependency injection functions
│   └── main.py          # FastAPI app entry point
│
├── bot/                 # Telegram bot application
│   ├── handlers/        # Command/CallbackQuery handlers (organized by domain)
│   │   ├── __init__.py  # Handler registration
│   │   ├── start.py     # Start command & registration
│   │   ├── user.py      # User-specific command handlers
│   │   ├── admin.py     # Admin command handlers
│   │   ├── seller.py    # Seller command handlers
│   │   ├── account.py   # Account management handlers
│   │   ├── service.py   # Service management handlers
│   │   ├── payment.py   # Payment-related handlers
│   │   ├── callback.py  # Callback query handlers
│   │   └── settings.py  # Settings-related handlers
│   │
│   ├── keyboards/       # Keyboard builders
│   │   ├── __init__.py  # Export all keyboards
│   │   ├── main.py      # Main menu keyboards
│   │   ├── admin.py     # Admin-specific keyboards
│   │   ├── user.py      # User-specific keyboards
│   │   ├── seller.py    # Seller-specific keyboards
│   │   ├── service.py   # Service-related keyboards
│   │   └── payment.py   # Payment-related keyboards
│   │
│   ├── commands/        # Command handlers for different user roles
│   │   ├── __init__.py  # Command registration
│   │   ├── common.py    # Commands available to all users
│   │   ├── user.py      # User-specific commands
│   │   ├── admin.py     # Admin-specific commands
│   │   └── seller.py    # Seller-specific commands
│   │
│   ├── conversations/   # Multi-step conversation handlers
│   │   ├── __init__.py  # Export conversations
│   │   ├── registration.py # User registration flow
│   │   ├── purchase.py  # Service purchase flow
│   │   ├── payment.py   # Payment submission flow
│   │   └── settings.py  # Settings update flow
│   │
│   ├── channels/        # Channel notification handlers
│   │   ├── __init__.py  # Export channel handlers
│   │   ├── admin.py     # Admin channel handlers
│   │   ├── payment.py   # Payment verification channel
│   │   ├── alert.py     # Alert channel handlers
│   │   ├── report.py    # Report channel handlers
│   │   └── log.py       # Log channel handlers
│   │
│   ├── middlewares/     # Bot middlewares
│   │   ├── __init__.py  # Export middlewares
│   │   ├── auth.py      # Authentication middleware
│   │   ├── rate_limit.py # Rate limiting
│   │   └── logging.py   # Request logging
│   │
│   ├── services/        # Bot-specific services
│   │   ├── __init__.py  # Export services
│   │   ├── api.py       # API client for communicating with backend
│   │   ├── localization.py # Localization service
│   │   ├── message.py   # Message formatting service
│   │   └── state.py     # Conversation state management
│   │
│   ├── templates/       # Message templates
│   │   ├── __init__.py  # Export templates
│   │   ├── user.py      # User-related message templates
│   │   ├── service.py   # Service-related templates
│   │   ├── payment.py   # Payment-related templates
│   │   └── admin.py     # Admin-related templates
│   │
│   ├── utils/           # Bot utility functions
│   │   ├── __init__.py  # Export utilities
│   │   ├── formatting.py # Message formatting utilities
│   │   ├── validators.py # Input validation utilities
│   │   ├── decorators.py # Handler decorators (auth, etc.)
│   │   └── helpers.py   # Miscellaneous helper functions
│   │
│   └── main.py          # Telegram bot entry point
│
├── core/                # Shared components across API & Bot
│   ├── __init__.py      # Export core components
│   ├── config/          # Configuration management
│   │   ├── __init__.py  # Export config
│   │   ├── settings.py  # Application settings
│   │   ├── environment.py # Environment configuration
│   │   └── constants.py # System constants
│   │
│   ├── database/        # Database connection & utilities
│   │   ├── __init__.py  # Export database components
│   │   ├── session.py   # Database session management
│   │   ├── migrations.py # Migration utilities
│   │   └── utils.py     # Database utilities
│   │
│   ├── security/        # Security-related functionality
│   │   ├── __init__.py  # Export security components
│   │   ├── password.py  # Password hashing
│   │   ├── jwt.py       # JWT handling
│   │   ├── encryption.py # Data encryption/decryption
│   │   └── permissions.py # Role-based permissions
│   │
│   ├── logging/         # Logging configuration
│   │   ├── __init__.py  # Export logging components
│   │   ├── setup.py     # Logging setup
│   │   ├── formatters.py # Log formatters
│   │   └── handlers.py  # Custom log handlers
│   │
│   ├── cache/           # Caching functionality
│   │   ├── __init__.py  # Export cache components
│   │   ├── redis.py     # Redis client & utilities
│   │   ├── decorators.py # Cache decorators
│   │   └── keys.py      # Cache key management
│   │
│   ├── exceptions/      # Custom exceptions
│   │   ├── __init__.py  # Export exceptions
│   │   ├── api.py       # API-related exceptions
│   │   ├── auth.py      # Authentication exceptions
│   │   ├── business.py  # Business logic exceptions
│   │   └── integration.py # External integration exceptions
│   │
│   ├── utils/           # Shared utility functions
│   │   ├── __init__.py  # Export utilities
│   │   ├── dates.py     # Date/time utilities
│   │   ├── strings.py   # String manipulation utilities
│   │   ├── validation.py # Data validation utilities
│   │   └── files.py     # File handling utilities
│   │
│   └── metrics.py       # Prometheus collectors (Future Phase)
│
├── integrations/        # External service integrations
│   ├── __init__.py      # Export integrations
│   ├── panels/          # 3x-ui panel API client & logic
│   │   ├── __init__.py  # Export panel clients
│   │   ├── client.py    # Base XuiPanelClient class
│   │   ├── types.py     # Panel data type definitions
│   │   ├── inbounds.py  # Inbound management
│   │   ├── clients.py   # Client management
│   │   ├── traffic.py   # Traffic operations
│   │   ├── system.py    # System operations
│   │   └── models.py    # Panel data models
│   │
│   ├── payments/        # Payment gateway integrations
│   │   ├── __init__.py  # Export payment clients
│   │   ├── zarinpal.py  # ZarinPal API client
│   │   ├── models.py    # Payment models
│   │   └── webhooks.py  # Payment webhook handlers
│   │
│   └── sms/             # SMS service integrations
│       ├── __init__.py  # Export SMS clients
│       ├── client.py    # Base SMS client
│       └── melipayamak.py # Melipayamak integration (example)
│
├── migrations/          # Alembic database migrations
│   ├── versions/        # Individual migration script versions
│   ├── env.py           # Alembic environment configuration
│   └── script.py.mako   # Migration script template
│
├── scripts/             # Utility & operational scripts
│   ├── install.sh       # Main installation script
│   ├── backup.sh        # Database/config backup script
│   ├── setup_db.py      # Initial DB setup/checks
│   ├── healthcheck.py   # System health check script
│   ├── moonvpn.sh       # MoonVPN CLI tool implementation
│   ├── maintenance/     # Maintenance scripts
│   │   ├── cleanup.py   # Database cleanup utilities
│   │   ├── migrate.py   # Panel migration helper
│   │   └── repair.py    # System repair utilities
│   │
│   ├── monitoring/      # Monitoring scripts
│   │   ├── check_panels.py # Panel health monitoring
│   │   ├── check_clients.py # Client status monitoring
│   │   └── stats.py     # System statistics generator
│   │
│   └── utils/           # Script utilities
│       ├── colors.sh    # Terminal color definitions
│       ├── functions.sh # Common bash functions
│       └── validators.sh # Input validation utilities
│
├── tests/               # Automated tests
│   ├── __init__.py      # Test package
│   ├── conftest.py      # pytest configuration
│   ├── api/             # API tests
│   │   ├── __init__.py  # Test package
│   │   ├── test_routes/ # API route tests
│   │   ├── test_services/ # Service tests
│   │   └── test_models/ # Model tests
│   │
│   ├── bot/             # Bot tests
│   │   ├── __init__.py  # Test package
│   │   ├── test_handlers/ # Handler tests
│   │   ├── test_keyboards/ # Keyboard tests
│   │   └── test_conversations/ # Conversation tests
│   │
│   ├── core/            # Core component tests
│   │   ├── __init__.py  # Test package
│   │   ├── test_config/ # Configuration tests
│   │   ├── test_database/ # Database tests
│   │   └── test_security/ # Security tests
│   │
│   ├── integrations/    # Integration tests
│   │   ├── __init__.py  # Test package
│   │   ├── test_panels/ # Panel client tests
│   │   └── test_payments/ # Payment integration tests
│   │
│   └── fixtures/        # Test fixtures
│       ├── __init__.py  # Test package
│       ├── users.py     # User fixtures
│       ├── panels.py    # Panel fixtures
│       ├── clients.py   # Client fixtures
│       └── database.py  # Database fixtures
│
├── locales/             # Localization files
│   ├── fa/              # Persian translations
│   │   └── LC_MESSAGES/ # Message files
│   └── en/              # English translations (if needed)
│       └── LC_MESSAGES/ # Message files
│
├── docs/                # Documentation
│   ├── api/             # API documentation
│   ├── setup/           # Setup guides
│   ├── admin/           # Admin guides
│   ├── user/            # User guides
│   ├── architecture/    # Architecture documentation
│   └── development/     # Development guides
│
├── .env.example         # Example environment variables template
├── alembic.ini          # Alembic configuration file
├── docker-compose.yml   # Docker Compose service definitions
├── Dockerfile.api       # Dockerfile for API service
├── Dockerfile.bot       # Dockerfile for Bot service
└── README.md            # Project overview and setup instructions
```

## 3. Key Features

### 3.1. Panel Management (3x-ui Focus)
- **Multi-Panel Support:** Connect and manage multiple 3x-ui instances.
- **Health Checks:** Automated, periodic checks for panel status, connectivity, and basic stats (e.g., CPU, RAM). Report failures to Alert Channel. 🩺
- **Location Tagging:** Associate panels with geographic locations (e.g., 🇩🇪 Germany, 🇫🇷 France) for user selection. Flags required! 🚩
- **Inbound Management:** Create, view, update, and delete inbounds programmatically via the API.
- **Resilient Client:** Robust 3x-ui API client with error handling, retries, and connection pooling.
- **(Enhanced) Automated Failover:** Basic mechanism to re-assign clients to a healthy panel in the same location if their current panel fails (manual trigger initially, potential automation later).

**Technical Implementation Details:**
- Create a dedicated API client (`XuiPanelClient`) in `integrations/panels/client.py` that handles authentication, connection pooling, and request formatting. This client will focus solely on HTTP communication with the panel API.
- Implement a separate `PanelService` class in `api/services/panel_service.py` that acts as an abstraction layer between the application and the panel API client. The service will manage business logic, handle multiple panels, and provide high-level operations.
- Use dependency injection in FastAPI to provide the service to route handlers.
- Implement retry logic with exponential backoff for transient failures.
- Store encrypted panel credentials in the database with a secure encryption key stored in environment variables.
- Create a scheduler for periodic health checks (recommended interval: 5-15 minutes).
- Design panel selection algorithm that considers current load, geographic proximity, and health status.

### 3.2. Telegram Bot Interface
- **Multi-Interaction Methods:**
    - **Commands:** Standard `/command` interface (e.g., `/start`, `/plans`).
    - **Inline Keyboards:** Interactive buttons within messages for navigation and actions (e.g., selecting plans, confirming actions). ✨
    - **Reply Keyboards:** Custom keyboard layouts for common actions (e.g., main menu options). ⌨️
- **User Roles:** Distinct interfaces and capabilities for Regular Users, Sellers, and Admins.
- **Persian Language & Tone:** All user-facing text MUST be in friendly, professional Persian. Use engaging language, marketing flair, and relevant, tasteful emojis. Examples: "سرویس شما با موفقیت تمدید شد! 🎉", "برای دیدن پلن‌های شگفت‌انگیز ما، دکمه زیر رو بزن! 👇".
- **State Management:** Use conversation handlers for multi-step processes (e.g., purchasing, submitting payment proof).
- **User Experience:** Focus on intuitive navigation, clear instructions, and helpful feedback messages.

**Technical Implementation Details:**
- Create separate modules for each user role in `bot/handlers/` (user.py, admin.py, seller.py).
- Implement a messages.py module with all Persian language text constants to centralize localization.
- Create a conversation_handlers.py module for complex multi-step processes using ConversationHandler from python-telegram-bot.
- Define clear keyboard layouts in keyboards.py with named constants for each menu/action type.
- Use python-telegram-bot v20+ with Application builder pattern for modern, async implementation.
- Implement proper timeout handling for user interactions to prevent stale conversations.
- Follow Service Layer architecture pattern by creating bot-specific service classes that interact with core business services rather than directly accessing models or external APIs.

### 3.3. Channel-Based Notification System
- **Single Bot, Multiple Channels:** One bot manages notifications across specialized channels.
- **Dynamic Configuration:** Admins can configure channel IDs via the bot settings.
- **Interactive Admin Actions:** Use inline buttons in channels for tasks like payment approval. 👍👎
- **Channel Types:**
    - **Admin Channel:** General alerts, high-priority actions (needs config). 👑
    - **Payment Verification Channel:** Card-to-card receipt submissions for admin approval/rejection. 💳
    - **Report Channel:** Scheduled performance/sales reports. 📊
    - **Log Channel:** Detailed system activity/error logs (configurable level). 📜
    - **Alert Channel:** Critical system issues (panel down, errors). ⚠️
    - **Backup Channel:** Receives database/config backup files. 💾
- **(Enhanced) Notification Formatting:** Use Markdown for clear, readable messages in channels.

**Technical Implementation Details:**
- Create a NotificationManager class in `bot/channels.py` to centralize all channel notifications.
- Implement a `NotificationService` in `api/services/notification_service.py` to provide a service layer for notification-related business logic.
- Design template system for different notification types with standardized formats.
- Implement a callback query handler for interactive buttons in channels.
- Store channel IDs in database with default values in environment variables.
- Create helper methods for different message formats (alerts, reports, logs, receipts).
- Use Python's logging module integration to send log messages to the appropriate channel based on severity.
- Implement a queue-based system for notification delivery to handle high-volume situations and prevent rate limiting.

### 3.4. Client Account Management (V2Ray Focus)
- **Protocols:** Support VMESS & VLESS initially.
- **Automated Provisioning:** Create/disable/enable/delete client accounts on the selected 3x-ui panel via API integration.
- **Status & Usage Monitoring:** Regularly fetch client status, data usage, and expiration dates from panels.
- **User Self-Service (via Bot):**
    - View account details & connection info (QR code 🖼️, subscription link 🔗).
    - Check data usage & remaining days. ⏳
    - Renew service. 🔄
    - Change server location (if multiple panels in different locations exist). 🌍
    - Change protocol (VMESS/VLESS). ↔️
    - Add personal notes to their account. 📝
    - Toggle auto-renewal preference. 自动续费
    - Freeze/unfreeze account (pausing subscription time). ❄️
- **(Enhanced) Intelligent Panel Selection:** Automatically suggest or select the least loaded panel within the chosen location for new clients.

**Technical Implementation Details:**
- Create `ClientService` in `api/services/client_service.py` with methods for creating, updating, and monitoring clients.
- Implement `UserService` in `api/services/user_service.py` to manage user-related operations.
- Separate business logic from data access by implementing Repository classes for database operations.
- Implement scheduled jobs to update client usage statistics (recommended: hourly updates).
- Create a `QrCodeService` for generating QR codes using a library like segno or qrcode.
- Store client configuration data in the database, not just relying on the panel.
- Calculate expiration dates accurately, accounting for frozen time periods.
- Create protocol-specific configuration generation for VMESS and VLESS.
- Define load balancing algorithm for new client allocation across panels.
- Implement the service layer in a way that allows for easy testing and mocking in unit tests.

### 3.5. Payment System
- **Manual Card-to-Card:**
    - User submits recipient card details (chosen from a rotating pool) and uploads receipt image via bot. 🧾
    - Bot forwards details & image to Payment Verification Channel with "Approve ✅" / "Reject ❌" buttons for authorized admins.
    - Admin approval triggers automatic wallet credit for the user. 💰
    - Configurable rotating bank card details (managed by admins).
    - All receipts archived (potentially in a separate channel or stored linked to the transaction).
- **ZarinPal Integration:**
    - Standard web gateway flow initiated from the bot. 🛒
    - Secure callback handling to verify payment status.
    - Automatic wallet crediting upon successful payment verification.
- **Internal Wallet System:**
    - Track user balances (Toman/IRT).
    - Record all transactions (deposit, purchase, withdrawal, commission, refund).
    - Users can view balance and transaction history via bot. 🏦
- **(Enhanced) AI Receipt Pre-Verification (Future Idea):** Explore OCR/AI tools to perform basic checks on receipts before admin review (e.g., matching amount, checking for duplicates).

**Technical Implementation Details:**
- Create a `WalletService` in `api/services/wallet_service.py` to handle all wallet operations.
- Implement a `PaymentService` in `api/services/payment_service.py` to manage payment processes including verification.
- Develop a `TransactionService` to record and manage all financial transactions with proper types and references.
- Design a secure `BankCardService` for rotating card selection with configurable rules.
- Store receipt images securely in a dedicated storage system with proper access controls.
- Create ZarinPal integration via a dedicated client class in `integrations/payments/zarinpal.py`.
- Implement proper locking mechanisms using Redis for financial operations to prevent race conditions.
- Create a thorough audit log for all financial transactions.
- Implement the Observer pattern to handle payment events and trigger appropriate actions when payments are completed or rejected.
- Build a transaction reconciliation system to verify the integrity of financial records.

### 3.6. Seller/Reseller System (Simplified)
- **Discount Model:** Sellers get a percentage discount on plan purchases made *for* their clients.
- **Commission Tracking:** Track sales made by sellers and calculate potential commissions (details TBD, focus on discount first).
- **Seller Dashboard (Bot):** Basic view of their client list and sales count/volume. 📈
- **Client Assignment:** Mechanism to link a client to a specific seller (e.g., during purchase or via referral).
- **(Enhanced) Referral Links:** Generate unique referral links for sellers to share. New users signing up via link are automatically associated with the seller. 🤝

**Technical Implementation Details:**
- Create a `SellerService` in `api/services/seller_service.py` to manage seller-specific operations.
- Implement a `ReferralService` to handle referral code generation and verification.
- Develop discount calculation logic in the order processing pipeline.
- Store seller-client relationships in the database with proper indexing for efficient queries.
- Create reporting queries and analytics for seller performance metrics.
- Design intuitive seller dashboard with key performance indicators.
- Generate unique deeplinks for Telegram referrals.
- Implement a commission calculation and payment system.
- Create an event-based system for tracking sales and commissions.
- Build a notifications system for sellers about their sales and commissions.

### 3.7. Free Trial System
- **Eligibility:** Verify Iranian phone numbers (+98) via SMS (requires integration later) or manual admin approval initially. 🇮🇷
- **One-Time Use:** Limit trials to one per verified user/phone number.
- **Automated Provisioning:** Create temporary client account on a designated panel/inbound with limited duration (e.g., 1-6 hours) and traffic (e.g., 100-500MB). 🎁
- **Automatic Expiry/Cleanup:** System automatically disables/deletes trial accounts after expiry.
- **Anti-Abuse:** Implement checks to prevent misuse (e.g., IP tracking, device fingerprinting - advanced).

**Technical Implementation Details:**
- Create a `TrialService` in `api/services/trial_service.py` to manage free trial allocations and checks.
- Implement phone number validation with Iranian phone number format checking.
- Create scheduled job to clean up expired trial accounts.
- Set up designated trial inbounds on panels with appropriate configurations.
- Implement anti-abuse measures based on IP addresses and device information.
- Create a verification system for phone numbers.
- Build a tracking system for trial usage and conversion rates.
- Implement a trial account cleanup job that runs at regular intervals.
- Set up trial-specific notification templates and flows.
- Design analytics for measuring trial effectiveness and conversion rates.

### 3.8. Administrative Tools (via Bot)
- **User Management:** Search, view details, ban/unban, manually adjust wallet balance, assign roles. 👥
- **Plan Management:** Create, edit, activate/deactivate service plans (name, traffic, duration, price). 🏷️
- **Panel Management:** Add, edit, remove 3x-ui panels; view status and stats. 🖥️
- **Server Location Management:** Define and manage locations (name, flag). 📍
- **Payment Management:** View payment history, manually verify/reject card-to-card payments (primarily done via channel).
- **Bank Card Management:** Add/edit/activate/deactivate bank cards used for card-to-card payments.
- **Broadcast Messaging:** Send messages to all users or specific roles (Users, Sellers). 📣
- **Channel Configuration:** Set Telegram Channel IDs for notifications. ⚙️
- **System Statistics:** View basic stats (user count, active clients, total sales).

**Technical Implementation Details:**
- Create comprehensive admin handlers in `bot/handlers/admin.py`.
- Develop an `AdminService` in `api/services/admin_service.py` for admin-specific operations.
- Implement a `BroadcastService` to handle message broadcasting to users.
- Create a `StatisticsService` for generating system statistics and reports.
- Implement paginated displays for large data sets (users, clients, transactions).
- Create proper role-based access control with a `PermissionService` for admin commands.
- Design intuitive keyboard navigation for admin functions.
- Implement command timeouts and confirmations for destructive operations.
- Create admin audit logging for all administrative actions.
- Build a dashboard for monitoring system health and performance.
- Implement report generation for sales, traffic, and user activity.

### 3.9. Backup and Security
- **Automated Backups:** Regular (e.g., daily) backups of the MySQL database.
- **Backup Delivery:** Send backup files (.sql.gz) to the dedicated Backup Telegram Channel. 🛡️
- **Secure Password Storage:** Hash passwords using robust algorithms (e.g., Argon2, bcrypt).
- **API Security:** Implement JWT for API authentication, HTTPS enforcement.
- **Rate Limiting:** Apply rate limits to bot commands and API endpoints via Redis. 🚦
- **Access Control:** Role-based access control enforced in both API and Bot handlers.
- **Sensitive Data Encryption:** Encrypt sensitive panel credentials in the database. 🔒
- **Activity Logging:** Log important admin actions and system events to Log Channel.

**Technical Implementation Details:**
- Create a `BackupService` in `api/services/backup_service.py` to manage database backups.
- Implement a `SecurityService` in `api/services/security_service.py` for managing security functions.
- Use mysqldump with proper compression for database backups.
- Implement JWT with proper expiration and refresh mechanisms in `core/security.py`.
- Create rate limiting middleware using Redis for both API and Bot in `api/middlewares/rate_limit.py`.
- Use a secure encryption library (cryptography) for sensitive data in `core/security.py`.
- Implement proper sanitization for all user inputs.
- Create comprehensive logging with appropriate levels in `core/logging.py`.
- Design backup rotation and cleanup strategy.
- Implement a `RoleService` to manage access control based on user roles.
- Create an audit log system for all sensitive operations.
- Implement IP-based blocking for suspicious activities.
- Add thorough input validation and sanitization to prevent injection attacks.
- Create a security incident response system with automated alerts.

### 3.10. API & Developer Features
- **OpenAPI Documentation:** Auto-generated interactive API docs (Swagger UI/ReDoc) via FastAPI. 📚
- **API Key Management:** Generate and manage API keys for potential future external integrations (low priority). 🔑
- **Webhooks:** Consider webhooks for real-time event notifications (e.g., payment success) for potential future integrations (low priority).
- **Health Checks:** Implement comprehensive health checks for all services.
- **Metrics:** Collect and expose application metrics for monitoring.

**Technical Implementation Details:**
- Configure FastAPI to generate comprehensive OpenAPI documentation.
- Create an `ApiKeyService` in `api/services/apikey_service.py` for API key management.
- Implement a `WebhookService` for webhook delivery and management.
- Add detailed descriptions to all API endpoints, parameters, and responses.
- Create security schemes in FastAPI for authentication.
- Design webhook delivery system with retry logic.
- Implement API key generation and verification.
- Add health check endpoints for all services.
- Create a metrics collection system using Prometheus.
- Develop a monitoring dashboard using Grafana.
- Implement proper error handling and logging for all API endpoints.
- Create a developer portal for API documentation and key management (Future Phase).

## 4. Non-Functional Requirements

### 4.1. Performance
- **Response Time:** API responses should be fast (<500ms for typical requests). Bot interactions should feel responsive.
- **Concurrency:** System should handle multiple simultaneous users efficiently.
- **Caching:** Implement caching for frequently accessed data to reduce database load.
- **Database Optimization:** Use proper indexing and query optimization.
- **Background Processing:** Use asynchronous processing for long-running tasks.

### 4.2. Scalability
- **Horizontal Scaling:** Architecture should allow for adding more panels and handling a growing user base.
- **Containerization:** Docker setup aids in scaling components independently.
- **Statelessness:** Design services to be stateless for easier scaling.
- **Load Balancing:** Implement load balancing for distributing traffic across instances.
- **Database Scaling:** Design with potential sharding and replication in mind.

### 4.3. Reliability
- **System Resilience:** System should be resilient to panel failures. Health checks and potential failover mechanisms are key.
- **Error Recovery:** Implement proper error handling and recovery mechanisms.
- **Logging:** Comprehensive logging for debugging and monitoring.
- **Monitoring:** Implement monitoring for early detection of issues.
- **Circuit Breakers:** Implement circuit breakers for external service calls.

### 4.4. Maintainability
- **Code Quality:** Code should be clean, well-commented (English), follow Python best practices (PEP 8), and be modular.
- **Documentation:** Comprehensive documentation for code, APIs, and system architecture.
- **Testing:** Extensive test coverage to ensure code quality and prevent regressions.
- **CI/CD:** Future implementation of continuous integration and deployment pipelines.
- **Dependency Management:** Clear management of external dependencies.

### 4.5. Usability
- **Telegram Bot Interface:** Must be intuitive and easy to use for non-technical users.
- **Persian Localization:** All user-facing content must be in Persian.
- **Responsive Design:** Bot interface should be usable on mobile devices.
- **Error Messages:** Clear, friendly error messages in Persian.
- **Help System:** Comprehensive help system for users.

### 4.6. Service-Oriented Architecture
- **Service Layer:** Implement business logic in dedicated service classes that are reusable across the application.
- **Separation of Concerns:** Clearly separate data access, business logic, and presentation layers.
- **Dependency Injection:** Use FastAPI's dependency injection system to provide services to routes.
- **Repository Pattern:** Abstract database operations behind repository interfaces.
- **Consistent Service API:** Design services with consistent, well-documented interfaces.

### 4.7. Layered Architecture
- **Presentation Layer:** API routes and bot handlers that handle user interactions.
- **Service Layer:** Business logic encapsulated in service classes.
- **Data Access Layer:** Repository classes for database operations.
- **Domain Layer:** Core business models and logic.
- **Integration Layer:** Adapters for external systems (panels, payment gateways).

**Technical Implementation Details:**
- Add response time monitoring to API endpoints.
- Use database indexing strategically for performance.
- Implement caching for frequently accessed data using Redis.
- Create health check endpoints for all services.
- Design with horizontal scaling in mind.
- Implement comprehensive error handling throughout the application.
- Create clear user flow diagrams for complex operations.
- Use dependency injection to provide services to API routes.
- Implement the repository pattern for database operations.
- Create service classes for all major business functions.
- Design clear interfaces between layers.
- Implement unit tests for each layer.

## 5. Project Phases

*Focus is on delivering a Minimum Viable Product (MVP) first, iterating based on feedback.*

### Phase 0: Core Infrastructure & Setup (Current Focus - ~2 weeks)
- **Goal:** Get the basic structure running locally with Docker.
- **Tasks:**
    - [ID-001] Setup project directory structure.
    - [ID-006] Setup Docker (`Dockerfile`, `docker-compose.yml` with API, Bot, MySQL, Redis, phpMyAdmin).
    - [ID-005] Create `.env.example`.
    - [ID-004] Define core DB Models (Users, Roles, Panels, Locations, Plans, Clients, WalletTransactions) & Setup Alembic. Create initial migration.
    - [ID-009] Implement `core/database.py` & `core/config.py`.
    - [ID-002] Initialize FastAPI (`api/main.py`, health check `/ping`).
    - [ID-003] Initialize Telegram Bot (`bot/main.py`, `/start` handler responding with basic welcome message & keyboard).
    - [ID-007] Basic 3x-ui connection test function (`integrations/panels/client.py`).
    - [ID-012] Setup basic logging (`core/logging.py`).
    - [ID-008] Basic `moonvpn` command concept (e.g., script to run docker-compose up/down).
    - [ID-010] Setup Persian language support infrastructure.
    - [ID-011] Setup basic notification channel system (bot/channels.py).
    - [ID-013] Create initial test framework setup.
- **Deliverable:** Runnable Docker environment, basic API/Bot responding, DB schema initialized.

### Phase 0.5: Service Layer Implementation (~2 weeks)
- **Goal:** Implement service layer architecture and core business logic services
- **Tasks:**
    - [ID-014] Correct the structure of panel client implementation
    - [ID-015] Create panel service layer
    - [ID-016] Implement security and encryption
    - [ID-017] Complete the channel notification system
    - [ID-018] Implement the test framework
    - Implement core service classes for all major features:
      - PanelService
      - UserService
      - ClientService
      - WalletService
      - NotificationService
      - SecurityService
- **Deliverable:** Complete service layer architecture, corrected panel client implementation, enhanced security, and comprehensive testing framework.

### Phase 1: User & Panel Foundations (~3 weeks)
- **Goal:** User registration, basic admin panel management.
- **Tasks:**
    - Implement User registration via `/start`.
    - Implement Role system (Admin, User, Seller).
    - Basic JWT Auth for API.
    - Admin commands to add/list/view panels and locations.
    - Panel health check implementation.
    - Bot commands for users to view profile (`/profile`).
    - Setup notification channels & basic channel sender (`bot/channels.py`). Send welcome message to Admin channel on new user registration.
- **Deliverable:** Users can register, Admins can manage panels, basic health checks run.

### Phase 2: Plans, Purchase Flow & Client Provisioning (~3 weeks)
- **Goal:** Define plans, allow users to buy, create clients on panels.
- **Tasks:**
    - Admin commands to manage Plans.
    - User command `/plans` to view active plans.
    - Implement `/buy` conversation flow (select plan, select location).
    - Implement Wallet system backend (deposit via manual approval flow).
    - Implement card-to-card payment submission & verification channel logic.
    - Implement Client provisioning logic (create client on selected panel after purchase).
    - User command `/myaccount` to view basic client details (status, expiry).
- **Deliverable:** Users can view plans, deposit funds via card-to-card, buy a plan, and get a V2Ray account created.

### Phase 3 & Beyond: Advanced Features
- ZarinPal Integration
- Full Seller System
- Free Trial System
- Advanced Client Management (Freeze, Change Location/Protocol, Renew)
- Auto-Renewal
- Full Reporting & Statistics
- Monitoring Integration
- Security Hardening & Optimization

*(Detailed planning for these phases will occur later)*

## 6. Testing Strategy

### 6.1. Unit Testing
- **Focus:** Test individual components in isolation
- **Tools:** pytest for running tests, pytest-asyncio for testing async code
- **Coverage:** Aim for 80%+ code coverage for critical components
- **Target Areas:**
  - Service layer classes
  - Utility functions
  - Data models
  - Schema validation
  - Security functions
- **Implementation:**
  - Use dependency injection for easier mocking
  - Create fixtures for common test scenarios
  - Implement parameterized tests for multiple test cases
  - Use proper assertion messages for clear test failures

### 6.2. Integration Testing
- **Focus:** Test interactions between components
- **Tools:** pytest with test database
- **Target Areas:**
  - API endpoint behavior
  - Database operations
  - External service integrations (3x-ui panel, payment gateways)
  - Event processing flows
- **Implementation:**
  - Create test database with isolated schema
  - Implement database fixtures with test data
  - Use test clients for API and bot testing
  - Mock external services when appropriate

### 6.3. End-to-End Testing
- **Focus:** Test complete user flows
- **Type:** Primarily manual testing initially
- **Target Areas:**
  - User registration and login
  - Plan purchasing
  - Payment verification
  - Account management
  - Admin operations
- **Implementation:**
  - Create detailed test plans for each flow
  - Document test results
  - Consider automated E2E testing for critical paths

### 6.4. Security Testing
- **Focus:** Verify security measures
- **Target Areas:**
  - Authentication and authorization
  - Input validation
  - Rate limiting
  - Encryption
  - Session management
- **Implementation:**
  - Implement tests for security bypasses
  - Check for proper error responses
  - Verify access controls

**Technical Implementation Details:**
- Use pytest for all automated testing.
- Create separate test directories for unit, integration, and API tests.
- Implement factory classes for test data generation.
- Create database fixtures for testing with isolated schemas.
- Implement mock objects for external dependencies.
- Define clear test naming conventions.
- Set up CI pipeline for automated test runs (Future Phase).
- Create test coverage reporting.
- Document test cases and procedures.

## 7. Documentation Standards

### 7.1. Code Documentation
- **Inline Comments:** Use English for code comments, explaining non-obvious logic.
- **Docstrings:** Follow Google Python Style Guide for docstrings.
- **Type Hints:** Use type hints for all function parameters and return values.
- **Module Headers:** Include brief description and author information at the top of each module.
- **Class and Function Documentation:** Document purpose, parameters, return values, and exceptions.

### 7.2. API Documentation
- **OpenAPI:** Leverage FastAPI's automatic OpenAPI docs.
- **Endpoint Descriptions:** Add detailed descriptions to routes and schemas.
- **Example Requests/Responses:** Include examples for all endpoints.
- **Authentication Details:** Document authentication requirements.
- **Error Responses:** Document possible error responses and their meanings.

### 7.3. System Documentation
- **Architecture Overview:** Maintain documentation of system architecture.
- **Component Interactions:** Document how components interact with each other.
- **Database Schema:** Document database schema with relationships.
- **Integration Points:** Document external system integrations.
- **Configuration Options:** Document all configuration options and their meanings.

### 7.4. User Documentation
- **Admin Guide:** Document admin features and operations.
- **User Guide:** Create tutorials for common user actions.
- **Bot Command Reference:** Document all bot commands and their functions.
- **FAQ:** Maintain a frequently asked questions document.
- **Troubleshooting Guide:** Create troubleshooting procedures for common issues.

### 7.5. Project Documentation
- **README.md:** Keep updated with setup instructions and project overview.
- **CHANGELOG.md:** Maintain a simple changelog for significant changes.
- **Requirements:** This file (`@.cursor/project-requirements.md`) serves as the primary requirements document.
- **Memories/Lessons:** Use `@.cursor/memories.md` and `@.cursor/lessons-learned.md` as per the rules.
- **Contributor Guidelines:** Document coding standards and contribution process.

**Technical Implementation Details:**
- Follow Google Python Style Guide for docstrings.
- Add type hints to all function parameters and return values.
- Document all public API endpoints with examples.
- Create architectural diagrams for complex interactions.
- Document environment variables and their purposes.
- Create user guides for common bot interactions.
- Document database schema with relationships.
- Maintain up-to-date documentation as the system evolves.
- Use markdown for all documentation for consistency.
- Keep documentation in version control alongside code.

## 8. Database Schema (Key Tables)

### 8.1. Core Tables

1. **users**
   - `id`: INT PRIMARY KEY AUTO_INCREMENT
   - `telegram_id`: BIGINT UNIQUE
   - `username`: VARCHAR(255) NULL
   - `full_name`: VARCHAR(255) NULL
   - `phone`: VARCHAR(20) NULL
   - `email`: VARCHAR(255) NULL
   - `role_id`: INT FOREIGN KEY
   - `balance`: DECIMAL(10,2) DEFAULT 0.00
   - `is_banned`: BOOLEAN DEFAULT FALSE
   - `is_active`: BOOLEAN DEFAULT TRUE
   - `referral_code`: VARCHAR(20) UNIQUE NULL
   - `referred_by_id`: INT FOREIGN KEY NULL
   - `lang`: VARCHAR(10) DEFAULT 'fa'
   - `last_login`: DATETIME NULL
   - `login_ip`: VARCHAR(45) NULL
   - `created_at`: DATETIME
   - `updated_at`: DATETIME

2. **roles**
   - `id`: INT PRIMARY KEY AUTO_INCREMENT
   - `name`: ENUM('admin', 'seller', 'user')
   - `description`: TEXT NULL
   - `discount_percent`: INT DEFAULT 0
   - `commission_percent`: INT DEFAULT 0
   - `can_manage_panels`: BOOLEAN DEFAULT FALSE
   - `can_manage_users`: BOOLEAN DEFAULT FALSE
   - `can_manage_plans`: BOOLEAN DEFAULT FALSE
   - `can_approve_payments`: BOOLEAN DEFAULT FALSE
   - `can_broadcast`: BOOLEAN DEFAULT FALSE
   - `is_admin`: BOOLEAN DEFAULT FALSE
   - `is_seller`: BOOLEAN DEFAULT FALSE
   - `created_at`: DATETIME
   - `updated_at`: DATETIME

3. **panels**
   - `id`: INT PRIMARY KEY AUTO_INCREMENT
   - `name`: VARCHAR(100)
   - `url`: VARCHAR(255) UNIQUE
   - `login_path`: VARCHAR(50) DEFAULT '/login'
   - `username`: VARCHAR(100)
   - `password`: VARCHAR(255) ENCRYPTED
   - `location_id`: INT FOREIGN KEY
   - `panel_type`: VARCHAR(50) DEFAULT '3x-ui'
   - `is_active`: BOOLEAN DEFAULT TRUE
   - `is_healthy`: BOOLEAN DEFAULT FALSE
   - `last_check`: DATETIME NULL
   - `status_message`: VARCHAR(255) NULL
   - `priority`: INT DEFAULT 0
   - `created_by`: INT FOREIGN KEY NULL
   - `created_at`: DATETIME
   - `updated_at`: DATETIME

4. **locations**
   - `id`: INT PRIMARY KEY AUTO_INCREMENT
   - `name`: VARCHAR(100) UNIQUE
   - `flag`: VARCHAR(10) NULL
   - `country_code`: VARCHAR(2) NULL
   - `is_active`: BOOLEAN DEFAULT TRUE
   - `description`: TEXT NULL
   - `default_inbound_id`: INT NULL
   - `protocols_supported`: VARCHAR(100) NULL  # comma-separated list of supported protocols
   - `inbound_tag_pattern`: VARCHAR(100) NULL  # pattern for generating inbound tags
   - `default_remark_prefix`: VARCHAR(50) NULL  # prefix for client remarks
   - `created_at`: DATETIME
   - `updated_at`: DATETIME

### 8.2. Service-Related Tables

5. **plans**
   - `id`: INT PRIMARY KEY AUTO_INCREMENT
   - `name`: VARCHAR(100)
   - `traffic`: BIGINT  # in GB
   - `days`: INT
   - `price`: DECIMAL(10,2)
   - `description`: TEXT NULL
   - `features`: TEXT NULL  # JSON array of additional features
   - `is_active`: BOOLEAN DEFAULT TRUE
   - `is_featured`: BOOLEAN DEFAULT FALSE
   - `max_clients`: INT NULL
   - `protocols`: VARCHAR(255) NULL  # comma-separated protocols (vmess, vless)
   - `category_id`: INT NULL FOREIGN KEY  # reference to plan_categories
   - `sorting_order`: INT DEFAULT 0
   - `created_at`: DATETIME
   - `updated_at`: DATETIME

6. **plan_categories**
   - `id`: INT PRIMARY KEY AUTO_INCREMENT
   - `name`: VARCHAR(100)
   - `description`: TEXT NULL
   - `sorting_order`: INT DEFAULT 0
   - `is_active`: BOOLEAN DEFAULT TRUE
   - `created_at`: DATETIME
   - `updated_at`: DATETIME

7. **clients**
   - `id`: INT PRIMARY KEY AUTO_INCREMENT
   - `user_id`: INT FOREIGN KEY
   - `panel_id`: INT FOREIGN KEY
   - `location_id`: INT FOREIGN KEY
   - `plan_id`: INT FOREIGN KEY
   - `order_id`: INT FOREIGN KEY NULL
   - `client_uuid`: VARCHAR(36)
   - `email`: VARCHAR(255)
   - `remark`: VARCHAR(255)  # Display name identifier
   - `expire_date`: DATETIME
   - `traffic`: BIGINT  # in GB
   - `used_traffic`: BIGINT DEFAULT 0  # in GB
   - `status`: VARCHAR(20)  # active, expired, disabled, frozen
   - `protocol`: VARCHAR(20)  # vmess, vless
   - `config_json`: TEXT NULL  # JSON configuration for additional features
   - `subscription_url`: VARCHAR(255) NULL
   - `notes`: TEXT NULL
   - `freeze_start`: DATETIME NULL
   - `freeze_end`: DATETIME NULL
   - `is_trial`: BOOLEAN DEFAULT FALSE
   - `auto_renew`: BOOLEAN DEFAULT FALSE
   - `last_notified`: DATETIME NULL
   - `created_at`: DATETIME
   - `updated_at`: DATETIME

8. **client_id_sequences**
   - `id`: INT PRIMARY KEY AUTO_INCREMENT
   - `location_id`: INT FOREIGN KEY
   - `last_id`: INT DEFAULT 0
   - `prefix`: VARCHAR(20) NULL
   - `created_at`: DATETIME
   - `updated_at`: DATETIME

### 8.3. Financial Tables

9. **orders**
   - `id`: INT PRIMARY KEY AUTO_INCREMENT
   - `user_id`: INT FOREIGN KEY
   - `plan_id`: INT FOREIGN KEY
   - `payment_method`: VARCHAR(50)
   - `amount`: DECIMAL(10,2)
   - `discount_amount`: DECIMAL(10,2) DEFAULT 0
   - `final_amount`: DECIMAL(10,2)
   - `status`: VARCHAR(20)  # pending, completed, failed, cancelled
   - `notes`: TEXT NULL
   - `created_at`: DATETIME
   - `updated_at`: DATETIME

10. **transactions**
   - `id`: INT PRIMARY KEY AUTO_INCREMENT
   - `user_id`: INT FOREIGN KEY
   - `amount`: DECIMAL(10,2)
   - `type`: VARCHAR(20)  # deposit, withdraw, purchase, refund, commission
   - `reference_id`: INT NULL  # Reference to payment_id or order_id
   - `description`: TEXT NULL
   - `balance_after`: DECIMAL(10,2)
   - `created_at`: DATETIME

11. **payments**
   - `id`: INT PRIMARY KEY AUTO_INCREMENT
   - `user_id`: INT FOREIGN KEY
   - `order_id`: INT NULL FOREIGN KEY
   - `amount`: DECIMAL(10,2)
   - `payment_method`: VARCHAR(50)
   - `payment_gateway_id`: VARCHAR(100) NULL
   - `card_number`: VARCHAR(20) NULL
   - `tracking_code`: VARCHAR(100) NULL
   - `receipt_image`: VARCHAR(255) NULL
   - `status`: VARCHAR(20)  # pending, verified, rejected
   - `admin_id`: INT NULL FOREIGN KEY  # Admin who verified
   - `verification_notes`: TEXT NULL
   - `verified_at`: DATETIME NULL
   - `created_at`: DATETIME
   - `updated_at`: DATETIME

12. **bank_cards**
    - `id`: INT PRIMARY KEY AUTO_INCREMENT
    - `bank_name`: VARCHAR(100)
    - `card_number`: VARCHAR(20)
    - `account_number`: VARCHAR(30) NULL
    - `owner_name`: VARCHAR(100)
    - `is_active`: BOOLEAN DEFAULT TRUE
    - `rotation_priority`: INT DEFAULT 0
    - `last_used`: DATETIME NULL
    - `daily_limit`: DECIMAL(15,2) NULL
    - `monthly_limit`: DECIMAL(15,2) NULL
    - `created_at`: DATETIME
    - `updated_at`: DATETIME

### 8.4. System Tables

13. **notification_channels**
    - `id`: INT PRIMARY KEY AUTO_INCREMENT
    - `name`: VARCHAR(100)  # admin, payment, report, log, alert, backup
    - `channel_id`: VARCHAR(100)
    - `description`: TEXT NULL
    - `notification_types`: TEXT NULL  # JSON array of notification types
    - `is_active`: BOOLEAN DEFAULT TRUE
    - `created_at`: DATETIME
    - `updated_at`: DATETIME

14. **settings**
    - `id`: INT PRIMARY KEY AUTO_INCREMENT
    - `key`: VARCHAR(100) UNIQUE
    - `value`: TEXT
    - `description`: TEXT NULL
    - `is_public`: BOOLEAN DEFAULT FALSE
    - `group`: VARCHAR(50) NULL  # For grouping related settings
    - `created_at`: DATETIME
    - `updated_at`: DATETIME

### 8.5. Future Phase Tables

15. **discount_codes** (Future Phase)
    - `id`: INT PRIMARY KEY AUTO_INCREMENT
    - `code`: VARCHAR(50) UNIQUE
    - `discount_type`: VARCHAR(20)  # percentage, fixed
    - `discount_value`: DECIMAL(10,2)
    - `max_uses`: INT NULL
    - `used_count`: INT DEFAULT 0
    - `min_order_amount`: DECIMAL(10,2) DEFAULT 0
    - `max_discount_amount`: DECIMAL(10,2) NULL
    - `expires_at`: DATETIME NULL
    - `is_active`: BOOLEAN DEFAULT TRUE
    - `created_at`: DATETIME
    - `updated_at`: DATETIME

16. **user_devices** (Future Phase)
    - `id`: INT PRIMARY KEY AUTO_INCREMENT
    - `user_id`: INT FOREIGN KEY
    - `device_id`: VARCHAR(100)
    - `device_name`: VARCHAR(100)
    - `device_type`: VARCHAR(50)
    - `last_login`: DATETIME
    - `last_ip`: VARCHAR(45)
    - `is_active`: BOOLEAN DEFAULT TRUE
    - `created_at`: DATETIME
    - `updated_at`: DATETIME

17. **audit_logs** (Future Phase)
    - `id`: INT PRIMARY KEY AUTO_INCREMENT
    - `user_id`: INT NULL FOREIGN KEY
    - `action`: VARCHAR(100)
    - `entity_type`: VARCHAR(50)
    - `entity_id`: INT NULL
    - `details`: TEXT NULL  # JSON with details
    - `ip_address`: VARCHAR(45)
    - `created_at`: DATETIME

**Technical Implementation Details:**
- Use SQLAlchemy ORM for database operations.
- Implement proper relationships between tables.
- Add appropriate indexes for frequently queried columns.
- Use foreign key constraints to maintain data integrity.
- Implement soft deletion where appropriate.
- Encrypt sensitive data in the database.
- Use migrations for schema changes.
- Implement optimistic locking for concurrent updates.
- Create database access layer with repository pattern.
- Use connection pooling for efficient database connections.

## 9. 3x-ui Panel API Integration

### 9.1. Overview
The MoonVPN system integrates with the 3x-ui panel developed by MHSanaei ([GitHub Repository](https://github.com/MHSanaei/3x-ui)). This integration allows for complete management of VPN services through automated API calls.

### 9.2. Authentication Flow
Before any API operation, the system must authenticate with the panel:

1. Send POST request to `/login` endpoint with admin credentials
2. Receive and store session cookies for subsequent requests
3. Implement automatic re-authentication when session expires
4. Use secure credential storage with encryption in the database

### 9.3. API Endpoints
The following 3x-ui panel API endpoints will be integrated:

#### Inbound Management
- **GET `/panel/api/inbounds/list`**: Retrieve all configured inbounds
- **GET `/panel/api/inbounds/get/:id`**: Get details of a specific inbound
- **POST `/panel/api/inbounds/add`**: Create a new inbound
- **POST `/panel/api/inbounds/update/:id`**: Update an existing inbound
- **POST `/panel/api/inbounds/del/:id`**: Delete an inbound

#### Client Management
- **POST `/panel/api/inbounds/addClient`**: Add a new client to an inbound
- **POST `/panel/api/inbounds/:id/delClient/:clientId`**: Remove a client
- **POST `/panel/api/inbounds/updateClient/:clientId`**: Update client configuration
- **GET `/panel/api/inbounds/getClientTraffics/:email`**: Get client traffic statistics
- **GET `/panel/api/inbounds/getClientTrafficsById/:id`**: Get client traffic by ID
- **GET `/panel/api/inbounds/clientIps/:email`**: Get client IP addresses
- **POST `/panel/api/inbounds/clearClientIps/:email`**: Clear client IP addresses
- **POST `/panel/api/inbounds/:id/resetClientTraffic/:email`**: Reset client traffic counter

#### Traffic & System Operations
- **POST `/panel/api/inbounds/resetAllTraffics`**: Reset all traffic statistics
- **POST `/panel/api/inbounds/resetAllClientTraffics/:id`**: Reset all clients' traffic in an inbound
- **POST `/panel/api/inbounds/delDepletedClients/:id`**: Remove clients with depleted traffic/time
- **GET `/panel/api/inbounds/createbackup`**: Create system backup
- **GET `/panel/api/inbounds/onlines`**: Get list of online users

### 9.4. Integration Architecture
The panel integration is structured in layers:

1. **HTTP Client Layer** (`XuiPanelClient` class in `integrations/panels/client.py`):
   - Handles low-level HTTP communications with the panel API
   - Manages authentication and session state
   - Implements retry logic and error handling
   - Provides connection pooling for performance
   - Implements methods corresponding to each API endpoint
   - Handles serialization/deserialization of requests and responses
   - Contains no business logic, only communication with the panel API

2. **Service Layer** (`PanelService` class in `api/services/panel_service.py`):
   - Acts as an abstraction layer between the application and the panel API client
   - Offers high-level business operations
   - Manages multiple panel instances
   - Implements panel selection algorithms
   - Handles failover between panels
   - Coordinates scheduled health checks
   - Contains business logic for panel management
   - Uses dependency injection for the HTTP client

3. **API Endpoints Layer** (in `api/routes/panel.py`):
   - Exposes REST endpoints for panel operations
   - Handles request validation and authorization
   - Provides standardized response formats
   - Implements rate limiting and security controls
   - Uses dependency injection for the PanelService

### 9.5. Health Monitoring System
A comprehensive health monitoring system checks panel status:

- Scheduled health checks every 5-15 minutes
- Monitoring of CPU, memory, and disk usage
- Verification of Xray service status
- Tracking response times and availability percentage
- Notification system for outages or performance issues
- Historical status data for performance analysis

### 9.6. Panel Selection Algorithm
The system uses a sophisticated algorithm for selecting the optimal panel for new clients:

1. Filter panels by requested location
2. Consider current load (number of clients)
3. Verify panel health status
4. Evaluate recent performance metrics
5. Apply priority settings for manual overrides
6. Select panel with optimal conditions

### 9.7. Failover Mechanism
In case of panel failure, the system provides:

1. Automatic detection of failing panels through health checks
2. Client migration capability to healthy panels in the same location
3. Temporary traffic routing for minimal service disruption
4. Notification to administrators through alert channels
5. Automatic retry of connections to restore service

## 10. System Architecture & Communication Flow

### 10.1. Service-Oriented Architecture
The system is designed with a service-oriented architecture that separates concerns and promotes maintainability:

1. **Service Layer**:
   - Contains all business logic in dedicated service classes
   - Each service focuses on a specific domain (panels, users, clients, payments, etc.)
   - Services are injected as dependencies where needed
   - Services may communicate with other services through well-defined interfaces
   - All services follow consistent patterns and error handling approaches

2. **Repository Layer**:
   - Abstracts database operations from services
   - Provides CRUD operations for models
   - Handles transaction management
   - Implements query optimization
   - Encapsulates all SQL-related logic

3. **Presentation Layer**:
   - API routes and bot handlers that interact with users
   - Validates input and formats output
   - Handles HTTP-specific concerns
   - Uses dependency injection to access services

4. **Integration Layer**:
   - Adapters for external systems (panels, payment gateways)
   - Handles communication protocols and formats
   - Implements retries and error handling for external systems

### 10.2. Bot-API Communication
The Telegram bot communicates with the API service through asynchronous HTTP requests:

1. Bot receives user commands or button clicks
2. Bot handlers process input and format API requests
3. Asynchronous HTTP client sends requests to API endpoints
4. API processes requests and returns responses
5. Bot formats responses in user-friendly Persian messages with appropriate emojis
6. Interactive keyboards are generated based on available options

### 10.3. Data Flow Architecture
The system follows a clear data flow pattern:

1. **User Input** → Telegram Bot receives commands/actions
2. **Bot Handlers** → Process and validate user input
3. **Bot Services** → Handle bot-specific business logic
4. **API Client** → Formats and sends requests to API
5. **API Controller** → Validates requests and authorizes actions
6. **Service Layer** → Implements business logic
7. **Repository Layer** → Handles database operations
8. **Integration Layer** → Communicates with external systems
9. **Response Path** → Returns results back through the chain
10. **Bot Output** → Formats data into user-friendly messages

### 10.4. Notification System Flow
The notification system operates as follows:

1. System events trigger notification requests
2. NotificationService processes the notification type and content
3. NotificationManager selects appropriate channel based on notification category
4. Message is formatted according to channel standards
5. Telegram API sends message to the designated channel
6. Interactive buttons are attached if admin action is required
7. Admin responses are captured by callback query handlers
8. Actions are processed and confirmation messages sent

### 10.5. Security Architecture
The system implements a multi-layered security approach:

1. Encrypted environment variables for sensitive credentials
2. JWT authentication for API access
3. Role-based access control for all operations
4. Input validation and sanitization at all entry points
5. Encrypted storage of panel credentials in database
6. Rate limiting to prevent abuse
7. Comprehensive logging for audit trails
8. Regular automated backups
9. Secure communication with panels via HTTPS

### 10.6. Dependency Injection System
The system uses FastAPI's dependency injection system to manage dependencies:

1. Services are defined as classes that can be injected into routes
2. Database session is injected into repositories
3. Repositories are injected into services
4. Integration clients are injected into services
5. Services are injected into API routes
6. This pattern enables:
   - Easy testing through mocking
   - Clear separation of concerns
   - Consistent dependency lifecycle management
   - Reduced coupling between components
