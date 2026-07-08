"""
CardeTrade Django Views - All Platform Views

This module contains all the views (handlers) for the CardeTrade platform.
Views are organized by feature area:

1. Authentication: Login, Register, Logout, Profile
2. Dashboards: Role-specific dashboards (Farmer, Trader, PM, Admin)
3. Batches: Create, List, Detail, Verify
4. Trading: Listings, Bids, Direct Buy
5. Orders: List, Detail
6. Farms: List, Create
7. Messaging: Conversations, Messages
8. Disputes: Create, List, Resolve
9. Notifications: List, Mark Read

Most views use Class-Based Views (CBVs) with:
- LoginRequiredMixin: Requires authentication
- @method_decorator(role_required(...)): Restricts access by role
- Role-based queryset filtering: Users only see their own data

View Naming Convention:
- *View: Class-based view
- get_queryset(): Filters data based on user role
- get_context_data(): Adds extra context to template
- form_valid(): Handles successful form submission
"""

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
    """
    Public homepage displaying platform overview.

    Shows:
    - Featured listings (active listings with batch and farmer info)
    - Platform statistics (user counts, batch count, order count)

    Accessible to all users (no login required).
    """

    template_name = 'app/dashboard/home.html'

    def get_context_data(self, **kwargs):
        """Add listings and platform statistics to template context."""
        context = super().get_context_data(**kwargs)
        # Get 6 active listings with related batch and farmer data
        context['listings'] = Listing.objects.filter(is_active=True).select_related('batch', 'farmer')[:6]
        # Calculate platform-wide statistics
        context['stats'] = {
            'farmers': User.objects.filter(role='farmer').count(),
            'traders': User.objects.filter(role='trader').count(),
            'batches': Batch.objects.count(),
            'orders': Order.objects.count(),
        }
        return context


class RegisterView(CreateView):
    """
    User registration view for new account creation with role-based verification.

    Handles:
    - Displaying the registration form
    - Validating form data including verification docs
    - Creating new user account with pending verification for PM/Farmer
    - Auto-login after successful registration
    - Redirecting to dashboard

    Verification flow:
    - Farmer/PM: uploads doc → account created (unverified) → admin reviews
    - Trader: auto-verified, can trade immediately
    """

    form_class = RegistrationForm
    template_name = 'app/auth/register.html'
    success_url = reverse_lazy('app:dashboard')

    def form_valid(self, form):
        """Save user, handle verification doc, show role-appropriate message."""
        user = form.save(commit=False)
        doc = form.cleaned_data.get('verification_doc')
        if doc:
            user.verification_doc = doc
        user.save()
        login(self.request, user)
        if user.role in ('farmer', 'product_manager'):
            messages.info(
                self.request,
                'Your account requires verification. An admin will review your documents shortly. '
                'You can browse the platform in the meantime.'
            )
        else:
            messages.success(self.request, f"Welcome to CardeTrade, {user.username}!")
        return redirect(self.get_success_url())

    def get_success_url(self):
        """Redirect to role-specific dashboard after registration."""
        return reverse_lazy('app:dashboard')


class LoginView(FormView):
    """
    User login view for authentication.

    Handles:
    - Displaying the login form
    - Authenticating username/password
    - Logging in successful users
    - Redirecting authenticated users to dashboard
    - Showing error messages for failed login

    If user is already logged in, redirects to dashboard immediately.
    """

    form_class = LoginForm
    template_name = 'app/auth/login.html'

    def form_valid(self, form):
        """Authenticate user and log them in if credentials are valid."""
        email = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user = authenticate(username=email, password=password)
        if user is not None:
            login(self.request, user)
            messages.success(self.request, f"Welcome back, {user.username}!")
            return redirect(self.get_success_url())
        messages.error(self.request, "Invalid email or password.")
        return self.form_invalid(form)

    def get_success_url(self):
        """Redirect to role-specific dashboard after login."""
        return reverse_lazy('app:dashboard')

    def get(self, request, *args, **kwargs):
        """If user is already logged in, redirect to dashboard."""
        if request.user.is_authenticated:
            return redirect('app:dashboard')
        return super().get(request, *args, **kwargs)


