"""
cardetrade/urls.py

Root URL configuration for the CardeTrade platform.
Routes requests to the appropriate app based on URL prefix:

URL Structure:
- /                    → Redirects to home page
- /admin/              → Django admin panel
- /accounts/           → Authentication, conversations, disputes
- /farmer/             → Farms, batches, farmer actions
- /trader/             → Listings, bids, orders, payments
- /pm/                 → Product manager quality verification
- /panel/              → Admin panel (PM approval, dispute resolution)
- /chat/api/           → AI chatbot API endpoint

Static/Media Files:
- Media files (user uploads) are served in development mode
- In production, use a web server (nginx, Apache) for static files

Notes:
- The admin panel is accessible at /admin/
- Media files are served from MEDIA_ROOT in development only
- Ordered so that root-level URLs don't conflict with app prefixes
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='accounts:home'), name='root_home'),  # Root → accounts home
    path('admin/', admin.site.urls),   # Django admin panel
    path('accounts/', include('accounts.urls')),  # Auth, conversations, disputes
    path('farmer/', include('farmer.urls')),      # Farms, batches, farmer actions
    path('trader/', include('trader.urls')),      # Listings, bids, orders, payments
    path('pm/', include('pm.urls')),              # PM quality verification
    path('panel/', include('panel.urls')),        # Admin panel
    path('', include('chat.urls')),               # AI chatbot API
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)  # Serve media files in dev
