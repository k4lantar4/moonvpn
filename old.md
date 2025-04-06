
## Project: MoonVPN System

### Project Overview
MoonVPN is a comprehensive management and sales system for V2Ray VPN services, initially focusing on integration with the 3x-ui panel (Sanai panel). The system provides an end-to-end solution for managing VPN servers, client accounts, payments, and reseller networks through an intuitive Telegram bot interface and a powerful API backend.

### Core Technologies:
- **Core API:** FastAPI (Python 3.10+) - High-performance asynchronous API framework with automatic OpenAPI documentation
- **Telegram Bot:** python-telegram-bot (v20+) - Asynchronous library for Telegram Bot API with webhook support
- **Database:** MySQL 8.0+ with SQLAlchemy ORM and Alembic migrations for versioned schema management
- **Caching:** Redis for performance optimization and rate limiting implementation
- **Deployment:** Docker containers and Docker Compose for simplified deployment and scaling
- **Installation:** Custom bash script (`moonvpn` command) for Ubuntu 22.04 LTS with automatic dependency resolution
- **Monitoring:** Prometheus integration for system metrics collection and Grafana dashboards

### Project Structure (Simplified):
```
moonvpn/
├── api/                           # API server & business logic
│   ├── models.py                  # Database models
│   ├── routes/                    # API routes by feature
│   │   ├── auth.py                # Authentication routes
│   │   ├── panels.py              # Panel management routes
│   │   ├── clients.py             # Client management routes
│   │   ├── plans.py               # Plan management routes
│   │   ├── payments.py            # Payment routes
│   │   └── admin.py               # Admin routes
│   ├── schemas.py                 # Pydantic schemas
│   ├── services.py                # Business logic
│   ├── dependencies.py            # FastAPI dependencies
│   └── main.py                    # API entry point
│
├── bot/                           # Telegram bot
│   ├── handlers/                  # Bot command handlers by user type
│   │   ├── user.py                # User handlers
│   │   ├── admin.py               # Admin handlers
│   │   └── seller.py              # Seller handlers
│   ├── keyboards.py               # Telegram keyboards
│   ├── channels.py                # Channel notifications
│   ├── states.py                  # Conversation states
│   ├── utils.py                   # Utility functions
│   └── main.py                    # Bot entry point
│
├── core/                          # Shared core components
│   ├── config.py                  # Configuration management
│   ├── database.py                # Database setup & sessions
│   ├── security.py                # Security functions
│   ├── logging.py                 # Logging setup
│   ├── cache.py                   # Redis cache implementation
│   └── metrics.py                 # Prometheus metrics collectors
│
├── integrations/                  # External integrations
│   ├── panels.py                  # Panel integrations (3x-ui/Sanai) 
│   ├── payments.py                # Payment integrations (ZarinPal)
│   └── sms.py                     # SMS verification service integration
│
├── migrations/                    # Database migrations
│   └── versions/                  # Migration versions
│
├── scripts/                       # Utility scripts
│   ├── install.sh                 # Installation script
│   ├── backup.sh                  # Backup script
│   ├── setup_db.py                # Database setup
│   └── healthcheck.py             # System health monitoring
│
├── tests/                         # Tests
│   ├── api_tests.py               # API tests
│   ├── bot_tests.py               # Bot tests
│   └── integration_tests.py       # Integration tests
│
├── .env.example                   # Example environment variables
├── alembic.ini                    # Alembic configuration
├── docker-compose.yml             # Docker setup
├── Dockerfile                     # Docker image definition
├── requirements.txt               # Python dependencies
└── README.md                      # Project documentation
```

### Key Features in Detail:

#### 1. Panel Management System
- **Multi-Panel Support**: Ability to connect to multiple 3x-ui panels simultaneously
- **Automatic Health Checking**: Regular verification of panel availability and statistics
- **Location Management**: Grouping panels by geographic location for user selection
- **Inbound Management**: Creating and managing inbounds on connected panels
- **Implementation**: REST API client with connection pooling and error handling
- **Enhanced Feature**: Automated failover system for transferring clients between panels in case of outages

