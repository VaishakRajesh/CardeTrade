# Database Schema — CardeTrade

## Overview

16 tables across a single `app` module. All enums use `models.TextChoices`. Every `ForeignKey` has an explicit `related_name`.

---

## Table: `app_user`

| Column | Type | Notes |
|--------|------|-------|
| id | BigAutoField | PK |
| password | VARCHAR(128) | Django hashed |
| last_login | DateTime | Nullable |
| is_superuser | Boolean | |
| username | VARCHAR(150) | Unique |
| first_name | VARCHAR(150) | |
| last_name | VARCHAR(150) | |
| email | VARCHAR(254) | |
| is_staff | Boolean | Auto-set on save |
| is_active | Boolean | |
| date_joined | DateTime | |
| role | VARCHAR(20) | farmer/trader/product_manager/admin |
| phone | VARCHAR(20) | |
| address | TEXT | |
| region | VARCHAR(100) | |

**Auto-behavior**: `save()` sets `is_staff`/`is_superuser` based on role:
- `admin` → both True
- `product_manager` → is_staff=True, is_superuser=False
- farmer/trader → both False

---

## Table: `app_farm`

| Column | Type | Notes |
|--------|------|-------|
| id | BigAutoField | PK |
| farmer_id | BigInt | FK → app_user, CASCADE |
| farm_name | VARCHAR(150) | |
| location | VARCHAR(200) | |
| region | VARCHAR(100) | |
| total_area_acres | Decimal(8,2) | Nullable |
| certification | VARCHAR(100) | |
| created_at | DateTime | auto_now_add |

---

## Table: `app_batch`

| Column | Type | Notes |
|--------|------|-------|
| id | BigAutoField | PK |
| batch_code | VARCHAR(50) | Unique, auto-generated |
| farmer_id | BigInt | FK → app_user, CASCADE |
| farm_id | BigInt | FK → app_farm, SET_NULL |
| quantity_kg | Decimal(10,2) | |
| harvest_date | Date | |
| description | TEXT | |
| estimated_price_per_kg | Decimal(10,2) | |
| status | VARCHAR(20) | pending/under_review/verified/listen/sold/rejected |
| created_at | DateTime | auto_now_add |
| updated_at | DateTime | auto_now |

**Batch code format**: `CDM-YYYY-NNNN` (auto-increment per year)

---

## Table: `app_qualityverification`

| Column | Type | Notes |
|--------|------|-------|
| id | BigAutoField | PK |
| batch_id | BigInt | FK → app_batch, CASCADE (OneToOne) |
| product_manager_id | BigInt | FK → app_user, SET_NULL |
| grade | VARCHAR(1) | A/B/C |
| moisture_content_pct | Decimal(5,2) | Nullable |
| aroma_score | SmallInt | 1-10, Nullable |
| color_score | SmallInt | 1-10, Nullable |
| purity_pct | Decimal(5,2) | Nullable |
| verified_price_per_kg | Decimal(10,2) | |
| remarks | TEXT | |
| verified_at | DateTime | auto_now_add |

---

## Table: `app_listing`

| Column | Type | Notes |
|--------|------|-------|
| id | BigAutoField | PK |
| batch_id | BigInt | FK → app_batch, CASCADE (OneToOne) |
| farmer_id | BigInt | FK → app_user, CASCADE |
| listing_type | VARCHAR(20) | fixed_price/auction |
| price_per_kg | Decimal(10,2) | |
| min_order_kg | Decimal(10,2) | Nullable |
| available_qty_kg | Decimal(10,2) | |
| auction_start_time | DateTime | Nullable |
| auction_end_time | DateTime | Nullable |
| is_active | Boolean | default=True |
| created_at | DateTime | auto_now_add |

---

## Table: `app_bid`

| Column | Type | Notes |
|--------|------|-------|
| id | BigAutoField | PK |
| listing_id | BigInt | FK → app_listing, CASCADE |
| trader_id | BigInt | FK → app_user, CASCADE |
| bid_price_per_kg | Decimal(10,2) | |
| quantity_kg | Decimal(10,2) | |
| status | VARCHAR(10) | active/accepted/rejected/outbid/expired |
| notes | TEXT | |
| bid_time | DateTime | auto_now_add |

---

## Table: `app_order`

| Column | Type | Notes |
|--------|------|-------|
| id | BigAutoField | PK |
| order_code | VARCHAR(50) | Unique, auto-generated |
| listing_id | BigInt | FK → app_listing, SET_NULL |
| batch_id | BigInt | FK → app_batch, SET_NULL |
| buyer_id | BigInt | FK → app_user, CASCADE |
| seller_id | BigInt | FK → app_user, CASCADE |
| bid_id | BigInt | FK → app_bid, SET_NULL |
| quantity_kg | Decimal(10,2) | |
| price_per_kg | Decimal(10,2) | |
| total_amount | Decimal(12,2) | **GeneratedField** (computed: qty × price) |
| status | VARCHAR(20) | pending/confirmed/processing/shipped/delivered/cancelled/disputed |
| payment_status | VARCHAR(20) | unpaid/partially_paid/paid/refunded |
| created_at | DateTime | auto_now_add |
| updated_at | DateTime | auto_now |

