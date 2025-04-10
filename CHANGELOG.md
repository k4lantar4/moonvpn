# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Persian language support infrastructure
  - Added i18n module for handling translations
  - Created language selection command and handlers
  - Added language preference to user model
  - Added Persian and English translation files
  - Added language selection button to main menu
- `RoleRepository` to fetch roles dynamically.

### Changed
- Updated bot's main menu to include language selection
- Improved user model to match database schema
- Enhanced bot's response system to support multiple languages
- **Schema Sync:** Refactored all SQLAlchemy models (`core/database/models/*`) to use Mapped/mapped_column syntax and aligned default values, constraints, and relationships with the `moonvpn_db.sql` schema.
- **Alembic:** Generated and successfully applied migration `680e56ec8ff0` to update the database schema.
- **CLI Script (`scripts/moonvpn.sh`):** Fixed argument parsing for the `revision` command.
- **Seed Scripts:** Removed internal `session.commit()` calls from `seed_plans.py`, `seed_settings.py`, and `seed_notification_channels.py` to allow central commit in `seed_all.py`.

### Fixed
- Database connection and Redis issues
- Bot's health check implementation
- API service version endpoint
- **Default User Role:** Corrected user registration logic (`UserService`, `handle_start`) to dynamically fetch the 'USER' role ID by name using `RoleRepository` instead of relying on a hardcoded ID (like 1), preventing incorrect role assignments.

## [0.2.1] - YYYY-MM-DD # Update Date
### Changed
- **Refactoring Phase 1:** Completed major refactoring tasks:
  - Removed obsolete API service components (`api/` directory, `ApiClient`, etc.).
  - Consolidated service logic into `bot/services/`.
  - Refactored handlers in `bot/handlers/` to use new services directly.
  - Cleaned up `core/` directory structure.
  - Verified database setup (`session.py`, repositories).
  - Verified panel integration client (`integrations/panels/client.py`).
- **CLI Script (`scripts/moonvpn.sh`):** Updated to work with the bot-only architecture, executing commands like migrations and tests within the `moonvpn_bot` container.
- **Project Structure:** Removed unnecessary files/directories (`multiple`, `core/monitoring`, `core/services`) to align with defined architecture.
- **Documentation:** Updated `ARCHITECTURE.md` to reflect the simplified bot-centric architecture.

## [0.0.3] - 2024-03-19
### Added
- Enhanced configuration management in `config.py`
  - Added comprehensive settings validation
  - Implemented environment detection
  - Added Persian comments for clarity
  - Added new configuration options for Redis, CORS, rate limiting
  - Added monitoring and system limits configuration
- Improved database connection handling in `database.py`
  - Added optimized connection settings
  - Implemented MySQL event listeners for timezone and strict mode
  - Added context manager for session management
  - Integrated Redis with connection pooling
  - Added utility functions for connection checks
  - Implemented proper error handling
- Comprehensive logging system in `logging.py`
  - Added colored console output with detailed formatting
  - Implemented rotating file logs for different environments
  - Added Telegram channel integration for critical errors
  - Created environment-specific log directories
  - Added proper log filtering for third-party libraries
  - Added utility functions for easy logger access
- Docker environment setup
  - Created Dockerfile.api and Dockerfile.bot with multi-stage builds
  - Created docker-compose.yml with all required services
  - Added .dockerignore for better builds
  - Created database initialization script (init.sql)
  - Created start.sh script for easy deployment
  - Added health checks for all services
  - Configured proper networking and volumes
  - Set up phpMyAdmin for database management

### Changed
- Updated task tracking in `scratchpad.md`
  - Marked tasks ID-003, ID-006, ID-009, and ID-012 as completed
  - Added detailed progress notes for completed tasks

## [0.0.2] - 2024-03-19
### Added
- Created `docs/phases/PHASE-0/overview.md` with detailed phase documentation
- Added `ARCHITECTURE.md` with comprehensive system design documentation
- Enhanced task tracking in `.cursor/scratchpad.md`
- Created initial logging system structure

### Changed
- Updated project documentation structure
- Improved task organization and tracking

## [0.0.1] - 2024-03-19
### Added
- Initial project skeleton
- Basic file structure
- Core configuration files
- Documentation setup
  - README.md
  - project-requirements.md
  - .cursor/scratchpad.md

[Unreleased]: https://github.com/yourusername/moonvpn/compare/v0.0.3...HEAD
[0.0.3]: https://github.com/yourusername/moonvpn/compare/v0.0.2...v0.0.3
[0.0.2]: https://github.com/yourusername/moonvpn/compare/v0.0.1...v0.0.2
[0.0.1]: https://github.com/yourusername/moonvpn/releases/tag/v0.0.1 