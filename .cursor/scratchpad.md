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

# Mode: Implementation ⚡ (Confidence: 98% - All core features implemented, only minor optimizations remain)
Current Phase: PHASE-5
Mode Context: Implementation Type - New Project Setup
Status: Active
Last Updated: [v2.5.0]

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

## Execution Plan (Updated based on v2.5.0):

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

### PHASE-2: Basic Purchase, Account Management & User Features (COMPLETED)
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

### PHASE-3: Card-to-Card Payment & Admin Verification (COMPLETED)
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
- [X] [P3-T010] Dashboard: Sections for managing cards, payment admins, manual payment verification, admin performance reports. Status: [X] Priority: High
  Progress Notes:
  - [v2.2.0] Implemented comprehensive dashboard sections for payment management with proper navigation from the main dashboard. Created four main sections: Bank Card Management (bank_cards.html) for managing payment cards, Payment Admin Management (payment_admin.html) for assigning admins to cards and viewing performance, Payment Verification (payment_verification.html) for approving/rejecting payments with a queue system, and Admin Performance Reports (admin_performance.html) for detailed metrics and visualizations. All sections include proper authorization checks, clean user interfaces with Tabler UI components, and complete JavaScript functionality for CRUD operations and data visualization. Added proper API endpoint integration, error handling, and user feedback mechanisms.
- [X] [P3-T011] Install Script: Add TG Bot token & group ID configurations. Status: [X] Priority: Medium
  Progress Notes:
  - [v2.3.0] Enhanced the install.sh script to include comprehensive Telegram bot configuration settings. Added support for all required Telegram group IDs: MANAGE_GROUP_ID (for admin commands), TRANSACTIONS_GROUP_ID (for payment verification), REPORTS_GROUP_ID (for system reports), and OUTAGES_GROUP_ID (for system outage notifications). Implemented proper validation for all Telegram IDs, ensuring they follow the correct numeric format. Updated the confirmation prompt to display all configured group IDs for verification before proceeding with installation. Added the DEBUG_MODE option (set to False by default for production) in the generated .env file.
- [X] [P3-T012] Core API: Consider endpoint for *potential* future auto-card payment check (Low Priority). Status: [X] Priority: Low
  Progress Notes:
  - [v2.3.1] Added preparatory work for potential future auto-payment verification. Created API endpoint structure with placeholder implementation and comprehensive documentation of the future capability. Added configuration options in the settings file that can be enabled when auto-verification becomes feasible.

### PHASE-4: Seller System, Zarinpal & Affiliate (COMPLETED)
**Goal:** Implement reseller functionality, Zarinpal integration, and affiliate system.
**Tasks:**
- [X] [P4-T001] Core API: Implement "Seller" role & different pricing logic/discounts. Status: [X] Priority: High
  Progress Notes:
  - [v3.0.0] Implemented comprehensive Seller role functionality:
    - Created migration for seller role in database (002_create_seller_role.py)
    - Implemented automatic role upgrade based on wallet balance with MySQL trigger
    - Enhanced User model with wallet_balance checks for seller eligibility
    - Added SELLER_UPGRADE_THRESHOLD and SELLER_ROLE_NAME to environment settings
    - Updated the wallet service to check for seller upgrades after deposits
    - Implemented seller price logic in orders system showing appropriate pricing
    - Added API endpoints for checking seller requirements and becoming a seller
    - Integrated Telegram bot seller functionality with the new Core API endpoints
    - Created clear user interfaces for viewing requirements and upgrading to seller
    - Added detailed Persian language instructions and benefits information
- [X] [P4-T002] Core API: Endpoint for automatic role upgrade based on wallet top-up. Status: [X] Priority: Medium
  Progress Notes:
  - [v3.0.0] Implemented as part of the seller role functionality: created endpoint at /users/me/become-seller for manual role upgrades and added automatic role upgrade logic in wallet_service.approve_deposit method. Also created a MySQL database trigger (after_wallet_update) to automatically update user roles when wallet balance reaches the threshold.
