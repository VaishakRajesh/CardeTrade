# API Reference — CardeTrade

All endpoints are server-rendered HTML pages (no REST API). URL prefix: `/app/`

---

## Authentication

| Method | URL | Name | Access | Template |
|--------|-----|------|--------|----------|
| GET/POST | `register/` | `app:register` | Anonymous | `app/auth/register.html` |
| GET/POST | `login/` | `app:login` | Anonymous | `app/auth/login.html` |
| GET | `logout/` | `app:logout` | Authenticated | Redirect |
| GET/POST | `profile/` | `app:profile` | Authenticated | `app/auth/profile.html` |

---

## Dashboard

| Method | URL | Name | Access | Template |
|--------|-----|------|--------|----------|
| GET | `` | `app:home` | Authenticated | `app/dashboard/home.html` |
| GET | `dashboard/farmer/` | `app:farmer_dashboard` | Farmer | `app/dashboard/farmer.html` |
| GET | `dashboard/trader/` | `app:trader_dashboard` | Trader | `app/dashboard/trader.html` |
| GET | `dashboard/pm/` | `app:pm_dashboard` | PM | `app/dashboard/pm.html` |
| GET | `dashboard/admin/` | `app:admin_dashboard` | Admin | `app/dashboard/admin.html` |

---

## Farms

| Method | URL | Name | Access | Template |
|--------|-----|------|--------|----------|
| GET/POST | `farms/create/` | `app:farm_create` | Farmer | `app/farms/create.html` |
| GET | `farms/` | `app:farm_list` | Farmer | `app/farms/list.html` |

---

## Batches

| Method | URL | Name | Access | Template |
|--------|-----|------|--------|----------|
| GET | `batches/` | `app:batch_list` | Farmer, PM, Admin | `app/batches/list.html` |
| GET/POST | `batches/create/` | `app:batch_create` | Farmer | `app/batches/create.html` |
| GET | `batches/<pk>/` | `app:batch_detail` | Farmer, PM, Admin | `app/batches/detail.html` |
| GET/POST | `batches/<pk>/verify/` | `app:batch_verify` | PM | `app/batches/verify.html` |

---

## Trading (Listings & Bids)

| Method | URL | Name | Access | Template |
|--------|-----|------|--------|----------|
| GET | `listings/` | `app:listing_list` | Trader, PM | `app/trading/listing_list.html` |
| GET | `listings/<pk>/` | `app:listing_detail` | Trader, PM | `app/trading/listing_detail.html` |
| GET/POST | `listings/<pk>/bid/` | `app:place_bid` | Trader | `app/trading/place_bid.html` |
| GET/POST | `listings/<pk>/buy/` | `app:direct_buy` | Trader | `app/trading/direct_buy.html` |
| GET | `bids/` | `app:my_bids` | Trader | `app/trading/my_bids.html` |

---

## Orders

| Method | URL | Name | Access | Template |
|--------|-----|------|--------|----------|
| GET | `orders/` | `app:order_list` | Farmer, Trader, PM | `app/orders/list.html` |
| GET | `orders/<pk>/` | `app:order_detail` | Farmer, Trader, PM | `app/orders/detail.html` |

---

## Messaging

| Method | URL | Name | Access | Template |
|--------|-----|------|--------|----------|
| GET | `conversations/` | `app:conversation_list` | Authenticated | `app/messaging/conversation_list.html` |
| GET/POST | `conversations/<pk>/` | `app:conversation_detail` | Participant | `app/messaging/conversation_detail.html` |
| GET/POST | `conversations/create/` | `app:conversation_create` | Authenticated | `app/messaging/conversation_list.html` |

---

## Disputes

| Method | URL | Name | Access | Template |
|--------|-----|------|--------|----------|
| GET/POST | `disputes/create/<order_pk>/` | `app:dispute_create` | Farmer, Trader | `app/disputes/create.html` |
| GET | `disputes/` | `app:dispute_list` | Authenticated | `app/disputes/list.html` |
| GET/POST | `disputes/<pk>/resolve/` | `app:dispute_resolve` | PM, Admin | `app/disputes/resolve.html` |

---

## Notifications

| Method | URL | Name | Access | Template |
|--------|-----|------|--------|----------|
| GET | `notifications/` | `app:notification_list` | Authenticated | `app/notifications/list.html` |
| POST | `notifications/mark-read/<pk>/` | `app:notification_mark_read` | Authenticated | Redirect |
