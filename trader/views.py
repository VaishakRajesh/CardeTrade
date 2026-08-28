"""
trader/views.py

Views for trader-facing functionality: dashboard, marketplace listings,
placing bids, managing orders, and making payments.
"""

from django.shortcuts import redirect, get_object_or_404
from django.http import HttpResponseForbidden
from django.views.generic import TemplateView, CreateView, ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.db.models import Sum, Max, Count, Q
from accounts.decorators import role_required
from .models import Listing, Bid, Order, Payment, OrderTracking


@method_decorator(role_required('trader'), name='dispatch')
# Trader's main dashboard showing listings, bids, orders, and spending stats
class TraderDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'trader/dashboard.html'

    # Gather active listings, user's bids, orders, and summary statistics
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        from farmer.models import Batch
        context['listings'] = Listing.objects.filter(is_active=True).select_related('batch', 'farmer')[:6]
        context['my_bids'] = Bid.objects.filter(trader=user).select_related('listing__batch')[:5]
        context['orders'] = Order.objects.filter(buyer=user).order_by('-created_at')[:5]

        context['stats'] = {
            'active_bids': Bid.objects.filter(trader=user, status='active').count(),
            'won_orders': Order.objects.filter(buyer=user).count(),
            'total_spent': Order.objects.filter(buyer=user).aggregate(total=Sum('total_amount'))['total'] or 0,
        }
        return context


# Public marketplace listing page showing all active auction listings
class ListingListView(ListView):
    model = Listing
    template_name = 'trader/trading/listing_list.html'
    context_object_name = 'listings'
    paginate_by = 12

    # Annotate each listing with highest bid and bid count for display
    def get_queryset(self):
        return Listing.objects.filter(is_active=True)\
            .select_related('batch__verification', 'batch__farm', 'farmer')\
            .annotate(
                highest_bid=Max('bids__bid_price_per_kg',
                    filter=Q(bids__status='active')),
                active_bid_count=Count('bids',
                    filter=Q(bids__status='active')),
            )


@method_decorator(role_required('farmer', 'trader', 'product_manager', 'admin'), name='dispatch')
# Shows detailed view of a single listing with bid history
class ListingDetailView(LoginRequiredMixin, DetailView):
    model = Listing
    template_name = 'trader/trading/listing_detail.html'
    context_object_name = 'listing'


# Handles placing a new bid on an auction listing
@method_decorator(role_required('trader'), name='dispatch')
class PlaceBidView(LoginRequiredMixin, CreateView):
    model = Bid
    template_name = 'trader/trading/place_bid.html'
    fields = ['bid_price_per_kg', 'quantity_kg', 'notes']

    # Verify the listing is active before allowing a bid
    def dispatch(self, request, *args, **kwargs):
        self.listing = get_object_or_404(Listing, pk=kwargs['pk'])
        if not self.listing.is_active:
            messages.error(request, "This listing is no longer active.")
            return redirect('trader:listing_list')
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
        return reverse('trader:listing_detail', kwargs={'pk': self.listing.pk})


@method_decorator(role_required('trader'), name='dispatch')
# Lists all bids placed by the current trader
class MyBidsView(LoginRequiredMixin, ListView):
    model = Bid
    template_name = 'trader/trading/my_bids.html'
    context_object_name = 'bids'

    # Show only bids made by the logged-in trader
    def get_queryset(self):
        return Bid.objects.filter(trader=self.request.user).select_related('listing__batch')


@method_decorator(role_required('farmer', 'trader', 'product_manager', 'admin'), name='dispatch')
# Lists orders — filtered by role (buyer for traders, seller for farmers)
class OrderListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'trader/orders/list.html'
    context_object_name = 'orders'
    paginate_by = 10

    # Filter orders based on user role: buyer, seller, or all (admin/PM)
    def get_queryset(self):
        user = self.request.user
        if user.role == 'farmer':
            return Order.objects.filter(seller=user).select_related('buyer', 'batch')
        elif user.role == 'trader':
            return Order.objects.filter(buyer=user).select_related('seller', 'batch')
        return Order.objects.all().select_related('buyer', 'seller', 'batch')


@method_decorator(role_required('trader'), name='dispatch')
# Handles payment processing for an order (buyer only)
class MakePaymentView(LoginRequiredMixin, TemplateView):
    template_name = 'trader/orders/pay.html'

    # Ensure the order belongs to the current user and is not already paid
    def dispatch(self, request, *args, **kwargs):
        self.order = get_object_or_404(Order, pk=kwargs['pk'], buyer=request.user)
        if self.order.payment_status == 'paid':
            messages.info(request, "This order is already paid.")
            return redirect('trader:order_detail', pk=self.order.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['order'] = self.order
        return context

    # Process the payment: create Payment record and update order status
    def post(self, request, *args, **kwargs):
        order = self.order
        method = request.POST.get('payment_method', '')
        ref = request.POST.get('transaction_ref', '')

        if method not in dict(Payment.PaymentMethod.choices):
            messages.error(request, "Invalid payment method.")
            return self.render_to_response(self.get_context_data())

        Payment.objects.create(
            order=order,
            payer=request.user,
            amount=order.total_amount,
            payment_method=method,
            transaction_ref=ref or f"MOCK-{timezone.now().timestamp():.0f}",
            status=Payment.Status.COMPLETED,
            paid_at=timezone.now(),
        )

        order.payment_status = Order.PaymentStatus.PAID
        order.status = Order.Status.CONFIRMED
        order.save(update_fields=['payment_status', 'status'])

        messages.success(request, f"Payment of Rs{order.total_amount} completed successfully!")
        return redirect('trader:order_detail', pk=order.pk)


@method_decorator(role_required('farmer', 'trader', 'product_manager', 'admin'), name='dispatch')
# Shows detailed view of a single order with payment and tracking info
class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = 'trader/orders/detail.html'
    context_object_name = 'order'


@method_decorator(role_required('farmer', 'admin'), name='dispatch')
# Allows the seller (farmer) or an admin to log an order tracking update
class OrderTrackingCreateView(LoginRequiredMixin, CreateView):
    model = OrderTracking
    template_name = 'trader/orders/track.html'
    fields = ['status', 'location', 'notes']

    # Restrict to the seller of the order (or an admin)
    def dispatch(self, request, *args, **kwargs):
        self.order = get_object_or_404(Order, pk=kwargs['pk'])
        if not (request.user == self.order.seller or request.user.role == 'admin'):
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.order = self.order
        form.instance.updated_by = self.request.user
        response = super().form_valid(form)
        # Propagate the tracking status onto the parent order so its
        # fulfillment status reflects the latest update.
        self.order.status = form.instance.status
        self.order.save(update_fields=['status'])
        messages.success(self.request, "Tracking update added.")
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['order'] = self.order
        return context

    def get_success_url(self):
        return reverse('trader:order_detail', kwargs={'pk': self.order.pk})
