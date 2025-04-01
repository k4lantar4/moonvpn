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

# Mode: Implementation ⚡ (Confidence: 94% - Minor uncertainties on SSH/Auto-Pay specifics)
Current Phase: PHASE-3
Mode Context: Implementation Type - New Project Setup
Status: Active
Last Updated: [v1.6.0]

## Project: MoonVPN System

### Core Technologies:
- **Core API:** FastAPI (Python)
- **Telegram Bot:** python-telegram-bot (Python)
- **Database:** MySQL with SQLAlchemy ORM
- **Dashboard Frontend:** FastAPI Templates with Tabler UI Kit
- **Installation:** Bash script (`moonvpn` command) for Ubuntu 22

### Project Structure (Mono-repo):
```
moonvpn/
├── core_api/         # FastAPI Backend (API & Dashboard Logic)
├── telegram_bot/     # Telegram Bot Logic
├── dashboard_frontend/ # (Likely integrated in core_api templates)
├── scripts/          # Installation & Helper Scripts (install.sh -> moonvpn)
├── docs/             # Project Documentation
├── .gitignore
└── README.md
```

### Key Features Summary:
- V2Ray (Vmess/Vless) account sales & management (initially 3x-ui panel).
- Telegram Bot as primary user & admin interface (including detailed admin menus).
- Web Dashboard (Tabler UI) for comprehensive management.
- Payment: Manual Card-to-Card (Admin verification via dedicated TG groups), Zarinpal, Internal Wallet.
- Seller/Reseller System (Automatic upgrade based on wallet top-up, custom pricing/limits).
- Free Trial for verified Iranian users (+98 & channel join).
- Advanced Management via dedicated Telegram Groups (MANAGE, REPORTS, LOGS, TRANSACTIONS, OUTAGES, SELLERS, BACKUPS).
- User Subscription Features: Freeze, User Notes, Change Protocol/Location, Auto-Renew toggle.
- Affiliate/Referral System.
- Free Proxy Configuration (via Bot/Dashboard).
- Advanced Server Actions via SSH (Reboot, Restart Xray) - Requires secure credential handling.
- Detailed Admin Roles & Permissions Management (via Bot/Dashboard).
- `moonvpn` command-line installation script for easy setup.

## Execution Plan (Updated based on v0.1.7):

### Phase-0: Setup & Infrastructure (COMPLETED)
**Goal:** Prepare project structure, detailed database schema, basic API/Bot setup, and installation script.
**Tasks:**
- [X] [P0-T001] Define detailed Database Schema (MySQL) - Incorporating new tables/fields (Locations, Settings, Roles, Affiliate, User Notes, Freeze, etc.). Status: [X] Priority: High
- [X] [P0-T002] Setup Mono-repo project structure locally. Status: [X] Priority: High
- [X] [P0-T003] Initialize Core API (FastAPI) project: basic setup, DB connection (SQLAlchemy). Status: [X] Priority: Medium
- [X] [P0-T004] Initialize Telegram Bot (python-telegram-bot) project: basic setup, API token config. Status: [X] Priority: Medium
- [X] [P0-T005] Create initial `scripts/install.sh` structure. Status: [X] Priority: Low
- [X] [P0-T006] Select & integrate Tabler UI template basics into FastAPI. Status: [X] Priority: Medium
- [X] [P0-T007] Create initial `README.md` and `.gitignore`. Status: [X] Priority: Low

### Phase-1: Core Bot, User Registration & Roles (COMPLETED)
**Goal:** Implement basic bot functions, user registration/verification, and basic Admin Role/Permission structure.
**Tasks:**
- [X] [P1-T001] Core API: User management endpoints (register, get info, update role). Status: [X] Priority: High
- [X] [P1-T002] Core API: Basic Plan, Panel, Location CRUD endpoints. Status: [X] Priority: Medium
- [X] [P1-T003] Core API: Implement basic Roles & Permissions structure (e.g., CRUD for Roles, Permissions, Role-Permission mapping). Status: [X] Priority: High
- [X] [P1-T004] Telegram Bot: `/start` command, registration flow (+98 check, channel join check via API). Status: [X] Priority: High
  Progress Notes:
  - [v0.1.3] Implemented /start handler, contact handler, API calls for user check/registration, +98 phone validation, and channel membership check.
