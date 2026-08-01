"""
accounts/models.py

Defines the core data models for the CardeTrade platform:
User (custom auth), Conversation, ConversationParticipant,
Message, Dispute, Report, and AuditLog.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.utils import timezone

# Custom user model with role-based authentication
class User(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    # Enum of platform roles: Farmer, Trader, Product Manager, Admin
    class Role(models.TextChoices):
        FARMER = 'farmer', 'Farmer'
        TRADER = 'trader', 'Trader'
        PRODUCT_MANAGER = 'product_manager', 'Product Manager'
        ADMIN = 'admin', 'Admin'

    email = models.EmailField(unique=True, blank=False, null=False)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.FARMER)
    phone = models.CharField(max_length=20, blank=True, default='')
    address = models.TextField(blank=True, default='')
    region = models.CharField(max_length=100, blank=True, default='')
    is_verified = models.BooleanField(default=False)
    verification_doc = models.FileField(upload_to='documents/verification/', null=True, blank=True)

    # Auto-set is_staff/is_superuser based on role; admins are always verified
    def save(self, *args, **kwargs):
        if self.role == self.Role.ADMIN:
            self.is_staff = True
            self.is_superuser = True
            self.is_verified = True
        elif self.role == self.Role.PRODUCT_MANAGER:
            self.is_staff = True
            self.is_superuser = False
        elif self.role == self.Role.TRADER:
            self.is_staff = False
            self.is_superuser = False
            self.is_verified = True
        else:
            self.is_staff = False
            self.is_superuser = False
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"


# Represents a messaging conversation between users (linked to batch or order)
class Conversation(models.Model):
    # Conversation types: quality review, batch inquiry, order support, general
    class Type(models.TextChoices):
        QUALITY_REVIEW = 'quality_review', 'Quality Review'
        BATCH_INQUIRY = 'batch_inquiry', 'Batch Inquiry'
        ORDER_SUPPORT = 'order_support', 'Order Support'
        GENERAL = 'general', 'General'

    # Conversation visibility status: open, archived, or locked
    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        ARCHIVED = 'archived', 'Archived'
        LOCKED = 'locked', 'Locked'

    batch = models.ForeignKey('farmer.Batch', on_delete=models.SET_NULL, null=True, blank=True, related_name='conversations')
    order = models.ForeignKey('trader.Order', on_delete=models.SET_NULL, null=True, blank=True, related_name='conversations')
    type = models.CharField(max_length=20, choices=Type.choices)
    subject = models.CharField(max_length=200, blank=True, default='')
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)
    last_message_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-last_message_at']

    def __str__(self):
        return f"Conversation {self.id} ({self.type})"


# Links a user to a conversation with their role and read status
class ConversationParticipant(models.Model):
    # Role the participant plays within this specific conversation
    class RoleInChat(models.TextChoices):
        FARMER = 'farmer', 'Farmer'
        PRODUCT_MANAGER = 'product_manager', 'Product Manager'
        TRADER = 'trader', 'Trader'
        ADMIN = 'admin', 'Admin'

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='conversation_participations')
    role_in_chat = models.CharField(max_length=20, choices=RoleInChat.choices)
    joined_at = models.DateTimeField(auto_now_add=True)
    last_read_at = models.DateTimeField(null=True, blank=True)
    is_muted = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('conversation', 'user')

    def __str__(self):
        return f"{self.user.username} in Conversation {self.conversation.id}"


# Individual message within a conversation (supports text, images, documents)
class Message(models.Model):
    # Type of message content: text, image, document, or system-generated
    class MessageType(models.TextChoices):
        TEXT = 'text', 'Text'
        IMAGE = 'image', 'Image'
        DOCUMENT = 'document', 'Document'
        SYSTEM = 'system', 'System'

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='sent_messages')
    message_type = models.CharField(max_length=10, choices=MessageType.choices, default=MessageType.TEXT)
    content = models.TextField(blank=True, default='')
    attachments = models.JSONField(null=True, blank=True, default=list)
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sent_at']

    def __str__(self):
        return f"Message {self.id} in Conversation {self.conversation.id}"


# Tracks disputes raised on orders between buyers and sellers
class Dispute(models.Model):
    # Lifecycle: open → under_review → resolved → closed
    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        UNDER_REVIEW = 'under_review', 'Under Review'
        RESOLVED = 'resolved', 'Resolved'
        CLOSED = 'closed', 'Closed'

    order = models.ForeignKey('trader.Order', on_delete=models.CASCADE, related_name='disputes')
    raised_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='disputes_raised')
    against_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='disputes_against')
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    resolution = models.TextField(blank=True, default='')
    resolved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='disputes_resolved')
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Dispute {self.id} - Order {self.order.order_code} ({self.status})"


# Stores generated analytical reports (trade summary, grade distribution, etc.)
class Report(models.Model):
    # Types of reports that can be generated
    class ReportType(models.TextChoices):
        TRADE_SUMMARY = 'trade_summary', 'Trade Summary'
        GRADE_DISTRIBUTION = 'grade_distribution', 'Grade Distribution'
        FARMER_PERFORMANCE = 'farmer_performance', 'Farmer Performance'
        TRADER_ACTIVITY = 'trader_activity', 'Trader Activity'
        REVENUE = 'revenue', 'Revenue'

    generated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='generated_reports')
    report_type = models.CharField(max_length=30, choices=ReportType.choices)
    date_from = models.DateField(null=True, blank=True)
    date_to = models.DateField(null=True, blank=True)
    parameters = models.JSONField(null=True, blank=True, default=dict)
    file_path = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_report_type_display()} - {self.created_at.date()}"


# Immutable audit trail for all data mutations across the platform
class AuditLog(models.Model):
    # Enum of all tracked database tables
    class TableType(models.TextChoices):
        USER = 'auth_user', 'User'
        FARM = 'farm', 'Farm'
        BATCH = 'batch', 'Batch'
        QUALITY_VERIFICATION = 'qualityverification', 'Quality Verification'
        LISTING = 'listing', 'Listing'
        BID = 'bid', 'Bid'
        ORDER = 'order', 'Order'
        ORDER_TRACKING = 'ordertracking', 'Order Tracking'
        PAYMENT = 'payment', 'Payment'
        DISPUTE = 'dispute', 'Dispute'
        CONVERSATION = 'conversation', 'Conversation'
        MESSAGE = 'message', 'Message'
        REPORT = 'report', 'Report'
        AUDIT_LOG = 'auditlog', 'Audit Log'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    action = models.CharField(max_length=100)
    table_name = models.CharField(max_length=50, choices=TableType.choices)
    record_id = models.IntegerField()
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    ip_address = models.CharField(max_length=45, blank=True, default='')
    logged_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'audit logs'
        ordering = ['-logged_at']
        indexes = [
            models.Index(fields=['table_name', 'record_id']),
            models.Index(fields=['action']),
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"[{self.logged_at}] {self.action} on {self.table_name}#{self.record_id}"
