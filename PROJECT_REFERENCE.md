# CardeTrade — Project Reference

> **Cardamom Trading Platform** | Django 5.x | Single-App Architecture (`app`)
> 
> A centralized web platform for transparent, verified-grade-first trading of cardamom between farmers, traders, and companies.

---

## Table of Contents

1. [Project Identity](#1-project-identity)
2. [Repository Structure](#2-repository-structure)
3. [Tech Stack](#3-tech-stack)
4. [User Roles & Permissions](#4-user-roles--permissions)
5. [Role Enforcement System](#5-role-enforcement-system)
6. [Complete Database Schema (16 Tables)](#6-complete-database-schema-16-tables)
7. [Entity Relationship Map](#7-entity-relationship-map)
8. [Status State Machines](#8-status-state-machines)
9. [URL Structure](#9-url-structure)
10. [View Patterns](#10-view-patterns)
11. [Form Patterns](#11-form-patterns)
12. [Template Patterns](#12-template-patterns)
13. [Signal Implementations](#13-signal-implementations)
14. [Admin Configuration](#14-admin-configuration)
15. [Testing Patterns](#15-testing-patterns)
16. [Business Flow / User Journeys](#16-business-flow--user-journeys)
17. [Code Conventions & Rules](#17-code-conventions--rules)
18. [Setup Guide](#18-setup-guide)
19. [Environment Variables](#19-environment-variables)
20. [Quick Reference Cheat Sheets](#20-quick-reference-cheat-sheets)

---

## 1. Project Identity

| Property | Value |
|----------|-------|
| **Name** | CardeTrade — Cardamom Trading Platform |
| **Type** | Django 5.x web application (Python 3.11+) |
| **Database** | SQLite (dev) / PostgreSQL (prod) |
| **Frontend** | HTML + CSS + Bootstrap 5 (server-rendered templates) |
| **Auth** | Custom `AbstractUser` with role field |
| **App Architecture** | Single app named `app` (all models, views, forms in one place) |
| **Styling** | Bootstrap 5 only (no MUI, no React, no Tailwind) |
| **Audit** | Every mutation logged via `AuditLog` |
| **Tests** | Django `TestCase` with `setUpTestData` |

### Core Philosophy

```
                    GRADE FIRST → TRADE SECOND
```

A batch **cannot** be sold until an independent Product Manager has inspected it and assigned an official quality grade (A, B, or C). This removes the guesswork and disputes from traditional cardamom trading.

---

## 2. Repository Structure

```
CardeTrade/
├── .env                          # Environment variables (never commit)
├── .gitignore
├── AGENTS.md                     # AI agent instruction manual
├── manage.py                     # Django CLI entry point
├── requirements.txt              # Python dependencies
│
├── cardetrade/                   # Django project configuration
│   ├── __init__.py
│   ├── settings.py               # AUTH_USER_MODEL = 'app.User'
│   ├── urls.py                   # Root URL routing
│   ├── wsgi.py                   # WSGI deployment entry
│   └── asgi.py                   # ASGI entry
│
├── app/                          # Single Django app (core of the platform)
│   ├── __init__.py
│   ├── models.py                 # All 16 tables
│   ├── views.py                  # All platform views (CBVs + FBVs)
│   ├── urls.py                   # All URL routes
│   ├── forms.py                  # All forms
│   ├── decorators.py             # @role_required, etc.
│   ├── admin.py                  # Admin configurations
│   ├── tests.py                  # All test cases
│   ├── signals.py                # Post-save signals
│   ├── middleware.py              # Audit middleware
│   ├── utils.py                  # Helper functions
│   ├── templates/app/            # App-specific HTML templates
│   └── migrations/               # Django auto-generated migrations
│
├── templates/                    # Shared templates
│   ├── base.html                 # Bootstrap 5 nav + footer + alerts
│   ├── includes/                 # Navbar, sidebar, pagination partials
│   └── admin/                    # Django admin overrides
│
├── static/                       # Static assets
│   ├── css/style.css
│   └── js/main.js
│
└── media/                        # User-uploaded files
    ├── batch_images/
    └── documents/
```

---

## 3. Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Backend** | Python 3.11+ / Django 5.x | Web framework, ORM, auth, routing |
| **Database** | SQLite (dev) / PostgreSQL (prod) | Relational data storage |
| **ORM** | Django ORM (with `GeneratedField` for computed columns) | Database abstraction |
| **Frontend** | HTML5, CSS3, Vanilla JS | Server-rendered templates |
| **Styling** | Bootstrap 5 | Responsive UI, grid system, components |
| **Forms** | `django-crispy-forms` + `crispy-bootstrap5` | Form rendering |
| **Auth** | Django Auth + `AbstractUser` | Built-in sessions, password hashing |
| **Authorization** | Custom `@role_required` decorator | Role-based view gating |
| **Auditing** | Django `post_save` signals | Automatic audit log entries |
| **Messaging** | Database-driven | In-app chat system |
| **Payments** | Manual record | Payment tracking |

### Dependencies (`requirements.txt`)

```
Django>=5.0,<5.2
python-decouple==3.*
Pillow==10.*
django-crispy-forms==2.*
crispy-bootstrap5==2024.*
```

---

## 4. User Roles & Permissions

### Role Definitions

| Role | `role` field value | `is_staff` | `is_superuser` | Capabilities | Restricted From |
|------|-------------------|------------|----------------|--------------|-----------------|
| **Farmer** | `farmer` | `False` | `False` | Register farms, create batches, view verification, accept offers, track orders | Bidding, verification, admin panel |
| **Trader** | `trader` | `False` | `False` | Browse listings, direct buy, place bids, track orders, make payments | Creating batches, verification |
| **Product Manager** | `product_manager` | `True` | `False` | Verify batches, assign grade A/B/C, set verified price, chat with farmers | Trading, bidding |
| **Admin** | `admin` | `True` | `True` | All CRUD, user management, reports, dispute resolution, audit view | Nothing |

### Role → `is_staff` / `is_superuser` Mapping

Set automatically in `User.save()`:

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

## 5. Role Enforcement System

### Decorator (`app/decorators.py`)

```python
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
```

### Convenience Decorators

| Decorator | Allowed Roles |
|-----------|---------------|
| `@farmer_required` | `farmer` |
| `@trader_required` | `trader` |
| `@pm_required` | `product_manager` |
| `@admin_required` | `admin` |
| `@staff_required` | `product_manager`, `admin` |
| `@trade_participant_required` | `farmer`, `trader` |

### Usage on CBVs

```python
from django.utils.decorators import method_decorator

@method_decorator(role_required('farmer'), name='dispatch')
class BatchCreateView(LoginRequiredMixin, CreateView):
    ...
```

### Usage on FBVs

```python
@role_required('farmer')
def create_batch(request):
    ...
```

---

## 6. Complete Database Schema (16 Tables)

### 6.1 `User` — All system accounts

```python
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
```

**Inherited from `AbstractUser`:** `username`, `email`, `password`, `first_name`, `last_name`, `is_active`, `is_staff`, `is_superuser`, `date_joined`, `last_login`.

---

### 6.2 `Farm` — Farmer-owned farm profiles

| Field | Type | Constraints |
|-------|------|-------------|
| `farmer` | FK → `User` | `on_delete=CASCADE`, `related_name='farms'`, `limit_choices_to={'role': 'farmer'}` |
| `farm_name` | `CharField(150)` | `NOT NULL` |
| `location` | `CharField(200)` | `blank=True, default=''` |
| `region` | `CharField(100)` | `blank=True, default=''` |
| `total_area_acres` | `DecimalField(8,2)` | `null=True, blank=True` |
| `certification` | `CharField(100)` | `blank=True, default=''` |
| `created_at` | `DateTimeField` | `auto_now_add=True` |

**Meta:** `verbose_name_plural = 'farms'`, `ordering = ['-created_at']`

---

### 6.3 `Batch` — Cardamom batch lifecycle (core entity)

| Field | Type | Constraints |
|-------|------|-------------|
| `batch_code` | `CharField(50)` | `unique=True, editable=False` — format: `CDM-YYYY-NNNN` |
| `farmer` | FK → `User` | `on_delete=CASCADE`, `related_name='batches'`, `limit_choices_to={'role': 'farmer'}` |
| `farm` | FK → `Farm` | `on_delete=SET_NULL`, `null=True`, `related_name='batches'` |
| `quantity_kg` | `DecimalField(10,2)` | `NOT NULL` |
| `harvest_date` | `DateField` | `NOT NULL` |
| `description` | `TextField` | `blank=True, default=''` |
| `estimated_price_per_kg` | `DecimalField(10,2)` | `NOT NULL` |
| `status` | `CharField(20)` | `choices=Status.choices, default=Status.PENDING` |
| `created_at` | `DateTimeField` | `auto_now_add=True` |
| `updated_at` | `DateTimeField` | `auto_now=True` |

#### `Batch.Status` (TextChoices)

```
PENDING       → 'pending'
UNDER_REVIEW  → 'under_review'
VERIFIED      → 'verified'
LISTED        → 'listed'
SOLD          → 'sold'
REJECTED      → 'rejected'
```

**Batch Code Generation:**
```python
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
```

---

### 6.4 `QualityVerification` — Product Manager grading records

| Field | Type | Constraints |
|-------|------|-------------|
| `batch` | `OneToOneField` → `Batch` | `on_delete=CASCADE`, `related_name='verification'` |
| `product_manager` | FK → `User` | `on_delete=SET_NULL`, `null=True`, `related_name='verifications'` |
| `grade` | `CharField(1)` | `choices=Grade.choices` (A/B/C) |
| `moisture_content_pct` | `DecimalField(5,2)` | `null=True, blank=True` |
| `aroma_score` | `PositiveSmallIntegerField` | `null=True, blank=True` (1–10) |
| `color_score` | `PositiveSmallIntegerField` | `null=True, blank=True` (1–10) |
| `purity_pct` | `DecimalField(5,2)` | `null=True, blank=True` |
| `verified_price_per_kg` | `DecimalField(10,2)` | `NOT NULL` |
| `remarks` | `TextField` | `blank=True, default=''` |
| `verified_at` | `DateTimeField` | `auto_now_add=True` |

**Rule:** One verification per batch (enforced by `OneToOneField`).

---

### 6.5 `Listing` — Active market board listings

| Field | Type | Constraints |
|-------|------|-------------|
| `batch` | `OneToOneField` → `Batch` | `on_delete=CASCADE`, `related_name='listing'` |
| `farmer` | FK → `User` | `on_delete=CASCADE`, `related_name='listings'` |
| `listing_type` | `CharField(20)` | `choices=ListingType.choices` |
| `price_per_kg` | `DecimalField(10,2)` | `NOT NULL` |
| `min_order_kg` | `DecimalField(10,2)` | `null=True, blank=True` |
| `available_qty_kg` | `DecimalField(10,2)` | `NOT NULL` |
| `auction_start_time` | `DateTimeField` | `null=True, blank=True` |
| `auction_end_time` | `DateTimeField` | `null=True, blank=True` |
| `is_active` | `BooleanField` | `default=True` |
| `created_at` | `DateTimeField` | `auto_now_add=True` |

#### `Listing.ListingType` (TextChoices)

```
FIXED_PRICE  → 'fixed_price'
AUCTION      → 'auction'
```

**Rule:** One listing per batch (enforced by `OneToOneField`).

---

### 6.6 `Bid` — Auction bid records

| Field | Type | Constraints |
|-------|------|-------------|
| `listing` | FK → `Listing` | `on_delete=CASCADE`, `related_name='bids'` |
| `trader` | FK → `User` | `on_delete=CASCADE`, `related_name='bids'`, `limit_choices_to={'role': 'trader'}` |
| `bid_price_per_kg` | `DecimalField(10,2)` | `NOT NULL` |
| `quantity_kg` | `DecimalField(10,2)` | `NOT NULL` |
| `status` | `CharField(10)` | `choices=Status.choices, default=Status.ACTIVE` |
| `notes` | `TextField` | `blank=True, default=''` |
| `bid_time` | `DateTimeField` | `auto_now_add=True` |

#### `Bid.Status` (TextChoices)

```
ACTIVE   → 'active'
ACCEPTED → 'accepted'
REJECTED → 'rejected'
OUTBID   → 'outbid'
EXPIRED  → 'expired'
```

**Meta:** `ordering = ['-bid_price_per_kg']`

---

### 6.7 `Order` — Confirmed trade orders (core transaction entity)

| Field | Type | Constraints |
|-------|------|-------------|
| `order_code` | `CharField(50)` | `unique=True, editable=False` — format: `ORD-YYYY-NNNN` |
| `listing` | FK → `Listing` | `on_delete=SET_NULL`, `null=True`, `related_name='orders'` |
| `batch` | FK → `Batch` | `on_delete=SET_NULL`, `null=True`, `related_name='orders'` |
| `buyer` | FK → `User` | `on_delete=CASCADE`, `related_name='purchases'`, `limit_choices_to={'role': 'trader'}` |
| `seller` | FK → `User` | `on_delete=CASCADE`, `related_name='sales'`, `limit_choices_to={'role': 'farmer'}` |
| `bid` | FK → `Bid` | `on_delete=SET_NULL`, `null=True, blank=True`, `related_name='orders'` |
| `quantity_kg` | `DecimalField(10,2)` | |
| `price_per_kg` | `DecimalField(10,2)` | |
| `total_amount` | `GeneratedField` | `quantity_kg * price_per_kg` (computed column) |
| `status` | `CharField(20)` | `choices=Status.choices, default=Status.PENDING` |
| `payment_status` | `CharField(20)` | `choices=PaymentStatus.choices, default=PaymentStatus.UNPAID` |
| `created_at` | `DateTimeField` | `auto_now_add=True` |
| `updated_at` | `DateTimeField` | `auto_now=True` |

#### `Order.Status` (TextChoices)

```
PENDING     → 'pending'
CONFIRMED   → 'confirmed'
PROCESSING  → 'processing'
SHIPPED     → 'shipped'
DELIVERED   → 'delivered'
CANCELLED   → 'cancelled'
DISPUTED    → 'disputed'
```

#### `Order.PaymentStatus` (TextChoices)

```
UNPAID          → 'unpaid'
PARTIALLY_PAID  → 'partially_paid'
PAID            → 'paid'
REFUNDED        → 'refunded'
```

**`total_amount` using Django 5+ `GeneratedField`:**
```python
total_amount = GeneratedField(
    expression=ExpressionWrapper(
        F('quantity_kg') * F('price_per_kg'),
        output_field=DecimalField(max_digits=12, decimal_places=2)
    ),
    output_field=DecimalField(max_digits=12, decimal_places=2),
    db_persist=True
)
```

---

### 6.8 `OrderTracking` — Shipment/delivery status history

| Field | Type | Constraints |
|-------|------|-------------|
| `order` | FK → `Order` | `on_delete=CASCADE`, `related_name='tracking_entries'` |
| `status` | `CharField(20)` | `choices=Status.choices` |
| `location` | `CharField(200)` | `blank=True, default=''` |
| `notes` | `TextField` | `blank=True, default=''` |
| `updated_by` | FK → `User` | `on_delete=SET_NULL`, `null=True`, `related_name='tracking_updates'` |
| `tracked_at` | `DateTimeField` | `auto_now_add=True` |

---

### 6.9 `Payment` — Payment transaction records

| Field | Type | Constraints |
|-------|------|-------------|
| `order` | FK → `Order` | `on_delete=CASCADE`, `related_name='payments'` |
| `payer` | FK → `User` | `on_delete=SET_NULL`, `null=True`, `related_name='payments'` |
| `amount` | `DecimalField(12,2)` | |
| `payment_method` | `CharField(20)` | `choices=PaymentMethod.choices` |
| `transaction_ref` | `CharField(100)` | `unique=True, null=True, blank=True` |
| `status` | `CharField(10)` | `choices=Status.choices, default=Status.PENDING` |
| `paid_at` | `DateTimeField` | `null=True, blank=True` |
| `created_at` | `DateTimeField` | `auto_now_add=True` |

#### `Payment.PaymentMethod` (TextChoices)

```
BANK_TRANSFER  → 'bank_transfer'
MOBILE_MONEY   → 'mobile_money'
CASH           → 'cash'
ESCROW         → 'escrow'
```

---

### 6.10 `Dispute` — Conflict resolution records

| Field | Type | Constraints |
|-------|------|-------------|
| `order` | FK → `Order` | `on_delete=CASCADE`, `related_name='disputes'` |
| `raised_by` | FK → `User` | `on_delete=CASCADE`, `related_name='disputes_raised'` |
| `against_user` | FK → `User` | `on_delete=CASCADE`, `related_name='disputes_against'` |
| `reason` | `TextField` | |
| `status` | `CharField(20)` | `choices=Status.choices, default=Status.OPEN` |
| `resolution` | `TextField` | `blank=True, default=''` |
| `resolved_by` | FK → `User` | `on_delete=SET_NULL`, `null=True, blank=True` |
| `created_at` | `DateTimeField` | `auto_now_add=True` |
| `resolved_at` | `DateTimeField` | `null=True, blank=True` |

#### `Dispute.Status` (TextChoices)

```
OPEN          → 'open'
UNDER_REVIEW  → 'under_review'
RESOLVED      → 'resolved'
CLOSED        → 'closed'
```

---

### 6.11 `Notification` — In-app notification system

| Field | Type | Constraints |
|-------|------|-------------|
| `user` | FK → `User` | `on_delete=CASCADE`, `related_name='notifications'` |
| `type` | `CharField(30)` | `choices=Type.choices` |
| `message` | `TextField` | |
| `reference_id` | `IntegerField` | `null=True, blank=True` |
| `reference_type` | `CharField(50)` | `blank=True, default=''` |
| `is_read` | `BooleanField` | `default=False` |
| `created_at` | `DateTimeField` | `auto_now_add=True` |

#### `Notification.Type` (TextChoices)

```
BID_RECEIVED      → 'bid_received'
BID_ACCEPTED      → 'bid_accepted'
ORDER_PLACED      → 'order_placed'
ORDER_SHIPPED     → 'order_shipped'
PAYMENT_RECEIVED  → 'payment_received'
BATCH_VERIFIED    → 'batch_verified'
DISPUTE_RAISED    → 'dispute_raised'
```

---

### 6.12 `Conversation` — Chat thread headers

| Field | Type | Constraints |
|-------|------|-------------|
| `batch` | FK → `Batch` | `on_delete=SET_NULL`, `null=True, blank=True` |
| `order` | FK → `Order` | `on_delete=SET_NULL`, `null=True, blank=True` |
| `type` | `CharField(20)` | `choices=Type.choices` |
| `subject` | `CharField(200)` | `blank=True, default=''` |
| `status` | `CharField(10)` | `choices=Status.choices, default=Status.OPEN` |
| `created_at` | `DateTimeField` | `auto_now_add=True` |
| `last_message_at` | `DateTimeField` | `null=True, blank=True` |

#### `Conversation.Type` (TextChoices)

```
QUALITY_REVIEW  → 'quality_review'
BATCH_INQUIRY   → 'batch_inquiry'
ORDER_SUPPORT   → 'order_support'
GENERAL         → 'general'
```

---

### 6.13 `ConversationParticipant` — Thread membership (M2M with attributes)

| Field | Type | Constraints |
|-------|------|-------------|
| `conversation` | FK → `Conversation` | `on_delete=CASCADE`, `related_name='participants'` |
| `user` | FK → `User` | `on_delete=CASCADE`, `related_name='conversation_participations'` |
| `role_in_chat` | `CharField(20)` | `choices=RoleInChat.choices` |
| `joined_at` | `DateTimeField` | `auto_now_add=True` |
| `last_read_at` | `DateTimeField` | `null=True, blank=True` |
| `is_muted` | `BooleanField` | `default=False` |
| `is_active` | `BooleanField` | `default=True` |

**Meta:** `unique_together = ('conversation', 'user')`

---

### 6.14 `Message` — Individual chat messages (high volume)

| Field | Type | Constraints |
|-------|------|-------------|
| `conversation` | FK → `Conversation` | `on_delete=CASCADE`, `related_name='messages'` |
| `sender` | FK → `User` | `on_delete=SET_NULL`, `null=True` |
| `message_type` | `CharField(10)` | `choices=MessageType.choices, default=MessageType.TEXT` |
| `content` | `TextField` | `blank=True, default=''` |
| `attachments` | `JSONField` | `null=True, blank=True, default=list` |
| `is_edited` | `BooleanField` | `default=False` |
| `edited_at` | `DateTimeField` | `null=True, blank=True` |
| `is_deleted` | `BooleanField` | `default=False` (soft delete — only table with this) |
| `deleted_at` | `DateTimeField` | `null=True, blank=True` |
| `sent_at` | `DateTimeField` | `auto_now_add=True` |

---

### 6.15 `Report` — Admin-generated report records

| Field | Type | Constraints |
|-------|------|-------------|
| `generated_by` | FK → `User` | `on_delete=CASCADE`, `related_name='generated_reports'` |
| `report_type` | `CharField(30)` | `choices=ReportType.choices` |
| `date_from` | `DateField` | `null=True, blank=True` |
| `date_to` | `DateField` | `null=True, blank=True` |
| `parameters` | `JSONField` | `null=True, blank=True, default=dict` |
| `file_path` | `CharField(255)` | `blank=True, default=''` |
| `created_at` | `DateTimeField` | `auto_now_add=True` |

#### `Report.ReportType` (TextChoices)

```
TRADE_SUMMARY        → 'trade_summary'
GRADE_DISTRIBUTION   → 'grade_distribution'
FARMER_PERFORMANCE   → 'farmer_performance'
TRADER_ACTIVITY      → 'trader_activity'
REVENUE              → 'revenue'
```

---

### 6.16 `AuditLog` — Immutable action trail

| Field | Type | Constraints |
|-------|------|-------------|
| `user` | FK → `User` | `on_delete=SET_NULL`, `null=True, blank=True` |
| `action` | `CharField(100)` | e.g., `'batch.verified'`, `'order.created'` |
| `table_name` | `CharField(50)` | |
| `record_id` | `IntegerField` | |
| `old_value` | `JSONField` | `null=True, blank=True` |
| `new_value` | `JSONField` | `null=True, blank=True` |
| `ip_address` | `CharField(45)` | `blank=True, default=''` |
| `logged_at` | `DateTimeField` | `auto_now_add=True` |

**Indexes:** `(table_name, record_id)`, `(action)`, `(user)`

---

## 7. Entity Relationship Map

```
User ──1:N── Farm
User ──1:N── Batch (as farmer)
User ──1:N── QualityVerification (as product_manager)
User ──1:N── Listing (as farmer)
User ──1:N── Bid (as trader)
User ──1:N── Order (as buyer)
User ──1:N── Order (as seller)
User ──1:N── Payment (as payer)
User ──1:N── Dispute (as raised_by / against_user)
User ──1:N── Notification
User ──1:N── AuditLog
User ──M:N── Conversation (via ConversationParticipant)

Batch ──1:1── QualityVerification
Batch ──1:1── Listing
Batch ──1:N── Order
Batch ──1:N── Conversation

Listing ──1:N── Bid
Listing ──1:N── Order

Order ──1:N── OrderTracking
Order ──1:N── Payment
Order ──1:N── Dispute
Order ──1:N── Conversation

Conversation ──1:N── Message
Conversation ──1:N── ConversationParticipant
```

---

## 8. Status State Machines

### Batch Status Flow

```
                      ┌──────────────────┐
                      │     PENDING      │
                      │  (farmer creates)│
                      └────────┬─────────┘
                               │
                      ┌────────▼─────────┐
                      │   UNDER_REVIEW   │
                      │  (PM picks up)   │
                      └────────┬─────────┘
                               │
                    ┌──────────┴──────────┐
                    │                     │
          ┌─────────▼─────────┐  ┌────────▼─────────┐
          │     VERIFIED      │  │     REJECTED     │
          │ (PM grades A/B/C) │  │                  │
          └─────────┬─────────┘  └──────────────────┘
                    │
          ┌─────────▼─────────┐
          │      LISTED       │
          │(listing auto-     │
          │ created via signal)│
          └─────────┬─────────┘
                    │
          ┌─────────▼─────────┐
          │       SOLD        │
          │  (all qty sold)   │
          └───────────────────┘
```

### Order Status Flow

```
                 ┌──────────┐
                 │ PENDING  │
                 └────┬─────┘
                      │
                 ┌────▼─────┐
                 │CONFIRMED │
                 └────┬─────┘
                      │
                 ┌────▼─────┐
                 │PROCESSING│
                 └────┬─────┘
                      │
                 ┌────▼─────┐
                 │ SHIPPED  │
                 └────┬─────┘
                      │
                 ┌────▼──────┐
                 │ DELIVERED │
                 │   ✓ Done  │
                 └───────────┘

Any stage ──→ CANCELLED
Any stage ──→ DISPUTED
```

### Dispute Status Flow

```
OPEN → UNDER_REVIEW → RESOLVED → CLOSED
```

### Bid Status Flow

```
ACTIVE → ACCEPTED | REJECTED | OUTBID | EXPIRED
```

---

## 9. URL Structure

### Root `cardetrade/urls.py`

```python
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('app.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

### App `app/urls.py`

```python
from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('profile/', views.ProfileView.as_view(), name='profile'),

    # Farms
    path('farms/', views.FarmListView.as_view(), name='farm_list'),
    path('farms/create/', views.FarmCreateView.as_view(), name='farm_create'),
    path('farms/<int:pk>/', views.FarmUpdateView.as_view(), name='farm_edit'),

    # Batches
    path('batches/', views.BatchListView.as_view(), name='batch_list'),
    path('batches/create/', views.BatchCreateView.as_view(), name='batch_create'),
    path('batches/<int:pk>/', views.BatchDetailView.as_view(), name='batch_detail'),
    path('batches/<int:pk>/verify/', views.BatchVerifyView.as_view(), name='batch_verify'),

    # Trading / Listings
    path('listings/', views.ListingListView.as_view(), name='listing_list'),
    path('listings/<int:pk>/', views.ListingDetailView.as_view(), name='listing_detail'),
    path('listings/<int:pk>/bid/', views.PlaceBidView.as_view(), name='place_bid'),
    path('listings/<int:pk>/buy/', views.DirectBuyView.as_view(), name='direct_buy'),
    path('bids/', views.MyBidsView.as_view(), name='my_bids'),

    # Orders
    path('orders/', views.OrderListView.as_view(), name='order_list'),
    path('orders/<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),

    # Notifications
    path('notifications/', views.NotificationListView.as_view(), name='notification_list'),
    path('notifications/<int:pk>/read/', views.MarkNotificationReadView.as_view(), name='mark_read'),

    # Dashboard
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('', views.HomeView.as_view(), name='home'),
]
```

---

## 10. View Patterns

### Class-Based Views (CBVs) — Preferred

```python
from django.views.generic import CreateView, ListView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from .decorators import role_required
from .models import Batch
from .forms import BatchForm

@method_decorator(role_required('farmer'), name='dispatch')
class BatchCreateView(LoginRequiredMixin, CreateView):
    model = Batch
    form_class = BatchForm
    template_name = 'app/batch_create.html'
    success_url = reverse_lazy('batch_list')

    def form_valid(self, form):
        form.instance.farmer = self.request.user
        return super().form_valid(form)
```

### Function-Based Views (FBVs) — For Simple Pages

```python
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
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

---

## 11. Form Patterns

```python
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

class VerificationForm(forms.ModelForm):
    class Meta:
        model = QualityVerification
        fields = ['grade', 'moisture_content_pct', 'aroma_score',
                  'color_score', 'purity_pct', 'verified_price_per_kg', 'remarks']
```

---

## 12. Template Patterns

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
                        <button type="submit" class="btn btn-success">Submit Batch</button>
                    </div>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

---

## 13. Signal Implementations

### 13.1 Batch Verified → Create Listing

```python
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Batch, Listing

@receiver(post_save, sender=Batch)
def create_listing_on_verification(sender, instance, created, **kwargs):
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

### 13.2 Order Created → Notify Seller

```python
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

### 13.3 Bid Placed → Notify Farmer

```python
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

### 13.4 Message Sent → Update Conversation Timestamp

```python
@receiver(post_save, sender=Message)
def update_conversation_timestamp(sender, instance, created, **kwargs):
    if created:
        conversation = instance.conversation
        conversation.last_message_at = instance.sent_at
        conversation.save(update_fields=['last_message_at'])
```

### Signal Registration in `apps.py`

```python
from django.apps import AppConfig

class AppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'

    def ready(self):
        import app.signals
```

---

## 14. Admin Configuration

```python
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Batch, QualityVerification, Listing, Bid, Order

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'role', 'is_staff', 'is_active']
    list_filter = ['role', 'is_staff', 'is_active']
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 'phone', 'region')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser',
                                     'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )

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

## 15. Testing Patterns

### Test Structure

```python
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

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

    def test_batch_created_as_pending(self):
        self.client.login(username='farmer', password='test')
        response = self.client.post(reverse('batch_create'), {
            'quantity_kg': 100.50,
            'harvest_date': '2026-03-15',
            'estimated_price_per_kg': 45.00,
        })
        self.assertEqual(response.status_code, 302)
        batch = Batch.objects.last()
        self.assertEqual(batch.status, Batch.Status.PENDING)

    def test_unauthorized_access_returns_403(self):
        trader = User.objects.create_user(
            username='trader', password='test', role='trader'
        )
        self.client.login(username='trader', password='test')
        response = self.client.get(reverse('batch_create'))
        self.assertEqual(response.status_code, 403)
```

### Running Tests

```bash
# All tests
python manage.py test

# With coverage
coverage run --source='.' manage.py test
coverage report
```

---

## 16. Business Flow / User Journeys

### End-to-End Flow

```
1. FARMER:  Register → Create Farm → Create Batch (pending)
2. PM:      View pending batches → Inspect batch → Verify (verified)
            → SIGNAL auto-creates Listing (listed)
3. TRADER:  Browse listings → Direct Buy OR Place Bid
4. ADMIN:   Approve bid → Order created → Update shipping status
5. ALL:     Receive notifications at each step
```

### Notification Triggers

| Event | Notification To |
|-------|-----------------|
| Bid received on farmer's listing | Farmer |
| Bid accepted / Outbid | Trader |
| Order placed | Farmer |
| Order shipped | Trader (buyer) |
| Payment received | Farmer |
| Batch verified | Farmer |
| Dispute raised | Admin |

---

## 17. Code Conventions & Rules

### Critical Rules (Must Follow)

| # | Rule | Rationale |
|---|------|-----------|
| **R1** | Use `models.TextChoices` for all enums | Database stores strings, not integers |
| **R2** | Always set `related_name` on every `ForeignKey` | Django creates backwards relations automatically |
| **R3** | `total_amount` on Order must be `GeneratedField` or `@property` | Never store as a regular DB column |
| **R4** | `AUTH_USER_MODEL = 'app.User'` must be set before first migration | Otherwise Django creates its own `auth_user` table |
| **R5** | Soft delete for `messages` only | Messages are sensitive; hard delete causes data loss |
| **R6** | Every state mutation must be logged in `audit_logs` | Legal/compliance requirement |
| **R7** | `is_staff=True` for Product Manager but `is_superuser=False` | PM gets admin panel access but not full control |
| **R8** | Always reference ENUM constants via model class, not as raw strings | e.g., `Batch.Status.PENDING` not `'pending'` |
| **R9** | `conversation_participants` uses `unique_together`, not composite PK | Django doesn't support composite PKs |
| **R10** | Farmers cannot bid. Traders cannot create batches. PMs cannot trade. | Enforce via `@role_required` decorator |

### Import Order

```python
# 1. Python standard library
from functools import wraps
import json

# 2. Django core
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden
from django.urls import reverse, reverse_lazy
from django.utils import timezone

# 3. Third-party
from crispy_forms.helper import FormHelper

# 4. Local project imports
from .decorators import role_required
from .models import Batch, Order
from .forms import BatchForm
```

### Decimal Field Standards

| Field | `max_digits` | `decimal_places` |
|-------|--------------|------------------|
| `quantity_kg` | 10 | 2 |
| `price_per_kg` | 10 | 2 |
| `total_amount` | 12 | 2 |
| `area_acres` | 8 | 2 |
| `moisture_pct` | 5 | 2 |
| `purity_pct` | 5 | 2 |
| `min_order_kg` | 10 | 2 |

### Common Pitfalls (Must Avoid)

| Pitfall | Correct Approach |
|---------|-----------------|
| `class Status(models.IntegerChoices)` | `class Status(models.TextChoices)` |
| `farmer = models.ForeignKey(User)` without `related_name` | `farmer = models.ForeignKey(User, related_name='batches')` |
| `'pending'` hardcoded in view logic | `Batch.Status.PENDING` |
| `@login_required` only, no role check | `@role_required('farmer')` which includes login check |
| Creating listing manually in a view | Use `post_save` signal on Batch verification |
| Storing files without validation | Check file type, size, use `FileExtensionValidator` |

---

## 18. Setup Guide

### Prerequisites

- Python 3.11+
- pip
- Virtual environment (recommended)

### Installation

```bash
# 1. Clone and enter project
git clone <repo-url> CardeTrade
cd CardeTrade

# 2. Create and activate virtual environment
python -m venv env
# Windows:
env\Scripts\activate
# macOS/Linux:
source env/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run migrations
python manage.py makemigrations app
python manage.py migrate

# 5. Create superuser
python manage.py createsuperuser

# 6. Run dev server
python manage.py runserver

# Open: http://127.0.0.1:8000/
```

### Requirements (`requirements.txt`)

```
Django>=5.0,<5.2
python-decouple==3.*
Pillow==10.*
django-crispy-forms==2.*
crispy-bootstrap5==2024.*
```

---

## 19. Environment Variables

```ini
# .env (never commit)
DJANGO_SECRET_KEY=your-strong-secret-key-here
DJANGO_DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
```

---

## 20. Quick Reference Cheat Sheets

### `@role_required` Quick Reference

```python
@role_required('farmer')                          # Create batch, register farm
@role_required('trader')                          # Place bid, direct buy
@role_required('product_manager')                 # Verify batch
@role_required('admin')                           # Resolve dispute, reports
@role_required('product_manager', 'admin')        # Staff-only views
@role_required('farmer', 'trader')                # Order list (participants)
```

### Status Transition Summary

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

### File & Naming Conventions

| Resource | Convention | Example |
|----------|------------|---------|
| Model | `PascalCase, singular` | `QualityVerification`, `OrderTracking` |
| Model field | `snake_case` | `verified_price_per_kg` |
| View (CBV) | `PascalCase + View` | `BatchCreateView` |
| View (FBV) | `snake_case` | `register_view` |
| Form | `PascalCase + Form` | `BatchForm` |
| Template | `snake_case` | `batch_create.html` |
| URL name | `snake_case` | `batch_create`, `listing_list` |
| Signal receiver | `snake_case, descriptive` | `create_listing_on_verification` |

### Settings Config (Critical Lines)

```python
AUTH_USER_MODEL = 'app.User'          # Must be set before first migration
INSTALLED_APPS = ['app', ...]         # Single app
LOGIN_URL = '/login/'
CRISPY_TEMPLATE_PACK = 'bootstrap5'
```