- [X] [P1-T005] Telegram Bot: Display main menu & plans (fetched via API). Status: [X] Priority: Medium
  Progress Notes:
  - [v0.1.4] Added get_active_plans to API client. Created main menu keyboard and handler. Implemented show_main_menu and handle_buy_service (fetches plans, displays with inline buttons). Integrated menu into start handler. Registered buy service handler.
- [X] [P1-T006] Telegram Bot: Basic Wallet display. Status: [X] Priority: Low
- [X] [P1-T009] Dashboard: Basic Role/Permission management interface. Status: [X] Priority: Medium
- [X] [P1-T010] Install Script: Add Python, pip, MySQL installation steps. Status: [X] Priority: Low

### PHASE-2: Basic Purchase, Account Management & User Features (CURRENT PHASE)
**Goal:** Implement account creation, basic user management, and user-facing subscription features (Freeze, Notes, Auto-Renew).
**Tasks:**
- [X] [P2-T001] Core API: 3x-ui panel API integration (login, add user, get info, *modify user for protocol/location?*, *enable/disable user for freeze*). Status: [X] Priority: High
  Progress Notes:
  - [v0.1.7] Need to fix circular imports in schema modules before implementing this functionality.
- [X] [P2-T002] Core API: Order creation logic (link user, plan). Status: [X] Priority: Medium
  Progress Notes:
  - [v0.4.2] Implemented order creation logic using OrderService to properly validate inputs and use plan defaults when needed. Enhanced the OrderCreate schema and endpoint to better handle discount calculations. Updated the create_order endpoint to use the service for better validation.
- [X] [P2-T003] Core API: Endpoint to trigger account creation on panel. Status: [X] Priority: High
  Progress Notes:
  - [v0.4.2] Implemented comprehensive client creation on panel via the order service. Enhanced the OrderService.create_client_on_panel method to create a subscription after successful client creation on the panel, linking the order, subscription, and panel client together. Added proper fields to models and schemas, including subscription_id in Order model, client details in Subscription model, and appropriate relationships. Added error handling to ensure failures during subscription creation don't prevent client creation.
- [X] [P2-T004] Core API: Endpoints for fetching account details (link/QR, usage) from panel. Status: [X] Priority: Medium
  Progress Notes:
  - [v0.4.1] Implemented endpoints to retrieve client configuration and QR codes through the subscription service. Created three new endpoints:
    - GET /subscriptions/{id}/config - Returns detailed connection information
    - GET /subscriptions/{id}/qrcode - Returns QR code for easy mobile setup
    - GET /subscriptions/{id}/traffic - Returns traffic usage statistics
    These endpoints integrate with the PanelService to fetch real-time data from the VPN panel while ensuring proper authorization checks (users can only access their own configurations).
- [X] [P2-T005] Core API: Logic for Freeze/Unfreeze, User Notes, Auto-Renew setting on Subscription. Status: [X] Priority: Medium
- [X] [P2-T006] Core API: Logic for Change Protocol/Location (if feasible via 3x-ui API or needs alternative). Status: [X] Priority: Medium
- [X] [P2-T007] Telegram Bot: Purchase flow (select plan, create order via API). Status: [X] Priority: High
  Progress Notes:
  - [v0.4.5] Implemented purchase flow including selecting plans, choosing payment methods, creating orders, handling card-to-card payments with receipt upload, and simulating admin approval flow for payments.
- [X] [P2-T008] Telegram Bot: "My Account" section (list accounts, get details, Freeze/Unfreeze, Add Note, Toggle Auto-Renew, Change Protocol/Location options via API). Status: [X] Priority: High
  Progress Notes:
  - [v0.4.6] Implemented comprehensive "My Accounts" section in the Telegram bot with functionality to list and manage user subscriptions. Created API client functions for all subscription operations including get_user_subscriptions, get_subscription_details, get_subscription_qrcode, get_subscription_traffic, and various management functions. Added account listing and detailed view showing subscription status, expiry date, protocol, and other details. Implemented traffic usage visualization with text-based progress bar. Added management features including freeze/unfreeze, note addition, auto-renewal toggling, and protocol/location changing. Used ConversationHandler pattern with clear state management for complex user flow.
