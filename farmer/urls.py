"""
farmer/urls.py

URL routing for the farmer app: dashboard, farm management,
batch management, bids, and orders.
"""

from django.urls import path
from . import views

app_name = 'farmer'

urlpatterns = [
    path('dashboard/', views.FarmerDashboardView.as_view(), name='dashboard'),

    # Farms
    path('farms/', views.FarmListView.as_view(), name='farm_list'),
    path('farms/create/', views.FarmCreateView.as_view(), name='farm_create'),

    # Batches
    path('batches/', views.BatchListView.as_view(), name='batch_list'),
    path('batches/create/', views.BatchCreateView.as_view(), name='batch_create'),
    path('batches/<int:pk>/', views.BatchDetailView.as_view(), name='batch_detail'),

    # Bids
    path('bids/', views.MyBidsView.as_view(), name='my_bids'),
    path('bids/<int:pk>/accept/', views.AcceptBidView.as_view(), name='accept_bid'),

    # Orders
    path('orders/', views.OrderListView.as_view(), name='order_list'),
]
