from django.contrib import admin
from .models import SystemSettings

@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    """Admin interface for SystemSettings model"""
    
    list_display = [
        'site_name',
        'maintenance_mode',
        'enable_2fa',
        'enable_email_notifications',
        'enable_telegram_notifications',
        'enable_card_payment',
        'default_language',
        'enable_rtl',
        'updated_at',
    ]
    
    list_filter = [
        'maintenance_mode',
        'enable_2fa',
        'enable_email_notifications',
        'enable_telegram_notifications',
        'enable_card_payment',
        'default_language',
        'enable_rtl',
    ]
    
    readonly_fields = ['created_at', 'updated_at']
    
    def has_add_permission(self, request):
        # Only allow one instance
        return not SystemSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False 