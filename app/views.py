from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, CreateView, ListView, DetailView, FormView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.http import HttpResponseForbidden
from django.db.models import Count, Sum, Q
from .decorators import role_required, farmer_required, trader_required, pm_required, admin_required
from .forms import RegistrationForm, LoginForm, UserProfileForm
from .models import (
    User, Farm, Batch, QualityVerification, Listing, Bid,
    Order, OrderTracking, Payment, Dispute, Notification,
    Conversation, ConversationParticipant, Message, AuditLog
)


class HomeView(TemplateView):
    template_name = 'app/dashboard/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['listings'] = Listing.objects.filter(is_active=True).select_related('batch', 'farmer')[:6]
        context['stats'] = {
            'farmers': User.objects.filter(role='farmer').count(),
            'traders': User.objects.filter(role='trader').count(),
            'batches': Batch.objects.count(),
            'orders': Order.objects.count(),
        }
        return context


class RegisterView(CreateView):
    form_class = RegistrationForm
    template_name = 'app/auth/register.html'
    success_url = reverse_lazy('app:dashboard')

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, f"Welcome to CardeTrade, {user.username}!")
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse_lazy('app:dashboard')


class LoginView(FormView):
    form_class = LoginForm
    template_name = 'app/auth/login.html'

    def form_valid(self, form):
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(self.request, user)
            messages.success(self.request, f"Welcome back, {user.username}!")
            return redirect(self.get_success_url())
        messages.error(self.request, "Invalid username or password.")
        return self.form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('app:dashboard')

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('app:dashboard')
        return super().get(request, *args, **kwargs)


class LogoutView(TemplateView):
    def get(self, request, *args, **kwargs):
        logout(request)
        messages.info(request, "You have been logged out.")
        return redirect('app:login')


class ProfileView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserProfileForm
    template_name = 'app/auth/profile.html'
    success_url = reverse_lazy('app:profile')

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, "Profile updated successfully!")
        return super().form_valid(form)


class DashboardRedirectView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        role = request.user.role
        if role == 'farmer':
            return redirect('app:farmer_dashboard')
        elif role == 'trader':
            return redirect('app:trader_dashboard')
        elif role == 'product_manager':
            return redirect('app:pm_dashboard')
        elif role == 'admin':
            return redirect('app:admin_dashboard')
        return redirect('app:home')


@method_decorator(role_required('farmer'), name='dispatch')
class FarmerDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'app/dashboard/farmer.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['batches'] = Batch.objects.filter(farmer=user).order_by('-created_at')[:5]
        context['farms'] = Farm.objects.filter(farmer=user)
        context['listings'] = Listing.objects.filter(farmer=user).select_related('batch')[:5]
        context['orders'] = Order.objects.filter(seller=user).order_by('-created_at')[:5]
        context['bids'] = Bid.objects.filter(listing__farmer=user).select_related('trader', 'listing__batch')[:5]
        context['notifications'] = Notification.objects.filter(user=user, is_read=False)[:10]
        context['stats'] = {
            'total_batches': Batch.objects.filter(farmer=user).count(),
            'active_listings': Listing.objects.filter(farmer=user, is_active=True).count(),
            'total_orders': Order.objects.filter(seller=user).count(),
            'pending_bids': Bid.objects.filter(listing__farmer=user, status='active').count(),
        }
        return context


@method_decorator(role_required('trader'), name='dispatch')
class TraderDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'app/dashboard/trader.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['listings'] = Listing.objects.filter(is_active=True).select_related('batch', 'farmer')[:6]
        context['my_bids'] = Bid.objects.filter(trader=user).select_related('listing__batch')[:5]
        context['orders'] = Order.objects.filter(buyer=user).order_by('-created_at')[:5]
        context['notifications'] = Notification.objects.filter(user=user, is_read=False)[:10]
        context['stats'] = {
            'active_bids': Bid.objects.filter(trader=user, status='active').count(),
            'won_orders': Order.objects.filter(buyer=user).count(),
            'total_spent': Order.objects.filter(buyer=user).aggregate(total=Sum('total_amount'))['total'] or 0,
        }
        return context


