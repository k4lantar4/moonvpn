*This scratchpad file serves as a phase-specific task tracker and implementation planner. The Mode System on Line 1 is critical and must never be deleted. It defines two core modes: Implementation Type for new feature development and Bug Fix Type for issue resolution. Each mode requires specific documentation formats, confidence tracking, and completion criteria. Use "plan" trigger for planning phase (🎯) and "agent" trigger for execution phase (⚡) after reaching 95% confidence. Follow strict phase management with clear documentation transfer process.*

`MODE SYSTEM TYPES (DO NOT DELETE!):
1. Implementation Type (New Features):
   - Trigger: User requests new implementation
   - Format: MODE: Implementation, FOCUS: New functionality
   - Requirements: Detailed planning, architecture review, documentation
   - Process: Plan mode (🎯) → 95% confidence → Agent mode (⚡)

2. Bug Fix Type (Issue Resolution):
   - Trigger: User reports bug/issue
   - Format: MODE: Bug Fix, FOCUS: Issue resolution
   - Requirements: Problem diagnosis, root cause analysis, solution verification
   - Process: Plan mode (🎯) → Chain of thought analysis → Agent mode (⚡)

Cross-reference with @memories.md and @lessons-learned.md for context and best practices.`

# Mode: PLAN 🎯
MODE: Implementation, FOCUS: Project Initialization & Phase 0 Setup
Confidence: 95%
Current Phase: PHASE-0
Status: Active
Last Updated: v0.0.6

# Phase Tracking

## Phase 0: Core Infrastructure & Setup (~2 weeks)
Status: In Progress
Phase Completion Criteria:
- [X] Docker environment fully configured and tested
- [X] Database schema properly initialized
- [X] Core API and Bot respond to basic requests
- [X] Persian language support implemented
- [ ] Test coverage meets minimum requirements
- [ ] Documentation updated
- [ ] All Phase 0 tasks completed and tested

## Current Status Summary (v0.0.6)

Completed Tasks:
1. [ID-001] ✅ Project directory structure
2. [ID-002] ✅ FastAPI application skeleton
3. [ID-003] ✅ Telegram Bot skeleton
4. [ID-004] ✅ Database Models & Alembic
5. [ID-005] ✅ Environment configuration
6. [ID-006] ✅ Docker environment
7. [ID-009] ✅ Core config & database
8. [ID-012] ✅ Logging system
9. [ID-010] ✅ Persian language support

Next Priority Tasks:
1. [ID-007] 3x-ui panel connection (High) - In progress
2. [ID-013] Test framework setup (High)
3. [ID-011] Notification channels (Medium)
4. [ID-008] MoonVPN command (Medium)

Infrastructure Status:
- Docker Environment: ✅ Configured and healthy
- Database: ✅ Initialized with required tables
- API Service: ✅ Running and healthy
- Bot Service: ✅ Running and healthy (Verified with test message)
- Redis: ✅ Running and healthy
- phpMyAdmin: ✅ Accessible and functional
- Language Support: ✅ Persian and English implemented
- Telegram Bot: ✅ Responding to commands and messages

Known Issues:
- Test coverage needs to be implemented
- Documentation needs to be updated
- 3x-ui panel integration needs to be completed beyond basic connectivity test
- Comprehensive database schema needs full implementation

Next Steps:
1. Complete database model updates and create new models [ID-004]
   - Update Location model with new fields (default_inbound_id, protocols_supported, etc.)
   - Create plan_categories and plans models
   - Create client_id_sequences model for automated client ID generation
   - Create client model with proper relationships
   - Create remaining models (orders, transactions, payments, etc.)
   - Create Alembic migration for all new models and changes
   - Run migration and verify database structure

2. Complete 3x-ui panel connection implementation [ID-007]
   - Implement comprehensive API client for all 3x-ui endpoints
   - Create secure credential storage system
   - Implement panel health checking system
   - Create PanelService for managing multiple panels
   - Add API endpoints for panel management

3. Set up test framework and implement tests [ID-013]
   - Create pytest configuration
   - Set up test database fixtures
   - Implement unit tests for models and services
   - Add integration tests for API endpoints
   - Set up CI pipeline for automated testing

