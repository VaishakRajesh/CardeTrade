"""
farmer/tests.py

Regression tests for the farmer workflow:
- Verifying a batch auto-creates exactly one AUCTION listing via the signal (fix #3/farmer+pm).
- Accepting a bid creates an Order, marks other bids outbid, and is safe under
  a simulated concurrent accept (transaction.atomic + select_for_update) (fix #4).
"""

from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from threading import Thread

from farmer.models import Batch
from trader.models import Listing, Bid, Order

User = get_user_model()


class BatchVerifyListingTest(TestCase):
    """Verifying a batch must auto-create exactly one auction Listing."""

    @classmethod
    def setUpTestData(cls):
        cls.farmer = User.objects.create_user(
            username='farmer', email='farmer@test.com', password='Testpass123!',
            role='farmer',
        )
        cls.pm = User.objects.create_user(
            username='pm', email='pm@test.com', password='Testpass123!',
            role='product_manager', is_active=True,
        )
        cls.batch = Batch.objects.create(
            farmer=cls.farmer, quantity_kg=100,
            harvest_date='2026-01-15', estimated_price_per_kg=45.00,
        )

    def test_verify_creates_one_auction_listing(self):
        from pm.models import QualityVerification
        QualityVerification.objects.create(
            batch=self.batch, grade='A', verified_price_per_kg=50.00,
            product_manager=self.pm, moisture_content_pct=10.5,
            aroma_score=8, color_score=9, purity_pct=98.5,
        )
        self.batch.status = Batch.Status.VERIFIED
        self.batch.save()

        # Exactly one Listing is created and it is an auction.
        self.assertEqual(Listing.objects.count(), 1)
        listing = Listing.objects.first()
        self.assertEqual(listing.listing_type, Listing.ListingType.AUCTION)
        # The batch is flipped to LISTED by the signal.
        self.batch.refresh_from_db()
        self.assertEqual(self.batch.status, Batch.Status.LISTED)


class AcceptBidTest(TransactionTestCase):
    """
    Accepting a bid creates an Order, marks other bids outbid, and does not
    double-create Orders even under a simulated concurrent accept.
    """

    def setUp(self):
        self.farmer = User.objects.create_user(
            username='farmer', email='farmer@test.com', password='Testpass123!',
            role='farmer',
        )
        self.trader1 = User.objects.create_user(
            username='trader1', email='trader1@test.com', password='Testpass123!',
            role='trader',
        )
        self.trader2 = User.objects.create_user(
            username='trader2', email='trader2@test.com', password='Testpass123!',
            role='trader',
        )
        self.batch = Batch.objects.create(
            farmer=self.farmer, quantity_kg=100,
            harvest_date='2026-01-15', estimated_price_per_kg=45.00,
        )
        self.listing = Listing.objects.create(
            batch=self.batch, farmer=self.farmer,
            listing_type='auction', price_per_kg=40,
            available_qty_kg=100,
        )
        self.bid1 = Bid.objects.create(
            listing=self.listing, trader=self.trader1,
            bid_price_per_kg=42, quantity_kg=100,
        )
        self.bid2 = Bid.objects.create(
            listing=self.listing, trader=self.trader2,
            bid_price_per_kg=41, quantity_kg=100,
        )

    def _accept(self, bid_pk):
        # Each thread needs its own client + login (farmer accepts the bid).
        from django.test import Client
        c = Client()
        c.login(username='farmer@test.com', password='Testpass123!')
        c.post(reverse('farmer:accept_bid', args=[bid_pk]))

    def test_accept_bid_creates_order_and_marks_outbid(self):
        self._accept(self.bid1.pk)

        self.assertEqual(Order.objects.count(), 1)
        self.bid1.refresh_from_db()
        self.bid2.refresh_from_db()
        self.assertEqual(self.bid1.status, Bid.Status.ACCEPTED)
        self.assertEqual(self.bid2.status, Bid.Status.OUTBID)

        # Accepting the now-outbid bid must NOT create a second order.
        self._accept(self.bid2.pk)
        self.assertEqual(Order.objects.count(), 1)

    def test_concurrent_accept_does_not_double_create(self):
        # Fire two concurrent accepts of the SAME bid; exactly one Order remains.
        t1 = Thread(target=self._accept, args=(self.bid1.pk,))
        t2 = Thread(target=self._accept, args=(self.bid1.pk,))
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        self.assertEqual(Order.objects.count(), 1)
