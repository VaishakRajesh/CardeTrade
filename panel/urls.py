"""
panel/urls.py

URL routing for the admin panel: dashboard, product manager
account management (approve/reject), and dispute resolution.
"""

from django.urls import path
from . import views

app_name = 'panel'

urlpatterns = [
    # Admin dashboard with platform-wide statistics
    path('dashboard/', views.AdminDashboardView.as_view(), name='dashboard'),

    # Admin lists (Recent Orders / Recent Users)
    path('orders/', views.RecentOrdersView.as_view(), name='recent_orders'),
    path('users/', views.RecentUsersView.as_view(), name='recent_users'),

    # PM Management
    path('pm/pending/', views.PendingPMListView.as_view(), name='pm_pending_list'),
    path('pm/<int:pk>/', views.PMDetailView.as_view(), name='pm_detail'),
    path('pm/<int:pk>/accept/', views.AcceptPMView.as_view(), name='pm_accept'),
    path('pm/<int:pk>/reject/', views.RejectPMView.as_view(), name='pm_reject'),

    # User management (admin review + enable/disable) — additive, separate from PM approval
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user_detail'),
    path('users/<int:pk>/revoke/', views.RevokeUserView.as_view(), name='user_revoke'),
    path('users/<int:pk>/reactivate/', views.ReactivateUserView.as_view(), name='user_reactivate'),

    # Disputes
    path('disputes/<int:pk>/resolve/', views.DisputeResolveView.as_view(), name='dispute_resolve'),
]
