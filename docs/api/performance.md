# Performance Testing API Documentation

This document describes the API endpoints for performance testing in MoonVPN.

## Base URL

```
/api/v1/performance
```

## Authentication

All endpoints require authentication using a valid JWT token. Include the token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

## Endpoints

### Start Load Test

```http
POST /load
```

Starts a load test with the given configuration.

#### Request Body

```json
{
    "concurrent_users": 10,
    "actions_per_user": 5,
    "action_delay": 0.1,
    "api_latency": 0.05,
    "error_rate": 0.1,
    "max_instances": 3
}
```

#### Parameters

- `concurrent_users` (integer): Number of concurrent users to simulate
- `actions_per_user` (integer): Number of actions per user
- `action_delay` (float): Delay between actions in seconds
- `api_latency` (float): Simulated API latency in seconds
- `error_rate` (float): Rate of simulated API errors (0-1)
- `max_instances` (integer): Maximum number of instances for scalability testing

#### Response

```json
"test_id_1"
```

### Start Stress Test

```http
POST /stress
```

Starts a stress test with the given configuration.

#### Request Body

```json
{
    "concurrent_users": 10,
    "actions_per_user": 5,
    "action_delay": 0.1,
    "api_latency": 0.05,
    "error_rate": 0.1,
    "max_instances": 3
}
```

#### Parameters

Same as load test.

#### Response

```json
"test_id_2"
```

### Start Scalability Test

```http
POST /scalability
```

Starts a scalability test with the given configuration.

#### Request Body

```json
{
    "concurrent_users": 10,
    "actions_per_user": 5,
    "action_delay": 0.1,
    "api_latency": 0.05,
    "error_rate": 0.1,
    "max_instances": 3
}
```

#### Parameters

Same as load test.

#### Response

```json
"test_id_3"
```

### Stop Test

```http
POST /{test_id}/stop
```

Stops a running test.

#### Parameters

- `test_id` (path): The ID of the test to stop

#### Response

```json
true
```

#### Error Response

```json
{
    "detail": "Test {test_id} not found"
}
```

### Get Test Status

```http
GET /{test_id}/status
```

Gets the status of a test.

#### Parameters

- `test_id` (path): The ID of the test

#### Response

```json
{
    "test_id": "test_id",
    "status": "running",
    "results": []
}
```

#### Error Response

```json
{
    "detail": "Test {test_id} not found"
}
```

### Get Test Summary

```http
GET /{test_id}/summary
```

Gets a summary of test results.

#### Parameters

- `test_id` (path): The ID of the test

#### Response

```json
{
    "test_id": "test_id",
    "type": "load",
    "start_time": "2024-01-01T00:00:00",
    "end_time": "2024-01-01T00:01:00",
    "duration": 60.0,
    "status": "completed",
    "total_users": 10,
    "total_actions": 50,
    "success_rate": 0.95,
    "avg_cpu_usage": 50.0,
    "avg_memory_usage": 60.0,
    "avg_disk_usage": 40.0,
    "avg_duration": 1.0
}
```

#### Error Responses

```json
{
    "detail": "Test {test_id} not found"
}
```

```json
{
    "detail": "No results available"
}
```

### List Tests

```http
GET /
```

Lists all performance tests.

#### Response

```json
[
    {
        "id": "test_id_1",
        "type": "load",
        "config": {},
        "start_time": "2024-01-01T00:00:00",
        "end_time": "2024-01-01T00:01:00",
        "duration": 60.0,
        "status": "completed",
        "results": []
    },
    {
        "id": "test_id_2",
        "type": "stress",
        "config": {},
        "start_time": "2024-01-01T00:01:00",
        "end_time": null,
        "duration": null,
        "status": "running",
        "results": []
    }
]
```

### Get Test Results

```http
GET /{test_id}/results
```

Gets detailed results for a test.

#### Parameters

- `test_id` (path): The ID of the test

#### Response

```json
[
    {
        "id": 1,
        "test_id": "test_id",
        "user_id": 1,
        "duration": 1.0,
        "cpu_usage": 50.0,
        "memory_usage": 60.0,
        "disk_usage": 40.0,
        "success": true,
        "timestamp": "2024-01-01T00:00:00"
    }
]
```

#### Error Response

```json
{
    "detail": "Test {test_id} not found"
}
```

## Error Handling

All endpoints may return the following error responses:

- `401 Unauthorized`: Invalid or missing authentication token
- `403 Forbidden`: User does not have permission to access the resource
- `404 Not Found`: Test not found
- `500 Internal Server Error`: Server-side error occurred

## Rate Limiting

API requests are limited to 100 requests per minute per user. Exceeding this limit will result in a `429 Too Many Requests` response.

## Versioning

