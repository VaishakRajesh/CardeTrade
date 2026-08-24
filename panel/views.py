"""
panel/views.py

Views for the admin panel: dashboard, PM account management
(approve/reject), and dispute resolution.
"""

from django.shortcuts import redirect, get_object_or_404
from django.views.generic import TemplateView, ListView, UpdateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.db.models import Sum
from accounts.decorators import role_required
from accounts.models import User, Dispute, AuditLog


@method_decorator(role_required('admin'), name='dispatch')
# Main admin dashboard with platform-wide statistics and recent activity
class AdminDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'panel/dashboard.html'

    # Gather user counts, batches, orders, revenue, and open disputes
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from farmer.models import Batch
        from trader.models import Order

        context['users'] = User.objects.all().order_by('-date_joined')[:10]
        context['pending_disputes'] = Dispute.objects.filter(status='open')[:5]
        context['recent_orders'] = Order.objects.all().order_by('-created_at')[:10]

        context['stats'] = {
            'total_users': User.objects.count(),
            'farmers': User.objects.filter(role='farmer').count(),
            'traders': User.objects.filter(role='trader').count(),
            'pms': User.objects.filter(role='product_manager').count(),
            'total_batches': Batch.objects.count(),
            'total_orders': Order.objects.count(),
            'revenue': Order.objects.exclude(status='cancelled').aggregate(
                total=Sum('total_amount')
            )['total'] or 0,
            'open_disputes': Dispute.objects.filter(status='open').count(),
        }
        # Pending product-manager accounts awaiting admin approval
        pending_pms = User.objects.filter(role='product_manager', is_active=False).order_by('-date_joined')
        context['pending_pms'] = pending_pms[:5]
        context['pending_pm_count'] = pending_pms.count()
        return context


# Lists product manager accounts awaiting admin approval
class PendingPMListView(LoginRequiredMixin, ListView):
    model = User
    template_name = 'panel/pm/pending.html'
    context_object_name = 'pending_pms'

    # Show only inactive PM accounts pending approval
    def get_queryset(self):
        return User.objects.filter(
            role='product_manager',
            is_active=False
        ).order_by('-date_joined')

    @method_decorator(role_required('admin'))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


# Displays the full profile of a product-manager account for admin review
@method_decorator(role_required('admin'), name='dispatch')
class PMDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'panel/pm/detail.html'

    # Load the PM account and expose it to the template as `pm`
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pm'] = get_object_or_404(
            User, pk=self.kwargs['pk'], role='product_manager'
        )
        return context


# Approves a pending PM account (sets is_active and is_verified)
class AcceptPMView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        user = get_object_or_404(User, pk=kwargs['pk'], role='product_manager', is_active=False)
        user.is_active = True
        user.is_verified = True
        user.save(update_fields=['is_active', 'is_verified'])
        # Audit: record the admin approval (R6 — every mutation is logged)
        AuditLog.objects.create(
            user=request.user,
            action='user.pm_accepted',
            table_name=AuditLog.TableType.USER,
            record_id=user.pk,
            new_value={'is_active': True, 'is_verified': True},
            ip_address=request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '')),
        )
        messages.success(request, f"PM account {user.username} has been accepted.")
        return redirect('panel:pm_pending_list')

    @method_decorator(role_required('admin'))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


# Rejects a pending PM account (leaves it inactive)
class RejectPMView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        user = get_object_or_404(User, pk=kwargs['pk'], role='product_manager', is_active=False)
        user.is_active = False
        user.save(update_fields=['is_active'])
        # Audit: record the admin rejection (R6 — every mutation is logged)
        AuditLog.objects.create(
            user=request.user,
            action='user.pm_rejected',
            table_name=AuditLog.TableType.USER,
            record_id=user.pk,
            new_value={'is_active': False},
            ip_address=request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '')),
        )
        messages.success(request, f"PM account {user.username} has been rejected.")
        return redirect('panel:pm_pending_list')

    @method_decorator(role_required('admin'))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


@method_decorator(role_required('admin'), name='dispatch')
class DisputeResolveView(LoginRequiredMixin, UpdateView):
    model = Dispute
    template_name = 'panel/disputes/resolve.html'
    fields = ['resolution', 'status']
    context_object_name = 'dispute'

    def form_valid(self, form):
        form.instance.resolved_by = self.request.user
        if form.instance.status in ['resolved', 'closed']:
            form.instance.resolved_at = timezone.now()
        form.save()
        # Audit: record the dispute resolution (R6 — every mutation is logged)
        AuditLog.objects.create(
            user=self.request.user,
            action='dispute.resolved',
            table_name=AuditLog.TableType.DISPUTE,
            record_id=form.instance.pk,
            new_value={
                'status': form.instance.status,
                'resolution': form.instance.resolution,
            },
            ip_address=self.request.META.get('HTTP_X_FORWARDED_FOR', self.request.META.get('REMOTE_ADDR', '')),
        )
        messages.success(self.request, "Dispute resolved successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('accounts:dispute_list')


# ---------------------------------------------------------------------------
# Generic admin user review (read-only) + account enable/disable actions.
# These are ADDITIVE and do not affect the PM approval workflow above.
# ---------------------------------------------------------------------------

@method_decorator(role_required('admin'), name='dispatch')
class UserDetailView(LoginRequiredMixin, TemplateView):
    """Admin read-only profile view for ANY user (farmer, trader, PM, admin)."""
    template_name = 'panel/user_detail.html'

    # Load the user by pk and expose it to the template as `u`
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['u'] = get_object_or_404(User, pk=self.kwargs['pk'])
        return context


# Deactivates a user account (revoke access); admins cannot revoke themselves
class RevokeUserView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        user = get_object_or_404(User, pk=kwargs['pk'])
        if user.pk == request.user.pk:
            messages.error(request, "You cannot revoke your own access.")
            return redirect('panel:user_detail', pk=user.pk)
        user.is_active = False
        user.save(update_fields=['is_active'])
        # Audit: record the revocation (R6 — every mutation is logged)
        AuditLog.objects.create(
            user=request.user,
            action='user.revoked',
            table_name=AuditLog.TableType.USER,
            record_id=user.pk,
            new_value={'is_active': False},
            ip_address=request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '')),
        )
        messages.success(request, f"Access revoked for {user.username}.")
        return redirect('panel:user_detail', pk=user.pk)

    @method_decorator(role_required('admin'))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


# Re-activates a previously revoked user account
class ReactivateUserView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        user = get_object_or_404(User, pk=kwargs['pk'])
        user.is_active = True
        user.save(update_fields=['is_active'])
        # Audit: record the reactivation (R6 — every mutation is logged)
        AuditLog.objects.create(
            user=request.user,
            action='user.reactivated',
            table_name=AuditLog.TableType.USER,
            record_id=user.pk,
            new_value={'is_active': True},
            ip_address=request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '')),
        )
        messages.success(request, f"Access restored for {user.username}.")
        return redirect('panel:user_detail', pk=user.pk)

    @method_decorator(role_required('admin'))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