- [X] [P2-T009] Telegram Bot: Simulate payment confirmation to trigger account creation. Status: [X] Priority: Medium
  Progress Notes:
  - [v0.4.7] Implemented integration between payment confirmation in Telegram bot and the backend API for automatic account creation. Enhanced the payment confirmation process by adding API functions confirm_order_payment and reject_order_payment that invoke the core API's create-client endpoint. Updated the admin payment confirmation handler to handle both successful and failed API responses, showing detailed subscription information to users upon successful account creation and providing appropriate error notifications when issues occur. The implementation ensures that order status tracking is maintained throughout the process and orders can be manually processed if automatic creation fails.
- [X] [P2-T010] Dashboard: Display user's V2Ray accounts and details (including new features). Status: [X] Priority: Medium
- [X] [P2-T011] Install Script: Add database setup steps. Status: [X] Priority: Low

### PHASE-3: Card-to-Card Payment & Admin Verification
**Goal:** Implement the manual payment flow with Telegram group verification.
**Tasks:**
- [X] [P3-T001] Core API: Manage Bank Cards (CRUD). Status: [X] Priority: High
  Progress Notes:
  - [v1.5.0] Implemented comprehensive bank card management functionality including model, schema, CRUD operations, and API endpoints. Created a migration script for the bank_cards table. Added full Telegram bot support with admin handlers for card listing, creation, detailed viewing, status toggling, priority management, and deletion. Implementation follows security best practices for handling sensitive financial information.
- [X] [P3-T002] Core API: Manage Payment Admins & assign to cards/groups (link to Roles/Permissions). Status: [X] Priority: High
  Progress Notes:
  - [v1.6.0] Implemented comprehensive payment admin management system with database models (PaymentAdminAssignment, PaymentAdminMetrics), migration script, service layer (PaymentAdminService), and API endpoints. Created functionality for creating/updating assignments, tracking metrics, and selecting appropriate admins for payment verification using a load-balancing algorithm. Added specialized endpoints for recording processed payments and generating performance statistics. Implementation includes features for assigning specific admins to verify payments for particular bank cards and receive notifications in designated Telegram groups.
- [X] [P3-T003] Core API: Endpoints for submitting payment proof & updating order status (pending, approved, rejected). Status: [X] Priority: High
  Progress Notes:
  - [v1.7.0] Implemented comprehensive payment proof submission and verification system.
- [X] [P3-T004] Core API: Logic for rotating bank cards display. Status: [X] Priority: Medium
  Progress Notes:
  - [v1.5.0] Implemented bank card rotation logic in `get_next_active_card` method of CRUDBankCard class and `get_next_bank_card_for_payment` in BankCardService. The logic intelligently selects cards based on priority groups and rotation within the same priority to distribute payment load evenly. Added API endpoint `/bank-cards/next-for-payment` and appropriate API client method in the Telegram bot to fetch the next card for payment processing.
- [X] [P3-T005] Core API: Generate reports on payment admin performance. Status: [X] Priority: Medium
  Progress Notes:
  - [v1.9.0] Implemented comprehensive payment admin performance reporting system:
    - Created detailed schemas for PaymentAdminPerformanceMetrics, PaymentAdminReportData, and PaymentAdminReportResponse
    - Added generate_performance_reports method to PaymentAdminService that calculates:
      - Total processed/approved/rejected payments for each admin
      - Average response times and approval rates
      - Distribution of rejection reasons and bank cards
      - Daily/weekly/monthly processing statistics
    - Added API endpoint at /payment-admins/reports with filtering by dates and admin_id
    - Implemented Telegram bot reporting with command /reports showing both text reports and visual charts
    - Added matplotlib visualization of admin performance metrics with comparative charts
    - Created flexible date range filtering (today, current week, current month, all time)
