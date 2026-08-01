"""
accounts/signals.py

Django signal handlers for the accounts app.
Automatically updates conversation timestamps when new messages are sent.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Message


# Update the parent conversation's last_message_at when a new message is sent
@receiver(post_save, sender=Message)
def update_conversation_timestamp(sender, instance, created, **kwargs):
    if created:
        conversation = instance.conversation
        conversation.last_message_at = instance.sent_at
        conversation.save(update_fields=['last_message_at'])
