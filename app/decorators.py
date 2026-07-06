from functools import wraps
from django.shortcuts import redirect
from django.http import HttpResponseForbidden


def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('app:login')
            if request.user.role not in roles:
                return HttpResponseForbidden()
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


def farmer_required(view_func):
    return role_required('farmer')(view_func)


def trader_required(view_func):
    return role_required('trader')(view_func)


def pm_required(view_func):
    return role_required('product_manager')(view_func)


def admin_required(view_func):
    return role_required('admin')(view_func)


def staff_required(view_func):
    return role_required('product_manager', 'admin')(view_func)


def trade_participant_required(view_func):
    return role_required('farmer', 'trader')(view_func)