class LogoutView(TemplateView):
    """
    User logout view.

    Logs out the current user and redirects to the login page.
    Uses GET method for simplicity (could use POST for security).
    """

    def get(self, request, *args, **kwargs):
        """Log out user and redirect to login page."""
        logout(request)
        messages.info(request, "You have been logged out.")
        return redirect('app:login')


class ProfileView(LoginRequiredMixin, UpdateView):
    """
    User profile view for viewing and editing profile information.

    Allows authenticated users to:
    - View their current profile details
    - Update personal information (name, email, phone, address, region)

    The get_object() method returns the current user instead of
    looking up by primary key from the URL.
    """

    model = User
    form_class = UserProfileForm
    template_name = 'app/auth/profile.html'
    success_url = reverse_lazy('app:profile')

    def get_object(self, queryset=None):
        """Return the current logged-in user instead of looking up by ID."""
        return self.request.user

    def form_valid(self, form):
        """Show success message after profile update."""
        messages.success(self.request, "Profile updated successfully!")
        return super().form_valid(form)


class DashboardRedirectView(LoginRequiredMixin, TemplateView):
    """
    Redirects users to their role-specific dashboard.

    This view acts as a single entry point that sends each user
    to the appropriate dashboard based on their role:
    - Farmer -> Farmer Dashboard
    - Trader -> Trader Dashboard
    - Product Manager -> PM Dashboard
    - Admin -> Admin Dashboard
    """

    def get(self, request, *args, **kwargs):
        """Redirect based on user role."""
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
    """
    Farmer-specific dashboard showing their farm activity.

    Displays:
    - Recent batches (last 5)
    - Their farms
    - Active listings
    - Recent orders (as seller)
    - Bids on their listings
    - Unread notifications
    - Activity statistics

    Access restricted to farmers only via @role_required('farmer').
    """

    template_name = 'app/dashboard/farmer.html'

    def get_context_data(self, **kwargs):
        """Load farmer-specific data into template context."""
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Recent batches created by this farmer
        context['batches'] = Batch.objects.filter(farmer=user).order_by('-created_at')[:5]
        # All farms owned by this farmer
        context['farms'] = Farm.objects.filter(farmer=user)
        # Active listings for this farmer's batches
        context['listings'] = Listing.objects.filter(farmer=user).select_related('batch')[:5]
        # Recent orders where farmer is the seller
        context['orders'] = Order.objects.filter(seller=user).order_by('-created_at')[:5]
        # Bids received on farmer's listings
        context['bids'] = Bid.objects.filter(listing__farmer=user).select_related('trader', 'listing__batch')[:5]
        # Unread notifications
        context['notifications'] = Notification.objects.filter(user=user, is_read=False)[:10]
        # Activity statistics
        context['stats'] = {
            'total_batches': Batch.objects.filter(farmer=user).count(),
            'active_listings': Listing.objects.filter(farmer=user, is_active=True).count(),
            'total_orders': Order.objects.filter(seller=user).count(),
            'pending_bids': Bid.objects.filter(listing__farmer=user, status='active').count(),
        }
        return context


@method_decorator(role_required('trader'), name='dispatch')
class TraderDashboardView(LoginRequiredMixin, TemplateView):
    """
    Trader-specific dashboard showing their trading activity.

    Displays:
    - Available listings (for browsing)
    - Their active bids
    - Recent orders (as buyer)
    - Unread notifications
    - Trading statistics

    Access restricted to traders only via @role_required('trader').
    """

    template_name = 'app/dashboard/trader.html'

    def get_context_data(self, **kwargs):
        """Load trader-specific data into template context."""
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Active listings available for purchase
        context['listings'] = Listing.objects.filter(is_active=True).select_related('batch', 'farmer')[:6]
        # Bids placed by this trader
        context['my_bids'] = Bid.objects.filter(trader=user).select_related('listing__batch')[:5]
        # Recent orders where trader is the buyer
        context['orders'] = Order.objects.filter(buyer=user).order_by('-created_at')[:5]
        # Unread notifications
        context['notifications'] = Notification.objects.filter(user=user, is_read=False)[:10]
        # Trading statistics
        context['stats'] = {
            'active_bids': Bid.objects.filter(trader=user, status='active').count(),
            'won_orders': Order.objects.filter(buyer=user).count(),
            'total_spent': Order.objects.filter(buyer=user).aggregate(total=Sum('total_amount'))['total'] or 0,
        }
        return context


