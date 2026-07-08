"""
CardeTrade Django Decorators - Role-Based Access Control

This module provides decorators for restricting view access based on user roles.
Decorators are used to enforce permissions at the view level.

Decorator Usage:
- @role_required('farmer'): Only farmers can access
- @role_required('trader'): Only traders can access
- @role_required('product_manager'): Only PMs can access
- @role_required('admin'): Only admins can access
- @role_required('farmer', 'trader'): Farmers and traders can access

How it works:
1. Checks if user is authenticated (redirects to login if not)
2. Checks if user's role is in the allowed roles list
3. Returns 403 Forbidden if role doesn't match
4. Calls the view function if authorized

Example:
    @role_required('farmer')
    def create_batch(request):
        # Only farmers can reach this code
        ...
"""

from functools import wraps
from django.shortcuts import redirect
from django.http import HttpResponseForbidden


def role_required(*roles):
    """
    Decorator that restricts view access to users with specific roles.

    Args:
        *roles: One or more role strings (e.g., 'farmer', 'trader')

    Returns:
        Decorated view function that checks role before execution

    Usage:
        @role_required('farmer')
        def my_view(request):
            ...

        @role_required('farmer', 'trader')
        def my_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            # Check if user is logged in
            if not request.user.is_authenticated:
                return redirect('app:login')
            # Check if user has required role
            if request.user.role not in roles:
                return HttpResponseForbidden()  # 403 Forbidden
            # User is authorized, call the view
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


def farmer_required(view_func):
    """Shorthand decorator: only farmers can access."""
    return role_required('farmer')(view_func)


def trader_required(view_func):
    """Shorthand decorator: only traders can access."""
    return role_required('trader')(view_func)


def pm_required(view_func):
    """Shorthand decorator: only product managers can access."""
    return role_required('product_manager')(view_func)


def admin_required(view_func):
    """Shorthand decorator: only admins can access."""
    return role_required('admin')(view_func)


def staff_required(view_func):
    """Shorthand decorator: PMs and admins can access (staff members)."""
    return role_required('product_manager', 'admin')(view_func)


def trade_participant_required(view_func):
    """Shorthand decorator: farmers and traders can access (buyers and sellers)."""
    return role_required('farmer', 'trader')(view_func)