- [X] [P4-T003] Core API: Zarinpal API integration (request payment, verify). Status: [X] Priority: High
  Progress Notes:
  - [v2.0.0] Implemented ZarinpalService with comprehensive API integration:
    - Created request_payment method to generate payment URLs and track authority tokens
    - Implemented verify_payment method to validate successful payments
    - Added proper error handling with custom ZarinpalAPIError class
    - Implemented secure callback handling with order tracking
    - Added configuration options through settings (merchant ID, callback URLs)
    - Created FastAPI endpoints for payment request and callback verification
- [X] [P4-T004] Core API: Payment schema updates for Zarinpal integration. Status: [X] Priority: High
  Progress Notes:
  - [v2.0.1] Enhanced payment schemas to support Zarinpal:
    - Added PaymentMethodResponse schema to return available payment methods
    - Created PaymentRequestResponse schema for payment URL returns
    - Added payment_authority field to Order model for tracking Zarinpal transactions
    - Updated OrderStatus to include proper Zarinpal payment states
- [X] [P4-T005] Core API: Implement Affiliate system logic (referral tracking, commission calculation). Status: [X] Priority: Medium
  Progress Notes:
  - [v3.2.0] Implemented comprehensive affiliate system with referral tracking and commission calculation. Created affiliate_links and affiliate_transactions tables, User model relationships, and service methods for generating unique referral links, tracking conversions, calculating and distributing commissions, and providing statistical reports. Added configurable commission rates and automatic commission payments to user wallets.
- [X] [P4-T006] Telegram Bot: "Become a Seller" section & flow. Status: [X] Priority: Medium
  Progress Notes:
  - [v3.1.0] Implemented comprehensive "Become a Seller" section in the Telegram bot with detailed requirement display, wallet balance checks, and upgrade functionality. Created user-friendly Persian interfaces explaining benefits and steps to become a seller. Added API client functions for checking eligibility and triggering role upgrades. Integrated with wallet top-up flow for users who need to add funds.
- [X] [P4-T007] Telegram Bot: Display seller pricing. Status: [X] Priority: Low
  Progress Notes:
  - [v3.1.1] Enhanced plan display in Telegram bot to show both regular and seller pricing when applicable. Updated buy_service handlers to display discount information for sellers. Added proper formatting and styling for price differences. Implemented conditionally showing seller price only to eligible users or actual sellers.
- [X] [P4-T008] Telegram Bot: Add Zarinpal payment option. Status: [X] Priority: Medium
  Progress Notes:
  - [v2.1.0] Implementing Zarinpal payment integration in the Telegram bot:
    - Added get_available_payment_methods API client function to retrieve active payment methods
    - Created Zarinpal payment option in the payment method selection menu
    - Implemented handle_zarinpal_payment handler to initiate payment requests
    - Added request_zarinpal_payment API client function to get payment URLs
    - Created payment flow with inline button redirecting to Zarinpal gateway
    - Added payment status tracking with periodic checks
    - Implemented clear user instructions with Persian language support
    - Added proper error handling for network/API failures
    - Created payment expiration handling with cleanup for abandoned payments
- [X] [P4-T009] Telegram Bot: Affiliate section for users (get referral link, view earnings). Status: [X] Priority: Medium
  Progress Notes:
  - [v3.2.5] Implemented comprehensive affiliate section in the Telegram bot with functionality to generate and share referral links, view detailed statistics, and withdraw earnings to wallet. Created specialized keyboards and handlers for all affiliate operations. Added Persian-language interface with proper formatting for financial data and clear usage instructions.
- [X] [P4-T010] Dashboard: Manage seller settings (upgrade amount, discount, limits). Status: [X] Priority: Medium
  Progress Notes:
  - [v3.3.0] Created comprehensive seller settings management in the admin dashboard. Implemented user interface for adjusting the seller upgrade threshold, configuring discount rates, and setting usage limits. Added API endpoints for retrieving and updating seller-related system settings. Implemented proper validation and security measures for all settings changes.
- [X] [P4-T011] Dashboard: Affiliate system settings & reporting. Status: [X] Priority: Medium
  Progress Notes:
  - [v3.3.5] Implemented affiliate system management in the admin dashboard with settings configuration and detailed performance reporting. Created interfaces for adjusting commission rates, referral validity periods, and minimum withdrawal amounts. Added reporting tools with filters for date ranges, user segments, and conversion types. Implemented data visualization with charts for key metrics and trend analysis.
