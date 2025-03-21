# MoonVPN API

A FastAPI-based REST API for the MoonVPN service.

## Features

- User authentication and authorization
- JWT token-based security
- Password reset functionality
- Email verification
- Database integration with SQLAlchemy
- CORS support
- API documentation with OpenAPI/Swagger

## Prerequisites

- Python 3.8+
- SQLite (or any other supported database)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/moonvpn.git
cd moonvpn
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory with the following variables:
```env
SECRET_KEY=your-secret-key-here
SQLALCHEMY_DATABASE_URI=sqlite:///./moonvpn.db
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-specific-password
```

## Running the Application

1. Start the development server:
```bash
uvicorn main:app --reload
```

2. Access the API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Authentication

- `POST /api/v1/auth/login` - Login user
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/password-reset` - Request password reset
- `POST /api/v1/auth/password-reset/confirm` - Confirm password reset
- `POST /api/v1/auth/password-change` - Change user password
- `POST /api/v1/auth/verify-email` - Verify user email
- `POST /api/v1/auth/refresh-token` - Refresh access token

## Development

### Project Structure

```
moonvpn/
├── api/
│   └── v1/
│       └── endpoints/
│           └── auth.py
├── core/
│   ├── config.py
│   ├── database/
│   │   ├── models/
│   │   └── session.py
│   └── schemas/
│       └── auth.py
├── main.py
├── requirements.txt
└── README.md
```

### Running Tests

```bash
pytest
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

# MoonVPN Management Scripts

This directory contains various management scripts for MoonVPN, each designed to handle specific aspects of the system. All scripts support Persian language output and provide comprehensive functionality for system management.

## Available Scripts

### 1. Main CLI (`moonvpn`)
The main command-line interface for MoonVPN management.

```bash
./moonvpn [command] [options]
```

Commands:
- `install`: Install MoonVPN
- `update`: Update MoonVPN
- `status`: Check system status
- `logs`: View system logs
- `backup`: Manage backups
- `ssl`: Manage SSL certificates
- `domain`: Manage domains
- `config`: Manage configurations
- `service`: Manage services
- `firewall`: Manage firewall
- `monitoring`: Manage monitoring
- `security`: Manage security
- `maintenance`: Perform maintenance tasks

### 2. Backup Management (`backup.sh`)
Manages system backups and restorations.

```bash
./backup.sh [command] [options]
```

Commands:
- `create`: Create a new backup
- `restore`: Restore from a backup
- `list`: List available backups
- `delete`: Delete a backup

### 3. SSL Management (`ssl.sh`)
Manages SSL certificates and security.

```bash
./ssl.sh [command] [options]
```

Commands:
- `install`: Install SSL certificate
- `renew`: Renew SSL certificate
- `status`: Check SSL status

### 4. Domain Management (`domain.sh`)
Manages domain configurations.

```bash
./domain.sh [command] [options]
```

Commands:
- `add`: Add a new domain
- `remove`: Remove a domain
- `list`: List configured domains

### 5. Configuration Management (`config.sh`)
Manages system configurations.

```bash
./config.sh [command] [options]
```

Commands:
- `show`: Show current configuration
- `edit`: Edit configuration
- `reset`: Reset to default configuration

### 6. Firewall Management (`firewall.sh`)
Manages system firewall rules.

```bash
./firewall.sh [command] [options]
```

Commands:
- `enable`: Enable firewall
- `disable`: Disable firewall
- `rules`: Manage firewall rules
- `status`: Check firewall status

### 7. Monitoring Management (`monitoring.sh`)
Manages system monitoring.

```bash
./monitoring.sh [command] [options]
```

Commands:
- `metrics`: Show system metrics
- `alerts`: Manage monitoring alerts
- `dashboard`: Open monitoring dashboard

### 8. Security Management (`security.sh`)
Manages system security.

```bash
./security.sh [command] [options]
```

Commands:
- `audit`: Perform security audit
- `update`: Update security measures
- `report`: Generate security report

### 9. Maintenance Management (`maintenance.sh`)
Performs system maintenance tasks.

```bash
./maintenance.sh [command] [options]
```

Commands:
- `cleanup`: Clean up system resources
- `optimize`: Optimize system performance
- `health`: Check system health
- `report`: Generate maintenance report

## Usage Examples

1. Check system status:
```bash
./moonvpn status
```

2. Create a backup:
```bash
./backup.sh create
```

3. Install SSL certificate:
```bash
./ssl.sh install
```

4. Add a new domain:
```bash
./domain.sh add example.com
```

5. Show current configuration:
```bash
./config.sh show
```

6. Enable firewall:
```bash
./firewall.sh enable
```

7. View system metrics:
```bash
./monitoring.sh metrics
```

8. Perform security audit:
```bash
./security.sh audit
```

9. Optimize system:
```bash
./maintenance.sh optimize
```

## Requirements

- Linux/Unix operating system
- Docker and Docker Compose installed
- Root privileges for most operations
- Persian language support (UTF-8)

## Notes

- All scripts require root privileges to run
- Backup files are stored in `/var/backups/moonvpn`
- Reports are stored in `reports/` directory
- Logs are stored in `/var/log/moonvpn`
- Configuration files are stored in `/etc/moonvpn`

## Support

For support and issues, please contact the MoonVPN team or refer to the documentation.
