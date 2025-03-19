# 🌙 MoonVPN Project Blueprint

## 1. Project Overview

MoonVPN is a comprehensive VPN management system with a Telegram bot, web dashboard, and API for managing V2Ray VPN accounts. This project enables selling and managing VPN subscriptions through a Telegram bot and web interface, integrated with a 3x-UI panel server.

## 2. Core Components

### 2.1 Directory Structure
```
moonvpn/
├── backend/         # Django REST API backend
├── bot/             # Telegram bot with Python
├── docker/          # Docker configuration files
├── frontend/        # React.js web dashboard
├── nginx/           # Nginx configuration
├── scripts/         # CLI and utility scripts
├── config/          # Configuration files
├── docs/            # Documentation
├── logs/            # Log files
├── .env             # Environment variables
├── docker-compose.yml  # Docker services definition
├── install.sh       # Installation script
└── moonvpn          # CLI management tool
```

### 2.2 Key Components

#### 2.2.1 Telegram Bot (`/bot`)
- User registration and authentication
- VPN account purchase and management
- Account status and traffic monitoring
- Payment processing
- Admin notifications and management
- Help and support commands

#### 2.2.2 Backend API (`/backend`)
- User management
- VPN server management and connection
- Subscription and payment handling
- Traffic monitoring and quota enforcement
- Integration with 3x-UI panels
- Authentication and authorization

#### 2.2.3 Web Dashboard (`/frontend`)
- Admin login and authentication
- User management
- Server monitoring and configuration
- Subscription and payment oversight
- Traffic and usage analytics
- System settings

#### 2.2.4 Docker Configuration (`/docker`)
- Container definitions for all services
- Volume management
- Network configuration
- Environment variables

#### 2.2.5 CLI Tool (`/scripts/moonvpn`)
- Installation and setup
- Service management (start/stop/restart)
- Configuration and backup management
- Diagnostic tools

## 3. Technical Architecture

### 3.1 Services

- **Bot Service**: Python Telegram bot with handlers and database connections
- **API Service**: Django REST Framework with PostgreSQL database
- **Frontend Service**: React.js with Redux state management
- **Database Service**: PostgreSQL for data persistence
- **Cache Service**: Redis for caching and task queues
- **Web Server**: Nginx for serving frontend and proxying backend
- **SSL Service**: Certbot for SSL certificate management

### 3.2 Communication Flow

1. **User -> Telegram Bot**: Users interact with the Telegram bot
2. **Bot -> API**: Bot communicates with API to manage accounts
3. **API -> 3x-UI Panel**: API connects to VPN panel server to create/manage accounts
4. **Admin -> Web Dashboard**: Admins manage the system via web dashboard
5. **Dashboard -> API**: Dashboard communicates with API for data
6. **API -> Database**: API stores and retrieves data from PostgreSQL

### 3.3 Database Schema

#### 3.3.1 Main Tables
- **Users**: Telegram user info and account details
- **Servers**: VPN server configurations and status
- **Subscriptions**: User subscription plans and details
- **Payments**: Payment records and transaction history
- **VPNAccounts**: Actual VPN account credentials and status
- **Notifications**: System notification settings and logs

## 4. Features

### 4.1 Bot Features
- `/start`: User registration and welcome
- `/buy`: Purchase a subscription plan
- `/account`: View account status and details
- `/status`: Check server status and traffic usage
- `/payment`: Process and confirm payments
- `/support`: Contact support and get help
- `/change_location`: Change VPN server location
- Admin commands for management and monitoring

### 4.2 API Endpoints
- `/api/v1/auth/`: Authentication and user management
- `/api/v1/servers/`: Server management and status
- `/api/v1/subscriptions/`: Subscription plans and user subscriptions
- `/api/v1/payments/`: Payment processing and records
- `/api/v1/vpn/`: VPN account management
- `/api/v1/admin/`: Administrative functions
- `/api/v1/health/`: System health monitoring

### 4.3 Dashboard Sections
- Dashboard overview with key metrics
- User management and details
- Server configuration and monitoring
- Subscription plan management
- Payment history and processing
- System settings and configuration
- Analytics and reports

## 5. Security Measures

- JWT-based authentication
- HTTPS/SSL encryption
- Encrypted storage of sensitive data
- Role-based access control
- Input validation and sanitization
- Rate limiting and brute force protection
- Regular automated backups

## 6. Deployment

### 6.1 Requirements
- Ubuntu 22.04 LTS server
- Domain name with DNS configured
- Telegram Bot token from @BotFather
- 3x-UI panel server credentials

### 6.2 Installation Process
1. Clone repository
2. Configure environment variables
3. Run installation script
4. Set up SSL certificates
5. Configure Telegram webhook
6. Start all services
7. Create admin user
8. Set up notification groups

## 7. Development Guidelines

### 7.1 Coding Standards
- PEP 8 for Python code
- ESLint and Prettier for JavaScript/React
- Conventional commits for version control
- Documentation for all public functions and classes

### 7.2 Testing
- Unit tests for core functionality
- Integration tests for service interactions
- End-to-end tests for critical workflows
- Load testing for performance validation

## 8. Future Enhancements

- Multi-language support
- Additional payment gateways
- More VPN protocols and panels
- Mobile app for administration
- Advanced analytics and reporting
- Affiliate and reseller program 