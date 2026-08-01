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

    # PM Management
    path('pm/pending/', views.PendingPMListView.as_view(), name='pm_pending_list'),
    path('pm/<int:pk>/accept/', views.AcceptPMView.as_view(), name='pm_accept'),
    path('pm/<int:pk>/reject/', views.RejectPMView.as_view(), name='pm_reject'),

    # Disputes
    path('disputes/<int:pk>/resolve/', views.DisputeResolveView.as_view(), name='dispute_resolve'),
]
