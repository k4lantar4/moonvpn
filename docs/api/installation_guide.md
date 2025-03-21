# Installation Guide

This guide provides detailed instructions for installing and configuring the V2Ray Account Management System on an Ubuntu 22.04 VPS.

## Prerequisites

Before you begin, make sure you have:

- An Ubuntu 22.04 LTS server with root access
- A domain name pointing to your server's IP address (recommended for production)
- A Telegram Bot token (obtain from [@BotFather](https://t.me/BotFather))
- Access to at least one 3x-UI panel

## Installation Options

### Option 1: One-Command Installation (Recommended)

1. SSH into your server:
   ```bash
   ssh root@your_server_ip
   ```

2. Download and run the installation script:
   ```bash
   wget -O install.sh https://raw.githubusercontent.com/k4lantar4/moonvpn/main/install.sh
   chmod +x install.sh
   sudo ./install.sh
   ```

3. Follow the prompts to configure your environment variables.

### Option 2: Manual Installation

1. Update system packages:
   ```bash
   apt update && apt upgrade -y
   ```

2. Install Docker and Docker Compose:
   ```bash
   apt install apt-transport-https ca-certificates curl gnupg lsb-release -y
   curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
   echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
   apt update
   apt install docker-ce docker-ce-cli containerd.io docker-compose-plugin -y
   ```

3. Clone the repository:
   ```bash
   git clone https://github.com/k4lantar4/moonvpn.git /opt/v2ray-bot
   cd /opt/v2ray-bot
   ```

4. Configure environment variables:
   ```bash
   cp .env.example .env
   nano .env  # Edit variables as needed
   ```

5. Start the application:
   ```bash
   docker compose up -d
   ```

## Post-Installation Setup

After installation, you need to:

1. **Set Up Telegram Webhook**
   ```bash
   curl -F "url=https://your_domain_or_ip/webhook" https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook
   ```

2. **Access the Admin Panel**
   - Go to `https://your_domain_or_ip/admin`
   - Log in with the credentials specified in your `.env` file

3. **Configure 3x-UI Panel Integration**
   - In the admin panel, go to "Panel Management"
   - Add your 3x-UI panel information

## Configuration

### Environment Variables

Key environment variables to configure:

| Variable | Description | Example |
|----------|-------------|---------|
| TELEGRAM_BOT_TOKEN | Your Telegram bot token | 1234567890:AAG-abc123def456ghi789jkl |
| ADMIN_USER_IDS | Telegram user IDs of admins | ["123456789","987654321"] |
| XUI_PANEL_URL | URL of your 3x-UI panel | http://your-panel-url:54321 |
| XUI_PANEL_USERNAME | 3x-UI panel username | admin |
| XUI_PANEL_PASSWORD | 3x-UI panel password | your_secure_password |
| ZARINPAL_MERCHANT | Zarinpal merchant ID | your_merchant_id |

## Troubleshooting

### Common Issues

1. **Docker services not starting**
   - Check logs: `docker compose logs -f`
   - Ensure ports are not in use: `netstat -tulpn`

2. **Webhook not working**
   - Verify your domain points to your server
   - Check Nginx logs: `docker compose logs nginx`
   - Confirm SSL is properly configured

3. **3x-UI panel connection issues**
   - Verify panel URL is accessible
   - Check credentials are correct
   - Ensure network allows connection between server and panel

## Updating

To update to the latest version:

```bash
cd /opt/v2ray-bot
git pull
docker compose down
docker compose up -d
```

## Security Recommendations

1. Enable firewall and only allow necessary ports:
   ```bash
   ufw allow 22/tcp
   ufw allow 80/tcp
   ufw allow 443/tcp
   ufw enable
   ```

2. Set up SSL/TLS for secure connections
3. Regularly update your system and the application
4. Use strong passwords for all services 