# Backup System Deployment Guide

## Overview

This guide provides detailed instructions for deploying and configuring the MoonVPN Backup System. The system is designed to be deployed as part of the main MoonVPN application or as a standalone service.

## Prerequisites

### System Requirements
- Python 3.9 or higher
- PostgreSQL 13 or higher
- Redis 6.0 or higher
- Sufficient storage space for backups
- Network access to storage providers

### Dependencies
```bash
# Core dependencies
python-telegram-bot>=20.0
fastapi>=0.68.0
sqlalchemy>=1.4.0
alembic>=1.7.0
apscheduler>=3.8.1
python-jose>=3.3.0
passlib>=1.7.4
aiohttp>=3.8.0
pydantic>=1.9.0

# Storage providers
boto3>=1.26.137  # For S3
azure-storage-blob>=12.14.0  # For Azure
google-cloud-storage>=2.10.0  # For GCS

# Monitoring
prometheus-client>=0.14.0
```

## Installation Steps

### 1. Environment Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Create configuration directory
mkdir -p /etc/moonvpn/backup
```

### 2. Database Setup

```sql
-- Create database
CREATE DATABASE moonvpn_backup;

-- Create user
CREATE USER backup_user WITH PASSWORD 'your_secure_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE moonvpn_backup TO backup_user;
```

### 3. Configuration

Create `/etc/moonvpn/backup/config.py`:
```python
class BackupConfig:
    # Database
    DATABASE_URL = "postgresql://backup_user:your_secure_password@localhost/moonvpn_backup"
    
    # Storage
    STORAGE_PROVIDER = "local"
    LOCAL_STORAGE_PATH = "/var/backups/moonvpn"
    
    # S3 Configuration (if using S3)
    AWS_ACCESS_KEY = "your_access_key"
    AWS_SECRET_KEY = "your_secret_key"
    AWS_REGION = "your_region"
    S3_BUCKET = "your_bucket"
    
    # Azure Configuration (if using Azure)
    AZURE_CONNECTION_STRING = "your_connection_string"
    AZURE_CONTAINER = "your_container"
    
    # GCS Configuration (if using GCS)
    GCS_CREDENTIALS_FILE = "/path/to/credentials.json"
    GCS_BUCKET = "your_bucket"
    
    # Backup Settings
    MAX_BACKUP_SIZE = 1024 * 1024 * 1024  # 1GB
    COMPRESSION_ENABLED = True
    ENCRYPTION_ENABLED = True
    ENCRYPTION_KEY = "your_encryption_key"
    
    # Schedule Settings
    DEFAULT_RETENTION_DAYS = 30
    MAX_CONCURRENT_BACKUPS = 5
    
    # Verification Settings
    VERIFY_AFTER_BACKUP = True
    VERIFICATION_TIMEOUT = 3600  # 1 hour
    
    # Notification Settings
    NOTIFY_ON_SUCCESS = True
    NOTIFY_ON_FAILURE = True
    NOTIFICATION_CHANNELS = ["telegram", "email"]
    
    # Security Settings
    API_KEY = "your_api_key"
    JWT_SECRET = "your_jwt_secret"
    ALLOWED_IPS = ["127.0.0.1"]
    
    # Logging
    LOG_LEVEL = "INFO"
    LOG_FILE = "/var/log/moonvpn/backup.log"
```

### 4. Directory Setup

```bash
# Create required directories
mkdir -p /var/backups/moonvpn
mkdir -p /var/log/moonvpn
mkdir -p /etc/moonvpn/backup/keys

# Set permissions
chown -R moonvpn:moonvpn /var/backups/moonvpn
chown -R moonvpn:moonvpn /var/log/moonvpn
chown -R moonvpn:moonvpn /etc/moonvpn/backup
chmod 700 /etc/moonvpn/backup/keys
```

### 5. Database Migration

```bash
# Run migrations
alembic upgrade head

# Verify migrations
alembic current
```

### 6. Service Setup

Create `/etc/systemd/system/moonvpn-backup.service`:
```ini
[Unit]
Description=MoonVPN Backup Service
After=network.target postgresql.service redis.service

[Service]
User=moonvpn
Group=moonvpn
WorkingDirectory=/opt/moonvpn
Environment=PYTHONPATH=/opt/moonvpn
ExecStart=/opt/moonvpn/venv/bin/python -m app.backup.main
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 7. Service Activation

```bash
# Reload systemd
systemctl daemon-reload

# Enable and start service
systemctl enable moonvpn-backup
systemctl start moonvpn-backup

# Check status
systemctl status moonvpn-backup
```

## Storage Provider Setup

### Local Storage
```bash
# Create backup directories
mkdir -p /var/backups/moonvpn/{full,incremental,differential}
chown -R moonvpn:moonvpn /var/backups/moonvpn
chmod 700 /var/backups/moonvpn
```

### Amazon S3
```bash
# Install AWS CLI
pip install awscli

# Configure AWS credentials
aws configure

# Test S3 access
aws s3 ls s3://your-bucket
```

### Azure Blob Storage
```bash
# Install Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Login to Azure
az login

# Create storage account and container
az storage account create --name <account_name> --resource-group <group_name>
az storage container create --name <container_name> --account-name <account_name>
```