@method_decorator(role_required('product_manager'), name='dispatch')
class PMDashboardView(LoginRequiredMixin, TemplateView):
    """
    Product Manager dashboard showing quality verification activity.

    Displays:
    - Batches pending review
    - Batches under review
    - Recent verifications performed by this PM
    - Unread notifications
    - Verification statistics

    Access restricted to product managers only.
    """

    template_name = 'app/dashboard/pm.html'

    def get_context_data(self, **kwargs):
        """Load PM-specific data into template context."""
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Batches awaiting PM review
        context['pending_batches'] = Batch.objects.filter(status='pending').select_related('farmer')[:10]
        # Batches currently being reviewed
        context['under_review'] = Batch.objects.filter(status='under_review').select_related('farmer')[:10]
        # Verifications performed by this PM
        context['recent_verifications'] = QualityVerification.objects.filter(product_manager=user).select_related('batch')[:10]
        # Unread notifications
        context['notifications'] = Notification.objects.filter(user=user, is_read=False)[:10]
        # Verification statistics
        context['stats'] = {
            'pending_review': Batch.objects.filter(status='pending').count(),
            'under_review': Batch.objects.filter(status='under_review').count(),
            'verified_today': QualityVerification.objects.filter(product_manager=user).count(),
            'total_verified': QualityVerification.objects.count(),
        }
        return context


