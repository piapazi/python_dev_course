"""
Django settings for Trust Wave Bambili project.
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
# In production, this should be set as an environment variable
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-placeholder-key-for-development')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'


ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Add your app name here
    'trustwave.apps.TrustwaveConfig',
    # Third party apps
    'axes',  # For brute force protection
    "widget_tweaks",
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Brute force protection
    'axes.middleware.AxesMiddleware',
]

ROOT_URLCONF = 'django_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
            ],
        },
    },
]

WSGI_APPLICATION = 'django_project.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Custom Authentication Backend
AUTHENTICATION_BACKENDS = [
    # AxesBackend should be the first backend
    'axes.backends.AxesBackend',
    # Django's default
    'django.contrib.auth.backends.ModelBackend',
]

# Custom User Model
AUTH_USER_MODEL = 'trustwave.CustomUser'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 10,  # Stronger passwords
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Django Axes Configuration (Brute Force Protection)
AXES_FAILURE_LIMIT = 5  # Number of login attempts before lockout
AXES_LOCKOUT_TIME = 1  # Lockout time in hours
AXES_RESET_ON_SUCCESS = True  # Reset the number of failed attempts on success

# Session Security Settings
SESSION_COOKIE_SECURE = not DEBUG  # Send cookies only via HTTPS in production
SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access to session cookie
SESSION_COOKIE_SAMESITE = 'Lax'  # Controls when cookies are sent with requests from external sites
SESSION_EXPIRE_AT_BROWSER_CLOSE = True  # Session expires when browser is closed
SESSION_COOKIE_AGE = 3600  # Session timeout in seconds: 1 hour

# CSRF Protection
CSRF_COOKIE_SECURE = not DEBUG  # Send CSRF cookie only via HTTPS in production
CSRF_COOKIE_HTTPONLY = True  # Prevent JavaScript access to CSRF cookie
CSRF_COOKIE_SAMESITE = 'Lax'  # Controls when cookies are sent

# Security Headers
SECURE_BROWSER_XSS_FILTER = True  # Enable browser's XSS filtering protection
SECURE_CONTENT_TYPE_NOSNIFF = True  # Prevent browser from guessing content types
X_FRAME_OPTIONS = 'DENY'  # Prevent site from being embedded in frames/iframes

# Only enable these in production
if not DEBUG:
    SECURE_HSTS_SECONDS = 31536000  # Enable HTTP Strict Transport Security: 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True  # Apply HSTS to subdomains
    SECURE_HSTS_PRELOAD = True  # Allow site to be included in browser HSTS preload list
    SECURE_SSL_REDIRECT = True  # Redirect HTTP to HTTPS

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Static files
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Login URL
LOGIN_URL = '/login/'