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
Current Phase: PHASE-0
Mode Context: Implementation Type - New Project Setup
Status: Active
Last Updated: [v0.1.1]

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

## Execution Plan (Updated based on v0.1.1):

### Current Phase: PHASE-0: Setup & Infrastructure (Confidence: 94%)
**Goal:** Prepare project structure, detailed database schema, basic API/Bot setup, and installation script.
**Tasks:**
- [-] [P0-T001] Define detailed Database Schema (MySQL) - Incorporating new tables/fields (Locations, Settings, Roles, Affiliate, User Notes, Freeze, etc.). Status: [-] Priority: High
- [ ] [P0-T002] Setup Mono-repo project structure locally. Status: [ ] Priority: High
- [ ] [P0-T003] Initialize Core API (FastAPI) project: basic setup, DB connection (SQLAlchemy). Status: [ ] Priority: Medium
- [ ] [P0-T004] Initialize Telegram Bot (python-telegram-bot) project: basic setup, API token config. Status: [ ] Priority: Medium
- [ ] [P0-T005] Create initial `scripts/install.sh` structure. Status: [X] Priority: Low
- [ ] [P0-T006] Select & integrate Tabler UI template basics into FastAPI. Status: [ ] Priority: Medium
- [ ] [P0-T007] Create initial `README.md` and `.gitignore`. Status: [ ] Priority: Low

### PHASE-1: Core Bot, User Registration & Roles
**Goal:** Implement basic bot functions, user registration/verification, and basic Admin Role/Permission structure.
**Tasks:**
- [ ] [P1-T001] Core API: User management endpoints (register, get info, update role). Status: [ ] Priority: High
- [ ] [P1-T002] Core API: Basic Plan, Panel, Location CRUD endpoints. Status: [ ] Priority: Medium
- [ ] [P1-T003] Core API: Implement basic Roles & Permissions structure (e.g., CRUD for Roles, Permissions, Role-Permission mapping). Status: [ ] Priority: High
- [ ] [P1-T004] Telegram Bot: `/start` command, registration flow (+98 check, channel join check via API). Status: [ ] Priority: High
- [ ] [P1-T005] Telegram Bot: Display main menu & plans (fetched via API). Status: [ ] Priority: Medium
- [ ] [P1-T006] Telegram Bot: Basic Wallet display. Status: [ ] Priority: Low
- [ ] [P1-T007] Telegram Bot: Initial Admin Menu structure (e.g., for Superadmin in MANAGE group). Status: [ ] Priority: Medium
- [ ] [P1-T008] Dashboard: Login (TG ID + OTP via Bot), Basic user profile/wallet view. Status: [ ] Priority: Medium
- [ ] [P1-T009] Dashboard: Basic Role/Permission management interface. Status: [ ] Priority: Medium
- [ ] [P1-T010] Install Script: Add Python, pip, MySQL installation steps. Status: [ ] Priority: Low

### PHASE-2: Basic Purchase, Account Management & User Features
**Goal:** Implement account creation, basic user management, and user-facing subscription features (Freeze, Notes, Auto-Renew).
**Tasks:**
- [ ] [P2-T001] Core API: 3x-ui panel API integration (login, add user, get info, *modify user for protocol/location?*, *enable/disable user for freeze*). Status: [ ] Priority: High
- [ ] [P2-T002] Core API: Order creation logic (link user, plan). Status: [ ] Priority: Medium
- [ ] [P2-T003] Core API: Endpoint to trigger account creation on panel. Status: [ ] Priority: High
- [ ] [P2-T004] Core API: Endpoints for fetching account details (link/QR, usage) from panel. Status: [ ] Priority: Medium
- [ ] [P2-T005] Core API: Logic for Freeze/Unfreeze, User Notes, Auto-Renew setting on Subscription. Status: [ ] Priority: Medium
- [ ] [P2-T006] Core API: Logic for Change Protocol/Location (if feasible via 3x-ui API or needs alternative). Status: [ ] Priority: Medium
- [ ] [P2-T007] Telegram Bot: Purchase flow (select plan, create order via API). Status: [ ] Priority: High
- [ ] [P2-T008] Telegram Bot: "My Account" section (list accounts, get details, Freeze/Unfreeze, Add Note, Toggle Auto-Renew, Change Protocol/Location options via API). Status: [ ] Priority: High
- [ ] [P2-T009] Telegram Bot: Simulate payment confirmation to trigger account creation. Status: [ ] Priority: Medium
- [ ] [P2-T010] Dashboard: Display user's V2Ray accounts and details (including new features). Status: [ ] Priority: Medium
- [ ] [P2-T011] Install Script: Add database setup steps. Status: [ ] Priority: Low

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
