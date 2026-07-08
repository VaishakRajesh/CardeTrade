"""
CardeTrade Django Signals - Automated Event Handlers

This module contains Django signals that automatically trigger actions
when certain model events occur. Signals enable decoupled, event-driven
architecture.

Signal Types Used:
- post_save: Triggered after a model instance is saved

Signals Implemented:
1. Batch verified -> Auto-create Listing
2. Order created -> Notify seller
3. Bid created -> Notify farmer
4. Message created -> Update conversation timestamp

Signals are connected in apps.py ready() method.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Batch, Listing, Order, Bid, Notification, Message


@receiver(post_save, sender=Batch)
def create_listing_on_verification(sender, instance, created, **kwargs):
    """
    Signal: Create a Listing when a Batch is verified.

    Triggered when: A Batch is saved with status='verified'
    Action:
    - Gets the QualityVerification for this batch
    - Creates a fixed-price Listing with verified price
    - Updates batch status to 'listed'

    This automation ensures verified batches are immediately
    available for purchase on the marketplace.

    Args:
        sender: The model class (Batch)
        instance: The Batch instance that was saved
        created: True if this is a new instance
        **kwargs: Additional keyword arguments
    """
    if instance.status == Batch.Status.VERIFIED:
        # Get the verification record for this batch
        try:
            verification = instance.verification
        except Batch.verification.RelatedObjectDoesNotExist:
            return  # No verification found, skip

        # Create listing with verified price (or get existing)
        Listing.objects.get_or_create(
            batch=instance,
            defaults={
                'farmer': instance.farmer,
                'listing_type': Listing.ListingType.FIXED_PRICE,
                'price_per_kg': verification.verified_price_per_kg,
                'available_qty_kg': instance.quantity_kg,
            }
        )
        # Update batch status to listed
        instance.status = Batch.Status.LISTED
        instance.save(update_fields=['status'])


@receiver(post_save, sender=Order)
def notify_seller_on_order(sender, instance, created, **kwargs):
    """
    Signal: Notify the seller when a new Order is created.

    Triggered when: A new Order is saved (created=True)
    Action:
    - Creates a notification for the seller (farmer)
    - Includes order code and quantity in message

    This keeps farmers informed about new purchases.

    Args:
        sender: The model class (Order)
        instance: The Order instance that was saved
        created: True if this is a new instance
        **kwargs: Additional keyword arguments
    """
    if created:
        Notification.objects.create(
            user=instance.seller,  # Notify the farmer
            type=Notification.Type.ORDER_PLACED,
            message=f"New order {instance.order_code} for {instance.quantity_kg}kg",
            reference_id=instance.id,
            reference_type='order'
        )


@receiver(post_save, sender=Bid)
def notify_farmer_on_bid(sender, instance, created, **kwargs):
    """
    Signal: Notify the farmer when a new Bid is placed.

    Triggered when: A new Bid is saved (created=True)
    Action:
    - Creates a notification for the listing owner (farmer)
    - Includes bid price and batch code in message

    This keeps farmers informed about bids on their listings.

    Args:
        sender: The model class (Bid)
        instance: The Bid instance that was saved
        created: True if this is a new instance
        **kwargs: Additional keyword arguments
    """
    if created:
        Notification.objects.create(
            user=instance.listing.farmer,  # Notify the listing owner
            type=Notification.Type.BID_RECEIVED,
            message=f"New bid Rs{instance.bid_price_per_kg}/kg on {instance.listing.batch.batch_code}",
            reference_id=instance.id,
            reference_type='bid'
        )


@receiver(post_save, sender=Message)
def update_conversation_timestamp(sender, instance, created, **kwargs):
    """
    Signal: Update conversation's last_message_at when a Message is sent.

    Triggered when: A new Message is saved (created=True)
    Action:
    - Updates the conversation's last_message_at timestamp
    - Used for sorting conversations by most recent activity

    This ensures conversations are ordered by most recent message.

    Args:
        sender: The model class (Message)
        instance: The Message instance that was saved
        created: True if this is a new instance
        **kwargs: Additional keyword arguments
    """
    if created:
        conversation = instance.conversation
        conversation.last_message_at = instance.sent_at
        conversation.save(update_fields=['last_message_at'])