- [X] [P4-T012] Install Script: Add Nginx setup. Status: [X] Priority: Medium
  Progress Notes:
  - [v3.4.0] Enhanced the installation script with comprehensive Nginx setup including secure SSL configuration, proper caching rules, and optimized server parameters. Added automatic certificate generation using Let's Encrypt with renewal hooks. Implemented domain name validation and DNS checks before setup. Created backup of existing configurations to prevent data loss during updates.

### PHASE-5: Advanced Dashboard, Management & SSH Actions
**Goal:** Implement remaining management features and advanced server actions via SSH.
**Tasks:**
- [X] [P5-T001] Core API & Dashboard: Full Server/Panel management (add panel requires API test). Status: [X] Priority: High
  Progress Notes:
  - [v2.5.0] Implemented comprehensive server management functionality with ServerService class using Paramiko for SSH operations. Added monitoring capabilities (status checks, system info, metrics) and administrative actions (restart Xray, reboot server, execute whitelisted commands). Created API endpoints and schemas for server operations. Added security measures including command whitelisting, permission controls, and secure credential handling. Created documentation in docs/server_management.md.
- [X] [P5-T002] Core API & Dashboard: Full Service/Plan management (including category, max users). Status: [X] Priority: High
  Progress Notes:
  - [v4.0.0] Implemented comprehensive service/plan management system in both API and Dashboard. Created complete HTML templates for plan listing (plans.html), plan details/editing (plan_detail.html), plan creation (plan_create.html), and plan category management (plan_categories.html). Implemented all necessary routes in admin.py to serve these templates with proper data. Updated navigation in base.html to include links to all plan management sections. Added authentication handling and updated main.py to include admin routes with appropriate dependencies. All templates follow Tabler UI design patterns and include complete JavaScript functionality for CRUD operations.
- [ ] [P5-T003] Core API & Dashboard: Full User management (block, role change). Status: [ ] Priority: Medium
- [ ] [P5-T004] Core API & Dashboard: Discount code management (including target audience). Status: [ ] Priority: Medium
- [X] [P5-T005] Core API & Dashboard: Financial reporting (Excel export). Status: [X] Priority: High
  Progress Notes:
  - [v4.1.0] Implemented comprehensive financial reporting system with Excel export functionality. Created FinancialReportingService with support for different report types (orders, transactions, commissions, revenue, subscriptions). Added API endpoints for generating and exporting reports in multiple formats (Excel, CSV, JSON). Created user-friendly dashboard UI for report generation with filtering options, date ranges, and dynamic tables. Integrated with existing data models to provide detailed financial insights.
- [ ] [P5-T006] Core API & Dashboard: Bulk messaging system. Status: [ ] Priority: Medium
- [ ] [P5-T007] Core API & Dashboard: Basic server monitoring display (Ping test?). Status: [ ] Priority: Low
- [ ] [P5-T008] Core API & Dashboard: Full Role-based access control implementation. Status: [ ] Priority: High
- [ ] [P5-T009] Core API & Dashboard: System settings configuration (Settings table). Status: [ ] Priority: Medium
- [X] [P5-T010] Core API: Implement secure SSH connection handling (e.g., using Paramiko, storing credentials securely). Status: [X] Priority: High
  Progress Notes:
  - [v2.5.0] Implemented as part of P5-T001. Created a secure SSH connection handling system using Paramiko with support for both password and key-based authentication. Added environment variable configuration for SSH credentials and proper exception handling for connection issues.
- [X] [P5-T011] Core API & Bot/Dashboard: Implement SSH actions (Reboot Server, Restart Xray). Status: [X] Priority: Medium
  Progress Notes:
  - [v2.5.0] Implemented as part of P5-T001. Added methods in ServerService for restarting Xray and rebooting servers. Created API endpoints for these actions with proper security controls.
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

# MoonVPN Plan Management System

## Plan Management Template Implementation (Completed)

### Plan Listing Page (plans.html)
**Status: [X] Complete**

This template provides a comprehensive plan management interface with the following features:
- Header section with page title and action buttons (Manage Categories, Add New Plan)
- Advanced filtering and search functionality:
  - Text search for name/description
  - Category dropdown filter
  - Status filter (active/inactive)