- [X] [P3-T006] Telegram Bot: Implement card-to-card payment flow (display card, timer, upload proof). Status: [X] Priority: High
  Progress Notes:
  - [v1.8.0] Implemented comprehensive card-to-card payment flow in the Telegram bot:
    - Created `payment_proof_handlers.py` with conversation handlers for the payment process
    - Added bank card selection interface that displays available cards from the Core API
    - Implemented payment timer with 15-minute expiration and automatic cleanup
    - Added payment proof image upload with validation and processing
    - Implemented reference/tracking number collection and validation
    - Created secure image processing to send photos to the Core API
    - Added API client function for submitting payment proofs using FormData
    - Integrated with buy_flow handlers to properly handle payment method selection
    - Added proper error handling, cancellation options, and user notifications throughout the flow
    - Created helpful payment instructions and confirmations in Persian
- [X] [P3-T007] Telegram Bot: Send proof notification to specific TG group (based on card) with Approve/Reject buttons. Status: [X] Priority: High
  Progress Notes:
    - [v1.11.0] Implemented a comprehensive payment notification system:
      - Created a new `payment_notification_handlers.py` module with dedicated functions for sending notifications to Telegram groups
      - Added functions to display payment details, card information, and user data in the notification messages
      - Implemented approve/reject buttons in the notification interface
      - Created a rejection system with predefined reasons and custom rejection option
      - Added proper permission checking to ensure only payment admins can approve/reject
      - Implemented user notifications for both approval and rejection events
      - Added support for tracking Telegram message IDs in the database
      - Created new API endpoints for updating message tracking information
      - Integrated the notification system with the payment proof submission workflow
      - Added Persian-language interface with emoji indicators for better readability
- [X] [P3-T008] Telegram Bot: Handle admin actions (Approve/Reject callback) in group, check permissions, update order via API, notify user. Status: [X] Priority: High
  Progress Notes:
    - [v1.11.0] Implemented admin action handling as part of the payment notification system:
      - Created callback handlers for approval (handle_payment_approve) and rejection (handle_payment_reject) buttons
      - Implemented permission checks using is_payment_admin function to ensure only authorized admins can process payments
      - Created a multi-stage rejection workflow with predefined reasons and custom reason input
      - Added API communication with confirm_order_payment and reject_order_payment endpoints
      - Implemented user notifications with subscription details upon approval or detailed rejection reasons
      - Added error handling and fallback mechanisms for API communication issues
      - Provided admin feedback with processing status and results of their actions
      - Ensured secure handling of order IDs and admin attribution in the database
- [X] [P3-T009] Telegram Bot: Admin commands (in MANAGE group?) to manage cards & payment admins. Status: [X] Priority: Medium
  Progress Notes:
    - [v1.12.0] Implemented comprehensive payment admin management in the Telegram bot:
      - Created `payment_admin_handlers.py` with conversation handler for managing payment admins
      - Added API client functions for all payment admin operations (create, read, update, delete)
      - Implemented user-friendly interfaces for adding, viewing, updating, and removing payment admins
      - Created specialized keyboards for selecting users, bank cards, and managing Telegram groups
      - Added proper permission checking with superuser-only access for sensitive operations
      - Implemented proper masking of sensitive card information in admin interfaces
      - Added two-step confirmation for payment admin deletion to prevent accidents
      - Implemented comprehensive error handling for all operations
      - Created Persian-language interface with emoji indicators for better readability
      - Integrated the payment admin management with the main admin menu
- [ ] [P3-T010] Dashboard: Sections for managing cards, payment admins, manual payment verification, admin performance reports. Status: [ ] Priority: High
- [ ] [P3-T011] Install Script: Add TG Bot token & group ID configurations. Status: [ ] Priority: Medium
- [ ] [P3-T012] Core API: Consider endpoint for *potential* future auto-card payment check (Low Priority). Status: [ ] Priority: Low

