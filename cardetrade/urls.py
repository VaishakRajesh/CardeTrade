"""
CardeTrade Root URL Configuration

This is the main URL configuration for the CardeTrade project.
It routes incoming requests to the appropriate app.

URL Structure:
- /admin/: Django admin panel
- /: All app URLs (handled by app.urls)

Static/Media Files:
- Media files (user uploads) are served in development mode
- In production, use a web server (nginx, Apache) for static files

Notes:
- The admin panel is accessible at /admin/
- All app URLs are prefixed with root (/)
- Media files are served from MEDIA_ROOT in development
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),  # Django admin panel
    path('', include('app.urls')),  # Include all app URLs
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)  # Serve media files in dev
