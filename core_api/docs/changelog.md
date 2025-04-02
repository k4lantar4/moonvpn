# Changelog

## [Unreleased]

### Added
- Implemented server management system
  - Created ServerService for secure SSH operations
  - Added endpoints for server status monitoring
  - Added server metrics and system information retrieval
  - Implemented secure command execution with whitelist
  - Added administrative actions (restart Xray, reboot server)
  - Added batch status check for multiple servers
  - Created documentation in docs/server_management.md

- Implemented wallet management system
  - Added endpoints for deposits, withdrawals, and balance checking
  - Implemented transaction history and summary
  - Added admin endpoints for managing user wallets and transactions
  - Added payment support for orders using wallet balance
  - Added refund functionality for orders

## [0.1.0] - 2023-04-15

### Added
- Initial project setup
- User authentication and management
- Basic API structure 