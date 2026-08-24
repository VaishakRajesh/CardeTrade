"""
pm/views.py

Views for Product Manager functionality: dashboard with pending
batches and quality verification workflow.
"""

from django.shortcuts import redirect
from django.views import View
from django.views.generic import TemplateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.db import transaction
from django.utils import timezone
from accounts.decorators import role_required
from accounts.models import AuditLog
from farmer.models import Batch
from pm.models import QualityVerification


@method_decorator(role_required('product_manager'), name='dispatch')
# PM dashboard showing pending and under-review batches with verification stats
class PMDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'pm/dashboard.html'

    # Load pending batches, batches under review, and recent verifications by this PM
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['pending_batches'] = Batch.objects.filter(status='pending').select_related('farmer')[:50]
        context['under_review'] = Batch.objects.filter(status='under_review').select_related('farmer')[:50]
        context['recent_verifications'] = QualityVerification.objects.filter(product_manager=user).select_related('batch')[:50]

        context['stats'] = {
            'pending_review': Batch.objects.filter(status='pending').count(),
            'under_review': Batch.objects.filter(status='under_review').count(),
            'verified_today': QualityVerification.objects.filter(product_manager=user).count(),
            'total_verified': QualityVerification.objects.count(),
        }
        return context


@method_decorator(role_required('product_manager'), name='dispatch')
# Handles the quality verification form for a single batch
class BatchVerifyView(LoginRequiredMixin, UpdateView):
    model = Batch
    template_name = 'pm/batches/verify.html'
    context_object_name = 'batch'
    fields = []

    # Hide the form if the batch has already been verified
    def get_context_data(self, **kwargs):
        if hasattr(self.object, 'verification'):
            kwargs['form'] = None
        return super().get_context_data(**kwargs)

    # Remove the model instance from form kwargs since we're verifying, not editing the batch
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.pop('instance', None)
        return kwargs

    # Return a dynamically built ModelForm for QualityVerification
    def get_form_class(self):
        return self._get_verification_form_class()

    # Build the verification form class lazily
    @staticmethod
    def _get_verification_form_class():
        from django import forms as dj_forms
        class VForm(dj_forms.ModelForm):
            class Meta:
                model = QualityVerification
                fields = ['grade', 'moisture_content_pct', 'aroma_score', 'color_score', 'purity_pct', 'verified_price_per_kg', 'remarks']
                widgets = {'remarks': dj_forms.Textarea(attrs={'rows': 3})}
        return VForm

    # Process the verification: save grade/price and update batch status to VERIFIED
    def post(self, request, *args, **kwargs):
        # Lock the batch row so concurrent verifies serialize correctly
        with transaction.atomic():
            batch = Batch.objects.select_for_update().get(pk=self.kwargs['pk'])
            self.object = batch  # ensure template has `batch` on invalid re-render

            if hasattr(batch, 'verification'):
                messages.warning(request, "This batch has already been verified.")
                return redirect('farmer:batch_detail', pk=batch.pk)

            # Guard: if another PM has claimed this batch for review, block
            if batch.status == Batch.Status.UNDER_REVIEW and batch.claimed_by_id and batch.claimed_by_id != request.user.pk:
                messages.warning(request, f"This batch is currently being reviewed by {batch.claimed_by.username}.")
                return redirect('farmer:batch_detail', pk=batch.pk)

            # Implicitly claim the batch to the current PM if not already claimed
            if batch.status in (Batch.Status.PENDING, Batch.Status.UNDER_REVIEW) and batch.claimed_by_id is None:
                batch.status = Batch.Status.UNDER_REVIEW
                batch.claimed_by = request.user
                batch.claimed_at = timezone.now()
                batch.save(update_fields=['status', 'claimed_by', 'claimed_at'])

            form_class = self._get_verification_form_class()
            form = form_class(request.POST)
            if form.is_valid():
                verification = form.save(commit=False)
                verification.batch = batch
                verification.product_manager = request.user
                verification.save()
                batch.status = Batch.Status.VERIFIED
                batch.save(update_fields=['status'])
                # Audit: record verification (R6 — every mutation is logged)
                AuditLog.objects.create(
                    user=request.user,
                    action='batch.verified',
                    table_name=AuditLog.TableType.BATCH,
                    record_id=batch.pk,
                    new_value={'status': Batch.Status.VERIFIED},
                    ip_address=request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '')),
                )
                messages.success(request, f"Batch {batch.batch_code} has been verified!")
                return redirect('farmer:batch_detail', pk=batch.pk)

            messages.error(request, "Please correct the errors below.")
            return self.render_to_response(self.get_context_data(form=form))


@method_decorator(role_required('product_manager'), name='dispatch')
# Lets a PM claim a pending batch for review (sets under_review + claimed_by)
class StartReviewView(LoginRequiredMixin, View):
    # Claim the batch to the current PM; blocks if another PM already claimed it
    def post(self, request, *args, **kwargs):
        with transaction.atomic():
            # Lock the row so two PMs can't claim the same batch concurrently
            batch = Batch.objects.select_for_update().get(pk=kwargs['pk'])

            if hasattr(batch, 'verification') or batch.status == Batch.Status.VERIFIED:
                messages.warning(request, "This batch has already been verified.")
                return redirect('farmer:batch_detail', pk=batch.pk)

            # Already under review by someone else -> block
            if batch.status == Batch.Status.UNDER_REVIEW and batch.claimed_by_id and batch.claimed_by_id != request.user.pk:
                messages.warning(request, f"This batch is already being reviewed by {batch.claimed_by.username}.")
                return redirect('farmer:batch_detail', pk=batch.pk)

            # Claim it to the current PM
            batch.status = Batch.Status.UNDER_REVIEW
            batch.claimed_by = request.user
            batch.claimed_at = timezone.now()
            batch.save(update_fields=['status', 'claimed_by', 'claimed_at'])

        # Audit: record the claim (R6)
        AuditLog.objects.create(
            user=request.user,
            action='batch.claimed',
            table_name=AuditLog.TableType.BATCH,
            record_id=batch.pk,
            new_value={'status': Batch.Status.UNDER_REVIEW, 'claimed_by': request.user.pk},
            ip_address=request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '')),
        )
        messages.success(request, f"Batch {batch.batch_code} moved to review.")
        return redirect('pm:batch_verify', pk=batch.pk)

    # GET convenience: just go to the verify page
    def get(self, request, *args, **kwargs):
        return redirect('pm:batch_verify', pk=kwargs['pk'])
