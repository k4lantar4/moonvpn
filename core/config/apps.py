from django.apps import AppConfig

class ConfigConfig(AppConfig):
    name = 'config'
    verbose_name = 'Configuration'

    def ready(self):
        try:
            # Import celery app here to avoid circular imports
            from .celery import app as celery_app
            __all__ = ('celery_app',)
        except ImportError:
            pass 