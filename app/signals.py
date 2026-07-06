from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Batch, Listing, Order, Bid, Notification, Message


@receiver(post_save, sender=Batch)
def create_listing_on_verification(sender, instance, created, **kwargs):
    if instance.status == Batch.Status.VERIFIED:
        try:
            verification = instance.verification
        except Batch.verification.RelatedObjectDoesNotExist:
            return
        Listing.objects.get_or_create(
            batch=instance,
            defaults={
                'farmer': instance.farmer,
                'listing_type': Listing.ListingType.FIXED_PRICE,
                'price_per_kg': verification.verified_price_per_kg,
                'available_qty_kg': instance.quantity_kg,
            }
        )
        instance.status = Batch.Status.LISTED
        instance.save(update_fields=['status'])


@receiver(post_save, sender=Order)
def notify_seller_on_order(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            user=instance.seller,
            type=Notification.Type.ORDER_PLACED,
            message=f"New order {instance.order_code} for {instance.quantity_kg}kg",
            reference_id=instance.id,
            reference_type='order'
        )


@receiver(post_save, sender=Bid)
def notify_farmer_on_bid(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            user=instance.listing.farmer,
            type=Notification.Type.BID_RECEIVED,
            message=f"New bid Rs{instance.bid_price_per_kg}/kg on {instance.listing.batch.batch_code}",
            reference_id=instance.id,
            reference_type='bid'
        )


@receiver(post_save, sender=Message)
def update_conversation_timestamp(sender, instance, created, **kwargs):
    if created:
        conversation = instance.conversation
        conversation.last_message_at = instance.sent_at
        conversation.save(update_fields=['last_message_at'])
