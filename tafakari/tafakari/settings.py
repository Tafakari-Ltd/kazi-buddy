from pathlib import Path
from datetime import timedelta
import os
from dotenv import load_dotenv

# Load environment variables from .env locally (Render ignores this in production)
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# Use environment variable for secret key
SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret-key-for-dev")

# Set DEBUG based on environment
DEBUG = os.getenv("DEBUG", "False") == "True"

# Allow all domains on Render, restrict this in production if needed
ALLOWED_HOSTS = ['.onrender.com', 'localhost', '127.0.0.1']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'rest_framework',
    'rest_framework.authtoken',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'dj_rest_auth.registration',
    'accounts',
    'adminpanel',
    'analytics',
    'applications',
    'assignments',
    'employers',
    'workers',
    'jobs',
    'ratings',
    'utils',
    'skills',
    'documents',
]

SITE_ID = 1

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Added for static files in production
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'tafakari.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'tafakari.wsgi.application'

# Database - Render injects DATABASE_URL into env
import dj_database_url

DATABASES = {
    'default': dj_database_url.config(conn_max_age=600)
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# WhiteNoise configuration (serves static files on Render)
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'accounts.CustomUser'

# Django REST
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
}

REST_AUTH_REGISTER_SERIALIZERS = {
    'REGISTER_SERIALIZER': 'accounts.serializers.CustomRegisterSerializer',
}

# Email backend using Gmail (use app password for security)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = os.getenv("DEFAULT_FROM_EMAIL")
EMAIL_HOST_PASSWORD = os.getenv("DEFAULT_FROM_EMAIL_PASSWORD")
EMAIL_USE_TLS = True

# Google OAuth credentials
GOOGLE_OAUTH_CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
GOOGLE_OAUTH_CLIENT_SECRET = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")
GOOGLE_OAUTH_CALLBACK_URL = os.getenv("GOOGLE_OAUTH_CALLBACK_URL")

SOCIALACCOUNT_EMAIL_AUTHENTICATION = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True

SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "APPS": [
            {
                "client_id": GOOGLE_OAUTH_CLIENT_ID,
                "secret": GOOGLE_OAUTH_CLIENT_SECRET,
                "key": "",
            },
        ],
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {
            "access_type": "online",
        },
    }
}