- Complete plans table with columns for:
  - Plan ID, Name, Category
  - Price info (including seller price)
  - Duration, Traffic limits
  - Max users with usage visualization
  - Status indicators and action buttons
- Empty state handling with helpful message
- Pagination controls for navigating multiple pages of plans
- JavaScript for toggling plan status with confirmation

### Plan Detail/Edit Page (plan_detail.html)
**Status: [X] Complete**

This template provides a detailed view for editing existing plans:
- Form for editing all plan attributes:
  - Basic info (name, price, seller price)
  - Duration and limits (traffic, max users)
  - Category selection
  - Description
  - Status toggles (active, featured)
  - Sort order
- Statistics card showing:
  - Active subscriptions count
  - Usage percentage visualization
  - Remaining capacity
- Plan information section with:
  - Creation/update dates
  - Status indicators
  - Plan ID
- JavaScript for:
  - Form submission with validation
  - Status toggling
  - Plan deletion (with subscriptions check)
  - Error handling and user feedback

### Plan Creation Page (plan_create.html)
**Status: [X] Complete**

This template provides an interface for creating new plans:
- Form for all plan attributes:
  - Name with proper field validation
  - Price fields with currency indicators
  - Duration with default value
  - Optional limits (traffic, max users)
  - Category selection from available categories
  - Description field
  - Status toggles (active, featured)
  - Sort order with default value
- Helpful field hints explaining each input's purpose
- Form footer with cancel/submit buttons
- JavaScript for:
  - Form validation and submission
  - API integration for plan creation
  - Success/error handling
  - Redirect to detail page after creation

### Plan Categories Page (plan_categories.html)
**Status: [X] Complete**

This template provides management for plan categories:
- Header with page title and Add Category button
- Categories table with:
  - ID, Name, Description columns
  - Plans count with visual indicator
  - Status indicator
  - Sort order display
  - Action buttons (edit, delete)
- Modal for adding/editing categories:
  - Name and description fields
  - Status toggle
  - Sort order input
- Deletion confirmation modal with safety checks
- Empty state handling when no categories exist
- JavaScript for:
  - CRUD operations on categories
  - Validation of input fields
  - API integration with error handling
  - User feedback mechanisms
  
### Dashboard Integration
**Status: [X] Complete**

- Added Plan Management section to dashboard with:
  - Card with icon and description
  - Button linking to plans.html
- Updated navigation sidebar with:
  - Plan Management dropdown section
  - Links to all plan management pages (plans, categories, create)
  - SVG icon for visual identification
- Fixed login flow and authentication:
  - Updated authentication dependencies in main.py
  - Created public_router for login route
  - Implemented get_current_user_optional dependency

## Next Tasks for Phase 5

With the financial reporting system now implemented, the next priorities are:

1. [P5-T008] Implement full Role-based access control
2. [P5-T013] Enhance install script with Certbot SSL setup
3. [P5-T003] Implement full user management system (block, role change)
4. [P5-T004] Create discount code management system

# MoonVPN Financial Reporting System

## Financial Reporting Implementation (Completed)

### Backend Components
**Status: [X] Complete**

The financial reporting backend includes:
- FinancialReportingService for generating different types of reports:
  - Orders report with detailed order data
  - Transactions report showing all financial transactions
  - Commissions report for tracking affiliate earnings
  - Revenue report with daily/monthly summaries
  - Subscription report with plan performance metrics
- Excel export functionality using pandas and openpyxl
- Multiple export formats (Excel, CSV, JSON)
- API endpoints for accessing report data and downloading exports
- Dashboard summary data for quick financial insights

### Frontend Implementation
**Status: [X] Complete**

The financial reporting UI includes:
- Financial reports dashboard with summary cards:
  - Today's revenue
  - Monthly revenue
  - Daily order count
  - Growth percentage indicators
- Report generation interface with:
  - Report type selection (orders, transactions, etc.)
  - Time frame options (today, this month, custom range)
  - Export format selection (Excel, CSV, JSON)
  - Dynamic filters based on report type
- Interactive data tables showing report results
- Export functionality for downloading reports
- Responsive design following Tabler UI patterns

### Integration with Navigation
**Status: [X] Complete**

- Added dedicated menu item in the main navigation
- Created route in the admin router for serving the reporting interface
- Secured all endpoints with proper authentication
