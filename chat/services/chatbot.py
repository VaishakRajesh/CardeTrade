"""
chat/services/chatbot.py

Business logic for the CardeTrade AI chatbot. Fetches relevant
database context (listings, batches, farms, orders) based on the
user's query, builds a system prompt, calls the OpenRouter API,
and formats the AI response for display.
"""

import json
import os
from decimal import Decimal

import requests
from django.conf import settings
from django.db.models import Avg, Min, Max, Count, Q

from trader.models import Listing, Order
from farmer.models import Batch, Farm
from pm.models import QualityVerification
from accounts.models import User


# Custom JSON encoder that converts Decimal values to floats for serialization
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


# Base system instruction that defines the AI assistant's persona, platform rules, and cardamom knowledge
SYSTEM_PROMPT = """You are CardeTrade AI Assistant — a helpful expert on the CardeTrade cardamom trading platform.

## Platform Overview
CardeTrade is a premium digital marketplace connecting cardamom farmers, traders, and product managers in India. It enables farmers to list batches of cardamom, product managers to verify quality, and traders to purchase via fixed-price or auction.

## User Roles
- **Farmer**: Creates batches, registers farms, views bids, accepts bids
- **Trader**: Browses listings, places bids (auction), buys directly (fixed price), makes payments
- **Product Manager**: Reviews and verifies batch quality, sets verified prices
- **Admin**: Full system oversight, can disable users, revoke batches, resolve disputes

## Batch Workflow
1. Farmer creates batch → status=PENDING
2. Product Manager reviews → status=UNDER_REVIEW
3. PM verifies quality (Grade A/B/C with moisture, aroma, color, purity scores) → status=VERIFIED → Listing auto-created → status=LISTED
4. Batch can be sold via fixed-price or auction
5. Once sold → status=SOLD

## Listing Types
- **Fixed Price**: Trader buys immediately at listed price
- **Auction**: Traders place bids, farmer accepts the best one

## Quality Grades
- **Grade A**: Premium quality (green color, strong aroma, low moisture)
- **Grade B**: Good quality (standard grade)
- **Grade C**: Lower quality (higher moisture, lighter color)

## Cardamom Knowledge
- Cardamom (Elettaria cardamomum) is "Queen of Spices"
- Major Indian growing regions: Idukki (Kerala), Wayanad (Kerala), Coorg (Karnataka), Nilgiris (Tamil Nadu), Sikkim
- Key quality factors: color (green/unbleached), aroma intensity, oil content, moisture (ideal <12%), size
- Harvest season: August-February (main), June-July (early crop)
- Grades are determined by: size, color, aroma, moisture content, purity

## Important Rules
- Farmers cannot bid on listings
- Traders cannot create batches
- Product Managers cannot trade
- Only the farmer who owns a batch can accept bids on it

## Response Style
- Be concise, friendly, and helpful
- Use simple language, avoid jargon unless explaining it
- When providing data analysis, present it in a readable format
- If asked about something outside CardeTrade/cardamom, politely redirect to relevant topics
- When fetching database data, clearly label what data you're showing

## Current Date
{current_date}"""


