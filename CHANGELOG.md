## [Unreleased] - YYYY-MM-DD

### Added
- ...

### Changed
- Refactored `bot/` directory to a features-based structure:
  - Created `features/` directory and subdirectories for each feature (common, wallet, buy, etc.).
  - Moved relevant handlers, keyboards, and states into their respective feature directories.
  - Updated `main.py` to use `RedisStorage` and register feature routers.
  - Migrated `common` feature handlers (e.g., `/start`) to `features/common/handlers.py`.
  - Migrated `wallet` feature handlers, keyboards, and states to `features/wallet/`.
- Refactored and completed `core.integrations.XuiClient`:
  - Added missing methods from `py3xui.async_api` for clients, inbounds, server, and database operations.
  - Renamed existing methods for consistency with `py3xui`.
  - Fully implemented `get_config` method for VLESS and VMess link generation.
  - Improved error handling with specific `XuiAuthenticationError` and `XuiConnectionError`.
  - Enhanced Persian docstrings and logging across the class.
  - Removed non-functional `get_stats` method.
  - Cleaned up commented-out code and unnecessary comments.
- Refactored `bot/callbacks/admin_callbacks.py` file to improve handling of panel and inbound management:
  - Fixed methods `sync_panels`, `panel_inbounds_list`, `panel_connection_test`, and `panel_manage_inbounds_menu` to properly use `PanelService` and `InboundService`
  - Added proper Persian+English bilingual logging to all methods
  - Standardized back buttons and panel status change functionality
  - Added new `panel_sync_inbounds` and `panel_toggle_status` methods for better panel management
  - Fixed imports and error handling for better stability
  - Made sure all handler methods properly check admin permissions

### Fixed
- Fixed `TypeError` in `bot/middlewares/auth.py` by correcting arguments passed to `UserRepository.get_or_create_user`.
- Fixed `AttributeError` in `bot/features/common/handlers.py` by using `user.full_name` or `user.username` instead of `user.first_name`.
- ...

### Removed
- Removed old `bot/commands/`, `bot/callbacks/`, `bot/buttons/`, and `bot/states.py` files after refactoring.
- ...


## [Previous Version] - YYYY-MM-DD
... 