# MoonVPN Project Requirements 🚀 (v3 - Bot-Centric Architecture)

**Version:** 0.1.0
**Last Updated:** 2025-04-09

## 1. Introduction & Vision

### 1.1. Project Overview
MoonVPN aims to be a robust, user-friendly, and modern Telegram-based platform for managing and selling V2Ray VPN services. The system leverages a bot-centric architecture, where the Telegram bot serves as the primary interface for all user roles (Clients, Sellers, Admins) and orchestrates backend logic, database interactions, and external panel integrations (initially 3x-ui).

### 1.2. Goals & Objectives
- **Automation:** Automate VPN client provisioning, billing, and management.
- **User Experience:** Provide a seamless, intuitive, and engaging experience through a well-designed Telegram bot interface (Persian language first 🇮🇷✨).
- **Scalability:** Build a system capable of handling multiple panels and a growing user base.
- **Maintainability:** Ensure clean, modular, well-documented, and testable code.
- **Security:** Implement robust security practices for user data, panel credentials, and payments.
- **Flexibility:** Design for potential future integration with other panel types and payment gateways.

### 1.3. Target Audience
- **Clients:** End-users purchasing and using VPN services.
- **Sellers/Resellers:** Individuals selling VPN services with potential discounts/commissions.
- **Administrators:** System operators managing panels, users, plans, and overall system health.

## 2. Core Architecture & Technology Stack

### 2.1. Architectural Principles
- **Bot-Centric:** The Telegram bot is the core application logic driver. No separate backend API service.
- **Service-Oriented (within Bot):** Business logic is encapsulated within distinct, reusable services (`bot/services/`).
- **Layered Architecture:** Clear separation of concerns: Presentation (Handlers) -> Business Logic (Services) -> Data Access (Repositories) / Integrations.
- **Asynchronous:** Fully leverage Python's `asyncio` for non-blocking I/O.
- **Modularity:** Components are designed to be independent and easily replaceable/extendable.
- **Database as Source of Truth (for managed data):** Our database (`moonvpn_db.sql` schema) holds user info, plans, orders, wallet balances, panel connection details, etc. Panel state (client status, traffic) is fetched via API but may be cached.

### 2.2. Technology Stack
- **Programming Language:** Python 3.10+
- **Telegram Bot Framework:** `aiogram` 3.x
- **Database:** MySQL 8.0+
- **ORM & Migrations:** `SQLAlchemy` 2.x (async), `Alembic`
- **Database Driver:** `aiomysql` or `asyncmy`
- **Caching:** Redis (via `redis-py` async client)
- **HTTP Client:** `httpx`
- **Data Validation:** `Pydantic` V2
- **Configuration:** `Pydantic-Settings`
- **Deployment:** `Docker`, `Docker Compose`
- **Dependency Management:** `Poetry` or `PDM` (Recommended - using `pyproject.toml`)
- **Linting/Formatting:** `ruff`, `mypy`

