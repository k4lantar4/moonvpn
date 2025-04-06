# Phase 0: Core Infrastructure & Setup

## Overview
This phase focuses on establishing the core infrastructure and basic functionality of the MoonVPN system. The goal is to create a working foundation with Docker environment, FastAPI application, Telegram bot skeleton, database models, and basic integrations.

## Key Objectives
- Set up project directory structure
- Configure Docker environment for development and testing
- Implement basic FastAPI application with health endpoints
- Create Telegram bot skeleton with initial commands
- Define core database models and migrations
- Implement configuration management
- Create basic logging system
- Establish Persian language support infrastructure
- Implement basic 3x-ui panel connection test

## Tasks
The tasks for this phase are tracked in `.cursor/scratchpad.md` with IDs [ID-001] through [ID-013]. Each task has defined dependencies, testing requirements, and documentation needs.

## Implementation Details

### Project Structure
The project follows a modular structure separating the API, bot, core components, integrations, and tests. This organization ensures clean separation of concerns and maintainability.

### Docker Setup
Docker and Docker Compose are used to create a consistent development environment with all required services:
- API service (FastAPI application)
- Bot service (Telegram bot)
- MySQL database
- Redis for caching
- phpMyAdmin for database management

### Core Components
- **Configuration Management**: Environment-based configuration using dotenv
- **Database Connection**: SQLAlchemy ORM with async support
- **Logging System**: Centralized logging with proper levels and formats
- **Security Utilities**: Functions for hashing, JWT generation, and encryption

### Database Models
Core database models include:
- Users
- Roles
- Panels
- Locations
- Plans
- Clients
- Transactions
- Notification Channels

### Persian Language Support
Persian language support is implemented through a centralized message system that ensures consistent tone, proper emoji usage, and marketing flair for all user-facing communications.

## Deliverables
By the end of Phase 0, we will have:
- A runnable Docker environment with all required services
- A basic FastAPI application with health check endpoint
- A Telegram bot skeleton responding to basic commands
- Core database models defined with initial migration
- Basic 3x-ui panel connection test
- Project documentation including README, CHANGELOG, and architecture overview

## Testing
Phase 0 includes setting up the testing framework with pytest and implementing:
- Basic unit tests for core functionality
- Simple integration tests for database connections
- Manual testing of Telegram bot commands

## Next Steps
After completing Phase 0, we will move to Phase 1: User & Panel Foundations, which will build upon this core infrastructure to implement user registration, role-based access, panel management, and more advanced bot functionality. 