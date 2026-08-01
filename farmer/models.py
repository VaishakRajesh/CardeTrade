"""
farmer/models.py

Defines the Farm and Batch models for cardamom farming operations.
Farmers register their farms and create batches for quality verification.
"""

from django.db import models
from django.conf import settings
from django.utils import timezone


# Represents a farm registered by a farmer user
class Farm(models.Model):
    farmer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='farms',
        limit_choices_to={'role': 'farmer'}
    )
    farm_name = models.CharField(max_length=150)
    location = models.CharField(max_length=200, blank=True, default='')
    region = models.CharField(max_length=100, blank=True, default='')
    total_area_acres = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    certification = models.FileField(upload_to='documents/farms/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'farms'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.farm_name} ({self.farmer.username})"


# Represents a batch of cardamom submitted by a farmer for verification and sale
class Batch(models.Model):
    # Status lifecycle: pending → under_review → verified → listed → sold (or rejected)
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        UNDER_REVIEW = 'under_review', 'Under Review'
        VERIFIED = 'verified', 'Verified'
        LISTED = 'listed', 'Listed'
        SOLD = 'sold', 'Sold'
        REJECTED = 'rejected', 'Rejected'

    batch_code = models.CharField(max_length=50, unique=True, editable=False)
    farmer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='batches',
        limit_choices_to={'role': 'farmer'}
    )
    farm = models.ForeignKey(Farm, on_delete=models.SET_NULL, null=True, related_name='batches')
    quantity_kg = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='batch_images/', null=True, blank=True)
    harvest_date = models.DateField()
    description = models.TextField(blank=True, default='')
    estimated_price_per_kg = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'batches'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.batch_code} ({self.status})"

    # Auto-generate batch_code if not set (format: CDM-YYYY-NNNN)
    def save(self, *args, **kwargs):
        if not self.batch_code:
            self.batch_code = self._generate_batch_code()
        super().save(*args, **kwargs)

    # Generate a sequential batch code like CDM-2026-0001
    def _generate_batch_code(self):
        year = timezone.now().year
        last = Batch.objects.filter(batch_code__startswith=f'CDM-{year}-').order_by('batch_code').last()
        if last:
            num = int(last.batch_code.split('-')[2]) + 1
        else:
            num = 1
        return f'CDM-{year}-{num:04d}'
