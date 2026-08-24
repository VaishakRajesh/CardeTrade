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
from accounts.models import AuditLog
from pm.models import QualityVerification

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


class BatchClaimTest(TestCase):
    """PMs claim batches for review; another PM cannot verify a claimed batch."""

    def setUp(self):
        self.farmer = User.objects.create_user(
            username='farmer', email='farmer@test.com', password='Testpass123!',
            role='farmer',
        )
        self.pm1 = User.objects.create_user(
            username='pm1', email='pm1@test.com', password='Testpass123!',
            role='product_manager', is_active=True,
        )
        self.pm2 = User.objects.create_user(
            username='pm2', email='pm2@test.com', password='Testpass123!',
            role='product_manager', is_active=True,
        )
        self.batch = Batch.objects.create(
            farmer=self.farmer, quantity_kg=100,
            harvest_date='2026-01-15', estimated_price_per_kg=45.00,
            status=Batch.Status.PENDING,
        )

    def test_start_review_claims_batch(self):
        self.client.login(username='pm1@test.com', password='Testpass123!')
        response = self.client.post(reverse('pm:batch_start_review', args=[self.batch.pk]))
        self.assertEqual(response.status_code, 302)
        self.batch.refresh_from_db()
        self.assertEqual(self.batch.status, Batch.Status.UNDER_REVIEW)
        self.assertEqual(self.batch.claimed_by, self.pm1)
        self.assertTrue(AuditLog.objects.filter(action='batch.claimed', record_id=self.batch.pk).exists())

    def test_other_pm_cannot_claim_claimed_batch(self):
        self.batch.status = Batch.Status.UNDER_REVIEW
        self.batch.claimed_by = self.pm1
        self.batch.save(update_fields=['status', 'claimed_by'])
        self.client.login(username='pm2@test.com', password='Testpass123!')
        response = self.client.post(reverse('pm:batch_start_review', args=[self.batch.pk]))
        self.assertEqual(response.status_code, 302)
        self.batch.refresh_from_db()
        self.assertEqual(self.batch.claimed_by, self.pm1)  # unchanged

    def test_other_pm_cannot_verify_claimed_batch(self):
        self.batch.status = Batch.Status.UNDER_REVIEW
        self.batch.claimed_by = self.pm1
        self.batch.save(update_fields=['status', 'claimed_by'])
        self.client.login(username='pm2@test.com', password='Testpass123!')
        response = self.client.post(
            reverse('pm:batch_verify', args=[self.batch.pk]),
            {'grade': 'A', 'verified_price_per_kg': 50.00},
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(hasattr(self.batch, 'verification'))
        self.assertEqual(QualityVerification.objects.count(), 0)

    def test_owner_pm_can_verify_claimed_batch(self):
        self.batch.status = Batch.Status.UNDER_REVIEW
        self.batch.claimed_by = self.pm1
        self.batch.save(update_fields=['status', 'claimed_by'])
        self.client.login(username='pm1@test.com', password='Testpass123!')
        response = self.client.post(
            reverse('pm:batch_verify', args=[self.batch.pk]),
            {'grade': 'A', 'verified_price_per_kg': 50.00},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(QualityVerification.objects.filter(batch=self.batch).exists())
        self.batch.refresh_from_db()
        self.assertEqual(self.batch.status, Batch.Status.LISTED)
