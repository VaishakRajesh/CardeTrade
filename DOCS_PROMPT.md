# 📄 CardeTrade Documentation Generator Prompt

> **Copy-paste this entire file into any AI assistant (Claude, ChatGPT, etc.) to generate comprehensive documentation for the CardeTrade project.**

---

Below is the complete specification of the **CardeTrade** — Cardamom Trading Platform. Generate a full documentation suite covering:

1. **README.md** — Project overview, features, quick start, tech stack
2. **ARCHITECTURE.md** — System architecture, request flow, component interaction
3. **SETUP.md** — Step-by-step installation, configuration, deployment
4. **MODELS.md** — All 16 database tables with fields, types, constraints, relationships
5. **API.md** — Complete endpoint reference with methods, roles, templates
6. **WORKFLOW.md** — Business processes, status state machines, user journeys
7. **TEMPLATES.md** — UI/UX guide, design system, CSS classes, JS interactions
8. **TESTS.md** — Testing patterns, test cases, coverage

Use the following specification to generate all 8 documents. Format in clean GitHub-flavored Markdown.

---

## PROJECT IDENTITY

| Property | Value |
|----------|-------|
| **Name** | CardeTrade — Cardamom Trading Platform |
| **Type** | Django 5.x web application (Python 3.11+) |
| **Database** | SQLite (dev) / PostgreSQL (prod) |
| **Frontend** | HTML + CSS + JS + **Bootstrap 5** (server-rendered templates) |
| **Auth** | Custom `AbstractUser` with role field (role: `farmer`, `trader`, `product_manager`, `admin`) |
| **Styling** | Bootstrap 5 + custom premium CSS (`static/css/style.css`) — no Tailwind, no MUI, no React |
| **App Architecture** | Single-app design — all logic in `app/` directory |
| **Audit** | Every mutation logged via `AuditLog` model |
| **Tests** | Django `TestCase` with `setUpTestData` |
| **Forms** | `django-crispy-forms` + `crispy-bootstrap5` |
| **Core Philosophy** | "Grade First, Trade Second" — batch must be verified by PM before listing |

## REPOSITORY STRUCTURE

```
CardeTrade/
├── cardetrade/                          # Django project configuration
│   ├── __init__.py
│   ├── settings.py                      # AUTH_USER_MODEL = 'app.User', crispy config
│   ├── urls.py                          # Root URL dispatcher (path('', include('app.urls')))
│   ├── wsgi.py
│   └── asgi.py
├── app/                                 # Single Django application (all business logic)
│   ├── __init__.py
│   ├── models.py                        # All 16 database models
│   ├── views.py                         # All platform views (CBVs + FBVs)
│   ├── urls.py                          # Complete URL routing
│   ├── forms.py                         # RegistrationForm, LoginForm, BatchForm, VerificationForm, etc.
│   ├── decorators.py                    # @role_required, @farmer_required, @trader_required, etc.
│   ├── admin.py                         # Admin configurations for all models
│   ├── tests.py                         # Test cases
│   ├── signals.py                       # Post-save signal handlers
│   ├── middleware.py                     # AuditMiddleware (thread-local user/IP capture)
│   ├── utils.py                         # Helper functions
│   ├── templates/app/                   # App-specific HTML templates
│   │   ├── auth/                        # login.html, register.html, profile.html
│   │   ├── dashboard/                   # home.html, farmer.html, trader.html, pm.html, admin.html
│   │   ├── batches/                     # list.html, create.html, detail.html, verify.html
│   │   ├── trading/                     # listing_list.html, listing_detail.html, place_bid.html, direct_buy.html, my_bids.html
│   │   ├── orders/                      # list.html, detail.html
│   │   ├── farms/                       # list.html, create.html
│   │   ├── messaging/                   # conversation_list.html, conversation_detail.html
│   │   ├── disputes/                    # create.html, list.html, resolve.html
│   │   └── notifications/              # list.html
│   └── migrations/
├── templates/                           # Shared templates
│   ├── base.html                        # Bootstrap 5 base with preloader, premium CSS/JS
│   └── includes/
│       ├── navbar.html                  # Premium transparent navbar, notification dropdown
│       ├── alerts.html                  # Styled Django messages
│       └── footer.html                  # Premium dark footer
├── static/
│   ├── css/style.css                    # 1000+ lines premium CSS (25+ keyframes, design tokens)
│   ├── js/main.js                       # 200+ lines JS (animations, particles, tilt, parallax)
│   └── image/
│       ├── cardamom1.jpg                # Hero background, listing cards, auth pages
│       └── cardamom2.jpg                # Hero main image, philosophy section, auth logo
├── media/
│   ├── batch_images/
│   └── documents/
├── requirements.txt
├── manage.py
├── AGENTS.md                            # AI agent instruction manual
├── README.md
└── .env                                 # Environment variables
```

