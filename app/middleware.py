"""
CardeTrade Django Middleware - Audit Trail Support

This module provides middleware for capturing the current user and IP address
for audit logging purposes.

The middleware stores user/IP in thread-local storage so they can be accessed
from anywhere in the request cycle (models, views, signals).

How it works:
1. Middleware captures user and IP at start of each request
2. Stores them in thread-local storage (thread-safe)
3. Helper functions retrieve them for audit logging
4. AuditLog model uses these to record who made changes

Usage:
    from .middleware import get_current_user, get_current_ip

    user = get_current_user()  # Returns current User or None
    ip = get_current_ip()      # Returns IP address string
"""

import threading
from django.utils.deprecation import MiddlewareMixin

# Thread-local storage for request-specific data
_thread_locals = threading.local()


def get_current_user():
    """
    Get the current user from thread-local storage.

    Returns:
        User: The current authenticated user, or None if not logged in

    Usage:
        from .middleware import get_current_user
        user = get_current_user()
        if user:
            print(f"User {user.username} is making this request")
    """
    return getattr(_thread_locals, 'user', None)


def get_current_ip():
    """
    Get the current user's IP address from thread-local storage.

    Returns:
        str: IP address string, or empty string if not available

    Usage:
        from .middleware import get_current_ip
        ip = get_current_ip()
        print(f"Request from IP: {ip}")
    """
    return getattr(_thread_locals, 'ip', None)


class AuditMiddleware(MiddlewareMixin):
    """
    Middleware to capture user and IP for audit logging.

    This middleware runs at the start of every request and stores
    the user and IP address in thread-local storage. This allows
    models and signals to access the current request context.

    The middleware is added to MIDDLEWARE in settings.py:
        'app.middleware.AuditMiddleware'

    Thread-local storage is used because:
    - Each request runs in its own thread
    - Data is isolated between threads
    - No need to pass user/IP through function parameters
    """

    def process_request(self, request):
        """
        Capture user and IP at start of request.

        This method is called by Django for every request before
        the view is executed.
        """
        # Store current user (may be AnonymousUser if not logged in)
        _thread_locals.user = getattr(request, 'user', None)
        # Store client IP address (handles X-Forwarded-For for proxies)
        _thread_locals.ip = request.META.get('REMOTE_ADDR', '')
