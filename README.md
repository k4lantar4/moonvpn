# MoonVPN 🌙

A Telegram bot and web dashboard for managing VPN accounts.

## Project Structure

```
moonvpn/
├── app/                    # Main application package
│   ├── api/               # API endpoints and routers
│   ├── bot/               # Telegram bot implementation
│   ├── core/              # Core functionality and configs
│   ├── db/                # Database models and migrations
│   ├── services/          # Business logic services
│   ├── schemas/           # Pydantic schemas
│   └── utils/             # Utility functions
├── docs/                  # Documentation
├── tests/                 # Test files
├── scripts/               # Utility scripts
└── docker/               # Docker configuration
```

## Features

- 🤖 Telegram bot for user interaction
- 🚀 FastAPI backend
- 📊 Admin dashboard
- 🔒 VPN account management
- 💳 Payment processing
- 📈 Server monitoring
- 🌐 Multi-language support

## Tech Stack

- Python 3.9+
- FastAPI
- SQLAlchemy
- PostgreSQL
- Redis
- Docker
- Nginx

## Getting Started

1. Clone the repository:
```bash
git clone https://github.com/yourusername/moonvpn.git
cd moonvpn
```

2. Copy the environment file and configure it:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Start the containers:
```bash
docker-compose up -d
```

## Development

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run migrations:
```bash
alembic upgrade head
```

4. Start the development server:
```bash
uvicorn app.main:app --reload
```

## Testing

Run tests with pytest:
```bash
pytest
```

## Documentation

- API documentation: `/docs`
- Bot documentation: `docs/bot/`

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Database Setup

The project uses Alembic for database migrations. Here are the common database-related commands:

```bash
# Create a new migration
alembic revision -m "description_of_changes"

# Run migrations
alembic upgrade head

# Rollback migrations
alembic downgrade -1

# Show migration history
alembic history

# Show current migration version
alembic current
```

## Prerequisites

- Python 3.8+
- PostgreSQL 13+
- Redis 6+
- Docker (optional)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/moonvpn.git
cd moonvpn
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy the environment file and update the values:
```bash
cp .env.example .env
```

5. Set up the database:
```bash
# Initialize database and run migrations
python -m core.database.setup

# Or without seeding initial data
python -m core.database.setup --no-seed
```

## Development

1. Start the development server:
```bash
uvicorn main:app --reload
```

2. Run tests:
```bash
pytest
```

3. Format code:
```bash
black .
isort .
```

4. Check code style:
```bash
flake8
mypy .
```

## Project Structure

```
moonvpn/
├── alembic.ini           # Alembic configuration
├── core/                 # Core application code
│   ├── database/        # Database models and migrations
│   │   ├── models/     # SQLAlchemy models
│   │   ├── migrations/ # Alembic migrations
│   │   ├── backup.py   # Backup and restore tools
│   │   ├── config.py   # Database configuration
│   │   ├── connection.py # Database connection management
│   │   ├── maintenance.py # Database maintenance tools
│   │   ├── monitor.py  # Database monitoring tools
│   │   └── setup.py    # Database setup and seeding
│   ├── services/        # Business logic
│   ├── api/            # API endpoints
│   └── bot/            # Telegram bot
├── migrations/          # Database migrations
├── tests/              # Test files
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Database Management

### Migrations

The project uses Alembic for database migrations. Here are the common database-related commands:

```bash
# Create a new migration
alembic revision -m "description_of_changes"

# Run migrations
alembic upgrade head

# Rollback migrations
alembic downgrade -1

# Show migration history
alembic history

# Show current migration version
alembic current
```

### Maintenance

The project includes tools for database maintenance:

```bash
# Clean up expired transactions
python -m core.database.maintenance --cleanup-transactions 30

# Clean up failed payments
python -m core.database.maintenance --cleanup-payments 30

# Vacuum the database
python -m core.database.maintenance --vacuum

# Reindex the database
python -m core.database.maintenance --reindex

# Check database health
python -m core.database.maintenance --health-check
```

### Backup and Restore

The project includes tools for database backup and restore:

```bash
# Create a new backup
python -m core.database.backup --backup

# Restore from backup
python -m core.database.backup --restore backups/moonvpn_backup_20240320_100000.sql

# List available backups
python -m core.database.backup --list

# Clean up old backups
python -m core.database.backup --cleanup 30
```

### Monitoring

The project includes a real-time database monitoring tool:

```bash
# Start monitoring with default refresh interval (5 seconds)
python -m core.database.monitor

# Start monitoring with custom refresh interval
python -m core.database.monitor --refresh 10

# Monitor for a specific duration
python -m core.database.monitor --duration 300  # Monitor for 5 minutes
```

The monitoring tool provides:
- Connection statistics (active, idle, waiting connections)
- Table statistics (live tuples, dead tuples)
- Index statistics (scans, tuples read)
- Query statistics (top queries by execution time)

## Development

1. Start the development server:
```bash
uvicorn main:app --reload
```

2. Run tests:
```bash
pytest
```

3. Format code:
```bash
black .
isort .
```

4. Check code style:
```bash
flake8
mypy .
```

## Project Structure

```
moonvpn/
├── alembic.ini           # Alembic configuration
├── core/                 # Core application code
│   ├── database/        # Database models and migrations
│   │   ├── models/     # SQLAlchemy models
│   │   ├── migrations/ # Alembic migrations
│   │   ├── backup.py   # Backup and restore tools
│   │   ├── config.py   # Database configuration
│   │   ├── connection.py # Database connection management
│   │   ├── maintenance.py # Database maintenance tools
│   │   ├── monitor.py  # Database monitoring tools
│   │   └── setup.py    # Database setup and seeding
│   ├── services/        # Business logic
│   ├── api/            # API endpoints
│   └── bot/            # Telegram bot
├── migrations/          # Database migrations
├── tests/              # Test files
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Database Management

### Migrations

The project uses Alembic for database migrations. Here are the common database-related commands:

```bash
# Create a new migration
alembic revision -m "description_of_changes"

# Run migrations
alembic upgrade head

# Rollback migrations
alembic downgrade -1

# Show migration history
alembic history

# Show current migration version
alembic current
```

### Maintenance

The project includes tools for database maintenance:

```bash
# Clean up expired transactions
python -m core.database.maintenance --cleanup-transactions 30

# Clean up failed payments
python -m core.database.maintenance --cleanup-payments 30

# Vacuum the database
python -m core.database.maintenance --vacuum

# Reindex the database
python -m core.database.maintenance --reindex

# Check database health
python -m core.database.maintenance --health-check
```

### Backup and Restore

The project includes tools for database backup and restore:

```bash
# Create a new backup
python -m core.database.backup --backup

# Restore from backup
python -m core.database.backup --restore backups/moonvpn_backup_20240320_100000.sql

# List available backups
python -m core.database.backup --list

# Clean up old backups
python -m core.database.backup --cleanup 30
```

### Monitoring

The project includes a real-time database monitoring tool:

```bash
# Start monitoring with default refresh interval (5 seconds)
python -m core.database.monitor

# Start monitoring with custom refresh interval
python -m core.database.monitor --refresh 10

# Monitor for a specific duration
python -m core.database.monitor --duration 300  # Monitor for 5 minutes
```

The monitoring tool provides:
- Connection statistics (active, idle, waiting connections)
- Table statistics (live tuples, dead tuples)
- Index statistics (scans, tuples read)
- Query statistics (top queries by execution time)
