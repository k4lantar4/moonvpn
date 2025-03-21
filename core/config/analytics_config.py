"""
Configuration settings for the analytics service.
Defines parameters for metrics collection, reporting, and data retention.
"""

# Analytics Service Settings
ANALYTICS_SETTINGS = {
    # Service Configuration
    'ENABLED': True,
    'UPDATE_INTERVAL': 3600,  # 1 hour
    'RETENTION_DAYS': 90,
    'PROMETHEUS_PORT': 9090,
    'REPORTS_PATH': '/root/moonvpn/reports/analytics',
    
    # Metrics Configuration
    'METRICS': {
        'user': {
            'enabled': True,
            'collection_interval': 3600,  # 1 hour
            'retention_days': 90
        },
        'traffic': {
            'enabled': True,
            'collection_interval': 300,  # 5 minutes
            'retention_days': 90,
            'anomaly_detection': {
                'enabled': True,
                'threshold': 2.0  # Standard deviations
            }
        },
        'server': {
            'enabled': True,
            'collection_interval': 60,  # 1 minute
            'retention_days': 90,
            'alert_thresholds': {
                'cpu_usage': 80,  # Percentage
                'memory_usage': 85,  # Percentage
                'disk_usage': 90,  # Percentage
                'load_average': 5.0
            }
        },
        'security': {
            'enabled': True,
            'collection_interval': 300,  # 5 minutes
            'retention_days': 90,
            'alert_thresholds': {
                'failed_logins': 5,  # Per hour
                'suspicious_ips': 3,  # Per hour
                'blocked_ips': 10  # Per day
            }
        }
    },
    
    # Reporting Configuration
    'REPORTS': {
        'daily': {
            'enabled': True,
            'time': '00:00',  # UTC
            'metrics': ['user', 'traffic', 'server', 'security'],
            'format': 'json',
            'retention_days': 90
        },
        'weekly': {
            'enabled': True,
            'day': 'monday',
            'time': '00:00',  # UTC
            'metrics': ['user', 'traffic', 'server', 'security'],
            'format': 'json',
            'retention_days': 180
        },
        'monthly': {
            'enabled': True,
            'day': 1,
            'time': '00:00',  # UTC
            'metrics': ['user', 'traffic', 'server', 'security'],
            'format': 'json',
            'retention_days': 365
        }
    },
    
    # Storage Configuration
    'STORAGE': {
        'type': 'local',  # 'local', 's3', or 'ftp'
        'compression': True,
        'max_size_gb': 10,
        's3': {
            'bucket': 'moonvpn-analytics',
            'prefix': 'metrics/',
            'region': 'us-east-1'
        },
        'ftp': {
            'host': 'ftp.example.com',
            'port': 21,
            'path': '/analytics/'
        }
    },
    
    # Alert Configuration
    'ALERTS': {
        'enabled': True,
        'channels': ['admin', 'telegram', 'email'],
        'thresholds': {
            'user_growth': 10,  # Percentage
            'error_rate': 5,  # Percentage
            'server_load': 80,  # Percentage
            'traffic_spike': 200  # Percentage
        },
        'cooldown': 3600  # 1 hour between similar alerts
    },
    
    # Prometheus Configuration
    'PROMETHEUS': {
        'enabled': True,
        'port': 9090,
        'metrics': {
            'user_metrics': True,
            'traffic_metrics': True,
            'server_metrics': True,
            'security_metrics': True
        },
        'retention_days': 15
    },
    
    # Export Configuration
    'EXPORTS': {
        'formats': ['json', 'csv'],
        'max_range_days': 90,
        'rate_limit': {
            'requests_per_hour': 10,
            'max_size_mb': 100
        }
    }
}

# Metric Types and Descriptions
METRIC_TYPES = {
    'user': {
        'total_users': 'Total number of registered users',
        'active_users': 'Number of users active in the last 24 hours',
        'new_users': 'Number of new user registrations',
        'subscription_distribution': 'Distribution of subscription types',
        'user_retention': 'User retention rates',
        'geographic_distribution': 'User distribution by country',
        'device_distribution': 'User distribution by device type',
        'peak_usage_times': 'Peak usage times by hour'
    },
    'traffic': {
        'total_traffic': 'Total traffic volume',
        'traffic_by_protocol': 'Traffic distribution by protocol',
        'peak_traffic_times': 'Peak traffic times',
        'bandwidth_utilization': 'Bandwidth utilization percentage',
        'traffic_anomalies': 'Detected traffic anomalies'
    },
    'server': {
        'total_servers': 'Total number of VPN servers',
        'active_servers': 'Number of active servers',
        'server_load': 'Server load percentage',
        'bandwidth_usage': 'Bandwidth usage by server',
        'connection_count': 'Active connections per server',
        'error_rates': 'Error rates by server',
        'latency': 'Server latency measurements'
    },
    'security': {
        'blocked_ips': 'Number of blocked IP addresses',
        'suspicious_activities': 'Detected suspicious activities',
        'failed_logins': 'Failed login attempts',
        'security_incidents': 'Security incident reports',
        'vulnerability_scan': 'Vulnerability scan results'
    }
}

# Alert Severity Levels
ALERT_SEVERITY = {
    'critical': {
        'color': 'red',
        'priority': 1,
        'notification_channels': ['admin', 'telegram', 'email'],
        'retry_interval': 300  # 5 minutes
    },
    'high': {
        'color': 'orange',
        'priority': 2,
        'notification_channels': ['admin', 'telegram'],
        'retry_interval': 900  # 15 minutes
    },
    'medium': {
        'color': 'yellow',
        'priority': 3,
        'notification_channels': ['admin'],
        'retry_interval': 3600  # 1 hour
    },
    'low': {
        'color': 'blue',
        'priority': 4,
        'notification_channels': ['admin'],
        'retry_interval': 86400  # 24 hours
    }
}

# Report Templates
REPORT_TEMPLATES = {
    'daily': {
        'sections': [
            'user_summary',
            'traffic_summary',
            'server_health',
            'security_events'
        ],
        'charts': [
            'user_growth',
            'traffic_trends',
            'server_load',
            'security_incidents'
        ]
    },
    'weekly': {
        'sections': [
            'user_analysis',
            'traffic_analysis',
            'server_performance',
            'security_analysis',
            'recommendations'
        ],
        'charts': [
            'user_retention',
            'traffic_patterns',
            'server_metrics',
            'security_trends',
            'geographic_distribution'
        ]
    },
    'monthly': {
        'sections': [
            'executive_summary',
            'user_growth_analysis',
            'traffic_trend_analysis',
            'server_performance_review',
            'security_audit',
            'recommendations',
            'future_projections'
        ],
        'charts': [
            'user_growth_trends',
            'traffic_analysis',
            'server_performance_trends',
            'security_incident_trends',
            'geographic_expansion',
            'revenue_analysis'
        ]
    }
} 