# 🌿 CardeTrade — Premium Cardamom Trading Platform

> **Grade First, Trade Second.** A premium digital marketplace connecting cardamom farmers, traders, and product managers for transparent, verified, and fair trading.

<p align="center">
  <img src="static/image/cardamom1.jpg" alt="CardeTrade Hero" width="80%" style="border-radius:16px;box-shadow:0 20px 60px rgba(0,0,0,0.2);">
</p>

---

## ✨ Features at a Glance

| Category | Features |
|----------|----------|
| 🎨 **Premium UI/UX** | Glass morphism, parallax hero, 3D tilt cards, particle effects, floating images, scroll animations, counter animations, confetti, ripple effects |
| 🖼️ **Image-Rich Design** | Dual cardamom image hero, image galleries throughout, floating badges, gradient overlays on every page header |
| 🔐 **Role-Based Access** | Farmer, Trader, Product Manager, Admin — each with a custom dashboard and CRUD operations |
| 📊 **Complete Trading Lifecycle** | 16 database tables covering batch creation, quality verification, listing, bidding, ordering, payments, disputes, messaging |
| 🚀 **20+ Animations** | `fadeInUp`, `fadeInLeft/Right`, `scaleIn`, `floatUpDown`, `pulseGlow`, `shimmer`, `gradientShift`, `morphBlob`, `cardGlowBorder`, `rippleEffect`, `heartbeat`, `confettiFall` |
| 📱 **Fully Responsive** | Optimized for mobile, tablet, and desktop with 3 breakpoints |
| 💬 **Built-in Messaging** | Conversation threads, real-time chat interface, role-based participants |
| 🔄 **Automated Workflows** | Post-save signals: auto-create listings on verification, auto-notify on bids/orders |

---

## 🚀 Quick Start

```bash
# 1. Clone & enter
git clone <repo-url>
cd CardeTrade

# 2. Virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/Mac

# 3. Install dependencies
pip install -r requirements.txt

# 4. Database setup
python manage.py makemigrations
python manage.py migrate

# 5. Create admin account
python manage.py createsuperuser

# 6. Run development server
python manage.py runserver
```

### 🔑 Default Credentials
| Role | Username | Password |
|------|----------|----------|
| 🛡️ Admin | `admin` | `admin123` |

### 📌 Key URLs
| Page | URL | Access |
|------|-----|--------|
| 🏠 Homepage | `/` | Public |
| 📋 Register | `/register/` | Public |
| 🔑 Login | `/login/` | Public |
| ⚙️ Admin | `/admin/` | Staff |
| 📊 Dashboard | `/dashboard/` | Auth (auto-route) |
| 🛒 Marketplace | `/listings/` | Auth |
| 📦 Orders | `/orders/` | Auth |
| 💬 Messages | `/conversations/` | Auth |

---

## 🎨 Premium UI/UX Design System

### Color Palette
```
🌿 Primary Green:    #1a4d2e → #2d6a4f  (Deep forest greens)
🥇 Accent Gold:      #c8a951 → #d4af37  (Premium cardamom gold)
🍦 Background:       #faf3e0            (Warm cream)
🌑 Dark:             #0a1a10            (Deep dark green)
```

### CSS Architecture (Pure CSS — No Tailwind, No MUI)

The entire UI is hand-crafted CSS with **1000+ lines** of premium styles. No external UI libraries.

| Pattern | Implementation | Used In |
|---------|---------------|---------|
| **Glass Morphism** | `backdrop-filter: blur(28px) saturate(180%)` | Auth cards, navbar, modal backgrounds |
| **Gradient Overlays** | `linear-gradient(135deg, ...)` on `::after` | Hero, page headers, stat cards, buttons |
| **Parallax Effect** | `translateY(scroll * 0.12)` via JS | Hero background image |
| **3D Tilt Cards** | `perspective(1000px) rotateX/Y` via mousemove | All cards and listing cards |
| **Scroll Animations** | `IntersectionObserver` with opacity/transform | All `.animate-on-scroll` elements |
| **Floating Images** | `@keyframes floatUpDown` | Hero secondary image, particles |
| **Particle System** | JS-generated floating dots with random positions | Hero section background |
| **Counter Animation** | `setInterval` number stepping | Stat cards on all dashboards |
| **Gold Shimmer Text** | `background-size: 300%` with `@keyframes shimmer` | Hero title, brand logo |
| **Ripple Effect** | CSS `@keyframes rippleEffect` on click | All buttons |
| **Confetti** | `@keyframes confettiFall` with random colors | Success celebration button |
| **Card Glow** | `@keyframes cardGlowBorder` pulsing border | Cards on hover |

