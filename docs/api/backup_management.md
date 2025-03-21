# Backup Management API Documentation

## Overview
The Backup Management API provides endpoints for managing system backups, including creation, verification, restoration, and scheduling of backups. The system supports full, incremental, and differential backups across multiple storage providers.

## Models

### BackupType
```python
class BackupType(str, Enum):
    FULL = 'full'           # Complete system backup
    INCREMENTAL = 'incremental'   # Changes since last backup
    DIFFERENTIAL = 'differential' # Changes since last full backup
```

### BackupStatus
```python
class BackupStatus(str, Enum):
    PENDING = 'pending'         # Backup created but not started
    IN_PROGRESS = 'in_progress' # Backup currently running
    COMPLETED = 'completed'     # Backup finished successfully
    FAILED = 'failed'          # Backup failed
    VERIFIED = 'verified'       # Backup verified successfully
    DELETED = 'deleted'         # Backup has been deleted
```

### StorageProvider
```python
class StorageProvider(str, Enum):
    LOCAL = 'local'  # Local file system storage
    S3 = 's3'       # Amazon S3 storage
    AZURE = 'azure'  # Azure Blob storage
    GCS = 'gcs'     # Google Cloud Storage
```

## Endpoints

### Create Backup
Creates a new system backup.

```http
POST /api/v1/backups
```

#### Request Body
```json
{
    "name": "string",
    "description": "string (optional)",
    "backup_type": "full | incremental | differential",
    "storage_provider": "local | s3 | azure | gcs",
    "storage_path": "string",
    "metadata": "object (optional)"
}
```

#### Response
```json
{
    "id": "integer",
    "name": "string",
    "description": "string",
    "backup_type": "string",
    "status": "string",
    "storage_provider": "string",
    "storage_path": "string",
    "file_size": "integer",
    "checksum": "string",
    "created_at": "datetime",
    "started_at": "datetime",
    "completed_at": "datetime"
}
```

### Verify Backup
Verifies the integrity of a backup.

```http
POST /api/v1/backups/{backup_id}/verify
```

#### Response
```json
{
    "id": "integer",
    "status": "string",
    "verified_at": "datetime",
    "verified_by": "integer"
}
```

### Restore Backup
Restores a backup to the system.

```http
POST /api/v1/backups/{backup_id}/restore
```

#### Request Body
```json
{
    "target_path": "string (optional)"
}
```

#### Response
```json
{
    "success": "boolean",
    "message": "string"
}
```

### Get Backup
Retrieves details of a specific backup.

```http
GET /api/v1/backups/{backup_id}
```

#### Response
```json
{
    "id": "integer",
    "name": "string",
    "description": "string",
    "backup_type": "string",
    "status": "string",
    "storage_provider": "string",
    "storage_path": "string",
    "file_size": "integer",
    "checksum": "string",
    "created_at": "datetime",
    "started_at": "datetime",
    "completed_at": "datetime",
    "verified_at": "datetime",
    "expires_at": "datetime",
    "metadata": "object"
}
```

### List Backups
Retrieves a list of backups with optional filtering.

```http
GET /api/v1/backups
```

#### Query Parameters
- `skip` (integer, optional): Number of records to skip
- `limit` (integer, optional): Maximum number of records to return
- `status` (string, optional): Filter by backup status
- `backup_type` (string, optional): Filter by backup type
- `storage_provider` (string, optional): Filter by storage provider

#### Response
```json
{
    "total": "integer",
    "items": [
        {
            "id": "integer",
            "name": "string",
            "backup_type": "string",
            "status": "string",
            "created_at": "datetime",
            "completed_at": "datetime"
        }
    ]
}
```

### Create Backup Schedule
Creates a new backup schedule.

```http
POST /api/v1/backup-schedules
```

#### Request Body
```json
{
    "name": "string",
    "description": "string (optional)",
    "backup_type": "full | incremental | differential",
    "storage_provider": "local | s3 | azure | gcs",
    "storage_path": "string",
    "cron_expression": "string",
    "retention_days": "integer",
    "max_backups": "integer",
    "metadata": "object (optional)"
}
```

#### Response
```json
{
    "id": "integer",
    "name": "string",
    "description": "string",
    "backup_type": "string",
    "storage_provider": "string",
    "storage_path": "string",
    "cron_expression": "string",
    "retention_days": "integer",
    "max_backups": "integer",
    "is_active": "boolean",
    "last_run_at": "datetime",
    "next_run_at": "datetime",
    "created_at": "datetime"
}
```

## Error Responses

### 400 Bad Request
```json
{
    "error": "string",
    "message": "string",
    "details": "object (optional)"
}
```

### 404 Not Found
```json
{
    "error": "string",
    "message": "string"
}
```

### 500 Internal Server Error
```json
{
    "error": "string",
    "message": "string"
}
```

## Storage Providers

### Local Storage Provider
The local storage provider saves backups to the local file system.

Configuration:
```json
{
    "storage_provider": "local",
    "storage_path": "/path/to/backups"
}
```

### S3 Storage Provider (Future)
Amazon S3 storage provider for cloud backups.

Configuration:
```json
{
    "storage_provider": "s3",
    "bucket": "string",
    "region": "string",
    "access_key": "string",
    "secret_key": "string"
}
```

### Azure Storage Provider (Future)
Azure Blob storage provider for cloud backups.

Configuration:
```json
{
    "storage_provider": "azure",
    "container": "string",
    "connection_string": "string"
}
```

### GCS Storage Provider (Future)
Google Cloud Storage provider for cloud backups.

Configuration:
```json
{
    "storage_provider": "gcs",
    "bucket": "string",
    "credentials_file": "string"
}
```

## Best Practices

1. **Backup Types**
   - Use full backups for complete system snapshots
   - Use incremental backups for daily changes
   - Use differential backups for weekly changes

2. **Scheduling**
   - Schedule full backups weekly
   - Schedule incremental backups daily
   - Schedule differential backups every 3 days

3. **Retention**
   - Keep full backups for 90 days
   - Keep incremental backups for 30 days
   - Keep differential backups for 60 days

4. **Verification**
   - Verify backups immediately after creation
   - Schedule periodic verification of critical backups
   - Verify backups before restoration

5. **Storage**
   - Use multiple storage providers for critical data
   - Implement proper access controls
   - Monitor storage space usage

## Security Considerations

1. **Authentication**
   - All endpoints require authentication
   - Use role-based access control
   - Implement API key authentication

2. **Data Protection**
   - Encrypt sensitive data in backups
   - Secure storage provider credentials
   - Implement secure file transfer

3. **Access Control**
   - Restrict backup operations to admin users
   - Log all backup operations
   - Monitor for unauthorized access

## Rate Limiting

- Maximum 10 requests per minute per IP
- Maximum 5 concurrent backup operations
- Maximum 3 restore operations per hour 