# Environment Variables Documentation

This document describes all environment variables used in MoonVPN. All variables are prefixed with `MOONVPN_` to avoid conflicts with other applications.

## Database Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `MOONVPN_DB_HOST` | Database host address | `localhost` | No |
| `MOONVPN_DB_PORT` | Database port number | `5432` | No |
| `MOONVPN_DB_NAME` | Database name | `moonvpn` | No |
| `MOONVPN_DB_USER` | Database user | `postgres` | No |
| `MOONVPN_DB_PASSWORD` | Database password | `postgres` | No |
| `MOONVPN_DB_MAX_CONNECTIONS` | Maximum database connections | `100` | No |

## Redis Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `MOONVPN_REDIS_HOST` | Redis host address | `localhost` | No |
| `MOONVPN_REDIS_PORT` | Redis port number | `6379` | No |
| `MOONVPN_REDIS_DB` | Redis database number | `0` | No |

## Panel Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `MOONVPN_PANEL_TYPE` | Panel type (xui/v2ray) | `xui` | Yes |
| `MOONVPN_PANEL_DOMAIN` | Panel domain name | `vpn-panel.example.com` | Yes |
| `MOONVPN_PANEL_PORT` | Panel port number | `2096` | No |
| `MOONVPN_PANEL_USERNAME` | Panel admin username | `admin` | Yes |
| `MOONVPN_PANEL_PASSWORD` | Panel admin password | `admin` | Yes |
| `MOONVPN_PANEL_API_PATH` | Panel API endpoint path | `/panel/api` | No |
| `MOONVPN_PANEL_SSL` | Enable SSL for panel | `false` | No |

## Bot Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `MOONVPN_BOT_TOKEN` | Telegram bot token | - | Yes |
| `MOONVPN_ADMIN_ID` | Telegram admin user ID | `0` | Yes |
| `MOONVPN_ADMIN_USERNAME` | Telegram admin username | `admin` | Yes |

## Payment Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `MOONVPN_CARD_NUMBER` | Payment card number | - | No |
| `MOONVPN_CARD_HOLDER` | Payment card holder name | - | No |
| `MOONVPN_CARD_BANK` | Payment card bank name | - | No |

## Feature Flags

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `MOONVPN_FEATURE_PAYMENTS` | Enable payment features | `true` | No |
| `MOONVPN_FEATURE_ACCOUNT_CREATION` | Enable account creation | `true` | No |
| `MOONVPN_FEATURE_CHANGE_LOCATION` | Enable location change | `true` | No |
| `MOONVPN_FEATURE_TRAFFIC_QUERY` | Enable traffic queries | `true` | No |

## Application Settings

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `MOONVPN_DEBUG` | Enable debug mode | `false` | No |
| `MOONVPN_DEFAULT_LANGUAGE` | Default application language | `fa` | No |
| `MOONVPN_SECRET_KEY` | Django secret key | `your-secret-key-here` | Yes |
| `MOONVPN_ALLOWED_HOSTS` | Comma-separated allowed hosts | `localhost,127.0.0.1` | No |

## Backup Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `MOONVPN_BACKUP_STORAGE_PATH` | Backup storage directory | `/backups` | No |
| `MOONVPN_BACKUP_RETENTION_DAYS` | Days to keep backups | `30` | No |
| `MOONVPN_BACKUP_ENCRYPTION_KEY` | Backup encryption key | - | No |

## Example .env File

```env
# Database Configuration
MOONVPN_DB_HOST=localhost
MOONVPN_DB_PORT=5432
MOONVPN_DB_NAME=moonvpn
MOONVPN_DB_USER=postgres
MOONVPN_DB_PASSWORD=your-secure-password

# Redis Configuration
MOONVPN_REDIS_HOST=localhost
MOONVPN_REDIS_PORT=6379
MOONVPN_REDIS_DB=0

# Panel Configuration
MOONVPN_PANEL_TYPE=xui
MOONVPN_PANEL_DOMAIN=vpn-panel.example.com
MOONVPN_PANEL_PORT=2096
MOONVPN_PANEL_USERNAME=admin
MOONVPN_PANEL_PASSWORD=your-secure-password
MOONVPN_PANEL_SSL=true

# Bot Configuration
MOONVPN_BOT_TOKEN=your-bot-token
MOONVPN_ADMIN_ID=your-telegram-id
MOONVPN_ADMIN_USERNAME=your-username

# Application Settings
MOONVPN_DEBUG=false
MOONVPN_SECRET_KEY=your-secure-secret-key
MOONVPN_ALLOWED_HOSTS=your-domain.com,api.your-domain.com

# Backup Configuration
MOONVPN_BACKUP_STORAGE_PATH=/path/to/backups
MOONVPN_BACKUP_RETENTION_DAYS=30
MOONVPN_BACKUP_ENCRYPTION_KEY=your-encryption-key
``` 