@method_decorator(role_required('product_manager'), name='dispatch')
class PMDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'app/dashboard/pm.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['pending_batches'] = Batch.objects.filter(status='pending').select_related('farmer')[:10]
        context['under_review'] = Batch.objects.filter(status='under_review').select_related('farmer')[:10]
        context['recent_verifications'] = QualityVerification.objects.filter(product_manager=user).select_related('batch')[:10]
        context['notifications'] = Notification.objects.filter(user=user, is_read=False)[:10]
        context['stats'] = {
            'pending_review': Batch.objects.filter(status='pending').count(),
            'under_review': Batch.objects.filter(status='under_review').count(),
            'verified_today': QualityVerification.objects.filter(product_manager=user).count(),
            'total_verified': QualityVerification.objects.count(),
        }
        return context


@method_decorator(role_required('admin'), name='dispatch')
class AdminDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'app/dashboard/admin.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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
            'revenue': Order.objects.exclude(status='cancelled').aggregate(total=Sum('total_amount'))['total'] or 0,
            'open_disputes': Dispute.objects.filter(status='open').count(),
        }
        return context


@method_decorator(role_required('farmer'), name='dispatch')
class BatchCreateView(LoginRequiredMixin, CreateView):
    model = Batch
    template_name = 'app/batches/create.html'
    fields = ['farm', 'quantity_kg', 'harvest_date', 'description', 'estimated_price_per_kg']

    def form_valid(self, form):
        form.instance.farmer = self.request.user
        messages.success(self.request, "Batch created successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('app:batch_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['farm'].queryset = Farm.objects.filter(farmer=self.request.user)
        form.fields['farm'].required = False
        return form


class BatchListView(LoginRequiredMixin, ListView):
    model = Batch
    template_name = 'app/batches/list.html'
    context_object_name = 'batches'
    paginate_by = 12

    def get_queryset(self):
        user = self.request.user
        if user.role == 'farmer':
            return Batch.objects.filter(farmer=user).select_related('farm')
        return Batch.objects.all().select_related('farmer', 'farm')


@method_decorator(role_required('farmer', 'product_manager', 'admin', 'trader'), name='dispatch')
class BatchDetailView(LoginRequiredMixin, DetailView):
    model = Batch
    template_name = 'app/batches/detail.html'
    context_object_name = 'batch'


@method_decorator(role_required('product_manager'), name='dispatch')
class BatchVerifyView(LoginRequiredMixin, DetailView):
    model = Batch
    template_name = 'app/batches/verify.html'
    context_object_name = 'batch'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if not hasattr(self.object, 'verification'):
            context['form'] = self._get_verification_form()
        return context

    def _get_verification_form(self, data=None):
        from django import forms as dj_forms
        class VForm(dj_forms.ModelForm):
            class Meta:
                model = QualityVerification
                fields = ['grade', 'moisture_content_pct', 'aroma_score', 'color_score', 'purity_pct', 'verified_price_per_kg', 'remarks']
                widgets = {'remarks': dj_forms.Textarea(attrs={'rows': 3})}
        return VForm(data)

    def post(self, request, *args, **kwargs):
        batch = self.get_object()
        if hasattr(batch, 'verification'):
            messages.warning(request, "This batch has already been verified.")
            return redirect('app:batch_detail', pk=batch.pk)

        form = self._get_verification_form(request.POST)
        if form.is_valid():
            verification = form.save(commit=False)
            verification.batch = batch
            verification.product_manager = request.user
            verification.save()
            batch.status = Batch.Status.UNDER_REVIEW
            batch.save(update_fields=['status'])
            messages.success(request, f"Batch {batch.batch_code} has been verified!")
            return redirect('app:batch_detail', pk=batch.pk)

        messages.error(request, "Please correct the errors below.")
        return self.render_to_response(self.get_context_data(form=form))


class ListingListView(LoginRequiredMixin, ListView):
    model = Listing
    template_name = 'app/trading/listing_list.html'
    context_object_name = 'listings'
    paginate_by = 12

    def get_queryset(self):
        return Listing.objects.filter(is_active=True).select_related('batch', 'farmer')


@method_decorator(role_required('farmer', 'trader', 'product_manager', 'admin'), name='dispatch')
class ListingDetailView(LoginRequiredMixin, DetailView):
    model = Listing
    template_name = 'app/trading/listing_detail.html'
    context_object_name = 'listing'


@method_decorator(role_required('trader'), name='dispatch')
class PlaceBidView(LoginRequiredMixin, CreateView):
    model = Bid
    template_name = 'app/trading/place_bid.html'
    fields = ['bid_price_per_kg', 'quantity_kg', 'notes']

    def dispatch(self, request, *args, **kwargs):
        self.listing = get_object_or_404(Listing, pk=kwargs['pk'])
        if not self.listing.is_active:
            messages.error(request, "This listing is no longer active.")
            return redirect('app:listing_list')
        if self.listing.listing_type != 'auction':
            messages.error(request, "This listing is not an auction. Use 'Buy Now' instead.")
            return redirect('app:listing_detail', pk=self.listing.pk)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.listing = self.listing
        form.instance.trader = self.request.user
        messages.success(self.request, "Bid placed successfully!")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['listing'] = self.listing
        return context

    def get_success_url(self):
        return reverse_lazy('app:listing_detail', kwargs={'pk': self.listing.pk})


@method_decorator(role_required('trader'), name='dispatch')
class DirectBuyView(LoginRequiredMixin, TemplateView):
    template_name = 'app/trading/direct_buy.html'

    def dispatch(self, request, *args, **kwargs):
        self.listing = get_object_or_404(Listing, pk=kwargs['pk'])
        if not self.listing.is_active:
            messages.error(request, "This listing is no longer active.")
            return redirect('app:listing_list')
        if self.listing.listing_type != 'fixed_price':
            messages.error(request, "This listing is an auction. Use 'Place Bid' instead.")
            return redirect('app:listing_detail', pk=self.listing.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['listing'] = self.listing
        return context

    def post(self, request, *args, **kwargs):
        listing = self.listing
        quantity = request.POST.get('quantity_kg', listing.available_qty_kg)

        from decimal import Decimal
        try:
            quantity = Decimal(quantity)
        except (TypeError, ValueError):
            messages.error(request, "Invalid quantity.")
            return self.render_to_response(self.get_context_data())

        if quantity > listing.available_qty_kg:
            messages.error(request, f"Only {listing.available_qty_kg}kg available.")
            return self.render_to_response(self.get_context_data())

        order = Order.objects.create(
            listing=listing,
            batch=listing.batch,
            buyer=request.user,
            seller=listing.farmer,
            quantity_kg=quantity,
            price_per_kg=listing.price_per_kg,
        )

        listing.available_qty_kg -= quantity
        if listing.available_qty_kg <= 0:
            listing.is_active = False
        listing.save(update_fields=['available_qty_kg', 'is_active'])

        if listing.available_qty_kg <= 0:
            listing.batch.status = Batch.Status.SOLD
            listing.batch.save(update_fields=['status'])

        messages.success(request, f"Order {order.order_code} placed successfully!")
        return redirect('app:order_detail', pk=order.pk)


@method_decorator(role_required('trader', 'farmer'), name='dispatch')
class MyBidsView(LoginRequiredMixin, ListView):
    model = Bid
    template_name = 'app/trading/my_bids.html'
    context_object_name = 'bids'

    def get_queryset(self):
        user = self.request.user
        if user.role == 'farmer':
            return Bid.objects.filter(listing__farmer=user).select_related('trader', 'listing__batch')
        return Bid.objects.filter(trader=user).select_related('listing__batch')


@method_decorator(role_required('farmer', 'trader', 'product_manager', 'admin'), name='dispatch')
class OrderListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'app/orders/list.html'
    context_object_name = 'orders'
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        if user.role == 'farmer':
            return Order.objects.filter(seller=user).select_related('buyer', 'batch')
        elif user.role == 'trader':
            return Order.objects.filter(buyer=user).select_related('seller', 'batch')
        return Order.objects.all().select_related('buyer', 'seller', 'batch')


@method_decorator(role_required('farmer', 'trader', 'product_manager', 'admin'), name='dispatch')
class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = 'app/orders/detail.html'
    context_object_name = 'order'


@method_decorator(role_required('farmer'), name='dispatch')
class FarmListView(LoginRequiredMixin, ListView):
    model = Farm
    template_name = 'app/farms/list.html'
    context_object_name = 'farms'

    def get_queryset(self):
        return Farm.objects.filter(farmer=self.request.user)


@method_decorator(role_required('farmer'), name='dispatch')
class FarmCreateView(LoginRequiredMixin, CreateView):
    model = Farm
    template_name = 'app/farms/create.html'
    fields = ['farm_name', 'location', 'region', 'total_area_acres', 'certification']

    def form_valid(self, form):
        form.instance.farmer = self.request.user
        messages.success(self.request, "Farm registered successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('app:farm_list')


# ============================================================
# CONVERSATIONS & MESSAGING
# ============================================================

@method_decorator(role_required('farmer', 'trader', 'product_manager', 'admin'), name='dispatch')
class ConversationListView(LoginRequiredMixin, ListView):
    model = Conversation
    template_name = 'app/messaging/conversation_list.html'
    context_object_name = 'conversations'

    def get_queryset(self):
        return Conversation.objects.filter(
            participants__user=self.request.user,
            participants__is_active=True
        ).prefetch_related('participants__user').order_by('-last_message_at')


@method_decorator(role_required('farmer', 'trader', 'product_manager', 'admin'), name='dispatch')
class ConversationDetailView(LoginRequiredMixin, DetailView):
    model = Conversation
    template_name = 'app/messaging/conversation_detail.html'
    context_object_name = 'conversation'

    def get_queryset(self):
        return Conversation.objects.filter(
            participants__user=self.request.user,
            participants__is_active=True
        ).prefetch_related('messages__sender', 'participants__user')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        participant = self.object.participants.filter(user=self.request.user).first()
        if participant:
            participant.last_read_at = timezone.now()
            participant.save(update_fields=['last_read_at'])
        return context

    def post(self, request, *args, **kwargs):
        conversation = self.get_object()
        content = request.POST.get('content', '').strip()
        if content:
            Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=content
            )
        return redirect('app:conversation_detail', pk=conversation.pk)


@method_decorator(role_required('farmer', 'trader'), name='dispatch')
class ConversationCreateView(LoginRequiredMixin, CreateView):
    model = Conversation
    template_name = 'app/messaging/conversation_create.html'
    fields = ['subject']

    def dispatch(self, request, *args, **kwargs):
        self.batch = get_object_or_404(Batch, pk=kwargs.get('batch_pk', 0))
        return super().dispatch(request, *args, **kwargs)

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
        return redirect('app:conversation_detail', pk=form.instance.pk)

    def get_success_url(self):
        return reverse_lazy('app:conversation_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['batch'] = self.batch
        return context


# ============================================================
# DISPUTES
# ============================================================

@method_decorator(role_required('farmer', 'trader'), name='dispatch')
class DisputeCreateView(LoginRequiredMixin, CreateView):
    model = Dispute
    template_name = 'app/disputes/create.html'
    fields = ['reason']

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
        return redirect('app:dispute_list')

    def get_success_url(self):
        return reverse_lazy('app:dispute_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['order'] = self.order
        return context


@method_decorator(role_required('farmer', 'trader', 'product_manager', 'admin'), name='dispatch')
class DisputeListView(LoginRequiredMixin, ListView):
    model = Dispute
    template_name = 'app/disputes/list.html'
    context_object_name = 'disputes'
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return Dispute.objects.all().select_related('order', 'raised_by', 'against_user')
        return Dispute.objects.filter(
            Q(raised_by=user) | Q(against_user=user)
        ).select_related('order', 'raised_by')


@method_decorator(role_required('admin'), name='dispatch')
class DisputeResolveView(LoginRequiredMixin, UpdateView):
    model = Dispute
    template_name = 'app/disputes/resolve.html'
    fields = ['resolution', 'status']
    context_object_name = 'dispute'

    def form_valid(self, form):
        form.instance.resolved_by = self.request.user
        if form.instance.status in ['resolved', 'closed']:
            form.instance.resolved_at = timezone.now()
        messages.success(self.request, "Dispute resolved successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('app:dispute_list')


# ============================================================
# NOTIFICATIONS
# ============================================================

class NotificationListView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = 'app/notifications/list.html'
    context_object_name = 'notifications'
    paginate_by = 20

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')


class NotificationMarkReadView(LoginRequiredMixin, TemplateView):
    def post(self, request, *args, **kwargs):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        messages.success(request, "All notifications marked as read.")
        return redirect('app:notification_list')