### PHASE-4: Seller System, Zarinpal & Affiliate
**Goal:** Implement reseller functionality, Zarinpal integration, and affiliate system.
**Tasks:**
- [ ] [P4-T001] Core API: Implement "Seller" role & different pricing logic/discounts. Status: [ ] Priority: High
- [ ] [P4-T002] Core API: Endpoint for automatic role upgrade based on wallet top-up. Status: [ ] Priority: Medium
- [ ] [P4-T003] Core API: Zarinpal API integration (request payment, verify). Status: [ ] Priority: High
- [ ] [P4-T004] Core API: Implement Affiliate system logic (referral tracking, commission calculation). Status: [ ] Priority: Medium
- [ ] [P4-T005] Telegram Bot: "Become a Seller" section & flow. Status: [ ] Priority: Medium
- [ ] [P4-T006] Telegram Bot: Display seller pricing. Status: [ ] Priority: Low
- [ ] [P4-T007] Telegram Bot: Add Zarinpal payment option. Status: [ ] Priority: Medium
- [ ] [P4-T008] Telegram Bot: Affiliate section for users (get referral link, view earnings). Status: [ ] Priority: Medium
- [ ] [P4-T009] Dashboard: Manage seller settings (upgrade amount, discount, limits), Zarinpal config. Status: [ ] Priority: Medium
- [ ] [P4-T010] Dashboard: Affiliate system settings & reporting. Status: [ ] Priority: Medium
- [ ] [P4-T011] Install Script: Add Nginx setup. Status: [ ] Priority: Medium

### PHASE-5: Advanced Dashboard, Management & SSH Actions
**Goal:** Implement remaining management features and advanced server actions via SSH.
**Tasks:**
- [ ] [P5-T001] Core API & Dashboard: Full Server/Panel management (add panel requires API test). Status: [ ] Priority: High
- [ ] [P5-T002] Core API & Dashboard: Full Service/Plan management (including category, max users). Status: [ ] Priority: High
- [ ] [P5-T003] Core API & Dashboard: Full User management (block, role change). Status: [ ] Priority: Medium
- [ ] [P5-T004] Core API & Dashboard: Discount code management (including target audience). Status: [ ] Priority: Medium
- [ ] [P5-T005] Core API & Dashboard: Financial reporting (Excel export). Status: [ ] Priority: High
- [ ] [P5-T006] Core API & Dashboard: Bulk messaging system. Status: [ ] Priority: Medium
- [ ] [P5-T007] Core API & Dashboard: Basic server monitoring display (Ping test?). Status: [ ] Priority: Low
- [ ] [P5-T008] Core API & Dashboard: Full Role-based access control implementation. Status: [ ] Priority: High
- [ ] [P5-T009] Core API & Dashboard: System settings configuration (Settings table). Status: [ ] Priority: Medium
- [ ] [P5-T010] Core API: Implement secure SSH connection handling (e.g., using Paramiko, storing credentials securely). Status: [ ] Priority: High
- [ ] [P5-T011] Core API & Bot/Dashboard: Implement SSH actions (Reboot Server, Restart Xray). Status: [ ] Priority: Medium
- [ ] [P5-T012] Core API & Bot/Dashboard: Implement Free Proxy configuration. Status: [ ] Priority: Low
- [ ] [P5-T013] Install Script: Add Certbot SSL setup. Status: [ ] Priority: High

### PHASE-6: Free Trial, Optimization & Extras
**Goal:** Add free trial, optimize performance, and add final touches.
**Tasks:**
- [ ] [P6-T001] Core API & Bot: Implement one-time free trial logic (assign specific plan). Status: [ ] Priority: Medium
- [ ] [P6-T002] Review & optimize code across all modules (API, Bot, DB queries). Status: [ ] Priority: Medium
- [ ] [P6-T003] Add comprehensive logging and error handling (using `activity_logs` table). Status: [ ] Priority: High
- [ ] [P6-T004] Finalize `moonvpn` installation script and test thoroughly. Status: [ ] Priority: High
- [ ] [P6-T005] Write basic project documentation (README, setup guide). Status: [ ] Priority: Medium
- [ ] [P6-T006] Consider future feature: Reseller-specific bots. Status: [ ] Priority: Low
- [ ] [P6-T007] Consider future feature: Auto Card Payment (if feasible/secure API found). Status: [ ] Priority: Low

# MoonVPN Core API Development Scratchpad

## Current Phase: P3 - Card-to-Card Payment & Admin Verification

### P3-T001: Bank Card Management (Completed)
**Status: [X] Complete**

This task focused on implementing a comprehensive bank card management system for handling card-to-card payments:

#### Completed Implementation:
- Created `BankCard` model with:
  - Essential card information fields: `card_number`, `sheba_number`, `bank_name`, `account_owner`
  - Management fields: `is_active`, `priority`, `notes`
  - Security fields for tracking ownership and usage
  
