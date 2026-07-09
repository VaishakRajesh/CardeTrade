# CardeTrade — Project Handoff Document

**Document Version:** 2.0  
**Handoff Date:** 2026-07-09  
**Project Status:** Complete (per `done.txt`, dated 2026-07-08)  
**Prepared For:** Maintenance, operations, and future development teams

---

## Table of Contents

1. [Project Summary](#1-project-summary)
2. [Architecture Overview](#2-architecture-overview)
3. [Codebase Overview](#3-codebase-overview)
4. [Deployment & Operations](#4-deployment--operations)
5. [Dependencies & Integrations](#5-dependencies--integrations)
6. [Testing & QA Status](#6-testing--qa-status)
7. [Documentation & Resources](#7-documentation--resources)
8. [Future Considerations & Roadmap](#8-future-considerations--roadmap)
9. [Contact Information](#9-contact-information)
10. [Implementation Analysis & Completion Status (Referencing done.txt)](#10-implementation-analysis--completion-status-referencing-donetxt)

---

## 1. Project Summary

### What Is CardeTrade?

CardeTrade is a **Django 5.2 server-rendered web application** for premium cardamom trading in India. It connects four stakeholder roles — **Farmers**, **Traders**, **Product Managers (PMs)**, and **Admins** — through a transparent, quality-verified marketplace.

**Tagline:** *Grade First, Trade Second.*

### Project Objectives

| Objective | Status |
|-----------|--------|
| Role-based digital marketplace for cardamom | ✅ Delivered |
| Quality verification workflow before listing | ✅ Delivered |
| Fixed-price and auction trading models | ✅ Delivered |
| Full order lifecycle with tracking and payments | ✅ Delivered |
| Dispute resolution and in-app messaging | ✅ Delivered |
| Audit trail for compliance | ✅ Delivered (middleware + model) |
| Premium responsive UI with animations | ✅ Delivered |
| Email-based authentication | ✅ Delivered |
| User verification with document upload | ✅ Delivered |

### Key Features Delivered

- **Authentication:** Register, login (email + password), logout, profile editing
- **Role dashboards:** Farmer, Trader, PM, Admin — each with stats and quick actions
- **Farm management:** Farmers register farms linked to batches
- **Batch pipeline:** Create → review → verify → auto-list → sell
- **Quality verification:** PM grades batches (A/B/C), sets verified price
- **Marketplace:** Browse listings, place bids (auction), direct buy (fixed price)
- **Orders:** Full lifecycle with tracking timeline and payment records
- **Disputes:** Raise and resolve order disputes (admin)
- **Messaging:** Conversation threads with soft-deleted messages
- **Notifications:** Auto-generated on bids, orders, and key events
- **Admin panel:** Full CRUD for all 16 tables, bulk user verification
- **Premium UI:** Glass morphism, parallax hero, 4-layer cinematic background, scroll animations

### Technology at a Glance

| Layer | Technology |
|-------|------------|
| Backend | Python 3.11+, Django 5.2 |
| Database | SQLite (dev) / PostgreSQL (prod recommended) |
| Frontend | HTML + Bootstrap 5.3 + ~2,000 lines custom CSS + Vanilla JS |
| Auth | Custom `AbstractUser` with role field |
| Forms | django-crispy-forms + crispy-bootstrap5 |
| Deployment target | Render (free tier) — see `deploy.md` |

---

## 2. Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                        Browser (Client)                      │
│              Bootstrap 5 + Custom CSS + Vanilla JS           │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP
┌──────────────────────────▼──────────────────────────────────┐
│                    Django 5.2 (WSGI)                         │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ Middleware  │  │    Views     │  │    Templates      │  │
│  │ Auth, CSRF  │→ │ 28 CBVs      │→ │ Server-rendered   │  │
│  │ Audit       │  │ @role_required│  │ HTML             │  │
│  └─────────────┘  └──────┬───────┘  └───────────────────┘  │
│                          │                                   │
│  ┌─────────────┐  ┌──────▼───────┐  ┌───────────────────┐  │
│  │  Signals    │← │    Models    │→ │  SQLite / PG      │  │
│  │  (events)   │  │  16 tables   │  │  Database         │  │
│  └─────────────┘  └──────────────┘  └───────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Request Flow

```
Browser Request
  → cardetrade/urls.py (root router)
  → app/urls.py (feature routes)
  → Middleware stack (Security, Session, CSRF, Auth, Messages, Audit)
  → View (LoginRequiredMixin + @role_required decorator)
  → Model queries / form validation
  → Template render (extends base.html)
  → HTML response
```

### Data Flow — Core Trading Pipeline

```
Farmer creates Batch (pending)
  → PM reviews (under_review)
  → PM verifies quality → QualityVerification record (verified)
  → Signal: auto-create Listing (listed)
  → Trader bids OR direct-buys
  → Order created (pending) → Notification to seller
  → OrderTracking entries → Payment records
  → Optional: Dispute raised → Admin resolves
```

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Single Django app (`app/`) | Simpler deployment, no cross-app imports |
| Server-rendered templates (no SPA/DRF) | Faster MVP, lower complexity |
| `TextChoices` for all enums | Human-readable DB values (never `IntegerChoices`) |
| `GeneratedField` for `Order.total_amount` | DB-computed, avoids stale totals |
| Signal-created listings | Every verified batch is automatically listed |
| Soft delete on `Message` only | Other tables use status or hard delete |
| Email as `USERNAME_FIELD` | Better UX; username retained for display |
| Verification docs for Farmer/PM | Trust and compliance for sellers/reviewers |
| Thread-local audit middleware | Captures user/IP without passing through every call |
| Pure CSS (no Tailwind/React) | Full control over premium animations |

### Role Permission Matrix

| Action | Farmer | Trader | PM | Admin |
|--------|--------|--------|-----|-------|
| Create farm/batch | ✅ | ❌ | ❌ | ❌ |
| Verify batch | ❌ | ❌ | ✅ | ✅ |
| Browse listings | ✅ | ✅ | ✅ | ✅ |
| Place bid / buy | ❌ | ✅ | ❌ | ❌ |
| Resolve disputes | ❌ | ❌ | ❌ | ✅ |
| Django admin panel | ❌ | ❌ | ✅ (staff) | ✅ (superuser) |

---

## 3. Codebase Overview

### Repository Structure

```
CardeTrade/
├── cardetrade/                 # Django project configuration
│   ├── settings.py             # AUTH_USER_MODEL, crispy, static/media
│   ├── urls.py                 # Root URL routing (/admin/, include app.urls)
│   ├── wsgi.py                 # WSGI entry point
│   └── asgi.py                 # ASGI entry point (not used for WebSockets yet)
│
├── app/                        # Single application — all business logic
│   ├── models.py               # 16 database models (~930 lines)
│   ├── views.py                # 28 class-based views (~1,130 lines)
│   ├── urls.py                 # 30+ named URL patterns
│   ├── forms.py                # Registration, Login, Profile forms
│   ├── decorators.py           # @role_required and convenience variants
│   ├── signals.py              # Auto-listing, notifications, timestamps
│   ├── middleware.py           # AuditMiddleware (user/IP thread-local)
│   ├── admin.py                # All models registered + verify_users action
│   ├── apps.py                 # Signal connection in ready()
│   ├── utils.py                # Helper utilities
│   ├── tests.py                # Test scaffold (see Testing section)
│   ├── migrations/             # 0001–0004 (see Migrations)
│   └── templates/app/          # Feature-organized HTML templates
│       ├── auth/               # login, register, profile
│       ├── dashboard/          # home, farmer, trader, pm, admin
│       ├── batches/            # list, create, detail, verify
│       ├── trading/            # listings, bids, direct buy
│       ├── orders/             # list, detail
│       ├── farms/              # list, create
│       ├── messaging/          # conversation list/detail/create
│       ├── disputes/           # list, create, resolve
│       └── notifications/      # list
│
├── templates/                  # Shared templates
│   ├── base.html               # Bootstrap 5 shell, preloader, blocks
│   └── includes/               # navbar, alerts, footer
│
├── static/
│   ├── css/style.css           # ~2,000 lines premium design system
│   ├── js/main.js              # Animations, nav, counters, interactions
│   └── image/                  # cardamom1.jpg, cardamom2.jpg, bg.gif
│
├── docs/                       # Technical documentation
├── media/                      # User uploads (verification docs, etc.)
├── manage.py                   # Django CLI
├── requirements.txt            # Python dependencies
├── README.md                   # Project overview and quick start
├── AGENTS.md                   # AI agent coding conventions
├── deploy.md                   # Render deployment guide
├── user.md                     # Seed account credentials
├── done.txt                    # Project completion checklist
└── handoff.md                  # This document
```

### Database Models (16 Tables)

| # | Model | Purpose |
|---|-------|---------|
| 1 | `User` | Extended auth: role, email login, verification |
| 2 | `Farm` | Farmer farm profiles |
| 3 | `Batch` | Cardamom harvest batches (`CDM-YYYY-NNNN`) |
| 4 | `QualityVerification` | PM grade assessment (A/B/C) |
| 5 | `Listing` | Marketplace listing (fixed/auction) |
| 6 | `Bid` | Auction bids with status workflow |
| 7 | `Order` | Purchase orders (`ORD-YYYY-NNNN`, GeneratedField total) |
| 8 | `OrderTracking` | Order status timeline |
| 9 | `Payment` | Payment records |
| 10 | `Dispute` | Order dispute resolution |
| 11 | `Notification` | In-app notifications |
| 12 | `Conversation` | Chat threads |
| 13 | `ConversationParticipant` | Chat membership |
| 14 | `Message` | Chat messages (soft delete) |
| 15 | `Report` | Analytics report structure |
| 16 | `AuditLog` | Mutation audit trail |

### Views (28 Class-Based Views)

| Area | Views |
|------|-------|
| Auth | `HomeView`, `RegisterView`, `LoginView`, `LogoutView`, `ProfileView` |
| Dashboards | `DashboardRedirectView`, `FarmerDashboardView`, `TraderDashboardView`, `PMDashboardView`, `AdminDashboardView` |
| Batches | `BatchListView`, `BatchCreateView`, `BatchDetailView`, `BatchVerifyView` |
| Trading | `ListingListView`, `ListingDetailView`, `PlaceBidView`, `DirectBuyView`, `MyBidsView` |
| Orders | `OrderListView`, `OrderDetailView` |
| Farms | `FarmListView`, `FarmCreateView` |
| Messaging | `ConversationListView`, `ConversationDetailView`, `ConversationCreateView` |
| Disputes | `DisputeListView`, `DisputeCreateView`, `DisputeResolveView` |
| Notifications | `NotificationListView`, `NotificationMarkReadView` |

### URL Map (Key Routes)

| URL | Name | Access |
|-----|------|--------|
| `/` | `app:home` | Public |
| `/register/` | `app:register` | Public |
| `/login/` | `app:login` | Public |
| `/logout/` | `app:logout` | Auth |
| `/profile/` | `app:profile` | Auth |
| `/dashboard/` | `app:dashboard` | Auth (role redirect) |
| `/dashboard/farmer/` | `app:farmer_dashboard` | Farmer |
| `/dashboard/trader/` | `app:trader_dashboard` | Trader |
| `/dashboard/pm/` | `app:pm_dashboard` | PM |
| `/dashboard/admin/` | `app:admin_dashboard` | Admin |
| `/batches/` | `app:batch_list` | Auth |
| `/batches/create/` | `app:batch_create` | Farmer |
| `/batches/<pk>/verify/` | `app:batch_verify` | PM |
| `/listings/` | `app:listing_list` | Auth |
| `/listings/<pk>/bid/` | `app:place_bid` | Trader |
| `/listings/<pk>/buy/` | `app:direct_buy` | Trader |
| `/orders/` | `app:order_list` | Auth |
| `/conversations/` | `app:conversation_list` | Auth |
| `/disputes/` | `app:dispute_list` | Auth |
| `/notifications/` | `app:notification_list` | Auth |
| `/admin/` | Django Admin | Staff |

### Coding Standards & Conventions

Documented in detail in `AGENTS.md`. Critical rules:

- Always use `models.TextChoices` (never `IntegerChoices`)
- Set `related_name` on every `ForeignKey`
- Use `@role_required` decorator (not `@login_required` alone)
- Reference enum constants via model class (e.g. `Batch.Status.PENDING`)
- Prefer class-based views with `LoginRequiredMixin`
- Templates extend `base.html`; use Bootstrap 5 classes
- Signals live in `signals.py`, connected in `apps.py`
- Django `{# #}` comments must be **single-line only** (multiline comments render as visible text)

### Critical Code Areas

| File | Why Critical |
|------|--------------|
| `app/models.py` | All schema, business enums, auto-code generation |
| `app/views.py` | All HTTP handlers and role enforcement |
| `app/signals.py` | Auto-listing on verify — core business automation |
| `app/decorators.py` | Role-based access control |
| `app/middleware.py` | Audit context for compliance |
| `cardetrade/settings.py` | `AUTH_USER_MODEL`, middleware, static/media |
| `static/css/style.css` | Entire visual design system |
| `templates/includes/navbar.html` | Global navigation and role-aware menus |

### Recent UI Fixes (Post done.txt, 2026-07-09)

- Removed leaking multiline Django template comments from `home.html`, `listing_list.html`, `batches/list.html`
- Fixed navbar "Get Started" button text color when `.active` class applied (gold-on-gold invisible text)

---

## 4. Deployment & Operations

### Local Development

```bash
# Activate virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/Mac

pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Access at `http://127.0.0.1:8000/`

### Environment Configuration

| Variable | Dev Default | Production |
|----------|-------------|------------|
| `DJANGO_SECRET_KEY` | Hardcoded in settings (dev only) | Required — long random string |
| `DJANGO_DEBUG` | `True` | `False` |
| `ALLOWED_HOSTS` | `[]` (dev) | Domain list, e.g. `.onrender.com` |
| `DATABASE_URL` | SQLite (`db.sqlite3`) | PostgreSQL connection string |

> **Security note:** `settings.py` currently has a hardcoded `SECRET_KEY` and `DEBUG = True`. These **must** be moved to environment variables before any production deployment.

### Production Deployment (Render)

Full guide in `deploy.md`. Summary:

1. Push code to GitHub
2. Create Render Web Service (Python 3.11)
3. **Build command:** `pip install -r requirements.txt && python manage.py migrate`
4. **Start command:** `gunicorn cardetrade.wsgi:application --bind 0.0.0.0:$PORT`
5. Set environment variables (`DJANGO_SECRET_KEY`, `DJANGO_DEBUG=False`, `ALLOWED_HOSTS`)
6. Add `gunicorn` and `whitenoise` to `requirements.txt` for production
7. Use PostgreSQL (Render add-on) instead of ephemeral SQLite
8. Use S3/Cloudinary for media uploads (Render free tier does not persist files)

### Static & Media Files

| Type | Dev | Production |
|------|-----|------------|
| Static (CSS/JS/images) | `STATICFILES_DIRS` → served by Django | `collectstatic` + WhiteNoise or CDN |
| Media (uploads) | `MEDIA_ROOT/media/` | S3, Cloudinary, or persistent volume |

### Logging & Monitoring

| Mechanism | Status |
|-----------|--------|
| Django admin audit (`AuditLog` model) | ✅ Model exists; middleware captures user/IP |
| Application logging (Python `logging`) | ⚠️ Not configured — add for production |
| Error monitoring (Sentry, etc.) | ❌ Not integrated |
| Health check endpoint | ❌ Not implemented |

### Operational Runbook

| Task | Command |
|------|---------|
| Run dev server | `python manage.py runserver` |
| Apply migrations | `python manage.py migrate` |
| Create superuser | `python manage.py createsuperuser` |
| Collect static files | `python manage.py collectstatic` |
| System check | `python manage.py check` |
| Run tests | `python manage.py test app` |
| Verify user (admin) | Django Admin → Users → select → "Mark selected users as verified" |
| Reset DB (dev only) | Delete `db.sqlite3`, run `migrate` |

### Seed Accounts (Pre-loaded via Migration)

See `user.md` and Section 10. Login URL: **`/login/`** (email-based).

---

## 5. Dependencies & Integrations

### Python Dependencies (`requirements.txt`)

| Package | Version | Purpose |
|---------|---------|---------|
| `django` | ≥5.2, <5.3 | Web framework |
| `django-crispy-forms` | ≥2.0 | Form rendering |
| `crispy-bootstrap5` | ≥2024.0 | Bootstrap 5 form templates |
| `Pillow` | ≥10.0.0 | Image/file handling |
| `python-decouple` | ≥3.8 | Environment variable loading |

### Production Dependencies (Recommended, Not Yet in requirements.txt)

| Package | Purpose |
|---------|---------|
| `gunicorn` | WSGI HTTP server |
| `whitenoise` | Static file serving |
| `dj-database-url` | PostgreSQL URL parsing |
| `psycopg2-binary` | PostgreSQL adapter |

### Frontend CDN Dependencies

| Resource | Version | Loaded From |
|----------|---------|-------------|
| Bootstrap CSS/JS | 5.3.3 | cdn.jsdelivr.net |
| Bootstrap Icons | 1.11.3 | cdn.jsdelivr.net |

### External Integrations

| Integration | Status |
|-------------|--------|
| Payment gateway (Razorpay, Stripe, etc.) | ❌ Not integrated — manual payment records only |
| SMTP email (notifications) | ❌ Not configured |
| WebSocket / real-time messaging | ❌ Not implemented |
| Cloud storage (S3/Cloudinary) | ❌ Not configured |
| REST API (Django REST Framework) | ❌ Not implemented |
| Third-party auth (Google, OAuth) | ❌ Not implemented |

### Internal Integration Points

| Component | Integrates With |
|-----------|-----------------|
| `signals.py` | Models → auto-create listings, notifications |
| `middleware.py` | All requests → audit context |
| `decorators.py` | All protected views → role enforcement |
| `admin.py` | All 16 models → Django admin CRUD |

---

## 6. Testing & QA Status

### Testing Strategy (Designed)

Per `AGENTS.md` and `app/tests.py` scaffold:

- Django `TestCase` with `setUpTestData` for shared fixtures
- Test areas: models, views, forms, signals, permissions
- Naming: `test_<what>_<condition>_<expected_result>`
- Unauthorized access must return HTTP 403

### Current Test Coverage

| Area | Status |
|------|--------|
| `app/tests.py` | ⚠️ **Scaffold only** — example tests are commented out; no active test classes |
| Model unit tests | ❌ Not implemented |
| View integration tests | ❌ Not implemented |
| Signal tests | ❌ Not implemented |
| Permission/role tests | ❌ Not implemented |

```bash
python manage.py test app
# Currently runs 0 tests
```

### Manual QA Checklist (Verified During Development)

| Feature | Verified |
|---------|----------|
| Email login with seed accounts | ✅ |
| Role-based dashboard routing | ✅ |
| Batch create → verify → auto-listing signal | ✅ |
| Marketplace listing display | ✅ |
| Bid placement and notifications | ✅ |
| Direct buy order creation | ✅ |
| Conversation create (template was missing, now fixed) | ✅ |
| User verification upload on registration | ✅ |
| Admin bulk verify action | ✅ |
| Premium UI animations and background | ✅ |
| Template comment leak fix (multiline `{# #}`) | ✅ |
| Navbar "Get Started" button readability | ✅ |

### Known Issues & Limitations

| Issue | Severity | Notes |
|-------|----------|-------|
| No automated test suite | Medium | High regression risk on changes |
| `SECRET_KEY` hardcoded in settings | High (prod) | Must use env vars before deploy |
| Media files not persistent on Render free | Medium | Needs cloud storage |
| No real-time messaging | Low | Page refresh required |
| No email notifications sent | Low | In-app notifications only |
| Multiline `{# #}` comments in some templates | Low | May still exist in unvisited templates — use single-line or `{% comment %}` |
| `user.md` lists login as `/app/login/` | Low | Actual URL is `/login/` |

---

## 7. Documentation & Resources

### In-Repository Documentation

| Document | Path | Contents |
|----------|------|----------|
| README | `README.md` | Features, quick start, tech stack, endpoints |
| Agent Instructions | `AGENTS.md` | Full coding conventions, models, patterns |
| Handoff (this doc) | `handoff.md` | Complete project handover |
| Deployment Guide | `deploy.md` | Render deployment steps |
| Completion Status | `done.txt` | Done/pending checklist |
| Test Credentials | `user.md` | Seed account emails/passwords |
| Architecture | `docs/ARCHITECTURE.md` | System design, request flow |
| Models Reference | `docs/MODELS.md` | Database schema details |
| Workflows | `docs/WORKFLOW.md` | Batch, order, bid, dispute lifecycles |
| API/Endpoints | `docs/API.md` | URL reference with methods |
| Templates Guide | `docs/TEMPLATES.md` | UI/UX design patterns |
| Setup Guide | `docs/SETUP.md` | Installation and configuration |

### Key External References

- [Django 5.2 Documentation](https://docs.djangoproject.com/en/5.2/)
- [Bootstrap 5.3 Documentation](https://getbootstrap.com/docs/5.3/)
- [Render Deployment Docs](https://render.com/docs)

### Template Inventory (28 Unique Templates)

Organized under `app/templates/app/` by feature: auth (3), dashboard (5), batches (4), trading (5), orders (2), farms (2), messaging (3), disputes (3), notifications (1), plus shared `templates/base.html` and includes.

---

## 8. Future Considerations & Roadmap

Items explicitly listed as **pending** in `done.txt`:

| Priority | Item | Rationale |
|----------|------|-----------|
| High | Payment gateway integration | Enable real transactions (Razorpay/Stripe) |
| High | Comprehensive test coverage | Reduce regression risk before scaling |
| High | Production settings hardening | Env-based secrets, `DEBUG=False`, `ALLOWED_HOSTS` |
| Medium | SMTP email notifications | Order/bid alerts via email |
| Medium | Media storage on S3/Cloudinary | Persist uploads on cloud hosting |
| Medium | PostgreSQL for production | Replace ephemeral SQLite |
| Low | WebSocket real-time messaging | Live chat without page refresh |
| Low | REST API (DRF) | Mobile app or third-party integrations |
| Low | Report generation | Populate `Report` model with analytics |

### Suggested Next Steps for Incoming Team

1. **Week 1:** Run locally, log in with all 4 seed roles, walk through full batch→order workflow
2. **Week 1:** Add `gunicorn`, `whitenoise`, env-based `settings.py` for staging deploy
3. **Week 2:** Implement core test suite (auth, batch verify signal, role permissions)
4. **Week 2:** Audit all templates for multiline `{# #}` comments
5. **Month 1:** PostgreSQL + cloud media storage on Render
6. **Month 1:** Payment gateway POC

### Technical Debt

- `app/tests.py` is a scaffold with no active tests
- Universal audit logging signal (described in AGENTS.md) is partially implemented — middleware exists, full post_save audit receiver may need completion
- `Report` model exists but report generation views are not fully built
- Some templates still contain verbose inline developer comments

---

## 9. Contact Information

> **Note:** Replace placeholder contacts with actual team details before distribution.

| Role | Contact | Scope |
|------|---------|-------|
| Project Lead / Original Developer | *[To be filled]* | Architecture decisions, feature context |
| DevOps / Deployment | *[To be filled]* | Render, database, environment config |
| Product Owner | *[To be filled]* | Business rules, workflow priorities |
| QA Lead | *[To be filled]* | Test plans, acceptance criteria |

### Escalation Path

1. Check this `handoff.md` and `done.txt` for completion status
2. Review `AGENTS.md` for implementation conventions
3. Consult `docs/` for domain-specific details
4. Contact project lead for undocumented business logic

---

## 10. Implementation Analysis & Completion Status (Referencing done.txt)

This section maps every item in `done.txt` (dated **2026-07-08**) to its implementation in the codebase and confirms completion status.

### Completion Summary

| done.txt Section | Items | Status |
|------------------|-------|--------|
| COMPLETED (items 1–9) | 9 feature areas | ✅ All verified in codebase |
| PENDING / FUTURE WORK | 6 items | ⏳ Correctly documented as out of scope |

---

### Item 1: User Verification System ✅

**done.txt requirement:**
- `is_verified` and `verification_doc` on User model
- Farmers & PMs upload proof during registration
- Traders & Admin auto-verified
- Admin bulk verify action
- Conditional file upload in registration form
- Seed accounts pre-verified

**Implementation evidence:**

| Requirement | Location | Verified |
|-------------|----------|----------|
| `is_verified` field | `app/models.py` line 76 | ✅ |
| `verification_doc` FileField | `app/models.py` lines 77–81 | ✅ |
| Auto-verify Trader/Admin in `save()` | `app/models.py` lines 88–98 | ✅ |
| Registration form conditional upload | `app/forms.py` `RegistrationForm` | ✅ |
| Admin `verify_users` bulk action | `app/admin.py` lines 44–57 | ✅ |
| Migration 0004 | `app/migrations/0004_user_is_verified_user_verification_doc.py` | ✅ |
| Seed users `is_verified=True` | `app/migrations/0002_seed_default_users.py` | ✅ |

---

### Item 2: Email Login ✅

**done.txt requirement:**
- Login uses email + password (not username)
- `USERNAME_FIELD = 'email'`
- Login form shows "Email" field
- Error messages reference email

**Implementation evidence:**

| Requirement | Location | Verified |
|-------------|----------|----------|
| `USERNAME_FIELD = 'email'` | `app/models.py` line 57 | ✅ |
| Unique required email | `app/models.py` line 68 | ✅ |
| `LoginForm` with email field | `app/forms.py` `LoginForm` | ✅ |
| Login view uses email auth | `app/views.py` `LoginView` | ✅ |
| Migration 0003 (email unique) | `app/migrations/0003_alter_user_email.py` | ✅ |
| Login template | `app/templates/app/auth/login.html` | ✅ |

---

### Item 3: Admin Account / Seed Users ✅

**done.txt requirement:** Four pre-seeded accounts with documented credentials.

| Role | Email | Password | Username | Verified |
|------|-------|----------|----------|----------|
| Admin | admin@cardetrade.in | admin123 | admin | ✅ |
| PM | pm@cardetrade.in | pm123 | pm1 | ✅ |
| Farmer | farmer@cardetrade.in | farmer123 | farmer1 | ✅ |
| Trader | trader@cardetrade.in | trader123 | trader1 | ✅ |

**Implementation evidence:** `app/migrations/0002_seed_default_users.py`, `user.md`, `README.md`

---

### Item 4: Cinematic Background System ✅

**done.txt requirement:**
- 4-layer CSS background: bg.gif → ambient orbs → film grain → cream veil
- bg.gif on hero and homepage sections
- No zoomed hero image effects
- Consistent animated backdrop

**Implementation evidence:**

| Layer | Location | Verified |
|-------|----------|----------|
| bg.gif hero overlay | `home.html`, `static/image/bg.gif` | ✅ |
| Ambient orbs | `base.html` `.ambient-orbs`, `style.css` | ✅ |
| Film grain | `base.html` `.grain-overlay`, `style.css` | ✅ |
| Cream veil / body layers | `style.css` `body::before/::after` | ✅ |
| Section padding backdrop | `style.css` `.section-padding` | ✅ |
| Keyframes (bgCinema, orbDrift, grainShift) | `style.css` | ✅ |

---

### Item 5: Documentation ✅

**done.txt requirement:** README, deploy.md, handoff.md, done.txt updated.

| Document | Exists | Current |
|----------|--------|---------|
| `README.md` | ✅ | Email login, verification, seed accounts |
| `deploy.md` | ✅ | Render deployment guide |
| `handoff.md` | ✅ | This document (v2.0) |
| `done.txt` | ✅ | Completion checklist |
| `docs/` (6 files) | ✅ | Architecture, models, workflows, API, templates, setup |

---

### Item 6: Migrations ✅

| Migration | Purpose | Verified |
|-----------|---------|----------|
| `0001_initial` | All 16 tables | ✅ |
| `0002_seed_default_users` | 4 seed accounts | ✅ |
| `0003_alter_user_email` | Email unique constraint | ✅ |
| `0004_user_is_verified_user_verification_doc` | Verification fields | ✅ |

---

### Item 7: Animation Revamp ✅

**done.txt requirement:**
- Removed: confetti, heartbeat pulse, morphBlob
- Counter uses `requestAnimationFrame`
- Table hover uses CSS class toggle
- Cleaned up CSS keyframes

**Implementation evidence:**

| Change | Location | Verified |
|--------|----------|----------|
| rAF counter animation | `static/js/main.js` | ✅ |
| Table hover CSS class | `static/js/main.js` + `style.css` | ✅ |
| Removed low-quality effects | `style.css` (no morphBlob/confetti keyframes) | ✅ |
| Retained: bgCinema, orbDrift, grainShift | `style.css` | ✅ |

---

### Item 8: Messaging Fix ✅

**done.txt requirement:**
- Created missing `conversation_create.html` (was 404)
- Verified `conversation_detail.html` renders

**Implementation evidence:**

| Template | Path | Verified |
|----------|------|----------|
| Conversation create | `app/templates/app/messaging/conversation_create.html` | ✅ |
| Conversation detail | `app/templates/app/messaging/conversation_detail.html` | ✅ |
| Conversation create view | `app/views.py` `ConversationCreateView` | ✅ |
| URL pattern | `conversations/create/<int:batch_pk>/` | ✅ |

---

### Item 9: Credentials Doc ✅

**done.txt requirement:** `user.md` with correct emails (no erroneous `1` before `@`).

**Implementation evidence:** `user.md` — emails are `pm@cardetrade.in`, `farmer@cardetrade.in`, `trader@cardetrade.in` (correct format).

> Minor note: `user.md` lists login URL as `/app/login/` but actual route is `/login/`.

---

### Pending Items (Acknowledged, Not Blocking "Done" Status)

These are explicitly listed in `done.txt` as future work and are **not** required for the current handoff:

| Item | Status | Notes |
|------|--------|-------|
| Payment gateway integration | ⏳ Future | Manual `Payment` model records exist |
| SMTP/email notifications | ⏳ Future | In-app `Notification` model works |
| WebSocket real-time messaging | ⏳ Future | Polling/refresh-based chat |
| Media storage on S3/Cloudinary | ⏳ Future | Local `media/` works in dev |
| REST API (DRF) | ⏳ Future | Server-rendered only |
| Comprehensive test coverage | ⏳ Future | Scaffold in `tests.py` |

---

### Post–done.txt Fixes (2026-07-09)

These were addressed after `done.txt` was written but before this handoff:

| Fix | Files | Status |
|-----|-------|--------|
| Multiline template comments leaking to UI | `home.html`, `listing_list.html`, `batches/list.html` | ✅ Fixed |
| Navbar "Get Started" button invisible text when active | `style.css`, `main.js` | ✅ Fixed |

---

### Final Completion Verdict

**The project is complete per `done.txt` criteria.** All 9 completed items have been verified against the codebase. The 6 pending items are appropriately scoped as future enhancements and do not represent incomplete core functionality.

The receiving team can take ownership with confidence that:

1. All core trading workflows (batch → verify → list → bid/buy → order) are implemented
2. All 16 database models, 28 views, and 30+ URL routes are in place
3. Authentication, verification, role enforcement, and admin tools are functional
4. Documentation is comprehensive and cross-referenced
5. Seed accounts allow immediate end-to-end testing without manual setup

---

*End of Handoff Document — CardeTrade v1.0*