## COMPLETE DATABASE SCHEMA (16 TABLES)

### 1. User (extends AbstractUser)
- **role**: CharField(20), choices: `farmer`, `trader`, `product_manager`, `admin` (TextChoices)
- **phone**: CharField(20), blank=True
- **address**: TextField, blank=True
- **region**: CharField(100), blank=True
- **save() method**: Auto-sets `is_staff`/`is_superuser` — Admin → both True, PM → staff True superuser False, others → both False
- Inherits from AbstractUser: username, email, password, first_name, last_name, is_active, is_staff, is_superuser, date_joined, last_login

### 2. Farm
- **farmer**: FK→User (CASCADE, related_name='farms', limit_choices_to={'role':'farmer'})
- **farm_name**: CharField(150)
- **location**: CharField(200)
- **region**: CharField(100)
- **total_area_acres**: DecimalField(8,2), nullable
- **certification**: CharField(100)
- **created_at**: DateTimeField(auto_now_add)
- Meta: verbose_name_plural='farms', ordering=['-created_at']

### 3. Batch
- **batch_code**: CharField(50), unique, auto-generated format `CDM-{year}-{sequential:04d}`
- **farmer**: FK→User (CASCADE, related_name='batches', limit_choices_to={'role':'farmer'})
- **farm**: FK→Farm (SET_NULL, nullable, related_name='batches')
- **quantity_kg**: DecimalField(10,2)
- **harvest_date**: DateField()
- **description**: TextField
- **estimated_price_per_kg**: DecimalField(10,2)
- **status**: CharField(20), TextChoices: PENDING→under_review→VERIFIED→LISTED→SOLD / REJECTED
- **created_at**: DateTimeField(auto_now_add)
- **updated_at**: DateTimeField(auto_now)

### 4. QualityVerification (OneToOne→Batch)
- **batch**: OneToOneField→Batch (CASCADE, related_name='verification')
- **product_manager**: FK→User (SET_NULL, nullable, related_name='verifications')
- **grade**: CharField(1), TextChoices: A='A', B='B', C='C'
- **moisture_content_pct**: DecimalField(5,2), nullable
- **aroma_score**: PositiveSmallIntegerField, nullable (1-10)
- **color_score**: PositiveSmallIntegerField, nullable (1-10)
- **purity_pct**: DecimalField(5,2), nullable
- **verified_price_per_kg**: DecimalField(10,2)
- **remarks**: TextField
- **verified_at**: DateTimeField(auto_now_add)

### 5. Listing (OneToOne→Batch)
- **batch**: OneToOneField→Batch (CASCADE, related_name='listing')
- **farmer**: FK→User (CASCADE, related_name='listings')
- **listing_type**: CharField(20), TextChoices: FIXED_PRICE='fixed_price', AUCTION='auction'
- **price_per_kg**: DecimalField(10,2)
- **min_order_kg**: DecimalField(10,2), nullable
- **available_qty_kg**: DecimalField(10,2)
- **auction_start_time**: DateTimeField, nullable
- **auction_end_time**: DateTimeField, nullable
- **is_active**: BooleanField(default=True)
- **created_at**: DateTimeField(auto_now_add)

### 6. Bid
- **listing**: FK→Listing (CASCADE, related_name='bids')
- **trader**: FK→User (CASCADE, related_name='bids', limit_choices_to={'role':'trader'})
- **bid_price_per_kg**: DecimalField(10,2)
- **quantity_kg**: DecimalField(10,2)
- **status**: CharField(10), TextChoices: ACTIVE→ACCEPTED|REJECTED|OUTBID|EXPIRED
- **notes**: TextField
- **bid_time**: DateTimeField(auto_now_add)
- Meta: ordering=['-bid_price_per_kg']

