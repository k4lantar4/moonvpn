# MoonVPN System Architecture

## System Overview

MoonVPN is a comprehensive VPN management platform with a Telegram bot interface for end-users and a web dashboard for administrators. The system consists of several interconnected components:

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│   Telegram Bot  │◄────►│  Django Backend │◄────►│ React Dashboard │
└────────┬────────┘      └────────┬────────┘      └─────────────────┘
         │                        │
         │                        │
         ▼                        ▼
┌─────────────────┐      ┌─────────────────┐
│     Redis       │      │   PostgreSQL    │
└─────────────────┘      └─────────────────┘
         ▲                        ▲
         │                        │
         └────────────┬───────────┘
                      │
                      ▼
             ┌─────────────────┐
             │   3x-UI Panel   │
             └─────────────────┘
```

## Component Architecture

### 1. Telegram Bot (`/bot`)

The Telegram bot is built with Python using the python-telegram-bot library. It follows an asynchronous architecture and implements a command-based interface.

**Key Features:**
- User registration and authentication
- VPN subscription purchase flow
- Account status checking
- Server location selection
- Admin commands for system management

**Core Components:**
- `main.py`: Entry point and initialization
- `handlers/`: Command handlers for bot interactions
- `services/`: Business logic services
- `api_client.py`: Client for communicating with the 3x-UI panel
- `models/`: Data models
- `keyboards/`: Telegram inline keyboard definitions
- `i18n/`: Internationalization support

### 2. Backend API (`/backend`)

The backend is built with Django and Django REST Framework, providing RESTful API endpoints for both the bot and admin dashboard.

**Key Features:**
- User management
- VPN account management
- Server management
- Payment processing
- Analytics and reporting

**Core Components:**
- `api/`: API endpoints
- `models/`: Database models
- `services/`: Business logic services
- `v2ray/`: V2Ray/3x-UI panel integration
- `payments/`: Payment processing
- `subscriptions/`: Subscription management

### 3. Frontend Dashboard (`/frontend`)

The admin dashboard is built with React and provides a modern, responsive interface for system management.

**Key Features:**
- User management
- Server monitoring
- Transaction tracking
- Financial reporting
- Discount management
- Bulk messaging

**Core Components:**
- `src/components/`: UI components
- `src/pages/`: Page definitions
- `src/api/`: API client functions
- `src/hooks/`: Custom React hooks
- `src/context/`: React context providers

### 4. Database

PostgreSQL is used as the primary database with the following core models:

- **User**: End users and administrators
- **Server**: VPN server configurations
- **Location**: Geographic locations for servers
- **Account**: VPN accounts linked to users
- **Subscription**: Subscription plans and details
- **Payment**: Payment records
- **Transaction**: Financial transactions
- **Discount**: Discount codes
- **Traffic**: Traffic usage records

### 5. Redis

Redis is used for:
- Caching frequently accessed data
- Session management
- Rate limiting
- Task queues

### 6. 3x-UI Panel Integration

The system integrates with external 3x-UI panels for managing V2Ray/XRay VPN servers:
- API-based integration
- Session-based authentication
- Account creation and management
- Traffic monitoring

## Communication Flow

### 1. User Purchase Flow

1. User initiates `/buy` command in the Telegram bot
2. Bot presents available plans and locations
3. User selects plan and payment method
4. Bot creates pending order in the database
5. User completes payment
6. Bot verifies payment and creates account on the 3x-UI panel
7. Bot sends account details to the user

### 2. Admin Dashboard Flow

1. Admin logs in to the dashboard
2. Dashboard loads data from the backend API
3. Admin performs management actions
4. API processes requests and updates the database
5. Changes are reflected in both the dashboard and bot

## Deployment Architecture

The system is deployed using Docker with the following containers:

1. **Bot**: Telegram bot container
2. **Backend**: Django API container
3. **Frontend**: React dashboard container
4. **DB**: PostgreSQL database container
5. **Redis**: Redis cache container
6. **Nginx**: Web server for reverse proxy

## Security Architecture

- HTTPS for all communications
- JWT authentication for API access
- Role-based access control
- Rate limiting for API endpoints
- Encrypted storage for sensitive data

## Monitoring and Maintenance

- Logging to files and optional Sentry integration
- Health check endpoints
- Backup scripts for database and configurations
- Update mechanisms for system components 