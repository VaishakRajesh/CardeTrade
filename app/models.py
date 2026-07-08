"""
CardeTrade Django Models - All 16 Database Tables

This module defines all the database models for the CardeTrade cardamom trading platform.
Each model represents a database table with fields, relationships, and business logic.

Models Overview:
- User: Extended user model with role-based access (Farmer, Trader, PM, Admin)
- Farm: Farm information linked to farmers
- Batch: Cardamom batches created by farmers
- QualityVerification: Quality checks performed by product managers
- Listing: Products available for sale (fixed price or auction)
- Bid: Trader bids on auction listings
- Order: Purchase orders between traders and farmers
- OrderTracking: Status tracking for orders
- Payment: Payment records for orders
- Dispute: Order disputes between users
- Notification: User notifications
- Conversation: Messaging conversations
- ConversationParticipant: Users participating in conversations
- Message: Individual chat messages
- Report: Generated platform reports
- AuditLog: System audit trail for all changes
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db.models import F, ExpressionWrapper, DecimalField, GeneratedField
from django.utils import timezone


class User(AbstractUser):
    """
    Extended User model with role-based access control.

    Inherits from AbstractUser to get all standard Django auth fields (username,
    email, password, is_active, etc.) and adds platform-specific fields.

    Authentication uses email as the primary identifier (USERNAME_FIELD = 'email'),
    so users log in with email + password, not username + password.

    Roles:
    - Farmer: Can create farms, batches, and list products for sale
    - Trader: Can browse listings, place bids, and make purchases
    - Product Manager: Can verify batches, set quality grades, and review products
    - Admin: Full system access including admin panel

    The save() method automatically sets is_staff and is_superuser based on role:
    - Admin gets both is_staff=True and is_superuser=True
    - Product Manager gets is_staff=True but is_superuser=False
    - Farmer and Trader get both as False
    """

    # Use email as the unique identifier for authentication instead of username
    USERNAME_FIELD = 'email'
    # Username is still required but no longer the primary login identifier
    REQUIRED_FIELDS = ['username']

    class Role(models.TextChoices):
        FARMER = 'farmer', 'Farmer'
        TRADER = 'trader', 'Trader'
        PRODUCT_MANAGER = 'product_manager', 'Product Manager'
        ADMIN = 'admin', 'Admin'

    # Override email to be unique and required for authentication
    email = models.EmailField(unique=True, blank=False, null=False)
    # Platform-specific user fields
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.FARMER)
    phone = models.CharField(max_length=20, blank=True, default='')  # Contact phone number
    address = models.TextField(blank=True, default='')  # Physical address
    region = models.CharField(max_length=100, blank=True, default='')  # Geographic region

    def save(self, *args, **kwargs):
        """
        Override save to automatically set staff/superuser status based on role.
        This ensures admin panel access is always consistent with the user's role.
        """
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
        """Return email with role display for admin and templates."""
        return f"{self.email} ({self.get_role_display()})"


class Farm(models.Model):
    """
    Farm model representing a cardamom farm owned by a farmer.

    Each farmer can have multiple farms. Farm information is used to:
    - Track where cardamom batches originate from
    - Display farm details on batch listings
    - Enable geographic filtering of products

    Relationships:
    - farmer (FK -> User): The farmer who owns this farm
    - batches (reverse FK from Batch): All batches produced on this farm
    """

    farmer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='farms',
        limit_choices_to={'role': 'farmer'}  # Only farmers can own farms
    )
    farm_name = models.CharField(max_length=150)  # Name of the farm
    location = models.CharField(max_length=200, blank=True, default='')  # Specific location/address
    region = models.CharField(max_length=100, blank=True, default='')  # Geographic region
    total_area_acres = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)  # Farm size
    certification = models.CharField(max_length=100, blank=True, default='')  # Organic/fair-trade certs
    created_at = models.DateTimeField(auto_now_add=True)  # When the farm was registered

    class Meta:
        verbose_name_plural = 'farms'  # Fix plural in Django admin
        ordering = ['-created_at']  # Newest farms first

    def __str__(self):
        """Return farm name with owner for display."""
        return f"{self.farm_name} ({self.farmer.username})"


class Batch(models.Model):
    """
    Batch model representing a cardamom harvest batch.

    A batch is created by a farmer when they harvest cardamom. It goes through
    a workflow: pending -> under_review -> verified -> listed -> sold (or rejected).

    The batch_code is auto-generated in format: CDM-YYYY-NNNN
    (e.g., CDM-2026-0001 for the first batch of 2026)

    Status Flow:
    - PENDING: Newly created, awaiting PM review
    - UNDER_REVIEW: PM has selected batch for quality verification
    - VERIFIED: PM completed quality check, listing will be auto-created
    - LISTED: Batch is available for purchase on the marketplace
    - SOLD: All quantity has been purchased
    - REJECTED: Batch failed quality verification

    Relationships:
    - farmer (FK -> User): The farmer who created this batch
    - farm (FK -> Farm): The farm where this batch was harvested
    - verification (reverse FK from QualityVerification): Quality check results
    - listing (reverse FK from Listing): Marketplace listing for this batch
    - orders (reverse FK from Order): Purchase orders for this batch
    - conversations (reverse FK from Conversation): Discussions about this batch
    """

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'  # Awaiting PM review
        UNDER_REVIEW = 'under_review', 'Under Review'  # PM is reviewing
        VERIFIED = 'verified', 'Verified'  # Quality check passed
        LISTED = 'listed', 'Listed'  # Available for purchase
        SOLD = 'sold', 'Sold'  # All quantity purchased
        REJECTED = 'rejected', 'Rejected'  # Failed quality check

    batch_code = models.CharField(max_length=50, unique=True, editable=False)  # Auto-generated code
    farmer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='batches',
        limit_choices_to={'role': 'farmer'}  # Only farmers can create batches
    )
    farm = models.ForeignKey(Farm, on_delete=models.SET_NULL, null=True, related_name='batches')
    quantity_kg = models.DecimalField(max_digits=10, decimal_places=2)  # Harvest quantity
    harvest_date = models.DateField()  # When the cardamom was harvested
    description = models.TextField(blank=True, default='')  # Batch description/notes
    estimated_price_per_kg = models.DecimalField(max_digits=10, decimal_places=2)  # Farmer's asking price
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)  # When batch was created
    updated_at = models.DateTimeField(auto_now=True)  # Last status update

    class Meta:
        verbose_name_plural = 'batches'  # Fix plural in Django admin
        ordering = ['-created_at']  # Newest batches first

    def __str__(self):
        """Return batch code with status for display."""
        return f"{self.batch_code} ({self.status})"

    def save(self, *args, **kwargs):
        """
        Override save to auto-generate batch_code if not set.
        This ensures every batch gets a unique code like CDM-2026-0001.
        """
        if not self.batch_code:
            self.batch_code = self._generate_batch_code()
        super().save(*args, **kwargs)

    def _generate_batch_code(self):
        """
        Generate a unique batch code in format: CDM-YYYY-NNNN

        The code includes the current year and a 4-digit sequential number.
        Example: CDM-2026-0001, CDM-2026-0002, etc.

        Returns:
            str: Generated batch code
        """
        year = timezone.now().year
        # Find the last batch code for this year
        last = Batch.objects.filter(batch_code__startswith=f'CDM-{year}-').order_by('batch_code').last()
        if last:
            # Increment the last number by 1
            num = int(last.batch_code.split('-')[2]) + 1
        else:
            # First batch of the year
            num = 1
        return f'CDM-{year}-{num:04d}'


class QualityVerification(models.Model):
    """
    Quality verification record for a cardamom batch.

    Created by a Product Manager after physically inspecting a batch.
    Contains quality metrics and the final grade assigned to the batch.

    Grade System:
    - A: Premium quality (highest price)
    - B: Good quality (standard price)
    - C: Lower quality (reduced price)

    After verification, the batch status changes to 'verified' and a
    Listing is automatically created via the post_save signal.

    Relationships:
    - batch (OneToOne -> Batch): The batch being verified (one batch = one verification)
    - product_manager (FK -> User): The PM who performed the verification
    """

    class Grade(models.TextChoices):
        A = 'A', 'Grade A'  # Premium quality
        B = 'B', 'Grade B'  # Good quality
        C = 'C', 'Grade C'  # Lower quality

    batch = models.OneToOneField(Batch, on_delete=models.CASCADE, related_name='verification')
    product_manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='verifications'  # PM's verification history
    )
    grade = models.CharField(max_length=1, choices=Grade.choices)  # Quality grade (A/B/C)
    moisture_content_pct = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # Moisture %
    aroma_score = models.PositiveSmallIntegerField(null=True, blank=True)  # Aroma rating (1-10)
    color_score = models.PositiveSmallIntegerField(null=True, blank=True)  # Color rating (1-10)
    purity_pct = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # Purity %
    verified_price_per_kg = models.DecimalField(max_digits=10, decimal_places=2)  # Final verified price
    remarks = models.TextField(blank=True, default='')  # Additional notes
    verified_at = models.DateTimeField(auto_now_add=True)  # When verification was completed

    class Meta:
        verbose_name_plural = 'quality verifications'  # Fix plural in Django admin

    def __str__(self):
        """Return batch code with grade for display."""
        return f"Batch {self.batch.batch_code} -> Grade {self.grade}"


class Listing(models.Model):
    """
    Marketplace listing for a cardamom batch.

    Created automatically when a batch is verified, or can be manually created
    by farmers. Traders can purchase via fixed price or bid in auctions.

    Listing Types:
    - FIXED_PRICE: Buy immediately at the set price
    - AUCTION: Bidding system, highest bidder wins

    The available_qty_kg decreases as orders are placed until it reaches 0
    (listing becomes inactive).

    Relationships:
    - batch (OneToOne -> Batch): The batch being listed (one batch = one listing)
    - farmer (FK -> User): The farmer selling this batch
    - bids (reverse FK from Bid): Auction bids on this listing
    - orders (reverse FK from Order): Purchase orders for this listing
    """

    class ListingType(models.TextChoices):
        FIXED_PRICE = 'fixed_price', 'Fixed Price'  # Buy at set price
        AUCTION = 'auction', 'Auction'  # Bidding system

    batch = models.OneToOneField(Batch, on_delete=models.CASCADE, related_name='listing')
    farmer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='listings')
    listing_type = models.CharField(max_length=20, choices=ListingType.choices)  # Fixed price or auction
    price_per_kg = models.DecimalField(max_digits=10, decimal_places=2)  # Price per kilogram
    min_order_kg = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Minimum order
    available_qty_kg = models.DecimalField(max_digits=10, decimal_places=2)  # Remaining quantity
    auction_start_time = models.DateTimeField(null=True, blank=True)  # For auctions: when bidding opens
    auction_end_time = models.DateTimeField(null=True, blank=True)  # For auctions: when bidding closes
    is_active = models.BooleanField(default=True)  # Whether listing is visible/available
    created_at = models.DateTimeField(auto_now_add=True)  # When listing was created

    class Meta:
        ordering = ['-created_at']  # Newest listings first

    def __str__(self):
        """Return listing ID with batch code and type for display."""
        return f"Listing {self.id} - {self.batch.batch_code} ({self.listing_type})"


class Bid(models.Model):
    """
    Bid placed by a trader on an auction listing.

    Only traders can place bids on auction-type listings. Bids are ranked
    by price (highest first). The farmer can accept the winning bid.

    Bid Status Flow:
    - ACTIVE: Current highest bid (or under consideration)
    - ACCEPTED: Farmer accepted this bid, order will be created
    - REJECTED: Farmer rejected this bid
    - OUTBID: Another trader placed a higher bid
    - EXPIRED: Auction ended without accepting this bid

    Relationships:
    - listing (FK -> Listing): The auction listing being bid on
    - trader (FK -> User): The trader who placed this bid
    - orders (reverse FK from Order): Order created if bid is accepted
    """

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'  # Current highest bid
        ACCEPTED = 'accepted', 'Accepted'  # Farmer accepted
        REJECTED = 'rejected', 'Rejected'  # Farmer rejected
        OUTBID = 'outbid', 'Outbid'  # Higher bid received
        EXPIRED = 'expired', 'Expired'  # Auction ended

    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='bids')
    trader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bids',
        limit_choices_to={'role': 'trader'}  # Only traders can bid
    )
    bid_price_per_kg = models.DecimalField(max_digits=10, decimal_places=2)  # Trader's offered price
    quantity_kg = models.DecimalField(max_digits=10, decimal_places=2)  # Quantity they want to buy
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    notes = models.TextField(blank=True, default='')  # Optional message to farmer
    bid_time = models.DateTimeField(auto_now_add=True)  # When bid was placed

    class Meta:
        ordering = ['-bid_price_per_kg']  # Highest bid first

    def __str__(self):
        """Return bid ID with price and trader for display."""
        return f"Bid {self.id}: Rs{self.bid_price_per_kg}/kg by {self.trader.username}"


class Order(models.Model):
    """
    Purchase order for cardamom between a trader (buyer) and farmer (seller).

    Created when:
    - A trader buys a fixed-price listing directly
    - A farmer accepts a trader's bid on an auction listing

    The order tracks the transaction from creation to delivery, including
    payment status and shipping status.

    Order Status Flow:
    - PENDING: Order created, awaiting confirmation
    - CONFIRMED: Farmer confirmed the order
    - PROCESSING: Farmer is preparing the shipment
    - SHIPPED: Batch has been shipped
    - DELIVERED: Trader received the batch
    - CANCELLED: Order was cancelled by either party
    - DISPUTED: A dispute has been raised about this order

    Payment Status:
    - UNPAID: No payment received
    - PARTIALLY_PAID: Some payment received
    - PAID: Full payment received
    - REFUNDED: Payment was refunded

    Relationships:
    - listing (FK -> Listing): The listing being purchased
    - batch (FK -> Batch): The batch being purchased
    - buyer (FK -> User): The trader purchasing
    - seller (FK -> User): The farmer selling
    - bid (FK -> Bid): The winning bid (if auction purchase)
    - tracking_entries (reverse FK from OrderTracking): Status updates
    - payments (reverse FK from Payment): Payment records
    - disputes (reverse FK from Dispute): Any disputes raised
    - conversations (reverse FK from Conversation): Support discussions
    """

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'  # Order just created
        CONFIRMED = 'confirmed', 'Confirmed'  # Farmer confirmed
        PROCESSING = 'processing', 'Processing'  # Being prepared
        SHIPPED = 'shipped', 'Shipped'  # In transit
        DELIVERED = 'delivered', 'Delivered'  # Received by buyer
        CANCELLED = 'cancelled', 'Cancelled'  # Cancelled by either party
        DISPUTED = 'disputed', 'Disputed'  # Dispute raised

    class PaymentStatus(models.TextChoices):
        UNPAID = 'unpaid', 'Unpaid'  # No payment yet
        PARTIALLY_PAID = 'partially_paid', 'Partially Paid'  # Partial payment
        PAID = 'paid', 'Paid'  # Fully paid
        REFUNDED = 'refunded', 'Refunded'  # Refunded

    order_code = models.CharField(max_length=50, unique=True, editable=False)  # Auto-generated
    listing = models.ForeignKey(Listing, on_delete=models.SET_NULL, null=True, related_name='orders')
    batch = models.ForeignKey(Batch, on_delete=models.SET_NULL, null=True, related_name='orders')
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='purchases',  # Trader's purchase history
        limit_choices_to={'role': 'trader'}  # Only traders can buy
    )
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sales',  # Farmer's sales history
        limit_choices_to={'role': 'farmer'}  # Only farmers can sell
    )
    bid = models.ForeignKey(Bid, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    quantity_kg = models.DecimalField(max_digits=10, decimal_places=2)  # Quantity purchased
    price_per_kg = models.DecimalField(max_digits=10, decimal_places=2)  # Agreed price
    # total_amount is computed: quantity_kg * price_per_kg (auto-calculated by database)
    total_amount = GeneratedField(
        expression=ExpressionWrapper(
            F('quantity_kg') * F('price_per_kg'),
            output_field=DecimalField(max_digits=12, decimal_places=2)
        ),
        output_field=DecimalField(max_digits=12, decimal_places=2),
        db_persist=True  # Store in database for queries
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    payment_status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.UNPAID)
    created_at = models.DateTimeField(auto_now_add=True)  # When order was placed
    updated_at = models.DateTimeField(auto_now=True)  # Last status update

    class Meta:
        ordering = ['-created_at']  # Newest orders first

    def __str__(self):
        """Return order code with status for display."""
        return f"{self.order_code} - {self.status}"

    def save(self, *args, **kwargs):
        """
        Override save to auto-generate order_code if not set.
        This ensures every order gets a unique code like ORD-2026-0001.
        """
        if not self.order_code:
            self.order_code = self._generate_order_code()
        super().save(*args, **kwargs)

    def _generate_order_code(self):
        """
        Generate a unique order code in format: ORD-YYYY-NNNN

        The code includes the current year and a 4-digit sequential number.
        Example: ORD-2026-0001, ORD-2026-0002, etc.

        Returns:
            str: Generated order code
        """
        year = timezone.now().year
        # Find the last order code for this year
        last = Order.objects.filter(order_code__startswith=f'ORD-{year}-').order_by('order_code').last()
        if last:
            # Increment the last number by 1
            num = int(last.order_code.split('-')[2]) + 1
        else:
            # First order of the year
            num = 1
        return f'ORD-{year}-{num:04d}'


class OrderTracking(models.Model):
    """
    Status tracking entries for an order.

    Each time an order status changes, a new tracking entry is created
    to maintain a history of all status updates with timestamps.

    This provides an audit trail showing:
    - When the status changed
    - Who made the change
    - Any notes about the change
    - Location information (for shipments)

    Relationships:
    - order (FK -> Order): The order being tracked
    - updated_by (FK -> User): Who made the status update
    """

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        CONFIRMED = 'confirmed', 'Confirmed'
        PROCESSING = 'processing', 'Processing'
        SHIPPED = 'shipped', 'Shipped'
        DELIVERED = 'delivered', 'Delivered'
        CANCELLED = 'cancelled', 'Cancelled'

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='tracking_entries')
    status = models.CharField(max_length=20, choices=Status.choices)  # New status
    location = models.CharField(max_length=200, blank=True, default='')  # Shipment location
    notes = models.TextField(blank=True, default='')  # Additional notes
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='tracking_updates'  # User's tracking update history
    )
    tracked_at = models.DateTimeField(auto_now_add=True)  # When status was updated

    class Meta:
        verbose_name_plural = 'order tracking'  # Fix plural in Django admin
        ordering = ['-tracked_at']  # Most recent updates first

    def __str__(self):
        """Return order code with new status for display."""
        return f"Order {self.order.order_code} -> {self.status}"


class Payment(models.Model):
    """
    Payment record for an order.

    Tracks payments made by traders to farmers. An order can have multiple
    payments (partial payments) until fully paid.

    Payment Methods:
    - BANK_TRANSFER: Direct bank transfer
    - MOBILE_MONEY: Mobile money payment (M-Pesa, etc.)
    - CASH: Cash payment
    - ESCROW: Escrow service (holding payment until delivery)

    Payment Status Flow:
    - PENDING: Payment initiated, awaiting confirmation
    - COMPLETED: Payment successfully received
    - FAILED: Payment failed or declined
    - REFUNDED: Payment was refunded

    Relationships:
    - order (FK -> Order): The order being paid for
    - payer (FK -> User): The trader making the payment
    """

    class PaymentMethod(models.TextChoices):
        BANK_TRANSFER = 'bank_transfer', 'Bank Transfer'
        MOBILE_MONEY = 'mobile_money', 'Mobile Money'
        CASH = 'cash', 'Cash'
        ESCROW = 'escrow', 'Escrow'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'  # Awaiting confirmation
        COMPLETED = 'completed', 'Completed'  # Payment successful
        FAILED = 'failed', 'Failed'  # Payment failed
        REFUNDED = 'refunded', 'Refunded'  # Refunded to payer

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    payer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)  # Payment amount
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices)  # How payment was made
    transaction_ref = models.CharField(max_length=100, unique=True, null=True, blank=True)  # External reference ID
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    paid_at = models.DateTimeField(null=True, blank=True)  # When payment was completed
    created_at = models.DateTimeField(auto_now_add=True)  # When payment record was created

    def __str__(self):
        """Return payment ID with amount and status for display."""
        return f"Payment {self.id}: Rs{self.amount} ({self.status})"


class Dispute(models.Model):
    """
    Dispute raised by a user about an order.

    Either the buyer (trader) or seller (farmer) can raise a dispute
    if there's an issue with the order (e.g., quality problems, non-delivery).

    Dispute Status Flow:
    - OPEN: Dispute just raised, awaiting review
    - UNDER_REVIEW: Admin/PM is investigating
    - RESOLVED: Resolution has been decided
    - CLOSED: Dispute is fully closed

    Only admins can resolve disputes. The resolution field contains
    the final decision.

    Relationships:
    - order (FK -> Order): The order being disputed
    - raised_by (FK -> User): Who raised the dispute
    - against_user (FK -> User): Who the dispute is against
    - resolved_by (FK -> User): Admin who resolved it
    """

    class Status(models.TextChoices):
        OPEN = 'open', 'Open'  # Just raised
        UNDER_REVIEW = 'under_review', 'Under Review'  # Being investigated
        RESOLVED = 'resolved', 'Resolved'  # Decision made
        CLOSED = 'closed', 'Closed'  # Fully closed

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='disputes')
    raised_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='disputes_raised')
    against_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='disputes_against')
    reason = models.TextField()  # Why the dispute was raised
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    resolution = models.TextField(blank=True, default='')  # Admin's decision
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='disputes_resolved'  # Admin's resolved disputes
    )
    created_at = models.DateTimeField(auto_now_add=True)  # When dispute was raised
    resolved_at = models.DateTimeField(null=True, blank=True)  # When dispute was resolved

    class Meta:
        ordering = ['-created_at']  # Newest disputes first

    def __str__(self):
        """Return dispute ID with order code and status for display."""
        return f"Dispute {self.id} - Order {self.order.order_code} ({self.status})"


class Notification(models.Model):
    """
    In-app notification for users.

    Created automatically when important events occur (new bid, order placed,
    payment received, etc.). Users can view notifications to stay informed
    about platform activity.

    Notification Types:
    - BID_RECEIVED: Farmer received a new bid on their listing
    - BID_ACCEPTED: Trader's bid was accepted by farmer
    - ORDER_PLACED: Farmer received a new order
    - ORDER_SHIPPED: Trader notified that order was shipped
    - PAYMENT_RECEIVED: Farmer received payment
    - BATCH_VERIFIED: Farmer notified their batch was verified
    - DISPUTE_RAISED: User notified a dispute was raised against them

    The reference_id and reference_type fields allow linking notifications
    to specific objects (e.g., bid_id, order_id) for navigation.

    Relationships:
    - user (FK -> User): Who receives this notification
    """

    class Type(models.TextChoices):
        BID_RECEIVED = 'bid_received', 'Bid Received'  # New bid on listing
        BID_ACCEPTED = 'bid_accepted', 'Bid Accepted'  # Bid accepted
        ORDER_PLACED = 'order_placed', 'Order Placed'  # New order received
        ORDER_SHIPPED = 'order_shipped', 'Order Shipped'  # Order shipped
        PAYMENT_RECEIVED = 'payment_received', 'Payment Received'  # Payment received
        BATCH_VERIFIED = 'batch_verified', 'Batch Verified'  # Batch quality verified
        DISPUTE_RAISED = 'dispute_raised', 'Dispute Raised'  # Dispute raised

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=30, choices=Type.choices)  # Notification type
    message = models.TextField()  # Notification content
    reference_id = models.IntegerField(null=True, blank=True)  # ID of related object
    reference_type = models.CharField(max_length=50, blank=True, default='')  # Type of related object
    is_read = models.BooleanField(default=False)  # Whether user has seen it
    created_at = models.DateTimeField(auto_now_add=True)  # When notification was created

    class Meta:
        ordering = ['-created_at']  # Newest notifications first

    def __str__(self):
        """Return notification type with message preview."""
        return f"[{self.type}] {self.message[:50]}"


class Conversation(models.Model):
    """
    Messaging conversation between users.

    Used for communication about batches, orders, quality reviews,
    or general inquiries. Multiple users can participate in a conversation.

    Conversation Types:
    - QUALITY_REVIEW: Discussion about batch quality
    - BATCH_INQUIRY: Questions about a specific batch
    - ORDER_SUPPORT: Support for an order issue
    - GENERAL: General discussion

    Conversation Status:
    - OPEN: Active conversation
    - ARCHIVED: Conversation archived (read-only)
    - LOCKED: Conversation locked (no new messages)

    Relationships:
    - batch (FK -> Batch): Related batch (optional)
    - order (FK -> Order): Related order (optional)
    - participants (reverse FK from ConversationParticipant): Users in conversation
    - messages (reverse FK from Message): Messages in conversation
    """

    class Type(models.TextChoices):
        QUALITY_REVIEW = 'quality_review', 'Quality Review'  # Quality discussion
        BATCH_INQUIRY = 'batch_inquiry', 'Batch Inquiry'  # Batch questions
        ORDER_SUPPORT = 'order_support', 'Order Support'  # Order help
        GENERAL = 'general', 'General'  # General chat

    class Status(models.TextChoices):
        OPEN = 'open', 'Open'  # Active
        ARCHIVED = 'archived', 'Archived'  # Archived
        LOCKED = 'locked', 'Locked'  # Locked

    batch = models.ForeignKey(Batch, on_delete=models.SET_NULL, null=True, blank=True, related_name='conversations')
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='conversations')
    type = models.CharField(max_length=20, choices=Type.choices)  # Conversation type
    subject = models.CharField(max_length=200, blank=True, default='')  # Conversation subject
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)  # When conversation started
    last_message_at = models.DateTimeField(null=True, blank=True)  # Last message timestamp

    class Meta:
        ordering = ['-last_message_at']  # Most recent conversations first

    def __str__(self):
        """Return conversation ID with type for display."""
        return f"Conversation {self.id} ({self.type})"


class ConversationParticipant(models.Model):
    """
    Links users to conversations they participate in.

    Each conversation can have multiple participants. This model tracks:
    - Which users are in the conversation
    - Their role in the chat (farmer, trader, PM, admin)
    - When they joined and last read messages
    - Whether they've muted the conversation

    The unique_together constraint ensures a user can only be in a
    conversation once.

    Relationships:
    - conversation (FK -> Conversation): The conversation
    - user (FK -> User): The participant
    """

    class RoleInChat(models.TextChoices):
        FARMER = 'farmer', 'Farmer'
        PRODUCT_MANAGER = 'product_manager', 'Product Manager'
        TRADER = 'trader', 'Trader'
        ADMIN = 'admin', 'Admin'

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='conversation_participations')
    role_in_chat = models.CharField(max_length=20, choices=RoleInChat.choices)  # User's role in this chat
    joined_at = models.DateTimeField(auto_now_add=True)  # When they joined
    last_read_at = models.DateTimeField(null=True, blank=True)  # For unread message count
    is_muted = models.BooleanField(default=False)  # Muted notifications
    is_active = models.BooleanField(default=True)  # Whether still participating

    class Meta:
        unique_together = ('conversation', 'user')  # One user per conversation

    def __str__(self):
        """Return username with conversation ID for display."""
        return f"{self.user.username} in Conversation {self.conversation.id}"


class Message(models.Model):
    """
    Individual message within a conversation.

    Supports text, images, documents, and system messages. Messages can be
    edited or soft-deleted (marked as deleted but preserved for audit).

    Message Types:
    - TEXT: Regular text message
    - IMAGE: Image attachment
    - DOCUMENT: Document attachment
    - SYSTEM: System-generated message (e.g., "User joined")

    Soft Delete Pattern:
    Messages are soft-deleted (is_deleted=True) rather than hard-deleted
    to preserve conversation history and audit trail.

    Relationships:
    - conversation (FK -> Conversation): The conversation this message belongs to
    - sender (FK -> User): Who sent the message (null if system message)
    """

    class MessageType(models.TextChoices):
        TEXT = 'text', 'Text'  # Regular text
        IMAGE = 'image', 'Image'  # Image attachment
        DOCUMENT = 'document', 'Document'  # Document attachment
        SYSTEM = 'system', 'System'  # System message

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='sent_messages')
    message_type = models.CharField(max_length=10, choices=MessageType.choices, default=MessageType.TEXT)
    content = models.TextField(blank=True, default='')  # Message text content
    attachments = models.JSONField(null=True, blank=True, default=list)  # File attachments (JSON array)
    is_edited = models.BooleanField(default=False)  # Whether message was edited
    edited_at = models.DateTimeField(null=True, blank=True)  # When message was edited
    is_deleted = models.BooleanField(default=False)  # Soft delete flag
    deleted_at = models.DateTimeField(null=True, blank=True)  # When soft-deleted
    sent_at = models.DateTimeField(auto_now_add=True)  # When message was sent

    class Meta:
        ordering = ['sent_at']  # Messages in chronological order

    def __str__(self):
        """Return message ID with conversation ID for display."""
        return f"Message {self.id} in Conversation {self.conversation.id}"


class Report(models.Model):
    """
    Generated platform report for analytics and insights.

    Reports are generated by admins or PMs to analyze platform activity.
    The report is stored as a file (CSV/PDF) with metadata about parameters.

    Report Types:
    - TRADE_SUMMARY: Overview of all trades
    - GRADE_DISTRIBUTION: Distribution of quality grades
    - FARMER_PERFORMANCE: Farmer activity metrics
    - TRADER_ACTIVITY: Trader activity metrics
    - REVENUE: Revenue analysis

    Relationships:
    - generated_by (FK -> User): Who generated the report
    """

    class ReportType(models.TextChoices):
        TRADE_SUMMARY = 'trade_summary', 'Trade Summary'  # Trade overview
        GRADE_DISTRIBUTION = 'grade_distribution', 'Grade Distribution'  # Grade analysis
        FARMER_PERFORMANCE = 'farmer_performance', 'Farmer Performance'  # Farmer metrics
        TRADER_ACTIVITY = 'trader_activity', 'Trader Activity'  # Trader metrics
        REVENUE = 'revenue', 'Revenue'  # Revenue analysis

    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='generated_reports'
    )
    report_type = models.CharField(max_length=30, choices=ReportType.choices)  # Type of report
    date_from = models.DateField(null=True, blank=True)  # Report date range start
    date_to = models.DateField(null=True, blank=True)  # Report date range end
    parameters = models.JSONField(null=True, blank=True, default=dict)  # Report parameters
    file_path = models.CharField(max_length=255, blank=True, default='')  # Path to generated file
    created_at = models.DateTimeField(auto_now_add=True)  # When report was generated

    class Meta:
        ordering = ['-created_at']  # Newest reports first

    def __str__(self):
        """Return report type with date for display."""
        return f"{self.get_report_type_display()} - {self.created_at.date()}"


class AuditLog(models.Model):
    """
    System audit trail for tracking all database changes.

    Records every create, update, and delete operation across the platform.
    Used for compliance, debugging, and security monitoring.

    The audit log captures:
    - Who made the change (user)
    - What action was performed (action)
    - Which table and record was affected
    - Old and new values (for updates)
    - IP address of the requester

    Example actions: 'batch.created', 'order.updated', 'user.login'

    Indexes:
    - (table_name, record_id): Fast lookup for record history
    - (action): Fast filtering by action type
    - (user): Fast lookup for user activity

    Relationships:
    - user (FK -> User): Who performed the action (null for system actions)
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'  # User's audit history
    )
    action = models.CharField(max_length=100)  # e.g., 'batch.verified', 'order.created'
    table_name = models.CharField(max_length=50)  # Database table affected
    record_id = models.IntegerField()  # ID of the affected record
    old_value = models.JSONField(null=True, blank=True)  # Previous state (for updates)
    new_value = models.JSONField(null=True, blank=True)  # New state (for creates/updates)
    ip_address = models.CharField(max_length=45, blank=True, default='')  # Requester's IP
    logged_at = models.DateTimeField(auto_now_add=True)  # When the action occurred

    class Meta:
        verbose_name_plural = 'audit logs'  # Fix plural in Django admin
        ordering = ['-logged_at']  # Newest entries first
        indexes = [
            models.Index(fields=['table_name', 'record_id']),  # Record history lookup
            models.Index(fields=['action']),  # Action type filtering
            models.Index(fields=['user']),  # User activity lookup
        ]

    def __str__(self):
        """Return timestamp with action and record for display."""
        return f"[{self.logged_at}] {self.action} on {self.table_name}#{self.record_id}"