### 7. Order
- **order_code**: CharField(50), unique, auto-generated format `ORD-{year}-{sequential:04d}`
- **listing**: FK→Listing (SET_NULL, nullable, related_name='orders')
- **batch**: FK→Batch (SET_NULL, nullable, related_name='orders')
- **buyer**: FK→User (CASCADE, related_name='purchases', limit_choices_to={'role':'trader'})
- **seller**: FK→User (CASCADE, related_name='sales', limit_choices_to={'role':'farmer'})
- **bid**: FK→Bid (SET_NULL, nullable, related_name='orders')
- **quantity_kg**: DecimalField(10,2)
- **price_per_kg**: DecimalField(10,2)
- **total_amount**: GeneratedField (Django 5+) — computed as `quantity_kg * price_per_kg`, db_persist=True
- **status**: CharField(20), TextChoices: PENDING→CONFIRMED→PROCESSING→SHIPPED→DELIVERED / CANCELLED / DISPUTED
- **payment_status**: CharField(20), TextChoices: UNPAID→PARTIALLY_PAID→PAID→REFUNDED
- **created_at/updated_at**: auto_now_add / auto_now

### 8. OrderTracking
- **order**: FK→Order (CASCADE, related_name='tracking_entries')
- **status**: CharField(20), choices: PENDING→CONFIRMED→PROCESSING→SHIPPED→DELIVERED→CANCELLED
- **location**: CharField(200)
- **notes**: TextField
- **updated_by**: FK→User (SET_NULL, nullable, related_name='tracking_updates')
- **tracked_at**: DateTimeField(auto_now_add)
- Meta: verbose_name_plural='order tracking', ordering=['-tracked_at']

### 9. Payment
- **order**: FK→Order (CASCADE, related_name='payments')
- **payer**: FK→User (SET_NULL, nullable, related_name='payments')
- **amount**: DecimalField(12,2)
- **payment_method**: CharField(20), TextChoices: BANK_TRANSFER, MOBILE_MONEY, CASH, ESCROW
- **transaction_ref**: CharField(100), unique, nullable
- **status**: CharField(10), TextChoices: PENDING, COMPLETED, FAILED, REFUNDED
- **paid_at**: DateTimeField, nullable
- **created_at**: auto_now_add

### 10. Dispute
- **order**: FK→Order (CASCADE, related_name='disputes')
- **raised_by**: FK→User (CASCADE, related_name='disputes_raised')
- **against_user**: FK→User (CASCADE, related_name='disputes_against')
- **reason**: TextField()
- **status**: CharField(20), TextChoices: OPEN→UNDER_REVIEW→RESOLVED→CLOSED
- **resolution**: TextField, blank=True
- **resolved_by**: FK→User (SET_NULL, nullable, related_name='disputes_resolved')
- **created_at**: auto_now_add
- **resolved_at**: DateTimeField, nullable

### 11. Notification
- **user**: FK→User (CASCADE, related_name='notifications')
- **type**: CharField(30), TextChoices: BID_RECEIVED, BID_ACCEPTED, ORDER_PLACED, ORDER_SHIPPED, PAYMENT_RECEIVED, BATCH_VERIFIED, DISPUTE_RAISED
- **message**: TextField()
- **reference_id**: IntegerField, nullable
- **reference_type**: CharField(50)
- **is_read**: BooleanField(default=False)
- **created_at**: auto_now_add

### 12. Conversation
- **batch**: FK→Batch (SET_NULL, nullable, related_name='conversations')
- **order**: FK→Order (SET_NULL, nullable, related_name='conversations')
- **type**: CharField(20), TextChoices: QUALITY_REVIEW, BATCH_INQUIRY, ORDER_SUPPORT, GENERAL
- **subject**: CharField(200)
- **status**: CharField(10), TextChoices: OPEN, ARCHIVED, LOCKED
- **created_at**: auto_now_add
- **last_message_at**: DateTimeField, nullable

### 13. ConversationParticipant
- **conversation**: FK→Conversation (CASCADE, related_name='participants')
- **user**: FK→User (CASCADE, related_name='conversation_participations')
- **role_in_chat**: CharField(20), TextChoices: FARMER, PRODUCT_MANAGER, TRADER, ADMIN
- **joined_at**: auto_now_add
- **last_read_at**: DateTimeField, nullable
- **is_muted**: BooleanField(default=False)
- **is_active**: BooleanField(default=True)
- Meta: unique_together = ('conversation', 'user')

