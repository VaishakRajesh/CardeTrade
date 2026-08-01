# CardeTrade — Cardamom Trading Platform

## Project Status Report & Technical Documentation

---

| | |
|---|---|
| **Project Name** | CardeTrade — Cardamom Trading Platform |
| **Project Type** | Django 5.x Web Application (server-rendered, Bootstrap 5) |
| **Domain** | Agri-Tech / Commodity Marketplace (Indian Cardamom) |
| **Python** | 3.11+ |
| **Database** | SQLite (development) / PostgreSQL (production target) |
| **Authentication** | Custom `AbstractUser` with email login + role-based access control |
| **Report Date** | July 31, 2026 |
| **Development Stage** | Core MVP implemented — pre-demo / testing phase |

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Project Aim & Objectives](#2-project-aim--objectives)
3. [Technology Stack](#3-technology-stack)
4. [System Architecture](#4-system-architecture)
5. [Folder Structure](#5-folder-structure)
6. [Database Models (15 Tables)](#6-database-models-15-tables)
7. [URL Routing Structure](#7-url-routing-structure)
8. [Role-Based Features](#8-role-based-features)
9. [Business Workflows](#9-business-workflows)
10. [Current Development State](#10-current-development-state)
11. [Known Issues & Observations](#11-known-issues--observations)
12. [Setup & Installation](#12-setup--installation)
13. [Environment Variables](#13-environment-variables)
14. [Testing Status](#14-testing-status)
15. [Roadmap & Next Steps](#15-roadmap--next-steps)
16. [Appendix: Audit Logging & AI Chatbot](#16-appendix-audit-logging--ai-chatbot)

---

## 1. Executive Summary

CardeTrade is a **multi-role digital marketplace** that connects Indian cardamom farmers directly with verified traders, eliminating middlemen. The platform implements a complete trading lifecycle:

```
Farmer creates batch → Product Manager verifies quality → 
Batch auto-listed as auction → Traders bid → Farmer accepts bid → 
Order created → Trader pays → Order fulfilled
```

The system supports **4 user roles** (Farmer, Trader, Product Manager, Admin), **15 database tables**, a **Django admin panel**, an **AI chatbot assistant** (OpenRouter-powered with live database context), and a full **auction + order + payment + dispute** workflow.

**Current state:** The core MVP is fully implemented and the Django system check passes with zero issues. The database is migrated (24 tables created) but contains only seed data (1 admin user) — no real business records yet. This is the **pre-demo stage**: the code is feature-complete for a first demonstration, but test suites are empty and several known UX issues (documented in Section 11) should be fixed before public deployment.

---

## 2. Project Aim & Objectives

### 2.1 Primary Aim

Build a transparent, verified, and fair digital trading platform for cardamom that connects **farmers → quality verifiers → traders** with full traceability from harvest to delivery.

### 2.2 Core Objectives

| # | Objective | How It Is Achieved |
|---|-----------|--------------------|
| 1 | **Fair pricing** | Product Managers set verified benchmark prices per batch based on quality grade (A/B/C) |
| 2 | **Quality assurance** | Every batch must pass PM inspection (moisture %, aroma score, color score, purity %) before listing |
| 3 | **Zero middlemen** | Farmers sell directly to traders through the auction system |
| 4 | **Trust & accountability** | Verification documents, role enforcement, audit logging (R6 compliance rule) |
| 5 | **Dispute resolution** | Built-in dispute lifecycle handled by admins |
| 6 | **Market intelligence** | AI chatbot answers questions using live database context (prices, grades, regions) |
| 7 | **Traceability** | Unique batch codes (`CDM-YYYY-NNNN`) and order codes (`ORD-YYYY-NNNN`) track every unit |

---

## 3. Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Backend | **Django 5.2** (`django>=5.2,<5.3`) | Web framework, ORM, auth, admin |
| Language | Python 3.11+ | Application language |
| Database | SQLite (dev) → PostgreSQL (prod target) | Data persistence |
| Frontend | **Bootstrap 5.3.3** + Bootstrap Icons | UI framework (CDN) |
| Templates | Django Template Language (server-rendered, no SPA) | HTML rendering |
| Forms | `django-crispy-forms` + `crispy-bootstrap5` | Bootstrap form rendering |
| Images | Pillow 10+ | ImageField processing |
| Config | `python-decouple` (`.env` file) | Secret/config management |
| AI Chatbot | **OpenRouter API** (`requests`), default model `google/gemma-2-9b-it` | AI assistant with DB context |
| Advanced DB | `GeneratedField` (Django 5+) | Computed `total_amount` column |

### Key Design Decisions

1. **Custom User model** (`accounts.User`) with `USERNAME_FIELD = 'email'` — users log in with email, not username.
2. **Role-based access control** via `@role_required(...)` decorators (not Django groups) — simple and explicit.
3. **`GeneratedField` for `total_amount`** — the order total is a database-computed column (`quantity_kg × price_per_kg`), never stored as a regular field (avoids inconsistency).
4. **Signals for business rules** — a batch verification automatically creates an auction listing (no manual steps).
5. **Thread-local audit middleware** — captures the requesting user/IP for every request to support audit logging.

---

## 4. System Architecture

### 4.1 High-Level Architecture Diagram

```
┌────────────────────────────────────────────────────────────┐
│                     Django Web Server                       │
│                   (django.contrib.admin)                    │
├────────────────────────────────────────────────────────────┤
│                                                            │
│   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐     │
│   │ accounts │ │  farmer  │ │  trader  │ │    pm    │     │
│   │ auth,msg,│ │ farms &  │ │ listings,│ │ quality  │     │
│   │ disputes │ │ batches  │ │ bids,    │ │ verifica-│     │
│   │          │ │          │ │ orders   │ │ tion     │     │
│   └──────────┘ └──────────┘ └──────────┘ └──────────┘     │
│   ┌──────────┐ ┌──────────┐                                 │
│   │  panel   │ │   chat   │──▶ OpenRouter AI (external)    │
│   │ admin    │ │ chatbot  │                                 │
│   │ console  │ └──────────┘                                 │
│   └──────────┘                                              │
│                                                            │
├────────────────────────────────────────────────────────────┤
│   SQLite / PostgreSQL            Media (uploads)          │
│   15 application tables          batch images, docs        │
└────────────────────────────────────────────────────────────┘
```

### 4.2 Role → Permission Mapping

| Role | `User.role` value | `is_staff` | `is_superuser` | Auto-verified |
|------|-------------------|------------|----------------|---------------|
| Farmer | `farmer` | No | No | No (requires admin review) |
| Trader | `trader` | No | No | **Yes** (can trade immediately) |
| Product Manager | `product_manager` | **Yes** | No | No (account starts inactive, needs admin approval) |
| Admin | `admin` | **Yes** | **Yes** | Yes |

The `User.save()` method (accounts/models.py:35) automatically syncs these flags from the role.

### 4.3 Middleware Pipeline

```
Security → Session → Common → CSRF → Authentication → Messages → 
Clickjacking → AuditMiddleware (custom: captures user + IP per thread)
```

---

## 5. Folder Structure

```
CardeTrade/
├── README.md                        # Quick start guide + admin credentials
├── AGENTS.md                        # AI-agent instruction manual (dev rules)
├── requirements.txt                 # Python dependencies
├── .env                             # Environment variables (NOT committed)
├── .gitignore                       # Git ignore rules
│
├── manage.py                        # Django management entry point
│
├── cardetrade/                      # PROJECT CONFIGURATION PACKAGE
│   ├── __init__.py
│   ├── settings.py                  # All Django settings (auth, DB, apps, chatbot)
│   ├── urls.py                      # Root URL routing (all apps included)
│   ├── wsgi.py                      # WSGI deployment entry
│   └── asgi.py                      # ASGI entry (async support)
│
├── accounts/                        # AUTH + SHARED CORE APP
│   ├── models.py                    # User, Conversation, ConversationParticipant,
│   │                                #   Message, Dispute, Report, AuditLog
│   ├── views.py                     # Home, Register, Login, Logout, Profile,
│   │                                #   DashboardRedirect, Conversations, Disputes
│   ├── forms.py                     # RegistrationForm, LoginForm, UserProfileForm
│   ├── decorators.py                # @role_required + role shortcuts
│   ├── middleware.py                # AuditMiddleware (thread-local user/IP)
│   ├── signals.py                   # Message → conversation timestamp update
│   ├── admin.py                     # Custom UserAdmin
│   ├── urls.py                      # /accounts/ routes
│   ├── apps.py                      # AppConfig (loads signals in ready())
│   ├── migrations/                  # 0001, 0002 (user model + all shared tables)
│   └── templates/accounts/
│       ├── login.html               # Email + password login
│       ├── register.html            # Role-aware registration
│       ├── profile.html             # Profile editing
│       ├── dashboard/home.html      # Landing page (hero + stats)
│       ├── messaging/               # conversation_list / detail / create
│       └── disputes/                # list / create
│
├── farmer/                          # FARMER APP
│   ├── models.py                    # Farm, Batch
│   ├── views.py                     # Dashboard, Farm CRUD, Batch CRUD,
│   │                                #   MyBids, AcceptBid, Orders
│   ├── signals.py                   # Verified batch → auto-create Listing
│   ├── admin.py                     # BatchAdmin, FarmAdmin
│   ├── urls.py                      # /farmer/ routes
│   ├── apps.py                      # AppConfig
│   ├── migrations/                  # 0001_initial
│   └── templates/farmer/
│       ├── dashboard.html
│       ├── farms/                   # list, create
│       ├── batches/                 # list, detail, create
│       ├── trading/my_bids.html
│       └── orders/list.html
│
├── trader/                          # TRADER / MARKETPLACE APP
│   ├── models.py                    # Listing, Bid, Order, OrderTracking, Payment
│   ├── views.py                     # Dashboard, Listing list/detail, PlaceBid,
│   │                                #   MyBids, Order list/detail, MakePayment
│   ├── admin.py                     # ListingAdmin, BidAdmin, OrderAdmin, PaymentAdmin
│   ├── urls.py                      # /trader/ routes
│   ├── apps.py                      # AppConfig
│   ├── migrations/                  # 0001_initial
│   └── templates/trader/
│       ├── dashboard.html
│       ├── trading/                 # listing_list, listing_detail, place_bid, my_bids
│       └── orders/                  # list, detail, pay
│
├── pm/                              # PRODUCT MANAGER APP
│   ├── models.py                    # QualityVerification
│   ├── views.py                     # Dashboard, BatchVerifyView (dynamic form)
│   ├── admin.py                     # QualityVerificationAdmin
│   ├── urls.py                      # /pm/ routes
│   ├── apps.py
│   ├── migrations/                  # 0001_initial
│   └── templates/pm/
│       ├── dashboard.html           # Pending + under-review batches
│       └── batches/verify.html      # Grade/price verification form
│
├── panel/                           # ADMIN CONSOLE APP (no models)
│   ├── views.py                     # AdminDashboard, PendingPMList,
│   │                                #   AcceptPM, RejectPM, DisputeResolve
│   ├── urls.py                      # /panel/ routes
│   ├── admin.py
│   ├── apps.py
│   ├── migrations/                  # (empty)
│   └── templates/panel/
│       ├── dashboard.html           # Platform-wide KPIs
│       ├── pm_pending.html          # PM account approval queue
│       └── disputes/resolve.html    # Dispute resolution form
│
├── chat/                            # AI CHATBOT APP (no models)
│   ├── views.py                     # ChatBotAPIView (JSON POST endpoint)
│   ├── urls.py                      # /chat/api/
│   ├── services/
│   │   ├── __init__.py
│   │   └── chatbot.py               # SYSTEM_PROMPT, get_db_context(),
│   │                                #   call_openrouter(), format_response()
│   └── templates/                   # (chatbot widget lives in shared templates)
│
├── templates/                       # SHARED TEMPLATES
│   ├── base.html                    # Bootstrap 5 skeleton: navbar, alerts,
│   │                                #   hero, footer, chatbot widget, scripts
│   └── includes/
│       ├── navbar.html              # Role-aware nav links + user dropdown
│       ├── alerts.html              # Django messages as Bootstrap alerts
│       ├── footer.html
│       └── chatbot_widget.html      # Floating AI chat bubble
│
├── static/                          # STATIC ASSETS
│   ├── css/style.css                # Full custom design system (~2600 lines)
│   └── js/
│       ├── main.js                  # Preloader, counters, alerts, parallax, ripple…
│       └── chatbot.js               # Chat widget logic (fetch to /chat/api/)
│
├── media/                           # USER UPLOADS (gitignored)
│   ├── batch_images/                # Batch photos
│   └── documents/                   # Verification docs, farm certifications
│
└── db.sqlite3                       # Development database (gitignored)
```

---

## 6. Database Models (15 Tables)

### 6.1 `accounts` app (7 tables)

#### User — Custom authentication model
| Field | Type | Notes |
|-------|------|-------|
| `USERNAME_FIELD` | — | `email` (login by email) |
| `REQUIRED_FIELDS` | — | `['username']` |
| `email` | EmailField, **unique** | Login identifier |
| `role` | CharField(20), TextChoices | farmer / trader / product_manager / admin |
| `phone` | CharField(20) | Optional |
| `address` | TextField | Optional |
| `region` | CharField(100) | Optional |
| `is_verified` | BooleanField | Trader = True; Farmer/PM = False until approved |
| `verification_doc` | FileField | Business license / ID / certification |
| *inherited* | username, password, first/last name, is_active, is_staff, is_superuser, date_joined, last_login | From AbstractUser |

**Key logic:** `save()` auto-sets `is_staff` / `is_superuser` / `is_verified` from `role` (see 4.2).

#### Conversation — Messaging thread
`type` (quality_review / batch_inquiry / order_support / general), `status` (open / archived / locked), optional `batch` FK, optional `order` FK, `subject`, `last_message_at`.

#### ConversationParticipant — Link user ↔ conversation
`conversation` FK + `user` FK with `unique_together`, `role_in_chat`, `last_read_at`, `is_muted`, `is_active`.

#### Message — Chat message
`conversation` FK, `sender` FK (SET_NULL), `message_type` (text/image/document/system), `content`, `attachments` (JSON), `is_edited`, **soft-delete fields** (`is_deleted`, `deleted_at` — the only soft-delete table by design rule R5).

#### Dispute — Order dispute lifecycle
`order` FK, `raised_by` FK, `against_user` FK, `reason`, `status` (open → under_review → resolved → closed), `resolution`, `resolved_by`, `resolved_at`.

#### Report — Generated analytics records
`generated_by` FK, `report_type` (trade_summary, grade_distribution, farmer_performance, trader_activity, revenue), `date_from/date_to`, `parameters` (JSON), `file_path`.

#### AuditLog — Compliance audit trail
`user` FK (SET_NULL), `action`, `table_name`, `record_id`, `old_value`/`new_value` (JSON), `ip_address`, `logged_at`. Indexed on `(table_name, record_id)`, `action`, `user`.

### 6.2 `farmer` app (2 tables)

#### Farm
`farmer` FK (limited to role=farmers), `farm_name`, `location`, `region`, `total_area_acres`, `certification` (FileField), `created_at`.

#### Batch
| Field | Type | Notes |
|-------|------|-------|
| `batch_code` | CharField(50) **unique, editable=False** | Auto-generated `CDM-YYYY-NNNN` in `save()` |
| `farmer` | FK | Limited to role=farmers |
| `farm` | FK (SET_NULL, nullable) | Optional farm link |
| `quantity_kg` | Decimal(10,2) | |
| `image` | ImageField | Uploaded to `batch_images/` |
| `harvest_date` | DateField | |
| `description` | TextField | |
| `estimated_price_per_kg` | Decimal(10,2) | Farmer's expectation |
| `status` | CharField(20) | pending → under_review → verified → listed → sold / rejected |

### 6.3 `pm` app (1 table)

#### QualityVerification
OneToOne with Batch. Fields: `product_manager` FK, `grade` (A/B/C), `moisture_content_pct`, `aroma_score` (1-10), `color_score` (1-10), `purity_pct`, `verified_price_per_kg`, `remarks`, `verified_at`.

### 6.4 `trader` app (5 tables)

#### Listing — Auction marketplace item
OneToOne with Batch. `farmer` FK, `listing_type` (**only `auction` is active in the current code**), `price_per_kg` (starting price), `min_order_kg`, `available_qty_kg`, `auction_start_time` / `auction_end_time` (auto: now + 7 days), `is_active`.
Helper properties: `current_highest_bid`, `bid_count` (cached), `time_remaining`.

#### Bid
`listing` FK, `trader` FK (role-limited), `bid_price_per_kg`, `quantity_kg`, `status` (active / accepted / rejected / outbid / expired), `notes`, `bid_time`.

#### Order
| Field | Type | Notes |
|-------|------|-------|
| `order_code` | unique, editable=False | Auto `ORD-YYYY-NNNN` |
| `listing` / `batch` | FK (SET_NULL) | Origin of the purchase |
| `buyer` | FK | role=trader |
| `seller` | FK | role=farmer |
| `bid` | FK (SET_NULL, nullable) | The winning bid |
| `quantity_kg` | Decimal(10,2) | |
| `price_per_kg` | Decimal(10,2) | Accepted bid price |
| **`total_amount`** | **`GeneratedField`** | **DB-computed: `quantity_kg × price_per_kg`** (Django 5 feature, persisted) |
| `status` | pending → confirmed → processing → shipped → delivered / cancelled / disputed | |
| `payment_status` | unpaid / partially_paid / paid / refunded | |

#### OrderTracking — Fulfillment history
`order` FK, `status`, `location`, `notes`, `updated_by` FK, `tracked_at`. (Model exists; no UI flow writes tracking entries yet.)

#### Payment
`order` FK, `payer` FK, `amount`, `payment_method` (bank_transfer / mobile_money / cash / escrow), `transaction_ref` (unique), `status` (pending / completed / failed / refunded), `paid_at`, `created_at`. (Current flow creates a **mock completed payment** — no real payment gateway.)

### 6.5 Entity Relationship Summary

```
User 1───* Farm  1───* Batch 1───1 QualityVerification
                          │
Batch 1───1 Listing 1───* Bid
                    │       │
                    │       └─── (accepted bid → Order)
                    └───* Order 1───* Payment
                             │
                             ├───* OrderTracking
                             └───* Dispute
User 1───* Conversation ──* ConversationParticipant 1───* Message
```

---

## 7. URL Routing Structure

### Root (`cardetrade/urls.py`)

| URL | Target |
|-----|--------|
| `/` | Redirect → `accounts:home` |
| `/admin/` | Django admin |
| `/accounts/` | accounts app |
| `/farmer/` | farmer app |
| `/trader/` | trader app |
| `/pm/` | pm app |
| `/panel/` | panel app |
| `/chat/api/` | chatbot API |

### `accounts/` — 12 routes
`/` (home), `register/`, `login/`, `logout/`, `profile/`, `dashboard/`, `conversations/`, `conversations/<pk>/`, `conversations/create/<batch_pk>/`, `disputes/`, `disputes/create/<order_pk>/`

### `farmer/` — 9 routes
`dashboard/`, `farms/`, `farms/create/`, `batches/`, `batches/create/`, `batches/<pk>/`, `bids/`, `bids/<pk>/accept/`, `orders/`

### `trader/` — 8 routes
`dashboard/`, `listings/`, `listings/<pk>/`, `listings/<pk>/bid/`, `bids/`, `orders/`, `orders/<pk>/`, `orders/<pk>/pay/`

### `pm/` — 2 routes
`dashboard/`, `batches/<pk>/verify/`

### `panel/` — 5 routes
`dashboard/`, `pm/pending/`, `pm/<pk>/accept/`, `pm/<pk>/reject/`, `disputes/<pk>/resolve/`

### `chat/` — 1 route
`chat/api/` (POST JSON `{"message": "..."}` → `{"response": "..."}`)

---

## 8. Role-Based Features

### 🌾 Farmer
- Register farm (name, location, region, area, certification file)
- Create batch (farm, quantity, harvest date, description, estimated price, photo) → status `pending`
- View own batches / farms / received bids / orders
- **Accept a bid** (atomic operation): other active bids → `outbid`, winning bid → `accepted`, Order auto-created, listing quantity decremented, batch → `sold` when quantity exhausted
- Track order status as seller

### 🛒 Trader
- Browse active auction listings (annotated with highest bid + bid count)
- Place bids (price per kg, quantity, notes) — blocked on inactive listings
- View own bids and orders
- **Pay for an order** (mock payment: method + optional transaction ref → Payment record `completed`, order → `paid`)

### 🔬 Product Manager
- Dashboard: pending + under-review batches, own verification history
- **Verify a batch**: grade A/B/C, moisture %, aroma 1-10, color 1-10, purity %, verified price → Batch → `verified` → **signal auto-creates an Auction listing** (7-day duration) → batch → `listed`
- Cannot re-verify an already-verified batch (OneToOne guard)

### 🛡 Admin
- Platform dashboard: user counts, batch/order totals, revenue (sum of non-cancelled order totals), open disputes
- **Approve/reject PM accounts** (PM registers inactive; admin flips `is_active`)
- **Resolve disputes** (sets resolution text, status, resolved_by, resolved_at)
- Full Django admin (`/admin/`) for direct data management

### 🤖 All authenticated users
- AI chatbot widget (floating) with role-aware, database-context answers
- Messaging conversations (batch inquiries auto-add the batch farmer + a PM)
- Raise disputes on orders they participate in

---

## 9. Business Workflows

### 9.1 Batch Lifecycle
```
farmer:  create batch ──▶ PENDING
pm:      start review ──▶ UNDER_REVIEW
pm:      verify (grade+price) ──▶ VERIFIED
signal:  auto-create auction listing ──▶ LISTED
trader:  bid → farmer accepts → order → quantity 0 ──▶ SOLD
pm:      reject ──▶ REJECTED
```

### 9.2 Auction-to-Order Flow (implementation details)
1. Trader opens `trader:listing_detail`, clicks Bid, submits form (`trader:place_bid`).
2. Farmer sees bids in `farmer:my_bids`, clicks **Accept**.
3. `AcceptBidView.post` runs inside `transaction.atomic()` + `select_for_update()`:
   - All other active bids on the listing → `outbid`
   - Selected bid → `accepted`
   - `Order` created (buyer = bid.trader, seller = listing.farmer, price = bid price, total = GeneratedField)
   - `listing.available_qty_kg` reduced; at ≤ 0 → listing deactivated + batch → `sold`
4. Trader pays via `trader:order_pay` → mock `Payment` (completed) → order `payment_status` = `paid`.

### 9.3 Dispute Lifecycle
```
open ──▶ under_review ──▶ resolved ──▶ closed
(raised by buyer/seller) (admin work)  (final)
```
Creating a dispute also flips the order status to `disputed`.

### 9.4 PM Account Approval
```
PM registers (is_active=False, is_staff=True)
  → Admin: panel:pm_pending_list
  → Accept  → is_active=True, is_verified=True
  → Reject  → stays inactive
```

### 9.5 Signal-Driven Automation (farmer/signals.py)
`post_save` on Batch: when status becomes `verified` and a QualityVerification exists → `get_or_create` an auction `Listing` (start = now, end = now + 7 days, price = verified price) → batch status set to `listed`.

---

## 10. Current Development State

### 10.1 Verified Status (tested on July 31, 2026)

| Check | Result |
|-------|--------|
| `python manage.py check` | ✅ **No issues (0 silenced)** |
| Migrations applied | ✅ 24 database tables created |
| Valid login (email + password) | ✅ 302 → role dashboard |
| Registration (all roles) | ✅ Auto-login + role flags |
| Dashboard redirect per role | ✅ farmer / trader / pm / admin |
| System check of all apps | ✅ accounts, farmer, trader, pm, panel, chat all registered |

### 10.2 Database Snapshot (current records)

| Table | Records |
|-------|---------|
| Users | 1 (admin only: `admin@cardetrade.in`) |
| Farms / Batches / Listings / Bids / Orders / Payments / Verifications | 0 each |
| Disputes / Conversations / Messages | 0 each |

> **Interpretation:** The platform is fully built but **empty of demo data**. The immediate next step for a demo is to register test users (farmer, trader, PM), create a farm → batch → verify → bid → order chain, and populate the marketplace.

### 10.3 Implemented (MVP Complete)

- ✅ Email-based auth, registration with roles + document upload
- ✅ Role enforcement decorators on all role-specific views
- ✅ Farm & batch CRUD for farmers
- ✅ PM quality verification with auto-listing signal
- ✅ Auction listing browse + bid placement
- ✅ Bid acceptance with atomic order creation
- ✅ Mock payment flow
- ✅ Order lists per role + order detail
- ✅ Admin console: KPIs, PM approval, dispute resolution
- ✅ Messaging (conversations per batch, participants, read tracking, soft delete)
- ✅ AI chatbot with DB context + OpenRouter integration
- ✅ Custom premium UI (Bootstrap 5 + custom CSS/JS design system)
- ✅ Django admin registered for all apps

### 10.4 Not Yet Implemented / Partial

| Feature | Status |
|---------|--------|
| Fixed-price (direct buy) listings | Model supports it, **code creates auctions only** |
| Real payment gateway (Razorpay/Stripe/UPI) | Mock only |
| Order tracking UI (shipping updates) | Model exists, no workflow |
| Report generation module | Model exists, no views |
| Email notifications | Not present |
| Test suite | Empty across all apps (`# Create your tests here.`) |
| Audit log write path | Model + middleware exist; full auto-logging receiver not connected |
| Production deployment config (nginx, gunicorn, PostgreSQL) | Not present |
| `.env` real secrets | Defaults in place |

---

## 11. Known Issues & Observations

These are factual findings from code review and runtime testing. **Item 1 is the "login error" issue that prompted this report.**

### 11.1 ⚠️ Login fails silently — error message invisible (HIGH)
- **Location:** `accounts/templates/accounts/login.html:36-44`
- **Cause:** Django's `AuthenticationForm` puts invalid-credential errors into **`form.non_field_errors`**, but the template only renders `{{ field.errors.0 }}` per field and never renders `{{ form.non_field_errors }}`. Verified by runtime test: after a failed login, `non_field_errors` is absent from the rendered HTML.
- **Effect:** Users see the form simply reload with no error text (the generic alert banner auto-dismisses after 5 s).
- **Fix:** insert after `{% csrf_token %}`:
  ```html
  {% if form.non_field_errors %}
  <div class="alert alert-danger py-2 small">
      {% for error in form.non_field_errors %}{{ error }}{% endfor %}
  </div>
  {% endif %}
  ```

### 11.2 ⚠️ Email login is case-sensitive (MEDIUM)
- `USERNAME_FIELD = 'email'` (accounts/models.py:16) uses exact DB matching. Registering `John@Test.com` and logging in `john@test.com` fails silently.
- **Fix (recommended):** lowercase email in `User.save()` and in `LoginForm.clean_username()`.

### 11.3 🟡 Registration doc requirement can block farmers
- `RegistrationForm.clean_verification_doc` (accounts/forms.py:38) requires a verification document for farmer/PM. For quick demo testing, register traders or upload a dummy file.

### 11.4 🟡 PM accounts start inactive
- A newly registered PM cannot log in until an admin approves them via `/panel/pm/pending/` (by design, but surprising in demos).

### 11.5 🟡 `farmer:trading/my_bids.html` vs trader naming overlap
- Both `farmer` and `trader` apps define a `my_bids` view; templates are correctly namespaced per app.

### 11.6 🟡 Empty test suites
- All `tests.py` files contain only placeholders — no regression protection before the demo.

### 11.7 🟡 No fixed-price purchase despite model support
- `Listing.ListingType` defines only `AUCTION` in trader/models.py:19; AGENTS.md spec mentions fixed price. Demo must use the auction path only.

### 11.8 🟡 Mock payments
- `MakePaymentView` creates `Payment` records with `MOCK-<timestamp>` refs and immediately marks them completed. Fine for demo, not for production.

---

## 12. Setup & Installation

### Prerequisites
- Python 3.11+
- (Optional) Git

### Steps

```bash
# 1. Create & activate virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/macOS

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
#   - copy/ensure .env exists with:
#     DJANGO_SECRET_KEY=...
#     DJANGO_DEBUG=True
#     OPENROUTER_API_KEY=sk-or-v1-... (optional for chatbot)

# 4. Apply migrations
python manage.py migrate

# 5. Create admin (or use seeded admin below)
python manage.py createsuperuser
#   USERNAME_FIELD is email → enter email, then username, then password

# 6. Run the server
python manage.py runserver
```

### Seed Login (from README)
| Role | Email | Password |
|------|-------|----------|
| Admin | `admin@cardetrade.in` | `admin123` |

### Demo Walkthrough (recommended order)
1. Login as admin → approve yourself or create users via `/admin/`.
2. Register a **farmer** (upload a dummy verification doc) → create farm → create batch.
3. Register a **product manager** → approve via `/panel/pm/pending/` → PM logs in → verify the batch (grade + price).
4. Watch the auction listing appear automatically (signal).
5. Register a **trader** → place a bid → farmer accepts → order created → trader pays (mock).
6. Try the chatbot: "Show me active listings" or "What can a trader do?".

---

## 13. Environment Variables (`.env`)

```ini
DJANGO_SECRET_KEY=your-strong-secret-key-here
DJANGO_DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
OPENROUTER_API_KEY=sk-or-v1-your-key-here   # optional; chatbot needs it
OPENROUTER_MODEL=google/gemma-2-9b-it        # or any OpenRouter model
```

| Variable | Default | Purpose |
|----------|---------|---------|
| `DJANGO_SECRET_KEY` | insecure dev default | Session/signing secret |
| `DJANGO_DEBUG` | `True` in settings | Debug mode |
| `ALLOWED_HOSTS` | `127.0.0.1,localhost` | Host allowlist |
| `OPENROUTER_API_KEY` | empty | AI chatbot key (chatbot returns a friendly "not configured" message if empty) |
| `OPENROUTER_MODEL` | `google/gemma-2-9b-it` | AI model id |

---

## 14. Testing Status

| App | Test file | Content |
|-----|-----------|---------|
| accounts | `accounts/tests.py` | Placeholder only |
| farmer | `farmer/tests.py` | Placeholder only |
| trader | `trader/tests.py` | Placeholder only |
| pm | `pm/tests.py` | Placeholder only |
| panel | `panel/tests.py` | Placeholder only |
| chat | `chat/tests.py` | Placeholder only |

**Recommended test coverage to add (in priority order):**
1. Registration → role flags per role (accounts)
2. Login success/failure + login error visibility (accounts)
3. Verify batch → listing auto-creation signal (farmer/pm)
4. Bid acceptance → order creation + outbid marking, atomicity (farmer)
5. Role enforcement: trader hitting farmer views → 403 (accounts)
6. Payment flow → order paid (trader)

---

## 15. Roadmap & Next Steps

### Phase 1 — Stabilize (before demo, ~1-2 days)
- [ ] Fix login error visibility (Section 11.1)
- [ ] Email normalization (Section 11.2)
- [ ] Seed demo data: farmer, trader, PM, farm, batch, verification, listing, bid, order
- [ ] Add core tests (Section 14)

### Phase 2 — Complete MVP gaps (1-2 weeks)
- [ ] Fixed-price direct-buy flow
- [ ] Order tracking workflow (shipment updates)
- [ ] Reports module (admin-generated PDF/CSV reports)
- [ ] Audit log auto-write receiver (or `django-simple-history`)

### Phase 3 — Production readiness (2-4 weeks)
- [ ] Real payment gateway integration
- [ ] PostgreSQL + environment-based settings
- [ ] Email notifications (order placed, bid accepted, PM approval)
- [ ] Media/static serving via nginx/whitenoise
- [ ] Password reset flow
- [ ] Rate limiting + brute-force protection on login
- [ ] CI pipeline (lint, test, deploy)

---

## 16. Appendix: Audit Logging & AI Chatbot

### 16.1 Audit Logging Architecture
- **Model:** `accounts.AuditLog` — stores `action`, `table_name`, `record_id`, `old_value`/`new_value` JSON, `ip_address`, `user`.
- **Middleware:** `AuditMiddleware` saves current `user` + client IP to thread-local storage on every request (`accounts/middleware.py`).
- **Design intent (AGENTS.md rule R6):** every state mutation must be logged for compliance.
- **Current gap:** the `post_save`/`pre_save` receivers that write AuditLog rows are stubbed — the plumbing exists, the logging receiver is not fully connected. 

### 16.2 AI Chatbot (OpenRouter)
- **Endpoint:** `POST /chat/api/` with JSON `{"message": "..."}` → `{"response": "..."}` (login required).
- **Service:** `chat/services/chatbot.py`:
  - `SYSTEM_PROMPT` — persona, platform rules, cardamom domain knowledge, current date injected.
  - `get_db_context(user, query)` — keyword-matches the user's question against listings/batches/farms/orders and returns live JSON statistics (price range, grade distribution, region distribution, status counts) as an extra system message.
  - `call_openrouter(messages)` — HTTP POST to `https://openrouter.ai/api/v1/chat/completions` with 30 s timeout and graceful error messages (missing key, 401, timeout).
  - `format_response()` — strips markdown for plain-text chat display.
- **Frontend:** floating widget (`templates/includes/chatbot_widget.html` + `static/js/chatbot.js`) shown to authenticated users.
- **Role-awareness:** answers differ by role — e.g., a farmer's order queries are filtered to `seller=user`; traders see only their own purchases.

---

*End of Report — CardeTrade Cardamom Trading Platform, July 2026*
