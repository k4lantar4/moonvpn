# Server Management System

This document provides a comprehensive overview of the MoonVPN server management system, which enables secure monitoring and administration of VPN server infrastructure.

## Overview

The server management system provides three tiers of functionality:

1. **Basic Monitoring**: Non-invasive monitoring features that don't require authentication
2. **System Information**: Read-only SSH access to gather detailed system metrics
3. **Administrative Actions**: Privileged operations requiring secure SSH access

## Components

### ServerService

The `ServerService` class is the core component providing server management capabilities:

```python
# Usage example
with ServerService(server_id=1) as server_service:
    # Check basic connectivity
    status = server_service.check_status()
    
    # Get detailed system information
    system_info = server_service.get_system_info()
    
    # Restart the Xray service
    result = server_service.restart_xray()
```

### API Endpoints

The system exposes the following API endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/servers/{server_id}/status` | GET | Check server connectivity |
| `/servers/{server_id}/system-info` | GET | Get detailed system information |
| `/servers/{server_id}/metrics` | GET | Get real-time performance metrics |
| `/servers/{server_id}/restart-xray` | POST | Restart the Xray service |
| `/servers/{server_id}/reboot` | POST | Reboot the server |
| `/servers/{server_id}/execute` | POST | Execute a whitelisted command |
| `/servers/batch-status` | GET | Check status of multiple servers |

## Configuration

Server management requires the following environment variables to be set:

```
SSH_ENABLED=True
SSH_USERNAME=username
SSH_PASSWORD=password  # Optional - Use either password or key
SSH_KEY_PATH=/path/to/key  # Optional - Use either password or key
SSH_KEY_PASSPHRASE=passphrase  # Optional - Only needed if key is protected
SSH_CONNECTION_TIMEOUT=10
```

## Security Considerations

The server management system implements several security measures:

1. **Authentication Options**: Supports both password and key-based authentication
2. **Command Whitelisting**: Only pre-approved commands can be executed
3. **Permission Control**: All endpoints require superuser permissions
4. **Exception Handling**: Appropriate error responses without leaking sensitive information
5. **Secure Credential Storage**: Credentials stored in environment variables, not hardcoded

## Exception Handling

The system defines a hierarchy of exceptions for specific error scenarios:

- `ServerException`: Base exception for server-related errors
  - `ServerConnectionError`: Error connecting to the server
  - `ServerAuthenticationError`: Error authenticating with the server
  - `ServerCommandError`: Error executing a command on the server

Each exception is mapped to an appropriate HTTP status code in the API.

## Monitoring Capabilities

The system provides the following monitoring metrics:

- **Basic Status**: Server reachability and latency
- **System Information**: CPU, memory, disk usage, OS version, uptime
- **Performance Metrics**: CPU usage, memory usage, active connections
- **Service Status**: Status of Xray and other critical services

## Administrative Actions

Administrative actions include:

- Restarting the Xray service
- Rebooting the server
- Executing whitelisted commands for troubleshooting

## Implementation Details

The server management system is built using:

- **Paramiko**: Python library for SSH connections
- **FastAPI**: REST API framework
- **Pydantic**: Data validation and schema definition
- **Python's subprocess**: For non-SSH connectivity checks

## Future Enhancements

Planned future enhancements include:

1. SSH key rotation
2. Detailed traffic analysis
3. Automated server provisioning
4. Configuration management
5. Log aggregation and analysis 