# Fetches relevant database records (listings, batches, farms, orders) based on keywords in the user query
def get_db_context(user, query):
    query_lower = query.lower()
    context_parts = []

    listing_keywords = ['listing', 'listings', 'marketplace', 'available', 'price', 'prices', 'for sale',
                        'cheapest', 'expensive', 'best', 'grade', 'buy', 'purchase', 'inventory',
                        'stock', 'product', 'products', 'cardamom', 'qty', 'quantity']
    batch_keywords = ['batch', 'batches', 'pending', 'status', 'my batch']
    farm_keywords = ['farm', 'farms', 'location', 'region', 'certification', 'farming']
    order_keywords = ['order', 'orders', 'purchase', 'sold', 'sales', 'transaction']
    analysis_keywords = ['analy', 'compare', 'summary', 'overview', 'trend', 'statistics',
                         'report', 'distribution', 'average', 'best', 'top', 'recommend',
                         'cheapest', 'expensive', 'suggestion', 'help me choose']
    role_keywords = ['my role', 'what can i', 'permission', 'allowed', 'role']

    needs_listing = any(k in query_lower for k in listing_keywords)
    needs_batch = any(k in query_lower for k in batch_keywords)
    needs_farm = any(k in query_lower for k in farm_keywords)
    needs_order = any(k in query_lower for k in order_keywords)
    needs_analysis = any(k in query_lower for k in analysis_keywords)
    needs_role = any(k in query_lower for k in role_keywords)

    if needs_role and user.is_authenticated:
        role_descriptions = {
            'farmer': 'You can create batches, register farms, view bids on your listings, and accept bids.',
            'trader': 'You can browse marketplace listings, place bids on auctions, buy fixed-price listings directly, and view your orders.',
            'product_manager': 'You can review pending batches, verify quality, set verified prices, and generate reports.',
            'admin': 'You have full system access including disabling users, revoking batches, resolving disputes.',
        }
        desc = role_descriptions.get(user.role, '')
        context_parts.append(f"[USER CONTEXT] Logged in as: {user.username} (role: {user.role}). {desc}")

    if needs_listing or needs_analysis:
        listings = Listing.objects.filter(is_active=True).select_related('batch__verification', 'farmer', 'batch__farm')
        total = listings.count()
        if total > 0:
            grade_counts = {}
            regions = {}
            prices = []
            for l in listings:
                grade = None
                region = None
                try:
                    v = l.batch.verification
                    grade = v.grade
                except QualityVerification.DoesNotExist:
                    pass
                if l.batch.farm:
                    region = l.batch.farm.region
                g = grade or 'N/A'
                grade_counts[g] = grade_counts.get(g, 0) + 1
                r = region or 'Unknown'
                regions[r] = regions.get(r, 0) + 1
                prices.append(float(l.price_per_kg))

            top_listings = listings.order_by('-batch__verification__grade', 'price_per_kg')[:10]
            top_data = []
            for l in top_listings:
                grade = 'N/A'
                try:
                    grade = l.batch.verification.grade
                except QualityVerification.DoesNotExist:
                    pass
                top_data.append({
                    'id': l.id,
                    'grade': grade,
                    'price': float(l.price_per_kg),
                    'available_kg': float(l.available_qty_kg),
                    'type': l.listing_type,
                    'farmer': l.farmer.username,
                    'batch_code': l.batch.batch_code,
                    'region': l.batch.farm.region if l.batch.farm else 'N/A',
                })

            stats = {
                'total_active_listings': total,
                'price_range': {'min': min(prices), 'max': max(prices), 'avg': round(sum(prices) / len(prices), 2)} if prices else None,
                'grade_distribution': grade_counts,
                'region_distribution': regions,
                'sample_listings': top_data,
            }
            context_parts.append(f"[DATABASE: LISTINGS DATA]\n{json.dumps(stats, cls=DecimalEncoder, indent=2)}")

    if needs_batch:
        qs = Batch.objects.all().select_related('farmer', 'farm', 'verification')
        if user.is_authenticated and user.role == 'farmer':
            qs = qs.filter(farmer=user)
        batch_data = []
        for b in qs[:20]:
            grade = 'N/A'
            try:
                grade = b.verification.grade
            except QualityVerification.DoesNotExist:
                pass
            batch_data.append({
                'code': b.batch_code,
                'status': b.status,
                'qty_kg': float(b.quantity_kg),
                'est_price': float(b.estimated_price_per_kg),
                'harvest': str(b.harvest_date),
                'farmer': b.farmer.username,
                'grade': grade,
                'farm': b.farm.farm_name if b.farm else 'N/A',
            })
        counts_by_status = dict(Batch.objects.values('status').annotate(c=Count('id')).values_list('status', 'c'))
        context_parts.append(f"[DATABASE: BATCHES DATA]\n{json.dumps({'batches': batch_data, 'status_counts': counts_by_status}, cls=DecimalEncoder, indent=2)}")

    if needs_farm:
        farms = Farm.objects.all().select_related('farmer')[:20]
        farm_data = [{
            'name': f.farm_name,
            'location': f.location,
            'region': f.region,
            'area_acres': float(f.total_area_acres) if f.total_area_acres else None,
            'certification': bool(f.certification),
            'farmer': f.farmer.username,
        } for f in farms]
        region_counts = dict(Farm.objects.values('region').annotate(c=Count('id')).values_list('region', 'c'))
        context_parts.append(f"[DATABASE: FARMS DATA]\n{json.dumps({'farms': farm_data, 'region_counts': region_counts}, cls=DecimalEncoder, indent=2)}")

    if needs_order and user.is_authenticated:
        qs = Order.objects.all().select_related('buyer', 'seller', 'batch')
        if user.role == 'farmer':
            qs = qs.filter(seller=user)
        elif user.role == 'trader':
            qs = qs.filter(buyer=user)
        order_data = [{
            'code': o.order_code,
            'status': o.status,
            'payment': o.payment_status,
            'qty_kg': float(o.quantity_kg),
            'price_per_kg': float(o.price_per_kg),
            'total': float(o.total_amount),
            'buyer': o.buyer.username,
            'seller': o.seller.username,
        } for o in qs[:20]]
        status_counts = dict(qs.values('status').annotate(c=Count('id')).values_list('status', 'c'))
        context_parts.append(f"[DATABASE: ORDERS DATA]\n{json.dumps({'orders': order_data, 'status_counts': status_counts}, cls=DecimalEncoder, indent=2)}")

    return '\n\n'.join(context_parts)


# Sends the conversation messages to the OpenRouter API and returns the AI model's text response
def call_openrouter(messages, model=None):
    api_key = getattr(settings, 'OPENROUTER_API_KEY', os.environ.get('OPENROUTER_API_KEY', ''))
    if not api_key:
        return "The AI assistant is not configured yet. Please set the OPENROUTER_API_KEY in your .env file."

    model = model or getattr(settings, 'OPENROUTER_MODEL', 'google/gemma-2-9b-it')

    try:
        resp = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
                'HTTP-Referer': 'https://cardetrade.app',
                'X-Title': 'CardeTrade AI Assistant',
            },
            json={
                'model': model,
                'messages': messages,
                'temperature': 0.7,
                'max_tokens': 1024,
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return data['choices'][0]['message']['content']
    except requests.exceptions.Timeout:
        return "I'm sorry, the AI service is taking too long to respond. Please try again."
    except requests.exceptions.HTTPError as e:
        if resp.status_code == 401:
            return "Invalid API key. Please check your OPENROUTER_API_KEY in the .env file."
        return f"AI service error: {resp.status_code}. Please try again later."
    except Exception as e:
        return f"Sorry, I encountered an error. Please try again."


def format_response(text):
    """Convert minimal markdown to readable plain text."""
    text = text.replace('**', '').replace('__', '')
    text = text.replace('### ', '').replace('## ', '').replace('# ', '')
    return text.strip()
