"""
chat/tests.py

Smoke test for the chatbot API access control.
"""

from django.test import TestCase
from django.urls import reverse


class ChatAPIAccessTest(TestCase):
    """The chatbot API requires an authenticated user."""

    def test_anonymous_is_redirected_to_login(self):
        response = self.client.post(
            reverse('chat:chat_api'),
            data='{"message": "hello"}',
            content_type='application/json',
        )
        # login_required redirects unauthenticated requests.
        self.assertEqual(response.status_code, 302)