### Animation Catalog (25+ Keyframes)
```css
/* Entrance */
fadeInUp, fadeInDown, fadeInLeft, fadeInRight, scaleIn

/* Ambient */
floatUpDown, floatSlow, driftHorizontal, sway

/* Glow & Shimmer */
pulseGlow, pulseGlowGreen, shimmer, shimmerGold, gradientShift

/* Interactive */
cardGlowBorder, rippleEffect, heartbeat, spinSlow, morphBlob

/* Special */
typing, blink, confettiFall, rotateY, slideReveal
```

---

## 🗂️ Project Structure

```
CardeTrade/
│
├── cardetrade/                      # Django project config
│   ├── settings.py                  # AUTH_USER_MODEL, crispy, media
│   ├── urls.py                      # Root routing
│   └── wsgi.py / asgi.py            # Deployment entries
│
├── app/                             # Single app (all logic)
│   ├── models.py                    # 16 tables
│   ├── views.py                     # 28 class-based views
│   ├── urls.py                      # 30+ URL patterns
│   ├── forms.py                     # Registration, Login, Profile
│   ├── decorators.py                # @role_required system
│   ├── admin.py                     # All models registered
│   ├── signals.py                   # Auto-listing, notifications
│   ├── middleware.py                # Audit logging
│   │
│   └── templates/app/
│       ├── auth/                    # login, register, profile
│       ├── dashboard/               # home, farmer, trader, pm, admin
│       ├── batches/                 # list, create, detail, verify
│       ├── trading/                 # listing_list/detail, place_bid, direct_buy, my_bids
│       ├── orders/                  # list, detail
│       ├── farms/                   # list, create
│       ├── messaging/               # conversation_list/detail/create
│       ├── disputes/                # list, create, resolve
│       └── notifications/           # list
│
├── templates/                       # Shared templates
│   ├── base.html                    # Bootstrap 5 + preloader
│   └── includes/                    # navbar, alerts, footer
│
├── static/
│   ├── css/style.css                # 1000+ lines premium CSS
│   ├── js/main.js                   # All animations & interactions
│   └── image/
│       ├── cardamom1.jpg            # Hero primary / marketplace
│       └── cardamom2.jpg            # Hero secondary / philosophy
│
├── docs/                            # Documentation
│   ├── MODELS.md                    # Database schema
│   ├── WORKFLOW.md                  # Business workflows
│   ├── TEMPLATES.md                 # UI/UX design guide
│   ├── API.md                       # Endpoint reference
│   ├── ARCHITECTURE.md              # System architecture
│   └── SETUP.md                     # Setup & deployment
│
├── README.md                        # This file
├── AGENTS.md                        # AI agent instructions
├── requirements.txt                 # Dependencies
└── manage.py                        # Django CLI
```

---

## 👥 User Roles & Permissions

| Role | Description | Staff | Superuser | Key Actions |
|------|-------------|-------|-----------|-------------|
| 🌾 **Farmer** | Sell cardamom | ❌ | ❌ | Create farms, batches, view bids, fulfill orders |
| 📦 **Trader** | Buy cardamom | ❌ | ❌ | Browse listings, place bids, buy, track orders |
| ✅ **Product Manager** | Verify quality | ✅ | ❌ | Grade batches, set prices, manage pipeline |
| 🛡️ **Admin** | Full control | ✅ | ✅ | Manage users, resolve disputes, system oversight |

---

## 🗄️ Database (16 Tables)