#### 2. Telegram Channel-Based Notification System
- **Single Bot Architecture**: One primary bot with specialized Telegram channels for different functions
- **Channel Management**: Bot automatically sends appropriate messages to configured channels
- **Interactive Components**: Inline buttons in channels for admin approvals and actions
- **Specialized Channels**:
  - **Admin Channel**: For administrative alerts and approvals
  - **Payment Verification Channel**: For payment receipt verification by authorized admins
  - **Report Channel**: For system performance metrics and statistics
  - **Log Channel**: For detailed system activity logging
  - **Alert Channel**: For service disruption notifications
  - **Backup Channel**: For receiving regular database and configuration backups
- **Enhanced Feature**: Advanced channel analytics dashboard showing message engagement and admin response times

#### 3. Client Account Management
- **Protocol Support**: V2ray with VMESS/VLESS protocols
- **Account Creation**: Automatic account creation on selected panels
- **Status Monitoring**: Regular checking of account status, traffic usage
- **Account Modification**: Change protocol, server location, reset usage statistics
- **Account Lifecycle**: Creation, suspension, reactivation, and deletion workflows
- **Enhanced Feature**: Intelligent traffic allocation that monitors usage patterns and recommends optimal plans

#### 4. Payment System
- **Manual Card-to-Card**: 
  - User submits payment details and receipt through bot
  - Receipt forwarded to payment verification channel with approval buttons
  - Rotating bank card selection based on time of day or random assignment
  - Automated wallet crediting upon admin approval via channel buttons
  - All receipts archived in super-admin channel for oversight
- **ZarinPal Integration**:
  - Seamless integration with ZarinPal payment gateway
  - Secure payment processing with callbacks
  - Automatic wallet updating upon successful payment
- **Internal Wallet**:
  - Balance tracking for all users
  - Transaction history and reporting
  - Automatic deductions for purchases and renewals
- **Enhanced Feature**: AI-powered receipt verification system that can pre-verify standard bank receipts before admin approval

#### 5. Simplified Seller/Reseller System
- **Percentage-Based Discount Model**: Sellers receive configurable percentage discounts on all plans
- **Commission Tracking**: All sales and corresponding commissions tracked and reported
- **Seller Dashboard**: Comprehensive dashboard accessible within the main bot
- **Automatic Settlement**: Regular settlement processing through wallet system
- **Referral System**: Each seller gets unique referral links for tracking clients
- **Enhanced Feature**: Performance-based commission tiers that automatically adjust rates based on sales volume

#### 6. Free Trial System
- **Eligibility**: Verification of Iranian numbers (+98)
- **Limitations**: One-time usage per user
- **Implementation**: Temporary account creation with automatic expiration
- **Anti-Abuse**: Prevention of multiple trial requests
- **Enhanced Feature**: Limited-time promotional campaigns with custom trial parameters (duration, traffic, etc.)

#### 7. User Account Features
- **Account Freezing**: Temporarily pause service without losing remaining time
- **User Notes**: Ability to add notes to client accounts for reference
- **Protocol Changes**: Switch between supported protocols
- **Location Changes**: Move account between available server locations
- **Auto-Renewal**: Toggle option for automatic service renewal
- **Enhanced Feature**: Configurable usage alerts that notify users when they reach traffic thresholds (50%, 75%, 90%)

#### 8. Administrative Tools
- **User Management**: Create, modify, and delete user accounts
- **Plan Management**: Create and modify service plans with various configurations
- **Statistics Dashboard**: Real-time system performance metrics
- **Financial Reporting**: Comprehensive financial reports and transaction logs
- **Broadcast Messaging**: Send announcements to all users or specific groups
- **Channel Configuration**: Manage all notification channels directly through bot interface
- **Server Management**: Add/edit/remove servers without requiring terminal access
- **Enhanced Feature**: Scheduled reports delivery system with customizable KPIs and metrics

#### 9. Backup and Security
- **Automated Backups**: Regular database and configuration backups sent to dedicated channel
- **Encryption**: Secure storage of sensitive information
- **Access Control**: Role-based permissions system
- **Activity Logging**: Comprehensive logging of system activities sent to log channel
- **Enhanced Feature**: Geographic access restrictions with IP-based anomaly detection for admin accounts

#### 10. API Documentation and Developer Tools
- **Interactive API Docs**: Swagger/OpenAPI documentation for all endpoints
- **API Key Management**: Create and manage API keys for external integrations
- **Webhook Support**: Configure webhooks for real-time event notifications
- **Rate Limiting**: Configurable rate limits to prevent abuse
- **Enhanced Feature**: Developer sandbox environment for testing integrations without affecting production data

## Project Phases (Implementation Plan):

