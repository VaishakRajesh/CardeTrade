"""
pm/urls.py

URL routing for the Product Manager app: dashboard
and batch quality verification.
"""

from django.urls import path
from . import views

app_name = 'pm'

urlpatterns = [
    path('dashboard/', views.PMDashboardView.as_view(), name='dashboard'),
    path('batches/<int:pk>/verify/', views.BatchVerifyView.as_view(), name='batch_verify'),
]
