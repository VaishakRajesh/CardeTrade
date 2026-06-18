# 🌿 CardeTrade — Cardamom Trading Platform

> **A centralized, web-based system for transparent and efficient trade of cardamom between farmers, traders, and companies, with standardized quality verification through a dedicated Product Manager role.**

---

## 📑 Table of Contents

- [Project Overview](#-project-overview)
- [Problem & Solution](#-problem--solution)
- [Tech Stack](#-tech-stack)
- [Roles & Permissions](#-roles--permissions)
- [User Journeys](#-user-journeys)
- [Architecture](#-architecture)
- [Database Schema (16 Tables)](#-database-schema)
- [Entity Relationship Diagram](#-entity-relationship-diagram)
- [Business Rules](#-business-rules)
- [Workflows](#-workflows)
- [Django App Organization](#-django-app-organization)
- [API Reference](#-api-reference)
- [Testing Strategy](#-testing-strategy)
- [Setup Guide](#-setup-guide)
- [Deployment](#-deployment)
- [Security Considerations](#-security-considerations)
- [Contributing](#-contributing)
- [Roadmap](#-roadmap)

---

## 📖 Project Overview

CardeTrade is a **role-based** online marketplace where:

- **Farmers** register their farms, create cardamom batches, set estimated prices, and wait for quality verification before their stock becomes tradeable.
- **Product Managers** inspect batches, assign a quality grade (**A**, **B**, or **C**), set a verified market price, and approve the batch for listing.
- **Traders/Companies** browse verified listings, purchase directly at fixed price or participate in auctions via bidding.
- **Admins** oversee all transactions, manage users, resolve disputes, and generate trade/quality reports.

The platform enforces **standardized quality verification**, creates a **centralized transaction record**, and promotes **trust and fairness** — eliminating the opacity of traditional cardamom markets.

---

## 🎯 Problem & Solution

| Problem | Solution |
|---------|----------|
| Farmers receive unfair pricing due to lack of transparency | Verified market price assigned by certified Product Manager |
| Quality verification is inconsistent and disputed | Standardized grading (A/B/C) with multi-metric scoring (moisture, aroma, color, purity) |
| Traders must visit farms physically — slow and inefficient | Online marketplace with direct buy and auction mechanisms |
| No central record — transactions lost or manipulated | Full audit trail (audit_logs table) tracking every state change |
| Disputes over quality and pricing drain time | Dedicated dispute resolution workflow with admin mediation |
| Manual documentation prone to errors | Automated batch codes, order codes, and computed totals |

---

## 🛠 Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Backend** | Python 3.11+ / Django 5.x | Web framework, ORM, auth, routing |
| **Database** | SQLite (dev) / PostgreSQL (prod) | Relational data storage |
| **Frontend** | HTML5, CSS3, JavaScript (Vanilla) | Server-rendered templates |
| **Styling** | Bootstrap 5 | Responsive UI, grid, components |
| **Authentication** | Django Auth + `AbstractUser` | Built-in sessions, password hashing |
| **Authorization** | Custom `@role_required` decorator | Role-based view gating |
| **Auditing** | Django `post_save` signals | Automatic audit log entries |
| **Messaging** | Database-driven (conversations + messages tables) | In-app chat system |
| **Payments** | Manual record (bank_transfer, mobile_money, cash, escrow) | Payment tracking |

---

## 👥 Roles & Permissions

| Role | `user.is_staff` | `user.is_superuser` | Capabilities | Restricted From |
|------|-----------------|---------------------|--------------|-----------------|
| **Farmer** | `False` | `False` | Register farms, create batches, view verification, accept offers, track orders | Bidding, verification, admin panel |
| **Trader/Company** | `False` | `False` | Browse listings, direct buy, place bids, track orders, make payments | Creating batches, verification |
| **Product Manager** | `True` | `False` | Verify batches, assign grade A/B/C, set verified price, chat with farmers | Trading, bidding, admin panel |
| **Admin** | `True` | `True` | All CRUD, user management, all reports, dispute resolution, audit view | Nothing |

### Auth Enforcement Pattern

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

@role_required('product_manager', 'admin')
def verify_batch(request, batch_id):
    ...
```

---

## 🧭 User Journeys

### Farmer Journey
```
Sign Up (role: farmer)
  → Create Farm Profile
  → Record Batch (quantity, harvest date, estimated price)
  → Batch enters "pending" status
  → PM verifies → Farmer notified of grade & verified price
  → Batch listed automatically → Farmer waits for orders
  → Order received → Farmer ships → Tracks delivery
  → Payment received (marked paid)
```

### Product Manager Journey
```
Login (role: product_manager)
  → Dashboard shows pending batches
  → Select batch → Run quality checks
  → Assign Grade (A/B/C), set verified_price_per_kg
  → Submit verification → Batch auto-listed
  → Chat with farmer if clarification needed
```

### Trader Journey
```
Sign Up (role: trader)
  → Browse Listings (filter by grade, region, price)
  → Option A: Direct Buy at fixed price → Order created
  → Option B: Place Bid on auction listing
  → Track Order → Make Payment → Receive Delivery
  → Raise Dispute if quality doesn't match grade
```

### Admin Journey
```
Login (role: admin)
  → Dashboard with trade volume, grade distribution, active users
  → Manage Users (activate/deactivate, change roles)
  → View Reports (trade summary, quality reports, farmer performance)
  → Resolve Disputes → Close or mediate
  → Full Audit Log for any action
```

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Browser (Bootstrap 5)                │
│         HTML Templates ← Forms ← Django Templating      │
└──────────────────────────┬──────────────────────────────┘
                           │ HTTP Request/Response
┌──────────────────────────▼──────────────────────────────┐
│                   Django Application                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │ accounts │ │  farms   │ │ batches  │ │ trading  │   │
│  ├──────────┤ ├──────────┤ ├──────────┤ ├──────────┤   │
│  │ orders   │ │disputes  │ │ notif's  │ │messaging │   │
│  ├──────────┤ ├──────────┤ ├──────────┤ ├──────────┤   │
│  │ reports  │ │  audit   │ │          │ │          │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │
│                        │                                │
│         ┌──────────────▼──────────────┐                 │
│         │   Django ORM / Signals      │                 │
│         └──────────────┬──────────────┘                 │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│                   Database (SQLite/PostgreSQL)           │
│             16 Tables, Fully Normalized                 │
└─────────────────────────────────────────────────────────┘
```

### Request Lifecycle
```
User → Browser → URL → View → Decorator (role check)
  → View logic (ORM queries) → Signal triggers (audit, notif)
  → Template rendering → HTML Response → Browser
```

---

## 🗄 Database Schema

> All 16 tables with full column definitions, constraints, and descriptions.

---

### 1. `users` — All system accounts & role assignments

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `user_id` | `INT` | `PK, AUTO_INCREMENT` | Unique user identifier |
| `full_name` | `VARCHAR(100)` | `NOT NULL` | Full legal or display name |
| `email` | `VARCHAR(150)` | `UNIQUE, NOT NULL` | Used for login and notifications |
| `password_hash` | `VARCHAR(255)` | `NOT NULL` | Django PBKDF2 hashed password |
| `role` | `ENUM('farmer','trader','product_manager','admin')` | `NOT NULL` | Determines all access permissions |
| `phone` | `VARCHAR(20)` | `NULL` | Contact phone number |
| `address` | `TEXT` | `NULL` | Physical/mailing address |
| `region` | `VARCHAR(100)` | `NULL` | Geographic region (e.g., Idukki, Kerala) |
| `is_active` | `BOOLEAN` | `DEFAULT TRUE` | Can the user log in? |
| `is_staff` | `BOOLEAN` | `DEFAULT FALSE` | Django admin panel access |
| `created_at` | `TIMESTAMP` | `DEFAULT NOW()` | Registration timestamp |
| `updated_at` | `TIMESTAMP` | `ON UPDATE NOW()` | Last profile update |
| **Indexes** | | `PK(user_id)`, `UNIQUE(email)`, `INDEX(role)`, `INDEX(region)` | |

---

### 2. `farms` — Farmer-owned farm profiles

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `farm_id` | `INT` | `PK, AUTO_INCREMENT` | Unique farm identifier |
| `farmer_id` | `INT` | `FK → users.user_id, NOT NULL` | Farm owner (must be role='farmer') |
| `farm_name` | `VARCHAR(150)` | `NOT NULL` | Registered farm name |
| `location` | `VARCHAR(200)` | `NULL` | Physical address description |
| `region` | `VARCHAR(100)` | `NULL` | Growing region |
| `total_area_acres` | `DECIMAL(8,2)` | `NULL` | Farm size (0.00–999999.99) |
| `certification` | `VARCHAR(100)` | `NULL` | e.g., 'Organic', 'GAP', 'Fair Trade' |
| `created_at` | `TIMESTAMP` | `DEFAULT NOW()` | Registration date |
| **Indexes** | | `PK(farm_id)`, `INDEX(farmer_id)`, `INDEX(region)` | |

---

### 3. `batches` — Cardamom batch lifecycle (core entity)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `batch_id` | `INT` | `PK, AUTO_INCREMENT` | Unique batch identifier |
| `batch_code` | `VARCHAR(50)` | `UNIQUE, NOT NULL` | Business code, format: `CDM-YYYY-NNNN` |
| `farmer_id` | `INT` | `FK → users.user_id, NOT NULL` | Farmer who created the batch |
| `farm_id` | `INT` | `FK → farms.farm_id` | Source farm of this batch |
| `quantity_kg` | `DECIMAL(10,2)` | `NOT NULL` | Total weight in kilograms |
| `harvest_date` | `DATE` | `NOT NULL` | Date cardamom was harvested |
| `description` | `TEXT` | `NULL` | Farmer's notes (variety, condition, etc.) |
| `estimated_price_per_kg` | `DECIMAL(10,2)` | `NOT NULL` | Farmer's initial asking price |
| `status` | `ENUM('pending','under_review','verified','listed','sold','rejected')` | `DEFAULT 'pending'` | Current stage in batch lifecycle |
| `created_at` | `TIMESTAMP` | `DEFAULT NOW()` | Submission timestamp |
| `updated_at` | `TIMESTAMP` | `ON UPDATE NOW()` | Last status change |
| **Indexes** | | `PK(batch_id)`, `UNIQUE(batch_code)`, `INDEX(farmer_id)`, `INDEX(farm_id)`, `INDEX(status)` | |
| **Checks** | | `quantity_kg > 0`, `estimated_price_per_kg > 0` | |

---

### 4. `quality_verifications` — Product Manager grading records

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `verification_id` | `INT` | `PK, AUTO_INCREMENT` | Unique verification record |
| `batch_id` | `INT` | `FK → batches.batch_id, UNIQUE` | **One verification per batch** |
| `product_manager_id` | `INT` | `FK → users.user_id` | PM who performed verification |
| `grade` | `ENUM('A','B','C')` | `NOT NULL` | Final quality grade for the batch |
| `moisture_content_pct` | `DECIMAL(5,2)` | `NULL` | Moisture level percentage |
| `aroma_score` | `TINYINT(3)` | `NULL, CHECK(1–10)` | Aroma intensity/quality score |
| `color_score` | `TINYINT(3)` | `NULL, CHECK(1–10)` | Visual color quality score |
| `purity_pct` | `DECIMAL(5,2)` | `NULL` | Purity percentage (no foreign matter) |
| `verified_price_per_kg` | `DECIMAL(10,2)` | `NOT NULL` | Official verified market price |
| `remarks` | `TEXT` | `NULL` | PM's notes, observations, recommendations |
| `verified_at` | `TIMESTAMP` | `DEFAULT NOW()` | Date of verification |
| **Indexes** | | `PK(verification_id)`, `UNIQUE(batch_id)`, `INDEX(product_manager_id)` | |

---

### 5. `listings` — Active market board listings

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `listing_id` | `INT` | `PK, AUTO_INCREMENT` | Unique listing identifier |
| `batch_id` | `INT` | `FK → batches.batch_id, UNIQUE` | **One listing per batch** |
| `farmer_id` | `INT` | `FK → users.user_id` | Seller (farmer who owns the batch) |
| `listing_type` | `ENUM('fixed_price','auction')` | `NOT NULL` | Fixed price sale or auction |
| `price_per_kg` | `DECIMAL(10,2)` | `NOT NULL` | Starting price (auction) or fixed price |
| `min_order_kg` | `DECIMAL(10,2)` | `NULL` | Minimum purchasable quantity |
| `available_qty_kg` | `DECIMAL(10,2)` | `NOT NULL` | Remaining quantity for sale |
| `auction_start_time` | `DATETIME` | `NULL` | Auction start (only if listing_type='auction') |
| `auction_end_time` | `DATETIME` | `NULL` | Auction end (only if listing_type='auction') |
| `is_active` | `BOOLEAN` | `DEFAULT TRUE` | Whether listing is publicly visible |
| `created_at` | `TIMESTAMP` | `DEFAULT NOW()` | Date first listed |
| **Indexes** | | `PK(listing_id)`, `UNIQUE(batch_id)`, `INDEX(farmer_id)`, `INDEX(listing_type)`, `INDEX(is_active)` | |
| **Checks** | | `price_per_kg > 0`, `available_qty_kg >= 0` | |

---

### 6. `bids` — Auction bid records

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `bid_id` | `INT` | `PK, AUTO_INCREMENT` | Unique bid identifier |
| `listing_id` | `INT` | `FK → listings.listing_id` | Auction listing being bid on |
| `trader_id` | `INT` | `FK → users.user_id` | Trader who placed the bid |
| `bid_price_per_kg` | `DECIMAL(10,2)` | `NOT NULL` | Offered price per kilogram |
| `quantity_kg` | `DECIMAL(10,2)` | `NOT NULL` | Quantity the trader wants |
| `status` | `ENUM('active','accepted','rejected','outbid','expired')` | `DEFAULT 'active'` | Current bid status |
| `notes` | `TEXT` | `NULL` | Optional message with bid |
| `bid_time` | `TIMESTAMP` | `DEFAULT NOW()` | When bid was placed |
| **Indexes** | | `PK(bid_id)`, `INDEX(listing_id)`, `INDEX(trader_id)`, `INDEX(status)` | |
| **Checks** | | `bid_price_per_kg > 0`, `quantity_kg > 0` | |

---

### 7. `orders` — Confirmed trade orders (core transaction entity)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `order_id` | `INT` | `PK, AUTO_INCREMENT` | Unique order identifier |
| `order_code` | `VARCHAR(50)` | `UNIQUE, NOT NULL` | Business code, format: `ORD-YYYY-NNNN` |
| `listing_id` | `INT` | `FK → listings.listing_id` | Source listing |
| `batch_id` | `INT` | `FK → batches.batch_id` | Batch being traded |
| `buyer_id` | `INT` | `FK → users.user_id` | Trader buying (must be role='trader') |
| `seller_id` | `INT` | `FK → users.user_id` | Farmer selling (must be role='farmer') |
| `bid_id` | `INT` | `FK → bids.bid_id, NULL` | Associated bid (NULL for direct purchases) |
| `quantity_kg` | `DECIMAL(10,2)` | `NOT NULL` | Quantity in this order |
| `price_per_kg` | `DECIMAL(10,2)` | `NOT NULL` | Agreed price per kg |
| `total_amount` | `DECIMAL(12,2)` | `COMPUTED` | `quantity_kg × price_per_kg` (not stored) |
| `status` | `ENUM('pending','confirmed','processing','shipped','delivered','cancelled','disputed')` | `DEFAULT 'pending'` | Order lifecycle |
| `payment_status` | `ENUM('unpaid','partially_paid','paid','refunded')` | `DEFAULT 'unpaid'` | Payment state |
| `created_at` | `TIMESTAMP` | `DEFAULT NOW()` | Order creation timestamp |
| `updated_at` | `TIMESTAMP` | `ON UPDATE NOW()` | Last status update |
| **Indexes** | | `PK(order_id)`, `UNIQUE(order_code)`, `INDEX(buyer_id)`, `INDEX(seller_id)`, `INDEX(listing_id)`, `INDEX(status)` | |
| **Checks** | | `quantity_kg > 0`, `price_per_kg > 0` | |

---

### 8. `order_tracking` — Shipment/delivery status history

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `tracking_id` | `INT` | `PK, AUTO_INCREMENT` | Unique tracking entry |
| `order_id` | `INT` | `FK → orders.order_id` | Order being tracked |
| `status` | `ENUM('pending','confirmed','processing','shipped','delivered','cancelled')` | `NOT NULL` | Checkpoint status |
| `location` | `VARCHAR(200)` | `NULL` | Physical location at this checkpoint |
| `notes` | `TEXT` | `NULL` | Update notes (e.g., "Loaded onto truck #42") |
| `updated_by` | `INT` | `FK → users.user_id` | Who made this update |
| `tracked_at` | `TIMESTAMP` | `DEFAULT NOW()` | Timestamp of this checkpoint |
| **Indexes** | | `PK(tracking_id)`, `INDEX(order_id)`, `INDEX(updated_by)` | |

---

### 9. `payments` — Payment transaction records

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `payment_id` | `INT` | `PK, AUTO_INCREMENT` | Unique payment record |
| `order_id` | `INT` | `FK → orders.order_id` | Order being paid for |
| `payer_id` | `INT` | `FK → users.user_id` | Who made the payment |
| `amount` | `DECIMAL(12,2)` | `NOT NULL` | Amount paid |
| `payment_method` | `ENUM('bank_transfer','mobile_money','cash','escrow')` | `NOT NULL` | How payment was made |
| `transaction_ref` | `VARCHAR(100)` | `UNIQUE, NULL` | External bank or mobile money reference |
| `status` | `ENUM('pending','completed','failed','refunded')` | `DEFAULT 'pending'` | Payment outcome |
| `paid_at` | `TIMESTAMP` | `NULL` | When payment was completed |
| `created_at` | `TIMESTAMP` | `DEFAULT NOW()` | Record creation timestamp |
| **Indexes** | | `PK(payment_id)`, `INDEX(order_id)`, `INDEX(payer_id)`, `UNIQUE(transaction_ref)` | |

---

### 10. `disputes` — Conflict resolution records

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `dispute_id` | `INT` | `PK, AUTO_INCREMENT` | Unique dispute record |
| `order_id` | `INT` | `FK → orders.order_id` | Order under dispute |
| `raised_by` | `INT` | `FK → users.user_id` | User who raised the dispute |
| `against_user` | `INT` | `FK → users.user_id` | User being disputed against |
| `reason` | `TEXT` | `NOT NULL` | Description of the issue |
| `status` | `ENUM('open','under_review','resolved','closed')` | `DEFAULT 'open'` | Dispute progress |
| `resolution` | `TEXT` | `NULL` | Admin resolution notes |
| `resolved_by` | `INT` | `FK → users.user_id, NULL` | Admin who resolved it |
| `created_at` | `TIMESTAMP` | `DEFAULT NOW()` | Date dispute was raised |
| `resolved_at` | `TIMESTAMP` | `NULL` | Date dispute was closed |
| **Indexes** | | `PK(dispute_id)`, `INDEX(order_id)`, `INDEX(raised_by)`, `INDEX(status)` | |

---

### 11. `notifications` — In-app notification system

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `notification_id` | `INT` | `PK, AUTO_INCREMENT` | Unique notification |
| `user_id` | `INT` | `FK → users.user_id` | Recipient of notification |
| `type` | `ENUM('bid_received','bid_accepted','order_placed','order_shipped','payment_received','batch_verified','dispute_raised')` | `NOT NULL` | Category of notification |
| `message` | `TEXT` | `NOT NULL` | Human-readable notification body |
| `reference_id` | `INT` | `NULL` | ID of the related record |
| `reference_type` | `VARCHAR(50)` | `NULL` | e.g., 'order', 'bid', 'batch', 'dispute' |
| `is_read` | `BOOLEAN` | `DEFAULT FALSE` | Has user read this? |
| `created_at` | `TIMESTAMP` | `DEFAULT NOW()` | When notification was sent |
| **Indexes** | | `PK(notification_id)`, `INDEX(user_id)`, `INDEX(is_read)`, `INDEX(created_at)` | |

---

### 12. `reports` — Admin-generated report records

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `report_id` | `INT` | `PK, AUTO_INCREMENT` | Unique report record |
| `generated_by` | `INT` | `FK → users.user_id` | Admin who generated the report |
| `report_type` | `ENUM('trade_summary','grade_distribution','farmer_performance','trader_activity','revenue')` | `NOT NULL` | Type of report |
| `date_from` | `DATE` | `NULL` | Start of date range |
| `date_to` | `DATE` | `NULL` | End of date range |
| `parameters` | `JSON` | `NULL` | Flexible filter parameters as JSON |
| `file_path` | `VARCHAR(255)` | `NULL` | Path to exported PDF/CSV file |
| `created_at` | `TIMESTAMP` | `DEFAULT NOW()` | When report was generated |
| **Indexes** | | `PK(report_id)`, `INDEX(generated_by)`, `INDEX(report_type)`, `INDEX(created_at)` | |

---

### 13. `audit_logs` — Immutable action trail (every state change)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `log_id` | `INT` | `PK, AUTO_INCREMENT` | Unique log entry |
| `user_id` | `INT` | `FK → users.user_id, NULL` | Who performed the action (NULL for system) |
| `action` | `VARCHAR(100)` | `NOT NULL` | e.g., 'batch.verified', 'order.cancelled', 'user.registered' |
| `table_name` | `VARCHAR(50)` | `NOT NULL` | Database table that was changed |
| `record_id` | `INT` | `NOT NULL` | PK of the affected record |
| `old_value` | `JSON` | `NULL` | Full state before the change |
| `new_value` | `JSON` | `NULL` | Full state after the change |
| `ip_address` | `VARCHAR(45)` | `NULL` | Client IP (IPv4 or IPv6) |
| `logged_at` | `TIMESTAMP` | `DEFAULT NOW()` | Exact timestamp of action |
| **Indexes** | | `PK(log_id)`, `INDEX(user_id)`, `INDEX(action)`, `INDEX(table_name)`, `INDEX(record_id)`, `INDEX(logged_at)` | |

---

### 14. `conversations` — Chat thread headers

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `conversation_id` | `INT` | `PK, AUTO_INCREMENT` | Unique conversation thread |
| `batch_id` | `INT` | `FK → batches.batch_id, NULL` | Linked batch (for quality review chat) |
| `order_id` | `INT` | `FK → orders.order_id, NULL` | Linked order (for support chat) |
| `type` | `ENUM('quality_review','batch_inquiry','order_support','general')` | `NOT NULL` | Purpose of the conversation |
| `subject` | `VARCHAR(200)` | `NULL` | Optional thread title |
| `status` | `ENUM('open','archived','locked')` | `DEFAULT 'open'` | Thread state |
| `created_at` | `TIMESTAMP` | `DEFAULT NOW()` | When thread was created |
| `last_message_at` | `TIMESTAMP` | `NULL` | Denormalized for inbox sorting |
| **Indexes** | | `PK(conversation_id)`, `INDEX(batch_id)`, `INDEX(order_id)`, `INDEX(type)`, `INDEX(status)` | |

---

### 15. `conversation_participants` — Thread membership (many-to-many with attributes)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `conversation_id` | `INT` | `PK (composite), FK → conversations` | Thread the user belongs to |
| `user_id` | `INT` | `PK (composite), FK → users` | Participant in the thread |
| `role_in_chat` | `ENUM('farmer','product_manager','trader','admin')` | `NOT NULL` | Role snapshot at join time |
| `joined_at` | `TIMESTAMP` | `DEFAULT NOW()` | When user joined the thread |
| `last_read_at` | `TIMESTAMP` | `NULL` | Marks read position (replaces separate reads table) |
| `is_muted` | `BOOLEAN` | `DEFAULT FALSE` | Suppresses notification sounds only |
| `is_active` | `BOOLEAN` | `DEFAULT TRUE` | FALSE = user left the conversation |
| **Indexes** | | `PK(conversation_id, user_id)`, `INDEX(user_id)` | |
| **Note** | | Composite PK via Django `unique_together` | Django does not natively support composite PKs |

---

### 16. `messages` — Individual chat messages (high volume)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `message_id` | `BIGINT(20)` | `PK, AUTO_INCREMENT` | BIGINT for high-volume messaging |
| `conversation_id` | `INT` | `FK → conversations` | Thread this message belongs to |
| `sender_id` | `INT` | `FK → users.user_id` | Who sent the message |
| `message_type` | `ENUM('text','image','document','system')` | `DEFAULT 'text'` | Content type |
| `content` | `TEXT` | `NULL` | Message text body |
| `attachments` | `JSON` | `NULL` | `[{url, name, type, size_kb}]` |
| `is_edited` | `BOOLEAN` | `DEFAULT FALSE` | Was message edited after sending? |
| `edited_at` | `TIMESTAMP` | `NULL` | When it was last edited |
| `is_deleted` | `BOOLEAN` | `DEFAULT FALSE` | Soft delete flag (only table with soft delete) |
| `deleted_at` | `TIMESTAMP` | `NULL` | When soft-deleted |
| `sent_at` | `TIMESTAMP` | `DEFAULT NOW()` | When message was sent |
| **Indexes** | | `PK(message_id)`, `INDEX(conversation_id)`, `INDEX(sender_id)`, `INDEX(sent_at)` | |

---

## 🔗 Entity Relationship Diagram

```
┌───────────┐          ┌───────────────┐
│   users   │──────────│     farms     │
│           │1       N │               │
│           │──────────│    batches    │
│           │1       N │               │
│           │──────────│quality_verif. │
│           │1       N │               │
│           │──────────│   listings    │
│           │1       N │               │
│           │──────────│     bids      │
│           │1       N │               │
│           │──────────│    orders     │  (buyer_id)
│           │1       N │               │
│           │──────────│    orders     │  (seller_id)
│           │1       N │               │
│           │──────────│   payments    │
│           │1       N │               │
│           │──────────│   disputes    │  (raised_by)
│           │1       N │               │
│           │──────────│   disputes    │  (against_user)
│           │1       N │               │
│           │──────────│notifications  │
│           │1       N │               │
│           │──────────│  audit_logs   │
│           │1       N │               │
│           │──────────│conversation_  │
│           │M       N │participants   │
└───────────┘          └───────────────┘

┌───────────┐          ┌───────────────┐
│  batches  │1────────1│quality_verif. │
│           │1────────1│   listings    │
│           │1────────N│    orders     │
│           │1────────N│ conversations │
└───────────┘          └───────────────┘

┌───────────┐          ┌───────────────┐
│ listings  │1────────N│     bids      │
│           │1────────N│    orders     │
└───────────┘          └───────────────┘

┌───────────┐          ┌───────────────┐
│   orders  │1────────N│order_tracking │
│           │1────────N│   payments    │
│           │1────────N│   disputes    │
│           │1────────N│ conversations │
└───────────┘          └───────────────┘

┌──────────────┐       ┌───────────────┐
│conversations │1──────N│   messages    │
│              │1──────N│participants   │
└──────────────┘       └───────────────┘
```

---

## 📋 Business Rules

| # | Rule | Enforcement |
|---|------|-------------|
| 1 | **One verification per batch** | `UNIQUE` constraint on `quality_verifications.batch_id` |
| 2 | **One listing per batch** | `UNIQUE` constraint on `listings.batch_id` |
| 3 | `total_amount` is computed | `quantity_kg × price_per_kg` — use Django `GeneratedField` or `@property` |
| 4 | **Batch code format**: `CDM-YYYY-NNNN` | Auto-generated in model `save()` — NNNN zero-padded sequential |
| 5 | **Order code format**: `ORD-YYYY-NNNN` | Auto-generated in model `save()` — NNNN zero-padded sequential |
| 6 | **Only farmers can create batches** | `@role_required('farmer')` on create view |
| 7 | **Only PMs can verify batches** | `@role_required('product_manager')` on verify view |
| 8 | **Only traders can place bids** | `@role_required('trader')` on bid view |
| 9 | **Only admins resolve disputes** | `@role_required('admin')` on dispute resolve view |
| 10 | **Soft delete for messages only** | All other tables use hard delete or status-based deactivation |
| 11 | **Audit every state-changing action** | Django `post_save` signal writes to `audit_logs` |
| 12 | **PM cannot trade** | PM role excluded from trading views |
| 13 | **Auction auto-close** | System checks `auction_end_time` and auto-accepts highest bid |

---

## 🔄 Workflows

### 1. Batch Lifecycle (Complete)

```
                          ┌──────────────────┐
                          │  Farmer creates  │
                          │     Batch        │
                          │  status: pending │
                          └────────┬─────────┘
                                   │
                          ┌────────▼─────────┐
                          │  PM reviews       │
                          │  status: under_   │
                          │  review           │
                          └────────┬─────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
         ┌──────────▼──────────┐       ┌──────────▼──────────┐
         │  PM Verifies        │       │  PM Rejects         │
         │  Grade A/B/C        │       │  status: rejected   │
         │  verified_price set │       └─────────────────────┘
         │  status: verified   │
         └──────────┬──────────┘
                    │
         ┌──────────▼──────────┐
         │  Listing auto-      │
         │  created            │
         │  status: listed     │
         └──────────┬──────────┘
                    │
         ┌──────────▼──────────┐
         │  Batch Sold         │
         │  status: sold       │
         └─────────────────────┘
```

### 2. Trading Mechanisms

```
┌────────────────────────────────────────────────────────────┐
│                LISTING ACTIVE (is_active=True)              │
│  listing_type = 'fixed_price'  OR  listing_type = 'auction'│
└────────────────────────────────────────────────────────────┘
         │                                    │
         ▼                                    ▼
┌──────────────────┐              ┌──────────────────────────┐
│  Direct Buy      │              │  Bidding Window          │
│  Trader clicks   │              │  auction_start_time ≤    │
│  "Buy Now"       │              │  now ≤ auction_end_time   │
│  → Order created │              │                          │
│  (bid_id = NULL) │              │  Traders place bids      │
└────────┬─────────┘              │  → notification to       │
         │                        │    farmer                 │
         │                        └────────────┬─────────────┘
         │                                     │
         │                          ┌──────────▼──────────┐
         │                          │ Auction Expires      │
         │                          │ Highest bid wins     │
         │                          │ → Order auto-created │
         │                          │ (bid_id = winning    │
         │                          │  bid.bid_id)         │
         │                          └─────────────────────┘
         │
         ▼
┌────────────────────────────────────────────────────────────┐
│                    ORDER CREATED                           │
│  status: pending,  payment_status: unpaid                  │
└────────────────────────────────────────────────────────────┘
```

### 3. Order Fulfillment

```
                    ┌──────────┐
                    │ Pending  │
                    └────┬─────┘
                         │
                    ┌────▼─────┐
                    │Confirmed │
                    └────┬─────┘
                         │
                    ┌────▼─────┐
                    │Processing│
                    └────┬─────┘
                         │
                    ┌────▼─────┐
                    │ Shipped  │
                    └────┬─────┘
                         │
                    ┌────▼──────┐
                    │ Delivered │
                    │ ✓ Done   │
                    └──────────┘

  Any stage → Cancelled (by farmer or trader)
  If unresolved → Disputed → Admin resolves → Closed
```

### 4. Dispute Resolution

```
┌──────────┐    ┌──────────────┐    ┌──────────┐    ┌──────────┐
│  Open    │───▶│ Under Review │───▶│ Resolved │───▶│  Closed  │
└──────────┘    └──────────────┘    └──────────┘    └──────────┘
  Raised by        Admin views      Admin decides     Final state
  buyer/seller     evidence         outcome
```

### 5. Notification Triggers

```
Event                              → Notification To
─────────────────────────────────────────────────────────────
Bid received on farmer's listing   → Farmer
Bid accepted / Outbid notification  → Trader (winner/loser)
Order placed                       → Farmer
Order shipped                      → Trader (buyer)
Payment received                   → Farmer
Batch verified                     → Farmer
Dispute raised                     → Admin
```

---

## 📁 Django App Organization

```
cardetrade/
├── __init__.py
├── settings.py              # Django config, AUTH_USER_MODEL, etc.
├── urls.py                  # Root URL routing
├── wsgi.py                  # WSGI deployment entry

accounts/                    # User model, auth, role management
├── models.py                # Custom User (extends AbstractUser)
├── views.py                 # Login, Register, Profile
├── urls.py                  # /accounts/ routes
├── forms.py                 # Registration, Profile forms
├── decorators.py            # @role_required decorator
├── tests.py                 # Registration, login, role tests
├── templates/accounts/      # login.html, register.html, profile.html

farms/                       # Farm CRUD
├── models.py                # Farm model
├── views.py                 # Create, list, edit farm
├── urls.py                  # /farms/ routes
├── forms.py                 # Farm form
├── tests.py                 # Farm CRUD tests
├── templates/farms/         # create.html, detail.html

batches/                     # Batch lifecycle + verification
├── models.py                # Batch model
├── views.py                 # Create batch, verify batch
├── urls.py                  # /batches/ routes
├── forms.py                 # Batch form, Verification form
├── signals.py               # post_save → create Listing if verified
├── tests.py                 # Batch CRUD, status transitions
├── templates/batches/       # create.html, detail.html, verify.html

trading/                     # Listings, bids, buy now
├── models.py                # Listing, Bid models
├── views.py                 # Browse, detail, bid, buy
├── urls.py                  # /trading/ routes
├── forms.py                 # Bid form
├── tests.py                 # Listing creation, bid logic, auction
├── templates/trading/       # listings.html, listing_detail.html, bid_form.html

orders/                      # Orders, tracking, payments
├── models.py                # Order, OrderTracking, Payment models
├── views.py                 # Order list, detail, track
├── urls.py                  # /orders/ routes
├── forms.py                 # Tracking form
├── tests.py                 # Order flow, computed total
├── templates/orders/        # list.html, detail.html, tracking.html

disputes/                    # Dispute resolution
├── models.py                # Dispute model
├── views.py                 # Raise, list, resolve
├── urls.py                  # /disputes/ routes
├── forms.py                 # Dispute form, Resolution form
├── tests.py                 # Raise, resolve, role gating
├── templates/disputes/      # raise.html, list.html

notifications/               # In-app notification system
├── models.py                # Notification model
├── views.py                 # List, mark read
├── urls.py                  # /notifications/ routes
├── signals.py               # post_save triggers for events
├── tests.py                 # Trigger on events
├── templates/notifications/ # list.html

messaging/                   # Conversations + messages
├── models.py                # Conversation, Participant, Message
├── views.py                 # Inbox, conversation view, send
├── urls.py                  # /messaging/ routes
├── forms.py                 # Message form
├── tests.py                 # Send message, participants
├── templates/messaging/     # inbox.html, conversation.html

reports/                     # Admin reporting
├── models.py                # Report model
├── views.py                 # Dashboard, generate, export
├── urls.py                  # /reports/ routes
├── utils.py                 # Query aggregation helpers
├── tests.py                 # Report generation
├── templates/reports/       # dashboard.html

audit/                       # Audit log middleware + model
├── models.py                # AuditLog model
├── signals.py               # Generic post_save handler
├── middleware.py             # Captures IP address
├── tests.py                 # Audit log entries

templates/                   # Shared templates
├── base.html                # Bootstrap 5 nav, footer, alerts
├── includes/                # Partials (navbar, sidebar, pagination)
├── admin/                   # Django admin overrides

static/                      # Static assets
├── css/
│   └── style.css
├── js/
│   └── main.js

media/                       # User-uploaded files
├── batch_images/            # Batch photos
├── documents/               # Certificates, invoices
```

---

## 🌐 API Reference

### Authentication

| Method | Endpoint | Description | Auth | Request | Response |
|--------|----------|-------------|------|---------|----------|
| POST | `/api/auth/register/` | Register new user | Public | `{full_name, email, password, role, phone}` | `{user_id, email, role}` |
| POST | `/api/auth/login/` | Login | Public | `{email, password}` | Session cookie + `{user_id, role}` |
| POST | `/api/auth/logout/` | Logout | Session | — | 200 OK |
| GET | `/api/auth/profile/` | Get profile | Session | — | `{user_id, full_name, email, role, ...}` |
| PUT | `/api/auth/profile/` | Update profile | Session | `{full_name, phone, address, region}` | Updated profile |

### Farms

| Method | Endpoint | Description | Role |
|--------|----------|-------------|------|
| GET | `/api/farms/` | List my farms | Farmer |
| POST | `/api/farms/` | Create farm | Farmer |
| GET | `/api/farms/<id>/` | Farm detail | Farmer, Admin |
| PUT | `/api/farms/<id>/` | Update farm | Farmer (owner) |
| DELETE | `/api/farms/<id>/` | Delete farm | Farmer (owner) |

### Batches

| Method | Endpoint | Description | Role |
|--------|----------|-------------|------|
| GET | `/api/batches/` | List my batches | Farmer, PM, Admin |
| POST | `/api/batches/` | Create batch | Farmer |
| GET | `/api/batches/<id>/` | Batch detail | Farmer (owner), PM, Admin |
| PUT | `/api/batches/<id>/` | Update batch | Farmer (owner, pending only) |
| POST | `/api/batches/<id>/verify/` | Verify batch | PM |
| GET | `/api/batches/pending/` | Pending batches | PM |

### Trading / Listings

| Method | Endpoint | Description | Role |
|--------|----------|-------------|------|
| GET | `/api/listings/` | Browse active listings | All authenticated |
| GET | `/api/listings/<id>/` | Listing detail | All authenticated |
| GET | `/api/listings/my/` | My listings | Farmer |
| POST | `/api/listings/<id>/buy/` | Direct purchase | Trader |
| POST | `/api/listings/<id>/bid/` | Place bid | Trader |
| GET | `/api/bids/` | My bids | Trader |
| GET | `/api/bids/listing/<id>/` | Bids on a listing | Farmer (owner), Admin |

### Orders

| Method | Endpoint | Description | Role |
|--------|----------|-------------|------|
| GET | `/api/orders/` | My orders (buyer or seller) | Farmer, Trader |
| GET | `/api/orders/<id>/` | Order detail | Participant, Admin |
| POST | `/api/orders/<id>/cancel/` | Cancel order | Farmer, Trader (participant) |
| POST | `/api/orders/<id>/track/` | Add tracking checkpoint | Farmer, Admin |
| GET | `/api/orders/<id>/tracking/` | Get tracking history | Participant, Admin |

### Payments

| Method | Endpoint | Description | Role |
|--------|----------|-------------|------|
| POST | `/api/orders/<id>/pay/` | Record payment | Trader (buyer) |
| GET | `/api/orders/<id>/payments/` | Payment history | Participant, Admin |

### Disputes

| Method | Endpoint | Description | Role |
|--------|----------|-------------|------|
| POST | `/api/disputes/` | Raise dispute | Farmer, Trader |
| GET | `/api/disputes/` | List disputes (my or all) | Farmer, Trader, Admin |
| GET | `/api/disputes/<id>/` | Dispute detail | Participant, Admin |
| POST | `/api/disputes/<id>/resolve/` | Resolve dispute | Admin |

### Notifications

| Method | Endpoint | Description | Role |
|--------|----------|-------------|------|
| GET | `/api/notifications/` | My notifications | All authenticated |
| PUT | `/api/notifications/<id>/read/` | Mark as read | Recipient |
| PUT | `/api/notifications/read-all/` | Mark all as read | All authenticated |

### Messaging

| Method | Endpoint | Description | Role |
|--------|----------|-------------|------|
| GET | `/api/conversations/` | My conversations | All authenticated |
| POST | `/api/conversations/` | Create conversation | All authenticated |
| GET | `/api/conversations/<id>/` | Conversation detail (with messages) | Participant |
| POST | `/api/conversations/<id>/messages/` | Send message | Participant |
| PUT | `/api/conversations/<id>/read/` | Mark as read | Participant |

### Reports (Admin)

| Method | Endpoint | Description | Role |
|--------|----------|-------------|------|
| GET | `/api/reports/trade-summary/` | Trade volume, value, trends | Admin |
| GET | `/api/reports/grade-distribution/` | Grade A/B/C breakdown | Admin |
| GET | `/api/reports/farmer-performance/` | Top farmers by volume/value | Admin |
| GET | `/api/reports/trader-activity/` | Trader purchase activity | Admin |
| GET | `/api/reports/revenue/` | Platform revenue report | Admin |

### Audit Logs (Admin)

| Method | Endpoint | Description | Role |
|--------|----------|-------------|------|
| GET | `/api/audit-logs/` | Browse all logs (paginated) | Admin |
| GET | `/api/audit-logs/<id>/` | Single log detail | Admin |
| GET | `/api/audit-logs/table/<table_name>/` | Logs for specific table | Admin |

### Error Response Format

```json
{
    "error": true,
    "code": "VALIDATION_ERROR",
    "message": "Human-readable description",
    "details": {
        "field_name": ["Error message for this field"]
    }
}
```

### Pagination Format

```json
{
    "count": 142,
    "next": "/api/listings/?page=3",
    "previous": "/api/listings/?page=1",
    "results": [...]
}
```

---

## 🧪 Testing Strategy

### App-by-App Test Coverage

| App | Test Focus |
|-----|------------|
| **accounts** | User registration with each role, login/logout, profile update, role enforcement decorator |
| **farms** | Create farm, list farms (owner only), update farm (owner only), delete farm |
| **batches** | Create batch (farmer only), status transitions (pending→under_review→verified→listed→sold), auto code generation |
| **trading** | Auto-create listing after verification, browse active listings, direct buy (trader only), bid placement (trader only), auction auto-close logic |
| **orders** | Order creation from direct buy, order creation from winning bid, computed `total_amount`, status flow, cancel order (participant only) |
| **disputes** | Raise dispute (participant only), resolve dispute (admin only), status transitions |
| **notifications** | Triggers on each event type, mark as read, mark all as read |
| **messaging** | Create conversation, send message, participant management, last_message_at update, soft delete |
| **reports** | Generate each report type, date range filtering, empty data handling |
| **audit** | Log entry on every state change, IP capture, old/new value JSON capture |

### Example Test

```python
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()

class BatchVerificationWorkflowTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.farmer = User.objects.create_user(
            username='farmer1', email='farmer@test.com',
            password='test123', role='farmer'
        )
        cls.pm = User.objects.create_user(
            username='pm1', email='pm@test.com',
            password='test123', role='product_manager',
            is_staff=True
        )

    def test_batch_created_as_pending(self):
        self.client.login(username='farmer1', password='test123')
        response = self.client.post(reverse('batches:create'), {
            'quantity_kg': 100.50,
            'harvest_date': '2026-03-15',
            'estimated_price_per_kg': 45.00,
        })
        self.assertEqual(response.status_code, 302)
        batch = Batch.objects.last()
        self.assertEqual(batch.status, Batch.BatchStatus.PENDING)
        self.assertEqual(batch.farmer, self.farmer)

    def test_pm_can_verify_batch(self):
        batch = Batch.objects.create(
            farmer=self.farmer, quantity_kg=100, harvest_date='2026-03-15',
            estimated_price_per_kg=45, status='pending'
        )
        self.client.login(username='pm1', password='test123')
        response = self.client.post(
            reverse('batches:verify', args=[batch.id]),
            {'grade': 'A', 'verified_price_per_kg': 50.00}
        )
        batch.refresh_from_db()
        self.assertEqual(batch.status, 'verified')

    def test_verification_creates_listing(self):
        batch = Batch.objects.create(
            farmer=self.farmer, quantity_kg=100, harvest_date='2026-03-15',
            estimated_price_per_kg=45, status='verified'
        )
        self.assertTrue(Listing.objects.filter(batch=batch).exists())
```

### Running Tests

```bash
# All tests
python manage.py test

# Specific app
python manage.py test accounts

# Specific test class
python manage.py test batches.tests.BatchVerificationWorkflowTest

# With coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
coverage html     # Open htmlcov/index.html
```

---

## 🚀 Setup Guide

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- Virtual environment (recommended)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-org/cardetrade.git
cd cardetrade

# 2. Create and activate virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up the database
python manage.py makemigrations
python manage.py migrate

# 5. Create superuser (admin)
python manage.py createsuperuser

# 6. (Optional) Load sample data
python manage.py loaddata sample_data.json

# 7. Run development server
python manage.py runserver

# 8. Open in browser
# http://127.0.0.1:8000/
```

### Requirements File (`requirements.txt`)

```
Django>=5.0,<5.2
python-decouple==3.8
Pillow==10.*
django-crispy-forms==2.*
crispy-bootstrap5==2024.*
coverage==7.*
```

---

## 🚢 Deployment

### Production Checklist

- [ ] Set `DEBUG = False` in `settings.py`
- [ ] Generate strong `SECRET_KEY` (use `python-decouple` or env var)
- [ ] Switch database to PostgreSQL
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Set up HTTPS (certbot / nginx reverse proxy)
- [ ] Configure static files serving (`python manage.py collectstatic`)
- [ ] Configure media files serving (S3 or nginx)
- [ ] Set up proper logging
- [ ] Run migrations
- [ ] Create admin account
- [ ] Test all workflows in production mode

### Using Gunicorn + Nginx (Linux)

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn cardetrade.wsgi:application --workers=4 --bind=0.0.0.0:8000

# Nginx config example
# server {
#     listen 80;
#     server_name yourdomain.com;
#     location /static/ { alias /path/to/static/; }
#     location /media/ { alias /path/to/media/; }
#     location / { proxy_pass http://127.0.0.1:8000; }
# }
```

---

## 🔒 Security Considerations

| Concern | Mitigation |
|---------|------------|
| Password storage | Django PBKDF2 (default) — never store plain text |
| Role escalation | `@role_required` decorator on all protected views |
| CSRF | Django CSRF middleware (include `{% csrf_token %}` in all forms) |
| XSS | Django template auto-escaping |
| SQL injection | Django ORM (parameterized queries) — never raw SQL |
| Sensitive data exposure | No secrets in code, use `.env` file |
| Session hijacking | Secure cookie flags, HTTPS in production |
| Rate limiting | Django `django-axes` or custom middleware |
| Audit trail | Every mutation logged in `audit_logs` with user & IP |
| File upload validation | Check file type, size limit, scan for malware |

---

## 🤝 Contributing

### Code Conventions

- **Python**: Follow PEP 8 (use `black` formatter, `ruff` linter)
- **Django**: Follow Django's coding style guide
- **JavaScript**: ES6+ syntax, semicolons, 2-space indent
- **Templates**: Bootstrap 5 classes, no inline CSS, `{% load static %}`
- **Git commits**: `type(scope): description` e.g., `feat(batches): add verification workflow`

### Pull Request Process

1. Create branch: `feature/description` or `fix/description`
2. Write tests for new functionality
3. Run `python manage.py test` — all must pass
4. Run `ruff check .` — no lint errors
5. Submit PR with description of changes
6. Request review from maintainer

---

## 🗺 Roadmap

| Phase | Features | Status |
|-------|----------|--------|
| **Phase 1** | User auth, role management, farm CRUD | ✅ Done |
| **Phase 2** | Batch creation, quality verification workflow | ✅ Done |
| **Phase 3** | Listings, direct buy, bidding mechanism | ✅ Done |
| **Phase 4** | Order management, tracking, payments | ✅ Done |
| **Phase 5** | Dispute resolution, notifications | ✅ Done |
| **Phase 6** | In-app messaging system | ✅ Done |
| **Phase 7** | Admin reports, audit log | ✅ Done |
| **Phase 8** | PDF/CSV report export | 🔜 Planned |
| **Phase 9** | Real-time notifications (WebSocket) | 🔜 Planned |
| **Phase 10** | Mobile app (React Native) | 💡 Future |
| **Phase 11** | ML-based price prediction | 💡 Future |

---

## 📄 License

This project is proprietary. All rights reserved.

---

*Built with Django • Designed for Cardamom Farmers, Traders, and Markets.*