**Order code format**: `ORD-YYYY-NNNN` (auto-increment per year)

---

## Table: `app_ordertracking`

| Column | Type | Notes |
|--------|------|-------|
| id | BigAutoField | PK |
| order_id | BigInt | FK → app_order, CASCADE |
| status | VARCHAR(20) | |
| location | VARCHAR(200) | |
| notes | TEXT | |
| updated_by_id | BigInt | FK → app_user, SET_NULL |
| tracked_at | DateTime | auto_now_add |

---

## Table: `app_payment`

| Column | Type | Notes |
|--------|------|-------|
| id | BigAutoField | PK |
| order_id | BigInt | FK → app_order, CASCADE |
| payer_id | BigInt | FK → app_user, SET_NULL |
| amount | Decimal(12,2) | |
| payment_method | VARCHAR(20) | bank_transfer/mobile_money/cash/escrow |
| transaction_ref | VARCHAR(100) | Unique, Nullable |
| status | VARCHAR(10) | pending/completed/failed/refunded |
| paid_at | DateTime | Nullable |
| created_at | DateTime | auto_now_add |

---

## Table: `app_dispute`

| Column | Type | Notes |
|--------|------|-------|
| id | BigAutoField | PK |
| order_id | BigInt | FK → app_order, CASCADE |
| raised_by_id | BigInt | FK → app_user, CASCADE |
| against_user_id | BigInt | FK → app_user, CASCADE |
| reason | TEXT | |
| status | VARCHAR(20) | open/under_review/resolved/closed |
| resolution | TEXT | |
| resolved_by_id | BigInt | FK → app_user, SET_NULL |
| created_at | DateTime | auto_now_add |
| resolved_at | DateTime | Nullable |

---

## Table: `app_notification`

| Column | Type | Notes |
|--------|------|-------|
| id | BigAutoField | PK |
| user_id | BigInt | FK → app_user, CASCADE |
| type | VARCHAR(30) | bid_received/bid_accepted/order_placed/order_shipped/payment_received/batch_verified/dispute_raised |
| message | TEXT | |
| reference_id | Int | Nullable |
| reference_type | VARCHAR(50) | |
| is_read | Boolean | default=False |
| created_at | DateTime | auto_now_add |

---

## Table: `app_conversation`

| Column | Type | Notes |
|--------|------|-------|
| id | BigAutoField | PK |
| batch_id | BigInt | FK → app_batch, SET_NULL |
| order_id | BigInt | FK → app_order, SET_NULL |
| type | VARCHAR(20) | quality_review/batch_inquiry/order_support/general |
| subject | VARCHAR(200) | |
| status | VARCHAR(10) | open/archived/locked |
| created_at | DateTime | auto_now_add |
| last_message_at | DateTime | Nullable |

---

## Table: `app_conversationparticipant`

| Column | Type | Notes |
|--------|------|-------|
| id | BigAutoField | PK |
| conversation_id | BigInt | FK → app_conversation, CASCADE |
| user_id | BigInt | FK → app_user, CASCADE |
| role_in_chat | VARCHAR(20) | farmer/product_manager/trader/admin |
| joined_at | DateTime | auto_now_add |
| last_read_at | DateTime | Nullable |
| is_muted | Boolean | default=False |
| is_active | Boolean | default=True |

**Constraint**: `unique_together = (conversation, user)`

---

## Table: `app_message`

| Column | Type | Notes |
|--------|------|-------|
| id | BigAutoField | PK |
| conversation_id | BigInt | FK → app_conversation, CASCADE |
| sender_id | BigInt | FK → app_user, SET_NULL |
| message_type | VARCHAR(10) | text/image/document/system |
| content | TEXT | |
| attachments | JSON | default=list |
| is_edited | Boolean | default=False |
| edited_at | DateTime | Nullable |
| is_deleted | Boolean | default=False, **soft delete** |
| deleted_at | DateTime | Nullable |
| sent_at | DateTime | auto_now_add |

---

## Table: `app_report`

| Column | Type | Notes |
|--------|------|-------|
| id | BigAutoField | PK |
| generated_by_id | BigInt | FK → app_user, CASCADE |
| report_type | VARCHAR(30) | trade_summary/grade_distribution/farmer_performance/trader_activity/revenue |
| date_from | Date | Nullable |
| date_to | Date | Nullable |
| parameters | JSON | default=dict |
| file_path | VARCHAR(255) | |
| created_at | DateTime | auto_now_add |

---

## Table: `app_auditlog`

| Column | Type | Notes |
|--------|------|-------|
| id | BigAutoField | PK |
| user_id | BigInt | FK → app_user, SET_NULL |
| action | VARCHAR(100) | e.g., 'batch.verified' |
| table_name | VARCHAR(50) | |
| record_id | Integer | |
| old_value | JSON | Nullable |
| new_value | JSON | Nullable |
| ip_address | VARCHAR(45) | |
| logged_at | DateTime | auto_now_add |

**Indexes**: (table_name, record_id), (action), (user)
