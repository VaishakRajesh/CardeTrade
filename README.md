# CardeTrade — Cardamom Trading Platform

Multi-role platform connecting cardamom farmers, traders, and product managers for verified trading.

## Quick Start

```bash
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Admin Access

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@cardetrade.in | admin123 |

all password:@Vaishak123
Login at `/accounts/login/`. Create more users via Django admin.

## Apps

| App | Purpose |
|-----|---------|
| `accounts` | Auth, profiles, messaging, disputes |
| `farmer` | Farm & batch management |
| `trader` | Listings, bids, orders, payments |
| `pm` | Quality verification |
| `panel` | Admin dashboard, PM approval |
| `chat` | AI chatbot assistant |

## Tech

Django 5, SQLite/PostgreSQL, Bootstrap 5, pure CSS/JS.