4. Implement notification channel system [ID-011]
   - Create NotificationManager class
   - Implement support for different channel types
   - Create templates for various notification types
   - Add callback handlers for interactive buttons

5. Create moonvpn command [ID-008]
   - Implement basic script for Docker management
   - Add commands for common operations (start, stop, status)
   - Create installation and update procedures
   - Add backup and restore functionality

# Tasks

## Core Infrastructure Tasks

[ID-001] Setup project directory structure based on project-requirements.md
Status: [X] Priority: High
Dependencies: None
Requirements Reference: project-requirements.md#2-Core-Technologies-&-Architecture
Expected Completion: Completed
Testing Requirements:
- Unit tests required: No
- Integration tests required: No
- E2E tests required: No
Documentation Requirements:
- API documentation needed: No
- User guide updates needed: No
- System architecture updates needed: Yes
Progress Notes:
- [v0.0.1] Initial task definition.
- [v0.0.2] Directory structure confirmed against project-requirements.md.

[ID-002] Initialize FastAPI application skeleton (`api/main.py`, basic structure)
Status: [X] Priority: High
Dependencies: ID-001, ID-009, ID-010
Requirements Reference: project-requirements.md#2-Core-Technologies-&-Architecture
Expected Completion: Completed
Testing Requirements:
- Unit tests required: Yes
- Integration tests required: No
- E2E tests required: No
Documentation Requirements:
- API documentation needed: Yes (Basic Swagger/ReDoc)
- User guide updates needed: No
- System architecture updates needed: No
Progress Notes:
- [v0.0.3] Starting implementation.
- [v0.0.4] Implemented basic app, logging setup, and /ping endpoint.

[ID-003] Initialize Telegram Bot skeleton (`bot/main.py`, basic `/start` handler)
Status: [X] Priority: High
Dependencies: ID-001, ID-009
Requirements Reference: project-requirements.md#3.2-Telegram-Bot-Interface
Expected Completion: Completed
Testing Requirements:
- Unit tests required: Yes
- Integration tests required: No
- E2E tests required: Yes
Documentation Requirements:
- API documentation needed: No
- User guide updates needed: Yes
- System architecture updates needed: No
Progress Notes:
- [v0.0.1] Initial task definition.
- [v0.0.4] Implemented basic polling bot with /start, /help, echo handlers and sample keyboard.

[ID-004] Define core Database Models (`api/models.py`) & Setup Alembic
Status: [X] Priority: High
Dependencies: ID-001, ID-009
Requirements Reference: project-requirements.md#2-Core-Technologies-&-Architecture
Expected Completion: Completed
Testing Requirements:
- Unit tests required: Yes
- Integration tests required: Yes
- E2E tests required: No
Documentation Requirements:
- API documentation needed: Yes
- User guide updates needed: No
- System architecture updates needed: Yes
Progress Notes:
- [v0.0.1] Initial task definition.
- [v0.0.6] Initial models created: User, Role, Panel, Location
- [v0.0.6] Remaining models need to be implemented in next phase: Plan, Client, Transaction, Payment, BankCard, NotificationChannel
- [v0.0.7] Database schema reviewed and updated according to the latest requirements
- [v0.0.7] Need to update Location model with new fields: default_inbound_id, protocols_supported, inbound_tag_pattern, default_remark_prefix

Tasks still needed for ID-004:
1. Update Location model with the following fields:
   - default_inbound_id: INT NULL
   - protocols_supported: VARCHAR(100) NULL
   - inbound_tag_pattern: VARCHAR(100) NULL
   - default_remark_prefix: VARCHAR(50) NULL

2. Create new models based on updated schema:
   - Plan model with new fields (features, category_id, sorting_order)
   - PlanCategory model
   - Client model with updated fields (location_id, uuid/client_uuid, remark, config_json, subscription_url)
   - ClientIdSequence model for sequential client ID management
   - Transaction model
   - Payment model
   - Order model
   - BankCard model
   - NotificationChannel model
   - Settings model with 'group' field
   - (Future) DiscountCode model
   - (Future) UserDevice model
   - (Future) AuditLog model

3. Update relationships between models:
   - Connect Location to ClientIdSequence
   - Connect Plan to PlanCategory
   - Connect Client to Location
   - Add proper indexing to improve query performance
   - Ensure all foreign key relationships are properly defined