### Phase 0: Core Infrastructure Setup (2 weeks)
- **Database Schema Design**:
  - Design and implement all core database tables
  - Set up Alembic migrations framework
  - Create initial database migration script
  - Implement database versioning and rollback capability
- **Installation Script Development**:
  - Create `moonvpn` command-line tool for installation
  - Implement system requirements checking
  - Develop Docker setup configuration
  - Add health check and troubleshooting diagnostics
- **API Foundation**:
  - Implement FastAPI application structure
  - Create health check endpoints
  - Set up authentication framework (JWT)
  - Implement basic CRUD operations for core entities
  - Configure rate limiting and API documentation
- **Telegram Bot Skeleton**:
  - Set up bot framework with `/start` command
  - Implement basic conversation handlers
  - Create notification channel system
  - Configure webhook mode for production
- **Panel Integration**:
  - Implement 3x-ui API client
  - Create inbound listing and retrieval functionality
  - Set up connection pooling and error handling
  - Add panel connectivity monitoring
- **Testing Framework**:
  - Set up pytest testing environment
  - Create basic API and integration tests
  - Implement CI pipeline for automated testing
  - Add coverage reporting
- **Deliverables**: 
  - Working API with health endpoints
  - Basic Telegram bot with connection to API
  - Functional panel integration with test capabilities
  - Automated installation script
  - CI/CD pipeline for development workflow

### Phase 1: User and Panel Management (3 weeks)
- **User Authentication System**:
  - Implement user registration via Telegram
  - Create user role system (admin, user, seller)
  - Develop permission management system
  - Add phone verification system for Iranian numbers
  - Implement session management and device tracking
- **Panel Management**:
  - Create panel addition/editing/removal system
  - Implement panel health monitoring
  - Develop location management system
  - Add automatic panel selection based on load
  - Configure TLS certificate monitoring
- **Bot Command Framework**:
  - Implement all basic bot commands
  - Create inline keyboard navigation system
  - Develop state management for complex conversations
  - Add pagination for large result sets
  - Implement conversation timeout handling
- **Channel Notification System**:
  - Implement channel configuration management via bot
  - Create formatted notifications for different channels
  - Develop interactive components for admin actions in channels
  - Add message scheduling capabilities
  - Configure notification batching to prevent spam
- **Admin Dashboard**:
  - Implement admin command handlers
  - Create user management system
  - Develop panel administration tools
  - Add real-time system monitoring
  - Implement admin action logging and audit trail
- **Deliverables**:
  - Complete user authentication and management
  - Fully functional panel management system
  - Working bot command structure with admin capabilities
  - Operational notification channels
  - Administrative dashboard with monitoring tools

### Phase 2: Service Plans and Client Management (3 weeks)
- **Plan Management**:
  - Implement service plan creation and management
  - Develop pricing structure system
  - Create plan activation/deactivation functionality
  - Add time-limited promotional plans
  - Implement configurable plan visibility options
- **Purchase Flow**:
  - Implement purchase conversation in bot
  - Create order processing system
  - Develop order status tracking
  - Add cart functionality for multiple purchases
  - Implement purchase recommendation engine
- **Client Creation**:
  - Implement client creation on 3x-ui panel
  - Develop client configuration generation
  - Create QR code and configuration link generation
  - Add batch client creation capability
  - Implement client template system
- **Client Monitoring**:
  - Implement traffic usage monitoring
  - Create expiration checking system
  - Develop status reporting functionality
  - Add usage pattern analytics
  - Implement anomaly detection for unusual traffic patterns
- **Wallet System**:
  - Implement internal wallet system
  - Create transaction logging
  - Develop wallet balance management
  - Add wallet transfer between users
  - Implement automatic balance notifications
- **Deliverables**:
  - Complete plan management system
  - Functional purchase flow
  - Automated client creation and configuration
  - Working client monitoring and wallet systems
  - Enhanced client analytics and reporting

### Phase 3: Advanced Client Features (3 weeks)
- **Protocol Management**:
  - Implement protocol change functionality
  - Develop protocol-specific configuration options
  - Create protocol migration process
  - Add automatic protocol optimization
  - Implement protocol performance analytics
- **Location Change**:
  - Implement server location change system
  - Develop cross-panel client migration
  - Create location availability checking
  - Add location performance comparison
  - Implement geographic proximity recommendation
