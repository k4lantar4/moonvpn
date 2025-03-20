# Database Migrations

This directory contains the database migration scripts for the MoonVPN project using Alembic.

## Directory Structure

```
migrations/
├── README.md           # This file
├── alembic.ini        # Alembic configuration file
├── env.py             # Alembic environment configuration
├── script.py.mako     # Migration script template
└── versions/          # Migration version files
    └── 001_initial.py # Initial migration
```

## Usage

### Creating a New Migration

To create a new migration:

```bash
# Generate a new migration
alembic revision -m "description_of_changes"

# Generate a new migration with autogenerate
alembic revision --autogenerate -m "description_of_changes"
```

### Running Migrations

To run migrations:

```bash
# Upgrade to the latest version
alembic upgrade head

# Upgrade to a specific version
alembic upgrade 001

# Downgrade one version
alembic downgrade -1

# Downgrade to a specific version
alembic downgrade 001
```

### Checking Migration Status

To check the current migration status:

```bash
# Show current version
alembic current

# Show migration history
alembic history

# Show migration history with details
alembic history --verbose
```

## Best Practices

1. Always review auto-generated migrations before applying them
2. Test migrations in a development environment first
3. Back up your database before running migrations in production
4. Keep migration files in version control
5. Use meaningful names for migration files
6. Include both upgrade and downgrade paths
7. Document any manual steps required in the migration comments

## Troubleshooting

If you encounter issues:

1. Check the database connection settings in `alembic.ini`
2. Verify that all models are imported in `env.py`
3. Ensure the database user has sufficient privileges
4. Check the migration history for any failed migrations
5. Review the logs for detailed error messages

## Adding New Models

When adding new models:

1. Create the model in the appropriate file under `core/database/models/`
2. Import the model in `env.py`
3. Generate a new migration using `alembic revision --autogenerate`
4. Review the generated migration file
5. Apply the migration using `alembic upgrade head` 