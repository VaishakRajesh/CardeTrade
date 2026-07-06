# AGENTS.md — AI Agent Instruction Manual for CardeTrade

> **Purpose**: This file provides every rule, pattern, convention, and implementation detail an AI coding agent needs to work on the CardeTrade project correctly and autonomously. Follow these instructions precisely.

---

## 📌 Table of Contents

1. [Project Identity](#-project-identity)
2. [Repository Map](#-repository-map)
3. [Critical Rules — Read First](#-critical-rules--read-first)
4. [Role System — Exact Implementation](#-role-system--exact-implementation)
5. [Complete Django Models (All 16 Tables)](#-complete-django-models)
6. [URL Structure — Every App](#-url-structure)
7. [View Patterns](#-view-patterns)
8. [Form Patterns](#-form-patterns)
9. [Template Patterns](#-template-patterns)
10. [Signal Implementations](#-signal-implementations)
11. [Admin Configuration](#-admin-configuration)
12. [Testing Patterns — Every App](#-testing-patterns)
13. [Code Generation Rules](#-code-generation-rules)
14. [File & Naming Conventions](#-file--naming-conventions)
15. [Import Conventions](#-import-conventions)
16. [Common Pitfalls — Must Avoid](#-common-pitfalls--must-avoid)
17. [Settings & Config Reference](#-settings--config-reference)
18. [Environment Variables](#-environment-variables)
19. [Quick Reference Cheat Sheets](#-quick-reference-cheat-sheets)

---

## 🆔 Project Identity

| Property | Value |
|----------|-------|
| **Name** | CardeTrade — Cardamom Trading Platform |
| **Type** | Django 5.x web application (Python 3.11+) |
| **Database** | SQLite (dev) / PostgreSQL (prod) |
| **Frontend** | HTML + CSS + JS + **Bootstrap 5** (server-rendered templates) |
| **Auth** | Custom `AbstractUser` with role field |
| **Styling** | Bootstrap 5 only (no MUI, no React, no Tailwind) |
| **Audit** | Every mutation logged |
| **Tests** | Django `TestCase` with `setUpTestData` |

---

## 🗂 Repository Map

```
CardeTrade/                              # Root
├── README.md
├── AGENTS.md
├── requirements.txt
├── .env
├── .gitignore
│
cardetrade/
├── __init__.py
├── settings.py              # Django config, AUTH_USER_MODEL = 'app.User'
├── urls.py                  # Root URL routing
├── wsgi.py                  # WSGI deployment entry

app/                         # Core single app
├── __init__.py
├── models.py                # All 16 tables (User, Farm, Batch, Listing, Order...)
├── views.py                 # All platform views
├── urls.py                  # / routes
├── forms.py                 # All forms
├── decorators.py            # @role_required, etc.
├── admin.py                 # Admin configurations
├── tests.py                 # Test cases
├── signals.py               # Post-save signals
├── middleware.py            # Audit middleware
├── utils.py                 # Helpers
├── templates/app/           # App-specific HTML files
└── migrations/

templates/                   # Shared templates
├── base.html                # Bootstrap 5 nav + footer + alerts
├── includes/                # Partials (navbar, sidebar, pagination)
└── admin/                   # Django admin overrides

static/                      # Static assets
├── css/
│   └── style.css
└── js/
    └── main.js

media/                       # User-uploaded files
├── batch_images/
└── documents/
```

---

## ⚠️ Critical Rules — Read First

These override all other considerations:

| # | Rule | Rationale |
|---|------|-----------|
| **R1** | Never use `IntegerChoices`. Always use `models.TextChoices` for ENUM-like fields | Database stores strings, not integers |
| **R2** | Always set `related_name` on every `ForeignKey` | Django creates backwards relations automatically |
| **R3** | `total_amount` on Order must be `GeneratedField` (Django 5+) or `@property` | Never store as a regular DB column |
| **R4** | `AUTH_USER_MODEL = 'app.User'` must be set in `settings.py` **before** first migration | Otherwise Django creates its own `auth_user` table |
| **R5** | Soft delete for `messages` only. All other tables use hard delete or status | Messages are sensitive; hard delete causes data loss |
| **R6** | Every state mutation must be logged in `audit_logs` | Legal/compliance requirement |
| **R7** | `is_staff=True` for Product Manager but `is_superuser=False` | PM gets admin panel access but not full control |
| **R8** | Always reference ENUM constants via model class, never as raw strings | e.g., `Batch.Status.PENDING` not `'pending'` |
| **R9** | `conversation_participants` uses `unique_together`, not composite PK | Django doesn't support composite PKs |
| **R10** | Farmers cannot bid. Traders cannot create batches. PMs cannot trade. | Enforce via `@role_required` decorator |

---

## 👤 Role System — Exact Implementation

### User Model

```python
# app/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class Role(models.TextChoices):
        FARMER = 'farmer', 'Farmer'
        TRADER = 'trader', 'Trader'
        PRODUCT_MANAGER = 'product_manager', 'Product Manager'
        ADMIN = 'admin', 'Admin'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.FARMER
    )
    phone = models.CharField(max_length=20, blank=True, default='')
    address = models.TextField(blank=True, default='')
    region = models.CharField(max_length=100, blank=True, default='')

    # Inherited from AbstractUser:
    # username, email, password, first_name, last_name
    # is_active, is_staff, is_superuser
    # date_joined, last_login
```

### Role Enforcement Decorator

```python
# app/decorators.py
from functools import wraps
from django.shortcuts import redirect
from django.http import HttpResponseForbidden

def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            if request.user.role not in roles:
                return HttpResponseForbidden()
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator

# Convenience variants
def farmer_required(view_func):
    return role_required('farmer')(view_func)

def trader_required(view_func):
    return role_required('trader')(view_func)

def pm_required(view_func):
    return role_required('product_manager')(view_func)

def admin_required(view_func):
    return role_required('admin')(view_func)

def staff_required(view_func):
    """For PM or Admin (any is_staff)"""
    return role_required('product_manager', 'admin')(view_func)

def trade_participant_required(view_func):
    """Farmer (seller) or Trader (buyer)"""
    return role_required('farmer', 'trader')(view_func)
```

### Role → is_staff / is_superuser Mapping

| Role | In `User.role` | `is_staff` | `is_superuser` |
|------|----------------|------------|----------------|
| Farmer | `'farmer'` | `False` | `False` |
| Trader | `'trader'` | `False` | `False` |
| Product Manager | `'product_manager'` | `True` | `False` |
| Admin | `'admin'` | `True` | `True` |

✅ **Set in `User.save()` or in the registration view.**

```python
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
```

---

## 📦 Complete Django Models (All 16 Tables)

### app/models.py

```python
from django.contrib.auth.models import AbstractUser
from django.db import models

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
```

### app/models.py

```python
from django.db import models
from django.conf import settings

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
    total_area_acres = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )
    certification = models.CharField(max_length=100, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'farms'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.farm_name} ({self.farmer.username})"
```

### app/models.py

```python
from django.db import models
from django.conf import settings
from django.utils import timezone

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
    farm = models.ForeignKey(
        'Farm',
        on_delete=models.SET_NULL,
        null=True,
        related_name='batches'
    )
    quantity_kg = models.DecimalField(max_digits=10, decimal_places=2)
    harvest_date = models.DateField()
    description = models.TextField(blank=True, default='')
    estimated_price_per_kg = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
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
        last = Batch.objects.filter(
            batch_code__startswith=f'CDM-{year}-'
        ).order_by('batch_code').last()
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

    batch = models.OneToOneField(
        Batch,
        on_delete=models.CASCADE,
        related_name='verification'
    )
    product_manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='verifications'
    )
    grade = models.CharField(max_length=1, choices=Grade.choices)
    moisture_content_pct = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    aroma_score = models.PositiveSmallIntegerField(null=True, blank=True)  # 1-10
    color_score = models.PositiveSmallIntegerField(null=True, blank=True)  # 1-10
    purity_pct = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    verified_price_per_kg = models.DecimalField(max_digits=10, decimal_places=2)
    remarks = models.TextField(blank=True, default='')
    verified_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'quality verifications'

    def __str__(self):
        return f"Batch {self.batch.batch_code} → Grade {self.grade}"
```

### app/models.py

```python
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator

class Listing(models.Model):
    class ListingType(models.TextChoices):
        FIXED_PRICE = 'fixed_price', 'Fixed Price'
        AUCTION = 'auction', 'Auction'

    batch = models.OneToOneField(
        'Batch',
        on_delete=models.CASCADE,
        related_name='listing'
    )
    farmer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='listings'
    )
    listing_type = models.CharField(
        max_length=20,
        choices=ListingType.choices
    )
    price_per_kg = models.DecimalField(max_digits=10, decimal_places=2)
    min_order_kg = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
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

    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name='bids'
    )
    trader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bids',
        limit_choices_to={'role': 'trader'}
    )
    bid_price_per_kg = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_kg = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ACTIVE
    )
    notes = models.TextField(blank=True, default='')
    bid_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-bid_price_per_kg']

    def __str__(self):
        return f"Bid {self.id}: ₹{self.bid_price_per_kg}/kg by {self.trader.username}"
```

### app/models.py

```python
from django.db import models
from django.conf import settings
from django.db.models import F, ExpressionWrapper, DecimalField, GeneratedField
from django.utils import timezone

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
    listing = models.ForeignKey(
        'Listing',
        on_delete=models.SET_NULL,
        null=True,
        related_name='orders'
    )
    batch = models.ForeignKey(
        'Batch',
        on_delete=models.SET_NULL,
        null=True,
        related_name='orders'
    )
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
    bid = models.ForeignKey(
        'Bid',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )
    quantity_kg = models.DecimalField(max_digits=10, decimal_places=2)
    price_per_kg = models.DecimalField(max_digits=10, decimal_places=2)

    # Django 5+ GeneratedField (computed column)
    total_amount = GeneratedField(
        expression=ExpressionWrapper(
            F('quantity_kg') * F('price_per_kg'),
            output_field=DecimalField(max_digits=12, decimal_places=2)
        ),
        output_field=DecimalField(max_digits=12, decimal_places=2),
        db_persist=True
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.UNPAID
    )
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
        last = Order.objects.filter(
            order_code__startswith=f'ORD-{year}-'
        ).order_by('order_code').last()
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

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='tracking_entries'
    )
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
        return f"Order {self.order.order_code} → {self.status}"


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

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    payer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='payments'
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices)
    transaction_ref = models.CharField(max_length=100, unique=True, null=True, blank=True)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING
    )
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment {self.id}: ₹{self.amount} ({self.status})"
```

### app/models.py

```python
from django.db import models
from django.conf import settings

class Dispute(models.Model):
    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        UNDER_REVIEW = 'under_review', 'Under Review'
        RESOLVED = 'resolved', 'Resolved'
        CLOSED = 'closed', 'Closed'

    order = models.ForeignKey(
        'Order',
        on_delete=models.CASCADE,
        related_name='disputes'
    )
    raised_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='disputes_raised'
    )
    against_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='disputes_against'
    )
    reason = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN
    )
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
```

### app/models.py

```python
from django.db import models
from django.conf import settings

class Notification(models.Model):
    class Type(models.TextChoices):
        BID_RECEIVED = 'bid_received', 'Bid Received'
        BID_ACCEPTED = 'bid_accepted', 'Bid Accepted'
        ORDER_PLACED = 'order_placed', 'Order Placed'
        ORDER_SHIPPED = 'order_shipped', 'Order Shipped'
        PAYMENT_RECEIVED = 'payment_received', 'Payment Received'
        BATCH_VERIFIED = 'batch_verified', 'Batch Verified'
        DISPUTE_RAISED = 'dispute_raised', 'Dispute Raised'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
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
```

### app/models.py

```python
from django.db import models
from django.conf import settings

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

    batch = models.ForeignKey(
        'Batch',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conversations'
    )
    order = models.ForeignKey(
        'Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conversations'
    )
    type = models.CharField(max_length=20, choices=Type.choices)
    subject = models.CharField(max_length=200, blank=True, default='')
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.OPEN
    )
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

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='participants'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='conversation_participations'
    )
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

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='sent_messages'
    )
    message_type = models.CharField(
        max_length=10,
        choices=MessageType.choices,
        default=MessageType.TEXT
    )
    content = models.TextField(blank=True, default='')
    attachments = models.JSONField(null=True, blank=True, default=list)
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    # Soft delete — only table with this pattern
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sent_at']

    def __str__(self):
        return f"Message {self.id} in Conversation {self.conversation.id}"
```

### app/models.py

```python
from django.db import models
from django.conf import settings

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
```

### app/models.py

```python
from django.db import models
from django.conf import settings

class AuditLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    action = models.CharField(max_length=100)  # e.g., 'batch.verified'
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
```

---

## 🌐 URL Structure

### Root `cardetrade/urls.py`

```python
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('app/', include('app.urls')),
    path('app/', include('app.urls')),
    path('app/', include('app.urls')),
    path('app/', include('app.urls')),
    path('app/', include('app.urls')),
    path('app/', include('app.urls')),
    path('app/', include('app.urls')),
    path('app/', include('app.urls')),
    path('app/', include('app.urls')),
    path('app/', include('app.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

### Each App's URL Patterns

```python
# app/urls.py
from django.urls import path
from . import views

app_name = 'accounts'
urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
]

# app/urls.py
app_name = 'batches'
urlpatterns = [
    path('', views.BatchListView.as_view(), name='list'),
    path('create/', views.BatchCreateView.as_view(), name='create'),
    path('<int:pk>/', views.BatchDetailView.as_view(), name='detail'),
    path('<int:pk>/verify/', views.BatchVerifyView.as_view(), name='verify'),
]

# app/urls.py
app_name = 'trading'
urlpatterns = [
    path('', views.ListingListView.as_view(), name='listings'),
    path('<int:pk>/', views.ListingDetailView.as_view(), name='detail'),
    path('<int:pk>/bid/', views.PlaceBidView.as_view(), name='place_bid'),
    path('<int:pk>/buy/', views.DirectBuyView.as_view(), name='direct_buy'),
    path('bids/', views.MyBidsView.as_view(), name='my_bids'),
]
```

---

## 👁 View Patterns

### Class-Based Views (CBV) — Preferred

```python
# app/views.py
from django.views.generic import CreateView, DetailView, ListView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from ..accounts.decorators import role_required
from django.utils.decorators import method_decorator
from .models import Batch
from .forms import BatchForm

@method_decorator(role_required('farmer'), name='dispatch')
class BatchCreateView(LoginRequiredMixin, CreateView):
    model = Batch
    form_class = BatchForm
    template_name = 'app/batch_create.html'
    success_url = reverse_lazy('app:list')

    def form_valid(self, form):
        form.instance.farmer = self.request.user
        return super().form_valid(form)


@method_decorator(role_required('farmer', 'product_manager', 'admin'), name='dispatch')
class BatchDetailView(LoginRequiredMixin, DetailView):
    model = Batch
    template_name = 'app/batch_detail.html'
    context_object_name = 'batch'


@method_decorator(role_required('product_manager'), name='dispatch')
class BatchVerifyView(LoginRequiredMixin, UpdateView):
    model = Batch
    fields = []  # No direct edit; handled via verification form
    template_name = 'app/batch_verify.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['verification_form'] = VerificationForm()
        return context

    def post(self, request, *args, **kwargs):
        batch = self.get_object()
        form = VerificationForm(request.POST)
        if form.is_valid():
            verification = form.save(commit=False)
            verification.batch = batch
            verification.product_manager = request.user
            verification.save()
            batch.status = Batch.Status.VERIFIED
            batch.save()
            return redirect('app:detail', pk=batch.pk)
        return self.form_invalid(form)
```

### Function-Based Views (FBV) — For Simple Pages

```python
# app/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from .forms import RegistrationForm

def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = RegistrationForm()
    return render(request, 'app/register.html', {'form': form})
```

### `@role_required` on Function Views

```python
from .decorators import role_required

@role_required('farmer')
def create_batch(request):
    ...
```

---

## 📝 Form Patterns

```python
# app/forms.py
from django import forms
from .models import Batch, QualityVerification

class BatchForm(forms.ModelForm):
    class Meta:
        model = Batch
        fields = ['farm', 'quantity_kg', 'harvest_date',
                  'description', 'estimated_price_per_kg']
        widgets = {
            'harvest_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_quantity_kg(self):
        qty = self.cleaned_data['quantity_kg']
        if qty <= 0:
            raise forms.ValidationError("Quantity must be greater than 0")
        return qty

    def clean_estimated_price_per_kg(self):
        price = self.cleaned_data['estimated_price_per_kg']
        if price <= 0:
            raise forms.ValidationError("Price must be greater than 0")
        return price


class VerificationForm(forms.ModelForm):
    class Meta:
        model = QualityVerification
        fields = ['grade', 'moisture_content_pct', 'aroma_score',
                  'color_score', 'purity_pct', 'verified_price_per_kg', 'remarks']
        widgets = {
            'remarks': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_aroma_score(self):
        score = self.cleaned_data['aroma_score']
        if score is not None and (score < 1 or score > 10):
            raise forms.ValidationError("Score must be between 1 and 10")
        return score

    def clean_verified_price_per_kg(self):
        price = self.cleaned_data['verified_price_per_kg']
        if price <= 0:
            raise forms.ValidationError("Price must be greater than 0")
        return price
```

---

## 🎨 Template Patterns

### `base.html` Structure

```html
<!DOCTYPE html>
{% load static %}
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}CardeTrade{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="{% static 'css/style.css' %}">
</head>
<body>
    {% include 'includes/navbar.html' %}
    {% include 'includes/alerts.html' %}
    <main class="container mt-4">
        {% block content %}{% endblock %}
    </main>
    {% include 'includes/footer.html' %}
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="{% static 'js/main.js' %}"></script>
</body>
</html>
```

### App Template Example

```django
{# app/batch_create.html #}
{% extends 'base.html' %}
{% load crispy_forms_tags %}

{% block title %}Create Batch - CardeTrade{% endblock %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-md-8">
        <div class="card shadow">
            <div class="card-header bg-success text-white">
                <h4 class="mb-0">Create New Batch</h4>
            </div>
            <div class="card-body">
                <form method="post" novalidate>
                    {% csrf_token %}
                    {{ form|crispy }}
                    <div class="d-grid gap-2 mt-3">
                        <button type="submit" class="btn btn-success">
                            Submit Batch
                        </button>
                    </div>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

### Alert/Message Pattern

```django
{# includes/alerts.html #}
{% if messages %}
<div class="container mt-2">
    {% for message in messages %}
    <div class="alert alert-{{ message.tags }} alert-dismissible fade show" role="alert">
        {{ message }}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    </div>
    {% endfor %}
</div>
{% endif %}
```

---

## ⚡ Signal Implementations

### 1. Batch Verified → Create Listing

```python
# app/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Batch
from app.models import Listing

@receiver(post_save, sender=Batch)
def create_listing_on_verification(sender, instance, created, **kwargs):
    """When a batch status changes to 'verified', auto-create a Listing."""
    if instance.status == Batch.Status.VERIFIED:
        try:
            verification = instance.verification
        except Batch.verification.RelatedObjectDoesNotExist:
            return

        Listing.objects.get_or_create(
            batch=instance,
            defaults={
                'farmer': instance.farmer,
                'listing_type': Listing.ListingType.FIXED_PRICE,
                'price_per_kg': verification.verified_price_per_kg,
                'available_qty_kg': instance.quantity_kg,
            }
        )
        instance.status = Batch.Status.LISTED
        instance.save(update_fields=['status'])
```

### 2. Order Created → Notify Seller

```python
# app/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order
from app.models import Notification

@receiver(post_save, sender=Order)
def notify_seller_on_order(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            user=instance.seller,
            type=Notification.Type.ORDER_PLACED,
            message=f"New order {instance.order_code} for {instance.quantity_kg}kg",
            reference_id=instance.id,
            reference_type='order'
        )
```

### 3. Bid Placed → Notify Farmer

```python
# app/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Bid
from app.models import Notification

@receiver(post_save, sender=Bid)
def notify_farmer_on_bid(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            user=instance.listing.farmer,
            type=Notification.Type.BID_RECEIVED,
            message=f"New bid ₹{instance.bid_price_per_kg}/kg on {instance.listing.batch.batch_code}",
            reference_id=instance.id,
            reference_type='bid'
        )
```

### 4. Universal Audit Logger

```python
# app/signals.py
import json
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.forms.models import model_to_dict
from .models import AuditLog
from .middleware import get_current_user, get_current_ip

# This is a simplified pattern. For complete coverage,
# consider django-simple-history or django-auditlog.
# For custom lightweight implementation:

EXCLUDED_MODELS = {'AuditLog', 'Notification', 'Session', 'LogEntry'}

@receiver(pre_save, sender=None)  # Connect dynamically in apps.py
def audit_pre_save(sender, **kwargs):
    """Capture old state before save."""
    pass  # Complex; see full implementation notes below
```

> **Full audit approach**: Use a middleware that stores the current user/IP per thread, then a `post_save` receiver connected to all models (except AuditLog itself) that serializes old/new values and writes to `audit_logs`.

```python
# app/middleware.py
import threading
from django.utils.deprecation import MiddlewareMixin

_thread_locals = threading.local()

def get_current_user():
    return getattr(_thread_locals, 'user', None)

def get_current_ip():
    return getattr(_thread_locals, 'ip', None)

class AuditMiddleware(MiddlewareMixin):
    def process_request(self, request):
        _thread_locals.user = getattr(request, 'user', None)
        _thread_locals.ip = request.META.get('REMOTE_ADDR', '')
```

### 5. Message Sent → Update Conversation

```python
# app/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Message

@receiver(post_save, sender=Message)
def update_conversation_timestamp(sender, instance, created, **kwargs):
    if created:
        conversation = instance.conversation
        conversation.last_message_at = instance.sent_at
        conversation.save(update_fields=['last_message_at'])
```

---

## ⚙ Admin Configuration

```python
# app/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'role', 'is_staff', 'is_active']
    list_filter = ['role', 'is_staff', 'is_active']
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('full_name', 'email', 'phone', 'region')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser',
                                     'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )

# app/admin.py
from django.contrib import admin
from .models import Batch, QualityVerification

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
```

---

## 🧪 Testing Patterns

### app/tests.py

```python
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()

class UserRegistrationTest(TestCase):
    def test_register_farmer(self):
        response = self.client.post(reverse('app:register'), {
            'username': 'farmer1',
            'email': 'farmer@test.com',
            'password1': 'testpass123',
            'password2': 'testpass123',
            'role': 'farmer',
        })
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username='farmer1')
        self.assertEqual(user.role, 'farmer')
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_register_pm_sets_staff(self):
        response = self.client.post(reverse('app:register'), {
            'username': 'pm1',
            'email': 'pm@test.com',
            'password1': 'testpass123',
            'password2': 'testpass123',
            'role': 'product_manager',
        })
        user = User.objects.get(username='pm1')
        self.assertTrue(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_role_enforcement_decorator(self):
        farmer = User.objects.create_user(
            username='farmer', password='test', role='farmer'
        )
        self.client.login(username='farmer', password='test')
        response = self.client.get(reverse('app:create'))
        self.assertEqual(response.status_code, 200)

        # Trader cannot access batch create
        trader = User.objects.create_user(
            username='trader', password='test', role='trader'
        )
        self.client.login(username='trader', password='test')
        response = self.client.get(reverse('app:create'))
        self.assertEqual(response.status_code, 403)
```

### app/tests.py

```python
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import Batch, QualityVerification
from app.models import Listing

User = get_user_model()

class BatchWorkflowTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.farmer = User.objects.create_user(
            username='farmer', password='test', role='farmer'
        )
        cls.pm = User.objects.create_user(
            username='pm', password='test', role='product_manager'
        )
        cls.batch = Batch.objects.create(
            farmer=cls.farmer,
            quantity_kg=100,
            harvest_date='2026-01-15',
            estimated_price_per_kg=45.00,
            status=Batch.Status.UNDER_REVIEW
        )

    def test_verify_batch_creates_listing(self):
        self.client.login(username='pm', password='test')
        response = self.client.post(
            reverse('app:verify', args=[self.batch.id]),
            {
                'grade': 'A',
                'verified_price_per_kg': 50.00,
                'moisture_content_pct': 10.5,
                'aroma_score': 8,
                'color_score': 9,
                'purity_pct': 98.5,
            }
        )
        self.batch.refresh_from_db()
        self.assertEqual(self.batch.status, Batch.Status.LISTED)
        self.assertTrue(Listing.objects.filter(batch=self.batch).exists())

    def test_batch_code_format(self):
        batch = Batch.objects.create(
            farmer=self.farmer,
            quantity_kg=50,
            harvest_date='2026-02-01',
            estimated_price_per_kg=40.00
        )
        import re
        self.assertTrue(re.match(r'^CDM-\d{4}-\d{4}$', batch.batch_code))
```

### app/tests.py

```python
from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Listing, Bid
from app.models import Batch

User = get_user_model()

class BiddingTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.farmer = User.objects.create_user(
            username='farmer', password='test', role='farmer'
        )
        cls.trader1 = User.objects.create_user(
            username='trader1', password='test', role='trader'
        )
        cls.trader2 = User.objects.create_user(
            username='trader2', password='test', role='trader'
        )
        batch = Batch.objects.create(
            farmer=cls.farmer, quantity_kg=100,
            harvest_date='2026-01-15', estimated_price_per_kg=45
        )
        cls.listing = Listing.objects.create(
            batch=batch, farmer=cls.farmer,
            listing_type='auction', price_per_kg=40,
            available_qty_kg=100
        )

    def test_highest_bid_wins_auction(self):
        Bid.objects.create(
            listing=self.listing, trader=self.trader1,
            bid_price_per_kg=42, quantity_kg=100
        )
        Bid.objects.create(
            listing=self.listing, trader=self.trader2,
            bid_price_per_kg=45, quantity_kg=100
        )
        highest = Bid.objects.filter(listing=self.listing).order_by('-bid_price_per_kg').first()
        self.assertEqual(highest.trader, self.trader2)
        self.assertEqual(float(highest.bid_price_per_kg), 45.0)
```

---

## 🤖 Code Generation Rules

When writing code for CardeTrade, follow these rules strictly:

### Models

```
- Use models.TextChoices for ALL enums (never IntegerChoices)
- Set related_name on EVERY ForeignKey
- Use ForeignKey instead of IntegerField for relations
- Set on_delete explicitly (CASCADE for ownership, SET_NULL for optional, PROTECT for financial)
- Use auto_now_add=True for created_at, auto_now=True for updated_at
- Always define __str__
- Always define Meta with ordering and verbose_name
```

### Views

```
- Prefer Class-Based Views over Function-Based Views
- Use @method_decorator(role_required(...), name='dispatch') on CBVs
- Use LoginRequiredMixin on every authenticated view
- Set form.instance.user = request.user in form_valid
- Use get_object_or_404 instead of try/except
- Use redirect on success, render on failure
```

### URLs

```
- Use app_name = 'app_name' in each app's urls.py
- Use path() not url()
- Use named URL patterns (name='...') for reverse()
- Include all app patterns in root urls.py
```

### Templates

```
- Extend base.html ({% extends 'base.html' %})
- Use Bootstrap 5 classes (container, row, col, card, btn, table, form-control)
- Use {% crispy form %} for forms (requires django-crispy-forms + crispy-bootstrap5)
- Use {% url 'app_name:view_name' %} for linking
- Use {% static '...' %} for static files
- Never use inline CSS (except for very specific one-off overrides)
```

### Forms

```
- Use ModelForm for model-backed forms
- Use clean_<field>() for field validation
- Use crispy_forms_tags for rendering
```

### Signals

```
- Keep signals in signals.py (not in models.py or views.py)
- Use @receiver decorator for clarity
- Connect signals in apps.py ready() method
```

### Tests

```
- Use cls.setUpTestData for data shared across tests
- Use self.setUp for per-test data
- Test: status codes, redirects, database state, content
- Always test unauthorized access returns 403
```

---

## 📁 File & Naming Conventions

| Resource | Convention | Example |
|----------|------------|---------|
| Django App | `plural_lowercase` | `batches`, `orders`, `farms` |
| Model | `PascalCase, singular` | `QualityVerification`, `OrderTracking` |
| Model field | `snake_case` | `verified_price_per_kg`, `quantity_kg` |
| View (CBV) | `PascalCase + View` | `BatchCreateView`, `ListingDetailView` |
| View (FBV) | `snake_case` | `register_view`, `verify_batch` |
| Form | `PascalCase + Form` | `BatchForm`, `VerificationForm` |
| Signal receiver | `snake_case, descriptive` | `create_listing_on_verification` |
| Template | `snake_case, descriptive` | `batch_create.html`, `order_tracking.html` |
| URL name | `snake_case` | `app:create`, `app:listings` |
| Migration | Auto-generated | Don't rename |

---

## 📥 Import Conventions

```python
# Standard library
from functools import wraps
import re
import json

# Django core
from django.db import models
from django.db.models import Q, F, ExpressionWrapper
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, ListView, DetailView, UpdateView
from django.contrib import messages

# Third-party
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Row, Column

# Local (within project)
from ..accounts.decorators import role_required
from .models import Batch, QualityVerification
from .forms import BatchForm, VerificationForm
from app.models import Listing
from app.models import Notification
```

### Import Order (strict)
1. Python standard library
2. Django core
3. Third-party packages (crispy, etc.)
4. Local project imports (relative)

---

## 🚫 Common Pitfalls — Must Avoid

| # | Pitfall | Correct Approach |
|---|---------|-----------------|
| 1 | `class Status(models.IntegerChoices)` | `class Status(models.TextChoices)` |
| 2 | `farmer = models.ForeignKey(User)` without `related_name` | `farmer = models.ForeignKey(User, related_name='batches')` |
| 3 | `total_amount = models.DecimalField(...)` | `GeneratedField(...)` or `@property` |
| 4 | `'pending'` hardcoded in view logic | `Batch.Status.PENDING.value` or `Batch.Status.PENDING` |
| 5 | `@login_required` only, no role check | `@role_required('farmer')` which includes login check |
| 6 | Creating listing manually in a view | Use `post_save` signal on Batch verification |
| 7 | `on_delete=models.PROTECT` for everything | Use CASCADE for ownership, SET_NULL for optional FKs |
| 8 | Storing files without validation | Check file type, size, use `FileExtensionValidator` |
| 9 | `unique_together` with `null=True` columns | `null` values violate uniqueness; use `null=False` or custom logic |
| 10 | Forgetting to register models in `admin.py` | Always register all models with `@admin.register` |

---

## ⚙ Settings & Config Reference

### `cardetrade/settings.py` (critical sections)

```python
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'dev-secret-key-change-in-prod')
DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '127.0.0.1,localhost').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party
    'crispy_forms',
    'crispy_bootstrap5',
    # Local apps (order matters: accounts first)
    'accounts',
    'farms',
    'batches',
    'trading',
    'orders',
    'disputes',
    'notifications',
    'messaging',
    'reports',
    'audit',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'app.middleware.AuditMiddleware',  # Custom: captures user/IP for audit
]

ROOT_URLCONF = 'cardetrade.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

AUTH_USER_MODEL = 'app.User'  # ← MUST be set before first migration

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

LOGIN_URL = '/app/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/app/login/'

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
```

---

## 🔐 Environment Variables

```ini
# .env (never commit this file)
DJANGO_SECRET_KEY=your-strong-secret-key-here
DJANGO_DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
DATABASE_URL=sqlite:///db.sqlite3
```

---

## 📋 Quick Reference Cheat Sheets

### `@role_required` Quick Reference

```python
# Which decorator for which view:
@role_required('farmer')                          # Create batch, register farm
@role_required('trader')                          # Place bid, direct buy
@role_required('product_manager')                 # Verify batch
@role_required('admin')                           # Resolve dispute, reports
@role_required('product_manager', 'admin')        # Staff-only views
@role_required('farmer', 'trader')                # Order list (participants)
```

### Status Transition Map

```
Batch:     pending → under_review → verified → listed → sold
                                     └→ rejected
Order:     pending → confirmed → processing → shipped → delivered
           any ──────────────────────────────────────→ cancelled
           any ──────────────────────────────────────→ disputed
Dispute:   open → under_review → resolved → closed
Bid:       active → accepted | rejected | outbid | expired
```

### Batch → Listing → Order Flow

```
Batch.created (pending)
  → PM picks for review (under_review)
  → PM verifies (verified) → SIGNAL creates Listing (listed)
  → Trader buys or wins auction → Order created (pending)
  → Order fulfilled → (delivered)
```

### Decimal Field Standards

| Field | max_digits | decimal_places |
|-------|------------|----------------|
| quantity_kg | 10 | 2 |
| price_per_kg | 10 | 2 |
| total_amount | 12 | 2 |
| area_acres | 8 | 2 |
| moisture_pct | 5 | 2 |
| purity_pct | 5 | 2 |
| min_order_kg | 10 | 2 |

---

*End of AGENTS.md — Follow these instructions precisely for all CardeTrade development tasks.*
