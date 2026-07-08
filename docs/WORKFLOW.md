# Business Workflows — CardeTrade

## Batch Lifecycle

```
1. Farmer creates batch                 → status = 'pending'
2. PM takes batch for review            → status = 'under_review'
3. PM verifies quality/grades           → status = 'verified'
4. Signal auto-creates Listing          → status = 'listed'
5. Trader buys/wins auction             → status = 'sold'
6. Order created, batch locked
```

### Status Transitions

```
pending → under_review → verified → listed → sold
                          └→ rejected
```

---

## Order Lifecycle

```
1. Order created (buy/successful bid)  → status = 'pending'
2. Seller confirms                      → status = 'confirmed'
3. Processing/packing                   → status = 'processing'
4. Shipped                             → status = 'shipped'
5. Delivered                          → status = 'delivered'
```

### Cancel/Dispute

```
Any status → cancelled (by buyer/seller agreement)
Any status → disputed (if issue arises)
```

### Payment Status

```
unpaid → partially_paid → paid → refunded
```

---

## Fixed Price Flow

```
1. PM verifies batch → Listing with fixed_price type created
2. Listing appears in marketplace with price_per_kg
3. Trader clicks "Buy Now"
4. Order created at that price
5. Farmer notified automatically
```

---

## Auction Flow

```
1. PM verifies batch → Listing with auction type created
2. Listing appears with auction_start_time/auction_end_time
3. Traders place bids (price must exceed current highest)
4. When auction ends:
   a. Highest bid wins → Order created automatically
   b. All other bids marked 'outbid'
5. Farmer notified of winning bid
```

---

## Quality Verification Flow

```
1. PM picks batch from 'under_review' list
2. Tests: moisture, aroma (1-10), color (1-10), purity %
3. Assigns grade: A (premium), B (standard), C (economy)
4. Sets verified_price_per_kg
5. On save: batch → 'verified', signal creates Listing
6. Farmer notified
```

---

## Role Permissions Matrix

| Action | Farmer | Trader | PM | Admin |
|--------|--------|--------|----|-------|
| Register/Login | ✓ | ✓ | ✓ | ✓ |
| Manage Profile | ✓ | ✓ | ✓ | ✓ |
| Create Farm | ✓ | ✗ | ✗ | ✗ |
| Create Batch | ✓ | ✗ | ✗ | ✗ |
| View Batches | Own | All | All | All |
| Verify Batch | ✗ | ✗ | ✓ | ✓ |
| Create Listing | Auto (signal) | ✗ | ✓ | ✓ |
| View Listings | Own | All | All | All |
| Place Bid | ✗ | ✓ | ✗ | ✗ |
| Buy (Fixed) | ✗ | ✓ | ✗ | ✗ |
| View Orders | Sales | Purchases | All | All |
| Process Order | ✓ | ✓ | ✓ | ✓ |
| Track Order | ✓ | ✓ | ✓ | ✓ |
| Raise Dispute | ✓ | ✓ | ✗ | ✓ |
| Resolve Dispute | ✗ | ✗ | ✓ | ✓ |
| Send Message | ✓ | ✓ | ✓ | ✓ |
| View Reports | ✗ | ✗ | ✓ | ✓ |
| Audit Logs | ✗ | ✗ | ✗ | ✓ |
| Manage Users | ✗ | ✗ | ✗ | ✓ |