### 2.3. Directory Structure (`/root/moonvpn/`)
```
moonvpn/
├── bot/                      # === BOT CORE === (Primary Application Logic)
│   ├── __init__.py
│   ├── main.py               # Bot Entry Point: Initializes bot, dispatcher, routers, services.
│   │
│   ├── handlers/             # User Interaction Layer: Processes Telegram updates (messages, callbacks).
│   │   ├── __init__.py
│   │   ├── common/           # Handlers for general commands (e.g., /start, /help).
│   │   ├── user/             # Handlers specific to regular users (e.g., /myaccounts, /buy).
│   │   ├── admin/            # Handlers for administrator commands (e.g., /syncinbounds, /users).
│   │   └── seller/           # Handlers for seller-specific actions (e.g., /commission).
│   │
│   ├── services/             # Business Logic Layer: Encapsulates core functionalities. Orchestrates repositories & integrations.
│   │   ├── __init__.py
│   │   ├── base_service.py   # Optional: Base class with common service dependencies (repos, session).
│   │   ├── user_service.py   # Manages user registration, profile, roles, balance.
│   │   ├── panel_service.py  # Manages panel CRUD in DB, interacts with panel clients for sync/health checks.
│   │   ├── client_service.py # Manages VPN client lifecycle (provisioning, status sync, user actions) in DB and on panel.
│   │   ├── plan_service.py   # Manages plans and categories.
│   │   ├── location_service.py # Manages locations.
│   │   ├── payment_service.py # Handles payment processes (gateway integration, card-to-card verification).
│   │   ├── wallet_service.py # Manages user wallet balances and transactions.
│   │   ├── notification_service.py # Sends notifications to designated channels.
│   │   ├── security_service.py # Provides security-related checks/operations within the bot flow.
│   │   ├── backup_service.py # Coordinates database backups.
│   │   └── ...               # Other services (e.g., trial_service.py, referral_service.py).
│   │
│   ├── keyboards/            # UI Components: Builders for Telegram Inline and Reply Keyboards.
│   │   ├── __init__.py
│   │   ├── inline/           # Inline keyboard builders (e.g., admin_panels_kb.py).
│   │   └── reply/            # Reply keyboard builders (e.g., main_menu_kb.py).
│   │
│   ├── middlewares/          # Request Processing Pipeline: Intercepts and processes incoming updates before handlers.
│   │   ├── __init__.py
│   │   └── auth.py           # Example: Checks user existence and role permissions.
│   │
│   ├── filters/              # Custom Logic for Handler Triggering: Decides if a handler should run based on specific criteria.
│   │   ├── __init__.py
│   │   └── role.py           # Example: Filter handlers based on user role (Admin, Seller, User).
│   │
│   ├── states/               # Finite State Machine (FSM) Definitions: Manages multi-step conversation flows.
│   │   ├── __init__.py
│   │   └── order_states.py   # Example: States for the plan purchase process.
│   │
│   └── utils/                # Bot-Specific Utilities: Helper functions primarily used within the bot layer.
│       ├── __init__.py
│       └── formatters.py     # Example: Functions for formatting messages sent to users.
│
├── core/                     # === SHARED CORE COMPONENTS === (Foundation for the entire application)
│   ├── __init__.py
│   ├── config.py             # Configuration Management: Loads settings from .env using Pydantic Settings.
│   │
│   ├── database/             # Data Persistence Layer: Handles all database interactions.
│   │   ├── __init__.py
│   │   ├── session.py        # Database Session Management: Provides async SQLAlchemy sessions.
│   │   ├── models/           # Data Structures: Defines SQLAlchemy ORM models mirroring DB tables.
│   │   │   ├── __init__.py
│   │   │   ├── base.py       # Base model class.
│   │   │   └── ...           # Individual model files (e.g., user.py, panel.py, client.py).
│   │   │
│   │   └── repositories/     # Data Access Logic: Implements the Repository Pattern for clean data operations.
│   │       ├── __init__.py
│   │       ├── base_repo.py  # Base repository with generic CRUD methods.
│   │       └── ...           # Specific repositories for each model (e.g., user_repo.py, panel_repo.py).
│   │
│   ├── schemas/              # Data Validation & Transfer Objects: Pydantic schemas for API validation and data structuring between layers.
│   │   ├── __init__.py
│   │   └── ...               # Schemas for different entities (e.g., user_schemas.py, panel_schemas.py).
│   │
│   ├── security.py           # Shared Security Utilities: Functions for hashing, encryption, etc.
│   ├── logging_config.py     # Logging Setup: Configures application-wide logging.
│   ├── cache.py              # Caching Layer: Redis connection setup and caching utilities.
│   ├── exceptions.py         # Custom Exceptions: Defines project-specific error classes.
│   └── utils.py              # Common Utilities: General helper functions usable across the project (datetime, strings, etc.).
│
├── integrations/             # === EXTERNAL SERVICE INTEGRATIONS === (Connectors to the outside world)
│   ├── __init__.py
│   ├── panels/               # VPN Panel Clients: Code to interact with different panel APIs.
│   │   ├── __init__.py
│   │   ├── base.py           # Abstract base class/interface defining common panel operations.
│   │   ├── xui_client.py     # Client implementation for 3x-ui panels using httpx.
│   │   └── exceptions.py     # Exceptions specific to panel interactions.
│   │
│   ├── payments/             # Payment Gateway Clients: Code for integrating with payment providers.
│   │   ├── __init__.py
│   │   └── zarinpal.py       # Example client for Zarinpal.
│   │
│   └── sms/                  # SMS Service Clients (Optional): For future features like OTP.
│       └── ...
│
├── migrations/               # === DATABASE MIGRATIONS === (Managing DB Schema Evolution)
│   ├── versions/             # Alembic migration script files.
│   ├── env.py                # Alembic configuration script (connects models and DB).
│   └── script.py.mako        # Template for generating new migration scripts.
│
├── scripts/                  # === UTILITY & MANAGEMENT SCRIPTS ===
│   ├── __init__.py
│   ├── moonvpn               # Main CLI Tool (Bash wrapper for Docker Compose & common tasks). *Executable, not .sh*
│   ├── seed_all.py           # Main database seeding script (run via `moonvpn seed`).
│   ├── _seed_scripts/        # Helper scripts called by seed_all.py.
│   └── run_bot_dev.py        # Optional: Helper for running the bot locally outside Docker for quick tests.
│
├── tests/                    # === AUTOMATED TESTS ===
│   ├── __init__.py
│   ├── conftest.py           # Pytest configuration and shared fixtures.
│   ├── unit/                 # Unit tests focusing on isolated components (services, repos).
│   ├── integration/          # Integration tests checking interactions between components (e.g., service + repo + DB).
│   └── fixtures/             # Test data files or factories.
│
├── locales/                  # === LOCALIZATION FILES === (Supporting multiple languages)
│   ├── fa/LC_MESSAGES/       # Persian translations.
│   │   └── messages.po       # Source file for translations (gettext format).
│   └── en/LC_MESSAGES/       # English translations (optional).
│       └── messages.po
│
├── docs/                     # === PROJECT DOCUMENTATION ===
│   ├── index.md              # Main documentation portal.
│   └── phases/               # Documentation related to specific development phases.
│
├── .env.example              # Environment variable template file.
├── .gitignore                # Specifies intentionally untracked files that Git should ignore.
├── alembic.ini               # Alembic configuration file.
├── docker-compose.yml        # Defines and configures the multi-container Docker application (bot, db, redis).
├── Dockerfile.bot            # Instructions for building the bot's Docker image.
└── pyproject.toml            # Project metadata, dependencies, and tool configurations (for Poetry/PDM).
```
**Purpose of Directories:**
- `bot/`: Contains all code directly related to the Telegram bot interface and the application's core business logic. Separated into handlers (input/output), services (logic), keyboards/filters/states (bot specifics), and utils.
- `core/`: Houses shared, fundamental components like database access, configuration, security, logging, caching, and common utilities, used across the application.
- `integrations/`: Isolates code responsible for communicating with external services (VPN panels, payment gateways). Ensures loose coupling.
- `migrations/`: Manages database schema evolution using Alembic.
- `scripts/`: Provides command-line tools for managing the project (installation, running tasks, seeding data).
- `tests/`: Contains all automated tests, separated into unit and integration tests.
- `locales/`: Stores translation files for internationalization (i18n).
- `docs/`: Holds project documentation.

