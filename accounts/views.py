"""
accounts/views.py

Handles user-facing views: registration, login/logout, profile
management, messaging conversations, and dispute handling.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, CreateView, ListView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.http import HttpResponseForbidden
from django.db.models import Q
from .decorators import role_required
from .forms import RegistrationForm, LoginForm, UserProfileForm
from accounts.models import User, Conversation, ConversationParticipant, Message, Dispute, AuditLog
from farmer.models import Batch
from trader.models import Order


# Landing page showing active listings and platform statistics
class HomeView(TemplateView):
    template_name = 'accounts/dashboard/home.html'

    # Add recent listings and user/batch/order counts to the template context
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from trader.models import Listing
        context['listings'] = Listing.objects.filter(is_active=True).select_related('batch', 'farmer')[:6]
        context['stats'] = {
            'farmers': User.objects.filter(role='farmer').count(),
            'traders': User.objects.filter(role='trader').count(),
            'batches': Batch.objects.count(),
            'orders': Order.objects.count(),
        }
        return context


# Handles new user registration with role selection and document upload
class RegisterView(CreateView):
    form_class = RegistrationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:dashboard')

    # Create user, handle auto-login, and show role-specific messages
    def form_valid(self, form):
        user = form.save(commit=False)
        doc = form.cleaned_data.get('verification_doc')
        if doc:
            user.verification_doc = doc
        user.save()
        if user.role == 'product_manager':
            messages.info(self.request, 'Your account requires admin approval. You can browse the platform in the meantime.')
            return redirect(self.get_success_url())
        login(self.request, user)
        if user.role == 'farmer':
            messages.info(self.request, 'Your account requires verification. An admin will review your documents shortly.')
        else:
            messages.success(self.request, f"Welcome to CardeTrade, {user.username}!")
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('accounts:dashboard')


# Handles user login with email-based authentication
class LoginView(TemplateView):
    template_name = 'accounts/login.html'

    # Pass the login form to the template (preserves bound form with errors on failed POST)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'form' not in kwargs:
            context['form'] = LoginForm()
        return context

    # Validate credentials and log the user in on success
    def post(self, request, *args, **kwargs):
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {user.username}!")
                return redirect('accounts:dashboard')
        messages.error(request, "Invalid email or password.")
        return self.render_to_response(self.get_context_data(form=form))

    # Redirect authenticated users away from the login page
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('accounts:dashboard')
        return super().get(request, *args, **kwargs)


# Logs the user out and redirects to the login page
class LogoutView(TemplateView):
    def get(self, request, *args, **kwargs):
        logout(request)
        messages.info(request, "You have been logged out.")
        return redirect('accounts:login')


# Allows authenticated users to view/edit profile and change password on the same page (all roles)
class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/profile.html'

    # Provide both forms: profile_form/form (same object for backwards compat) + password_form
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'profile_form' not in kwargs and 'form' not in kwargs:
            profile_form = UserProfileForm(instance=self.request.user)
            context['profile_form'] = profile_form
            context['form'] = profile_form
        elif 'profile_form' in kwargs:
            context['form'] = kwargs['profile_form']
        if 'password_form' not in kwargs:
            # kwargs may already contain password_form on POST error re-render
            if 'password_form' not in context:
                context['password_form'] = PasswordChangeForm(user=self.request.user)
        return context

    def post(self, request, *args, **kwargs):
        # Determine which card was submitted by button name
        if 'update_profile' in request.POST:
            profile_form = UserProfileForm(request.POST, instance=request.user)
            password_form = PasswordChangeForm(user=request.user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Profile updated successfully!")
                return redirect('accounts:profile')
            # Re-render with profile errors, keep empty password form
            return self.render_to_response(self.get_context_data(profile_form=profile_form, password_form=password_form))

        elif 'change_password' in request.POST:
            profile_form = UserProfileForm(instance=request.user)
            password_form = PasswordChangeForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                # Audit compliance (R6) — log password change, ignore audit failures
                try:
                    AuditLog.objects.create(
                        user=request.user,
                        action='user.password_changed',
                        table_name=AuditLog.TableType.USER,
                        record_id=request.user.pk,
                        ip_address=request.META.get('REMOTE_ADDR', ''),
                    )
                except Exception:
                    pass
                messages.success(request, "Password changed successfully!")
                return redirect('accounts:profile')
            return self.render_to_response(self.get_context_data(profile_form=profile_form, password_form=password_form))

        # Fallback (no recognized button) — treat as profile update
        return self.get(request, *args, **kwargs)


# Redirects users to their role-specific dashboard after login
class DashboardRedirectView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        role = request.user.role
        if role == 'farmer':
            return redirect('farmer:dashboard')
        elif role == 'trader':
            return redirect('trader:dashboard')
        elif role == 'product_manager':
            return redirect('pm:dashboard')
        elif role == 'admin':
            return redirect('panel:dashboard')
        return redirect('accounts:home')


@method_decorator(role_required('farmer', 'trader', 'product_manager', 'admin'), name='dispatch')
# Lists all active conversations the current user is participating in
class ConversationListView(LoginRequiredMixin, ListView):
    model = Conversation
    template_name = 'accounts/messaging/conversation_list.html'
    context_object_name = 'conversations'

    # Filter conversations to only those where the user is an active participant
    def get_queryset(self):
        return Conversation.objects.filter(
            participants__user=self.request.user,
            participants__is_active=True
        ).prefetch_related('participants__user').order_by('-last_message_at')


@method_decorator(role_required('farmer', 'trader', 'product_manager', 'admin'), name='dispatch')
# Displays a single conversation and allows sending new messages
class ConversationDetailView(LoginRequiredMixin, DetailView):
    model = Conversation
    template_name = 'accounts/messaging/conversation_detail.html'
    context_object_name = 'conversation'

    # Ensure user is an active participant, prefetch messages and participants
    def get_queryset(self):
        return Conversation.objects.filter(
            participants__user=self.request.user,
            participants__is_active=True
        ).prefetch_related('messages__sender', 'participants__user')

    # Mark messages as read by updating the user's last_read_at timestamp
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        participant = self.object.participants.filter(user=self.request.user).first()
        if participant:
            participant.last_read_at = timezone.now()
            participant.save(update_fields=['last_read_at'])
        return context

    # Handle sending a new message in this conversation
    def post(self, request, *args, **kwargs):
        conversation = self.get_object()
        content = request.POST.get('content', '').strip()
        if content:
            Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=content
            )
        return redirect('accounts:conversation_detail', pk=conversation.pk)


@method_decorator(role_required('farmer', 'trader'), name='dispatch')
# Creates a new conversation tied to a specific batch
class ConversationCreateView(LoginRequiredMixin, CreateView):
    model = Conversation
    template_name = 'accounts/messaging/conversation_create.html'
    fields = ['subject']

    # Look up the batch from the URL and make it available to the view
    def dispatch(self, request, *args, **kwargs):
        self.batch = get_object_or_404(Batch, pk=kwargs.get('batch_pk', 0))
        return super().dispatch(request, *args, **kwargs)

    # Save the conversation, add participants (current user + batch farmer/PM)
    def form_valid(self, form):
        form.instance.batch = self.batch
        form.instance.type = Conversation.Type.BATCH_INQUIRY
        form.save()

        ConversationParticipant.objects.create(
            conversation=form.instance,
            user=self.request.user,
            role_in_chat=self.request.user.role
        )

        other_user = self.batch.farmer if self.request.user != self.batch.farmer else User.objects.filter(role='product_manager').first()
        if other_user:
            ConversationParticipant.objects.create(
                conversation=form.instance,
                user=other_user,
                role_in_chat='product_manager' if other_user.role == 'product_manager' else 'farmer'
            )
        messages.success(request, "Conversation started!")
        return redirect('accounts:conversation_detail', pk=form.instance.pk)

    def get_success_url(self):
        return reverse('accounts:conversation_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['batch'] = self.batch
        return context


@method_decorator(role_required('farmer', 'trader'), name='dispatch')
# Allows a buyer or seller to raise a dispute on an order
class DisputeCreateView(LoginRequiredMixin, CreateView):
    model = Dispute
    template_name = 'accounts/disputes/create.html'
    fields = ['reason']

    # Verify the user is a participant in the order before allowing dispute creation
    def dispatch(self, request, *args, **kwargs):
        self.order = get_object_or_404(Order, pk=kwargs['order_pk'])
        if request.user != self.order.buyer and request.user != self.order.seller:
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.order = self.order
        form.instance.raised_by = self.request.user
        form.instance.against_user = self.order.seller if self.request.user == self.order.buyer else self.order.buyer
        form.save()
        self.order.status = Order.Status.DISPUTED
        self.order.save(update_fields=['status'])
        messages.success(request, "Dispute raised. An admin will review it shortly.")
        return redirect('accounts:dispute_list')

    def get_success_url(self):
        return reverse('accounts:dispute_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['order'] = self.order
        return context


@method_decorator(role_required('farmer', 'trader', 'product_manager', 'admin'), name='dispatch')
# Lists disputes — admins see all, others see only their own
class DisputeListView(LoginRequiredMixin, ListView):
    model = Dispute
    template_name = 'accounts/disputes/list.html'
    context_object_name = 'disputes'
    paginate_by = 10

    # Admins see all disputes; regular users see only those they are involved in
    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return Dispute.objects.all().select_related('order', 'raised_by', 'against_user')
        return Dispute.objects.filter(
            Q(raised_by=user) | Q(against_user=user)
        ).select_related('order', 'raised_by')