### 14. Message
- **conversation**: FK→Conversation (CASCADE, related_name='messages')
- **sender**: FK→User (SET_NULL, nullable, related_name='sent_messages')
- **message_type**: CharField(10), TextChoices: TEXT, IMAGE, DOCUMENT, SYSTEM
- **content**: TextField
- **attachments**: JSONField, nullable, default=list
- **is_edited**: BooleanField(default=False)
- **edited_at**: DateTimeField, nullable
- **is_deleted**: BooleanField(default=False) — SOFT DELETE (only table with this)
- **deleted_at**: DateTimeField, nullable
- **sent_at**: auto_now_add

### 15. Report
- **generated_by**: FK→User (CASCADE, related_name='generated_reports')
- **report_type**: CharField(30), TextChoices: TRADE_SUMMARY, GRADE_DISTRIBUTION, FARMER_PERFORMANCE, TRADER_ACTIVITY, REVENUE
- **date_from**: DateField, nullable
- **date_to**: DateField, nullable
- **parameters**: JSONField, nullable, default=dict
- **file_path**: CharField(255)
- **created_at**: auto_now_add

### 16. AuditLog
- **user**: FK→User (SET_NULL, nullable, related_name='audit_logs')
- **action**: CharField(100) — e.g., 'batch.verified', 'order.created'
- **table_name**: CharField(50)
- **record_id**: IntegerField()
- **old_value**: JSONField, nullable
- **new_value**: JSONField, nullable
- **ip_address**: CharField(45)
- **logged_at**: auto_now_add
- Indexes: (table_name, record_id), (action), (user)

## KEY RELATIONSHIPS

- User 1:N Farm (farmer only)
- User 1:N Batch (farmer only)
- Batch 1:1 QualityVerification
- Batch 1:1 Listing
- Listing 1:N Bid
- Listing 1:N Order
- Order 1:N OrderTracking, Payment, Dispute, Conversation
- Conversation M:N User (via ConversationParticipant)
- Conversation 1:N Message
- User 1:N Notification, AuditLog

## URL STRUCTURE

### Root (cardetrade/urls.py)
```python
path('admin/', admin.site.urls),
path('', include('app.urls')),
```

### App URLs (app/urls.py)
All namespaced under `app:`:

**Auth**: `/register/`, `/login/`, `/logout/`, `/profile/`
**Dashboard**: `/dashboard/` (auto-redirect by role), `/dashboard/farmer/`, `/dashboard/trader/`, `/dashboard/pm/`, `/dashboard/admin/`
**Home**: `/` (homepage)
**Farms**: `/farms/`, `/farms/create/`, `/farms/<pk>/`
**Batches**: `/batches/`, `/batches/create/`, `/batches/<pk>/`, `/batches/<pk>/verify/`
**Trading**: `/listings/`, `/listings/<pk>/`, `/listings/<pk>/bid/`, `/listings/<pk>/buy/`, `/bids/`
**Orders**: `/orders/`, `/orders/<pk>/`
**Notifications**: `/notifications/`, `/notifications/<pk>/read/`
**Messaging**: `/conversations/`, `/conversations/create/`, `/conversations/<pk>/`
**Disputes**: `/disputes/`, `/disputes/create/`, `/disputes/<pk>/resolve/`

## ROLE ENFORCEMENT SYSTEM

```python
# app/decorators.py
def role_required(*roles):
    # Returns 403 if user not in allowed roles
    # Redirects to login if unauthenticated

# Convenience decorators:
@farmer_required        → farmer only
@trader_required        → trader only
@pm_required            → product_manager only
@admin_required         → admin only
@staff_required         → product_manager or admin
@trade_participant_required → farmer or trader
```

Usage on CBVs: `@method_decorator(role_required('farmer'), name='dispatch')`
Usage on FBVs: `@role_required('farmer')`

## VIEW PATTERNS

CBVs preferred: `LoginRequiredMixin + @method_decorator(role_required(...)) + CreateView/ListView/DetailView/UpdateView`

