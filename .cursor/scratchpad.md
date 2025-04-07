*This scratchpad file serves as a phase-specific task tracker and implementation planner. The Mode System on Line 1 is critical and must never be deleted. It defines two core modes: Implementation Type for new feature development and Bug Fix Type for issue resolution. Each mode requires specific documentation formats, confidence tracking, and completion criteria. Use "plan" trigger for planning phase (🎯) and "agent" trigger for execution phase (⚡) after reaching 95% confidence. Follow strict phase management with clear documentation transfer process.*

`MODE SYSTEM TYPES (DO NOT DELETE!):
1. Implementation Type (New Features):
   - Trigger: User requests new implementation
   - Format: MODE: Implementation, FOCUS: New functionality
   - Requirements: Detailed planning, architecture review, documentation
   - Process: Plan mode (🎯) → 95% confidence → Agent mode (⚡)

2. Bug Fix Type (Issue Resolution):
   - Trigger: User reports bug/issue
   - Format: MODE: Bug Fix, FOCUS: Issue resolution
   - Requirements: Problem diagnosis, root cause analysis, solution verification
   - Process: Plan mode (🎯) → Chain of thought analysis → Agent mode (⚡)

Cross-reference with @memories.md and @lessons-learned.md for context and best practices.`

# Mode: PLAN 🎯
MODE: Implementation, FOCUS: Project Initialization & Phase 0 Setup
Confidence: 95%
Current Phase: PHASE-0
Status: Active
Last Updated: v0.1.0

# Phase Tracking

## Phase 0: Core Infrastructure & Setup (~2 weeks)
Status: In Progress
Phase Completion Criteria:
- [X] Docker environment fully configured and tested
- [X] Database schema properly initialized
- [X] Core API and Bot respond to basic requests
- [X] Persian language support implemented
- [ ] Test coverage meets minimum requirements
- [X] Documentation updated
- [X] All Phase 0 tasks completed and tested

## Current Status Summary (v0.1.0)

Completed Tasks:
1. [ID-001] ✅ Project directory structure
2. [ID-002] ✅ FastAPI application skeleton
3. [ID-003] ✅ Telegram Bot skeleton
4. [ID-004] ✅ Database Models & Alembic
5. [ID-004-1] ✅ Update existing database models
6. [ID-004-2] ✅ Create new database models
7. [ID-005] ✅ Environment configuration
8. [ID-006] ✅ Docker environment
9. [ID-007] ✅ 3x-ui panel connection
10. [ID-008] ✅ MoonVPN command
11. [ID-009] ✅ Core config & database
12. [ID-010] ✅ Persian language support
13. [ID-011] ✅ Notification channels
14. [ID-012] ✅ Logging system

Next Priority Tasks:
1. [ID-013] Test framework setup (High)
2. [ID-014] Refine panel connection implementation (Medium)
3. [ID-015] Create panel service layer (Medium)

Infrastructure Status:
- Docker Environment: ✅ Configured and healthy
- Database: ✅ Initialized with required tables
- API Service: ✅ Running and healthy
- Bot Service: ✅ Running and healthy (Verified with test message)
- Redis: ✅ Running and healthy
- phpMyAdmin: ✅ Accessible and functional
- Language Support: ✅ Persian and English implemented
- Telegram Bot: ✅ Responding to commands and messages
- Panel Connection: ✅ Basic connectivity and management implemented
- Notification System: ✅ Channel-based notifications implemented
- CLI Tool: ✅ MoonVPN command implemented for service management
- Healthcheck: ✅ System health monitoring implemented
- Backup System: ✅ Automated backup functionality implemented

Known Issues:
- Test coverage needs to be implemented
- Panel service layer needs refinement
- Client management needs to be improved

Next Steps:
1. Set up test framework and implement tests [ID-013]
   - Create pytest configuration
   - Set up test database fixtures
   - Implement unit tests for models and services
   - Add integration tests for API endpoints
   - Set up CI pipeline for automated testing

2. Refine panel connection implementation [ID-014]
   - Improve error handling and connection reliability
   - Add support for additional panel operations
   - Implement better credential management
   - Add comprehensive logging

3. Create panel service layer [ID-015]
   - Create PanelService for unified panel management
   - Implement database models for panels
   - Add encryption for panel credentials
   - Create CRUD operations for panels
   - Implement panel selection logic

# شناسایی تناقضات و مشکلات پروژه

## تناقضات بین الزامات و پیاده‌سازی

