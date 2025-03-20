# Resource Optimization API Documentation

## Overview

The Resource Optimization API provides endpoints for managing and monitoring system resource optimization processes. This API allows you to start, stop, and monitor optimization processes for various system resources such as CPU, memory, disk, and network.

## Base URL

```
/api/v1/optimization
```

## Authentication

All endpoints require authentication using a Bearer token. Include the token in the Authorization header:

```
Authorization: Bearer <your_token>
```

## Endpoints

### Start Optimization

Start a new resource optimization process.

```
POST /start
```

#### Request Body

```json
{
    "resource_type": "cpu",
    "target_usage": 80.0,
    "max_iterations": 3,
    "interval": 1.0,
    "threshold": 0.1,
    "parameters": {}
}
```

#### Parameters

- `resource_type` (string, required): Type of resource to optimize (cpu, memory, disk, network)
- `target_usage` (float, required): Target usage percentage (0-100)
- `max_iterations` (integer, optional): Maximum number of optimization iterations (default: 3)
- `interval` (float, optional): Interval between optimization attempts in seconds (default: 1.0)
- `threshold` (float, optional): Threshold for considering optimization complete (default: 0.1)
- `parameters` (object, optional): Additional optimization parameters

#### Response

```json
{
    "success": true,
    "message": "Optimization started successfully",
    "data": {
        "optimization_id": "test_optimization_id"
    }
}
```

### Stop Optimization

Stop the current resource optimization process.

```
POST /stop
```

#### Response

```json
{
    "success": true,
    "message": "Optimization stopped successfully"
}
```

### Get Optimization Status

Get the current status of the optimization process.

```
GET /status
```

#### Response

```json
{
    "is_active": true,
    "resource_type": "cpu",
    "last_optimized": "2024-03-14T12:00:00Z",
    "current_metrics": {
        "cpu_percent": 75.0
    },
    "optimization_history": []
}
```

### Get Optimization History

Get the history of optimization operations.

```
GET /history
```

#### Response

```json
{
    "total_optimizations": 5,
    "successful_optimizations": 4,
    "failed_optimizations": 1,
    "history": []
}
```

### Get Resource Metrics

Get current resource metrics.

```
GET /metrics
```

#### Response

```json
{
    "timestamp": "2024-03-14T12:00:00Z",
    "metrics": {
        "cpu_percent": 75.0,
        "memory_percent": 60.0
    },
    "optimization_status": {
        "is_active": true
    }
}
```

### Get Optimization Summary

Get a summary of optimization operations.

```
GET /summary
```

#### Response

```json
{
    "total_optimizations": 10,
    "successful_optimizations": 8,
    "failed_optimizations": 2,
    "average_improvement": 15.5,
    "best_optimization": {
        "improvement": 25.0
    },
    "worst_optimization": {
        "improvement": 5.0
    },
    "resource_types": {
        "cpu": 5,
        "memory": 5
    }
}
```

## Error Handling

The API uses standard HTTP status codes:

- 200: Success
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 500: Internal Server Error

Error responses include a detail message:

```json
{
    "detail": "Error message"
}
```

## Rate Limiting

The API is rate limited to 100 requests per minute per user.

## Versioning

This is version 1 of the Resource Optimization API.

## Support

For support, please contact the system administrator or refer to the system documentation. 