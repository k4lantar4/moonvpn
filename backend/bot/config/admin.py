from django.contrib import admin
from django.urls import path
from django.utils.html import format_html
from django.urls import reverse

# Customize admin site
admin.site.site_header = 'moonvpn Administration'
admin.site.site_title = 'moonvpn Admin'
admin.site.index_title = 'Welcome to moonvpn Administration'

# Add monitoring link to admin index
class moonvpnAdminSite(admin.AdminSite):
    """Customized admin site for moonvpn"""
    
    def get_urls(self):
        urls = super().get_urls()
        # Add your custom URLs here
        return urls
    
    def index(self, request, extra_context=None):
        """Add monitoring dashboard link to admin index page"""
        extra_context = extra_context or {}
        extra_context['monitoring_url'] = reverse('monitoring_dashboard')
        return super().index(request, extra_context)
        
# Register the custom admin site
admin_site = moonvpnAdminSite(name='moonvpn_admin')
admin.site = admin_site 