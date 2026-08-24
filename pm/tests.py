"""
pm/tests.py

Regression test for the Product Manager verification workflow:
verifying a batch through the PM view auto-creates the auction Listing (fix #3).
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from farmer.models import Batch
from trader.models import Listing

User = get_user_model()


class PMVerifyCreatesListingTest(TestCase):
    """BatchVerifyView verification triggers listing creation via the signal."""

    def setUp(self):
        self.farmer = User.objects.create_user(
            username='farmer', email='farmer@test.com', password='Testpass123!',
            role='farmer',
        )
        self.pm = User.objects.create_user(
            username='pm', email='pm@test.com', password='Testpass123!',
            role='product_manager', is_active=True,
        )
        self.batch = Batch.objects.create(
            farmer=self.farmer, quantity_kg=100,
            harvest_date='2026-01-15', estimated_price_per_kg=45.00,
            status=Batch.Status.UNDER_REVIEW,
        )

    def test_pm_verify_creates_listing(self):
        self.client.login(username='pm@test.com', password='Testpass123!')
        response = self.client.post(
            reverse('pm:batch_verify', args=[self.batch.pk]),
            {
                'grade': 'A',
                'verified_price_per_kg': 50.00,
                'moisture_content_pct': 10.5,
                'aroma_score': 8,
                'color_score': 9,
                'purity_pct': 98.5,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Listing.objects.count(), 1)
        listing = Listing.objects.first()
        self.assertEqual(listing.listing_type, Listing.ListingType.AUCTION)