## 3. Functional Requirements (Features)

*(This section will detail each feature based on the database schema and expected functionality. Initial high-level points below, to be expanded.)*

### 3.1. User Management (`UserService`, `UserHandler`, `UserRepo`)
- Registration via `/start` command.
- Role assignment (Admin, Seller, User).
- Profile viewing (`/profile`).
- Balance checking (`/wallet`).
- Language preference setting (`/language`).
- Referral system (generation/tracking) (`ReferralService`).
- Admin capabilities: Search, Ban/Unban, Edit Balance, Assign Role (`AdminHandler`, `AdminService`).

### 3.2. Panel & Location Management (`PanelService`, `LocationService`, `AdminHandler`, `PanelRepo`, `LocationRepo`)
- Admin: Add, Edit, List, Remove Panels (store connection details securely in DB - `panels` table).
- Admin: Add, Edit, List, Remove Locations (`locations` table).
- Automated Panel Health Checks (`PanelService` + Scheduled Task): Periodically check panel connectivity/status (`/login` or specific health endpoint if available), update `panels.is_healthy`. Report failures via `NotificationService`.
- Inbound Management (`PanelService`, `PanelRepo`, `xui_client`):
    - **Read Inbounds from Panel:** Fetch inbound list via `GET /panel/api/inbounds/list` (`xui_client`).
    - **Store/Sync Inbounds:** Store relevant inbound details (ID, tag, protocol, port, etc.) in `panel_inbounds` table, associated with the `panels.id`. Sync periodically or on demand. *(Addresses user question 5)*.
    - Admin Interface: Allow admins to view/manage synced inbounds (e.g., mark as active/inactive for use in plans).

