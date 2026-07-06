# CardeTrade — Cardamom Trading Platform

A comprehensive digital marketplace connecting cardamom farmers, traders, and product managers for seamless, verified, and transparent trading.

## Overview

CardeTrade is a Django-based web platform that digitizes the entire cardamom trading lifecycle — from harvest registration and quality verification to listing, bidding, ordering, payment, and dispute resolution. Built with a role-based access system, it ensures each participant (Farmer, Trader, Product Manager, Admin) interacts only with the features relevant to their role.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CardeTrade Platform                        │
├─────────────────────────────────────────────────────────────┤
│  Django 5.2  |  SQLite (dev) / PostgreSQL (prod)  |  Bootstrap 5 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────┐  ┌──────────┐  ┌──────────┐  ┌───────────┐   │
│  │ Farmer  │  │  Trader  │  │  PM      │  │  Admin    │   │
│  │ Dashboard│  │ Dashboard│  │ Dashboard│  │ Dashboard │   │
│  └────┬────┘  └────┬─────┘  └────┬─────┘  └─────┬─────┘   │
│       │             │             │               │         │
│  ┌────▼─────────────▼─────────────▼───────────────▼────┐   │
│  │                  Role Enforcement                    │   │
│  │           (@role_required decorator)                 │   │
│  └───────────────────────┬─────────────────────────────┘   │
│                          │                                  │
│  ┌───────────────────────▼─────────────────────────────┐   │
│  │                  Core Business Logic                  │   │
│  │  Batches → Verification → Listings → Bids → Orders  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Role System

| Role | Description | Staff Access | Superuser |
|------|-------------|-------------|-----------|
| **Farmer** | Registers batches, manages farms, views bids, fulfills orders | No | No |
| **Trader** | Browses listings, places bids, purchases cardamom, tracks orders | No | No |
| **Product Manager** | Verifies batch quality, grades cardamom, manages listings | Yes | No |
| **Admin** | Full system control, dispute resolution, reports, user management | Yes | Yes |

## Database Schema (16 Tables)

### Core User & Farm
| Table | Purpose | Key Fields |
|-------|---------|------------|
| `User` | Extended auth user | role, phone, address, region |
| `Farm` | Farmer's farm profile | farmer (FK), farm_name, location, area |

### Batch Management
| Table | Purpose | Key Fields |
|-------|---------|------------|
| `Batch` | Cardamom harvest batch | batch_code, farmer (FK), quantity_kg, status |
| `QualityVerification` | PM quality assessment | batch (1-to-1), grade (A/B/C), scores, verified_price |
| `Listing` | Published batch for sale | batch (1-to-1), type (fixed/auction), price, availability |

### Trading
| Table | Purpose | Key Fields |
|-------|---------|------------|
| `Bid` | Trader's bid on auction | listing (FK), trader (FK), bid_price, quantity, status |
| `Order` | Completed purchase | buyer, seller, quantity, price, total_amount (GeneratedField) |

### Order Fulfillment
| Table | Purpose | Key Fields |
|-------|---------|------------|
| `OrderTracking` | Order status timeline | order (FK), status, location, updated_by |
| `Payment` | Payment records | order (FK), amount, method, transaction_ref, status |
| `Dispute` | Dispute resolution | order (FK), raised_by, against, reason, status |

### Communication
| Table | Purpose | Key Fields |
|-------|---------|------------|
| `Conversation` | Chat thread | type, subject, status, last_message_at |
| `ConversationParticipant` | Chat membership | conversation (FK), user (FK), role_in_chat |
| `Message` | Individual message (soft-delete) | conversation (FK), sender, content, attachments |
| `Notification` | System notifications | user (FK), type, message, reference, is_read |

### Analytics & Audit
| Table | Purpose | Key Fields |
|-------|---------|------------|
| `Report` | Generated analytics | report_type, date range, file_path |
| `AuditLog` | All state mutations | user, action, table_name, old/new values |

## Status Workflows

### Batch Lifecycle
```
Pending → Under Review → Verified → Listed → Sold
                          └→ Rejected
```

### Order Lifecycle
```
Pending → Confirmed → Processing → Shipped → Delivered
  └─────────────────────→ Cancelled
  └─────────────────────→ Disputed
```

### Bid Lifecycle
```
Active → Accepted | Rejected | Outbid | Expired
```

### Dispute Lifecycle
```
Open → Under Review → Resolved → Closed
```

## Key Business Rules

1. **R1**: ENUM fields use `TextChoices`, never `IntegerChoices`
2. **R2**: Every `ForeignKey` has an explicit `related_name`
3. **R3**: `total_amount` on Order is a `GeneratedField` (computed column)
4. **R4**: `AUTH_USER_MODEL = 'app.User'` is set before first migration
5. **R5**: Only `Message` supports soft delete
6. **R6**: Every state mutation is logged in `AuditLog`
7. **R7**: Product Manager has `is_staff=True` but `is_superuser=False`
8. **R8**: ENUM values are referenced via model class, never raw strings
9. **R9**: Farmers cannot bid. Traders cannot create batches. PMs cannot trade.

## Project Structure