### Google Cloud Storage
```bash
# Install Google Cloud SDK
curl https://sdk.cloud.google.com | bash

# Initialize SDK
gcloud init

# Create service account and download key
gcloud iam service-accounts create backup-service
gcloud projects add-iam-policy-binding <project_id> \
    --member="serviceAccount:backup-service@<project_id>.iam.gserviceaccount.com" \
    --role="roles/storage.admin"
gcloud iam service-accounts keys create /etc/moonvpn/backup/keys/gcs-key.json \
    --iam-account=backup-service@<project_id>.iam.gserviceaccount.com
```

## Monitoring Setup

### Prometheus Configuration
Add to `/etc/prometheus/prometheus.yml`:
```yaml
scrape_configs:
  - job_name: 'moonvpn_backup'
    static_configs:
      - targets: ['localhost:9090']
```

### Grafana Dashboard
1. Import the backup system dashboard (ID: `moonvpn_backup`)
2. Configure data source to point to Prometheus
3. Set up alerting rules

## Security Configuration

### Firewall Rules
```bash
# Allow API access
ufw allow from trusted_ip to any port 8000

# Allow monitoring access
ufw allow from monitoring_ip to any port 9090
```

### SSL/TLS Setup
```bash
# Generate certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/moonvpn/backup/keys/backup.key \
    -out /etc/moonvpn/backup/keys/backup.crt

# Set permissions
chmod 600 /etc/moonvpn/backup/keys/backup.key
chmod 644 /etc/moonvpn/backup/keys/backup.crt
```

## Backup Schedule Setup

### Default Schedules
```sql
-- Full backup weekly
INSERT INTO backup_schedules (
    name, backup_type, cron_expression, retention_days
) VALUES (
    'Weekly Full', 'full', '0 0 * * 0', 90
);

-- Incremental backup daily
INSERT INTO backup_schedules (
    name, backup_type, cron_expression, retention_days
) VALUES (
    'Daily Incremental', 'incremental', '0 0 * * 1-6', 30
);

-- Differential backup every 3 days
INSERT INTO backup_schedules (
    name, backup_type, cron_expression, retention_days
) VALUES (
    'Triday Differential', 'differential', '0 0 */3 * *', 60
);
```

## Verification

### Service Health Check
```bash
# Check service status
systemctl status moonvpn-backup

# Check logs
journalctl -u moonvpn-backup

# Test API
curl -X GET http://localhost:8000/api/v1/backups/health \
    -H "Authorization: Bearer your_api_key"
```

### Backup Verification
```bash
# Verify recent backups
curl -X POST http://localhost:8000/api/v1/backups/verify-all \
    -H "Authorization: Bearer your_api_key"

# Check backup storage
du -sh /var/backups/moonvpn/*
```

## Troubleshooting

### Common Issues

1. **Service Won't Start**
   ```bash
   # Check logs
   journalctl -u moonvpn-backup -n 100
   
   # Check permissions
   ls -la /var/backups/moonvpn
   ls -la /var/log/moonvpn
   ```

2. **Database Connection Issues**
   ```bash
   # Check PostgreSQL status
   systemctl status postgresql
   
   # Test connection
   psql -U backup_user -d moonvpn_backup -h localhost
   ```

3. **Storage Issues**
   ```bash
   # Check disk space
   df -h
   
   # Check inode usage
   df -i
   ```

### Log Analysis
```bash
# Check error logs
grep ERROR /var/log/moonvpn/backup.log

# Check warning logs
grep WARNING /var/log/moonvpn/backup.log

# Monitor logs in real-time
tail -f /var/log/moonvpn/backup.log
```

## Maintenance

### Regular Tasks

1. **Log Rotation**
   Add to `/etc/logrotate.d/moonvpn-backup`:
   ```
   /var/log/moonvpn/backup.log {
       daily
       rotate 14
       compress
       delaycompress
       notifempty
       create 0640 moonvpn moonvpn
       postrotate
           systemctl kill -s USR1 moonvpn-backup
       endscript
   }
   ```

2. **Database Maintenance**
   ```bash
   # Vacuum database
   psql -U backup_user -d moonvpn_backup -c "VACUUM ANALYZE;"
   
   # Check table sizes
   psql -U backup_user -d moonvpn_backup -c "\d+"
   ```

3. **Storage Cleanup**
   ```bash
   # Clean old backups
   curl -X POST http://localhost:8000/api/v1/backups/cleanup \
       -H "Authorization: Bearer your_api_key"
   
   # Verify storage usage
   du -sh /var/backups/moonvpn/*
   ```

## Upgrade Procedure

1. **Backup Current State**
   ```bash
   # Stop service
   systemctl stop moonvpn-backup
   
   # Backup database
   pg_dump -U backup_user moonvpn_backup > backup.sql
   
   # Backup configuration
   cp -r /etc/moonvpn/backup /etc/moonvpn/backup.old
   ```

2. **Update Code**
   ```bash
   # Update code
   cd /opt/moonvpn
   git pull
   
   # Update dependencies
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Run Migrations**
   ```bash
   # Apply database migrations
   alembic upgrade head
   ```

4. **Restart Service**
   ```bash
   # Start service
   systemctl start moonvpn-backup
   
   # Check status
   systemctl status moonvpn-backup
   ```

## Support

For issues and support:
- Check logs: `/var/log/moonvpn/backup.log`
- Contact: support@moonvpn.com
- Documentation: https://docs.moonvpn.com/backup
- GitHub: https://github.com/moonvpn/backup 