1. **[ID-007] پیاده‌سازی اتصال به پنل 3x-ui:**
   - **مشکل**: پیاده‌سازی فعلی در `integrations/panels/client.py` برخی از اندپوینت‌های API پنل 3x-ui را پوشش می‌دهد، اما ساختار آن با معماری سرویس‌محور پروژه همخوانی ندارد
   - **راه‌حل**: نیاز به ایجاد لایه سرویس مناسب در `api/services/panel_service.py` است
   - **اولویت**: بالا

2. **عدم پیاده‌سازی سرویس‌های کسب و کار:**
   - **مشکل**: فایل‌های `api/services.py` و `api/dependencies.py` خالی هستند
   - **راه‌حل**: پیاده‌سازی سرویس‌های مورد نیاز برای هر بخش طبق معماری پروژه
   - **اولویت**: متوسط

3. **عدم تکمیل سیستم اطلاع‌رسانی کانال‌ها (تسک [ID-011]):**
   - **مشکل**: فایل `bot/channels.py` وجود دارد اما خالی است
   - **راه‌حل**: پیاده‌سازی کلاس NotificationManager و سیستم اطلاع‌رسانی طبق نیازمندی‌ها
   - **اولویت**: متوسط

4. **عدم پیاده‌سازی دستور moonvpn (تسک [ID-008]):**
   - **مشکل**: اسکریپت مدیریت داکر هنوز پیاده‌سازی نشده است
   - **راه‌حل**: ایجاد اسکریپت مناسب در دایرکتوری `scripts/`
   - **اولویت**: متوسط

5. **عدم پیاده‌سازی چارچوب تست (تسک [ID-013]):**
   - **مشکل**: دایرکتوری `tests/` وجود دارد اما خالی است
   - **راه‌حل**: پیاده‌سازی تست‌های واحد و یکپارچگی با استفاده از pytest
   - **اولویت**: بالا

6. **نقص در امنیت و رمزنگاری:**
   - **مشکل**: فایل `core/security.py` وجود دارد اما خالی است و رمزنگاری اطلاعات حساس پنل پیاده‌سازی نشده است
   - **راه‌حل**: پیاده‌سازی رمزنگاری برای اطلاعات حساس و سیستم JWT
   - **اولویت**: بالا

7. **عدم پیاده‌سازی کش:**
   - **مشکل**: فایل `core/cache.py` خالی است
   - **راه‌حل**: پیاده‌سازی مدیریت کش با استفاده از Redis
   - **اولویت**: متوسط

## تسک‌های جدید برای اصلاح پروژه

### [ID-014] اصلاح ساختار پیاده‌سازی کلاینت پنل
Status: [ ] Priority: High
Dependencies: ID-007
Requirements Reference: project-requirements.md#3.1-Panel-Management, project-requirements.md#10.3x-ui-Panel-API-Integration
Expected Completion: TBD
Progress Notes:
- [v0.0.9] شناسایی مشکلات ساختاری در پیاده‌سازی کلاینت پنل
- [v0.0.9] تعریف تسک جدید برای اصلاح مطابق مستندات رسمی 3x-ui

#### زیرتسک‌ها:
1. بازبینی و اصلاح کلاس `XuiPanelClient` برای پوشش کامل API پنل 3x-ui
2. اصلاح پارامترهای متد برای تطبیق کامل با API رسمی
3. پیاده‌سازی اندپوینت‌های نیازمند پیاده‌سازی طبق مستندات رسمی

### [ID-015] ایجاد لایه سرویس برای مدیریت پنل
Status: [ ] Priority: High
Dependencies: ID-007, ID-014
Requirements Reference: project-requirements.md#3.1-Panel-Management
Expected Completion: TBD
Progress Notes:
- [v0.0.9] شناسایی نیاز به لایه سرویس جداگانه برای مدیریت پنل

#### زیرتسک‌ها:
1. ایجاد کلاس `PanelService` در `api/services/panel_service.py`
2. پیاده‌سازی متدهای مدیریت پنل (CRUD)
3. پیاده‌سازی الگوریتم انتخاب پنل برای تخصیص کاربر
4. پیاده‌سازی مکانیزم بررسی سلامت پنل‌ها
5. پیاده‌سازی مدیریت چندین پنل به صورت یکپارچه

### [ID-016] پیاده‌سازی امنیت و رمزنگاری
Status: [ ] Priority: High
Dependencies: ID-009
Requirements Reference: project-requirements.md#3.9-Backup-and-Security
Expected Completion: TBD
Progress Notes:
- [v0.0.9] شناسایی نیاز به پیاده‌سازی سیستم امنیتی

#### زیرتسک‌ها:
1. پیاده‌سازی رمزنگاری اطلاعات حساس در `core/security.py`
2. پیاده‌سازی سیستم JWT برای احراز هویت API
3. پیاده‌سازی هش کردن رمزهای عبور
4. پیاده‌سازی محدودیت نرخ (Rate Limiting) با استفاده از Redis

