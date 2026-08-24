"""
panel/tests.py

Smoke/regression test for the admin panel access control.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from accounts.models import User, AuditLog

User = get_user_model()


class PanelAccessTest(TestCase):
    """Only admins may reach the admin dashboard."""

    def test_trader_rejected(self):
        trader = User.objects.create_user(
            username='trader', email='trader@test.com', password='Testpass123!',
            role='trader',
        )
        self.client.login(username='trader@test.com', password='Testpass123!')
        response = self.client.get(reverse('panel:dashboard'))
        self.assertEqual(response.status_code, 403)

    def test_admin_allowed(self):
        admin = User.objects.create_user(
            username='admin', email='admin@test.com', password='Testpass123!',
            role='admin',
        )
        self.client.login(username='admin@test.com', password='Testpass123!')
        response = self.client.get(reverse('panel:dashboard'))
        self.assertEqual(response.status_code, 200)


class PMApprovalTest(TestCase):
    """PM registration is pending; admin can review, accept, reject, and audit."""

    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin', email='admin@test.com', password='Testpass123!',
            role='admin',
        )
        self.client.login(username='admin@test.com', password='Testpass123!')

    def _make_pending_pm(self):
        return User.objects.create_user(
            username='newpm', email='newpm@test.com', password='Testpass123!',
            role='product_manager',
        )

    def test_new_pm_is_inactive(self):
        pm = self._make_pending_pm()
        self.assertFalse(pm.is_active)

    def test_pm_detail_view(self):
        pm = self._make_pending_pm()
        response = self.client.get(reverse('panel:pm_detail', args=[pm.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, pm.username)

    def test_accept_pm_activates_and_audits(self):
        pm = self._make_pending_pm()
        response = self.client.post(reverse('panel:pm_accept', args=[pm.pk]))
        self.assertEqual(response.status_code, 302)
        pm.refresh_from_db()
        self.assertTrue(pm.is_active)
        self.assertTrue(pm.is_verified)
        self.assertTrue(AuditLog.objects.filter(
            action='user.pm_accepted', record_id=pm.pk).exists())

    def test_reject_pm_keeps_inactive_and_audits(self):
        pm = self._make_pending_pm()
        response = self.client.post(reverse('panel:pm_reject', args=[pm.pk]))
        self.assertEqual(response.status_code, 302)
        pm.refresh_from_db()
        self.assertFalse(pm.is_active)
        self.assertTrue(AuditLog.objects.filter(
            action='user.pm_rejected', record_id=pm.pk).exists())

    def test_dashboard_lists_pending_pms(self):
        self._make_pending_pm()
        response = self.client.get(reverse('panel:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Pending PM Approvals')


class UserDetailTest(TestCase):
    """Admin can view any user's detail and revoke/reactivate access."""

    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin', email='admin@test.com', password='Testpass123!',
            role='admin',
        )
        self.client.login(username='admin@test.com', password='Testpass123!')
        self.target = User.objects.create_user(
            username='target', email='target@test.com', password='Testpass123!',
            role='trader',
        )

    def test_user_detail_view(self):
        response = self.client.get(reverse('panel:user_detail', args=[self.target.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.target.username)

    def test_revoke_deactivates_and_audits(self):
        response = self.client.post(reverse('panel:user_revoke', args=[self.target.pk]))
        self.assertEqual(response.status_code, 302)
        self.target.refresh_from_db()
        self.assertFalse(self.target.is_active)
        self.assertTrue(AuditLog.objects.filter(
            action='user.revoked', record_id=self.target.pk).exists())

    def test_reactivate_activates_and_audits(self):
        self.target.is_active = False
        self.target.save(update_fields=['is_active'])
        response = self.client.post(reverse('panel:user_reactivate', args=[self.target.pk]))
        self.assertEqual(response.status_code, 302)
        self.target.refresh_from_db()
        self.assertTrue(self.target.is_active)
        self.assertTrue(AuditLog.objects.filter(
            action='user.reactivated', record_id=self.target.pk).exists())

    def test_cannot_revoke_self(self):
        response = self.client.post(reverse('panel:user_revoke', args=[self.admin.pk]))
        self.assertEqual(response.status_code, 302)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)
