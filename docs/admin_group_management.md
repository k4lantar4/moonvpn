# Admin Group Management System

## Overview

The Admin Group Management System is a comprehensive solution for managing admin groups in the MoonVPN Telegram Bot. It provides functionality for creating, managing, and monitoring admin groups, as well as sending notifications to these groups based on system events and status updates.

## Features

### Admin Groups

- Create and manage different types of admin groups
- Assign members to groups with specific roles
- Configure notification preferences for each group
- Monitor group activity and member status

### Group Types

1. **MANAGE** 🛡️
   - Main management group
   - Handles core administrative functions
   - Receives high-priority notifications

2. **REPORTS** 📊
   - System reports and statistics
   - Performance metrics
   - Usage analytics

3. **LOGS** 📄
   - User activity logs
   - System logs
   - Error logs

4. **TRANSACTIONS** 💰
   - Payment tracking
   - Transaction monitoring
   - Financial reports

5. **OUTAGES** ⚠️
   - Service issues
   - System alerts
   - Emergency notifications

6. **SELLERS** 👥
   - Reseller management
   - Partner notifications
   - Sales reports

7. **BACKUPS** 💾
   - Backup notifications
   - System snapshots
   - Data integrity reports

### Commands

#### Group Management

- `/create_admin_group <name> <chat_id> <type> [description]`
  - Create a new admin group
  - Example: `/create_admin_group MoonVPN Management 123456789 manage Main management group`

- `/list_admin_groups [type]`
  - List all admin groups or groups of a specific type
  - Example: `/list_admin_groups manage`

- `/update_admin_group <chat_id> <field> <value>`
  - Update group details
  - Fields: name, description, icon, notification_level, is_active
  - Example: `/update_admin_group 123456789 name New Name`

- `/delete_admin_group <chat_id>`
  - Delete an admin group
  - Example: `/delete_admin_group 123456789`

#### Member Management

- `/add_admin_member <group_chat_id> <user_id> [role]`
  - Add a member to an admin group
  - Roles: admin, moderator, member
  - Example: `/add_admin_member 123456789 987654321 admin`

- `/remove_admin_member <group_chat_id> <user_id>`
  - Remove a member from an admin group
  - Example: `/remove_admin_member 123456789 987654321`

- `/list_admin_members <group_chat_id>`
  - List all members of an admin group
  - Example: `/list_admin_members 123456789`

#### Monitoring

- `/status`
  - Get current system status
  - Shows CPU, memory, disk usage, and network statistics

- `/health`
  - Perform a comprehensive health check
  - Checks database, network, disk, memory, and CPU status

- `/start_monitoring [interval]`
  - Start automatic system monitoring
  - Interval in seconds (default: 300, min: 60, max: 3600)
  - Example: `/start_monitoring 600`

- `/stop_monitoring`
  - Stop automatic system monitoring

## Database Schema

### AdminGroup

```sql
CREATE TABLE admin_group (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    chat_id INTEGER UNIQUE NOT NULL,
    type VARCHAR(50) NOT NULL,
    description TEXT,
    icon VARCHAR(10) DEFAULT '📊',
    notification_level VARCHAR(20) DEFAULT 'normal',
    is_active BOOLEAN DEFAULT true,
    notification_types JSONB DEFAULT '[]',
    added_by JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### AdminGroupMember

```sql
CREATE TABLE admin_group_member (
    id SERIAL PRIMARY KEY,
    group_id INTEGER REFERENCES admin_group(id),
    user_id INTEGER NOT NULL,
    role VARCHAR(50) DEFAULT 'member',
    added_by JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(group_id, user_id)
);
```

## Notification Types

1. **System Status**
   - CPU usage
   - Memory usage
   - Disk usage
   - Network status
   - System uptime

2. **Error Notifications**
   - System errors
   - Service failures
   - Connection issues
   - Database errors

3. **User Activity**
   - User actions
   - Command usage
   - Login attempts
   - Settings changes

4. **Transactions**
   - Payment received
   - Subscription updates
   - Refund requests
   - Financial alerts

5. **Service Outages**
   - System downtime
   - Service degradation
   - Maintenance updates
   - Emergency alerts

## Security

- All commands require admin privileges
- Group operations are logged for audit purposes
- Member roles are strictly enforced
- Sensitive operations require additional verification

## Best Practices

1. **Group Creation**
   - Use descriptive names
   - Set appropriate notification levels
   - Configure notification types based on group purpose
   - Document group purpose in description

2. **Member Management**
   - Assign roles based on responsibilities
   - Regularly review member access
   - Document member additions and removals
   - Use appropriate role levels

3. **Monitoring**
   - Set reasonable monitoring intervals
   - Configure appropriate thresholds
   - Review monitoring data regularly
   - Take action on critical alerts

4. **Notifications**
   - Use appropriate notification levels
   - Include relevant context in messages
   - Format messages for readability
   - Monitor notification delivery

## Error Handling

The system includes comprehensive error handling for:

- Invalid group types
- Duplicate group names
- Invalid member roles
- Database errors
- Network issues
- Permission violations

## Future Enhancements

1. **Planned Features**
   - Group templates
   - Automated member rotation
   - Advanced notification rules
   - Custom monitoring metrics

2. **Integration Opportunities**
   - External monitoring systems
   - Ticketing systems
   - Analytics platforms
   - Backup systems

## Support

For support with the Admin Group Management System:

1. Check the documentation
2. Review error messages
3. Contact system administrators
4. Submit bug reports

## Contributing

To contribute to the Admin Group Management System:

1. Follow coding standards
2. Write comprehensive tests
3. Update documentation
4. Submit pull requests

## License

This system is part of the MoonVPN Telegram Bot and is subject to its license terms. 