"""
Celery configuration for MoonVPN
"""

import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Create the Celery app
app = Celery('moonvpn')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# Configure Celery Beat schedule
app.conf.beat_schedule = {
    # VPN tasks
    'sync-all-vpn-servers': {
        'task': 'vpn.tasks.sync_all_servers',
        'schedule': 300.0,  # Every 5 minutes
    },
    'check-expired-vpn-accounts': {
        'task': 'vpn.tasks.check_expired_accounts',
        'schedule': 3600.0,  # Every hour
    },
    'check-vpn-traffic-limits': {
        'task': 'vpn.tasks.check_traffic_limits',
        'schedule': 3600.0,  # Every hour
    },
    'collect-vpn-server-metrics': {
        'task': 'vpn.tasks.collect_server_metrics',
        'schedule': 900.0,  # Every 15 minutes
    },
    'cleanup-old-vpn-metrics': {
        'task': 'vpn.tasks.cleanup_old_metrics',
        'schedule': 'crontab(hour=0, minute=0)',  # Daily at midnight
        'kwargs': {'days': 30},
    },
    
    # Existing tasks
    'check-expired-subscriptions': {
        'task': 'v2ray.tasks.check_expirations_task',
        'schedule': 3600.0,  # Every hour
    },
    'cleanup-old-notifications': {
        'task': 'main.tasks.cleanup_old_notifications',
        'schedule': 'crontab(hour=0, minute=0)',  # Daily at midnight
    },
    'process-pending-withdrawals': {
        'task': 'payments.tasks.process_pending_withdrawals',
        'schedule': 1800.0,  # Every 30 minutes
    },
    'sync-payment-gateways': {
        'task': 'payments.tasks.sync_payment_gateways',
        'schedule': 300.0,  # Every 5 minutes
    },
    'analyze-usage-patterns': {
        'task': 'analytics.tasks.analyze_usage_patterns',
        'schedule': 21600.0,  # Every 6 hours
    },
    'backup-system': {
        'task': 'main.tasks.backup_system',
        'schedule': 1800.0,  # Every 30 minutes
    },
    'generate-ai-content': {
        'task': 'content.tasks.generate_ai_content',
        'schedule': 21600.0,  # Every 6 hours
    },
    'cleanup-old-backups': {
        'task': 'main.tasks.cleanup_old_backups',
        'schedule': 'crontab(hour=0, minute=0)',  # Daily at midnight
    },
    'monitor-server-locations': {
        'task': 'v2ray.tasks.monitor_server_locations',
        'schedule': 300.0,  # Every 5 minutes
    },
    'balance-server-load': {
        'task': 'v2ray.tasks.balance_server_load',
        'schedule': 600.0,  # Every 10 minutes
    },
    'sync-3xui-panel': {
        'task': 'v2ray.tasks.sync_panel_task',
        'schedule': 300.0,  # Every 5 minutes
    },
    'sync-accounts': {
        'task': 'v2ray.tasks.sync_accounts_task',
        'schedule': 900.0,  # Every 15 minutes
    },
}

@app.task(bind=True)
def debug_task(self):
    """Debug task to print request"""
    print(f'Request: {self.request!r}') 