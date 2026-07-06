from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db.models import F, ExpressionWrapper, DecimalField, GeneratedField
from django.utils import timezone


class User(AbstractUser):
    class Role(models.TextChoices):
        FARMER = 'farmer', 'Farmer'
        TRADER = 'trader', 'Trader'
        PRODUCT_MANAGER = 'product_manager', 'Product Manager'
        ADMIN = 'admin', 'Admin'

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.FARMER)
    phone = models.CharField(max_length=20, blank=True, default='')
    address = models.TextField(blank=True, default='')
    region = models.CharField(max_length=100, blank=True, default='')

    def save(self, *args, **kwargs):
        if self.role == self.Role.ADMIN:
            self.is_staff = True
            self.is_superuser = True
        elif self.role == self.Role.PRODUCT_MANAGER:
            self.is_staff = True
            self.is_superuser = False
        else:
            self.is_staff = False
            self.is_superuser = False
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class Farm(models.Model):
    farmer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='farms',
        limit_choices_to={'role': 'farmer'}
    )
    farm_name = models.CharField(max_length=150)
    location = models.CharField(max_length=200, blank=True, default='')
    region = models.CharField(max_length=100, blank=True, default='')
    total_area_acres = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    certification = models.CharField(max_length=100, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'farms'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.farm_name} ({self.farmer.username})"


class Batch(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        UNDER_REVIEW = 'under_review', 'Under Review'
        VERIFIED = 'verified', 'Verified'
        LISTED = 'listed', 'Listed'
        SOLD = 'sold', 'Sold'
        REJECTED = 'rejected', 'Rejected'

    batch_code = models.CharField(max_length=50, unique=True, editable=False)
    farmer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='batches',
        limit_choices_to={'role': 'farmer'}
    )
    farm = models.ForeignKey(Farm, on_delete=models.SET_NULL, null=True, related_name='batches')
    quantity_kg = models.DecimalField(max_digits=10, decimal_places=2)
    harvest_date = models.DateField()
    description = models.TextField(blank=True, default='')
    estimated_price_per_kg = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'batches'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.batch_code} ({self.status})"

    def save(self, *args, **kwargs):
        if not self.batch_code:
            self.batch_code = self._generate_batch_code()
        super().save(*args, **kwargs)

    def _generate_batch_code(self):
        year = timezone.now().year
        last = Batch.objects.filter(batch_code__startswith=f'CDM-{year}-').order_by('batch_code').last()
        if last:
            num = int(last.batch_code.split('-')[2]) + 1
        else:
            num = 1
        return f'CDM-{year}-{num:04d}'


class QualityVerification(models.Model):
    class Grade(models.TextChoices):
        A = 'A', 'Grade A'
        B = 'B', 'Grade B'
        C = 'C', 'Grade C'

    batch = models.OneToOneField(Batch, on_delete=models.CASCADE, related_name='verification')
    product_manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='verifications'
    )
    grade = models.CharField(max_length=1, choices=Grade.choices)
    moisture_content_pct = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    aroma_score = models.PositiveSmallIntegerField(null=True, blank=True)
    color_score = models.PositiveSmallIntegerField(null=True, blank=True)
    purity_pct = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    verified_price_per_kg = models.DecimalField(max_digits=10, decimal_places=2)
    remarks = models.TextField(blank=True, default='')
    verified_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'quality verifications'

    def __str__(self):
        return f"Batch {self.batch.batch_code} -> Grade {self.grade}"


class Listing(models.Model):
    class ListingType(models.TextChoices):
        FIXED_PRICE = 'fixed_price', 'Fixed Price'
        AUCTION = 'auction', 'Auction'

    batch = models.OneToOneField(Batch, on_delete=models.CASCADE, related_name='listing')
    farmer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='listings')
    listing_type = models.CharField(max_length=20, choices=ListingType.choices)
    price_per_kg = models.DecimalField(max_digits=10, decimal_places=2)
    min_order_kg = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    available_qty_kg = models.DecimalField(max_digits=10, decimal_places=2)
    auction_start_time = models.DateTimeField(null=True, blank=True)
    auction_end_time = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Listing {self.id} - {self.batch.batch_code} ({self.listing_type})"


