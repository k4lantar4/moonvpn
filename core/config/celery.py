"""
Celery configuration for the V2Ray management system.

This module contains:
- Celery app configuration
- Task scheduling
- Task registration
"""

import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')

app = Celery('main')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# Configure Celery beat schedule
app.conf.beat_schedule = {
    # Server synchronization tasks
    'sync-servers': {
        'task': 'v2ray.tasks.sync_servers',
        'schedule': 300.0,  # Every 5 minutes
    },
    'monitor-servers': {
        'task': 'v2ray.tasks.monitor_servers',
        'schedule': 300.0,  # Every 5 minutes
    },
    'check-server-health': {
        'task': 'v2ray.tasks.check_server_health',
        'schedule': 900.0,  # Every 15 minutes
    },
    'cleanup-monitoring-data': {
        'task': 'v2ray.tasks.cleanup_old_monitoring_data',
        'schedule': crontab(hour=0, minute=0),  # Daily at midnight
    },
    'update-seller-commissions': {
        'task': 'v2ray.tasks.update_seller_commissions',
        'schedule': crontab(hour=0, minute=30),  # Daily at 00:30
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}') 