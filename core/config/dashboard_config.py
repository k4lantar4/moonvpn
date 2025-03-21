"""
Configuration settings for the dashboard web interface.
Defines parameters for web server, authentication, and UI components.
"""

import os
from pathlib import Path

# Dashboard Settings
DASHBOARD_SETTINGS = {
    # Server Configuration
    'HOST': '0.0.0.0',
    'PORT': 8080,
    'DEBUG': False,
    'SECRET_KEY': os.getenv('DASHBOARD_SECRET_KEY', 'your-secret-key-here'),
    'SESSION_TIMEOUT': 3600,  # 1 hour
    
    # Security Settings
    'ALLOWED_HOSTS': ['localhost', '127.0.0.1'],
    'CORS_ORIGINS': ['http://localhost:8080'],
    'SSL': {
        'enabled': False,
        'cert_path': '/etc/ssl/certs/dashboard.crt',
        'key_path': '/etc/ssl/private/dashboard.key'
    },
    'RATE_LIMIT': {
        'enabled': True,
        'requests_per_minute': 60,
        'burst': 100
    },
    
    # Authentication Settings
    'AUTH': {
        'session_cookie_name': 'moonvpn_dashboard',
        'session_cookie_secure': True,
        'session_cookie_httponly': True,
        'password_min_length': 12,
        'password_require_special': True,
        'password_require_numbers': True,
        'max_login_attempts': 5,
        'lockout_duration': 900,  # 15 minutes
        'mfa': {
            'enabled': True,
            'issuer': 'MoonVPN Dashboard',
            'digits': 6,
            'interval': 30
        }
    },
    
    # UI Configuration
    'UI': {
        'theme': 'dark',
        'logo_path': '/static/images/logo.png',
        'favicon_path': '/static/images/favicon.ico',
        'title': 'MoonVPN Dashboard',
        'refresh_interval': 30,  # seconds
        'date_format': 'YYYY-MM-DD HH:mm:ss',
        'timezone': 'UTC',
        'language': 'en',
        'items_per_page': 50,
        'chart_theme': 'dark'
    },
    
    # Feature Flags
    'FEATURES': {
        'user_management': True,
        'server_management': True,
        'traffic_monitoring': True,
        'security_monitoring': True,
        'analytics': True,
        'backup_management': True,
        'settings_management': True,
        'api_access': True
    },
    
    # Navigation
    'NAVIGATION': {
        'sidebar': [
            {
                'name': 'Dashboard',
                'icon': 'dashboard',
                'path': '/',
                'roles': ['admin', 'manager', 'viewer']
            },
            {
                'name': 'Users',
                'icon': 'users',
                'path': '/users',
                'roles': ['admin', 'manager']
            },
            {
                'name': 'Servers',
                'icon': 'server',
                'path': '/servers',
                'roles': ['admin', 'manager']
            },
            {
                'name': 'Traffic',
                'icon': 'traffic',
                'path': '/traffic',
                'roles': ['admin', 'manager', 'viewer']
            },
            {
                'name': 'Security',
                'icon': 'shield',
                'path': '/security',
                'roles': ['admin']
            },
            {
                'name': 'Analytics',
                'icon': 'chart',
                'path': '/analytics',
                'roles': ['admin', 'manager']
            },
            {
                'name': 'Settings',
                'icon': 'settings',
                'path': '/settings',
                'roles': ['admin']
            }
        ]
    },
    
    # Chart Configurations
    'CHARTS': {
        'traffic': {
            'types': ['line', 'bar'],
            'colors': {
                'upload': '#00ff00',
                'download': '#0000ff',
                'total': '#ff0000'
            },
            'intervals': ['hour', 'day', 'week', 'month']
        },
        'users': {
            'types': ['line', 'pie'],
            'colors': {
                'active': '#00ff00',
                'inactive': '#ff0000',
                'suspended': '#ffff00'
            }
        },
        'servers': {
            'types': ['gauge', 'line'],
            'colors': {
                'load': '#ff0000',
                'memory': '#00ff00',
                'disk': '#0000ff'
            },
            'thresholds': {
                'warning': 70,
                'critical': 90
            }
        }
    },
    
    # API Settings
    'API': {
        'version': 'v1',
        'prefix': '/api',
        'documentation_url': '/api/docs',
        'rate_limit': {
            'enabled': True,
            'requests_per_minute': 100
        },
        'cors': {
            'enabled': True,
            'origins': ['http://localhost:8080']
        }
    },
    
    # Notification Settings
    'NOTIFICATIONS': {
        'enabled': True,
        'polling_interval': 30,  # seconds
        'max_items': 100,
        'categories': {
            'system': {
                'color': '#ff0000',
                'icon': 'warning'
            },
            'user': {
                'color': '#00ff00',
                'icon': 'user'
            },
            'security': {
                'color': '#ffff00',
                'icon': 'shield'
            }
        }
    },
    
    # Export Settings
    'EXPORTS': {
        'formats': ['csv', 'json', 'pdf'],
        'max_rows': 10000,
        'timeout': 300,  # 5 minutes
        'path': str(Path(__file__).parent.parent.parent / 'exports')
    },
    
    # Cache Settings
    'CACHE': {
        'enabled': True,
        'backend': 'redis',
        'url': os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
        'timeout': 300,  # 5 minutes
        'key_prefix': 'dashboard:'
    }
}

