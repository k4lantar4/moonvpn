# MoonVPN 🌕 - V2Ray Account Management System

MoonVPN is a comprehensive system designed for selling and managing V2Ray (Vmess/Vless) accounts, featuring a powerful Telegram bot interface and a web-based dashboard. This project aims to provide a seamless experience for both end-users and administrators.

## Project Structure

This project follows a mono-repo structure:

-   **/core_api**: FastAPI backend handling business logic, database interactions, panel API connections, and serving the web dashboard.
-   **/telegram_bot**: Python application using `python-telegram-bot` library for user and admin interactions via Telegram.
-   **/scripts**: Installation and utility scripts (e.g., `moonvpn` command-line installer).
-   **/docs**: Project documentation.

## Core Technologies

-   **Backend**: Python, FastAPI
-   **Telegram Bot**: `python-telegram-bot`
-   **Database**: MySQL with SQLAlchemy ORM
-   **Dashboard UI**: Tabler (integrated via FastAPI Templates)
-   **Deployment**: Ubuntu 22 (Target OS for installation script)

## Key Features (Planned)

-   V2Ray Account Sales & Management (3x-ui Panel Focus)
-   Telegram Bot Interface (User & Admin)
-   Web Dashboard (Admin & User)
-   Multiple Payment Methods (Manual Card-to-Card, Zarinpal, Wallet)
-   Seller/Reseller System
-   Free Trial Option
-   Advanced Admin Management via Bot & Dashboard
-   Affiliate System
-   User Subscription Management (Freeze, Notes, etc.)
-   Automated Installation Script (`moonvpn`)

## Development Status

Currently in **Phase 0: Setup & Infrastructure**.

*(More details on setup, configuration, and usage will be added later)*

## Development Status

Currently in **Phase 4: Seller System, Zarinpal & Affiliate**.

### Completed Phases:
- ✅ **Phase 0: Setup & Infrastructure** - Project structure, database schema, basic API/Bot setup
- ✅ **Phase 1: Core Bot, User Registration & Roles** - User management, basic plan/panel endpoints, roles & permissions
- ✅ **Phase 2: Basic Purchase, Account Management & User Features** - Panel API integration, order creation, account management
- ✅ **Phase 3: Card-to-Card Payment & Admin Verification** - Bank card management, payment admin system, payment verification flows

### Current Focus:
- 🔄 **Phase 4: Seller System, Zarinpal & Affiliate** - Implementing reseller functionality, Zarinpal integration, affiliate system
- ✅ Zarinpal API integration completed
- ✅ Payment schema updates for Zarinpal completed
- 🔄 Seller role & pricing logic implementation in progress
- 🔄 Affiliate system development in progress

### Installation

The system can be installed on Ubuntu 22.04 using the included install script:

```bash
# Clone the repository
git clone https://github.com/yourusername/moonvpn.git
cd moonvpn

# Make the installation script executable
chmod +x scripts/install.sh

# Run the installation script
./scripts/install.sh
```

The installation script will guide you through the setup process, including:
- Configuring domain name & SSL certificates
- Setting up MySQL database
- Configuring Telegram bot token and group IDs
- Setting up systemd services

### Documentation

For more detailed documentation, see the `/docs` directory.

*(More detailed usage instructions and configuration options will be added in Phase 6)*