### 3.3. Plan Management (`PlanService`, `AdminHandler`, `PlanRepo`, `PlanCategoryRepo`)
- Admin: Create, Edit, List, Activate/Deactivate Plans (`plans` table).
- Admin: Manage Plan Categories (`plan_categories` table).
- Associate plans with protocols, potentially specific inbounds or locations.

### 3.4. Client (VPN Account) Management (`ClientService`, `PanelService`, `UserHandler`, `ClientRepo`, `xui_client`)
- **Provisioning:**
    - User selects Plan and Location.
    - `ClientService` determines the appropriate Panel (`PanelService` might help select based on location/health) and Inbound (`panel_inbounds`).
    - `ClientService` generates unique `remark` and `panel_client_email` based on patterns (`settings` table, `client_id_sequences`).
    - `ClientService` calls `PanelService.add_client_to_panel()`.
    - `PanelService` uses `xui_client.add_client()` (using `POST /panel/api/inbounds/addClient`) to create the client on the 3x-ui panel.
    - `ClientService` saves client details (UUID, remark, email, user_id, panel_id, plan_id, expire_date, etc.) to the `clients` table in our DB, including the `panel_client_email` used.
- **User Self-Service (`UserHandler`, `ClientService`):**
    - View Accounts (`/myaccounts`).
    - Get Config/QR/Subscription Link.
    - View Usage (requires fetching from panel via `xui_client.get_client_traffics()` and periodically updating `clients.used_traffic` via `ClientService.sync_client_usage`).
    - Renew Service:
        - Calculates new `expire_date` based on plan duration, starting from `max(now, current_expiry)`.
        - Updates panel via `PanelService.update_client_on_panel` (enable, new traffic limit, new expiry time).
        - Optionally resets traffic on panel if `reset_traffic=True` is passed.
        - Resets `used_traffic_bytes` to 0 and updates other details in the `clients` table.
    - **Freeze Account:** `ClientService.update_client_status()` calls `PanelService.disable_client_on_panel()` (using `POST /panel/api/inbounds/updateClient/:clientId` with `enable: false`). Update `clients.status` to `DISABLED_USER` or similar. **Crucially, `expire_date` does not stop ticking.** (*Note: Currently uses `panel_client_email` as identifier, see Section 6.3 for API details.*)
    - **Unfreeze Account:** `ClientService.update_client_status()` calls `PanelService.enable_client_on_panel()` (using `POST /panel/api/inbounds/updateClient/:clientId` with `enable: true`). Update `clients.status` to `ACTIVE`. (*Note: Currently uses `panel_client_email` as identifier.*)
    - *Other actions like changing location/protocol need careful implementation based on panel API capabilities (might involve deleting and recreating).*
- **Status Synchronization (`ClientService` scheduled tasks):**
    - `run_periodic_usage_sync`: Periodically fetch client usage from the panel (`xui_client.get_client_traffics()`) via `sync_client_usage` and update `clients.used_traffic_bytes` in the DB.
    - `run_periodic_expiry_check`: Periodically check for expired clients and update their status to `EXPIRED` in the DB via `update_client_status` (which also attempts to disable them on the panel).
- **Error Handling Consideration:**
    - **Critical:** Need a consistent strategy for handling failures during panel interactions (`PanelAPIError`, `PanelAuthenticationError`, `ServiceError`, or `False` return values). Currently, some operations (like `renew_client`) raise errors, while others (like `update_client_status`) only log the error and proceed with DB updates. This can lead to inconsistencies between the database state and the actual panel state. A unified approach (e.g., always raising an error or implementing a retry mechanism with clear logging) is required.