### [ID-017] تکمیل پیاده‌سازی سیستم اطلاع‌رسانی کانال‌ها
Status: [X] Priority: Medium
Dependencies: ID-003, ID-010
Requirements Reference: project-requirements.md#3.3-Channel-Based-Notification-System
Expected Completion: Completed
Progress Notes:
- [v0.0.9] شناسایی ناتمام بودن سیستم اطلاع‌رسانی کانال‌ها
- [v0.1.0] پیاده‌سازی کامل کلاس NotificationManager و سیستم قالب‌ها
- [v0.1.0] اضافه کردن پشتیبانی از کانال‌های مختلف و سطوح اولویت
- [v0.1.0] پیاده‌سازی دکمه‌های تعاملی و پیام‌های چندرسانه‌ای
- [v0.1.0] اضافه کردن پشتیبانی از زبان فارسی و ایموجی‌ها

### [ID-018] پیاده‌سازی چارچوب تست
Status: [ ] Priority: High
Dependencies: ID-002, ID-003, ID-004, ID-007
Requirements Reference: project-requirements.md#6-Testing-Strategy
Expected Completion: TBD
Progress Notes:
- [v0.0.9] شناسایی نیاز به پیاده‌سازی چارچوب تست

#### زیرتسک‌ها:
1. راه‌اندازی pytest و پیکربندی آن
2. پیاده‌سازی فیکسچرهای تست برای پایگاه داده
3. پیاده‌سازی تست‌های واحد برای سرویس‌های اصلی
4. پیاده‌سازی تست‌های یکپارچگی برای اندپوینت‌های API
5. پیاده‌سازی تست‌های اتصال به پنل 3x-ui

### [ID-019] بهبود و تکمیل مستندات
Status: [ ] Priority: Medium
Dependencies: ID-001, ID-005, ID-008, ID-009, ID-010, ID-011
Requirements Reference: project-requirements.md#5-Documentation
Expected Completion: TBD
Progress Notes:
- [v0.1.0] شناسایی نیاز به بهبود و تکمیل مستندات پروژه

#### زیرتسک‌ها:
1. به‌روزرسانی README.md با دستورالعمل‌های نصب و راه‌اندازی کامل
2. ایجاد ARCHITECTURE.md برای توضیح معماری سیستم
3. ایجاد API.md برای مستندسازی API‌های سیستم
4. بهبود توضیحات داخل کد (inline comments) در همه فایل‌ها
5. ایجاد راهنمای کاربری برای ربات تلگرام
6. ایجاد راهنمای مدیریت سیستم برای ادمین‌ها
7. ایجاد مستندات فنی برای توسعه‌دهندگان

### [ID-020] گسترش پوشش تست و ارتقای کیفیت کد
Status: [ ] Priority: High
Dependencies: ID-018
Requirements Reference: project-requirements.md#6-Testing-Strategy
Expected Completion: TBD
Progress Notes:
- [v0.1.0] شناسایی نیاز به گسترش پوشش تست و ارتقای کیفیت کد

#### زیرتسک‌ها:
1. افزودن لینترها (flake8, pylint) و فرمترها (black) به پروژه
2. پیاده‌سازی CI/CD برای اجرای خودکار تست‌ها و لینترها
3. افزایش پوشش تست تا حداقل 80% برای کدهای اصلی
4. پیاده‌سازی آزمون بار (load testing) برای API
5. اضافه کردن تست‌های امنیتی برای شناسایی آسیب‌پذیری‌ها
6. پیاده‌سازی تست‌های جامع برای ربات تلگرام و اینترفیس‌های کاربری

## برنامه اجرایی

1. ابتدا تسک‌های با اولویت بالا را اجرا کنید:
   - [ID-014] اصلاح ساختار پیاده‌سازی کلاینت پنل
   - [ID-015] ایجاد لایه سرویس برای مدیریت پنل
   - [ID-016] پیاده‌سازی امنیت و رمزنگاری
   - [ID-018] پیاده‌سازی چارچوب تست

2. سپس به تسک‌های با اولویت متوسط بپردازید:
   - [ID-017] تکمیل پیاده‌سازی سیستم اطلاع‌رسانی کانال‌ها
   - [ID-008] پیاده‌سازی دستور moonvpn
   
3. پس از تکمیل هر تسک، بررسی کاملی انجام دهید تا از تطابق با نیازمندی‌های پروژه اطمینان حاصل شود

4. مستندات را به‌روز کنید و تغییرات را در CHANGELOG.md ثبت کنید

# Tasks

## Core Infrastructure Tasks