@method_decorator(role_required('admin'), name='dispatch')
class AdminDashboardView(LoginRequiredMixin, TemplateView):
    """
    Admin dashboard showing platform-wide statistics and activity.

    Displays:
    - Recent users
    - Open disputes
    - Recent orders
    - Platform statistics (users, batches, orders, revenue)

    Access restricted to admins only.
    """

    template_name = 'app/dashboard/admin.html'

    def get_context_data(self, **kwargs):
        """Load admin-specific data into template context."""
        context = super().get_context_data(**kwargs)

        # Recent users by registration date
        context['users'] = User.objects.all().order_by('-date_joined')[:10]
        # Open disputes awaiting resolution
        context['pending_disputes'] = Dispute.objects.filter(status='open')[:5]
        # Recent orders across platform
        context['recent_orders'] = Order.objects.all().order_by('-created_at')[:10]
        # Platform-wide statistics
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
    """
    View for farmers to create new cardamom batches.

    Features:
    - Form with fields: farm, quantity, harvest date, description, price
    - Auto-assigns batch to current farmer
    - Filters farm dropdown to only show farmer's own farms
    - Farm is optional (can create batch without linking to farm)
    - Generates unique batch code (CDM-YYYY-NNNN) on save

    Access restricted to farmers only.
    """

    model = Batch
    template_name = 'app/batches/create.html'
    fields = ['farm', 'quantity_kg', 'harvest_date', 'description', 'estimated_price_per_kg']

    def form_valid(self, form):
        """Assign batch to current farmer before saving."""
        form.instance.farmer = self.request.user
        messages.success(self.request, "Batch created successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to batch list after creation."""
        return reverse_lazy('app:batch_list')

    def get_form(self, form_class=None):
        """Filter farm dropdown to only show farmer's own farms."""
        form = super().get_form(form_class)
        form.fields['farm'].queryset = Farm.objects.filter(farmer=self.request.user)
        form.fields['farm'].required = False  # Farm is optional
        return form


class BatchListView(LoginRequiredMixin, ListView):
    """
    List view for displaying cardamom batches.

    Features:
    - Farmers see only their own batches
    - Other roles see all batches
    - Paginated (12 per page)
    - Optimized with select_related for farmer and farm data

    Accessible to all authenticated users.
    """

    model = Batch
    template_name = 'app/batches/list.html'
    context_object_name = 'batches'
    paginate_by = 12  # 12 batches per page

    def get_queryset(self):
        """Filter batches based on user role."""
        user = self.request.user
        if user.role == 'farmer':
            # Farmers only see their own batches
            return Batch.objects.filter(farmer=user).select_related('farm')
        # Other roles see all batches
        return Batch.objects.all().select_related('farmer', 'farm')


@method_decorator(role_required('farmer', 'product_manager', 'admin', 'trader'), name='dispatch')
class BatchDetailView(LoginRequiredMixin, DetailView):
    """
    Detail view for displaying a single batch with all its information.

    Shows:
    - Batch details (code, quantity, status, etc.)
    - Farm information
    - Quality verification (if verified)
    - Listing information (if listed)
    - Related orders

    Access restricted to farmers, PMs, admins, and traders.
    """

    model = Batch
    template_name = 'app/batches/detail.html'
    context_object_name = 'batch'


@method_decorator(role_required('product_manager'), name='dispatch')
class BatchVerifyView(LoginRequiredMixin, DetailView):
    """
    View for Product Managers to verify batch quality.

    Features:
    - Displays batch details with verification form
    - Form includes: grade, moisture, aroma, color, purity, price, remarks
    - Creates QualityVerification record on successful submission
    - Updates batch status to 'under_review'
    - Prevents duplicate verification
    - After verification, batch can be listed via signal

    Access restricted to product managers only.
    """

    model = Batch
    template_name = 'app/batches/verify.html'
    context_object_name = 'batch'

    def get_context_data(self, **kwargs):
        """Add verification form to context if batch not yet verified."""
        context = super().get_context_data(**kwargs)
        if not hasattr(self.object, 'verification'):
            context['form'] = self._get_verification_form()
        return context

    def _get_verification_form(self, data=None):
        """Create the verification form class dynamically."""
        from django import forms as dj_forms
        class VForm(dj_forms.ModelForm):
            class Meta:
                model = QualityVerification
                fields = ['grade', 'moisture_content_pct', 'aroma_score', 'color_score', 'purity_pct', 'verified_price_per_kg', 'remarks']
                widgets = {'remarks': dj_forms.Textarea(attrs={'rows': 3})}
        return VForm(data)

    def post(self, request, *args, **kwargs):
        """Handle verification form submission."""
        batch = self.get_object()

        # Prevent duplicate verification
        if hasattr(batch, 'verification'):
            messages.warning(request, "This batch has already been verified.")
            return redirect('app:batch_detail', pk=batch.pk)

        form = self._get_verification_form(request.POST)
        if form.is_valid():
            # Create verification record
            verification = form.save(commit=False)
            verification.batch = batch
            verification.product_manager = request.user
            verification.save()
            # Update batch status
            batch.status = Batch.Status.UNDER_REVIEW
            batch.save(update_fields=['status'])
            messages.success(request, f"Batch {batch.batch_code} has been verified!")
            return redirect('app:batch_detail', pk=batch.pk)

        messages.error(request, "Please correct the errors below.")
        return self.render_to_response(self.get_context_data(form=form))


class ListingListView(LoginRequiredMixin, ListView):
    """
    List view for marketplace listings.

    Shows all active listings available for purchase.
    Traders can browse and either buy directly or place bids.

    Features:
    - Only shows active listings
    - Optimized with select_related for batch and farmer
    - Paginated (12 per page)

    Accessible to all authenticated users.
    """

    model = Listing
    template_name = 'app/trading/listing_list.html'
    context_object_name = 'listings'
    paginate_by = 12  # 12 listings per page

    def get_queryset(self):
        """Return only active listings with related data."""
        return Listing.objects.filter(is_active=True).select_related('batch', 'farmer')


@method_decorator(role_required('farmer', 'trader', 'product_manager', 'admin'), name='dispatch')
class ListingDetailView(LoginRequiredMixin, DetailView):
    """
    Detail view for a marketplace listing.

    Shows:
    - Listing details (type, price, quantity available)
    - Batch information
    - Farmer information
    - For auctions: list of bids
    - Action buttons (Buy Now or Place Bid)

    Access restricted to farmers, traders, PMs, and admins.
    """

    model = Listing
    template_name = 'app/trading/listing_detail.html'
    context_object_name = 'listing'


@method_decorator(role_required('trader'), name='dispatch')
class PlaceBidView(LoginRequiredMixin, CreateView):
    """
    View for traders to place bids on auction listings.

    Features:
    - Form with fields: bid price, quantity, notes
    - Validates listing is active and is an auction type
    - Auto-assigns listing and trader
    - Trader can only bid on auction listings (not fixed price)
    - After placing bid, farmer is notified

    Access restricted to traders only.
    """

    model = Bid
    template_name = 'app/trading/place_bid.html'
    fields = ['bid_price_per_kg', 'quantity_kg', 'notes']

    def dispatch(self, request, *args, **kwargs):
        """Validate listing exists, is active, and is auction type."""
        self.listing = get_object_or_404(Listing, pk=kwargs['pk'])
        if not self.listing.is_active:
            messages.error(request, "This listing is no longer active.")
            return redirect('app:listing_list')
        if self.listing.listing_type != 'auction':
            messages.error(request, "This listing is not an auction. Use 'Buy Now' instead.")
            return redirect('app:listing_detail', pk=self.listing.pk)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """Assign listing and trader before saving bid."""
        form.instance.listing = self.listing
        form.instance.trader = self.request.user
        messages.success(self.request, "Bid placed successfully!")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        """Add listing to template context."""
        context = super().get_context_data(**kwargs)
        context['listing'] = self.listing
        return context

    def get_success_url(self):
        """Redirect back to listing detail after placing bid."""
        return reverse_lazy('app:listing_detail', kwargs={'pk': self.listing.pk})


@method_decorator(role_required('trader'), name='dispatch')
class DirectBuyView(LoginRequiredMixin, TemplateView):
    """
    View for traders to directly purchase fixed-price listings.

    Features:
    - Shows listing details and purchase form
    - Validates quantity doesn't exceed available stock
    - Creates order automatically
    - Updates listing available quantity
    - Marks listing inactive if sold out
    - Updates batch status to 'SOLD' if completely sold

    Access restricted to traders only.
    """

    template_name = 'app/trading/direct_buy.html'

    def dispatch(self, request, *args, **kwargs):
        """Validate listing exists, is active, and is fixed-price type."""
        self.listing = get_object_or_404(Listing, pk=kwargs['pk'])
        if not self.listing.is_active:
            messages.error(request, "This listing is no longer active.")
            return redirect('app:listing_list')
        if self.listing.listing_type != 'fixed_price':
            messages.error(request, "This listing is an auction. Use 'Place Bid' instead.")
            return redirect('app:listing_detail', pk=self.listing.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Add listing to template context."""
        context = super().get_context_data(**kwargs)
        context['listing'] = self.listing
        return context

    def post(self, request, *args, **kwargs):
        """Handle purchase form submission."""
        listing = self.listing
        quantity = request.POST.get('quantity_kg', listing.available_qty_kg)

        # Validate quantity
        from decimal import Decimal
        try:
            quantity = Decimal(quantity)
        except (TypeError, ValueError):
            messages.error(request, "Invalid quantity.")
            return self.render_to_response(self.get_context_data())

        if quantity > listing.available_qty_kg:
            messages.error(request, f"Only {listing.available_qty_kg}kg available.")
            return self.render_to_response(self.get_context_data())

        # Create order
        order = Order.objects.create(
            listing=listing,
            batch=listing.batch,
            buyer=request.user,
            seller=listing.farmer,
            quantity_kg=quantity,
            price_per_kg=listing.price_per_kg,
        )

        # Update listing availability
        listing.available_qty_kg -= quantity
        if listing.available_qty_kg <= 0:
            listing.is_active = False  # Mark as sold out
        listing.save(update_fields=['available_qty_kg', 'is_active'])

        # Update batch status if completely sold
        if listing.available_qty_kg <= 0:
            listing.batch.status = Batch.Status.SOLD
            listing.batch.save(update_fields=['status'])

        messages.success(request, f"Order {order.order_code} placed successfully!")
        return redirect('app:order_detail', pk=order.pk)


@method_decorator(role_required('trader', 'farmer'), name='dispatch')
class MyBidsView(LoginRequiredMixin, ListView):
    """
    List view for displaying bids.

    Features:
    - Traders see bids they've placed
    - Farmers see bids received on their listings
    - Shows bid status, price, quantity, and related listing

    Access restricted to traders and farmers.
    """

    model = Bid
    template_name = 'app/trading/my_bids.html'
    context_object_name = 'bids'

    def get_queryset(self):
        """Filter bids based on user role."""
        user = self.request.user
        if user.role == 'farmer':
            # Farmers see bids on their listings
            return Bid.objects.filter(listing__farmer=user).select_related('trader', 'listing__batch')
        # Traders see their own bids
        return Bid.objects.filter(trader=user).select_related('listing__batch')


@method_decorator(role_required('farmer', 'trader', 'product_manager', 'admin'), name='dispatch')
class OrderListView(LoginRequiredMixin, ListView):
    """
    List view for displaying orders.

    Features:
    - Farmers see orders where they are the seller
    - Traders see orders where they are the buyer
    - PMs and admins see all orders
    - Paginated (10 per page)

    Access restricted to farmers, traders, PMs, and admins.
    """

    model = Order
    template_name = 'app/orders/list.html'
    context_object_name = 'orders'
    paginate_by = 10  # 10 orders per page

    def get_queryset(self):
        """Filter orders based on user role."""
        user = self.request.user
        if user.role == 'farmer':
            # Farmers see orders they're selling
            return Order.objects.filter(seller=user).select_related('buyer', 'batch')
        elif user.role == 'trader':
            # Traders see orders they're buying
            return Order.objects.filter(buyer=user).select_related('seller', 'batch')
        # PMs and admins see all orders
        return Order.objects.all().select_related('buyer', 'seller', 'batch')


@method_decorator(role_required('farmer', 'trader', 'product_manager', 'admin'), name='dispatch')
class OrderDetailView(LoginRequiredMixin, DetailView):
    """
    Detail view for a single order.

    Shows:
    - Order details (code, status, quantities, prices)
    - Buyer and seller information
    - Batch information
    - Payment status
    - Tracking history
    - Action buttons (confirm, ship, deliver, dispute)

    Access restricted to farmers, traders, PMs, and admins.
    """

    model = Order
    template_name = 'app/orders/detail.html'
    context_object_name = 'order'


@method_decorator(role_required('farmer'), name='dispatch')
class FarmListView(LoginRequiredMixin, ListView):
    """
    List view for displaying farmer's farms.

    Shows only the farms owned by the current farmer.
    Each farm displays name, location, area, and certification.

    Access restricted to farmers only.
    """

    model = Farm
    template_name = 'app/farms/list.html'
    context_object_name = 'farms'

    def get_queryset(self):
        """Return only farms owned by current farmer."""
        return Farm.objects.filter(farmer=self.request.user)


@method_decorator(role_required('farmer'), name='dispatch')
class FarmCreateView(LoginRequiredMixin, CreateView):
    """
    View for farmers to register new farms.

    Features:
    - Form with fields: name, location, region, area, certification
    - Auto-assigns farm to current farmer
    - All fields optional except farm_name

    Access restricted to farmers only.
    """

    model = Farm
    template_name = 'app/farms/create.html'
    fields = ['farm_name', 'location', 'region', 'total_area_acres', 'certification']

    def form_valid(self, form):
        """Assign farm to current farmer before saving."""
        form.instance.farmer = self.request.user
        messages.success(self.request, "Farm registered successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to farm list after creation."""
        return reverse_lazy('app:farm_list')


# ============================================================
# CONVERSATIONS & MESSAGING
# ============================================================

@method_decorator(role_required('farmer', 'trader', 'product_manager', 'admin'), name='dispatch')
class ConversationListView(LoginRequiredMixin, ListView):
    """
    List view for displaying user's conversations.

    Shows all conversations where the user is an active participant.
    Ordered by most recent message.

    Features:
    - Only shows conversations user participates in
    - Prefetches participants and users for efficiency
    - Shows unread message count

    Accessible to all authenticated users.
    """

    model = Conversation
    template_name = 'app/messaging/conversation_list.html'
    context_object_name = 'conversations'

    def get_queryset(self):
        """Return conversations where user is an active participant."""
        return Conversation.objects.filter(
            participants__user=self.request.user,
            participants__is_active=True
        ).prefetch_related('participants__user').order_by('-last_message_at')


@method_decorator(role_required('farmer', 'trader', 'product_manager', 'admin'), name='dispatch')
class ConversationDetailView(LoginRequiredMixin, DetailView):
    """
    Detail view for a single conversation with messages.

    Features:
    - Shows all messages in the conversation
    - Allows sending new messages (POST)
    - Updates last_read_at for unread tracking
    - Shows participants

    Access restricted to conversation participants only.
    """

    model = Conversation
    template_name = 'app/messaging/conversation_detail.html'
    context_object_name = 'conversation'

    def get_queryset(self):
        """Return conversations where user is an active participant."""
        return Conversation.objects.filter(
            participants__user=self.request.user,
            participants__is_active=True
        ).prefetch_related('messages__sender', 'participants__user')

    def get_context_data(self, **kwargs):
        """Update last_read_at when viewing conversation."""
        context = super().get_context_data(**kwargs)
        # Mark conversation as read
        participant = self.object.participants.filter(user=self.request.user).first()
        if participant:
            participant.last_read_at = timezone.now()
            participant.save(update_fields=['last_read_at'])
        return context

    def post(self, request, *args, **kwargs):
        """Handle sending a new message."""
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
    """
    View to create a new conversation about a batch.

    Features:
    - Creates conversation linked to a batch
    - Automatically adds current user as participant
    - Adds the other party (farmer or PM) as participant
    - Sets conversation type to BATCH_INQUIRY

    Access restricted to farmers and traders.
    """

    model = Conversation
    template_name = 'app/messaging/conversation_create.html'
    fields = ['subject']

    def dispatch(self, request, *args, **kwargs):
        """Get the batch for this conversation."""
        self.batch = get_object_or_404(Batch, pk=kwargs.get('batch_pk', 0))
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """Create conversation and add participants."""
        form.instance.batch = self.batch
        form.instance.type = Conversation.Type.BATCH_INQUIRY
        form.save()

        # Add current user as participant
        ConversationParticipant.objects.create(
            conversation=form.instance,
            user=self.request.user,
            role_in_chat=self.request.user.role
        )

        # Add other party (farmer if trader initiated, PM if farmer initiated)
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
        """Redirect to conversation list after creation."""
        return reverse_lazy('app:conversation_list')

    def get_context_data(self, **kwargs):
        """Add batch to template context."""
        context = super().get_context_data(**kwargs)
        context['batch'] = self.batch
        return context


# ============================================================
# DISPUTES
# ============================================================

@method_decorator(role_required('farmer', 'trader'), name='dispatch')
class DisputeCreateView(LoginRequiredMixin, CreateView):
    """
    View for farmers and traders to raise disputes about orders.

    Features:
    - Form with field: reason for dispute
    - Validates user is a party to the order (buyer or seller)
    - Sets against_user to the other party
    - Updates order status to 'disputed'
    - Admin will be notified to review

    Access restricted to farmers and traders (order participants).
    """

    model = Dispute
    template_name = 'app/disputes/create.html'
    fields = ['reason']

    def dispatch(self, request, *args, **kwargs):
        """Validate user is a party to this order."""
        self.order = get_object_or_404(Order, pk=kwargs['order_pk'])
        if request.user != self.order.buyer and request.user != self.order.seller:
            return HttpResponseForbidden()  # Not a party to this order
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """Create dispute and update order status."""
        form.instance.order = self.order
        form.instance.raised_by = self.request.user
        # Set against_user to the other party
        form.instance.against_user = self.order.seller if self.request.user == self.order.buyer else self.order.buyer
        form.save()
        # Update order status
        self.order.status = Order.Status.DISPUTED
        self.order.save(update_fields=['status'])
        messages.success(request, "Dispute raised. An admin will review it shortly.")
        return redirect('app:dispute_list')

    def get_success_url(self):
        """Redirect to dispute list after creation."""
        return reverse_lazy('app:dispute_list')

    def get_context_data(self, **kwargs):
        """Add order to template context."""
        context = super().get_context_data(**kwargs)
        context['order'] = self.order
        return context


@method_decorator(role_required('farmer', 'trader', 'product_manager', 'admin'), name='dispatch')
class DisputeListView(LoginRequiredMixin, ListView):
    """
    List view for displaying disputes.

    Features:
    - Admins see all disputes
    - Farmers/traders see only disputes they're involved in
    - Paginated (10 per page)

    Access restricted to all authenticated users.
    """

    model = Dispute
    template_name = 'app/disputes/list.html'
    context_object_name = 'disputes'
    paginate_by = 10  # 10 disputes per page

    def get_queryset(self):
        """Filter disputes based on user role."""
        user = self.request.user
        if user.role == 'admin':
            # Admins see all disputes
            return Dispute.objects.all().select_related('order', 'raised_by', 'against_user')
        # Other users see only disputes they're involved in
        return Dispute.objects.filter(
            Q(raised_by=user) | Q(against_user=user)
        ).select_related('order', 'raised_by')


@method_decorator(role_required('admin'), name='dispatch')
class DisputeResolveView(LoginRequiredMixin, UpdateView):
    """
    View for admins to resolve disputes.

    Features:
    - Form with fields: resolution, status
    - Sets resolved_by to current admin
    - Sets resolved_at timestamp when status is resolved/closed

    Access restricted to admins only.
    """

    model = Dispute
    template_name = 'app/disputes/resolve.html'
    fields = ['resolution', 'status']
    context_object_name = 'dispute'

    def form_valid(self, form):
        """Set resolver and timestamp."""
        form.instance.resolved_by = self.request.user
        if form.instance.status in ['resolved', 'closed']:
            form.instance.resolved_at = timezone.now()
        messages.success(self.request, "Dispute resolved successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to dispute list after resolution."""
        return reverse_lazy('app:dispute_list')


# ============================================================
# NOTIFICATIONS
# ============================================================

class NotificationListView(LoginRequiredMixin, ListView):
    """
    List view for displaying user's notifications.

    Shows all notifications for the current user, ordered by newest first.
    Includes both read and unread notifications.

    Features:
    - Shows all user notifications
    - Paginated (20 per page)
    - Unread count shown in navbar

    Accessible to all authenticated users.
    """

    model = Notification
    template_name = 'app/notifications/list.html'
    context_object_name = 'notifications'
    paginate_by = 20  # 20 notifications per page

    def get_queryset(self):
        """Return notifications for current user, newest first."""
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')


class NotificationMarkReadView(LoginRequiredMixin, TemplateView):
    """
    View to mark all notifications as read.

    Called when user clicks "Mark all as read" button.
    Updates all unread notifications to read status.

    Uses POST method for state-changing operation.
    """

    def post(self, request, *args, **kwargs):
        """Mark all unread notifications as read."""
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        messages.success(request, "All notifications marked as read.")
        return redirect('app:notification_list')