```
CardeTrade/
├── cardetrade/              # Django project configuration
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py / asgi.py
├── app/                     # Single Django application (all logic)
│   ├── models.py            # All 16 database models
│   ├── views.py             # All platform views (CBVs)
│   ├── urls.py              # URL routing
│   ├── forms.py             # Registration, Login, Profile forms
│   ├── decorators.py        # Role-based access decorators
│   ├── admin.py             # Admin panel configuration
│   ├── signals.py           # Post-save signal handlers
│   ├── middleware.py        # Audit logging middleware
│   ├── utils.py             # Helper functions
│   ├── tests.py             # Test cases
│   └── templates/app/       # Feature-organized templates
│       ├── auth/            # Authentication (login, register, profile)
│       │   ├── login.html
│       │   ├── register.html
│       │   └── profile.html
│       ├── dashboard/       # Role-specific dashboards
│       │   ├── home.html      # Landing page
│       │   ├── farmer.html    # Farmer dashboard
│       │   ├── trader.html    # Trader dashboard
│       │   ├── pm.html        # Product Manager dashboard
│       │   └── admin.html     # Admin dashboard
│       ├── batches/         # Batch management
│       │   ├── list.html
│       │   ├── create.html
│       │   ├── detail.html
│       │   └── verify.html
│       ├── trading/         # Trading & bidding
│       │   ├── listing_list.html
│       │   ├── listing_detail.html
│       │   ├── place_bid.html
│       │   ├── direct_buy.html
│       │   └── my_bids.html
│       ├── orders/          # Order management
│       │   ├── list.html
│       │   └── detail.html
│       └── farms/           # Farm management
│           ├── list.html
│           └── create.html
├── templates/               # Shared templates
│   ├── base.html            # Bootstrap 5 base template
│   └── includes/            # Reusable partials
│       ├── navbar.html
│       ├── alerts.html
│       └── footer.html
├── static/                  # Static assets
│   ├── css/style.css        # Custom CSS (no Tailwind)
│   ├── js/main.js           # JavaScript
│   ├── cardamom1.jpg        # Hero image
│   └── cardamom2.jpg        # Secondary image
├── media/                   # User-uploaded files
│   ├── batch_images/
│   └── documents/
├── project.md               # This file — project documentation
├── README.md                # Quick start guide
├── AGENTS.md                # AI agent development instructions
├── requirements.txt
└── manage.py
```

## Tech Stack

| Technology | Version |
|------------|---------|
| Python | 3.11+ |
| Django | 5.2 |
| Bootstrap | 5.3 |
| SQLite | (dev) |
| PostgreSQL | (prod) |
| CSS | Pure CSS (no Tailwind) |

## Setup

```bash
# Clone & enter
git clone <repo-url>
cd CardeTrade

# Virtual environment
python -m venv venv
venv\Scripts\activate   # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Database setup
python manage.py makemigrations
python manage.py migrate

# Create superuser (Admin)
python manage.py createsuperuser
# Default: admin / admin123

# Run development server
python manage.py runserver
```

## API Endpoints

### Authentication
| URL | Method | Description | Access |
|-----|--------|-------------|--------|
| `/` | GET | Homepage / Landing page | Public |
| `/register/` | GET/POST | User registration | Public |
| `/login/` | GET/POST | User login | Public |
| `/logout/` | GET | Logout | Authenticated |
| `/profile/` | GET/POST | View/edit profile | Authenticated |

### Dashboards
| URL | Method | Description | Role |
|-----|--------|-------------|------|
| `/dashboard/` | GET | Role-based redirect | All |
| `/dashboard/farmer/` | GET | Farmer dashboard | Farmer |
| `/dashboard/trader/` | GET | Trader dashboard | Trader |
| `/dashboard/pm/` | GET | PM dashboard | Product Manager |
| `/dashboard/admin/` | GET | Admin dashboard | Admin |

### Batches
| URL | Method | Description | Role |
|-----|--------|-------------|------|
| `/batches/` | GET | List batches | All |
| `/batches/create/` | GET/POST | Create batch | Farmer |
| `/batches/<id>/` | GET | Batch detail | All |
| `/batches/<id>/verify/` | GET/POST | Verify batch | PM |

### Trading
| URL | Method | Description | Role |
|-----|--------|-------------|------|
| `/listings/` | GET | Browse listings | All |
| `/listings/<id>/` | GET | Listing detail | All |
| `/listings/<id>/bid/` | GET/POST | Place bid | Trader |
| `/listings/<id>/buy/` | GET/POST | Direct buy | Trader |
| `/bids/` | GET | My bids | Farmer/Trader |

### Orders & Farms
| URL | Method | Description | Role |
|-----|--------|-------------|------|
| `/orders/` | GET | Order list | All |
| `/orders/<id>/` | GET | Order detail | All |
| `/farms/` | GET | Farm list | Farmer |
| `/farms/create/` | GET/POST | Create farm | Farmer |

## Template Design

Templates use **Bootstrap 5** grid and components with custom CSS styling. Key design features:
- Custom CSS classes (`card-custom`, `btn-custom`, `stat-card`, `hero-wrapper`, etc.)
- Cardamom images (`cardamom1.jpg`, `cardamom2.jpg`) used in hero section and auth pages
- Responsive layout for desktop and mobile
- Role-based navigation with highlighted active links
- Toast-style alert messages
- Gradient-based stat cards with icons

## Testing

```bash
python manage.py test app.tests
```

## License

MIT
