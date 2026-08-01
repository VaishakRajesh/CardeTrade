"""
accounts/decorators.py

Provides role-based access control decorators for views.
Enforces that only users with specified roles can access certain views.
"""

from functools import wraps
from django.shortcuts import redirect
from django.http import HttpResponseForbidden


# Generic decorator: restricts access to users with any of the given roles
def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('accounts:login')
            if request.user.role not in roles:
                return HttpResponseForbidden()
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


# Restrict view to farmers only
def farmer_required(view_func):
    return role_required('farmer')(view_func)


# Restrict view to traders only
def trader_required(view_func):
    return role_required('trader')(view_func)


# Restrict view to product managers only
def pm_required(view_func):
    return role_required('product_manager')(view_func)


# Restrict view to admins only
def admin_required(view_func):
    return role_required('admin')(view_func)


# Restrict view to staff roles (product manager or admin)
def staff_required(view_func):
    return role_required('product_manager', 'admin')(view_func)


# Restrict view to trade participants (farmer or trader)
def trade_participant_required(view_func):
    return role_required('farmer', 'trader')(view_func)
