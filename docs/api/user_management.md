# User Management API Documentation

## Overview
This document describes the API endpoints for managing users in the MoonVPN system. All endpoints require authentication and appropriate permissions.

## Base URL
```
/api/users
```

## Authentication
All requests must include a valid session token in the cookie. If not authenticated, endpoints will return `401 Unauthorized`.

## Error Responses
All endpoints may return these common errors:
- `400 Bad Request`: Invalid input data
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Requested resource not found
- `500 Internal Server Error`: Server-side error

## Endpoints

### List Users
```http
GET /api/users
```

Query users with pagination and search capabilities.

**Query Parameters:**
- `page` (integer, default: 1): Page number
- `limit` (integer, default: 20): Items per page
- `search` (string, optional): Search by username or email

**Response:**
```json
{
    "users": [
        {
            "id": "string",
            "username": "string",
            "email": "string",
            "role": "string",
            "subscription": {
                "plan": "string",
                "expires_at": "string (ISO date)",
                "status": "string"
            },
            "traffic": {
                "used": "number",
                "limit": "number",
                "percentage": "number"
            },
            "status": "string",
            "created_at": "string (ISO date)",
            "last_active": "string (ISO date) | null"
        }
    ]
}
```

### Create User
```http
POST /api/users
```

Create a new user account.

**Request Body (form-data):**
```json
{
    "username": "string (required)",
    "email": "string (required)",
    "password": "string (required)",
    "role": "string (required) [admin|manager|user]",
    "plan": "string (required) [basic|premium|enterprise]",
    "expires_at": "string (required) (ISO date)",
    "traffic_limit": "number (required) (GB)",
    "status": "string (required) [active|inactive|suspended]"
}
```

**Response:**
```json
{
    "success": true,
    "user_id": "string"
}
```

### Get User
```http
GET /api/users/{user_id}
```

Retrieve details for a specific user.

**Response:**
```json
{
    "id": "string",
    "username": "string",
    "email": "string",
    "role": "string",
    "subscription": {
        "plan": "string",
        "expires_at": "string (ISO date)",
        "status": "string"
    },
    "traffic": {
        "used": "number",
        "limit": "number",
        "percentage": "number"
    },
    "status": "string",
    "created_at": "string (ISO date)",
    "last_active": "string (ISO date) | null"
}
```

### Update User
```http
PUT /api/users/{user_id}
```

Update an existing user's information.

**Request Body (form-data):**
```json
{
    "email": "string (required)",
    "role": "string (required) [admin|manager|user]",
    "plan": "string (required) [basic|premium|enterprise]",
    "expires_at": "string (required) (ISO date)",
    "traffic_limit": "number (required) (GB)",
    "status": "string (required) [active|inactive|suspended]",
    "password": "string (optional)"
}
```

**Response:**
```json
{
    "success": true
}
```

### Delete User
```http
DELETE /api/users/{user_id}
```

Delete a user account.

**Response:**
```json
{
    "success": true
}
```

### Get User Details
```http
GET /api/users/{user_id}/details
```

Get detailed information about a user including traffic history and activity.

**Response:**
```json
{
    "username": "string",
    "email": "string",
    "total_traffic": "number",
    "active_sessions": "number",
    "created_at": "string (ISO date)",
    "traffic_history": [
        {
            "timestamp": "string (ISO date)",
            "bytes_in": "number",
            "bytes_out": "number"
        }
    ],
    "recent_activity": [
        {
            "type": "string",
            "message": "string",
            "timestamp": "string (ISO date)",
            "icon": "string"
        }
    ]
}
```

### Export Users
```http
GET /api/users/export
```

Export all users' data in CSV format.

**Response:**
- Content-Type: text/csv
- Content-Disposition: attachment; filename=users_export_YYYYMMDD.csv

CSV columns:
- username
- email
- role
- plan
- expires_at
- traffic_used
- traffic_limit
- status
- created_at
- last_active

## Permission Requirements

| Endpoint | Required Permission |
|----------|-------------------|
| List Users | users.view |
| Create User | users.create |
| Get User | users.view |
| Update User | users.edit |
| Delete User | users.delete |
| Get User Details | users.view |
| Export Users | users.export |

## Rate Limiting
- All endpoints are rate-limited to 100 requests per minute per IP address
- Export endpoint is limited to 10 requests per hour per IP address

## Data Types

### User Status
- `active`: Account is active and can be used
- `inactive`: Account is temporarily disabled
- `suspended`: Account is suspended due to violation
- `deleted`: Account is marked for deletion

### Subscription Plans
- `basic`: Basic plan with limited features
- `premium`: Premium plan with advanced features
- `enterprise`: Enterprise plan with full features

### User Roles
- `admin`: Full system access
- `manager`: Can manage users but not system settings
- `user`: Regular user with limited access

### Activity Types
- `login`: User login events
- `logout`: User logout events
- `traffic`: Traffic usage events
- `subscription`: Subscription changes
- `settings`: Settings changes
- `security`: Security-related events 