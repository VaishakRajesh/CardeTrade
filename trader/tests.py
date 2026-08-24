"""
trader/tests.py

Regression test for the payment workflow:
paying for an order transitions payment_status to paid and creates exactly one
Payment record (fix #4 / trader).
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from farmer.models import Batch
from trader.models import Listing, Order, Payment

User = get_user_model()


class PaymentTest(TestCase):
    """Paying for an order marks it paid and creates a single Payment row."""

    def setUp(self):
        self.farmer = User.objects.create_user(
            username='farmer', email='farmer@test.com', password='Testpass123!',
            role='farmer',
        )
        self.trader = User.objects.create_user(
            username='trader', email='trader@test.com', password='Testpass123!',
            role='trader',
        )
        self.batch = Batch.objects.create(
            farmer=self.farmer, quantity_kg=100,
            harvest_date='2026-01-15', estimated_price_per_kg=45.00,
        )
        self.listing = Listing.objects.create(
            batch=self.batch, farmer=self.farmer,
            listing_type='auction', price_per_kg=40, available_qty_kg=100,
        )
        self.order = Order.objects.create(
            listing=self.listing, batch=self.batch,
            buyer=self.trader, seller=self.farmer,
            quantity_kg=100, price_per_kg=40,
        )

    def test_payment_transitions_to_paid(self):
        self.client.login(username='trader@test.com', password='Testpass123!')
        response = self.client.post(
            reverse('trader:order_pay', args=[self.order.pk]),
            {'payment_method': 'bank_transfer', 'transaction_ref': 'TXN-001'},
        )
        self.assertEqual(response.status_code, 302)

        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PAID)
        self.assertEqual(Payment.objects.count(), 1)
        payment = Payment.objects.first()
        self.assertEqual(payment.status, Payment.Status.COMPLETED)
