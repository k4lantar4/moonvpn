"""
Security and monitoring configuration settings.
"""

# Security Settings
SECURITY_CONFIG = {
    'PROXYCHECK_API_KEY': '',  # Get from https://proxycheck.io/
    'MAX_LOGIN_ATTEMPTS': 5,
    'LOGIN_ATTEMPT_WINDOW': 900,  # 15 minutes
    'IP_BLOCK_DURATION': 86400,  # 24 hours
    'RATE_LIMITS': {
        'login': {
            'max_requests': 5,
            'time_window': 300  # 5 minutes
        },
        'payment': {
            'max_requests': 10,
            'time_window': 3600  # 1 hour
        },
        'api': {
            'max_requests': 100,
            'time_window': 60  # 1 minute
        }
    },
    'GEOLOCATION_SETTINGS': {
        'max_distance_km': 1000,  # Maximum allowed distance between consecutive logins
        'check_enabled': True
    }
}

# Traffic Monitoring Settings
TRAFFIC_CONFIG = {
    'CHECK_INTERVAL': 300,  # 5 minutes
    'WARNING_THRESHOLDS': {
        'traffic': [50, 75, 90, 95],  # Percentage of limit
        'bandwidth': [50, 75, 90, 95]  # Percentage of capacity
    },
    'TRAFFIC_EXCEEDED_ACTIONS': {
        'suspend_service': True,
        'notify_user': True,
        'notify_admin': True
    }
}

# Backup Settings
BACKUP_CONFIG = {
    'BACKUP_ENABLED': True,
    'BACKUP_INTERVAL': 86400,  # 24 hours
    'BACKUP_RETENTION_DAYS': 30,
    'BACKUP_TYPES': ['database', 'configurations', 'logs'],
    'REMOTE_STORAGE': {
        'enabled': False,
        'provider': 'none',  # 's3', 'ftp', etc.
        'credentials': {}
    }
}

# Analytics Settings
ANALYTICS_CONFIG = {
    'ENABLED': True,
    'UPDATE_INTERVAL': 3600,  # 1 hour
    'METRICS': {
        'user_metrics': True,
        'server_metrics': True,
        'financial_metrics': True,
        'traffic_metrics': True
    },
    'RETENTION_DAYS': 90
}

# Notification Settings
NOTIFICATION_CONFIG = {
    'ADMIN_NOTIFICATIONS': {
        'security_alerts': True,
        'traffic_exceeded': True,
        'payment_issues': True,
        'server_issues': True
    },
    'USER_NOTIFICATIONS': {
        'traffic_warnings': True,
        'expiration_reminders': True,
        'payment_confirmations': True,
        'service_updates': True
    }
} 