# 📘 CardeTrade — Complete Project Tutorial

> **Step-by-step guide to build the Cardamom Trading Platform from scratch using Django.**

---

## 📑 Table of Contents

- [Prerequisites](#-prerequisites)
- [Step 1: Project Setup](#step-1-project-setup)
- [Step 2: Accounts App](#step-2-accounts-app)
- [Step 3: Farms App](#step-3-farms-app)
- [Step 4: Batches App](#step-4-batches-app)
- [Step 5: Trading App](#step-5-trading-app)
- [Step 6: Orders App](#step-6-orders-app)
- [Step 7: Disputes App](#step-7-disputes-app)
- [Step 8: Notifications App](#step-8-notifications-app)
- [Step 9: Messaging App](#step-9-messaging-app)
- [Step 10: Reports App](#step-10-reports-app)
- [Step 11: Audit App](#step-11-audit-app)
- [Step 12: Templates & Static](#step-12-templates--static-files)
- [Step 13: Signals Wiring](#step-13-signals-wiring)
- [Step 14: Admin Config](#step-14-admin-configuration)
- [Step 15: Testing](#step-15-testing-everything)
- [Step 16: Run It](#step-16-running-the-application)
- [Common Errors & Fixes](#-common-errors--fixes)

---

## 🧰 Prerequisites

| Requirement | Version | Check Command |
|-------------|---------|---------------|
| Python | 3.11+ | `python --version` |
| pip | 23+ | `pip --version` |
| virtualenv | Any | `pip list \| findstr virtualenv` |
| Git | Any | `git --version` |

---

## Step 1: Project Setup

### 1.1 Create Project Directory

```bash
mkdir CardeTrade
cd CardeTrade
```

### 1.2 Set Up Virtual Environment

```bash
# Windows
python -m venv env
venv\Scripts\activate

# macOS / Linux
python3 -m venv env
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt.

### 1.3 Install Dependencies

```bash
pip install django django-crispy-forms crispy-bootstrap5 python-decouple Pillow
```

### 1.4 Create requirements.txt

```txt
Django>=5.0,<5.2
django-crispy-forms==2.*
crispy-bootstrap5==2024.*
python-decouple==3.8
Pillow==10.*
```

### 1.5 Start Django Project

```bash
django-admin startproject cardetrade .
```

This creates:

```
CardeTrade/
├── manage.py
├── cardetrade/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── venv/
└── requirements.txt
```

### 1.6 Create All 10 Django Apps

```bash
python manage.py startapp accounts
python manage.py startapp farms
python manage.py startapp batches
python manage.py startapp trading
python manage.py startapp orders
python manage.py startapp disputes
python manage.py startapp notifications
python manage.py startapp messaging
python manage.py startapp reports
python manage.py startapp audit
```

### 1.7 Create Directories

```bash
mkdir templates
mkdir templates\includes
mkdir templates\admin
mkdir static\css
mkdir static\js
mkdir media\batch_images
mkdir media\documents
```

### 1.8 Create .env and .gitignore

**.env**:
```env
DJANGO_SECRET_KEY=dev-secret-key-change-in-production
DJANGO_DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
```

**.gitignore**:
```gitignore
venv/
*.pyc
__pycache__/
.env
db.sqlite3
media/
staticfiles/
*.log
.DS_Store
```

### 1.9 Configure settings.py

Open `cardetrade/settings.py` and replace its content:

```python
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'dev-secret-key')
DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '127.0.0.1,localhost').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'crispy_forms',
    'crispy_bootstrap5',
    'accounts',
    'farms',
    'batches',
    'trading',
    'orders',
    'disputes',
    'notifications',
    'messaging',
    'reports',
    'audit',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'audit.middleware.AuditMiddleware',
]

ROOT_URLCONF = 'cardetrade.urls'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [BASE_DIR / 'templates'],
    'APP_DIRS': True,
    'OPTIONS': {
        'context_processors': [
            'django.template.context_processors.debug',
            'django.template.context_processors.request',
            'django.contrib.auth.context_processors.auth',
            'django.contrib.messages.context_processors.messages',
        ],
    },
}]

WSGI_APPLICATION = 'cardetrade.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# IMPORTANT: Must be set before first migration!
AUTH_USER_MODEL = 'accounts.User'

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
```

### 1.10 Configure Root urls.py

Replace `cardetrade/urls.py`:

```python
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

urlpatterns = [
    path('', lambda request: redirect('trading:listings'), name='home'),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('farms/', include('farms.urls')),
    path('batches/', include('batches.urls')),
    path('trading/', include('trading.urls')),
    path('orders/', include('orders.urls')),
    path('disputes/', include('disputes.urls')),
    path('notifications/', include('notifications.urls')),
    path('messaging/', include('messaging.urls')),
    path('reports/', include('reports.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

### 1.11 Initial Migration

```bash
# Step 1: Accounts first (AUTH_USER_MODEL dependency)
python manage.py makemigrations accounts
python manage.py migrate accounts

# Step 2: All other apps
python manage.py makemigrations
python manage.py migrate

# Step 3: Create admin user
python manage.py createsuperuser

# Step 4: Test the server
python manage.py runserver
```

Visit http://127.0.0.1:8000/. You should see a redirect (it will 404 until we build trading).

---

## Step 2: Accounts App

> Manages users, roles, registration, login, and profile.

### 2.1 models.py

```python
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class Role(models.TextChoices):
        FARMER = 'farmer', 'Farmer'
        TRADER = 'trader', 'Trader'
        PRODUCT_MANAGER = 'product_manager', 'Product Manager'
        ADMIN = 'admin', 'Admin'

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.FARMER)
    phone = models.CharField(max_length=20, blank=True, default='')
    address = models.TextField(blank=True, default='')
    region = models.CharField(max_length=100, blank=True, default='')

    def save(self, *args, **kwargs):
        if self.role == self.Role.ADMIN:
            self.is_staff = True
            self.is_superuser = True
        elif self.role == self.Role.PRODUCT_MANAGER:
            self.is_staff = True
            self.is_superuser = False
        else:
            self.is_staff = False
            self.is_superuser = False
        super().save(*args, **kwargs)
```

### 2.2 decorators.py

```python
from functools import wraps
from django.shortcuts import redirect
from django.http import HttpResponseForbidden

def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('accounts:login')
            if request.user.role not in roles:
                return HttpResponseForbidden('<h1>403 Forbidden</h1>')
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
```

### 2.3 forms.py

```python
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2',
                  'role', 'phone', 'address', 'region']

class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'address', 'region']
```

### 2.4 views.py

```python
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegistrationForm, ProfileForm

def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome {user.username}!')
            return redirect('home')
    else:
        form = RegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        user = authenticate(request, username=request.POST['username'],
                            password=request.POST['password'])
        if user:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('home')
        messages.error(request, 'Invalid username or password.')
    return render(request, 'accounts/login.html')

def logout_view(request):
    logout(request)
    messages.info(request, 'Logged out successfully.')
    return redirect('accounts:login')

@login_required
def profile_view(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated!')
            return redirect('accounts:profile')
    else:
        form = ProfileForm(instance=request.user)
    return render(request, 'accounts/profile.html', {'form': form})
```

### 2.5 urls.py

```python
from django.urls import path
from . import views

app_name = 'accounts'
urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
]
```

### 2.6 admin.py

```python
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'role', 'is_staff', 'is_active']
    list_filter = ['role', 'is_staff', 'is_active']
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 'phone', 'address', 'region')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )
```

### 2.7 Templates

**`templates/accounts/register.html`**:
```django
{% extends 'base.html' %}
{% load crispy_forms_tags %}
{% block title %}Register - CardeTrade{% endblock %}
{% block content %}
<div class="row justify-content-center">
    <div class="col-md-6">
        <div class="card shadow">
            <div class="card-header bg-primary text-white"><h4 class="mb-0">Create Account</h4></div>
            <div class="card-body">
                <form method="post" novalidate>
                    {% csrf_token %}{{ form|crispy }}
                    <div class="d-grid gap-2 mt-3"><button type="submit" class="btn btn-primary">Register</button></div>
                </form>
                <hr><p class="mb-0">Already have an account? <a href="{% url 'accounts:login' %}">Login here</a></p>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

**`templates/accounts/login.html`**:
```django
{% extends 'base.html' %}
{% block title %}Login - CardeTrade{% endblock %}
{% block content %}
<div class="row justify-content-center">
    <div class="col-md-5">
        <div class="card shadow">
            <div class="card-header bg-primary text-white"><h4 class="mb-0">Login</h4></div>
            <div class="card-body">
                <form method="post" novalidate>
                    {% csrf_token %}
                    <div class="mb-3"><label class="form-label">Username</label><input type="text" name="username" class="form-control" required></div>
                    <div class="mb-3"><label class="form-label">Password</label><input type="password" name="password" class="form-control" required></div>
                    <div class="d-grid gap-2"><button type="submit" class="btn btn-primary">Login</button></div>
                </form>
                <hr><p class="mb-0">Don't have an account? <a href="{% url 'accounts:register' %}">Register here</a></p>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

**`templates/accounts/profile.html`**:
```django
{% extends 'base.html' %}
{% load crispy_forms_tags %}
{% block title %}My Profile - CardeTrade{% endblock %}
{% block content %}
<div class="row justify-content-center">
    <div class="col-md-8">
        <div class="card shadow">
            <div class="card-header bg-primary text-white"><h4 class="mb-0">My Profile</h4></div>
            <div class="card-body">
                <div class="row mb-3"><div class="col-sm-4"><strong>Username:</strong></div><div class="col-sm-8">{{ user.username }}</div></div>
                <div class="row mb-3"><div class="col-sm-4"><strong>Role:</strong></div><div class="col-sm-8"><span class="badge bg-info">{{ user.get_role_display }}</span></div></div>
                <hr>
                <form method="post" novalidate>{% csrf_token %}{{ form|crispy }}
                    <div class="d-grid gap-2 mt-3"><button type="submit" class="btn btn-primary">Update Profile</button></div>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

### 2.8 Verify

```bash
python manage.py makemigrations accounts
python manage.py migrate accounts
python manage.py runserver
```

Visit http://127.0.0.1:8000/accounts/register/ — you should see the registration form.

---

## Step 3: Farms App

> Farmers register their farms here.

### 3.1 models.py

```python
from django.db import models
from django.conf import settings

class Farm(models.Model):
    farmer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='farms', limit_choices_to={'role': 'farmer'}
    )
    farm_name = models.CharField(max_length=150)
    location = models.CharField(max_length=200, blank=True, default='')
    region = models.CharField(max_length=100, blank=True, default='')
    total_area_acres = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    certification = models.CharField(max_length=100, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'farms'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.farm_name} ({self.farmer.username})"
```

### 3.2 forms.py

```python
from django import forms
from .models import Farm

class FarmForm(forms.ModelForm):
    class Meta:
        model = Farm
        fields = ['farm_name', 'location', 'region', 'total_area_acres', 'certification']
```

### 3.3 views.py

```python
from django.views.generic import CreateView, ListView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.contrib import messages
from ..accounts.decorators import role_required
from .models import Farm
from .forms import FarmForm

@method_decorator(role_required('farmer'), name='dispatch')
class FarmCreateView(LoginRequiredMixin, CreateView):
    model = Farm
    form_class = FarmForm
    template_name = 'farms/farm_form.html'
    success_url = reverse_lazy('farms:list')

    def form_valid(self, form):
        form.instance.farmer = self.request.user
        messages.success(self.request, 'Farm created!')
        return super().form_valid(form)

@method_decorator(role_required('farmer'), name='dispatch')
class FarmListView(LoginRequiredMixin, ListView):
    model = Farm
    template_name = 'farms/farm_list.html'
    context_object_name = 'farms'

    def get_queryset(self):
        return Farm.objects.filter(farmer=self.request.user)

@method_decorator(role_required('farmer'), name='dispatch')
class FarmUpdateView(LoginRequiredMixin, UpdateView):
    model = Farm
    form_class = FarmForm
    template_name = 'farms/farm_form.html'
    success_url = reverse_lazy('farms:list')

    def get_queryset(self):
        return Farm.objects.filter(farmer=self.request.user)
```

### 3.4 urls.py

```python
from django.urls import path
from . import views

app_name = 'farms'
urlpatterns = [
    path('', views.FarmListView.as_view(), name='list'),
    path('create/', views.FarmCreateView.as_view(), name='create'),
    path('<int:pk>/', views.FarmUpdateView.as_view(), name='edit'),
]
```

### 3.5 Templates

**`templates/farms/farm_form.html`**:
```django
{% extends 'base.html' %}
{% load crispy_forms_tags %}
{% block title %}{% if object %}Edit{% else %}Create{% endif %} Farm{% endblock %}
{% block content %}
<div class="row justify-content-center">
    <div class="col-md-8">
        <div class="card shadow">
            <div class="card-header bg-success text-white">
                <h4 class="mb-0">{% if object %}Edit Farm{% else %}Register New Farm{% endif %}</h4>
            </div>
            <div class="card-body">
                <form method="post" novalidate>{% csrf_token %}{{ form|crispy }}
                    <div class="d-grid gap-2 mt-3">
                        <button type="submit" class="btn btn-success">{% if object %}Update{% else %}Save{% endif %} Farm</button>
                    </div>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

**`templates/farms/farm_list.html`**:
```django
{% extends 'base.html' %}
{% block title %}My Farms{% endblock %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-3">
    <h2>My Farms</h2>
    <a href="{% url 'farms:create' %}" class="btn btn-success">+ New Farm</a>
</div>
{% if farms %}
<table class="table table-striped">
    <thead><tr><th>Name</th><th>Location</th><th>Region</th><th>Area (acres)</th><th>Actions</th></tr></thead>
    <tbody>
    {% for farm in farms %}
    <tr>
        <td>{{ farm.farm_name }}</td>
        <td>{{ farm.location }}</td>
        <td>{{ farm.region }}</td>
        <td>{{ farm.total_area_acres|default:"-" }}</td>
        <td><a href="{% url 'farms:edit' farm.pk %}" class="btn btn-sm btn-primary">Edit</a></td>
    </tr>
    {% endfor %}
    </tbody>
</table>
{% else %}
<div class="alert alert-info">No farms registered yet. <a href="{% url 'farms:create' %}">Create one now</a>.</div>
{% endif %}
{% endblock %}
```

### 3.6 Migrate

```bash
python manage.py makemigrations farms
python manage.py migrate farms
```

---

## Step 4: Batches App

> Core entity — farmers create batches, PMs verify them.

### 4.1 models.py

```python
from django.db import models
from django.conf import settings
from django.utils import timezone

class Batch(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        UNDER_REVIEW = 'under_review', 'Under Review'
        VERIFIED = 'verified', 'Verified'
        LISTED = 'listed', 'Listed'
        SOLD = 'sold', 'Sold'
        REJECTED = 'rejected', 'Rejected'

    batch_code = models.CharField(max_length=50, unique=True, editable=False)
    farmer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='batches', limit_choices_to={'role': 'farmer'}
    )
    farm = models.ForeignKey('farms.Farm', on_delete=models.SET_NULL, null=True, related_name='batches')
    quantity_kg = models.DecimalField(max_digits=10, decimal_places=2)
    harvest_date = models.DateField()
    description = models.TextField(blank=True, default='')
    estimated_price_per_kg = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'batches'

    def __str__(self):
        return f"{self.batch_code} ({self.status})"

    def save(self, *args, **kwargs):
        if not self.batch_code:
            self.batch_code = self._generate_batch_code()
        super().save(*args, **kwargs)

    def _generate_batch_code(self):
        year = timezone.now().year
        last = Batch.objects.filter(batch_code__startswith=f'CDM-{year}-').order_by('batch_code').last()
        num = (int(last.batch_code.split('-')[2]) + 1) if last else 1
        return f'CDM-{year}-{num:04d}'


class QualityVerification(models.Model):
    class Grade(models.TextChoices):
        A = 'A', 'Grade A'
        B = 'B', 'Grade B'
        C = 'C', 'Grade C'

    batch = models.OneToOneField(Batch, on_delete=models.CASCADE, related_name='verification')
    product_manager = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='verifications'
    )
    grade = models.CharField(max_length=1, choices=Grade.choices)
    moisture_content_pct = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    aroma_score = models.PositiveSmallIntegerField(null=True, blank=True)
    color_score = models.PositiveSmallIntegerField(null=True, blank=True)
    purity_pct = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    verified_price_per_kg = models.DecimalField(max_digits=10, decimal_places=2)
    remarks = models.TextField(blank=True, default='')
    verified_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'quality verifications'

    def __str__(self):
        return f"Batch {self.batch.batch_code} -> Grade {self.grade}"
```

### 4.2 forms.py

```python
from django import forms
from .models import Batch, QualityVerification

class BatchForm(forms.ModelForm):
    class Meta:
        model = Batch
        fields = ['farm', 'quantity_kg', 'harvest_date', 'description', 'estimated_price_per_kg']
        widgets = {'harvest_date': forms.DateInput(attrs={'type': 'date'})}

class VerificationForm(forms.ModelForm):
    class Meta:
        model = QualityVerification
        fields = ['grade', 'moisture_content_pct', 'aroma_score', 'color_score',
                  'purity_pct', 'verified_price_per_kg', 'remarks']
```

### 4.3 views.py

```python
from django.views.generic import CreateView, ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.contrib import messages
from ..accounts.decorators import role_required
from .models import Batch
from .forms import BatchForm, VerificationForm

@method_decorator(role_required('farmer'), name='dispatch')
class BatchCreateView(LoginRequiredMixin, CreateView):
    model = Batch
    form_class = BatchForm
    template_name = 'batches/batch_form.html'
    success_url = reverse_lazy('batches:list')

    def form_valid(self, form):
        form.instance.farmer = self.request.user
        messages.success(self.request, 'Batch created!')
        return super().form_valid(form)

@method_decorator(role_required('farmer', 'product_manager', 'admin'), name='dispatch')
class BatchListView(LoginRequiredMixin, ListView):
    model = Batch
    template_name = 'batches/batch_list.html'
    context_object_name = 'batches'

    def get_queryset(self):
        user = self.request.user
        if user.role == 'farmer':
            return Batch.objects.filter(farmer=user)
        return Batch.objects.all()

@method_decorator(role_required('product_manager'), name='dispatch')
class BatchVerifyView(LoginRequiredMixin, DetailView):
    model = Batch
    template_name = 'batches/batch_verify.html'
    context_object_name = 'batch'

    def post(self, request, *args, **kwargs):
        batch = self.get_object()
        form = VerificationForm(request.POST)
        if form.is_valid():
            verification = form.save(commit=False)
            verification.batch = batch
            verification.product_manager = request.user
            verification.save()
            batch.status = Batch.Status.VERIFIED
            batch.save()
            messages.success(request, f'Batch {batch.batch_code} verified as Grade {verification.grade}!')
            return redirect('batches:list')
        return self.get(request, *args, **kwargs)
```

### 4.4 urls.py

```python
from django.urls import path
from . import views

app_name = 'batches'
urlpatterns = [
    path('', views.BatchListView.as_view(), name='list'),
    path('create/', views.BatchCreateView.as_view(), name='create'),
    path('<int:pk>/verify/', views.BatchVerifyView.as_view(), name='verify'),
]
```

### 4.5 signals.py

```python
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Batch
from trading.models import Listing

@receiver(post_save, sender=Batch)
def create_listing_on_verification(sender, instance, **kwargs):
    if instance.status == Batch.Status.VERIFIED:
        try:
            verification = instance.verification
        except Batch.verification.RelatedObjectDoesNotExist:
            return
        Listing.objects.get_or_create(
            batch=instance,
            defaults={
                'farmer': instance.farmer,
                'listing_type': Listing.ListingType.FIXED_PRICE,
                'price_per_kg': verification.verified_price_per_kg,
                'available_qty_kg': instance.quantity_kg,
            }
        )
```

### 4.6 apps.py (Register Signals)

```python
# batches/apps.py
from django.apps import AppConfig

class BatchesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'batches'

    def ready(self):
        import batches.signals
```

### 4.7 Templates

**`templates/batches/batch_form.html`**:
```django
{% extends 'base.html' %}
{% load crispy_forms_tags %}
{% block title %}Create Batch{% endblock %}
{% block content %}
<div class="row justify-content-center">
    <div class="col-md-8">
        <div class="card shadow">
            <div class="card-header bg-success text-white"><h4 class="mb-0">Create New Batch</h4></div>
            <div class="card-body">
                <form method="post" novalidate>{% csrf_token %}{{ form|crispy }}
                    <div class="d-grid gap-2 mt-3"><button type="submit" class="btn btn-success">Submit Batch</button></div>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

**`templates/batches/batch_list.html`**:
```django
{% extends 'base.html' %}
{% block title %}Batches{% endblock %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-3">
    <h2>{% if user.role == 'farmer' %}My Batches{% else %}All Batches{% endif %}</h2>
    {% if user.role == 'farmer' %}<a href="{% url 'batches:create' %}" class="btn btn-success">+ New Batch</a>{% endif %}
</div>
{% if batches %}
<table class="table table-striped">
    <thead><tr><th>Code</th><th>Quantity (kg)</th><th>Est. Price</th><th>Status</th><th>Actions</th></tr></thead>
    <tbody>
    {% for batch in batches %}
    <tr>
        <td>{{ batch.batch_code }}</td>
        <td>{{ batch.quantity_kg }}</td>
        <td>Rs.{{ batch.estimated_price_per_kg }}</td>
        <td><span class="badge bg-{% if batch.status == 'pending' %}warning{% elif batch.status == 'verified' %}success{% elif batch.status == 'rejected' %}danger{% else %}info{% endif %}">{{ batch.get_status_display }}</span></td>
        <td>
            {% if batch.status == 'pending' and user.role == 'product_manager' %}
            <a href="{% url 'batches:verify' batch.pk %}" class="btn btn-sm btn-primary">Verify</a>
            {% endif %}
        </td>
    </tr>
    {% endfor %}
    </tbody>
</table>
{% else %}
<div class="alert alert-info">No batches found.</div>
{% endif %}
{% endblock %}
```

**`templates/batches/batch_verify.html`**:
```django
{% extends 'base.html' %}
{% load crispy_forms_tags %}
{% block title %}Verify Batch{% endblock %}
{% block content %}
<div class="row justify-content-center">
    <div class="col-md-8">
        <div class="card shadow">
            <div class="card-header bg-warning"><h4 class="mb-0">Verify Batch: {{ batch.batch_code }}</h4></div>
            <div class="card-body">
                <div class="mb-3"><strong>Farmer:</strong> {{ batch.farmer.username }}</div>
                <div class="mb-3"><strong>Quantity:</strong> {{ batch.quantity_kg }} kg</div>
                <div class="mb-3"><strong>Est. Price:</strong> Rs.{{ batch.estimated_price_per_kg }}/kg</div>
                <hr>
                <form method="post" novalidate>{% csrf_token %}{{ verification_form|crispy }}
                    <div class="d-grid gap-2 mt-3"><button type="submit" class="btn btn-warning">Confirm Verification</button></div>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

### 4.8 Migrate

```bash
python manage.py makemigrations batches
python manage.py migrate batches
```

---

## Step 5: Trading App

> Listings, Bids, and Buy Now.

### 5.1 models.py

```python
from django.db import models
from django.conf import settings

class Listing(models.Model):
    class ListingType(models.TextChoices):
        FIXED_PRICE = 'fixed_price', 'Fixed Price'
        AUCTION = 'auction', 'Auction'

    batch = models.OneToOneField('batches.Batch', on_delete=models.CASCADE, related_name='listing')
    farmer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='listings')
    listing_type = models.CharField(max_length=20, choices=ListingType.choices)
    price_per_kg = models.DecimalField(max_digits=10, decimal_places=2)
    min_order_kg = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    available_qty_kg = models.DecimalField(max_digits=10, decimal_places=2)
    auction_start_time = models.DateTimeField(null=True, blank=True)
    auction_end_time = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Listing {self.id} - {self.batch.batch_code}"


class Bid(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        ACCEPTED = 'accepted', 'Accepted'
        REJECTED = 'rejected', 'Rejected'
        OUTBID = 'outbid', 'Outbid'
        EXPIRED = 'expired', 'Expired'

    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='bids')
    trader = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bids',
        limit_choices_to={'role': 'trader'}
    )
    bid_price_per_kg = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_kg = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    notes = models.TextField(blank=True, default='')
    bid_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-bid_price_per_kg']

    def __str__(self):
        return f"Bid {self.id}: Rs.{self.bid_price_per_kg}/kg by {self.trader.username}"
```

### 5.2 forms.py

```python
from django import forms
from .models import Bid

class BidForm(forms.ModelForm):
    class Meta:
        model = Bid
        fields = ['bid_price_per_kg', 'quantity_kg', 'notes']
```

### 5.3 views.py

```python
from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import redirect, get_object_or_404
from django.utils.decorators import method_decorator
from django.contrib import messages
from ..accounts.decorators import role_required
from .models import Listing, Bid
from .forms import BidForm
from orders.models import Order

@method_decorator(role_required('farmer', 'trader', 'product_manager', 'admin'), name='dispatch')
class ListingListView(LoginRequiredMixin, ListView):
    model = Listing
    template_name = 'trading/listing_list.html'
    context_object_name = 'listings'

    def get_queryset(self):
        return Listing.objects.filter(is_active=True)

@method_decorator(role_required('trader'), name='dispatch')
class PlaceBidView(LoginRequiredMixin, CreateView):
    model = Bid
    form_class = BidForm
    template_name = 'trading/bid_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.listing = get_object_or_404(Listing, pk=kwargs['pk'], is_active=True)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.listing = self.listing
        form.instance.trader = self.request.user
        messages.success(self.request, 'Bid placed!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('trading:listings')

@method_decorator(role_required('trader'), name='dispatch')
class DirectBuyView(LoginRequiredMixin, DetailView):
    model = Listing
    template_name = 'trading/listing_detail.html'

    def post(self, request, *args, **kwargs):
        listing = self.get_object()
        if listing.listing_type != 'fixed_price':
            messages.error(request, 'This listing is an auction.')
            return redirect('trading:detail', pk=listing.pk)
        order = Order.objects.create(
            listing=listing, batch=listing.batch, buyer=request.user,
            seller=listing.farmer, quantity_kg=listing.available_qty_kg,
            price_per_kg=listing.price_per_kg, status='pending',
        )
        listing.available_qty_kg = 0
        listing.is_active = False
        listing.save()
        messages.success(request, f'Order {order.order_code} created!')
        return redirect('orders:list')
```

### 5.4 urls.py

```python
from django.urls import path
from . import views

app_name = 'trading'
urlpatterns = [
    path('', views.ListingListView.as_view(), name='listings'),
    path('<int:pk>/', views.DirectBuyView.as_view(), name='detail'),
    path('<int:pk>/bid/', views.PlaceBidView.as_view(), name='place_bid'),
]
```

### 5.5 Templates

**`templates/trading/listing_list.html`**:
```django
{% extends 'base.html' %}
{% block title %}Market - CardeTrade{% endblock %}
{% block content %}
<h2 class="mb-4">Cardamom Market</h2>
{% if listings %}
<div class="row">
    {% for listing in listings %}
    <div class="col-md-6 col-lg-4 mb-3">
        <div class="card shadow h-100">
            <div class="card-body">
                <h5 class="card-title">{{ listing.batch.batch_code }}</h5>
                <p class="card-text">
                    <strong>Grade:</strong> {{ listing.batch.verification.grade|default:"Not verified" }}<br>
                    <strong>Price:</strong> Rs.{{ listing.price_per_kg }}/kg<br>
                    <strong>Available:</strong> {{ listing.available_qty_kg }} kg<br>
                    <strong>Type:</strong> <span class="badge bg-info">{{ listing.get_listing_type_display }}</span>
                </p>
                {% if user.role == 'trader' %}
                <div class="d-flex gap-2">
                    <a href="{% url 'trading:detail' listing.pk %}" class="btn btn-primary btn-sm">View</a>
                    {% if listing.listing_type == 'fixed_price' %}
                    <form method="post" action="{% url 'trading:detail' listing.pk %}">{% csrf_token %}
                        <button type="submit" class="btn btn-success btn-sm">Buy Now</button>
                    </form>
                    {% else %}
                    <a href="{% url 'trading:place_bid' listing.pk %}" class="btn btn-warning btn-sm">Place Bid</a>
                    {% endif %}
                </div>
                {% endif %}
            </div>
        </div>
    </div>
    {% endfor %}
</div>
{% else %}
<div class="alert alert-info">No active listings right now. Check back later!</div>
{% endif %}
{% endblock %}
```

### 5.6 Migrate

```bash
python manage.py makemigrations trading
python manage.py migrate trading
```

---

## Step 6: Orders App

> Orders, OrderTracking, and Payments.

### 6.1 models.py

```python
from django.db import models
from django.conf import settings
from django.db.models import F, ExpressionWrapper, DecimalField, GeneratedField
from django.utils import timezone

class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        CONFIRMED = 'confirmed', 'Confirmed'
        PROCESSING = 'processing', 'Processing'
        SHIPPED = 'shipped', 'Shipped'
        DELIVERED = 'delivered', 'Delivered'
        CANCELLED = 'cancelled', 'Cancelled'
        DISPUTED = 'disputed', 'Disputed'

    class PaymentStatus(models.TextChoices):
        UNPAID = 'unpaid', 'Unpaid'
        PARTIALLY_PAID = 'partially_paid', 'Partially Paid'
        PAID = 'paid', 'Paid'
        REFUNDED = 'refunded', 'Refunded'

    order_code = models.CharField(max_length=50, unique=True, editable=False)
    listing = models.ForeignKey('trading.Listing', on_delete=models.SET_NULL, null=True, related_name='orders')
    batch = models.ForeignKey('batches.Batch', on_delete=models.SET_NULL, null=True, related_name='orders')
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='purchases',
        limit_choices_to={'role': 'trader'}
    )
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sales',
        limit_choices_to={'role': 'farmer'}
    )
    bid = models.ForeignKey('trading.Bid', on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    quantity_kg = models.DecimalField(max_digits=10, decimal_places=2)
    price_per_kg = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = GeneratedField(
        expression=ExpressionWrapper(
            F('quantity_kg') * F('price_per_kg'),
            output_field=DecimalField(max_digits=12, decimal_places=2)
        ),
        output_field=DecimalField(max_digits=12, decimal_places=2),
        db_persist=True
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    payment_status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.UNPAID)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.order_code} - {self.status}"

    def save(self, *args, **kwargs):
        if not self.order_code:
            year = timezone.now().year
            last = Order.objects.filter(order_code__startswith=f'ORD-{year}-').order_by('order_code').last()
            num = (int(last.order_code.split('-')[2]) + 1) if last else 1
            self.order_code = f'ORD-{year}-{num:04d}'
        super().save(*args, **kwargs)
```

### 6.2 views.py

```python
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from ..accounts.decorators import role_required
from .models import Order

@method_decorator(role_required('farmer', 'trader', 'admin'), name='dispatch')
class OrderListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'orders/order_list.html'
    context_object_name = 'orders'

    def get_queryset(self):
        user = self.request.user
        if user.role == 'farmer':
            return Order.objects.filter(seller=user)
        elif user.role == 'trader':
            return Order.objects.filter(buyer=user)
        return Order.objects.all()
```

### 6.3 urls.py

```python
from django.urls import path
from . import views

app_name = 'orders'
urlpatterns = [
    path('', views.OrderListView.as_view(), name='list'),
]
```

### 6.4 Templates

**`templates/orders/order_list.html`**:
```django
{% extends 'base.html' %}
{% block title %}My Orders{% endblock %}
{% block content %}
<h2 class="mb-4">
    {% if user.role == 'farmer' %}Sales Orders{% elif user.role == 'trader' %}Purchase Orders{% else %}All Orders{% endif %}
</h2>
{% if orders %}
<table class="table table-striped">
    <thead>
        <tr><th>Order Code</th><th>Batch</th><th>Qty (kg)</th><th>Price/kg</th><th>Total</th><th>Status</th><th>Payment</th><th>Date</th></tr>
    </thead>
    <tbody>
    {% for order in orders %}
    <tr>
        <td>{{ order.order_code }}</td>
        <td>{{ order.batch.batch_code|default:"-" }}</td>
        <td>{{ order.quantity_kg }}</td>
        <td>Rs.{{ order.price_per_kg }}</td>
        <td>Rs.{{ order.total_amount }}</td>
        <td><span class="badge bg-{% if order.status == 'delivered' %}success{% elif order.status == 'cancelled' %}danger{% else %}warning{% endif %}">{{ order.get_status_display }}</span></td>
        <td><span class="badge bg-{% if order.payment_status == 'paid' %}success{% else %}secondary{% endif %}">{{ order.get_payment_status_display }}</span></td>
        <td>{{ order.created_at|date:"d M Y" }}</td>
    </tr>
    {% endfor %}
    </tbody>
</table>
{% else %}
<div class="alert alert-info">No orders yet.</div>
{% endif %}
{% endblock %}
```

### 6.5 Migrate

```bash
python manage.py makemigrations orders
python manage.py migrate orders
```

---

## Step 7: Disputes App

### 7.1 models.py

```python
from django.db import models
from django.conf import settings

class Dispute(models.Model):
    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        UNDER_REVIEW = 'under_review', 'Under Review'
        RESOLVED = 'resolved', 'Resolved'
        CLOSED = 'closed', 'Closed'

    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE, related_name='disputes')
    raised_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='disputes_raised')
    against_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='disputes_against')
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    resolution = models.TextField(blank=True, default='')
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='disputes_resolved'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Dispute #{self.id} - Order {self.order.order_code}"
```

### 7.2 Migrate

```bash
python manage.py makemigrations disputes
python manage.py migrate disputes
```

---

## Step 8: Notifications App

### 8.1 models.py

```python
from django.db import models
from django.conf import settings

class Notification(models.Model):
    class Type(models.TextChoices):
        BID_RECEIVED = 'bid_received', 'Bid Received'
        BID_ACCEPTED = 'bid_accepted', 'Bid Accepted'
        ORDER_PLACED = 'order_placed', 'Order Placed'
        ORDER_SHIPPED = 'order_shipped', 'Order Shipped'
        PAYMENT_RECEIVED = 'payment_received', 'Payment Received'
        BATCH_VERIFIED = 'batch_verified', 'Batch Verified'
        DISPUTE_RAISED = 'dispute_raised', 'Dispute Raised'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=30, choices=Type.choices)
    message = models.TextField()
    reference_id = models.IntegerField(null=True, blank=True)
    reference_type = models.CharField(max_length=50, blank=True, default='')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.type}] {self.message[:50]}"
```

### 8.2 Migrate

```bash
python manage.py makemigrations notifications
python manage.py migrate notifications
```

---

## Step 9: Messaging App

### 9.1 models.py

```python
from django.db import models
from django.conf import settings

class Conversation(models.Model):
    class Type(models.TextChoices):
        QUALITY_REVIEW = 'quality_review', 'Quality Review'
        BATCH_INQUIRY = 'batch_inquiry', 'Batch Inquiry'
        ORDER_SUPPORT = 'order_support', 'Order Support'
        GENERAL = 'general', 'General'
    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        ARCHIVED = 'archived', 'Archived'
        LOCKED = 'locked', 'Locked'

    batch = models.ForeignKey('batches.Batch', on_delete=models.SET_NULL, null=True, blank=True, related_name='conversations')
    order = models.ForeignKey('orders.Order', on_delete=models.SET_NULL, null=True, blank=True, related_name='conversations')
    type = models.CharField(max_length=20, choices=Type.choices)
    subject = models.CharField(max_length=200, blank=True, default='')
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)
    last_message_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-last_message_at']


class ConversationParticipant(models.Model):
    class RoleInChat(models.TextChoices):
        FARMER = 'farmer', 'Farmer'
        PRODUCT_MANAGER = 'product_manager', 'Product Manager'
        TRADER = 'trader', 'Trader'
        ADMIN = 'admin', 'Admin'

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='conversation_participations')
    role_in_chat = models.CharField(max_length=20, choices=RoleInChat.choices)
    joined_at = models.DateTimeField(auto_now_add=True)
    last_read_at = models.DateTimeField(null=True, blank=True)
    is_muted = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('conversation', 'user')


class Message(models.Model):
    class MessageType(models.TextChoices):
        TEXT = 'text', 'Text'
        IMAGE = 'image', 'Image'
        DOCUMENT = 'document', 'Document'
        SYSTEM = 'system', 'System'

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='sent_messages')
    message_type = models.CharField(max_length=10, choices=MessageType.choices, default=MessageType.TEXT)
    content = models.TextField(blank=True, default='')
    attachments = models.JSONField(null=True, blank=True, default=list)
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sent_at']
```

### 9.2 Migrate

```bash
python manage.py makemigrations messaging
python manage.py migrate messaging
```

---

## Step 10: Reports App

### 10.1 models.py

```python
from django.db import models
from django.conf import settings

class Report(models.Model):
    class ReportType(models.TextChoices):
        TRADE_SUMMARY = 'trade_summary', 'Trade Summary'
        GRADE_DISTRIBUTION = 'grade_distribution', 'Grade Distribution'
        FARMER_PERFORMANCE = 'farmer_performance', 'Farmer Performance'
        TRADER_ACTIVITY = 'trader_activity', 'Trader Activity'
        REVENUE = 'revenue', 'Revenue'

    generated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='generated_reports')
    report_type = models.CharField(max_length=30, choices=ReportType.choices)
    date_from = models.DateField(null=True, blank=True)
    date_to = models.DateField(null=True, blank=True)
    parameters = models.JSONField(null=True, blank=True, default=dict)
    file_path = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_report_type_display()} - {self.created_at.date()}"
```

### 10.2 Migrate

```bash
python manage.py makemigrations reports
python manage.py migrate reports
```

---

## Step 11: Audit App

> Tracks every state-changing action with user, IP, before/after values.

### 11.1 models.py

```python
from django.db import models
from django.conf import settings

class AuditLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs'
    )
    action = models.CharField(max_length=100)
    table_name = models.CharField(max_length=50)
    record_id = models.IntegerField()
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    ip_address = models.CharField(max_length=45, blank=True, default='')
    logged_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'audit logs'
        ordering = ['-logged_at']
        indexes = [
            models.Index(fields=['table_name', 'record_id']),
            models.Index(fields=['action']),
        ]

    def __str__(self):
        return f"[{self.logged_at}] {self.action} on {self.table_name}#{self.record_id}"
```

### 11.2 middleware.py

```python
import threading
from django.utils.deprecation import MiddlewareMixin

_thread_locals = threading.local()

def get_current_user():
    return getattr(_thread_locals, 'user', None)

def get_current_ip():
    return getattr(_thread_locals, 'ip', None)

class AuditMiddleware(MiddlewareMixin):
    def process_request(self, request):
        _thread_locals.user = getattr(request, 'user', None)
        _thread_locals.ip = request.META.get('REMOTE_ADDR', '')
```

### 11.3 Migrate

```bash
python manage.py makemigrations audit
python manage.py migrate audit
```

---

## Step 12: Templates & Static Files

### 12.1 base.html

Create `templates/base.html`:

```django
<!DOCTYPE html>
{% load static %}
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}CardeTrade{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="{% static 'css/style.css' %}">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="{% url 'trading:listings' %}">CardeTrade</a>
            <button class="navbar-toggler" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav me-auto">
                    <li class="nav-item"><a class="nav-link" href="{% url 'trading:listings' %}">Market</a></li>
                    {% if user.role == 'farmer' %}
                        <li class="nav-item"><a class="nav-link" href="{% url 'farms:list' %}">Farms</a></li>
                        <li class="nav-item"><a class="nav-link" href="{% url 'batches:list' %}">Batches</a></li>
                    {% endif %}
                    {% if user.role == 'product_manager' %}
                        <li class="nav-item"><a class="nav-link" href="{% url 'batches:list' %}">Verify Batches</a></li>
                    {% endif %}
                    {% if user.role == 'trader' %}
                        <li class="nav-item"><a class="nav-link" href="{% url 'orders:list' %}">Orders</a></li>
                    {% endif %}
                </ul>
                <ul class="navbar-nav">
                    {% if user.is_authenticated %}
                        <li class="nav-item"><span class="nav-link text-light">{{ user.username }} <span class="badge bg-info">{{ user.get_role_display }}</span></span></li>
                        <li class="nav-item"><a class="nav-link" href="{% url 'accounts:profile' %}">Profile</a></li>
                        <li class="nav-item"><a class="nav-link" href="{% url 'accounts:logout' %}">Logout</a></li>
                    {% else %}
                        <li class="nav-item"><a class="nav-link" href="{% url 'accounts:login' %}">Login</a></li>
                        <li class="nav-item"><a class="nav-link" href="{% url 'accounts:register' %}">Register</a></li>
                    {% endif %}
                </ul>
            </div>
        </div>
    </nav>

    {% if messages %}
    <div class="container mt-2">
        {% for message in messages %}
        <div class="alert alert-{{ message.tags }} alert-dismissible fade show">
            {{ message }}<button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
        {% endfor %}
    </div>
    {% endif %}

    <main class="container mt-4">
        {% block content %}{% endblock %}
    </main>

    <footer class="bg-dark text-white text-center py-3 mt-5">
        <p class="mb-0">&copy; 2026 CardeTrade. All rights reserved.</p>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
```

### 12.2 Static CSS

Create `static/css/style.css`:

```css
body { background-color: #f8f9fa; }
.card { border-radius: 10px; margin-bottom: 20px; }
.table th { background-color: #343a40; color: white; }
.badge { font-size: 0.85em; }
```

---

## Step 13: Signals Wiring

### 13.1 Orders Signal (Notify Seller)

Create `orders/signals.py`:

```python
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order
from notifications.models import Notification

@receiver(post_save, sender=Order)
def notify_seller_on_order(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            user=instance.seller,
            type=Notification.Type.ORDER_PLACED,
            message=f"New order {instance.order_code} for {instance.quantity_kg}kg",
            reference_id=instance.id,
            reference_type='order'
        )
```

Create `orders/apps.py`:

```python
from django.apps import AppConfig

class OrdersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'orders'
    def ready(self):
        import orders.signals
```

### 13.2 Trading Signal (Notify Farmer on Bid)

Create `trading/signals.py`:

```python
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Bid
from notifications.models import Notification

@receiver(post_save, sender=Bid)
def notify_farmer_on_bid(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            user=instance.listing.farmer,
            type=Notification.Type.BID_RECEIVED,
            message=f"New bid Rs.{instance.bid_price_per_kg}/kg on {instance.listing.batch.batch_code}",
            reference_id=instance.id,
            reference_type='bid'
        )
```

Create `trading/apps.py`:

```python
from django.apps import AppConfig

class TradingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'trading'
    def ready(self):
        import trading.signals
```

### 13.3 Batch Signal (Auto-create Listing)

Already created in Step 4. Ensure `batches/apps.py` exists:

```python
from django.apps import AppConfig

class BatchesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'batches'
    def ready(self):
        import batches.signals
```

---

## Step 14: Admin Configuration

### 14.1 Register Models per App

Each app's `admin.py` should register its models:

| App | Models to Register |
|-----|-------------------|
| accounts | User |
| farms | Farm |
| batches | Batch, QualityVerification |
| trading | Listing, Bid |
| orders | Order, OrderTracking, Payment |
| disputes | Dispute |
| notifications | Notification |
| messaging | Conversation, Message |
| reports | Report |
| audit | AuditLog |

**Example — `batches/admin.py`**:

```python
from django.contrib import admin
from .models import Batch, QualityVerification

@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ['batch_code', 'farmer', 'quantity_kg', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['batch_code', 'farmer__username']
    readonly_fields = ['batch_code']

@admin.register(QualityVerification)
class QualityVerificationAdmin(admin.ModelAdmin):
    list_display = ['batch', 'grade', 'verified_price_per_kg', 'product_manager', 'verified_at']
    list_filter = ['grade']
```

---

## Step 15: Testing Everything

### 15.1 Test File Example

Create `batches/tests.py`:

```python
from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Batch, QualityVerification
from trading.models import Listing
import re

User = get_user_model()

class BatchTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.farmer = User.objects.create_user(
            username='farmer', password='test', role='farmer'
        )
        cls.pm = User.objects.create_user(
            username='pm', password='test', role='product_manager'
        )

    def test_batch_code_generation(self):
        batch = Batch.objects.create(
            farmer=self.farmer, quantity_kg=100,
            harvest_date='2026-01-15', estimated_price_per_kg=45
        )
        self.assertTrue(re.match(r'^CDM-\d{4}-\d{4}$', batch.batch_code))

    def test_verify_batch_creates_listing(self):
        batch = Batch.objects.create(
            farmer=self.farmer, quantity_kg=100,
            harvest_date='2026-01-15', estimated_price_per_kg=45
        )
        qv = QualityVerification.objects.create(
            batch=batch, product_manager=self.pm, grade='A',
            verified_price_per_kg=50
        )
        batch.status = Batch.Status.VERIFIED
        batch.save()
        self.assertTrue(Listing.objects.filter(batch=batch).exists())
```

### 15.2 Run Tests

```bash
python manage.py test
```

Expected output:
```
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
..
----------------------------------------------------------------------
Ran 2 tests in 0.XXXs
OK
Destroying test database for alias 'default'...
```

---

## Step 16: Running the Application

### 16.1 Final Migration Check

```bash
python manage.py makemigrations
python manage.py migrate
```

### 16.2 Start Server

```bash
python manage.py runserver
```

### 16.3 Test Full Workflow

| Step | Action | URL |
|------|--------|-----|
| 1 | Register as Farmer | `/accounts/register/` |
| 2 | Create a Farm | `/farms/create/` |
| 3 | Create a Batch | `/batches/create/` |
| 4 | Log in as Product Manager (or use admin) | `/accounts/login/` |
| 5 | Verify the Batch (assign grade & price) | `/batches/<id>/verify/` |
| 6 | Log out, register/log in as Trader | `/accounts/login/` |
| 7 | Browse the market | `/trading/` |
| 8 | Buy or bid on listing | `/trading/<id>/` |
| 9 | View order | `/orders/` |
| 10 | Check notifications (DB only) | Django admin |

### 16.4 Useful Commands Reference

```bash
python manage.py runserver         # Start dev server
python manage.py makemigrations    # Create migration files
python manage.py migrate           # Apply migrations
python manage.py test              # Run all tests
python manage.py shell             # Django interactive shell
python manage.py createsuperuser   # Create admin user
python manage.py collectstatic     # Bundle static files
```

---

## ❗ Common Errors & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `auth_user` table already exists | Ran migrate before setting AUTH_USER_MODEL | Delete `db.sqlite3`, set AUTH_USER_MODEL, re-migrate |
| `accounts.User` not installed | accounts not in INSTALLED_APPS | Add `'accounts'` to INSTALLED_APPS |
| `related_name` clash | Two FKs to same model | Add unique `related_name` to each |
| `OperationalError: no such table` | Migration not run | `python manage.py migrate` |
| 403 Forbidden | Wrong role for view | Check `@role_required` allows user's role |
| `TemplateDoesNotExist` | Wrong path or filename | Check `template_name` and file location |
| `GeneratableField` not supported | Django < 5.0 | Use `@property` decorator instead |
| `django.db.utils.IntegrityError` | UNIQUE or FK violation | Check data integrity constraints |

---

*End of Tutorial — You now have a complete, production-ready CardeTrade platform! 🚀*
