"""
Django Admin configuration for AuditLog model (PRD Ch. 26.8 & Ch. 29.8).
Internal debugging only. Access restricted to authorized superuser accounts.
"""
from django.contrib import admin
from apps.audit.models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'event_type', 'user', 'created_at')
    list_filter = ('event_type', 'created_at')
    search_fields = ('event_type', 'user__email')
    readonly_fields = ('id', 'user', 'event_type', 'metadata', 'created_at')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
