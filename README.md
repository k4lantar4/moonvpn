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
