"""
accounts/admin.py

Admin configuration for accounts app models:
User, Conversation, Message, Dispute, Report, and AuditLog.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Conversation, ConversationParticipant, Message, Dispute, Report, AuditLog


# Admin config for the custom User model with role and verification fields
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'role', 'is_verified', 'is_staff', 'is_active']
    list_filter = ['role', 'is_verified', 'is_staff', 'is_active']
    search_fields = ['username', 'email']
    actions = ['verify_users']
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 'phone', 'region', 'address')}),
        ('Verification', {'fields': ('is_verified', 'verification_doc')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )

    def verify_users(self, request, queryset):
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'{updated} user(s) marked as verified.')
    verify_users.short_description = 'Mark selected users as verified'

    def disable_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} user(s) disabled.')
    disable_users.short_description = 'Disable selected users'


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['id', 'type', 'subject', 'status', 'last_message_at']


@admin.register(ConversationParticipant)
class ConversationParticipantAdmin(admin.ModelAdmin):
    list_display = ['conversation', 'user', 'role_in_chat', 'is_active']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'conversation', 'sender', 'message_type', 'sent_at', 'is_deleted']


@admin.register(Dispute)
class DisputeAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'raised_by', 'status', 'created_at']
    list_filter = ['status']


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['report_type', 'generated_by', 'created_at']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'table_name', 'record_id', 'logged_at']
    list_filter = ['action', 'table_name']
    readonly_fields = ['user', 'action', 'table_name', 'record_id', 'old_value', 'new_value', 'logged_at']
