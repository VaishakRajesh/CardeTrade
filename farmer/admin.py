"""
farmer/admin.py

Admin configuration for Farm and Batch models.
"""

from django.contrib import admin
from .models import Farm, Batch


# Admin config for the Farm model
@admin.register(Farm)
class FarmAdmin(admin.ModelAdmin):
    list_display = ['farm_name', 'farmer', 'region', 'total_area_acres', 'created_at']
    list_filter = ['region']


# Admin config for the Batch model with an action to revoke batches
@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ['batch_code', 'farmer', 'quantity_kg', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['batch_code', 'farmer__username']
    readonly_fields = ['batch_code']
    actions = ['revoke_batches']

    # Admin action to set selected batches to REJECTED status
    def revoke_batches(self, request, queryset):
        updated = queryset.update(status=Batch.Status.REJECTED)
        self.message_user(request, f'{updated} batch(es) revoked.')
    revoke_batches.short_description = 'Revoke selected batches (set to REJECTED)'
