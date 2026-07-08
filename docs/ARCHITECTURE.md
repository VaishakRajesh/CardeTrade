# Architecture Overview — CardeTrade

## Design Philosophy

- **Single Django app** (`app/`) — all models, views, forms, templates in one place
- **Role-based access control** — 4 roles: Farmer, Trader, Product Manager, Admin
- **Server-rendered HTML** with Bootstrap 5 + custom CSS (no SPA, no REST API)
- **Signal-driven automation** — batch verification auto-creates listings, state changes trigger notifications

## Request Flow

```
Browser → Django URL Router → Middleware (Auth, Audit) → View → Model → Template → HTML Response
```

1. URL matched in `cardetrade/urls.py` → `app/urls.py`
2. Middleware processes request (auth, audit logging)
3. `@role_required` decorator checks user role
4. View function/class executes business logic
5. Model queries/updates database
6. Template renders HTML with context
7. Response returned to browser

## Component Interaction

```
User (Browser)
  │
  ├── Templates/ ──── CSS/JS ──── Static Files
  │
  ├── Views ──── Forms ──── Validation
  │     │
  │     ├── Models ──── Database (SQLite/PostgreSQL)
  │     │
  │     └── Signals ──── Automated Actions
  │             │
  │             ├── Create Listing on Verify
  │             ├── Notify on Order/Bid/Dispute
  │             ├── Update Conversation Timestamp
  │             └── Audit Logging
  │
  └── Decorators ──── Role Enforcement
```

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Single app | Simpler deployment, no cross-app import issues |
| Custom CSS (no Tailwind) | Full control over premium animations and glass morphism |
| `GeneratedField` for `total_amount` | Database-computed, avoids race conditions |
| `TextChoices` over `IntegerChoices` | Human-readable database values |
| Soft delete only for Messages | Hard delete causes data loss; other tables use status |
| Signal-created Listings | Guarantees a Listing exists for every verified batch |
| `unique_together` instead of composite PK | Django lacks composite PK support |
| Notification polling (no WebSocket) | Simpler implementation for MVP |

## Directory Layout

```
CardeTrade/
├── cardetrade/          # Project settings, root URL conf
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── app/                 # Single Django app
│   ├── models.py        # 16 tables
│   ├── views.py         # 28+ views
│   ├── urls.py          # 30+ routes
│   ├── forms.py         # ModelForms + validation
│   ├── decorators.py    # Role enforcement
│   ├── signals.py       # Post-save hooks
│   ├── middleware.py    # Audit context
│   ├── admin.py         # Admin configs
│   └── templates/app/   # Feature-based template folders
├── static/              # CSS, JS, images
├── templates/           # Base templates, includes
└── docs/                # Documentation
```