- **Service Freezing**:
  - Implement account freeze/unfreeze functionality
  - Develop time adjustment calculations
  - Create freeze status tracking
  - Add scheduled freezing capability
  - Implement maximum freeze duration limitations
- **Service Renewal**:
  - Implement manual renewal process
  - Develop renewal notification system
  - Create renewal pricing calculations
  - Add early renewal discounts
  - Implement renewal reminder scheduling
- **Traffic/Time Management**:
  - Implement traffic addition functionality
  - Develop time extension system
  - Create usage statistics reporting
  - Add usage prediction algorithms
  - Implement traffic gifting between users
- **Client Notes**:
  - Implement note addition and management
  - Develop note search and filtering
  - Create note notification system
  - Add templated notes for common scenarios
  - Implement note categorization
- **Client Removal**:
  - Implement client removal process
  - Develop removal confirmation system
  - Create removal record keeping
  - Add automated cleanup of expired clients
  - Implement client archiving instead of permanent deletion
- **Deliverables**:
  - Complete client management features
  - Functional protocol and location changing
  - Working freeze/unfreeze system
  - Operational renewal and extension features
  - Advanced client lifecycle management

### Phase 4: Payment System Implementation (2 weeks)
- **Card-to-Card Payment**:
  - Implement payment submission in bot with receipt upload
  - Create payment verification channel with interactive buttons
  - Develop rotating card system (time-based or random)
  - Implement automatic wallet crediting upon approval
  - Create receipt archiving in super-admin channel
  - Add image recognition for receipt validation
  - Implement payment timeout handling
- **ZarinPal Integration**:
  - Implement ZarinPal API client
  - Create payment initiation process
  - Develop callback handling
  - Implement payment verification
  - Add transaction reconciliation process
  - Create payment gateway status monitoring
- **Discount System**:
  - Implement discount code creation and management
  - Develop code application logic
  - Create discount tracking and reporting
  - Add time-limited discount campaigns
  - Implement referral-based discounts
  - Create stackable discount capability
- **Payment Notifications**:
  - Implement payment status notifications
  - Create receipt generation
  - Develop payment history viewing
  - Add payment export functionality
  - Implement configurable notification preferences
  - Create detailed transaction receipts
- **Deliverables**:
  - Complete card-to-card payment system
  - Functional ZarinPal integration
  - Working discount code system
  - Comprehensive payment notifications
  - Advanced financial tracking and reporting

### Phase 5: Seller System and Affiliate Features (2 weeks)
- **Seller Management**:
  - Implement seller role with percentage-based discounts
  - Develop commission calculation and tracking
  - Create seller dashboard within main bot
  - Add seller performance analytics
  - Implement tiered commission structure
  - Create seller approval workflow
- **Referral System**:
  - Implement referral link generation
  - Develop referral tracking
  - Create referral statistics reporting
  - Add multi-level referral capabilities
  - Implement referral reward customization
  - Create referral marketing materials
- **Financial Reporting**:
  - Implement detailed financial reports
  - Develop seller performance metrics
  - Create settlement processing
  - Add revenue forecasting
  - Implement tax calculation and reporting
  - Create financial data export functionality
- **User Limitations**:
  - Implement user throttling system
  - Develop abuse prevention measures
  - Create user restriction management
  - Add IP-based access controls
  - Implement suspicious activity detection
  - Create graduated restriction system
- **Deliverables**:
  - Complete seller management system
  - Working referral system
  - Comprehensive financial reporting
  - Effective user limitation mechanisms
  - Advanced sales analytics dashboard

### Phase 6: Advanced Features and Optimization (2 weeks)
- **Free Trial System**:
  - Implement trial eligibility checking
  - Develop trial account creation
  - Create trial expiration handling
  - Implement anti-abuse measures
  - Add conversion tracking from trial to paid
  - Create configurable trial parameters
  - Implement A/B testing for trial offers
- **Free Proxy System**:
  - Implement proxy configuration generation
  - Develop proxy server management
  - Create proxy usage tracking
  - Add rotating proxy capabilities
  - Implement proxy health monitoring
  - Create proxy access controls
- **Bulk Messaging**:
  - Implement user group targeting
  - Develop message scheduling
  - Create message template system
  - Add message performance analytics
  - Implement message personalization
  - Create multi-channel messaging
- **Auto-Renewal System**:
  - Implement renewal preference toggle
  - Develop automatic renewal processing
  - Create renewal failure handling
  - Add graduated renewal reminders
  - Implement renewal discount options
  - Create renewal analytics dashboard