4. Create Alembic migration script for the new models and changes to existing models

[ID-005] Create .env.example with comprehensive configuration options
Status: [X] Priority: High
Dependencies: ID-001
Requirements Reference: project-requirements.md#2-Core-Technologies-&-Architecture
Expected Completion: Completed
Testing Requirements:
- Unit tests required: No
- Integration tests required: No
- E2E tests required: No
Documentation Requirements:
- API documentation needed: No
- User guide updates needed: Yes
- System architecture updates needed: No
Progress Notes:
- [v0.0.2] Initial task definition.
- [v0.0.3] Enhanced .env.example with comprehensive settings, Persian translations, and improved organization.
- [v0.0.3] Added new configuration options for Redis, CORS, rate limiting, monitoring, and system limits.
- [v0.0.3] Added detailed bilingual comments and emojis for better readability.

[ID-006] Setup Docker environment (Dockerfile & docker-compose.yml)
Status: [X] Priority: High
Dependencies: ID-001, ID-005
Requirements Reference: project-requirements.md#2-Core-Technologies-&-Architecture
Expected Completion: Completed
Testing Requirements:
- Unit tests required: No
- Integration tests required: Yes
- E2E tests required: Yes
Documentation Requirements:
- API documentation needed: No
- User guide updates needed: Yes
- System architecture updates needed: Yes
Progress Notes:
- [v0.0.2] Initial task definition.
- [v0.0.3] Setup Docker with API, Bot, MySQL, Redis, and phpMyAdmin services.
- [v0.0.4] Fixed database configuration and access issues.
- [v0.0.4] Implemented proper health checks for all services.
- [v0.0.4] Fixed bot container health check using httpx.
- [v0.0.4] All services now running in healthy state.

[ID-007] Implement 3x-ui panel connection system
Status: [ ] Priority: High
Dependencies: ID-002
Requirements Reference: project-requirements.md#3.1-Panel-Management
Expected Completion: In progress
Testing Requirements:
- Unit tests required: Yes
- Integration tests required: Yes
- E2E tests required: No
Documentation Requirements:
- API documentation needed: Yes
- User guide updates needed: No
- System architecture updates needed: No
Progress Notes:
- [v0.0.2] Initial task definition.
- [v0.0.6] Basic panel connection client implemented in integrations/panels/client.py
- [v0.0.6] Added API endpoints for testing panel connection
- [v0.0.6] Implemented test script for panel connection
- [v0.0.6] Comprehensive tests created for unit and integration testing

Next Steps for ID-007:
- Implement complete API client for 3x-ui with all available endpoints
- Create a PanelService for managing multiple panels
- Implement panel health checking system
- Add support for inbound and client management
- Implement secure credential storage with encryption
- Develop panel selection algorithm based on load and geographical location
- Create scheduled health checks (5-15 minute intervals)
- Add failover mechanism for client migration between panels

API Endpoints to Implement:
- GET `/list` - Get all inbounds
- GET `/get/:id` - Get inbound with ID
- GET `/getClientTraffics/:email` - Get client traffic by email
- POST `/add` - Add new inbound
- POST `/addClient` - Add client to inbound
- POST `/:id/delClient/:clientId` - Delete client by ID
- POST `/updateClient/:clientId` - Update client by ID
- POST `/:id/resetClientTraffic/:email` - Reset client's traffic
- POST `/resetAllTraffics` - Reset all traffic for all inbounds
- POST `/resetAllClientTraffics/:id` - Reset all clients' traffic in an inbound
- POST `/delDepletedClients/:id` - Delete depleted clients

[ID-008] Create moonvpn command concept (basic script for Docker management)
Status: [ ] Priority: Medium
Dependencies: ID-006
Requirements Reference: project-requirements.md#2-Core-Technologies-&-Architecture
Expected Completion: TBD
Testing Requirements:
- Unit tests required: No
- Integration tests required: Yes
- E2E tests required: Yes
Documentation Requirements:
- API documentation needed: No
- User guide updates needed: Yes
- System architecture updates needed: No
Progress Notes:
- [v0.0.2] Initial task definition.

