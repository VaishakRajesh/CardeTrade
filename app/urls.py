from django.urls import path
from . import views

app_name = 'app'

urlpatterns = [
    # Authentication
    path('', views.HomeView.as_view(), name='home'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('profile/', views.ProfileView.as_view(), name='profile'),

    # Dashboards
    path('dashboard/', views.DashboardRedirectView.as_view(), name='dashboard'),
    path('dashboard/farmer/', views.FarmerDashboardView.as_view(), name='farmer_dashboard'),
    path('dashboard/trader/', views.TraderDashboardView.as_view(), name='trader_dashboard'),
    path('dashboard/pm/', views.PMDashboardView.as_view(), name='pm_dashboard'),
    path('dashboard/admin/', views.AdminDashboardView.as_view(), name='admin_dashboard'),

    # Batches
    path('batches/', views.BatchListView.as_view(), name='batch_list'),
    path('batches/create/', views.BatchCreateView.as_view(), name='batch_create'),
    path('batches/<int:pk>/', views.BatchDetailView.as_view(), name='batch_detail'),
    path('batches/<int:pk>/verify/', views.BatchVerifyView.as_view(), name='batch_verify'),

    # Listings
    path('listings/', views.ListingListView.as_view(), name='listing_list'),
    path('listings/<int:pk>/', views.ListingDetailView.as_view(), name='listing_detail'),
    path('listings/<int:pk>/bid/', views.PlaceBidView.as_view(), name='place_bid'),
    path('listings/<int:pk>/buy/', views.DirectBuyView.as_view(), name='direct_buy'),

    # Bids
    path('bids/', views.MyBidsView.as_view(), name='my_bids'),

    # Orders
    path('orders/', views.OrderListView.as_view(), name='order_list'),
    path('orders/<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),

    # Farms
    path('farms/', views.FarmListView.as_view(), name='farm_list'),
    path('farms/create/', views.FarmCreateView.as_view(), name='farm_create'),

    # Conversations
    path('conversations/', views.ConversationListView.as_view(), name='conversation_list'),
    path('conversations/<int:pk>/', views.ConversationDetailView.as_view(), name='conversation_detail'),
    path('conversations/create/<int:batch_pk>/', views.ConversationCreateView.as_view(), name='conversation_create'),

    # Disputes
    path('disputes/', views.DisputeListView.as_view(), name='dispute_list'),
    path('disputes/create/<int:order_pk>/', views.DisputeCreateView.as_view(), name='dispute_create'),
    path('disputes/<int:pk>/resolve/', views.DisputeResolveView.as_view(), name='dispute_resolve'),

    # Notifications
    path('notifications/', views.NotificationListView.as_view(), name='notification_list'),
    path('notifications/mark-read/', views.NotificationMarkReadView.as_view(), name='notification_mark_read'),
]