# Role Permissions
ROLE_PERMISSIONS = {
    'admin': {
        'users': ['view', 'create', 'edit', 'delete'],
        'servers': ['view', 'create', 'edit', 'delete', 'restart'],
        'traffic': ['view', 'export'],
        'security': ['view', 'manage'],
        'analytics': ['view', 'export'],
        'settings': ['view', 'edit'],
        'api': ['access']
    },
    'manager': {
        'users': ['view', 'create', 'edit'],
        'servers': ['view', 'restart'],
        'traffic': ['view', 'export'],
        'security': ['view'],
        'analytics': ['view', 'export'],
        'settings': ['view'],
        'api': ['access']
    },
    'viewer': {
        'users': ['view'],
        'servers': ['view'],
        'traffic': ['view'],
        'security': [],
        'analytics': ['view'],
        'settings': [],
        'api': []
    }
}

# Action Logs
ACTION_LOGS = {
    'enabled': True,
    'retention_days': 90,
    'categories': {
        'auth': ['login', 'logout', 'failed_login'],
        'user': ['create', 'update', 'delete', 'suspend'],
        'server': ['create', 'update', 'delete', 'restart'],
        'settings': ['update'],
        'export': ['generate']
    }
}

# UI Components
UI_COMPONENTS = {
    'cards': {
        'default': {
            'shadow': True,
            'rounded': True,
            'padding': 'p-4'
        },
        'metric': {
            'shadow': True,
            'rounded': True,
            'padding': 'p-6',
            'class': 'bg-gradient'
        }
    },
    'buttons': {
        'primary': {
            'class': 'btn-primary',
            'rounded': True
        },
        'secondary': {
            'class': 'btn-secondary',
            'rounded': True
        },
        'danger': {
            'class': 'btn-danger',
            'rounded': True
        }
    },
    'tables': {
        'default': {
            'striped': True,
            'hover': True,
            'responsive': True
        }
    },
    'forms': {
        'default': {
            'validation': True,
            'responsive': True
        }
    }
}

# Chart Defaults
CHART_DEFAULTS = {
    'responsive': True,
    'maintainAspectRatio': False,
    'legend': {
        'display': True,
        'position': 'top'
    },
    'tooltips': {
        'enabled': True,
        'mode': 'index',
        'intersect': False
    },
    'scales': {
        'xAxes': [{
            'gridLines': {
                'display': False
            }
        }],
        'yAxes': [{
            'gridLines': {
                'display': True
            }
        }]
    }
} 