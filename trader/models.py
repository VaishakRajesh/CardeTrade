"""
trader/models.py

Defines trading-related models: Listing (auction), Bid, Order,
OrderTracking, and Payment for the cardamom marketplace.
"""

from django.db import models
from django.conf import settings
from django.db.models import F, ExpressionWrapper, DecimalField, GeneratedField
from django.utils import timezone
from farmer.models import Batch


# Represents an auction listing for a verified batch of cardamom
class Listing(models.Model):
    # Only auction type is currently supported
    class ListingType(models.TextChoices):
        AUCTION = 'auction', 'Auction'

    batch = models.OneToOneField(Batch, on_delete=models.CASCADE, related_name='listing')
    farmer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='listings')
    listing_type = models.CharField(max_length=20, choices=ListingType.choices, default=ListingType.AUCTION)
    price_per_kg = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Starting price per kg')
    min_order_kg = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    available_qty_kg = models.DecimalField(max_digits=10, decimal_places=2)
    auction_start_time = models.DateTimeField(null=True, blank=True)
    auction_end_time = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Auction {self.id} - {self.batch.batch_code}"

    # Returns the highest active bid for this listing
    @property
    def current_highest_bid(self):
        bid = self.bids.filter(status='active').order_by('-bid_price_per_kg').first()
        return bid

    # Returns the number of active bids (cached if annotated in queryset)
    @property
    def bid_count(self):
        if hasattr(self, '_bid_count_cache'):
            return self._bid_count_cache
        return self.bids.filter(status='active').count()

    @bid_count.setter
    def bid_count(self, value):
        self._bid_count_cache = value

    # Returns the time left before the auction ends, or None if expired
    @property
    def time_remaining(self):
        if not self.auction_end_time:
            return None
        remaining = self.auction_end_time - timezone.now()
        return remaining if remaining.total_seconds() > 0 else None


# Represents a bid placed by a trader on an auction listing
class Bid(models.Model):
    # Status: active, accepted, rejected, outbid, or expired
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


# Represents a confirmed purchase order between a trader (buyer) and farmer (seller)
class Order(models.Model):
    # Fulfillment status: pending → confirmed → processing → shipped → delivered
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        CONFIRMED = 'confirmed', 'Confirmed'
        PROCESSING = 'processing', 'Processing'
        SHIPPED = 'shipped', 'Shipped'
        DELIVERED = 'delivered', 'Delivered'
        CANCELLED = 'cancelled', 'Cancelled'
        DISPUTED = 'disputed', 'Disputed'

    # Payment status: unpaid, partially paid, paid, or refunded
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

    # Auto-generate order_code if not set (format: ORD-YYYY-NNNN)
    def save(self, *args, **kwargs):
        if not self.order_code:
            self.order_code = self._generate_order_code()
        super().save(*args, **kwargs)

    # Generate a sequential order code like ORD-2026-0001
    def _generate_order_code(self):
        year = timezone.now().year
        last = Order.objects.filter(order_code__startswith=f'ORD-{year}-').order_by('order_code').last()
        if last:
            num = int(last.order_code.split('-')[2]) + 1
        else:
            num = 1
        return f'ORD-{year}-{num:04d}'


# Tracks the shipment/fulfillment status of an order over time
class OrderTracking(models.Model):
    # Tracking status lifecycle: pending → confirmed → processing → shipped → delivered
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
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='tracking_updates')
    tracked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'order tracking'
        ordering = ['-tracked_at']

    def __str__(self):
        return f"Order {self.order.order_code} -> {self.status}"


# Records payments made by traders against orders
class Payment(models.Model):
    # Supported payment methods: bank transfer, mobile money, cash, escrow
    class PaymentMethod(models.TextChoices):
        BANK_TRANSFER = 'bank_transfer', 'Bank Transfer'
        MOBILE_MONEY = 'mobile_money', 'Mobile Money'
        CASH = 'cash', 'Cash'
        ESCROW = 'escrow', 'Escrow'

    # Payment status: pending, completed, failed, or refunded
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