[ID-009] Implement core/config.py & core/database.py
Status: [X] Priority: High
Dependencies: ID-001
Requirements Reference: project-requirements.md#2-Core-Technologies-&-Architecture
Expected Completion: Completed
Testing Requirements:
- Unit tests required: Yes
- Integration tests required: Yes
- E2E tests required: No
Documentation Requirements:
- API documentation needed: No
- User guide updates needed: No
- System architecture updates needed: Yes
Progress Notes:
- [v0.0.2] Initial task definition.
- [v0.0.3] Enhanced config.py with comprehensive settings, environment validation, and Persian comments.
- [v0.0.3] Added new configuration options for Redis, CORS, rate limiting, monitoring, and system limits.
- [v0.0.3] Updated database.py with optimized connection handling, Redis integration, and utility functions.
- [v0.0.3] Added MySQL event listeners for timezone and strict mode.
- [v0.0.3] Implemented connection health checks and proper error handling.

[ID-010] Persian language support
Status: [X] Priority: High
Dependencies: ID-001, ID-002, ID-003
Requirements Reference: project-requirements.md#3-User-Interface-&-Experience
Expected Completion: Completed
Testing Requirements:
- Unit tests required: Yes
- Integration tests required: Yes
- E2E tests required: Yes
Documentation Requirements:
- API documentation needed: No
- User guide updates needed: Yes
- System architecture updates needed: Yes
Progress Notes:
- [v0.0.4] Initial task definition.
- [v0.0.4] Created i18n module for handling translations.
- [v0.0.4] Added language selection command and handlers.
- [v0.0.4] Added language preference to user model.
- [v0.0.4] Created Persian and English translation files.
- [v0.0.4] Added language selection button to main menu.
- [v0.0.4] Updated bot's response system to support multiple languages.
- [v0.0.5] Tested Persian language support with live bot - working correctly.
- [v0.0.5] Verified message delivery and Persian text rendering.
- [v0.0.5] Confirmed bot health check and service stability.

[ID-011] Setup basic notification channel system (bot/channels.py)
Status: [ ] Priority: Medium
Dependencies: ID-003
Requirements Reference: project-requirements.md#3.3-Channel-Based-Notification-System
Expected Completion: TBD
Testing Requirements:
- Unit tests required: Yes
- Integration tests required: Yes
- E2E tests required: Yes
Documentation Requirements:
- API documentation needed: No
- User guide updates needed: Yes
- System architecture updates needed: No
Progress Notes:
- [v0.0.2] Initial task definition.

[ID-012] Setup core logging system (core/logging.py)
Status: [X] Priority: High
Dependencies: ID-002, ID-003
Requirements Reference: project-requirements.md#2-Core-Technologies-&-Architecture
Expected Completion: Completed
Testing Requirements:
- Unit tests required: Yes
- Integration tests required: No
- E2E tests required: No
Documentation Requirements:
- API documentation needed: No
- User guide updates needed: No
- System architecture updates needed: Yes
Progress Notes:
- [v0.0.2] Initial task definition.
- [v0.0.3] Completed comprehensive logging system with multiple handlers, colored console output, rotating file logs, Telegram channel integration for critical errors, environment-specific log directories, and proper log filtering for third-party libraries.
- [v0.0.3] Added utility functions for easy logger access.

[ID-013] Create initial test framework setup
Status: [ ] Priority: High
Dependencies: ID-002, ID-003, ID-004
Requirements Reference: project-requirements.md#6-Testing-Strategy
Expected Completion: TBD
Testing Requirements:
- Unit tests required: N/A
- Integration tests required: N/A
- E2E tests required: N/A
Documentation Requirements:
- API documentation needed: No
- User guide updates needed: No
- System architecture updates needed: Yes
Progress Notes:
- [v0.0.2] Initial task definition.

[ID-004-1] Update existing database models with new fields
Status: [ ] Priority: High
Dependencies: ID-004
Requirements Reference: project-requirements.md#8-Database-Schema
Expected Completion: TBD
Testing Requirements:
- Unit tests required: Yes
- Integration tests required: Yes
- E2E tests required: No
Documentation Requirements:
- API documentation needed: Yes
- User guide updates needed: No
- System architecture updates needed: Yes
Progress Notes:
- [v0.0.7] Task created following project-requirements.md review and database schema update
- [v0.0.7] Need to update Location model with additional fields for inbound management
- [v0.0.7] Need to update Panel model by removing redundant fields

