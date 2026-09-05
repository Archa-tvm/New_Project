from django.contrib import admin
from .models import Tenant, TenantMembership, AuditLog

@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'plan', 'is_active', 'created_at')
    search_fields = ('name', 'slug', 'contact_email')
    list_filter = ('plan', 'is_active')

@admin.register(TenantMembership)
class TenantMembershipAdmin(admin.ModelAdmin):
    list_display = ('tenant', 'user', 'role', 'is_active', 'joined_at')
    list_filter = ('role', 'is_active')
    search_fields = ('user__username', 'tenant__name')

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'tenant', 'actor', 'action', 'resource_type', 'resource_id')
    list_filter = ('action', 'resource_type', 'tenant')
    search_fields = ('resource_id', 'actor__username')
