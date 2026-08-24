"""
trader/urls.py

URL routing for the trader app: dashboard, marketplace listings,
bidding, orders, and payments.
"""

from django.urls import path
from . import views

app_name = 'trader'

urlpatterns = [
    path('dashboard/', views.TraderDashboardView.as_view(), name='dashboard'),

    # Listings
    path('listings/', views.ListingListView.as_view(), name='listing_list'),
    path('listings/<int:pk>/', views.ListingDetailView.as_view(), name='listing_detail'),
    path('listings/<int:pk>/bid/', views.PlaceBidView.as_view(), name='place_bid'),

    # Bids
    path('bids/', views.MyBidsView.as_view(), name='my_bids'),

    # Orders
    path('orders/', views.OrderListView.as_view(), name='order_list'),
    path('orders/<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
    path('orders/<int:pk>/pay/', views.MakePaymentView.as_view(), name='order_pay'),
    path('orders/<int:pk>/track/', views.OrderTrackingCreateView.as_view(), name='order_track'),
]