Implementation Plan:
1. Update Location model to add new fields:
   ```python
   # Add to Location model
   default_inbound_id = Column(Integer, nullable=True)
   protocols_supported = Column(String(100), nullable=True)  # comma-separated list
   inbound_tag_pattern = Column(String(100), nullable=True)
   default_remark_prefix = Column(String(50), nullable=True)
   ```

2. Update Panel model to remove unused fields:
   ```python
   # Remove from Panel model
   # max_clients = Column(Integer, default=0)
   # current_clients = Column(Integer, default=0)
   ```

3. Create Alembic migration script for these changes:
   ```bash
   alembic revision --autogenerate -m "Update Location model with inbound fields, modify Panel model"
   ```

4. Run the migration:
   ```bash
   alembic upgrade head
   ```

5. Update relevant API schemas and service methods

[ID-004-2] Create new database models for core functionality
Status: [ ] Priority: High
Dependencies: ID-004, ID-004-1
Requirements Reference: project-requirements.md#8-Database-Schema
Expected Completion: TBD
Testing Requirements:
- Unit tests required: Yes
- Integration tests required: Yes
- E2E tests required: No
Documentation Requirements:
- API documentation needed: Yes
- User guide updates needed: No
- System architecture updates needed: Yes
Progress Notes:
- [v0.0.7] Task created following project-requirements.md review and database schema update
- [v0.0.7] Need to implement all models required for Phase 1 & 2

Implementation Plan:
1. Create models in priority order:
   - PlanCategory model
   - Plan model (with relationship to PlanCategory)
   - ClientIdSequence model (with relationship to Location)
   - Client model (with relationships to User, Panel, Location, Plan, Order)
   - Order model
   - Transaction model
   - Payment model
   - BankCard model
   - NotificationChannel model
   - Settings model

2. Define all relationships between models

3. Create Alembic migration script for new models:
   ```bash
   alembic revision --autogenerate -m "Add core models for plans, clients, payments and settings"
   ```

4. Run the migration:
   ```bash
   alembic upgrade head
   ```

5. Create initial data seed scripts for essential data (roles, settings)

# Detailed Database Schema

Based on project requirements and the latest updates in `project-requirements.md`, the following comprehensive database schema needs to be implemented. Existing models need updates, and new models must be created.

## Core Tables:

### 1. users (Partially Implemented)
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

Enhancements needed:
- Add proper indexing
- Add relationship to referred_by (self-referential) - Already implemented
- Implement secure password handling if needed

### 2. roles (Implemented)
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

Enhancements needed:
- Add `is_admin` and `is_seller` fields
- Implement comprehensive permission model

### 3. panels (Implemented with changes needed)
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

Enhancements needed:
- Remove `max_clients` and `current_clients` fields
- Implement encryption for password field
- Add relationship to location and users (already done)

### 4. locations (Implemented with changes needed)
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

Enhancements needed:
- Add new fields: default_inbound_id, protocols_supported, inbound_tag_pattern, default_remark_prefix
- Add relationship to panels (already done)
- Add relationship to ClientIdSequence

### 5. plans (To Be Implemented)
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

### 6. plan_categories (To Be Implemented)
- `id`: INT PRIMARY KEY AUTO_INCREMENT
- `name`: VARCHAR(100)
- `description`: TEXT NULL
- `sorting_order`: INT DEFAULT 0
- `is_active`: BOOLEAN DEFAULT TRUE
- `created_at`: DATETIME
- `updated_at`: DATETIME

### 7. clients (To Be Implemented)
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

### 8. client_id_sequences (To Be Implemented)
- `id`: INT PRIMARY KEY AUTO_INCREMENT
- `location_id`: INT FOREIGN KEY
- `last_id`: INT DEFAULT 0
- `prefix`: VARCHAR(20) NULL
- `created_at`: DATETIME
- `updated_at`: DATETIME

### 9. orders (To Be Implemented)
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

### 10. transactions (To Be Implemented)
- `id`: INT PRIMARY KEY AUTO_INCREMENT
- `user_id`: INT FOREIGN KEY
- `amount`: DECIMAL(10,2)
- `type`: VARCHAR(20)  # deposit, withdraw, purchase, refund, commission
- `reference_id`: INT NULL  # Reference to payment_id or order_id
- `description`: TEXT NULL
- `balance_after`: DECIMAL(10,2)
- `created_at`: DATETIME