[ID-001] Setup project directory structure based on project-requirements.md
Status: [X] Priority: High
Dependencies: None
Requirements Reference: project-requirements.md#2-Core-Technologies-&-Architecture
Expected Completion: Completed
Testing Requirements:
- Unit tests required: No
- Integration tests required: No
- E2E tests required: No
Documentation Requirements:
- API documentation needed: No
- User guide updates needed: No
- System architecture updates needed: Yes
Progress Notes:
- [v0.0.1] Initial task definition.
- [v0.0.2] Directory structure confirmed against project-requirements.md.

[ID-002] Initialize FastAPI application skeleton (`api/main.py`, basic structure)
Status: [X] Priority: High
Dependencies: ID-001, ID-009, ID-010
Requirements Reference: project-requirements.md#2-Core-Technologies-&-Architecture
Expected Completion: Completed
Testing Requirements:
- Unit tests required: Yes
- Integration tests required: No
- E2E tests required: No
Documentation Requirements:
- API documentation needed: Yes (Basic Swagger/ReDoc)
- User guide updates needed: No
- System architecture updates needed: No
Progress Notes:
- [v0.0.3] Starting implementation.
- [v0.0.4] Implemented basic app, logging setup, and /ping endpoint.

[ID-003] Initialize Telegram Bot skeleton (`bot/main.py`, basic `/start` handler)
Status: [X] Priority: High
Dependencies: ID-001, ID-009
Requirements Reference: project-requirements.md#3.2-Telegram-Bot-Interface
Expected Completion: Completed
Testing Requirements:
- Unit tests required: Yes
- Integration tests required: No
- E2E tests required: Yes
Documentation Requirements:
- API documentation needed: No
- User guide updates needed: Yes
- System architecture updates needed: No
Progress Notes:
- [v0.0.1] Initial task definition.
- [v0.0.4] Implemented basic polling bot with /start, /help, echo handlers and sample keyboard.

[ID-004] Define core Database Models (`api/models.py`) & Setup Alembic
Status: [X] Priority: High
Dependencies: ID-001, ID-009
Requirements Reference: project-requirements.md#2-Core-Technologies-&-Architecture
Expected Completion: Completed
Testing Requirements:
- Unit tests required: Yes
- Integration tests required: Yes
- E2E tests required: No
Documentation Requirements:
- API documentation needed: Yes
- User guide updates needed: No
- System architecture updates needed: Yes
Progress Notes:
- [v0.0.1] Initial task definition.
- [v0.0.6] Initial models created: User, Role, Panel, Location
- [v0.0.7] All models completed and migrated to database
- [v0.0.7] Database schema fully implemented according to requirements

[ID-004-1] Update existing database models with new fields
Status: [X] Priority: High
Dependencies: ID-004
Requirements Reference: project-requirements.md#8-Database-Schema
Expected Completion: Completed
Testing Requirements:
- Unit tests required: Yes
- Integration tests required: Yes
- E2E tests required: No
Documentation Requirements:
- API documentation needed: Yes
- User guide updates needed: No
- System architecture updates needed: Yes
Progress Notes:
- [v0.0.7] Task created following project-requirements.md review and database schema update
- [v0.0.7] Updated Location model with inbound management fields
- [v0.0.7] Updated Role model with is_admin and is_seller fields
- [v0.0.7] Removed unused fields from Panel model
- [v0.0.7] Created and executed Alembic migration

[ID-004-2] Create new database models for core functionality
Status: [X] Priority: High
Dependencies: ID-004, ID-004-1
Requirements Reference: project-requirements.md#8-Database-Schema
Expected Completion: Completed
Testing Requirements:
- Unit tests required: Yes
- Integration tests required: Yes
- E2E tests required: No
Documentation Requirements:
- API documentation needed: Yes
- User guide updates needed: No
- System architecture updates needed: Yes
Progress Notes:
- [v0.0.7] Task created following project-requirements.md review and database schema update
- [v0.0.7] Implemented all required models: PlanCategory, Plan, ClientIdSequence, Client, Order, Transaction, Payment, BankCard, NotificationChannel, Settings
- [v0.0.7] Defined all relationships between models
- [v0.0.7] Created and executed Alembic migration
- [v0.0.7] Verified all tables and relationships in database

[ID-005] Create .env.example with comprehensive configuration options
Status: [X] Priority: High
Dependencies: ID-001
Requirements Reference: project-requirements.md#2-Core-Technologies-&-Architecture
Expected Completion: Completed
Testing Requirements:
- Unit tests required: No
- Integration tests required: No
- E2E tests required: No
Documentation Requirements:
- API documentation needed: No
- User guide updates needed: Yes
- System architecture updates needed: No
Progress Notes:
- [v0.0.2] Initial task definition.
- [v0.0.3] Enhanced .env.example with comprehensive settings, Persian translations, and improved organization.
- [v0.0.3] Added new configuration options for Redis, CORS, rate limiting, monitoring, and system limits.
- [v0.0.3] Added detailed bilingual comments and emojis for better readability.

