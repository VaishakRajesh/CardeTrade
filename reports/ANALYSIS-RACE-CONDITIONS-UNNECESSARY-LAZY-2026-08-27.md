# CardeTrade — User-Side Race Conditions, Unnecessary Code & Lazy/Weird Functions Analysis

- **Date:** 2026-08-27
- **Project:** CardeTrade — Cardamom Trading Platform (Django 5.x, Python 3.11+, SQLite dev / PostgreSQL prod)
- **Scope:** User-facing write paths: `farmer`, `trader`, `pm`, `panel`, `accounts`, `chat` + `cardetrade/settings.py` and shared middleware/signals/templates
- **Analyst:** Muse Spark (OpenCode) — static audit via two explore subagents + direct file reads; agent shell unavailable so `manage.py check / pytest / runserver` not executed
- **Related docs:** `AGENTS.md` (R1–R13), `reports/CHANGE-REPORT-*.md`

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [How Race Conditions Happen in Django (Primer)](#2-how-race-conditions-happen-in-django-primer)
3. [Race Conditions — User Side (12 Findings)](#3-race-conditions--user-side-12-findings)
   - [R1 — Batch Code `last()+1`](#r1--farmer-models-py-76-89-batch-code-last1--high)
   - [R2 — Order Code `last()+1`](#r2--trader-models-py-155-168-order-code-last1--high)
   - [R3 — Listing Auto-Creation Signal](#r3--farmer-signals-py-15-37-listing-auto-creation--high)
   - [R4 — PlaceBid No Lock](#r4--trader-views-py-71-98-placebid-no-lock--high)
   - [R5 — MakePayment Double Payment](#r5--trader-views-py-132-172-makepayment-double-payment--high)
   - [R6 — AcceptBid Oversell](#r6--farmer-views-py-154-203-acceptbid-oversell--high)
   - [R7 — Dispute Create Lost Update](#r7--accounts-views-py-235-255-dispute-create-lost-update--medium)
   - [R8 — Conversation Create Triple Insert](#r8--accounts-views-py-191-225-conversation-create-triple-insert--medium)
   - [R9 — Dispute Resolve Overwrite](#r9--panel-views-py-160-188-dispute-resolve-overwrite--medium)
   - [R10 — PM Approve/Revoke TOCTOU](#r10--panel-views-py-114-250-pm-approvereject-and-user-revokereactivate-toctou--medium)
   - [R11 — Conversation `last_message_at` Lost Update](#r11--accounts-signals-py-18-23-conversation-last_message_at-lost-update--medium)
   - [R12 — OrderTracking Status Drift](#r12--trader-views-py-185-209-ordertracking-status-drift--medium)
4. [Unnecessary / Dead / Duplicate Code](#4-unnecessary--dead--duplicate-code)
5. [Lazy / Weird Function Misuse](#5-lazy--weird-function-misuse)
6. [Summary Tables](#6-summary-tables)
7. [Why These Matter Together](#7-why-these-matter-together)
8. [Recommended Fix Roadmap (Phased)](#8-recommended-fix-roadmap-phased)
9. [How to Verify Fixes](#9-how-to-verify-fixes)
10. [Glossary](#10-glossary)
11. [Appendix — File Reference](#11-appendix--file-reference)

---

## 1. Executive Summary

**What was audited:** Every user-facing mutation — creating batches, verifying as PM, listing creation, bidding, accepting bids / direct buy, paying, tracking orders, raising/resolving disputes, creating conversations/messages, approving PM accounts, revoking users, plus shared `lazy` patterns (`reverse_lazy` vs `reverse`, `gettext_lazy`, `cached_property`, queryset laziness).

**What is correct:** Only two flows currently use `transaction.atomic()` + `select_for_update()` correctly:
- `pm/views.py:BatchVerifyView.post` — locks the `Batch` row before setting `VERIFIED` and creating a `Listing`.
- `pm/views.py:StartReviewView.post` — locks before setting `UNDER_REVIEW` (claim). Its `AuditLog` is however outside the `atomic` block — low-severity gap.

**What is broken:** Every other write path is **unlocked**. The most load-bearing bugs are sequential code generators that read `MAX(code)` then `+1` without a lock — they work 99% of the time but fail with `500 IntegrityError` when two users hit the same button within the same second. Payment double-click can double-charge because there is no idempotency check under a lock. Bids can land on expired/inactive listings. Accepting two bids on the same listing can oversell inventory (e.g. 100 kg stock → two 60 kg orders = 120 kg). All races are hidden on SQLite dev (where `select_for_update()` is a no-op) and only surface under real concurrent traffic or on PostgreSQL prod.

**Also found:** Dead wrappers (`get_model()` that `ListView` never calls), redundant `LoginRequiredMixin` + `role_required` double guards, a hand-rolled cache that reinvents `@cached_property`, unused imports (`Avg, Min, Max, Q`), an orphan template (`panel/templates/panel/pm_pending.html`), `reverse_lazy` used inside methods where `reverse` is correct (8 sites), a dynamically-built `ModelForm` inside a view method, a signal factory that registers with string senders and therefore **never fires**, and a `tz.timedelta` bug that raises `AttributeError` the moment a batch is verified.

**Bottom line:** Fix the six `High` races first, then the `Medium` ones, then clean up the lazy/dead code. No migration is needed for the cleanup phase; the race fixes need small model/view/signal patches plus `IntegrityError` retry for code generation.

---

## 2. How Race Conditions Happen in Django (Primer)

If you are new to race conditions, this section explains the pattern in plain language.

### 2.1 The TOCTOU pattern (Time-Of-Check to Time-Of-Use)

```python
# Step 1 — CHECK: is the listing still active?
if listing.is_active:  # read from DB
    # Step 2 — 10 ms later, another user deactivates the same listing
    # Step 3 — USE: you still think is_active is True and create a Bid
    Bid.objects.create(listing=listing, ...)
```

Between the check and the use, another request changes the row. Your local copy is stale. In Django this almost always looks like:

```python
last = Batch.objects.filter(batch_code__startswith='CDM-2026-').order_by('batch_code').last()
new_code = f'CDM-2026-{int(last.batch_code.split("-")[2])+1:04d}'  # read MAX
Batch.objects.create(batch_code=new_code)                            # use MAX+1
```

Two concurrent requests both read the same `last`, both compute the same `new_code`, one `INSERT` succeeds, the other hits `UNIQUE constraint failed`.

### 2.2 Django's tools to fix it

| Tool | What it does | When to use |
|------|--------------|-------------|
| `with transaction.atomic():` | Groups several queries into one DB transaction — all succeed or all roll back | Any multi-step write (check + write, create listing + update batch, create payment + update order) |
| `Model.objects.select_for_update().get(pk=...)` | Locks the row so no other transaction can read it until you commit | When you need to read then write the same row (auction listing, order, batch claim) |
| `F('field') - value` | Does arithmetic inside the DB instead of Python | Decrementing `available_qty_kg`; avoids stale read |
| `IntegrityError` retry | The `unique=True` constraint is the final safety net; catch it and retry with next code | Sequential code generators |
| `unique_together` / partial unique index | Enforce "one active payment per order" etc. at DB level | Payment idempotency |

**Important caveat:** `select_for_update()` is **ignored by SQLite** (the dev DB `db.sqlite3`). Races are invisible locally and only appear on PostgreSQL prod or under real concurrent load/double-clicks.

---

## 3. Race Conditions — User Side (12 Findings)

### R1 — `farmer/models.py:76-89` Batch Code `last()+1` — **High**

```python
# farmer/models.py:76-89
def save(self, *args, **kwargs):
    if not self.batch_code:
        self.batch_code = self._generate_batch_code()
    super().save(*args, **kwargs)

def _generate_batch_code(self):
    year = timezone.now().year
    last = Batch.objects.filter(batch_code__startswith=f'CDM-{year}-').order_by('batch_code').last()
    if last:
        num = int(last.batch_code.split('-')[2]) + 1
    else:
        num = 1
    return f'CDM-{year}-{num:04d}'
```

**What is weird:** No `transaction.atomic()`, no row lock, no `F()`. The only protection is `batch_code = CharField(unique=True)` which turns a race into a `500`.

**Scenario:** Farmer A and Farmer B both `POST /farmer/batches/create/` at 10:00:00.100. Both read `last = CDM-2026-0005`, both compute `CDM-2026-0006`, one `INSERT` succeeds, the other raises `IntegrityError: UNIQUE constraint failed: farmer_batch.batch_code`.

**User-visible effect:** One farmer sees `500 Server Error`, must retry. If the view does not catch `IntegrityError`, the batch is lost.

**Fix pattern:**
```python
from django.db import transaction, IntegrityError

def save(self, *args, **kwargs):
    if not self.batch_code:
        for attempt in range(3):
            try:
                with transaction.atomic():
                    # lock the max row (or use SELECT ... FOR UPDATE on a counter table)
                    last = Batch.objects.select_for_update().filter(
                        batch_code__startswith=f'CDM-{year}-'
                    ).order_by('batch_code').last()
                    self.batch_code = f'CDM-{year}-{(int(last.batch_code.split("-")[2])+1) if last else 1:04d}'
                    return super().save(*args, **kwargs)
            except IntegrityError:
                if attempt == 2: raise
                continue
    return super().save(*args, **kwargs)
```
Alternatively: a dedicated `BatchCounter(year, next_num)` table with `F('next_num')+1` under lock, or a DB sequence.

---

### R2 — `trader/models.py:155-168` Order Code `last()+1` — **High**

Identical pattern to R1, inside `Order`:

```python
# trader/models.py:155-168 (same shape)
def _generate_order_code(self):
    last = Order.objects.filter(order_code__startswith=f'ORD-{year}-').order_by('order_code').last()
    ...
    return f'ORD-{year}-{num:04d}'
```

Called from `farmer/views.py:AcceptBidView.post:184` `Order.objects.create(...)` inside `transaction.atomic()` but **without** locking the `Order` table, so the lock on the `Listing` does not serialize `order_code` generation across different listings.

**Scenario:** Farmer accepts a bid on Listing 1 and concurrently (second tab) accepts on Listing 2. Both compute `ORD-2026-0010` → one `IntegrityError` rolls back the whole `AcceptBidView` atomic block, the bid stays `ACTIVE` but the farmer sees `500`.

**Fix:** Same `select_for_update` + retry as R1, or a counter table.

---

### R3 — `farmer/signals.py:15-37` Listing Auto-Creation — **High**

```python
# farmer/signals.py:15-37
@receiver(post_save, sender=Batch)
def create_listing_on_verification(sender, instance, created, **kwargs):
    if instance.status == Batch.Status.VERIFIED:
        verification = instance.verification  # may raise RelatedObjectDoesNotExist
        Listing.objects.get_or_create(batch=instance, defaults={...})
        instance.status = Batch.Status.LISTED
        instance.save(update_fields=['status'])
```

**What is weird:** `get_or_create` is not atomic without an outer `transaction.atomic()` + `IntegrityError` handling; the second `instance.save()` re-enters `post_save` (fires audit signals twice); if triggered via admin/shell there is no outer lock, so `Listing` is created but `Batch` can stay `VERIFIED` instead of `LISTED`.

**Scenario:** Two PMs concurrently verify the same batch (race before the lock was added, or via admin `status=verified`). Both signals see no listing, both `INSERT` `Listing(batch)` `OneToOne` → one `IntegrityError`; marketplace misses the listing, batch stuck `VERIFIED`.

**Fix:** Wrap in `with transaction.atomic():` + `Batch.objects.select_for_update().get(pk=instance.pk)`, use `select_for_update` + `get_or_create` inside, catch `IntegrityError`, re-read `instance.refresh_from_db()` before updating status.

---

### R4 — `trader/views.py:71-98` PlaceBid No Lock — **High**

```python
# trader/views.py:71-98 (simplified)
class PlaceBidView(CreateView):
    def dispatch(self, req, *args, **kwargs):
        self.listing = get_object_or_404(Listing, pk=kwargs['pk'])
        if not self.listing.is_active: return redirect(...)
        return super().dispatch(req, *args, **kwargs)

    def form_valid(self, form):
        form.instance.listing = self.listing
        form.instance.trader = self.request.user
        return super().form_valid(form)  # no atomic, no price/qty check
```

**What is weird:** `is_active` is checked in `dispatch` (one query), `INSERT Bid` happens in `form_valid` (second query). No `transaction.atomic()`, no `select_for_update` on `Listing`, no check of `auction_end_time`, no `bid_price > current_highest`, no `quantity <= available_qty`.

**Scenario:** Trader A and B bid same auction within 10 ms. Both pass `is_active True`. Both `INSERT` `ACTIVE` bids, even if the auction expired 1 ms earlier or the farmer accepted a bid concurrently and deactivated the listing.

**Fix:** `with transaction.atomic(): listing = Listing.objects.select_for_update().get(pk=...)` re-check `is_active`, `auction_end_time > now()`, `bid_price > highest`, `quantity <= available_qty` under lock before `Bid.objects.create()`.

---

### R5 — `trader/views.py:132-172` MakePayment Double Payment — **High**

```python
# trader/views.py:132-172 (simplified)
def post(self, req, *args, **kwargs):
    order = self.order  # from dispatch get_object_or_404
    Payment.objects.create(order=order, payer=req.user, amount=order.total_amount,
        payment_method=method, transaction_ref=ref or f"MOCK-{timezone.now().timestamp():.0f}",
        status=Payment.Status.COMPLETED, paid_at=timezone.now())
    order.payment_status = Order.PaymentStatus.PAID
    order.save(update_fields=['payment_status'])
```

**What is weird:** No `transaction.atomic()`, no `select_for_update` on `Order`, no `Payment.objects.filter(order=order, status=COMPLETED).exists()` check under lock. `transaction_ref` default uses second-precision `:.0f` → two double-clicks within same second generate identical `MOCK-...` → second hits `unique=True` `IntegrityError`; if user supplies `ref`, duplicate allowed.

**Scenario:** Trader double-clicks "Pay" or two tabs `POST /trader/orders/<pk>/pay/` concurrently. Both read `payment_status=UNPAID`, both `CREATE Payment COMPLETED`, both set `PAID` → double charge, two `Payment` rows for one `Order`.

**Fix:** `atomic` + `select_for_update` on `Order`, check `if order.payment_status == PAID or Payment.objects.filter(...).exists(): error`, generate `transaction_ref` via `uuid4` if blank, add DB partial unique constraint (`UniqueConstraint(fields=['order'], condition=Q(status='completed'))`).

---

### R6 — `farmer/views.py:154-203` AcceptBid Oversell — **High**

```python
# farmer/views.py:154-203 (inside with transaction.atomic():)
listing = Listing.objects.select_for_update().get(pk=listing.pk)  # correct
bid = Bid.objects.select_for_update().get(pk=bid.pk)              # correct
Bid.objects.filter(listing=listing, status='active').exclude(pk=bid.pk).update(status='outbid')
bid.status = Bid.Status.ACCEPTED; bid.save()
order = Order.objects.create(...)  # triggers R2
listing.available_qty_kg -= bid.quantity_kg  # Python arithmetic, not F()
if listing.available_qty_kg <= 0:
    listing.is_active = False
    listing.batch.status = Batch.Status.SOLD
listing.save(update_fields=['available_qty_kg', 'is_active'])
```

**What is weird:** Correct `select_for_update` for same `Listing`, but logic lacks `if bid.quantity_kg > listing.available_qty_kg: abort` and uses Python subtraction instead of `F('available_qty_kg') - qty`. No re-check of `listing.is_active` after acquiring the lock.

**Scenario:** Listing `available_qty=100 kg`. Farmer accepts Bid1 `60 kg` (tab 1) and Bid2 `60 kg` (tab 2) concurrently. Tx1: `100-60=40` stays active. Tx2 waits for lock, then `40-60=-20 → clamped to 0` and deactivates → two orders totaling 120 kg for 100 kg stock (oversell).

**Fix:** Under lock: `if not listing.is_active or bid.quantity_kg > listing.available_qty_kg: error`; then `listing.available_qty_kg = F('available_qty_kg') - bid.quantity_kg` + `refresh_from_db()`; handle `R2` retry.

---

### R7 — `accounts/views.py:235-255` Dispute Create Lost Update — Medium

```python
def form_valid(self, form):
    form.instance.order = self.order; form.instance.raised_by = self.request.user; form.save()
    self.order.status = Order.Status.DISPUTED
    self.order.save(update_fields=['status'])
```

No `atomic`/`select_for_update`. Concurrent `OrderTracking → SHIPPED` from farmer overwrites `DISPUTED`.

**Fix:** `atomic` + `select_for_update` on `Order`, set status and create dispute atomically.

---

### R8 — `accounts/views.py:191-225` Conversation Create Triple Insert — Medium

```python
def form_valid(self, form):
    form.instance.batch = self.batch; form.save()
    ConversationParticipant.objects.create(conversation=form.instance, user=self.request.user, ...)
    ConversationParticipant.objects.create(conversation=form.instance, user=other_user, ...)
```

Three `INSERT`s without `atomic`. Double-click creates two conversations.

**Fix:** Wrap in `transaction.atomic()`.

---

### R9 — `panel/views.py:160-188` Dispute Resolve Overwrite — Medium

`UpdateView` without `atomic`/`select_for_update`. Two admins `POST /panel/disputes/<pk>/resolve/` → last resolution clobbers first, `resolved_by` lost.

**Fix:** `atomic` + `select_for_update` + re-check `status` transition.

---

### R10 — `panel/views.py:114-250` PM Approve/Reject and User Revoke/Reactivate TOCTOU — Medium

```python
user = get_object_or_404(User, pk=pk, role='product_manager', is_active=False)
user.is_active = True; user.save(update_fields=['is_active'])
AuditLog.objects.create(action='user.pm_accepted', ...)
```

`get_object_or_404(is_active=False)` + immediate `save` without `select_for_update`. Concurrent approves → double `AuditLog`. Applies to `AcceptPMView:114`, `RejectPMView:138`, `RevokeUserView:209`, `ReactivateUserView:235`.

**Fix:** `atomic` + `select_for_update` + audit inside atomic.

---

### R11 — `accounts/signals.py:18-23` Conversation `last_message_at` Lost Update — Medium

```python
@receiver(post_save, sender=Message)
def update_conversation_timestamp(sender, instance, created, **kwargs):
    if created:
        conversation.last_message_at = instance.sent_at
        conversation.save(update_fields=['last_message_at'])
```

Read-modify-write without `F()`/`lock`. Two messages at same time → last writer wins, ordering broken for `ConversationListView:ordering=['-last_message_at']`.

**Fix:** `Conversation.objects.filter(pk=instance.conversation_id).update(last_message_at=instance.sent_at)` or `F()` + `select_for_update`.

---

### R12 — `trader/views.py:185-209` OrderTracking Status Drift — Medium

Creates `OrderTracking` but never propagates to `Order.status`; no `atomic`/`lock`. Two tracking updates (`SHIPPED` vs `DELIVERED`) succeed but order stays `processing`.

**Fix:** `atomic` + `select_for_update` on `Order`, update `Order.status` to match tracking status.

---

## 4. Unnecessary / Dead / Duplicate Code

| Location | Snippet / Pattern | Why Unnecessary |
|----------|-------------------|----------------|
| `farmer/views.py:132-135,148-150` `MyBidsView.get_model()` / `OrderListView.get_model()` | `def get_model(self): return Bid` | `ListView` uses `model` attribute, not `get_model()` → dead wrapper; use `model = Bid` |
| `accounts/views.py:139/154/190/233/266`, `farmer/views.py:20/46/58/75/115/123/138/154`, `trader/views.py:21/62/71/100/112/130/183`, `panel/views.py:21/55/68/100/196` | `LoginRequiredMixin` **+** `@method_decorator(role_required(...), name='dispatch')` on same CBV | `role_required` already does `if not authenticated → redirect('accounts:login')`; double guard is redundant (keep one for clarity or both explicitly; current mix is inconsistent) |
| `panel/templates/panel/pm_pending.html` | Orphan file (superseded by `panel/templates/panel/pm/pending.html`) | Dead template, safe to delete when shell available |
| `chat/services/chatbot.py:118-166` | `listings = Listing.objects.filter(...); total = listings.count(); for l in listings: ...; top = listings.order_by(...)[:10]` + Python loops for `avg/min/max` | Lazy queryset fires 3 queries; imports `Avg, Min, Max, Q` at `chat/services/chatbot.py:16` but never uses DB `aggregate()` — manual loops defeat DB aggregation |
| `trader/models.py:48-66` `bid_count` manual `_bid_count_cache` getter/setter | ```python @property def bid_count(self): if hasattr(self,'_bid_count_cache'): return ... else: return self.bids.filter(...).count() ``` | Reinvents `@cached_property`; correct DB way is `annotate(_annotated_bid_count=Count(...))` |
| `accounts/decorators.py:28-54` | 6 one-line wrappers `farmer_required = role_required('farmer')` | Per `AGENTS.md` they are intentional convenience; but direct `@role_required('farmer')` is clearer |

---

## 5. Lazy / Weird Function Misuse

### 5.1 `reverse_lazy` used inside methods (should be `reverse`)

**Rule:** `reverse_lazy` only for class attributes evaluated at import time (`success_url = reverse_lazy('accounts:dashboard')`, `RedirectView.as_view(url=reverse_lazy(...))`). Inside methods (`get_success_url()`, `form_valid()`, `post()`) use `reverse`.

**Current:** `reverse` is never imported; every view imports only `reverse_lazy` and misuses it inside methods.

| Location | Code | Fix |
|----------|------|-----|
| `accounts/views.py:13` | `from django.urls import reverse_lazy` | `from django.urls import reverse, reverse_lazy` |
| `accounts/views.py:66-67` `RegisterView.get_success_url()` | `return reverse_lazy('accounts:dashboard')` | `return reverse('accounts:dashboard')` (also redundant — `success_url` attr already same) |
| `accounts/views.py:224-225` `ConversationCreateView` | `return reverse_lazy('accounts:conversation_list')` | `return reverse(...)` |
| `accounts/views.py:257-258` `DisputeCreateView` | `return reverse_lazy('accounts:dispute_list')` | `return reverse(...)` |
| `farmer/views.py:12/71/88` | `return reverse_lazy('farmer:farm_list/batch_list')` | `return reverse(...)` |
| `trader/views.py:13/96/208` | `return reverse_lazy('trader:listing_detail', kwargs={'pk': ...})` | `return reverse(...)` |
| `panel/views.py:12/187` | `return reverse_lazy('accounts:dispute_list')` | `return reverse(...)` |
| `cardetrade/urls.py:34` `RedirectView(pattern_name='accounts:home')` | ✅ Correct — `pattern_name` is internally lazy | Keep |

### 5.2 `django.utils.functional` / translation — absent when it should be used

| Location | Issue |
|----------|-------|
| `trader/models.py:48-66` manual `_bid_count_cache` | Hand-rolled `cached_property`; `current_highest_bid`, `time_remaining` plain `@property` do `self.bids.filter(...).first()` per access → N+1 in listing loops. **Fix:** `from django.utils.functional import cached_property` |
| `accounts/middleware.py:8-31` `AuditMiddleware` | Stores `thread_locals.user = request.user` eagerly, never clears in `process_response` → thread-local leak. Add `process_response` to delete `_thread_locals` or use `try/finally`. |
| All `TextChoices` (`accounts/models.py:20`, `farmer/models.py:39`, `pm/models.py:16`, `trader/models.py:22/71/102/174/200`) | `class Role(models.TextChoices): FARMER='farmer','Farmer'` — plain strings while `settings.py:USE_I18N=True`. Should be `gettext_lazy('Farmer')` (`from django.utils.translation import gettext_lazy as _`). |

### 5.3 Lazy helpers that do more harm than good

| Location | What it does | Why weird |
|----------|--------------|-----------|
| `pm/views.py:69-77` `_get_verification_form_class()` | Builds a `ModelForm` class inside a `staticmethod` on every request | Bypasses `pm/forms.py` convention; move to `pm/forms.py:VerificationForm` and set `form_class = VerificationForm` |
| `accounts/signals.py:65-81` `_make_audit_receiver()` | Factory wrapping `_write_audit` + `for _model in ['farmer.Batch', ...]: receiver(post_save, sender=_model)` | **String sender never matches** → receivers **never fire** (dead audit); `dispatch_uid` with dot is non-canonical. Loop over real classes: `from farmer.models import Batch` + `@receiver(post_save, sender=Batch)` |
| `farmer/signals.py:10/32` `tz.timedelta` | `from django.utils import timezone as tz` then `tz.timedelta(days=7)` | `django.utils.timezone` has no `timedelta` → `AttributeError` the moment a batch is verified. **Fix:** `import datetime; timezone.now() + datetime.timedelta(days=7)` |

### 5.4 Other weird wrappers / dead code

- `accounts/views.py:221` `messages.success(request, ...)` → `request` undefined, should be `self.request` (`NameError` at runtime).
- `pm/views.py:31-32`, `farmer/views.py:41` raw strings `'pending'` instead of `Batch.Status.PENDING` — violates `AGENTS.md` R8.
- `chat/services/chatbot.py:25/265` `DecimalEncoder` + `format_response(text)` trivial wrappers → can be `json.dumps(default=str)`.

---

## 6. Summary Tables

### Race Conditions

| # | File | Vulnerability | Scenario (2 users) | Severity |
|---|------|---------------|-------------------|----------|
| R1 | `farmer/models.py:76-89` | `batch_code` `last()+1` no lock | 2 farmers create batch same second | High |
| R2 | `trader/models.py:155-168` | `order_code` `last()+1` no lock | 2 accepts on different listings same second | High |
| R3 | `farmer/signals.py:15-37` | `get_or_create` listing + recursive save no atomic | 2 PMs verify same batch | High |
| R4 | `trader/views.py:71-98` | `PlaceBid` no atomic/lock | 2 traders bid concurrent + auction expired | High |
| R5 | `trader/views.py:132-172` | `MakePayment` no lock/idempotency | Double-click Pay | High |
| R6 | `farmer/views.py:154-203` | `AcceptBid` oversell, Python `-` not `F()` | 2 tabs accept 60 kg on 100 kg listing | High |
| R7 | `accounts/views.py:235-255` | `DisputeCreate` no lock | Buyer dispute vs farmer ship | Medium |
| R8 | `accounts/views.py:191-225` | `Conversation` triple insert no atomic | Double-click create | Medium |
| R9 | `panel/views.py:160-188` | `DisputeResolve` no lock | 2 admins resolve same dispute | Medium |
| R10 | `panel/views.py:114/138/209/235` | `PM approve/revoke` TOCTOU | 2 admins approve same PM | Medium |
| R11 | `accounts/signals.py:18-23` | `last_message_at` lost update | 2 messages same conversation same second | Medium |
| R12 | `trader/views.py:185-209` | `OrderTracking` no sync/lock | Farmer + admin track together | Medium |

### Lazy/Unnecessary

| Category | Location | Issue | Severity |
|----------|----------|-------|----------|
| `reverse_lazy` in methods | 8 sites (`accounts/forms.py:66`, `trader:96`, etc.) | Should be `reverse` | Low (additive overhead) |
| String signal sender never fires | `accounts/signals.py:65-81` | Dead audit receivers | High (audit gap, R6 violation) |
| `tz.timedelta` bug | `farmer/signals.py:32` | `AttributeError` on verify | High (crash) |
| Manual `bid_count` cache | `trader/models.py:48-66` | Reinvents `@cached_property`, N+1 | Medium |
| Dead `get_model()` | `farmer/views.py:132,148` | Never called by `ListView` | Low |
| Double auth guard | 12 CBVs `LoginRequiredMixin` + `role_required` | Redundant but harmless | Low |
| Orphan template | `panel/templates/panel/pm_pending.html` | Unused | Low |

---

## 7. Why These Matter Together

A single double-click can traverse multiple bugs: e.g., trader double-clicks **Pay** (R5) while farmer ships the same order (R12) while a third user posts a message on the order's conversation (R11) — three lost updates at once. The `reverse_lazy`/`gettext_lazy`/`cached_property` issues do not cause crashes but add latency (lazy `Promise` wrappers, N+1 queries) and hide the `AttributeError`/`NameError` bugs that only surface at runtime. Fixing the lazy bugs first makes the race fixes easier to test (correct `reverse` in `get_success_url` makes redirects predictable; fixing `tz.timedelta` unblocks verification flow testing).

---

## 8. Recommended Fix Roadmap (Phased)

> **Order matters:** Fix crash bugs first, then High races, then Medium, then cleanup. No shell available now — some steps were not runtime-verified.

### Phase 0 — Confirm (read-only, when shell available)

- `python manage.py check`
- `python manage.py test farmer pm trader accounts panel --verbosity=2`
- Manual smoke: create 2 batches as two farmers at same time, place 2 bids, double-click Pay, verify `farmer/signals.py:tz.timedelta` raises or not, check `AuditLog` is written for claims.

### Phase 1 — Crash / Dead-Code (no lock needed, high leverage)

1. `farmer/signals.py:10/32` — `import datetime; timezone.now() + datetime.timedelta(days=7)`
2. `accounts/signals.py:65-81` — replace string `sender='farmer.Batch'` with real model classes; delete `_make_audit_receiver` factory, write explicit `@receiver(post_save, sender=Batch)` handlers; fix `dispatch_uid`.
3. `accounts/views.py:221` — `messages.success(self.request, ...)`
4. `trader/models.py:45/52` `'active'` → `Bid.Status.ACTIVE` (R8 compliance)

### Phase 2 — High Races (need `transaction.atomic` + `select_for_update` + `F()` + retry)

5. `farmer/models.py:76` & `trader/models.py:155` — `select_for_update` on max row inside `atomic` + `IntegrityError` retry loop (or counter table). Keep `unique=True` as final guard.
6. `farmer/signals.py:15-37` — wrap `get_or_create` + `batch.save` in `atomic` + `select_for_update`; catch `IntegrityError`; `refresh_from_db()`.
7. `trader/views.py:71` `PlaceBidView` — `atomic` + `select_for_update` on `Listing`; re-check `is_active`, `auction_end_time > now()`, `bid_price > highest`, `qty <= available` under lock.
8. `trader/views.py:132` `MakePaymentView` — `atomic` + `select_for_update` on `Order`; check `payment_status` + existing `Payment`; `uuid4` for `transaction_ref`; add partial unique constraint `UniqueConstraint(fields=['order'], condition=Q(status='completed'))`.
9. `farmer/views.py:167` `AcceptBidView` — keep lock, add `if bid.quantity_kg > listing.available_qty_kg: error`, use `F('available_qty_kg') - bid.quantity_kg` + `refresh_from_db()`.

### Phase 3 — Medium Races

10. `accounts/views.py:235` & `panel/views.py:160` & `panel/views.py:114/138/209/235` & `accounts/views.py:191/178` — wrap in `atomic` + `select_for_update`; move `AuditLog` creation inside atomic.
11. `accounts/signals.py:18` `update_conversation_timestamp` — use `Conversation.objects.filter(pk=...).update(last_message_at=instance.sent_at)` (single `UPDATE` no read) or `select_for_update` + `F()`.
12. `trader/views.py:185` `OrderTrackingCreateView` — `atomic` + `select_for_update` on `Order`, sync `Order.status = tracking.status`.

### Phase 4 — Lazy / Cleanup

13. Replace all 8 in-method `reverse_lazy` → `reverse` (keep 2 class-attr `reverse_lazy`); add `gettext_lazy` to `TextChoices` or set `USE_I18N=False` (decision needed).
14. `pm/views.py:69` → move `VForm` to `pm/forms.py:VerificationForm`; `trader/models.py` → `@cached_property`; `accounts/middleware.py:8` → add `process_response` to clear `thread_locals`; annotate `ListingListView` properly to avoid N+1.
15. Delete dead `get_model()` (`farmer/views.py:132/148`), delete orphan `panel/templates/panel/pm_pending.html`, remove unused `Avg/Min/Max/Q` imports, replace `chat/services/chatbot.py` Python loops with DB `aggregate()`.

---

## 9. How to Verify Fixes

| Check | Command / Manual Step | Expected |
|-------|----------------------|----------|
| Syntax | `python manage.py check` | `System check identified no issues (0 silenced)` |
| Unit | `python manage.py test farmer pm trader accounts --verbosity=2` | Previous `BatchVerify`/`AcceptBid` tests pass; new concurrency tests with `ThreadPoolExecutor` + `TransactionTestCase` pass |
| Double-click Pay | Click "Pay" twice quickly or `curl -X POST /trader/orders/<pk>/pay/` in two tabs | One `Payment` row, second returns error/idempotent success, no double charge |
| Two farmers create batch same second | Two browsers `POST /farmer/batches/create/` with same second | Two distinct `CDM-YYYY-NNNN`, no 500 |
| Bid on expired | Wait past `auction_end_time`, bid | `400 / "Auction ended"` not `201` |
| Update failures | Follow `plan → yes → migrate → test` workflow; use Postgres `READ COMMITTED` (`psql` direct) for final pass | No `IntegrityError` leak to user |

**SQLite note:** Do not rely on local `select_for_update` tests — they are no-ops on SQLite. Final verification must be on Postgres or with `TransactionTestCase` + threads and `IntegrityError` retry covered.

---

## 10. Glossary

| Term | Meaning |
|------|---------|
| **TOCTOU** | Time-of-check to time-of-use — checking a value then using it later without a lock, so it goes stale |
| **`transaction.atomic()`** | Django context manager that groups queries into one DB transaction (all-or-nothing) |
| **`select_for_update()`** | Locks selected rows until the transaction commits, so others wait |
| **`F()` expression** | Does arithmetic inside the DB (`UPDATE available_qty = available_qty - 60`) instead of Python |
| **`reverse` vs `reverse_lazy`** | `reverse` resolves URL immediately (for methods); `reverse_lazy` defers until needed (for class attributes at import time) |
| **`@cached_property` / `gettext_lazy`** | `cached_property` computes once and caches; `gettext_lazy` defers translation until rendering |
| **`IntegrityError`** | DB error when a `unique` constraint is violated — useful as final safety net with retry |

---

## 11. Appendix — File Reference

| Area | File |
|------|------|
| Settings / URLs | `cardetrade/settings.py`, `cardetrade/urls.py` |
| Auth & shared | `accounts/models.py`, `accounts/views.py`, `accounts/decorators.py`, `accounts/middleware.py`, `accounts/signals.py` |
| Farmer | `farmer/models.py`, `farmer/views.py`, `farmer/signals.py`, `farmer/admin.py` |
| Trader | `trader/models.py`, `trader/views.py`, `trader/signals.py` |
| PM | `pm/models.py`, `pm/views.py`, `pm/signals.py` (signal lives in `farmer/signals.py`) |
| Panel (admin) | `panel/views.py`, `panel/templates/panel/dashboard.html`, `panel/templates/panel/pm_pending.html` (orphan) |
| Chat | `chat/views.py`, `chat/services/chatbot.py` |

*Report saved to `reports/ANALYSIS-RACE-CONDITIONS-UNNECESSARY-LAZY-2026-08-27.md` — no DB migration, no config change associated with this report alone. Rollback: delete the `.md` file.*
