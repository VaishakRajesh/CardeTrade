"""
accounts/tests.py

Regression tests for account-level behaviour:
- Role-based is_staff / is_superuser / is_verified flags (fix #2 regression).
- Failed login shows a visible error (fix #1 regression).
- Mixed-case email login succeeds (fix #2 regression).
- @role_required rejects users of the wrong role.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


class RoleFlagsTest(TestCase):
    """Registering each role produces the correct staff/verified flags."""

    def test_farmer_flags(self):
        u = User.objects.create_user(
            username='farmer1', email='Farmer@Test.com', password='Testpass123!',
            role='farmer',
        )
        self.assertFalse(u.is_staff)
        self.assertFalse(u.is_superuser)
        self.assertFalse(u.is_verified)
        # Email normalized to lowercase on save (fix #2)
        self.assertEqual(u.email, 'farmer@test.com')

    def test_trader_flags(self):
        u = User.objects.create_user(
            username='trader1', email='trader@test.com', password='Testpass123!',
            role='trader',
        )
        self.assertFalse(u.is_staff)
        self.assertFalse(u.is_superuser)
        self.assertTrue(u.is_verified)

    def test_pm_flags(self):
        u = User.objects.create_user(
            username='pm1', email='pm@test.com', password='Testpass123!',
            role='product_manager',
        )
        self.assertTrue(u.is_staff)
        self.assertFalse(u.is_superuser)
        self.assertFalse(u.is_verified)

    def test_admin_flags(self):
        u = User.objects.create_user(
            username='admin1', email='admin@test.com', password='Testpass123!',
            role='admin',
        )
        self.assertTrue(u.is_staff)
        self.assertTrue(u.is_superuser)
        self.assertTrue(u.is_verified)


class LoginErrorTest(TestCase):
    """A failed login must render a visible error (regression for fix #1)."""

    def test_failed_login_shows_error(self):
        User.objects.create_user(
            username='existing', email='existing@test.com', password='Testpass123!',
            role='trader',
        )
        response = self.client.post(reverse('accounts:login'), {
            'username': 'existing@test.com',
            'password': 'wrong-password',
        })
        # LoginView re-renders the form on failure (HTTP 200, not a redirect).
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Please enter a correct', response.content)
        self.assertIn(b'alert-danger', response.content)

    def test_mixed_case_email_login_succeeds(self):
        User.objects.create_user(
            username='mixed', email='mixed@test.com', password='Testpass123!',
            role='trader',
        )
        # Stored email is lowercase; logging in with a mixed-case version works.
        response = self.client.post(reverse('accounts:login'), {
            'username': 'Mixed@TEST.com',
            'password': 'Testpass123!',
        })
        self.assertEqual(response.status_code, 302)


class RoleRequiredDecoratorTest(TestCase):
    """A trader hitting a farmer-only view is rejected with 403."""

    def test_wrong_role_rejected(self):
        trader = User.objects.create_user(
            username='tr', email='tr@test.com', password='Testpass123!', role='trader'
        )
        self.client.login(username='tr@test.com', password='Testpass123!')
        response = self.client.get(reverse('farmer:dashboard'))
        self.assertEqual(response.status_code, 403)

    def test_correct_role_allowed(self):
        farmer = User.objects.create_user(
            username='fa', email='fa@test.com', password='Testpass123!', role='farmer'
        )
        self.client.login(username='fa@test.com', password='Testpass123!')
        response = self.client.get(reverse('farmer:dashboard'))
        self.assertEqual(response.status_code, 200)