### 11. payments (To Be Implemented)
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

### 12. bank_cards (To Be Implemented)
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

### 13. notification_channels (To Be Implemented)
- `id`: INT PRIMARY KEY AUTO_INCREMENT
- `name`: VARCHAR(100)  # admin, payment, report, log, alert, backup
- `channel_id`: VARCHAR(100)
- `description`: TEXT NULL
- `notification_types`: TEXT NULL  # JSON array of notification types
- `is_active`: BOOLEAN DEFAULT TRUE
- `created_at`: DATETIME
- `updated_at`: DATETIME

### 14. settings (To Be Implemented)
- `id`: INT PRIMARY KEY AUTO_INCREMENT
- `key`: VARCHAR(100) UNIQUE
- `value`: TEXT
- `description`: TEXT NULL
- `is_public`: BOOLEAN DEFAULT FALSE
- `created_at`: DATETIME
- `updated_at`: DATETIME

### 15. discount_codes (To Be Implemented - Future Phase)
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

### 16. user_devices (To Be Implemented - Future Phase)
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

### 17. audit_logs (To Be Implemented - Future Phase)
- `id`: INT PRIMARY KEY AUTO_INCREMENT
- `user_id`: INT NULL FOREIGN KEY
- `action`: VARCHAR(100)
- `entity_type`: VARCHAR(50)
- `entity_id`: INT NULL
- `details`: TEXT NULL  # JSON with details
- `ip_address`: VARCHAR(45)
- `created_at`: DATETIME

# Detailed 3x-ui Panel API Integration