- **Backup System**:
  - Implement automated database backups
  - Develop configuration backups
  - Create backup verification and restoration system
  - Set up backup delivery to dedicated channel
  - Add encrypted backup storage
  - Implement geographic backup redundancy
  - Create backup retention policies
- **Code Optimization**:
  - Perform performance profiling
  - Implement caching strategies
  - Develop resource usage optimization
  - Add query optimization
  - Implement connection pooling
  - Create load balancing capability
- **Final Testing**:
  - Conduct comprehensive system testing
  - Perform stress and load testing
  - Implement final bug fixes
  - Add security penetration testing
  - Perform user experience testing
  - Create system documentation
- **Deliverables**:
  - Complete free trial and proxy systems
  - Functional bulk messaging capabilities
  - Working auto-renewal system
  - Robust backup and restoration system
  - Optimized and thoroughly tested codebase
  - Comprehensive system documentation

## Database Schema:

### Core Tables:

1. **users**
   - `id`: INT PRIMARY KEY AUTO_INCREMENT
   - `telegram_id`: BIGINT UNIQUE
   - `username`: VARCHAR(255) NULL
   - `full_name`: VARCHAR(255)
   - `phone`: VARCHAR(20) NULL
   - `email`: VARCHAR(255) NULL
   - `role_id`: INT FOREIGN KEY
   - `balance`: DECIMAL(10,2) DEFAULT 0
   - `is_banned`: BOOLEAN DEFAULT FALSE
   - `referral_code`: VARCHAR(20) UNIQUE
   - `referred_by`: INT NULL FOREIGN KEY
   - `lang`: VARCHAR(10) DEFAULT 'fa'
   - `last_login`: DATETIME NULL
   - `login_ip`: VARCHAR(45) NULL
   - `created_at`: DATETIME
   - `updated_at`: DATETIME

2. **roles**
   - `id`: INT PRIMARY KEY AUTO_INCREMENT
   - `name`: VARCHAR(50) UNIQUE
   - `discount_percent`: INT DEFAULT 0
   - `commission_percent`: INT DEFAULT 0
   - `max_clients`: INT DEFAULT 0
   - `can_create_client`: BOOLEAN DEFAULT FALSE
   - `can_delete_client`: BOOLEAN DEFAULT FALSE
   - `can_edit_client`: BOOLEAN DEFAULT FALSE
   - `can_manage_panels`: BOOLEAN DEFAULT FALSE
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
   - `url`: VARCHAR(255)
   - `username`: VARCHAR(100)
   - `password`: VARCHAR(255) ENCRYPTED
   - `location_id`: INT FOREIGN KEY
   - `panel_type`: VARCHAR(50) DEFAULT '3x-ui'
   - `inbound_id`: INT NULL
   - `max_clients`: INT DEFAULT 0
   - `current_clients`: INT DEFAULT 0
   - `is_active`: BOOLEAN DEFAULT TRUE
   - `last_check`: DATETIME NULL
   - `status`: VARCHAR(20) DEFAULT 'unknown'
   - `priority`: INT DEFAULT 0
   - `created_at`: DATETIME
   - `updated_at`: DATETIME

4. **plans**
   - `id`: INT PRIMARY KEY AUTO_INCREMENT
   - `name`: VARCHAR(100)
   - `traffic`: BIGINT  # in GB
   - `days`: INT
   - `price`: DECIMAL(10,2)
   - `description`: TEXT NULL
   - `is_active`: BOOLEAN DEFAULT TRUE
   - `is_featured`: BOOLEAN DEFAULT FALSE
   - `max_clients`: INT NULL
   - `protocols`: VARCHAR(255) NULL  # comma-separated protocols
   - `created_at`: DATETIME
   - `updated_at`: DATETIME

5. **locations**
   - `id`: INT PRIMARY KEY AUTO_INCREMENT
   - `name`: VARCHAR(100)
   - `flag`: VARCHAR(10)
   - `country_code`: VARCHAR(2)
   - `is_active`: BOOLEAN DEFAULT TRUE
   - `description`: TEXT NULL
   - `created_at`: DATETIME
   - `updated_at`: DATETIME

6. **orders**
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

