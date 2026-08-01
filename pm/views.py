"""
pm/views.py

Views for Product Manager functionality: dashboard with pending
batches and quality verification workflow.
"""

from django.shortcuts import redirect
from django.views.generic import TemplateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils.decorators import method_decorator
from accounts.decorators import role_required
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
        batch = self.get_object()

        if hasattr(batch, 'verification'):
            messages.warning(request, "This batch has already been verified.")
            return redirect('farmer:batch_detail', pk=batch.pk)

        form_class = self._get_verification_form_class()
        form = form_class(request.POST)
        if form.is_valid():
            verification = form.save(commit=False)
            verification.batch = batch
            verification.product_manager = request.user
            verification.save()
            batch.status = Batch.Status.VERIFIED
            batch.save(update_fields=['status'])
            messages.success(request, f"Batch {batch.batch_code} has been verified!")
            return redirect('farmer:batch_detail', pk=batch.pk)

        messages.error(request, "Please correct the errors below.")
        return self.render_to_response(self.get_context_data(form=form))
