"""
chat/urls.py

URL routing for the AI chatbot API endpoint.
"""

from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    # POST endpoint for sending messages to the AI chatbot
    path('chat/api/', views.ChatBotAPIView.as_view(), name='chat_api'),
]