7. **clients**
   - `id`: INT PRIMARY KEY AUTO_INCREMENT
   - `user_id`: INT FOREIGN KEY
   - `panel_id`: INT FOREIGN KEY
   - `plan_id`: INT FOREIGN KEY
   - `order_id`: INT FOREIGN KEY
   - `client_uuid`: VARCHAR(36)
   - `email`: VARCHAR(255)
   - `expire_date`: DATETIME
   - `traffic`: BIGINT  # in GB
   - `used_traffic`: BIGINT DEFAULT 0  # in GB
   - `status`: VARCHAR(20)  # active, expired, disabled, frozen
   - `protocol`: VARCHAR(20)  # vmess, vless
   - `notes`: TEXT NULL
   - `freeze_start`: DATETIME NULL
   - `freeze_end`: DATETIME NULL
   - `is_trial`: BOOLEAN DEFAULT FALSE
   - `auto_renew`: BOOLEAN DEFAULT FALSE
   - `last_notified`: DATETIME NULL
   - `created_at`: DATETIME
   - `updated_at`: DATETIME

8. **bank_cards**
   - `id`: INT PRIMARY KEY AUTO_INCREMENT
   - `bank_name`: VARCHAR(100)
   - `card_number`: VARCHAR(20)
   - `account_number`: VARCHAR(30) NULL
   - `owner_name`: VARCHAR(100)
   - `is_active`: BOOLEAN DEFAULT TRUE
   - `rotation_priority`: INT DEFAULT 0  # For card rotation system
   - `last_used`: DATETIME NULL
   - `daily_limit`: DECIMAL(15,2) NULL
   - `monthly_limit`: DECIMAL(15,2) NULL
   - `created_at`: DATETIME
   - `updated_at`: DATETIME

9. **transactions**
   - `id`: INT PRIMARY KEY AUTO_INCREMENT
   - `user_id`: INT FOREIGN KEY
   - `amount`: DECIMAL(10,2)
   - `type`: VARCHAR(20)  # deposit, withdraw, purchase, refund, commission
   - `reference_id`: INT NULL  # Reference to order_id, payment_id, etc.
   - `description`: TEXT NULL
   - `balance_after`: DECIMAL(10,2)
   - `created_at`: DATETIME

10. **payments**
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

11. **settings**
    - `id`: INT PRIMARY KEY AUTO_INCREMENT
    - `key`: VARCHAR(100) UNIQUE
    - `value`: TEXT
    - `description`: TEXT NULL
    - `is_public`: BOOLEAN DEFAULT FALSE
    - `created_at`: DATETIME
    - `updated_at`: DATETIME

12. **discount_codes**
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

13. **notification_channels**
    - `id`: INT PRIMARY KEY AUTO_INCREMENT
    - `name`: VARCHAR(100)  # admin, payment, report, log, alert, backup
    - `channel_id`: VARCHAR(100)
    - `description`: TEXT NULL
    - `notification_types`: TEXT NULL  # JSON array of notification types
    - `is_active`: BOOLEAN DEFAULT TRUE
    - `created_at`: DATETIME
    - `updated_at`: DATETIME

14. **payment_admins**
    - `id`: INT PRIMARY KEY AUTO_INCREMENT
    - `user_id`: INT FOREIGN KEY
    - `bank_card_id`: INT FOREIGN KEY
    - `is_active`: BOOLEAN DEFAULT TRUE
    - `max_daily_approvals`: INT NULL
    - `created_at`: DATETIME
    - `updated_at`: DATETIME

15. **commissions**
    - `id`: INT PRIMARY KEY AUTO_INCREMENT
    - `seller_id`: INT FOREIGN KEY
    - `client_id`: INT FOREIGN KEY
    - `order_id`: INT FOREIGN KEY
    - `amount`: DECIMAL(10,2)
    - `commission_amount`: DECIMAL(10,2)
    - `commission_percent`: DECIMAL(5,2)
    - `status`: VARCHAR(20) DEFAULT 'pending'  # pending, paid
    - `created_at`: DATETIME
    - `updated_at`: DATETIME

16. **audit_logs**
    - `id`: INT PRIMARY KEY AUTO_INCREMENT
    - `user_id`: INT NULL FOREIGN KEY
    - `action`: VARCHAR(100)
    - `entity_type`: VARCHAR(50)
    - `entity_id`: INT NULL
    - `details`: TEXT NULL  # JSON with details
    - `ip_address`: VARCHAR(45)
    - `created_at`: DATETIME

