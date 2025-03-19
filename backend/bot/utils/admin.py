"""
Admin interface for Utils module
"""

from django.contrib import admin

try:
    from utils.settings import SystemSetting
    
    @admin.register(SystemSetting)
    class SystemSettingAdmin(admin.ModelAdmin):
        """Admin interface for SystemSetting model"""
        
        list_display = ('key', 'value_display', 'is_json', 'updated_at')
        list_filter = ('is_json', 'created_at', 'updated_at')
        search_fields = ('key', 'description')
        readonly_fields = ('created_at', 'updated_at')
        fieldsets = (
            ('Setting Information', {
                'fields': ('key', 'description', 'is_json')
            }),
            ('Value', {
                'fields': ('value',)
            }),
            ('Timestamps', {
                'fields': ('created_at', 'updated_at'),
                'classes': ('collapse',)
            }),
        )
        
        def value_display(self, obj):
            """Display a truncated version of the value"""
            if not obj.value:
                return '-'
                
            value = obj.value
            if len(value) > 50:
                return f"{value[:50]}..."
            return value
        value_display.short_description = 'Value'
except ImportError:
    # SystemSetting model not available
    pass 