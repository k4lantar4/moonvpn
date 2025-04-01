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
Current Phase: PHASE-2
Mode Context: Implementation Type - New Project Setup
Status: Active
Last Updated: [v0.1.7]

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
- [ ] [P3-T001] Core API: Manage Bank Cards (CRUD). Status: [ ] Priority: High
- [ ] [P3-T002] Core API: Manage Payment Admins & assign to cards/groups (link to Roles/Permissions). Status: [ ] Priority: High
- [ ] [P3-T003] Core API: Endpoints for submitting payment proof & updating order status (pending, approved, rejected). Status: [ ] Priority: High
- [ ] [P3-T004] Core API: Logic for rotating bank cards display. Status: [ ] Priority: Medium
- [ ] [P3-T005] Core API: Generate reports on payment admin performance. Status: [ ] Priority: Medium
- [ ] [P3-T006] Telegram Bot: Implement card-to-card payment flow (display card, timer, upload proof). Status: [ ] Priority: High
- [ ] [P3-T007] Telegram Bot: Send proof notification to specific TG group (based on card) with Approve/Reject buttons. Status: [ ] Priority: High
- [ ] [P3-T008] Telegram Bot: Handle admin actions (Approve/Reject callback) in group, check permissions, update order via API, notify user. Status: [ ] Priority: High
- [ ] [P3-T009] Telegram Bot: Admin commands (in MANAGE group?) to manage cards & payment admins. Status: [ ] Priority: Medium
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

## Current Phase: P2 - VPN Panel Integration & API Development

### P2-T005: Implement Subscription Management (Freeze/Unfreeze, Notes, Auto-Renew)
**Status: [X] Complete**

This task focused on implementing a subscription management system with:
1. Freeze/unfreeze functionality (with date tracking)
2. User notes 
3. Auto-renewal settings

#### Completed Implementation:
- Created `Subscription` model with:
  - Freeze-related fields: `is_frozen`, `freeze_start_date`, `freeze_end_date`, `freeze_reason`
  - Notes field for admin and user notes
  - Auto-renew fields: `auto_renew`, `auto_renew_payment_method`
  
- Implemented `SubscriptionService` with methods:
  - `get_subscription` & `get_user_subscriptions` for retrieving subscription data
  - `create_subscription` for setting up new subscriptions
  - `freeze_subscription` & `unfreeze_subscription` for managing freeze state
  - `add_note` for adding notes to subscriptions
  - `toggle_auto_renew` for managing auto-renewal settings
  - `check_expired_subscriptions` for handling subscription expiration

- Created RESTful API endpoints:
  - GET `/subscriptions/` - List user's subscriptions
  - GET `/subscriptions/{id}` - Get specific subscription details
  - POST `/subscriptions/` - Create a new subscription (admin only)
  - POST `/subscriptions/{id}/freeze` - Freeze a subscription
  - POST `/subscriptions/{id}/unfreeze` - Unfreeze a subscription
  - POST `/subscriptions/{id}/notes` - Add a note
  - POST `/subscriptions/{id}/auto-renew` - Toggle auto-renewal

- Added relationships to:
  - `User` model for linking users to subscriptions
  - `Plan` model for connecting plans to subscriptions

- Developed comprehensive unit tests for:
  - Service methods - Testing all subscription operations
  - API endpoints - Ensuring proper HTTP interactions
  
- Integrated with `PanelService` to automatically:
  - Disable clients when subscriptions are frozen
  - Enable clients when subscriptions are unfrozen
  - Handle expired subscriptions

### Next Tasks:
1. P2-T006: Implement subscription renewal process
2. P2-T007: Create admin subscription management dashboard
3. P2-T008: Implement user subscription history tracking

[P2-T005] Add subscription management features (freeze, add notes, auto-renew toggle)
Status: [X] Priority: [Medium]
Dependencies: [P2-T003]
Progress Notes:
- [v0.4.3] Implemented subscription management features including freeze/unfreeze functionality with panel synchronization, note addition, and auto-renew toggle capabilities.

[P2-T006] Add protocol/location change feature for subscriptions
Status: [X] Priority: [Medium]
Dependencies: [P2-T003]
Progress Notes:
- [v0.4.4] Implemented protocol and location change functionality for active subscriptions. This allows users to change their VPN protocol or server location by moving to different inbounds or panels. Added comprehensive error handling with automatic rollback in case of failures, and ensured proper validation to prevent changes to expired or frozen subscriptions.

#### P2-T007: ✅ Purchase flow in the Telegram bot (Done)
- Implemented the flow for purchasing VPN subscriptions in the Telegram bot
- Added functionality for users to select plans, payment methods, and submit payments
- Created a system for admins to approve or reject payments
- Implemented proper error handling and user notifications

#### P2-T008: ✅ "My Account" section for listing accounts (Done)
- Created a new section in the Telegram bot for users to view and manage their VPN accounts
- Implemented functionality to list all user subscriptions with their status
- Added detailed view for each subscription showing expiry date, remaining days, protocol, and location
- Implemented QR code display for easy connection to VPN services
- Added traffic usage statistics with visual progress bar
- Implemented account management features:
  - Freeze/unfreeze subscription
  - Add notes to subscriptions
  - Toggle auto-renewal
  - Change protocol or location

#### P2-T009: ✅ Payment confirmation with automatic account creation (Done)
- Implemented a complete payment confirmation flow in the Telegram bot that triggers automatic account creation
- Added API functions for confirming and rejecting order payments:
  - `confirm_order_payment`: Calls the core API's create-client endpoint to create a VPN account
  - `reject_order_payment`: Updates the order status to rejected with detailed reason
- Enhanced the admin payment confirmation handler to display detailed subscription information
- Added robust error handling with appropriate messages for both users and admins
- Implemented a fallback mechanism for manual processing when automatic account creation fails
- Ensured proper cleanup of in-memory order data after successful processing
