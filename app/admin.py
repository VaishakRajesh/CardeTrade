from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, Farm, Batch, QualityVerification, Listing, Bid,
    Order, OrderTracking, Payment, Dispute, Notification,
    Conversation, ConversationParticipant, Message, Report, AuditLog
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'role', 'is_staff', 'is_active']
    list_filter = ['role', 'is_staff', 'is_active']
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 'phone', 'region', 'address')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )


@admin.register(Farm)
class FarmAdmin(admin.ModelAdmin):
    list_display = ['farm_name', 'farmer', 'region', 'total_area_acres', 'created_at']
    list_filter = ['region']


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ['batch_code', 'farmer', 'quantity_kg', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['batch_code', 'farmer__username']
    readonly_fields = ['batch_code']


@admin.register(QualityVerification)
class QualityVerificationAdmin(admin.ModelAdmin):
    list_display = ['batch', 'grade', 'verified_price_per_kg', 'product_manager', 'verified_at']
    list_filter = ['grade']


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ['id', 'batch', 'listing_type', 'price_per_kg', 'available_qty_kg', 'is_active']
    list_filter = ['listing_type', 'is_active']


@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = ['id', 'listing', 'trader', 'bid_price_per_kg', 'quantity_kg', 'status', 'bid_time']
    list_filter = ['status']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_code', 'buyer', 'seller', 'quantity_kg', 'total_amount', 'status', 'created_at']
    list_filter = ['status', 'payment_status']


@admin.register(OrderTracking)
class OrderTrackingAdmin(admin.ModelAdmin):
    list_display = ['order', 'status', 'location', 'updated_by', 'tracked_at']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'amount', 'payment_method', 'status', 'paid_at']
    list_filter = ['status', 'payment_method']


@admin.register(Dispute)
class DisputeAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'raised_by', 'status', 'created_at']
    list_filter = ['status']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'type', 'is_read', 'created_at']
    list_filter = ['type', 'is_read']


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['id', 'type', 'subject', 'status', 'last_message_at']


@admin.register(ConversationParticipant)
class ConversationParticipantAdmin(admin.ModelAdmin):
    list_display = ['conversation', 'user', 'role_in_chat', 'is_active']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'conversation', 'sender', 'message_type', 'sent_at', 'is_deleted']


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['report_type', 'generated_by', 'created_at']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'table_name', 'record_id', 'logged_at']
    list_filter = ['action', 'table_name']
    readonly_fields = ['user', 'action', 'table_name', 'record_id', 'old_value', 'new_value', 'logged_at']
