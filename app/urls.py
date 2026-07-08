"""
CardeTrade App URL Configuration

This module defines all URL patterns for the 'app' application.
URLs are organized by feature area:

1. Authentication: register, login, logout, profile
2. Dashboards: Role-specific dashboards
3. Batches: CRUD operations for cardamom batches
4. Listings: Marketplace listings
5. Bids: Auction bidding
6. Orders: Purchase orders
7. Farms: Farm management
8. Conversations: Messaging system
9. Disputes: Order disputes
10. Notifications: User notifications

URL Naming Convention:
- All URLs use app_name = 'app' namespace
- URL names use snake_case
- Access via {% url 'app:url_name' %} in templates
- Access via reverse('app:url_name') in Python

URL Parameters:
- <int:pk>: Primary key for detail/edit views
- <int:batch_pk>: Batch ID for batch-related actions
- <int:order_pk>: Order ID for order-related actions
"""

from django.urls import path
from . import views

app_name = 'app'  # Namespace for URL reversal

urlpatterns = [
    # ============================================================
    # AUTHENTICATION
    # ============================================================
    path('', views.HomeView.as_view(), name='home'),  # Public homepage
    path('register/', views.RegisterView.as_view(), name='register'),  # New user registration
    path('login/', views.LoginView.as_view(), name='login'),  # User login
    path('logout/', views.LogoutView.as_view(), name='logout'),  # User logout
    path('profile/', views.ProfileView.as_view(), name='profile'),  # Edit profile

    # ============================================================
    # DASHBOARDS
    # ============================================================
    path('dashboard/', views.DashboardRedirectView.as_view(), name='dashboard'),  # Redirect by role
    path('dashboard/farmer/', views.FarmerDashboardView.as_view(), name='farmer_dashboard'),  # Farmer view
    path('dashboard/trader/', views.TraderDashboardView.as_view(), name='trader_dashboard'),  # Trader view
    path('dashboard/pm/', views.PMDashboardView.as_view(), name='pm_dashboard'),  # PM view
    path('dashboard/admin/', views.AdminDashboardView.as_view(), name='admin_dashboard'),  # Admin view

    # ============================================================
    # BATCHES
    # ============================================================
    path('batches/', views.BatchListView.as_view(), name='batch_list'),  # List all batches
    path('batches/create/', views.BatchCreateView.as_view(), name='batch_create'),  # Create new batch
    path('batches/<int:pk>/', views.BatchDetailView.as_view(), name='batch_detail'),  # View batch details
    path('batches/<int:pk>/verify/', views.BatchVerifyView.as_view(), name='batch_verify'),  # Verify batch quality

    # ============================================================
    # LISTINGS (MARKETPLACE)
    # ============================================================
    path('listings/', views.ListingListView.as_view(), name='listing_list'),  # Browse listings
    path('listings/<int:pk>/', views.ListingDetailView.as_view(), name='listing_detail'),  # View listing
    path('listings/<int:pk>/bid/', views.PlaceBidView.as_view(), name='place_bid'),  # Place bid (auction)
    path('listings/<int:pk>/buy/', views.DirectBuyView.as_view(), name='direct_buy'),  # Buy now (fixed price)

    # ============================================================
    # BIDS
    # ============================================================
    path('bids/', views.MyBidsView.as_view(), name='my_bids'),  # View my bids

    # ============================================================
    # ORDERS
    # ============================================================
    path('orders/', views.OrderListView.as_view(), name='order_list'),  # List orders
    path('orders/<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),  # View order details

    # ============================================================
    # FARMS
    # ============================================================
    path('farms/', views.FarmListView.as_view(), name='farm_list'),  # List my farms
    path('farms/create/', views.FarmCreateView.as_view(), name='farm_create'),  # Register new farm

    # ============================================================
    # CONVERSATIONS (MESSAGING)
    # ============================================================
    path('conversations/', views.ConversationListView.as_view(), name='conversation_list'),  # List conversations
    path('conversations/<int:pk>/', views.ConversationDetailView.as_view(), name='conversation_detail'),  # View conversation
    path('conversations/create/<int:batch_pk>/', views.ConversationCreateView.as_view(), name='conversation_create'),  # Start new conversation

    # ============================================================
    # DISPUTES
    # ============================================================
    path('disputes/', views.DisputeListView.as_view(), name='dispute_list'),  # List disputes
    path('disputes/create/<int:order_pk>/', views.DisputeCreateView.as_view(), name='dispute_create'),  # Raise dispute
    path('disputes/<int:pk>/resolve/', views.DisputeResolveView.as_view(), name='dispute_resolve'),  # Resolve dispute

    # ============================================================
    # NOTIFICATIONS
    # ============================================================
    path('notifications/', views.NotificationListView.as_view(), name='notification_list'),  # List notifications
    path('notifications/mark-read/', views.NotificationMarkReadView.as_view(), name='notification_mark_read'),  # Mark all read
]
