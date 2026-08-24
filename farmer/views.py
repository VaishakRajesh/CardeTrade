"""
farmer/views.py

Views for farmer-facing functionality: dashboard, farm management,
batch management, viewing bids/orders, and accepting bids.
"""

from django.shortcuts import redirect, get_object_or_404
from django.views.generic import TemplateView, CreateView, ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.db.models import Sum
from accounts.decorators import role_required
from accounts.models import User
from .models import Farm, Batch


@method_decorator(role_required('farmer'), name='dispatch')
# Farmer's main dashboard showing batches, farms, listings, orders, and bids
class FarmerDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'farmer/dashboard.html'

    # Gather recent batches, farms, listings, orders, and summary stats
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['batches'] = Batch.objects.filter(farmer=user).order_by('-created_at')[:5]
        context['farms'] = Farm.objects.filter(farmer=user)

        from trader.models import Listing, Order, Bid
        context['listings'] = Listing.objects.filter(farmer=user).select_related('batch')[:5]
        context['orders'] = Order.objects.filter(seller=user).order_by('-created_at')[:5]
        context['bids'] = Bid.objects.filter(listing__farmer=user).select_related('trader', 'listing__batch')[:5]

        context['stats'] = {
            'total_batches': Batch.objects.filter(farmer=user).count(),
            'active_listings': Listing.objects.filter(farmer=user, is_active=True).count(),
            'total_orders': Order.objects.filter(seller=user).count(),
            'pending_bids': Bid.objects.filter(listing__farmer=user, status='active').count(),
        }
        return context


@method_decorator(role_required('farmer'), name='dispatch')
# Lists all farms registered by the current farmer
class FarmListView(LoginRequiredMixin, ListView):
    model = Farm
    template_name = 'farmer/farms/list.html'
    context_object_name = 'farms'

    # Only show farms belonging to the logged-in farmer
    def get_queryset(self):
        return Farm.objects.filter(farmer=self.request.user)


@method_decorator(role_required('farmer'), name='dispatch')
# Handles registration of a new farm by a farmer
class FarmCreateView(LoginRequiredMixin, CreateView):
    model = Farm
    template_name = 'farmer/farms/create.html'
    fields = ['farm_name', 'location', 'region', 'total_area_acres', 'certification']

    # Set the farmer field to the currently logged-in user
    def form_valid(self, form):
        form.instance.farmer = self.request.user
        messages.success(self.request, "Farm registered successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('farmer:farm_list')


@method_decorator(role_required('farmer'), name='dispatch')
# Handles creation of a new cardamom batch for verification and sale
class BatchCreateView(LoginRequiredMixin, CreateView):
    model = Batch
    template_name = 'farmer/batches/create.html'
    fields = ['farm', 'quantity_kg', 'harvest_date', 'description', 'estimated_price_per_kg', 'image']

    # Assign the batch to the logged-in farmer
    def form_valid(self, form):
        form.instance.farmer = self.request.user
        messages.success(self.request, "Batch created successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('farmer:batch_list')

    # Limit farm choices to only those owned by the current farmer
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['farm'].queryset = Farm.objects.filter(farmer=self.request.user)
        form.fields['farm'].required = False
        return form


# Lists batches — farmers see only their own, others see all
class BatchListView(LoginRequiredMixin, ListView):
    model = Batch
    template_name = 'farmer/batches/list.html'
    context_object_name = 'batches'
    paginate_by = 12

    # Farmers see their own batches; other roles see all batches
    def get_queryset(self):
        user = self.request.user
        if user.role == 'farmer':
            return Batch.objects.filter(farmer=user).select_related('farm')
        return Batch.objects.all().select_related('farmer', 'farm')


# Shows detailed info for a single batch (accessible by most roles)
@method_decorator(role_required('farmer', 'product_manager', 'admin', 'trader'), name='dispatch')
class BatchDetailView(LoginRequiredMixin, DetailView):
    model = Batch
    template_name = 'farmer/batches/detail.html'
    context_object_name = 'batch'


# Lists bids received on the current farmer's listings
@method_decorator(role_required('farmer', 'trader'), name='dispatch')
class MyBidsView(LoginRequiredMixin, ListView):
    template_name = 'farmer/trading/my_bids.html'
    context_object_name = 'bids'

    def get_queryset(self):
        from trader.models import Bid
        return Bid.objects.filter(listing__farmer=self.request.user).select_related('trader', 'listing__batch')

    def get_model(self):
        from trader.models import Bid
        return Bid


# Lists orders where the current farmer is the seller
@method_decorator(role_required('farmer'), name='dispatch')
class OrderListView(LoginRequiredMixin, ListView):
    template_name = 'farmer/orders/list.html'
    context_object_name = 'orders'
    paginate_by = 10

    def get_queryset(self):
        from trader.models import Order
        return Order.objects.filter(seller=self.request.user).select_related('buyer', 'batch')

    def get_model(self):
        from trader.models import Order
        return Order


# Handles bid acceptance: marks other bids as outbid and creates an order
@method_decorator(role_required('farmer'), name='dispatch')
class AcceptBidView(LoginRequiredMixin, TemplateView):
    def post(self, request, *args, **kwargs):
        from trader.models import Bid, Order, Listing
        bid = get_object_or_404(Bid, pk=kwargs['pk'], listing__farmer=request.user)

        if bid.status != Bid.Status.ACTIVE:
            messages.warning(request, "This bid is no longer active.")
            return redirect('farmer:my_bids')

        from django.db import transaction
        listing = bid.listing

        with transaction.atomic():
            # Lock the listing row so concurrent accepts serialize safely.
            listing = Listing.objects.select_for_update().get(pk=listing.pk)
            # Re-read the bid under the lock to get its latest status; this
            # prevents a double-accept (and a duplicate Order) under concurrency.
            bid = Bid.objects.select_for_update().get(pk=bid.pk)
            if bid.status != Bid.Status.ACTIVE:
                messages.warning(request, "This bid is no longer active.")
                return redirect('farmer:my_bids')

            Bid.objects.filter(listing=listing, status='active').exclude(pk=bid.pk).update(
                status=Bid.Status.OUTBID
            )

            bid.status = Bid.Status.ACCEPTED
            bid.save(update_fields=['status'])

            order = Order.objects.create(
                listing=listing,
                batch=listing.batch,
                buyer=bid.trader,
                seller=listing.farmer,
                bid=bid,
                quantity_kg=bid.quantity_kg,
                price_per_kg=bid.bid_price_per_kg,
            )

            listing.available_qty_kg -= bid.quantity_kg
            if listing.available_qty_kg <= 0:
                listing.available_qty_kg = 0
                listing.is_active = False
                listing.batch.status = Batch.Status.SOLD
                listing.batch.save(update_fields=['status'])
            listing.save(update_fields=['available_qty_kg', 'is_active'])

        messages.success(request, f"Bid accepted! Order {order.order_code} created.")
        return redirect('trader:order_detail', pk=order.pk)