17. **backups**
    - `id`: INT PRIMARY KEY AUTO_INCREMENT
    - `file_name`: VARCHAR(255)
    - `file_size`: BIGINT
    - `backup_type`: VARCHAR(20)  # database, config, full
    - `status`: VARCHAR(20)  # completed, failed
    - `channel_message_id`: VARCHAR(20) NULL
    - `notes`: TEXT NULL
    - `created_at`: DATETIME

18. **user_devices**
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

## Telegram Bot Commands:

### User Commands:
- `/start` - Start the bot and register user
- `/help` - Display help information
- `/plans` - Show available service plans
- `/buy` - Start purchase process
- `/myaccount` - Manage user accounts
  - View account details
  - Get configuration (QR/links)
  - Check usage statistics
  - Freeze/unfreeze account
  - Change protocol/location
  - Add notes
  - Renew service
- `/profile` - View and edit user profile
- `/wallet` - Manage wallet
  - Check balance
  - Add funds
  - View transaction history
- `/support` - Contact support
- `/free` - Request free trial (if eligible)
- `/proxy` - Get free HTTP proxy configuration
- `/notify` - Configure usage notifications
- `/devices` - Manage connected devices

### Admin Commands:
- `/admin` - Access admin panel
  - User management
  - Plan management
  - Panel management
  - Order management
  - Financial management
  - System settings
  - Channel configuration
- `/stats` - View system statistics
  - User statistics
  - Sales statistics
  - Traffic statistics
  - Server health statistics
- `/broadcast` - Send message to users
- `/addplan` - Add new service plan
- `/addpanel` - Add new panel
- `/logs` - View system logs
- `/transactions` - View all transactions
- `/orders` - Manage orders
- `/clients` - View all clients
- `/settings` - Edit system settings
- `/channels` - Configure notification channels
- `/cards` - Manage payment cards and rotation
- `/backup` - Trigger manual backup
- `/metrics` - View real-time system metrics
- `/audit` - View audit log of admin actions

### Seller Commands:
- `/seller` - Access seller dashboard
  - View commission statistics
  - View referral statistics
- `/clients` - View seller's clients
- `/earnings` - View earnings and commissions
- `/withdraw` - Request commission withdrawal
- `/promote` - Generate promotional materials
- `/analytics` - View customer conversion analytics

## Channel-Based Notification System:

### 1. Admin Channel
- **Purpose**: General administrative notifications
- **Content**:
  - System status updates
  - Critical alerts
  - Admin action requests
  - New user registrations
  - Important statistics
- **Interactive Features**:
  - Quick approval buttons for common requests
  - Direct links to admin dashboard sections
  - Priority flagging of urgent issues

### 2. Payment Verification Channel
- **Purpose**: Process card-to-card payment verifications
- **Content**:
  - Payment receipts with user details
  - Interactive buttons for verification/rejection
  - Payment amount and timestamp
  - Assigned bank card information
  - Automatic status updates
- **Interactive Features**:
  - One-tap approve/reject buttons
  - Quick note addition option
  - Suspicious payment flagging
  - Quick user history access

### 3. Report Channel
- **Purpose**: Regular system performance metrics
- **Content**:
  - Daily/weekly/monthly sales reports
  - User growth statistics
  - Traffic usage summaries
  - Revenue analytics
  - Plan popularity metrics
- **Interactive Features**:
  - Date range adjustment buttons
  - Metric filtering options
  - Export to PDF/Excel buttons
  - Comparison view toggles

### 4. Log Channel
- **Purpose**: Detailed system activity logs
- **Content**:
  - User actions
  - Admin operations
  - System events
  - Error reports
  - Security alerts
- **Interactive Features**:
  - Severity filtering
  - Entity-based filtering
  - Time range selection
  - Log export functionality

### 5. Alert Channel
- **Purpose**: Service disruption notifications
- **Content**:
  - Panel connectivity issues
  - Server downtime alerts
  - Resource exhaustion warnings
  - Security breach notifications
  - Critical error reports
- **Interactive Features**:
  - Acknowledgment buttons
  - Escalation options
  - Quick fix action buttons
  - Status update requests

### 6. Backup Channel
- **Purpose**: Storing system backups
- **Content**:
  - Database backup files
  - Configuration backups
  - Backup verification reports
  - Restoration instructions
  - Backup schedule notifications
- **Interactive Features**:
  - Backup verification buttons
  - Restoration initiation
  - Manual backup triggers
  - Backup testing options