Based on the 3x-ui panel documentation (https://github.com/MHSanaei/3x-ui), the following API endpoints should be implemented for full panel integration:

## Authentication
- `/login` - Login to the panel (POST)

## Inbound Management
- `/panel/api/inbounds/list` - Get all inbounds (GET)
- `/panel/api/inbounds/get/:id` - Get specific inbound by ID (GET)
- `/panel/api/inbounds/add` - Create new inbound (POST)
- `/panel/api/inbounds/update/:id` - Update existing inbound (POST)
- `/panel/api/inbounds/del/:id` - Delete inbound (POST)

## Client Management
- `/panel/api/inbounds/addClient` - Add client to inbound (POST)
- `/panel/api/inbounds/:id/delClient/:clientId` - Delete client (POST)
- `/panel/api/inbounds/updateClient/:clientId` - Update client (POST)

## Traffic Management
- `/panel/api/inbounds/getClientTraffics/:email` - Get client traffic by email (GET)
- `/panel/api/inbounds/getClientTrafficsById/:id` - Get client traffic by ID (GET)
- `/panel/api/inbounds/:id/resetClientTraffic/:email` - Reset client's traffic (POST)
- `/panel/api/inbounds/resetAllTraffics` - Reset all traffic (POST)
- `/panel/api/inbounds/resetAllClientTraffics/:id` - Reset all client traffic in inbound (POST)

## System Operations
- `/panel/api/inbounds/createbackup` - Create backup (GET)
- `/panel/api/inbounds/delDepletedClients/:id` - Delete depleted clients (POST)
- `/panel/api/inbounds/onlines` - Get online users (POST)

## Implementation Approach for ID-007

For complete implementation of the 3x-ui panel connection system:

1. **Create a comprehensive API client**:
   - Base client for authentication and session management
   - Method implementations for all API endpoints
   - Proper error handling and retry logic
   - Connection pooling and timeout handling
   - Response parsing and data conversion

2. **Create a PanelService**:
   - Management of multiple panel instances
   - CRUD operations for panels in database
   - Secure credential storage with encryption
   - Health monitoring system
   - Load balancing and client allocation logic
   - Failover mechanisms for panel failure scenarios

3. **Implement health checking system**:
   - Scheduled health checks (5-15 minute intervals)
   - Status tracking and history
   - Notification system for panel issues
   - Automatic recovery attempts

4. **Create API endpoints for panel management**:
   - Panel testing and connection verification
   - Panel CRUD operations
   - Health status queries
   - Statistics and metrics endpoints
   - Client management operations

This implementation will provide a robust foundation for all panel-related operations in future phases of the project.

## Core Requirements Tracking

### Persian Language Implementation
- [ ] Define Persian message templates and format standards
- [ ] Create emoji usage guidelines for user-facing messages
- [ ] Implement localization infrastructure in bot module
- [ ] Create Persian language test suite
- [ ] Document Persian language standards for developers

### Testing Framework
- [ ] Setup pytest environment for unit testing
- [ ] Create test data fixtures for common scenarios
- [ ] Define integration test approaches
- [ ] Setup E2E test procedures for Telegram bot
- [ ] Define minimum test coverage requirements

# Quality Assurance Checklist

For each completed task:
- [ ] Code follows Python best practices (PEP 8)
- [ ] Required tests implemented and passing
- [ ] Documentation updated as needed
- [ ] Persian language support implemented (if user-facing)
- [ ] Security best practices followed (no hardcoded credentials, proper error handling)
- [ ] Performance meets requirements
- [ ] Commits use descriptive messages

# Milestone 1 Testing Plan

After completing tasks [ID-001] through [ID-006]:
- [ ] Verify Docker environment starts correctly
- [ ] Ensure FastAPI responds to basic requests
- [ ] Confirm database connects and migrations work
- [ ] Test Telegram bot basic commands function
- [ ] Verify logging system captures events correctly

# Milestone 2 Testing Plan

After completing tasks [ID-007] through [ID-013]:
- [ ] Test 3x-ui panel connection functionality
- [ ] Verify Persian language support works in bot
- [ ] Ensure notification channels function correctly
- [ ] Test command-line utility (moonvpn)
- [ ] Run all unit and integration tests

# Developer Notes
- Persian language support is critical for all user-facing components
- Each task should be testable independently when possible
- Docker setup needs to support dev, test, and prod environments
- Focus on creating modular, reusable components
- Encrypt sensitive data (panel credentials) in database
- Implement proper error handling for all external API calls
- Design with scalability in mind - the system should support multiple panels
- Follow best security practices for all authentication flows
- Design APIs with OpenAPI documentation in mind

## Notes
- Remember to update CHANGELOG.md for each significant change
- Keep documentation up to date with implementation
- Follow Persian language guidelines for user-facing messages
- Ensure proper error handling and logging throughout
- Consider rate limiting for API and bot endpoints
- Plan for scalability in database design
- Keep security best practices in mind

## Questions
- Should we implement caching at the API level?
- What metrics should we collect for monitoring?
- Should we add support for multiple payment gateways?
- What is the expected scale of the system (number of users, panels, traffic)?
- Should we implement a more comprehensive role-based access control system?

## Dependencies
- Python 3.9+
- FastAPI
- SQLAlchemy
- python-telegram-bot
- Redis
- MySQL
- Docker & Docker Compose
- httpx (for API client)

## SQL Models Implementation Plan

For completing task [ID-004], we need to:

1. **Update existing models**:
   - Update Location model to add new fields:
     ```python
     # Add to Location model
     default_inbound_id = Column(Integer, nullable=True)
     protocols_supported = Column(String(100), nullable=True)  # comma-separated list
     inbound_tag_pattern = Column(String(100), nullable=True)
     default_remark_prefix = Column(String(50), nullable=True)
     ```
   
   - Update Panel model to remove unused fields:
     ```python
     # Remove from Panel model
     # max_clients = Column(Integer, default=0)
     # current_clients = Column(Integer, default=0)
     ```

2. **Create new models** (in priority order):
   - PlanCategory model
   - Plan model (with relationship to PlanCategory)
   - ClientIdSequence model (with relationship to Location)
   - Client model (with relationships to User, Panel, Location, Plan, Order)
   - Order model
   - Transaction model
   - Payment model
   - BankCard model
   - NotificationChannel model
   - Settings model
   - (Future) DiscountCode model
   - (Future) UserDevice model
   - (Future) AuditLog model

3. **Create Alembic migration**:
   - Update existing models
   - Add new models
   - Set up initial roles and settings

This implementation will fulfill the requirements specified in the project-requirements.md document for Phase 0 and prepare for Phase 1 & 2.