| # | Table | Key Purpose |
|---|-------|-------------|
| 1 | `User` | Extended auth with role, phone, region |
| 2 | `Farm` | Farm profile linked to farmer |
| 3 | `Batch` | Cardamom harvest with auto-generated code |
| 4 | `QualityVerification` | Grade assessment (A/B/C) |
| 5 | `Listing` | Published batch (fixed price / auction) |
| 6 | `Bid` | Auction bids with status workflow |
| 7 | `Order` | Purchase with **GeneratedField** total |
| 8 | `OrderTracking` | Status timeline |
| 9 | `Payment` | Payment records |
| 10 | `Dispute` | Dispute resolution |
| 11 | `Conversation` | Chat threads |
| 12 | `ConversationParticipant` | Chat membership |
| 13 | `Message` | Messages (soft delete) |
| 14 | `Notification` | System notifications |
| 15 | `Report` | Analytics reports |
| 16 | `AuditLog` | All state mutations logged |

---

## 🔄 Business Workflows

```
Batch:     Pending → Under Review → Verified (auto-listing) → Listed → Sold / Rejected
Order:     Pending → Confirmed → Processing → Shipped → Delivered
           └──────────────────────────────────────→ Cancelled / Disputed
Bid:       Active → Accepted / Rejected / Outbid / Expired
Dispute:   Open → Under Review → Resolved → Closed
```

### Automatic Actions (Signals)
- ✅ **Batch Verified** → Auto creates marketplace Listing
- 📩 **Order Created** → Notification sent to seller
- 🔨 **Bid Placed** → Notification sent to farmer
- 💬 **Message Sent** → Conversation timestamp updated

---

## 🛣️ All Endpoints

### Authentication
| URL | Method | Role |
|-----|--------|------|
| `/` | GET | Public |
| `/register/` | GET/POST | Public |
| `/login/` | GET/POST | Public |
| `/logout/` | GET | Auth |
| `/profile/` | GET/POST | Auth |

### Dashboards (Role-Based)
| URL | Role |
|-----|------|
| `/dashboard/` | All (auto-redirect) |
| `/dashboard/farmer/` | Farmer |
| `/dashboard/trader/` | Trader |
| `/dashboard/pm/` | PM |
| `/dashboard/admin/` | Admin |

### Batches & Trading
| URL | Method | Role |
|-----|--------|------|
| `/batches/` | GET | All |
| `/batches/create/` | GET/POST | Farmer |
| `/batches/<id>/verify/` | GET/POST | PM |
| `/listings/` | GET | All |
| `/listings/<id>/` | GET | All |
| `/listings/<id>/bid/` | GET/POST | Trader |
| `/listings/<id>/buy/` | POST | Trader |

### Communication & Support
| URL | Method | Role |
|-----|--------|------|
| `/conversations/` | GET | All |
| `/disputes/` | GET | All |
| `/disputes/create/<order_id>/` | GET/POST | Buyer/Seller |
| `/notifications/` | GET | All |

---

## 🧪 Testing

```bash
python manage.py test app.tests
```

---

## 📦 Tech Stack

| Technology | Version |
|------------|---------|
| Python | 3.11+ |
| Django | 5.2 |
| Database | SQLite (dev) / PostgreSQL (prod) |
| CSS | Pure CSS (1000+ lines, no frameworks) |
| JavaScript | Vanilla JS (no frameworks) |
| UI Library | Bootstrap 5.3 (minimal, grid only) |
| Icons | Bootstrap Icons 1.11 |
| Images | 2 premium cardamom photos |

---

## 📸 Premium Page Showcase

| Page | Highlights |
|------|-----------|
| 🏠 **Homepage** | Full-viewport parallax hero, dual cardamom images, floating particles, gold shimmer text, animated counters, feature cards with 3D tilt, image gallery, philosophy section |
| 🔑 **Login/Register** | Full-screen blurred cardamom background, glass morphism card (backdrop-filter: blur 28px), floating logo, premium form inputs with gold focus |
| 📊 **Dashboards** | Role-dedicated stats with gradient cards, image-backed page headers, premium tables with hover effects, quick action cards |
| 🛒 **Marketplace** | Card grid with image zoom, type badges (auction/fixed), grade badges (A/B/C circular), hover tilt, price emphasis |
| 💬 **Messaging** | Chat bubble interface, sent/received styling, auto-scroll, participant avatars |
| ⚖️ **Disputes** | Status timeline, resolution form, order context sidebar |

---

## 📜 License

MIT — Built for the cardamom trading community.
