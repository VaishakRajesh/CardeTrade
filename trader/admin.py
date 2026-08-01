"""
trader/admin.py

Admin configuration for trading models: Listing, Bid, Order,
OrderTracking, and Payment.
"""

from django.contrib import admin
from .models import Listing, Bid, Order, OrderTracking, Payment


# Admin config for auction listings
@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ['id', 'batch', 'farmer', 'listing_type', 'price_per_kg', 'available_qty_kg', 'is_active', 'created_at']
    list_filter = ['listing_type', 'is_active', 'created_at']
    search_fields = ['batch__batch_code', 'farmer__username']
    list_editable = ['is_active']
    date_hierarchy = 'created_at'


# Admin config for bids placed on listings
@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = ['id', 'listing', 'trader', 'bid_price_per_kg', 'quantity_kg', 'status', 'bid_time']
    list_filter = ['status']


# Admin config for purchase orders
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_code', 'buyer', 'seller', 'quantity_kg', 'total_amount', 'status', 'created_at']
    list_filter = ['status', 'payment_status']


# Admin config for order tracking entries
@admin.register(OrderTracking)
class OrderTrackingAdmin(admin.ModelAdmin):
    list_display = ['order', 'status', 'location', 'updated_by', 'tracked_at']


# Admin config for payment records
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'amount', 'payment_method', 'status', 'paid_at']
    list_filter = ['status', 'payment_method']
