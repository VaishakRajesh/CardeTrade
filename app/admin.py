"""
CardeTrade Django Admin - Admin Panel Configuration

This module configures the Django admin interface for all models.
The admin panel provides a web-based interface for managing platform data.

Admin Features:
- Custom list displays for each model
- Filters for narrowing down records
- Search functionality
- Read-only fields for auto-generated data
- Organized fieldsets for user management

All models are registered with @admin.register() decorator.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, Farm, Batch, QualityVerification, Listing, Bid,
    Order, OrderTracking, Payment, Dispute, Notification,
    Conversation, ConversationParticipant, Message, Report, AuditLog
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom User admin configuration.

    Extends Django's UserAdmin to include:
    - Role field in list display and filters
    - Phone, region, address in personal info section
    - Role field in permissions section

    Customizations:
    - list_display: Shows key user info in table view
    - list_filter: Filter by role, staff status, active status
    - fieldsets: Organized sections for user details
    """
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
        """Admin action to mark selected users as verified."""
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'{updated} user(s) marked as verified.')
    verify_users.short_description = 'Mark selected users as verified'


@admin.register(Farm)
class FarmAdmin(admin.ModelAdmin):
    """
    Farm admin configuration.

    Displays farm name, owner, region, area, and creation date.
    Filterable by region.
    """
    list_display = ['farm_name', 'farmer', 'region', 'total_area_acres', 'created_at']
    list_filter = ['region']


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    """
    Batch admin configuration.

    Displays batch code, farmer, quantity, status, and creation date.
    Filterable by status and creation date.
    Searchable by batch code and farmer username.
    Batch code is read-only (auto-generated).
    """
    list_display = ['batch_code', 'farmer', 'quantity_kg', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['batch_code', 'farmer__username']
    readonly_fields = ['batch_code']  # Auto-generated, not editable


@admin.register(QualityVerification)
class QualityVerificationAdmin(admin.ModelAdmin):
    """
    QualityVerification admin configuration.

    Displays batch, grade, price, PM, and verification date.
    Filterable by grade.
    """
    list_display = ['batch', 'grade', 'verified_price_per_kg', 'product_manager', 'verified_at']
    list_filter = ['grade']


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    """
    Listing admin configuration.

    Displays listing ID, batch, type, price, quantity, and active status.
    Filterable by listing type and active status.
    """
    list_display = ['id', 'batch', 'listing_type', 'price_per_kg', 'available_qty_kg', 'is_active']
    list_filter = ['listing_type', 'is_active']


@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    """
    Bid admin configuration.

    Displays bid ID, listing, trader, price, quantity, status, and time.
    Filterable by status.
    """
    list_display = ['id', 'listing', 'trader', 'bid_price_per_kg', 'quantity_kg', 'status', 'bid_time']
    list_filter = ['status']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """
    Order admin configuration.

    Displays order code, buyer, seller, quantity, total, status, and date.
    Filterable by status and payment status.
    """
    list_display = ['order_code', 'buyer', 'seller', 'quantity_kg', 'total_amount', 'status', 'created_at']
    list_filter = ['status', 'payment_status']


@admin.register(OrderTracking)
class OrderTrackingAdmin(admin.ModelAdmin):
    """
    OrderTracking admin configuration.

    Displays order, status, location, updater, and timestamp.
    """
    list_display = ['order', 'status', 'location', 'updated_by', 'tracked_at']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """
    Payment admin configuration.

    Displays payment ID, order, amount, method, status, and date.
    Filterable by status and payment method.
    """
    list_display = ['id', 'order', 'amount', 'payment_method', 'status', 'paid_at']
    list_filter = ['status', 'payment_method']


@admin.register(Dispute)
class DisputeAdmin(admin.ModelAdmin):
    """
    Dispute admin configuration.

    Displays dispute ID, order, raiser, status, and date.
    Filterable by status.
    """
    list_display = ['id', 'order', 'raised_by', 'status', 'created_at']
    list_filter = ['status']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """
    Notification admin configuration.

    Displays user, type, read status, and date.
    Filterable by type and read status.
    """
    list_display = ['user', 'type', 'is_read', 'created_at']
    list_filter = ['type', 'is_read']


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    """
    Conversation admin configuration.

    Displays conversation ID, type, subject, status, and last message time.
    """
    list_display = ['id', 'type', 'subject', 'status', 'last_message_at']


@admin.register(ConversationParticipant)
class ConversationParticipantAdmin(admin.ModelAdmin):
    """
    ConversationParticipant admin configuration.

    Displays conversation, user, chat role, and active status.
    """
    list_display = ['conversation', 'user', 'role_in_chat', 'is_active']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """
    Message admin configuration.

    Displays message ID, conversation, sender, type, time, and deleted status.
    """
    list_display = ['id', 'conversation', 'sender', 'message_type', 'sent_at', 'is_deleted']


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    """
    Report admin configuration.

    Displays report type, generator, and creation date.
    """
    list_display = ['report_type', 'generated_by', 'created_at']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """
    AuditLog admin configuration.

    Displays user, action, table, record ID, and timestamp.
    Filterable by action and table name.
    All fields are read-only (audit logs cannot be modified).
    """
    list_display = ['user', 'action', 'table_name', 'record_id', 'logged_at']
    list_filter = ['action', 'table_name']
    # All fields read-only - audit logs cannot be modified
    readonly_fields = ['user', 'action', 'table_name', 'record_id', 'old_value', 'new_value', 'logged_at']