class Bid(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        ACCEPTED = 'accepted', 'Accepted'
        REJECTED = 'rejected', 'Rejected'
        OUTBID = 'outbid', 'Outbid'
        EXPIRED = 'expired', 'Expired'

    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='bids')
    trader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bids',
        limit_choices_to={'role': 'trader'}
    )
    bid_price_per_kg = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_kg = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    notes = models.TextField(blank=True, default='')
    bid_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-bid_price_per_kg']

    def __str__(self):
        return f"Bid {self.id}: Rs{self.bid_price_per_kg}/kg by {self.trader.username}"


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        CONFIRMED = 'confirmed', 'Confirmed'
        PROCESSING = 'processing', 'Processing'
        SHIPPED = 'shipped', 'Shipped'
        DELIVERED = 'delivered', 'Delivered'
        CANCELLED = 'cancelled', 'Cancelled'
        DISPUTED = 'disputed', 'Disputed'

    class PaymentStatus(models.TextChoices):
        UNPAID = 'unpaid', 'Unpaid'
        PARTIALLY_PAID = 'partially_paid', 'Partially Paid'
        PAID = 'paid', 'Paid'
        REFUNDED = 'refunded', 'Refunded'

    order_code = models.CharField(max_length=50, unique=True, editable=False)
    listing = models.ForeignKey(Listing, on_delete=models.SET_NULL, null=True, related_name='orders')
    batch = models.ForeignKey(Batch, on_delete=models.SET_NULL, null=True, related_name='orders')
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='purchases',
        limit_choices_to={'role': 'trader'}
    )
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sales',
        limit_choices_to={'role': 'farmer'}
    )
    bid = models.ForeignKey(Bid, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    quantity_kg = models.DecimalField(max_digits=10, decimal_places=2)
    price_per_kg = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = GeneratedField(
        expression=ExpressionWrapper(
            F('quantity_kg') * F('price_per_kg'),
            output_field=DecimalField(max_digits=12, decimal_places=2)
        ),
        output_field=DecimalField(max_digits=12, decimal_places=2),
        db_persist=True
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    payment_status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.UNPAID)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.order_code} - {self.status}"

    def save(self, *args, **kwargs):
        if not self.order_code:
            self.order_code = self._generate_order_code()
        super().save(*args, **kwargs)

    def _generate_order_code(self):
        year = timezone.now().year
        last = Order.objects.filter(order_code__startswith=f'ORD-{year}-').order_by('order_code').last()
        if last:
            num = int(last.order_code.split('-')[2]) + 1
        else:
            num = 1
        return f'ORD-{year}-{num:04d}'


class OrderTracking(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        CONFIRMED = 'confirmed', 'Confirmed'
        PROCESSING = 'processing', 'Processing'
        SHIPPED = 'shipped', 'Shipped'
        DELIVERED = 'delivered', 'Delivered'
        CANCELLED = 'cancelled', 'Cancelled'

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='tracking_entries')
    status = models.CharField(max_length=20, choices=Status.choices)
    location = models.CharField(max_length=200, blank=True, default='')
    notes = models.TextField(blank=True, default='')
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='tracking_updates'
    )
    tracked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'order tracking'
        ordering = ['-tracked_at']

    def __str__(self):
        return f"Order {self.order.order_code} -> {self.status}"


class Payment(models.Model):
    class PaymentMethod(models.TextChoices):
        BANK_TRANSFER = 'bank_transfer', 'Bank Transfer'
        MOBILE_MONEY = 'mobile_money', 'Mobile Money'
        CASH = 'cash', 'Cash'
        ESCROW = 'escrow', 'Escrow'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'
        REFUNDED = 'refunded', 'Refunded'

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    payer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices)
    transaction_ref = models.CharField(max_length=100, unique=True, null=True, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment {self.id}: Rs{self.amount} ({self.status})"


class Dispute(models.Model):
    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        UNDER_REVIEW = 'under_review', 'Under Review'
        RESOLVED = 'resolved', 'Resolved'
        CLOSED = 'closed', 'Closed'

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='disputes')
    raised_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='disputes_raised')
    against_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='disputes_against')
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    resolution = models.TextField(blank=True, default='')
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='disputes_resolved'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Dispute {self.id} - Order {self.order.order_code} ({self.status})"


class Notification(models.Model):
    class Type(models.TextChoices):
        BID_RECEIVED = 'bid_received', 'Bid Received'
        BID_ACCEPTED = 'bid_accepted', 'Bid Accepted'
        ORDER_PLACED = 'order_placed', 'Order Placed'
        ORDER_SHIPPED = 'order_shipped', 'Order Shipped'
        PAYMENT_RECEIVED = 'payment_received', 'Payment Received'
        BATCH_VERIFIED = 'batch_verified', 'Batch Verified'
        DISPUTE_RAISED = 'dispute_raised', 'Dispute Raised'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=30, choices=Type.choices)
    message = models.TextField()
    reference_id = models.IntegerField(null=True, blank=True)
    reference_type = models.CharField(max_length=50, blank=True, default='')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.type}] {self.message[:50]}"


class Conversation(models.Model):
    class Type(models.TextChoices):
        QUALITY_REVIEW = 'quality_review', 'Quality Review'
        BATCH_INQUIRY = 'batch_inquiry', 'Batch Inquiry'
        ORDER_SUPPORT = 'order_support', 'Order Support'
        GENERAL = 'general', 'General'

    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        ARCHIVED = 'archived', 'Archived'
        LOCKED = 'locked', 'Locked'

    batch = models.ForeignKey(Batch, on_delete=models.SET_NULL, null=True, blank=True, related_name='conversations')
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='conversations')
    type = models.CharField(max_length=20, choices=Type.choices)
    subject = models.CharField(max_length=200, blank=True, default='')
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)
    last_message_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-last_message_at']

    def __str__(self):
        return f"Conversation {self.id} ({self.type})"


class ConversationParticipant(models.Model):
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


class Message(models.Model):
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


class Report(models.Model):
    class ReportType(models.TextChoices):
        TRADE_SUMMARY = 'trade_summary', 'Trade Summary'
        GRADE_DISTRIBUTION = 'grade_distribution', 'Grade Distribution'
        FARMER_PERFORMANCE = 'farmer_performance', 'Farmer Performance'
        TRADER_ACTIVITY = 'trader_activity', 'Trader Activity'
        REVENUE = 'revenue', 'Revenue'

    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='generated_reports'
    )
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


class AuditLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    action = models.CharField(max_length=100)
    table_name = models.CharField(max_length=50)
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
