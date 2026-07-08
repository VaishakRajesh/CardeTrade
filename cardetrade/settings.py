"""
CardeTrade Django Settings

This module contains all Django configuration for the CardeTrade project.
Settings are organized into sections:

1. Core Settings: Secret key, debug mode, allowed hosts
2. Installed Apps: Django apps and third-party packages
3. Middleware: Request/response processing pipeline
4. Templates: Template engine configuration
5. Database: Database connection settings
6. Auth: Authentication settings
7. Static/Media: File storage settings
8. Third-Party: Crispy Forms configuration

IMPORTANT: This file contains sensitive information (SECRET_KEY).
Never commit this file to version control. Use environment variables in production.
"""

from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: Keep the secret key used in production secret!
# In production, use: SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
SECRET_KEY = 'django-insecure-mw^uw=l4b(l8b-yk78x#m#ixzhe$vlm+ahvw$5db@9-fpa*4!o'

# SECURITY WARNING: Don't run with debug turned on in production!
# In production, use: DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True'
DEBUG = True

# Allowed hosts for deployment
# In production, set to your domain: ALLOWED_HOSTS = ['yourdomain.com']
ALLOWED_HOSTS = []

# ============================================================
# INSTALLED APPS
# ============================================================
# Django apps and third-party packages installed in this project
INSTALLED_APPS = [
    # Django built-in apps
    'django.contrib.admin',      # Admin panel
    'django.contrib.auth',       # Authentication system
    'django.contrib.contenttypes', # Content type framework
    'django.contrib.sessions',   # Session framework
    'django.contrib.messages',   # Messaging framework
    'django.contrib.staticfiles', # Static file serving
    
    # Third-party apps
    'crispy_forms',              # Form rendering utilities
    'crispy_bootstrap5',         # Bootstrap 5 template pack for crispy forms
    
    # Local apps
    'app',                       # Main application (CardeTrade)
]

# ============================================================
# MIDDLEWARE
# ============================================================
# Django middleware for processing requests and responses
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',           # Security headers
    'django.contrib.sessions.middleware.SessionMiddleware',   # Session handling
    'django.middleware.common.CommonMiddleware',              # Common utilities
    'django.middleware.csrf.CsrfViewMiddleware',              # CSRF protection
    'django.contrib.auth.middleware.AuthenticationMiddleware', # User authentication
    'django.contrib.messages.middleware.MessageMiddleware',   # Message framework
    'django.middleware.clickjacking.XFrameOptionsMiddleware', # Clickjacking protection
    'app.middleware.AuditMiddleware',                         # Custom: Audit trail support
]

# Root URL configuration
ROOT_URLCONF = 'cardetrade.urls'

# ============================================================
# TEMPLATES
# ============================================================
# Template engine configuration
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # Project-level templates
        'APP_DIRS': True,  # Look for templates in app directories
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',    # Debug context
                'django.template.context_processors.request',  # Request context
                'django.contrib.auth.context_processors.auth', # User context
                'django.contrib.messages.context_processors.messages', # Messages context
            ],
        },
    },
]

# WSGI application entry point
WSGI_APPLICATION = 'cardetrade.wsgi.application'

# ============================================================
# DATABASE
# ============================================================
# SQLite database for development
# In production, use PostgreSQL or MySQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ============================================================
# AUTH
# ============================================================
# Custom user model (must be set before first migration)
AUTH_USER_MODEL = 'app.User'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ============================================================
# INTERNATIONALIZATION
# ============================================================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True  # Enable translations
USE_TZ = True    # Enable timezone-aware datetimes

# ============================================================
# STATIC FILES (CSS, JavaScript, Images)
# ============================================================
STATIC_URL = 'static/'  # URL prefix for static files
STATICFILES_DIRS = [BASE_DIR / 'static']  # Where to find static files
STATIC_ROOT = BASE_DIR / 'staticfiles'    # Where to collect static files

# ============================================================
# MEDIA FILES (User Uploads)
# ============================================================
MEDIA_URL = '/media/'  # URL prefix for media files
MEDIA_ROOT = BASE_DIR / 'media'  # Where to store uploaded files

# ============================================================
# AUTH URLS
# ============================================================
LOGIN_URL = '/login/'              # Redirect URL for login required
LOGIN_REDIRECT_URL = '/dashboard/' # Redirect after successful login
LOGOUT_REDIRECT_URL = '/login/'   # Redirect after logout

# ============================================================
# CRISPY FORMS
# ============================================================
# Bootstrap 5 template pack for form rendering
CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'

# ============================================================
# DEFAULT AUTO FIELD
# ============================================================
# Use BigAutoField for primary keys (64-bit integers)
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