Key views:
- `RegisterView` (FBV) — auto-login after registration
- `LoginView` (FBV) — authenticate + login
- `HomeView` — public landing page with listings
- `DashboardView` — redirect by role
- `FarmerDashboardView`, `TraderDashboardView`, `PMDashboardView`, `AdminDashboardView`
- `BatchCreateView` — farmer only, sets `form.instance.farmer = request.user`
- `BatchVerifyView` — PM only, saves QualityVerification, updates batch status
- `ListingListView` — active listings
- `PlaceBidView` — trader only, validates bid >= listing price
- `DirectBuyView` — trader only, creates Order, updates available_qty
- `MyBidsView` — farmers see bids on their listings, traders see their own bids
- `OrderListView` — farmers see sales, traders see purchases

## FORM PATTERNS

- `RegistrationForm` — ModelForm for User: username, email, password1, password2, role, phone, region
- `LoginForm` — username, password
- `UserProfileForm` — first_name, last_name, email, phone, region, address
- `BatchForm` — ModelForm for Batch: farm, quantity_kg, harvest_date, description, estimated_price_per_kg
- `VerificationForm` — ModelForm for QualityVerification: grade, moisture, aroma, color, purity, verified_price, remarks
- `BidForm` — bid_price_per_kg, quantity_kg, notes
- `DirectBuyForm` — quantity_kg
- `FarmForm` — farm_name, location, region, total_area_acres, certification

## SIGNAL IMPLEMENTATIONS

1. **Batch verified → Create Listing**: `post_save` on Batch, if status==VERIFIED, auto-create Listing via get_or_create, then set batch to LISTED
2. **Order created → Notify seller**: `post_save` on Order, if created, create Notification for seller
3. **Bid placed → Notify farmer**: `post_save` on Bid, if created, create Notification for listing farmer
4. **Message sent → Update conversation timestamp**: `post_save` on Message, if created, update conversation.last_message_at
5. **Audit logging**: Middleware captures current user/IP per thread, signals log mutations

## STATUS STATE MACHINES

**Batch**: PENDING → UNDER_REVIEW → VERIFIED → LISTED → SOLD / REJECTED
**Order**: PENDING → CONFIRMED → PROCESSING → SHIPPED → DELIVERED / CANCELLED / DISPUTED
**Bid**: ACTIVE → ACCEPTED | REJECTED | OUTBID | EXPIRED
**Dispute**: OPEN → UNDER_REVIEW → RESOLVED → CLOSED

## BUSINESS FLOW (END-TO-END)

1. Farmer registers → creates farm → creates batch (PENDING)
2. PM views pending batches → inspects → verifies with grade A/B/C (VERIFIED)
3. Signal auto-creates Listing (LISTED)
4. Trader browses listings → Direct Buy OR Places Bid
5. If bid: farmer reviews → accepts → Order created
6. Order progresses: PENDING → CONFIRMED → PROCESSING → SHIPPED → DELIVERED
7. Notifications sent at each step

## TRADING MECHANISMS

**Fixed Price**: Trader enters qty → clicks Buy Now → Order created → available_qty decreased → if 0, listing deactivated and batch→SOLD
**Auction**: Traders place bids (anyone can outbid) → highest bid shown → farmer accepts one → Order created → others get OUTBID/EXPIRED

## SETUP

```bash
python -m venv .venv
.venv\Scripts\activate     # Windows
# source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
# Visit: http://127.0.0.1:8000/
```

## DEPENDENCIES (requirements.txt)
```
Django>=5.0,<5.2
python-decouple==3.*
Pillow==10.*
django-crispy-forms==2.*
crispy-bootstrap5==2024.*
```

## SETTINGS KEY CONFIG (cardetrade/settings.py)
```
AUTH_USER_MODEL = 'app.User'
INSTALLED_APPS = [..., 'crispy_forms', 'crispy_bootstrap5', 'app']
CRISPY_TEMPLATE_PACK = 'bootstrap5'
CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
LOGIN_URL = '/login/'
STATICFILES_DIRS = [BASE_DIR / 'static']
MEDIA_ROOT = BASE_DIR / 'media'
MIDDLEWARE includes 'app.middleware.AuditMiddleware'
```

## DESIGN SYSTEM (CSS — static/css/style.css)

