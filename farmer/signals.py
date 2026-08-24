"""
farmer/signals.py

Signal handlers for the farmer app.
Automatically creates a Listing when a batch is verified by a PM.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone as tz
from .models import Batch


# When a batch is verified, auto-create a trader listing and set status to LISTED
@receiver(post_save, sender=Batch)
def create_listing_on_verification(sender, instance, created, **kwargs):
    if instance.status == Batch.Status.VERIFIED:
        try:
            verification = instance.verification
        except Batch.verification.RelatedObjectDoesNotExist:
            return

        from trader.models import Listing as TraderListing
        # Only AUCTION listings are created today (see trader.models.Listing.ListingType).
        TraderListing.objects.get_or_create(
            batch=instance,
            defaults={
                'farmer': instance.farmer,
                'listing_type': TraderListing.ListingType.AUCTION,
                'price_per_kg': verification.verified_price_per_kg,
                'available_qty_kg': instance.quantity_kg,
                'auction_start_time': tz.now(),
                'auction_end_time': tz.now() + tz.timedelta(days=7),
            }
        )
        instance.status = Batch.Status.LISTED
        instance.save(update_fields=['status'])
