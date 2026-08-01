"""
pm/admin.py

Admin configuration for the QualityVerification model.
"""

from django.contrib import admin
from .models import QualityVerification


# Admin config for quality verification records
@admin.register(QualityVerification)
class QualityVerificationAdmin(admin.ModelAdmin):
    list_display = ['batch', 'grade', 'verified_price_per_kg', 'product_manager', 'verified_at']
    list_filter = ['grade']