This API is versioned. The current version is v1. Future versions will be available at `/api/v2/performance`, etc.

## Support

For support or questions about the API, please contact the system administrator or refer to the internal documentation.

# Performance Tuning API

Base URL: `/api/v1/performance`

## Authentication

All endpoints require authentication using a valid API key in the `Authorization` header:

```
Authorization: Bearer YOUR_API_KEY
```

## Rate Limiting

The API is rate limited to 100 requests per minute per API key.

## Endpoints

### Start Database Tuning

Start a database performance tuning process.

**POST** `/database`

#### Request Body

```json
{
  "max_connections": 100,
  "buffer_pool_size": 1024,
  "query_cache_size": 512,
  "cache_size": 2048,
  "eviction_policy": "lru",
  "ttl": 3600,
  "tcp_keepalive": true,
  "connection_timeout": 30,
  "max_retries": 3,
  "thread_pool_size": 10,
  "memory_limit": 4096,
  "gc_interval": 300
}
```

#### Response

```json
"tuning_id_123"
```

### Start Cache Tuning

Start a cache performance tuning process.

**POST** `/cache`

#### Request Body

Same as database tuning.

#### Response

```json
"tuning_id_456"
```

### Start Network Tuning

Start a network performance tuning process.

**POST** `/network`

#### Request Body

Same as database tuning.

#### Response

```json
"tuning_id_789"
```

### Start Application Tuning

Start an application performance tuning process.

**POST** `/application`

#### Request Body

Same as database tuning.

#### Response

```json
"tuning_id_012"
```

### Stop Tuning

Stop a running tuning process.

**POST** `/{tuning_id}/stop`

#### Response

```json
true
```

#### Error Response (404)

```json
{
  "detail": "Tuning process not found"
}
```

### Get Tuning Status

Get the status of a tuning process.

**GET** `/{tuning_id}/status`

#### Response

```json
{
  "tuning_id": "tuning_id_123",
  "status": "running",
  "results": [
    {
      "id": "result_1",
      "tuning_id": "tuning_id_123",
      "phase": "analysis",
      "metrics": {
        "query_performance": {},
        "index_usage": {},
        "table_statistics": {}
      },
      "timestamp": "2024-03-20T12:00:00Z"
    }
  ]
}
```

#### Error Response (404)

```json
{
  "detail": "Tuning process not found"
}
```

### Get Tuning Details

Get detailed information about a tuning process.

**GET** `/{tuning_id}`

#### Response

```json
{
  "id": "tuning_id_123",
  "type": "database",
  "config": {
    "max_connections": 100,
    "buffer_pool_size": 1024,
    "query_cache_size": 512,
    "cache_size": 2048,
    "eviction_policy": "lru",
    "ttl": 3600,
    "tcp_keepalive": true,
    "connection_timeout": 30,
    "max_retries": 3,
    "thread_pool_size": 10,
    "memory_limit": 4096,
    "gc_interval": 300
  },
  "start_time": "2024-03-20T12:00:00Z",
  "end_time": "2024-03-20T12:30:00Z",
  "duration": 1800,
  "status": "completed",
  "results": [
    {
      "id": "result_1",
      "tuning_id": "tuning_id_123",
      "phase": "analysis",
      "metrics": {
        "query_performance": {},
        "index_usage": {},
        "table_statistics": {}
      },
      "timestamp": "2024-03-20T12:00:00Z"
    }
  ]
}
```

#### Error Response (404)

```json
{
  "detail": "Tuning process not found"
}
```

### List Tunings

List all tuning processes.

**GET** `/`

#### Query Parameters

- `type` (optional): Filter by tuning type (database, cache, network, application)

#### Response

```json
[
  {
    "id": "tuning_id_123",
    "type": "database",
    "config": {
      "max_connections": 100,
      "buffer_pool_size": 1024,
      "query_cache_size": 512,
      "cache_size": 2048,
      "eviction_policy": "lru",
      "ttl": 3600,
      "tcp_keepalive": true,
      "connection_timeout": 30,
      "max_retries": 3,
      "thread_pool_size": 10,
      "memory_limit": 4096,
      "gc_interval": 300
    },
    "start_time": "2024-03-20T12:00:00Z",
    "end_time": "2024-03-20T12:30:00Z",
    "duration": 1800,
    "status": "completed",
    "results": []
  }
]
```

## Error Handling

The API uses standard HTTP status codes:

- 200: Success
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 429: Too Many Requests
- 500: Internal Server Error

Error responses include a detail message:

```json
{
  "detail": "Error message here"
}
```

## Versioning

This is version 1 of the Performance Tuning API. The version is included in the base URL.

## Support

For support, please contact:
- Email: support@moonvpn.com
- Documentation: https://docs.moonvpn.com/api/performance
- Status: https://status.moonvpn.com 