### 3.5. Payment & Wallet System (`PaymentService`, `WalletService`, `UserHandler`, `AdminHandler`, `PaymentRepo`, `TransactionRepo`, `BankCardRepo`, `ZarinpalClient`)
- **Internal Wallet (`WalletService`, `TransactionRepo`):** Manage `users.balance`, record all deposits, purchases, refunds, commissions in `transactions`.
- **Card-to-Card (`PaymentService`, `BankCardRepo`, `NotificationService`):**
    - Admin manages available cards (`bank_cards`).
    - User selects card, uploads receipt.
    - Bot sends details to verification channel (`NotificationService`).
    - Admin approves/rejects via inline buttons.
    - On approval, `PaymentService` calls `WalletService.deposit()`.
- **Zarinpal (`PaymentService`, `ZarinpalClient`):** Implement standard gateway flow (request payment, handle callback, verify, call `WalletService.deposit()`).

### 3.6. Seller System (`SellerService`, `ReferralService`, `SellerHandler`, `UserRepo`, `RoleRepo`)
- Discount application during purchase flow (`PaymentService` or `OrderService`).
- Commission tracking (potentially needs adjustments to `transactions` or a new table).
- Seller dashboard in bot.
- Referral link generation/handling.

### 3.7. Free Trial System (`TrialService`, `ClientService`, `PanelService`)
- Eligibility checks (initial manual approval, future SMS).
- Provision temporary client on designated panel/inbound via `ClientService`/`PanelService`.
- Schedule automatic disabling/deletion after expiry using `ClientService` and panel API.

### 3.8. Notifications (`NotificationService`, various Services)
- Send messages to configured Telegram channels (`notification_channels` table) for events:
    - New User Registration
    - Payment Verification Required
    - Payment Verified/Rejected
    - Panel Down/Recovered
    - Low Balance/Expiry Warning
    - Backup Completion
    - Critical Errors (from logging)
    - Reports (Sales, Usage)

### 3.9. Backup & Security (`BackupService`, `SecurityService`, `AdminHandler`)
- Automated DB backups (`mysqldump`) sent to channel (`BackupService`, `NotificationService`).
- Secure password hashing for panel creds (`core/security`).
- Bot command rate limiting (`bot/middlewares/`).
- Role-based access control (`bot/middlewares/auth.py`, `bot/filters/role.py`).

## 4. Non-Functional Requirements

*(To be detailed later - Performance, Scalability, Reliability, Maintainability, Usability)*

## 5. Data Model (Database Schema)

Refers to the schema defined in `moonvpn_db.sql`. Key tables and their purpose are reflected in `core/database/models/`.

*(Include a summary or link to the detailed schema if needed)*

## 6. 3x-ui Panel API Integration (`integrations/panels/xui_client.py`, `PanelService`)

### 6.1. Authentication
- Implement login flow (`POST /login`) using `httpx` client.
- Store session cookies securely (in memory with expiry, or potentially Redis if scaling bot instances).
- Handle session expiry and re-authentication.

