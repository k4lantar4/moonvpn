\# 🚀 MoonVPN - Project Requirements



\> Updated: 2025-04-21 &#x20;

\> Version: 1.1.0 (MVP + Enhanced Payment)



\---



\## 🧭 Overview

MoonVPN is a scalable and modular VPN service management system built on Python, Docker, and Telegram Bot. It allows users to purchase, manage, and use VPN services while enabling admins to control panels, inbounds, plans, clients, and payments. The system is designed for automation and future expansion including reseller support and potential web UI integration.



\---



\## 👥 User Roles



1\. \*\*User\*\* – Can register, view plans, buy services, manage accounts, and check balance.

2\. \*\*Admin\*\* – Manages users, panels, inbounds, orders, payments, and notifications.

3\. \*\*Seller (future)\*\* – Can define custom plans and discounts, track orders, and earn commission.

4\. \*\*SuperAdmin\*\* – Full access to override actions, review logs, and audit systems.



\---



\## 🧩 Core Features



\### 1. User System

\- Role-based registration via Telegram bot

\- Wallet balance tracking (transactional)

\- User profile and account history



\### 2. Plan System

\- Support for fixed and dynamic plans (volume/duration based)

\- Per-location plan assignment

\- Discounts (percentage, fixed, limited use, expiry)

\- Future-ready for seller-defined plans



\### 3. Panel Management

\- Add/edit/delete 3x-ui panels (by Admin only)

\- Sync panel health, stats, and inbounds

\- Restart panel core (optional for troubleshooting)



\### 4. Inbound Management

\- Sync inbounds from each panel

\- Store complete specs in DB (port, protocol, sniffing, tag, max clients)

\- Internal unique ID for each inbound (mapped to panel-specific ID)



\### 5. Client Account Management

\- Create clients on selected inbound

\- Auto-generate names (e.g., \`FR-Moonvpn-1001\`, with location suffixes)

\- Store config URL (vmess/vless) and QR

\- Ability to reset, renew, or move to a new location (inbound switch logic)

\- Track traffic usage and expiration



\### 6. Payment System

\- Wallet system (recharge and use)

\- Card-to-card payments with manual receipt confirmation

\- Auto-generated transaction tracking code

\- Multi-card support with intelligent card rotation

\- Discount support and internal balance refund logic

\- Admin approval via inline buttons



\### 7. Receipt & Card System

\- Bank card registry for manual transfers

\- Each card linked to specific admin and Telegram channel

\- Receipts (text/image/both) logged and sent to designated channels

\- Status updates to user after submission (pending/approved/rejected/expired)

\- Superadmin oversight and centralized audit channel

\- Future-ready for OCR and AI-based validation



\### 8. Notification System

\- Notify users: expiration, low balance, successful purchase

\- Notify admins: receipt submission, new order, failed sync

\- Queue support & summary stats for bulk sends

\- Telegram and future-ready for other channels



\### 9. Order System

\- Multi-stage order status: pending → confirmed → fulfilled → failed → expired

\- Order tracking (volume, expiry, client UUID, receipt ID)

\- Linked to discount usage and transaction record



\### 10. Location Logic

\- Human-readable name (e.g., Germany 🇩🇪)

\- Stored in DB (without requiring separate location table unless extended later)

\- Used to group inbounds and filter plans



\### 11. Admin Tools

\- Add panels and inbounds

\- Monitor panel health

\- Send mass or targeted notifications

\- Approve payments and manage receipts

\- View logs and override actions (SuperAdmin)



\---



\## 🛠️ Technology Stack

| Component     | Stack                                 |
|---------------|---------------------------------------|
| Language      | Python 3.12                           |
| Bot Framework | Aiogram 3.x                           |
| ORM           | SQLAlchemy 2.x                        |
| Migrations    | Alembic                               |
| HTTP Client   | aiohttp                               |
| DB            | MySQL 8.x with aiomysql driver        |
| Caching       | Redis (optional)                      |
| Deployment    | Docker, Docker Compose                |
| Dev Tools     | Poetry, Black, Pytest, GitHub Actions |

### Database Driver Notes
- The project uses `aiomysql` as the database driver for async/await support
- All service methods must be async and use await with database operations
- Alembic migrations automatically convert to pymysql for synchronous operation

## ✅ MVP Milestones



1\. Panel & inbound sync

2\. User wallet & registration

3\. Plan browsing and purchase (via wallet or card)

4\. Client creation in panel

5\. Delivery of config + QR

6\. Admin receipt approval via Telegram

7\. Notifications (basic)

8\. Full receipt management for manual card payments

9\. Internal ID tracking for transactions and audit



\---



\## 🔮 Future Features



\- Seller/reseller support (panel assignments, custom plans)

\- In-app analytics and admin dashboard

\- Web UI or RESTful API

\- Telegram-native subscription renewal system

\- User support requests and reporting tools

\- OCR receipt parsing

\- Admin commission reporting system



\---



\## 📁 References

\- \`docs/project-structure.md\`

\- \`docs/database-structure.md\`

\- \`docs/project-relationships.md\`


