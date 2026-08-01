"""
pm/models.py

Defines the QualityVerification model used by Product Managers
to grade and set prices for farmer-submitted cardamom batches.
"""

from django.db import models
from django.conf import settings
from farmer.models import Batch


# Records quality inspection results for a single batch of cardamom
class QualityVerification(models.Model):
    # Quality grades: A (premium), B (good), C (lower)
    class Grade(models.TextChoices):
        A = 'A', 'Grade A'
        B = 'B', 'Grade B'
        C = 'C', 'Grade C'

    batch = models.OneToOneField(Batch, on_delete=models.CASCADE, related_name='verification')
    product_manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='verifications'
    )
    grade = models.CharField(max_length=1, choices=Grade.choices)
    moisture_content_pct = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    aroma_score = models.PositiveSmallIntegerField(null=True, blank=True)
    color_score = models.PositiveSmallIntegerField(null=True, blank=True)
    purity_pct = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    verified_price_per_kg = models.DecimalField(max_digits=10, decimal_places=2)
    remarks = models.TextField(blank=True, default='')
    verified_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'quality verifications'

    def __str__(self):
        return f"Batch {self.batch.batch_code} -> Grade {self.grade}"
