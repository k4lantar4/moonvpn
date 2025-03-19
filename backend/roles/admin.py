from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import PermissionGroup, Permission, Role, UserRole, RoleChangeLog, RoleLog


class PermissionInline(admin.TabularInline):
    model = Permission
    extra = 0
    fields = ('name', 'codename', 'description')


@admin.register(PermissionGroup)
class PermissionGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'permissions_count')
    search_fields = ('name', 'description')
    inlines = [PermissionInline]
    
    def permissions_count(self, obj):
        return obj.permissions.count()
    permissions_count.short_description = _('Permissions')


class PermissionGroupFilter(admin.SimpleListFilter):
    title = _('Permission Group')
    parameter_name = 'group'
    
    def lookups(self, request, model_admin):
        groups = PermissionGroup.objects.all()
        return [(group.id, group.name) for group in groups]
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(group__id=self.value())
        return queryset


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ('codename', 'name')
    search_fields = ('codename', 'name')
    ordering = ('codename',)


class RolePermissionInline(admin.TabularInline):
    model = Role.permissions.through
    extra = 0
    verbose_name = _('Permission')
    verbose_name_plural = _('Permissions')
    autocomplete_fields = ('permission',)


class UserRoleInline(admin.TabularInline):
    model = UserRole
    extra = 0
    fields = ('user', 'assigned_by', 'assigned_at', 'expires_at', 'is_active')
    readonly_fields = ('assigned_at',)
    autocomplete_fields = ('user', 'assigned_by')


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'get_permissions_count', 'created_at', 'updated_at')
    search_fields = ('name', 'description')
    filter_horizontal = ('permissions',)
    readonly_fields = ('created_at', 'updated_at')
    
    def get_permissions_count(self, obj):
        return obj.permissions.count()
    get_permissions_count.short_description = 'Permissions'


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'assigned_by', 'assigned_at', 'expires_at', 'is_active')
    list_filter = ('role', 'is_active')
    search_fields = ('user__username', 'user__email', 'role__name')
    readonly_fields = ('assigned_at',)
    raw_id_fields = ('user', 'assigned_by')


@admin.register(RoleChangeLog)
class RoleChangeLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'role', 'user', 'performed_by', 'timestamp')
    list_filter = ('action', 'timestamp')
    search_fields = ('role__name', 'user__username', 'performed_by__username')
    readonly_fields = ('action', 'role', 'user', 'performed_by', 'timestamp', 'details')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(RoleLog)
class RoleLogAdmin(admin.ModelAdmin):
    list_display = ('role', 'action', 'user', 'timestamp')
    list_filter = ('action', 'timestamp')
    search_fields = ('role__name', 'user__username', 'details')
    readonly_fields = ('timestamp',)
    raw_id_fields = ('role', 'user') 