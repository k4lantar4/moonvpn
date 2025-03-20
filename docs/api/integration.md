# Integration API Documentation

This document describes the API endpoints for managing system integrations in MoonVPN.

## Base URL

```
/api/v1/integration
```

## Authentication

All endpoints require authentication using a valid JWT token. Include the token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

## Endpoints

### Get System Status

```http
GET /status
```

Returns the overall status of the system, including components, services, APIs, databases, and security.

#### Response

```json
{
    "timestamp": "2024-01-01T00:00:00",
    "components": {
        "status": "healthy"
    },
    "services": {
        "status": "healthy"
    },
    "apis": {
        "status": "healthy"
    },
    "databases": {
        "status": "healthy"
    },
    "security": {
        "status": "healthy"
    }
}
```

### Check System Health

```http
GET /health
```

Checks if the entire system is healthy.

#### Response

```json
true
```

### Restart Component

```http
POST /components/{component}/restart
```

Restarts a specific component of the system.

#### Parameters

- `component` (path): The name of the component to restart (e.g., "vpn", "bot", "payment")

#### Response

```json
true
```

#### Error Response

```json
{
    "detail": "Failed to restart component {component}"
}
```

### Backup Database

```http
POST /databases/backup
```

Backs up data from one database to another.

#### Parameters

- `source_db` (query): The name of the source database
- `target_db` (query): The name of the target database

#### Response

```json
true
```

#### Error Response

```json
{
    "detail": "Failed to backup database from {source_db} to {target_db}"
}
```

### Sync Databases

```http
POST /databases/sync
```

Synchronizes data between two databases.

#### Parameters

- `source_db` (query): The name of the source database
- `target_db` (query): The name of the target database

#### Response

```json
true
```

#### Error Response

```json
{
    "detail": "Failed to sync databases {source_db} and {target_db}"
}
```

### Authenticate User

```http
POST /security/authenticate
```

Authenticates a user using the security service.

#### Request Body

```json
{
    "username": "string",
    "password": "string"
}
```

#### Response

```json
{
    "token": "string",
    "user_id": 1
}
```

#### Error Response

```json
{
    "detail": "Authentication failed"
}
```

### Authorize Access

```http
POST /security/authorize
```

Authorizes user access to a resource.

#### Parameters

- `user_id` (query): The ID of the user
- `resource` (query): The resource to authorize access to

#### Response

```json
true
```

### Encrypt Data

```http
POST /security/encrypt
```

Encrypts data using the security service.

#### Request Body

```json
"string"
```

#### Response

```json
"string"
```

#### Error Response

```json
{
    "detail": "Failed to encrypt data"
}
```

### Decrypt Data

```http
POST /security/decrypt
```

Decrypts data using the security service.

#### Request Body

```json
"string"
```

#### Response

```json
"string"
```

#### Error Response

```json
{
    "detail": "Failed to decrypt data"
}
```

### Log Security Event

```http
POST /security/events
```

Logs a security event using the security service.

#### Request Body

```json
{
    "event": "string",
    "details": {}
}
```

#### Response

```json
true
```

#### Error Response

```json
{
    "detail": "Failed to log security event"
}
```

## Error Handling

All endpoints may return the following error responses:

- `401 Unauthorized`: Invalid or missing authentication token
- `403 Forbidden`: User does not have permission to access the resource
- `500 Internal Server Error`: Server-side error occurred

## Rate Limiting

API requests are limited to 100 requests per minute per user. Exceeding this limit will result in a `429 Too Many Requests` response.

## Versioning

This API is versioned. The current version is v1. Future versions will be available at `/api/v2/integration`, etc.

## Support

For support or questions about the API, please contact the system administrator or refer to the internal documentation. 