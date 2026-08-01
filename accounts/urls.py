"""
accounts/urls.py

URL routing for the accounts app: authentication,
messaging conversations, and dispute management.
"""

from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('dashboard/', views.DashboardRedirectView.as_view(), name='dashboard'),

    # Conversations
    path('conversations/', views.ConversationListView.as_view(), name='conversation_list'),
    path('conversations/<int:pk>/', views.ConversationDetailView.as_view(), name='conversation_detail'),
    path('conversations/create/<int:batch_pk>/', views.ConversationCreateView.as_view(), name='conversation_create'),

    # Disputes
    path('disputes/', views.DisputeListView.as_view(), name='dispute_list'),
    path('disputes/create/<int:order_pk>/', views.DisputeCreateView.as_view(), name='dispute_create'),
]
