# Handoff Document — CardeTrade

## Project Overview

CardeTrade is a Django 5.2 web application for premium cardamom trading. It connects farmers, traders, and product managers through a transparent, verified marketplace with role-based access.

## Architecture

```
Python 3.11 + Django 5.2 + SQLite/PostgreSQL + Bootstrap 5.3
Pure CSS (~2000 lines) + Vanilla JS — no React, no Tailwind
```

## Key Design Decisions

### Authentication
- **Login via email** (not username) — `USERNAME_FIELD = 'email'`
- `User.save()` auto-sets `is_staff`/`is_superuser` based on `role`
- 4 roles: `farmer`, `trader`, `product_manager`, `admin`

### Verification System (NEW)
- Farmers and Product Managers must upload a verification document during registration
- Traders and Admin are auto-verified
- Admin can verify users via Django admin panel (`/admin/`) using the "Mark selected users as verified" action
- `is_verified` boolean + `verification_doc` FileField on User model

### Model Highlights
- 16 database tables in a single `app/models.py`
- `Order.total_amount` uses Django 5+ `GeneratedField` (computed column)
- Auto-generated codes: `Batch.batch_code` (`CDM-2026-0001`), `Order.order_code` (`ORD-2026-0001`)
- Soft delete only on `Message` — all other tables hard delete

### Key URLs

| URL Pattern | View | Access |
|------------|------|--------|
| `/` | HomeView | Public |
| `/register/` | RegisterView | Public |
| `/login/` | LoginView | Public |
| `/dashboard/` | DashboardRedirectView | Auth |
| `/admin/` | Django Admin | Staff |
| `/batches/` | BatchListView / CreateView | Farmer/PM |
| `/listings/` | ListingListView | Auth |
| `/orders/` | OrderListView | Auth |

### Decorators
- `@role_required('farmer', 'trader')` — CBV via `@method_decorator`
- Convenience variants: `farmer_required`, `trader_required`, `pm_required`, `admin_required`, `staff_required`

### Signals (automated workflows)
- Batch verified → auto-create Listing
- Order created → notify seller
- Bid placed → notify farmer
- Message sent → update conversation timestamp

### Background System
- 4-layer cinematic CSS background: bg.gif (animated) → ambient orbs → film grain → cream veil
- `body::before` (z-index: -4) through `body::after` (z-index: -1)
- bg.gif also applied to hero overlay and section-padding for consistent animated backdrop

## Seed Accounts

| Role | Username | Email | Password |
|------|----------|-------|----------|
| Admin | admin | admin@cardetrade.in | admin123 |
| PM | pm1 | pm@cardetrade.in | pm123 |
| Farmer | farmer1 | farmer@cardetrade.in | farmer123 |
| Trader | trader1 | trader@cardetrade.in | trader123 |

## State of the Project

### Working
- Full authentication (register, login, logout, profile) with email
- Role-based dashboards (farmer, trader, pm, admin)
- Batch CRUD with auto-code generation
- Quality verification with grade assignment
- Listing (fixed price + auction) with auto-creation on verification
- Bidding system with status workflow
- Order lifecycle with GeneratedField total
- Order tracking timeline
- Payment recording
- Dispute creation and resolution
- Messaging (conversations + soft-delete messages)
- Notifications (auto-generated on key events)
- Reports (placeholder structure)
- Audit logging middleware
- Premium UI with animations (scroll, counter via requestAnimationFrame, particles, 3D tilt, glass morphism)
- 4-layer animated background system
- Email-based login
- Role-based verification with document upload
- Conversation create template (was missing, now fixed)

### Animation Notes
- Counter uses `requestAnimationFrame` (smooth 60fps, no setInterval)
- Table hover uses CSS class toggle (no inline styles)
- Low-quality effects removed: confetti, heartbeat pulse, morphBlob
- Background system retained: bgCinema, orbDrift, grainShift

### Credentials (user.md)
- Admin: admin@cardetrade.in / admin123
- PM: pm@cardetrade.in / pm123
- Farmer: farmer@cardetrade.in / farmer123
- Trader: trader@cardetrade.in / trader123

### Needs Attention
- **Tests**: Some tests exist in `app/tests.py` but coverage is incomplete
- **Payment integration**: No real payment gateway connected (records payments manually)
- **Email sending**: SMTP not configured — notification emails not sent
- **Real-time messaging**: No WebSocket/ASGI — messages require page refresh
- **Media files**: Render free tier doesn't persist uploads — needs S3/Cloudinary
- **API**: No REST API (no DRF) — all server-rendered templates

## Quick Commands

```bash
# Development
python manage.py runserver

# Migrations
python manage.py makemigrations
python manage.py migrate

# Admin
python manage.py createsuperuser

# Tests
python manage.py test app.tests

# Check
python manage.py check
```

## Environment Variables (`.env`)

```ini
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
DATABASE_URL=sqlite:///db.sqlite3
```
