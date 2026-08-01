"""
accounts/middleware.py

Middleware that captures the current user and IP address
per request thread for use in audit logging.
"""

import threading

_thread_locals = threading.local()


# Retrieve the current user from thread-local storage
def get_current_user():
    return getattr(_thread_locals, 'user', None)


# Retrieve the current request IP from thread-local storage
def get_current_ip():
    return getattr(_thread_locals, 'ip', '')


# Middleware that stores the current user and IP per-thread for audit logging
class AuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.user = getattr(request, 'user', None)
        _thread_locals.ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', ''))
        return self.get_response(request)