- Implemented `BankCardService` with methods:
  - CRUD operations for bank cards
  - Priority management for card rotation
  - Status toggling for enabling/disabling cards
  
- Created RESTful API endpoints:
  - GET `/bank-cards/` - List all bank cards with filtering options
  - GET `/bank-cards/{id}` - Get specific bank card details
  - POST `/bank-cards/` - Create a new bank card
  - PUT `/bank-cards/{id}` - Update a bank card
  - DELETE `/bank-cards/{id}` - Delete a bank card
  - PATCH `/bank-cards/{id}/toggle-status` - Enable/disable a bank card
  - PATCH `/bank-cards/{id}/priority` - Update card display priority

- Added Telegram Bot admin commands in the MANAGE group:
  - List all bank cards with status indicators
  - Add new bank cards with validation
  - View detailed card information
  - Toggle card active status
  - Manage card priority
  - Delete cards with confirmation

- Implemented data validation and security measures:
  - Card number format validation
  - SHEBA number validation
  - Proper permission checks for all operations
  - Secure handling of sensitive financial information

### P3-T002: Payment Admin Management (Completed)
**Status: [X] Complete**

This task focused on implementing a system for managing payment admins and their assignments to bank cards and Telegram groups:

#### Completed Implementation:
- Created database tables:
  - `payment_admin_assignments`: Tracks which admins are responsible for which cards/groups
  - `payment_admin_metrics`: Stores performance data for payment admins (response time, approval rate)
  
- Implemented `PaymentAdminService` with methods for:
  - Managing admin assignments (CRUD operations)
  - Tracking admin performance metrics
  - Selecting appropriate admins for payment verification using a load-balancing algorithm
  - Generating statistics on admin performance
  
- Created RESTful API endpoints:
  - GET/POST/PUT/DELETE for payment admin assignments
  - Endpoints for retrieving and updating metrics
  - Specialized endpoint for recording processed payments
  - Endpoint for selecting an appropriate admin for a new payment

- Added proper validation and security:
  - Validation of Telegram group IDs
  - Superuser-only access control
  - Proper error handling and logging
  
- Integrated with existing models:
  - Added relationships to User model
  - Connected to BankCard model for card assignments

### P3-T003: Payment Proof Submission (Completed)
**Status: [X] Completed**

This task focused on implementing a comprehensive payment proof submission and verification system:

#### Completed Implementation:
- Created database migration for enhanced Order fields:
  - `payment_proof_img_url`: Stores path to uploaded proof image
  - `payment_proof_submitted_at`: Tracks submission time
  - `payment_verified_at`: Records verification time
  - `payment_verification_admin_id`: Links to admin who verified
  - `payment_rejection_reason`: Stores reason for rejection if applicable
  - `payment_proof_telegram_msg_id`: For linking to Telegram messages
  
- Added new OrderStatus enum value:
  - `VERIFICATION_PENDING`: Indicates proof submitted but not yet verified
  
- Implemented FileStorageService for secure file handling:
  - Proper file validation (size, format)
  - Secure naming with UUID generation
  - Directory structure with proper permissions
  
- Enhanced OrderService with methods for:
  - `submit_payment_proof`: Process uploaded proof and update order status
  - `verify_payment_proof`: Approve/reject proof with admin attribution
  - Integration with PaymentAdminService for metrics tracking
  
- Created RESTful API endpoints:
  - POST `/payment-proofs/{order_id}/submit`: For users to upload payment proof
  - POST `/payment-proofs/{order_id}/verify`: For admins to verify/reject proofs
  - GET `/payment-proofs/pending`: Retrieve orders awaiting verification
  - GET `/payment-proofs/admin/{admin_id}`: List proofs verified by specific admin
  
- Added proper validation and security:
  - Image format and size validation
  - Permission checks (users can only submit for their own orders)
  - Required rejection reason when rejecting payments
  
- Added static file serving capability:
  - Configured proper directory structure 
  - Set up file mount points for uploaded files
  
The system now provides a complete workflow for users to submit payment proof and for admins to verify them, tracking metrics about verification performance and maintaining a secure record of all payment proofs.