[ID-006] Setup Docker environment (Dockerfile & docker-compose.yml)
Status: [X] Priority: High
Dependencies: ID-001, ID-005
Requirements Reference: project-requirements.md#2-Core-Technologies-&-Architecture
Expected Completion: Completed
Testing Requirements:
- Unit tests required: No
- Integration tests required: Yes
- E2E tests required: Yes
Documentation Requirements:
- API documentation needed: No
- User guide updates needed: Yes
- System architecture updates needed: Yes
Progress Notes:
- [v0.0.2] Initial task definition.
- [v0.0.3] Setup Docker with API, Bot, MySQL, Redis, and phpMyAdmin services.
- [v0.0.4] Fixed database configuration and access issues.
- [v0.0.4] Implemented proper health checks for all services.
- [v0.0.4] Fixed bot container health check using httpx.
- [v0.0.4] All services now running in healthy state.

[ID-007] Implement 3x-ui panel connection system
Status: [X] Priority: High
Dependencies: ID-002
Requirements Reference: project-requirements.md#3.1-Panel-Management
Expected Completion: Completed
Testing Requirements:
- Unit tests required: Yes
- Integration tests required: Yes
- E2E tests required: No
Documentation Requirements:
- API documentation needed: Yes
- User guide updates needed: No
- System architecture updates needed: No
Progress Notes:
- [v0.0.2] Initial task definition.
- [v0.0.6] Basic panel connection client implemented in integrations/panels/client.py
- [v0.0.6] Added API endpoints for testing panel connection
- [v0.0.6] Implemented test script for panel connection
- [v0.0.6] Comprehensive tests created for unit and integration testing
- [v0.0.8] Analyzed wizwiz project for better understanding of panel management requirements
- [v0.0.8] Updated implementation approach based on industry best practices
- [v0.1.0] Completed XuiPanelClient implementation with all required methods
- [v0.1.0] Added comprehensive error handling and connection management
- [v0.1.0] Implemented authentication and session handling
- [v0.1.0] Added support for all panel operations (inbounds, clients, traffic)

## Overview
This task implements a comprehensive connection system for 3x-ui panels. The system will manage multiple 3x-ui panel instances installed on different VPS servers. Each panel operates independently but is centrally managed by our application through the 3x-ui REST API. The system enables administrators to manage users, inbounds, clients, and monitor traffic across all panels from a single interface.

## Implementation Details

### Panel Connection
- Implement secure login and session management to 3x-ui panels
- Ensure proper error handling and retry mechanisms
- Support both HTTP and HTTPS connections
- Implement connection pooling for efficient resource usage

