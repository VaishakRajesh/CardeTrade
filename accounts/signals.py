"""
accounts/signals.py

Django signal handlers for the accounts app.
Automatically updates conversation timestamps when new messages are sent,
and writes audit-log rows for key mutations across the platform.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.forms.models import model_to_dict

from .models import Message, AuditLog
from .middleware import get_current_user, get_current_ip

# Real model classes for audit signal senders (string senders never fire)
from farmer.models import Batch
from pm.models import QualityVerification
from trader.models import Listing, Bid, Order, Payment
from accounts.models import Dispute


# Update the parent conversation's last_message_at when a new message is sent
@receiver(post_save, sender=Message)
def update_conversation_timestamp(sender, instance, created, **kwargs):
    if created:
        conversation = instance.conversation
        conversation.last_message_at = instance.sent_at
        conversation.save(update_fields=['last_message_at'])


# ---------------------------------------------------------------------------
# Audit logging: write an AuditLog row whenever a tracked model is created or
# updated. The acting user and request IP are pulled from the per-request
# thread-local storage populated by AuditMiddleware. When no request context
# exists (e.g. management commands, tests), user/IP are left blank.
# ---------------------------------------------------------------------------

# Maps the (app_label, model) -> AuditLog.TableType value to store.
_AUDIT_TABLES = {
    ('farmer', 'Batch'): AuditLog.TableType.BATCH,
    ('pm', 'QualityVerification'): AuditLog.TableType.QUALITY_VERIFICATION,
    ('trader', 'Listing'): AuditLog.TableType.LISTING,
    ('trader', 'Bid'): AuditLog.TableType.BID,
    ('trader', 'Order'): AuditLog.TableType.ORDER,
    ('trader', 'Payment'): AuditLog.TableType.PAYMENT,
    ('accounts', 'Dispute'): AuditLog.TableType.DISPUTE,
}


def _write_audit(instance, action):
    table_name = _AUDIT_TABLES.get(
        (instance._meta.app_label, instance._meta.model_name)
    )
    if not table_name:
        return
    try:
        new_value = model_to_dict(instance)
    except Exception:
        new_value = {'id': instance.pk}
    AuditLog.objects.create(
        user=get_current_user(),
        action=action,
        table_name=table_name,
        record_id=instance.pk,
        new_value=new_value,
        ip_address=get_current_ip(),
    )


def _audit_receiver(sender, instance, created, **kwargs):
    _write_audit(instance, 'created' if created else 'updated')


for _model in (Batch, QualityVerification, Listing, Bid, Order, Payment, Dispute):
    receiver(
        post_save,
        sender=_model,
        dispatch_uid=f'audit_{_model._meta.app_label}_{_model.__name__}',
    )(_audit_receiver)