### 6.2. Core API Endpoints to Implement (`xui_client.py`)
*(Based on [3x-ui API Docs](https://github.com/MHSanaei/3x-ui?tab=readme-ov-file#api-routes))*
- `login(username, password)`
- `get_inbounds()` -> `GET /panel/api/inbounds/list`
- `get_inbound(inbound_id)` -> `GET /panel/api/inbounds/get/:id`
- `add_client(inbound_id, client_settings)` -> `POST /panel/api/inbounds/addClient` (Needs correct payload structure for email, uuid, traffic, expiry etc.)
- `update_client(client_identifier, updates)` -> `POST /panel/api/inbounds/updateClient/:clientId` (Payload includes `enable`, traffic, expiry etc. `clientId` needs mapping based on protocol)
- `delete_client(inbound_id, client_identifier)` -> `POST /panel/api/inbounds/:id/delClient/:clientId`
- `get_client_traffics(email)` -> `GET /panel/api/inbounds/getClientTraffics/:email`
- *(Maybe)* `reset_client_traffic(inbound_id, email)` -> `POST /panel/api/inbounds/:id/resetClientTraffic/:email`
- *(Maybe)* `get_online_clients()` -> `POST /panel/api/inbounds/onlines`

### 6.3. Client Identifier (`clientId` in API)
- **Key Concepts and Implementation Details:**
    - **Protocol-Based Identifier Mapping:** The identifier required by the panel API varies by protocol:
        - VMESS/VLESS: Uses UUID (`client.id`) for client identification.
        - TROJAN: Uses password (`client.password`) for client identification.
        - SHADOWSOCKS: Uses email (`client.email`) for client identification.
    - **Required Parameters for API Operations:**
        - `inbound_id`: All operations require the inbound ID to specify which inbound the client belongs to.
        - `protocol`: Used to determine the correct identifier and API endpoint for each client.
        - `client_identifier`: The protocol-specific identifier for the client.
    - **Storage Strategy:**
        - Our database stores the client's specific identifier in the `panel_native_identifier` field of the `ClientAccount` model.
        - The `inbound_id` field stores the foreign key to the `panel_inbounds` table, capturing the relationship between client and inbound.
        - The protocol is determined based on the inbound's settings or stored explicitly for client operations.
    - **API Interaction Flow:**
        1. `ClientService` provides `inbound_id` and `protocol` to `PanelService` methods.
        2. `PanelService` passes these parameters to the correct `XuiPanelClient` methods.
        3. `XuiPanelClient` selects the appropriate API endpoint and identifies clients correctly based on protocol.
    - **Subscription URL Creation:**
        - Generated dynamically based on panel URL, protocol, and the client's identifier.
    - **Relationship Structure:**
        - `ClientAccount` has a foreign key `inbound_id` referencing `PanelInbound.id`
        - `ClientAccount` has a relationship named `inbound` that loads the associated `PanelInbound`
        - `PanelInbound` has a relationship named `client_accounts` that loads all associated `ClientAccount` records
        - These relationships use `back_populates` to maintain bidirectional integrity

## 7. Project Phases (Initial Plan)

### Phase 0: Foundation & Core Setup (✅ Completed)
- **Goal:** Establish project structure, core components, DB setup, and basic panel interaction.
- **Tasks:**
    - Finalize and create directory structure.
    - Implement `core/config.py`, `core/logging_config.py`, `core/security.py`, `core/cache.py`, `core/exceptions.py`.
    - Implement `core/database/session.py` (async).
    - Define all models in `core/database/models/` based on `moonvpn_db.sql`.
    - Define base repository `core/database/repositories/base_repo.py`.
    - Implement `integrations/panels/xui_client.py` with `login()` and `get_inbounds()`.
    - Setup Alembic (`migrations/`) and generate initial migration script based on models.
    - Develop `scripts/moonvpn.sh` for: install dependencies (poetry/pdm), run migrations, start/stop docker services.
    - Update `docker-compose.yml` and `Dockerfile.bot`.
- **Deliverable:** A runnable project structure with core components implemented, database schema created via migrations, basic panel connection possible, and bot successfully responding to `/start`.

### Phase 1: Bot Basics & Panel/Location Management (Current Focus 🎯)
- **Goal:** Implement basic bot functionality, admin commands for panels/locations, and inbound syncing.
- **Tasks:** Implement `bot/main.py`, common handlers, admin handlers for panels/locations, `PanelService`, `LocationService`, panel health checks, inbound syncing logic (`/syncinbounds`).
- **Deliverable:** Bot responds, admins can manage panels/locations, inbounds are synced via `/syncinbounds`.

*(Further phases: User registration, Plans, Purchase flow, Client provisioning, Payments, etc.)*

## 8. Documentation & Standards
- Follow rules defined in `@brain-memories-lessons-learned-scratchpad.mdc` and `@documentations-inline-comments-changelog-docs.mdc`.
- Code comments in English.
- User-facing text (bot messages) in Persian.
- Maintain `CHANGELOG.md`.
- Update this document (`@project-requirements.md`) as needed.

---
*This document provides the initial blueprint. Details will be refined during each phase.*