- **Color Tokens**: Forest green (#1a4d2e, #2d6a4f), Gold (#c8a951, #d4af37), Cream (#faf3e0)
- **CSS Variables**: Comprehensive design tokens (--clr-green-dark, --clr-gold, --shadow-card, --radius-card, etc.)
- **25+ Keyframe Animations**: fadeInUp, fadeInLeft, fadeInRight, scaleIn, float, floatSlow, shimmer, pulseGlow, gradientShift, cardGlow, ripple
- **Key CSS Classes**: 
  - `.hero-premium` — full-screen hero with gradient overlay + parallax
  - `.glass-card` — backdrop-filter blur with border glow
  - `.card-premium` — gradient top border on hover
  - `.stat-card-premium` with color variants: `.stat-card-green`, `-gold`, `-blue`, `-purple`, `-teal`, `-rose`
  - `.btn-premium-primary` — gold gradient with glow
  - `.btn-premium-secondary` — glass transparent
  - `.form-premium` — green focus ring
  - `.badge-premium-*` — color-coded status badges
  - `.grade-badge` — circular A/B/C grade indicators
  - `.listing-type-badge` — `.fixed` / `.auction` variants
  - `.chat-container`, `.msg-bubble`, `.notif-dropdown`, `.timeline-premium`, `.pagination-premium`
  - `.animate-on-scroll`, `.animate-on-scroll-left`, `.animate-on-scroll-right`, `.animate-on-scroll-scale`

## JAVASCRIPT (static/js/main.js — 200+ lines)

- **Preloader**: Full-screen with logo + spinner + subtitle, hides after 1.5s
- **Scroll Navbar**: .scrolled class added after 80px
- **IntersectionObserver**: Triggers .visible class for scroll animations
- **Counter Animation**: Animated numbers using data-target
- **Card Tilt**: 3D perspective rotate on mousemove
- **Parallax**: Hero background moves slower on scroll
- **Particle Generator**: 20 floating dots in hero
- **Scroll Progress Bar**: Fixed top bar
- **Ripple Effect**: Click ripple on .btn-premium
- **Confetti**: Random particles on celebrate button
- **Smooth Scroll**: Anchor links
- **Notification Bell**: Heartbeat animation when unread
- **Chat Auto-scroll**: Scrolls to bottom on load
- **Quantity Calculator**: Real-time price update on buy forms

## KEY RULES (Must Follow)

1. **R1**: Use `models.TextChoices` for ALL enums (never IntegerChoices)
2. **R2**: Always set `related_name` on every `ForeignKey`
3. **R3**: `total_amount` on Order is `GeneratedField` (Django 5+)
4. **R4**: `AUTH_USER_MODEL = 'app.User'` before first migration
5. **R5**: Soft delete ONLY for Messages (is_deleted=True)
6. **R6**: Every state mutation logged in AuditLog
7. **R7**: PM has is_staff=True, is_superuser=False
8. **R8**: Reference ENUMs via model class (e.g., `Batch.Status.PENDING`)
9. **R9**: unique_together on ConversationParticipant (no composite PK)
10. **R10**: Farmers cannot bid. Traders cannot create batches. PMs cannot trade.

## DECIMAL FIELD STANDARDS

| Field | max_digits | decimal_places |
|-------|------------|----------------|
| quantity_kg | 10 | 2 |
| price_per_kg | 10 | 2 |
| total_amount | 12 | 2 |
| area_acres | 8 | 2 |
| moisture_pct | 5 | 2 |
| purity_pct | 5 | 2 |
| min_order_kg | 10 | 2 |

## ADMIN CONFIGURATION

All 16 models registered in admin.py. Key configs:
- `UserAdmin` extends BaseUserAdmin: list_display [username, email, role, is_staff, is_active], list_filter [role, is_staff]
- `BatchAdmin`: list_display [batch_code, farmer, quantity_kg, status, created_at], list_filter [status], search_fields [batch_code, farmer__username], readonly_fields [batch_code]
- `QualityVerificationAdmin`: list_display [batch, grade, verified_price_per_kg, product_manager, verified_at], list_filter [grade]

## TESTING PATTERNS

- Use `cls.setUpTestData` for shared data
- Test: status codes (200, 302, 403), redirects, database state, content
- Always test unauthorized access returns 403
- Test batch code format with regex
- Test signal behavior (verification → listing created)
- Test auction highest bid wins

---

Now generate the documentation. Format each document with a title, table of contents (if long), and clean markdown. Use mermaid diagrams for workflows and state machines where helpful.
