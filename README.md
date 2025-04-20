# 🌙 MoonVPN

Telegram-based VPN management system with full integration for 3x-ui panel, user management, payments, and automated notifications.

## 🚀 امکانات اصلی

- 👤 مدیریت سطوح دسترسی (کاربر، ادمین، فروشنده)
- 🔄 ایجاد، تمدید و انتقال اکانت های VPN
- 💳 سیستم کیف پول و پرداخت
- 🏷️ مدیریت تخفیف‌ها
- 📱 رابط کاربری تلگرامی کامل
- 📨 سیستم نوتیفیکیشن برای کاربر و ادمین

## 🛠️ Technologies

- Python 3.12
- Aiogram 3.x
- SQLAlchemy 2.x with Alembic
- MySQL 8.3
- Redis
- Docker & Docker Compose
- Poetry for dependency management
- phpMyAdmin for database administration

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Git for cloning the repository

### Setup Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/moonvpn.git
   cd moonvpn
   ```

2. Copy and configure the environment file:
   ```bash
   cp .env.example .env
   # Edit .env with your preferred text editor
   ```

3. Start the services using the CLI tool:
   ```bash
   ./scripts/moonvpn up
   ```

4. Run database migrations:
   ```bash
   ./scripts/moonvpn migrate
   ```

5. Check the logs:
   ```bash
   ./scripts/moonvpn logs
   ```

## 📋 CLI Usage

MoonVPN comes with a CLI tool for easy management:

```bash
./scripts/moonvpn [command]
```

Available commands:

- `up` - Start all services
- `down` - Stop all services
- `restart` - Restart all services
- `logs [service]` - View logs (app, db, redis, phpmyadmin)
- `migrate` - Run database migrations
- `shell` - Open a shell in the app container
- `status` - Check status of all services
- `build` - Build the app container
- `ps` - List all running containers
- `help` - Show the help message

## 🌐 Web Access

- **phpMyAdmin**: http://localhost:8080
  - Username: root
  - Password: *from MYSQL_ROOT_PASSWORD in .env*

## 📁 Project Structure

The project follows a modular structure as defined in `docs/project-structure.md`:

- `bot/` - Telegram bot components (commands, callbacks, keyboards)
- `core/` - Business logic and services
- `db/` - Database models, repositories, and migrations
- `scripts/` - CLI tools and utilities

## 🧪 Development

For local development, use the `moonvpn` CLI to manage the Docker environment.

Never run commands like `python`, `alembic`, etc. directly - always use the CLI tool to ensure proper containerization.

```bash
# Example: Running tests in the container
./scripts/moonvpn shell
poetry run pytest
```

## 🔐 Security

- Always use environment variables for sensitive information
- Follow the principle of least privilege for user roles
- All services run in isolated Docker containers

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 مشارکت‌کنندگان

- محمدرضا ([@your-github](https://github.com/your-github))