### Panel API Integration
Implement all endpoints documented in the [3x-ui API Routes](https://github.com/MHSanaei/3x-ui?tab=readme-ov-file#api-routes):

#### Authentication
- `/login` (POST) - Panel authentication with username/password

#### Inbound Management
- `/panel/api/inbounds/list` - Get all inbounds
- `/panel/api/inbounds/get/:id` - Get specific inbound
- `/panel/api/inbounds/add` - Create new inbound
- `/panel/api/inbounds/update/:id` - Update existing inbound
- `/panel/api/inbounds/del/:id` - Delete inbound

#### Client Management
- `/panel/api/inbounds/addClient` - Add client to inbound
- `/panel/api/inbounds/:id/delClient/:clientId` - Delete client
- `/panel/api/inbounds/updateClient/:clientId` - Update client
- `/panel/api/inbounds/clientIps/:email` - Get client IP addresses
- `/panel/api/inbounds/clearClientIps/:email` - Clear client IP addresses

#### Traffic Management
- `/panel/api/inbounds/getClientTraffics/:email` - Get client traffic by email
- `/panel/api/inbounds/getClientTrafficsById/:id` - Get client traffic by ID
- `/panel/api/inbounds/:id/resetClientTraffic/:email` - Reset client's traffic
- `/panel/api/inbounds/resetAllTraffics` - Reset all traffics
- `/panel/api/inbounds/resetAllClientTraffics/:id` - Reset all client traffics in an inbound

#### System Operations
- `/panel/api/inbounds/createbackup` - Create backup
- `/panel/api/inbounds/delDepletedClients/:id` - Delete depleted clients
- `/panel/api/inbounds/onlines` - Get online users

### Panel Health Monitoring
- Implement health checks to verify panel availability
- Monitor panel resources and performance
- Set up alerting for panel issues or downtime
- Log panel status changes

### Panel Service Implementation
- Create a service layer for unified panel management
- Implement CRUD operations for panels in database
- Secure storage of panel credentials
- Automated panel discovery and registration
- Panel selection mechanisms for client allocation

### Security Considerations
- Encrypt all panel credentials in the database
- Implement rate limiting for API requests
- Use secure communication (HTTPS where available)
- Implement proper authentication for panel management APIs
- Log all panel operations for audit purposes

## ID-007 Subtasks
Each subtask should be implemented and tested independently:

### [ID-007-1] Basic Panel Client Implementation
Status: In Progress
- Implement base HTTP client with proper error handling
- Create authentication method for panel login
- Implement session management (cookies, tokens)
- Add connection pooling and timeout handling
- Add retry mechanisms for failed requests
- Create basic unit tests for client functionality

### [ID-007-2] Inbound Management API
Status: Not Started
- Implement client methods for inbound operations
- Add validation for inbound data
- Create proper data models for inbounds
- Implement all inbound API endpoints
- Add comprehensive unit tests

### [ID-007-3] Client Management API
Status: Not Started
- Implement client methods for client operations
- Add validation for client data
- Create proper data models for clients
- Implement all client API endpoints
- Add comprehensive unit tests

### [ID-007-4] Traffic Management API
Status: Not Started
- Implement client methods for traffic operations
- Add traffic data processing utilities
- Create proper data models for traffic data
- Implement all traffic API endpoints
- Add comprehensive unit tests

### [ID-007-5] System Operations API
Status: Not Started
- Implement client methods for system operations
- Add system utilities for backup handling
- Create proper data models for system operations
- Implement all system API endpoints
- Add comprehensive unit tests

### [ID-007-6] Panel Service Layer
Status: Not Started
- Create PanelService for unified panel management
- Implement database models for panels
- Add encryption for panel credentials
- Create CRUD operations for panels
- Implement panel selection logic
- Add comprehensive unit tests

### [ID-007-7] Panel Health Monitoring
Status: Not Started
- Implement health check mechanisms
- Create scheduling for periodic health checks
- Add notification system for health status changes
- Implement health data logging and analysis
- Add dashboard for monitoring panel health
- Add comprehensive unit tests

### [ID-007-8] API Endpoints for Panel Management
Status: Not Started
- Design RESTful API for panel management
- Implement API endpoints for CRUD operations
- Add validation and error handling
- Create documentation with Swagger/OpenAPI
- Add comprehensive unit and integration tests

### [ID-007-9] Integration and System Testing
Status: Not Started
- Create comprehensive integration test suite
- Implement end-to-end testing scenarios
- Add performance testing for API endpoints
- Create documentation for testing process
- Fix bugs and issues discovered during testing

Next Steps for ID-007:
- Implement complete API client for 3x-ui with all available endpoints
- Create a PanelService for managing multiple panels
- Implement panel health checking system
- Add support for inbound and client management
- Implement secure credential storage with encryption
- Create scheduled health checks (5-15 minute intervals)
- Add panel monitoring dashboard for administrators

API Endpoints to Implement:
- GET `/list` - Get all inbounds
- GET `/get/:id` - Get inbound with ID
- GET `/getClientTraffics/:email` - Get client traffic by email
- POST `/add` - Add new inbound
- POST `/addClient` - Add client to inbound
- POST `/:id/delClient/:clientId` - Delete client by ID
- POST `/updateClient/:clientId` - Update client by ID
- POST `/:id/resetClientTraffic/:email` - Reset client's traffic
- POST `/resetAllTraffics` - Reset all traffic for all inbounds
- POST `/resetAllClientTraffics/:id` - Reset all clients' traffic in an inbound
- POST `/delDepletedClients/:id` - Delete depleted clients

[ID-008] Create moonvpn command script for Docker management
Status: [X] Priority: Medium
Dependencies: ID-006
Requirements Reference: project-requirements.md#2-Core-Technologies-&-Architecture
Expected Completion: Completed
Testing Requirements:
- Unit tests required: No
- Integration tests required: Yes
- E2E tests required: Yes
Documentation Requirements:
- API documentation needed: No
- User guide updates needed: Yes
- System architecture updates needed: No
Progress Notes:
- [v0.0.2] Initial task definition.
- [v0.1.0] Implemented comprehensive command script in scripts/moonvpn.sh
- [v0.1.0] Added commands for service management (start, stop, restart, status)
- [v0.1.0] Implemented system installation and configuration
- [v0.1.0] Added logs viewing and management
- [v0.1.0] Implemented backup and restore functionality
- [v0.1.0] Added shell access to services
- [v0.1.0] Created update mechanism for the system
- [v0.1.0] Added comprehensive error handling and user feedback
- [v0.1.0] Added colorful Persian UI with emojis

[ID-009] Implement health check script
Status: [X] Priority: High
Dependencies: ID-001
Requirements Reference: project-requirements.md#2-Core-Technologies-&-Architecture
Expected Completion: Completed
Testing Requirements:
- Unit tests required: Yes
- Integration tests required: Yes
- E2E tests required: No
Documentation Requirements:
- API documentation needed: No
- User guide updates needed: No
- System architecture updates needed: Yes
Progress Notes:
- [v0.0.2] Initial task definition.
- [v0.0.3] Enhanced config.py with comprehensive settings, environment validation, and Persian comments.
- [v0.0.3] Added new configuration options for Redis, CORS, rate limiting, monitoring, and system limits.
- [v0.0.3] Updated database.py with optimized connection handling, Redis integration, and utility functions.
- [v0.0.3] Added MySQL event listeners for timezone and strict mode.
- [v0.0.3] Implemented connection health checks and proper error handling.
- [v0.1.0] Created comprehensive healthcheck.py script for monitoring system health
- [v0.1.0] Implemented checks for API, bot, database, Redis, and panel
- [v0.1.0] Added detailed reporting and status visualization
- [v0.1.0] Implemented both CLI and JSON output formats
- [v0.1.0] Added integration with the moonvpn command

[ID-010] Implement backup script
Status: [X] Priority: Medium
Dependencies: ID-006
Requirements Reference: project-requirements.md#3.9-Backup-and-Security
Expected Completion: Completed
Testing Requirements:
- Unit tests required: No
- Integration tests required: Yes
- E2E tests required: Yes
Documentation Requirements:
- API documentation needed: No
- User guide updates needed: Yes
- System architecture updates needed: No
Progress Notes:
- [v0.0.4] Initial task definition.
- [v0.0.4] Created i18n module for handling translations.
- [v0.0.4] Added language selection command and handlers.
- [v0.0.4] Added language preference to user model.
- [v0.0.4] Created Persian and English translation files.
- [v0.0.4] Added language selection button to main menu.
- [v0.0.4] Updated bot's response system to support multiple languages.
- [v0.0.5] Tested Persian language support with live bot - working correctly.
- [v0.0.5] Verified message delivery and Persian text rendering.
- [v0.0.5] Confirmed bot health check and service stability.
- [v0.1.0] Implemented comprehensive backup.sh script
- [v0.1.0] Added database backup functionality
- [v0.1.0] Implemented configuration file backup
- [v0.1.0] Added log file archiving
- [v0.1.0] Created automatic backup rotation (keeping only last 5 backups)
- [v0.1.0] Added colorful Persian UI with emoji support
- [v0.1.0] Integrated with moonvpn command

[ID-011] Setup notification channel system (bot/channels.py)
Status: [X] Priority: Medium
Dependencies: ID-003
Requirements Reference: project-requirements.md#3.3-Channel-Based-Notification-System
Expected Completion: Completed
Testing Requirements:
- Unit tests required: Yes
- Integration tests required: Yes
- E2E tests required: Yes
Documentation Requirements:
- API documentation needed: No
- User guide updates needed: Yes
- System architecture updates needed: No
Progress Notes:
- [v0.0.2] Initial task definition.
- [v0.1.0] Implemented comprehensive NotificationManager class
- [v0.1.0] Added support for multiple notification channels (admin, payment, report, log, alert, backup)
- [v0.1.0] Implemented message templates for various notification types
- [v0.1.0] Added support for interactive buttons and callbacks
- [v0.1.0] Implemented priority levels for notifications
- [v0.1.0] Added support for media attachments (images, documents)
- [v0.1.0] Created helper methods for common notification types
- [v0.1.0] Implemented comprehensive error handling and retries
- [v0.1.0] Added support for Persian notifications with emoji

[ID-012] Setup core logging system (core/logging.py)
Status: [X] Priority: High
Dependencies: ID-002, ID-003
Requirements Reference: project-requirements.md#2-Core-Technologies-&-Architecture
Expected Completion: Completed
Testing Requirements:
- Unit tests required: Yes
- Integration tests required: No
- E2E tests required: No
Documentation Requirements:
- API documentation needed: No
- User guide updates needed: No
- System architecture updates needed: Yes
Progress Notes:
- [v0.0.2] Initial task definition.
- [v0.0.3] Completed comprehensive logging system with multiple handlers, colored console output, rotating file logs, Telegram channel integration for critical errors, environment-specific log directories, and proper log filtering for third-party libraries.
- [v0.0.3] Added utility functions for easy logger access.

[ID-013] Create initial test framework setup
Status: [ ] Priority: High
Dependencies: ID-002, ID-003, ID-004
Requirements Reference: project-requirements.md#6-Testing-Strategy
Expected Completion: TBD
Testing Requirements:
- Unit tests required: N/A
- Integration tests required: N/A
- E2E tests required: N/A
Documentation Requirements:
- API documentation needed: No
- User guide updates needed: No
- System architecture updates needed: Yes
Progress Notes:
- [v0.0.2] Initial task definition.

## Core Requirements Tracking

### Persian Language Implementation
- [ ] Define Persian message templates and format standards
- [ ] Create emoji usage guidelines for user-facing messages
- [ ] Implement localization infrastructure in bot module
- [ ] Create Persian language test suite
- [ ] Document Persian language standards for developers

### Testing Framework
- [ ] Setup pytest environment for unit testing
- [ ] Create test data fixtures for common scenarios
- [ ] Define integration test approaches
- [ ] Setup E2E test procedures for Telegram bot
- [ ] Define minimum test coverage requirements

# Quality Assurance Checklist

For each completed task:
- [ ] Code follows Python best practices (PEP 8)
- [ ] Required tests implemented and passing
- [ ] Documentation updated as needed
- [ ] Persian language support implemented (if user-facing)
- [ ] Security best practices followed (no hardcoded credentials, proper error handling)
- [ ] Performance meets requirements
- [ ] Commits use descriptive messages

# Milestone 1 Testing Plan

After completing tasks [ID-001] through [ID-006]:
- [ ] Verify Docker environment starts correctly
- [ ] Ensure FastAPI responds to basic requests
- [ ] Confirm database connects and migrations work
- [ ] Test Telegram bot basic commands function
- [ ] Verify logging system captures events correctly

# Milestone 2 Testing Plan

After completing tasks [ID-007] through [ID-013]:
- [ ] Test 3x-ui panel connection functionality
- [ ] Verify Persian language support works in bot
- [ ] Ensure notification channels function correctly
- [ ] Test command-line utility (moonvpn)
- [ ] Run all unit and integration tests

# Developer Notes
- Persian language support is critical for all user-facing components
- Each task should be testable independently when possible
- Docker setup needs to support dev, test, and prod environments
- Focus on creating modular, reusable components
- Encrypt sensitive data (panel credentials) in database
- Implement proper error handling for all external API calls
- Design with scalability in mind - the system should support multiple panels
- Follow best security practices for all authentication flows
- Design APIs with OpenAPI documentation in mind

## Notes
- Remember to update CHANGELOG.md for each significant change
- Keep documentation up to date with implementation
- Follow Persian language guidelines for user-facing messages
- Ensure proper error handling and logging throughout
- Consider rate limiting for API and bot endpoints
- Plan for scalability in database design
- Keep security best practices in mind

## Questions
- Should we implement caching at the API level?
- What metrics should we collect for monitoring?
- Should we add support for multiple payment gateways?
- What is the expected scale of the system (number of users, panels, traffic)?
- Should we implement a more comprehensive role-based access control system?

## Dependencies
- Python 3.9+
- FastAPI
- SQLAlchemy
- python-telegram-bot
- Redis
- MySQL
- Docker & Docker Compose
- httpx (for API client)

## SQL Models Implementation Plan

For completing task [ID-004], we need to:

1. **Update existing models**:
   - Update Location model to add new fields:
     ```python
     # Add to Location model
     default_inbound_id = Column(Integer, nullable=True)
     protocols_supported = Column(String(100), nullable=True)  # comma-separated list
     inbound_tag_pattern = Column(String(100), nullable=True)
     default_remark_prefix = Column(String(50), nullable=True)
     ```
   
   - Update Panel model to remove unused fields:
     ```python
     # Remove from Panel model
     # max_clients = Column(Integer, default=0)
     # current_clients = Column(Integer, default=0)
     ```

2. **Create new models** (in priority order):
   - PlanCategory model
   - Plan model (with relationship to PlanCategory)
   - ClientIdSequence model (with relationship to Location)
   - Client model (with relationships to User, Panel, Location, Plan, Order)
   - Order model
   - Transaction model
   - Payment model
   - BankCard model
   - NotificationChannel model
   - Settings model

3. **Create Alembic migration**:
   - Update existing models
   - Add new models
   - Set up initial roles and settings

This implementation will fulfill the requirements specified in the project-requirements.md document for Phase 0 and prepare for Phase 1 & 2.