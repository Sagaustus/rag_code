"""Django settings for rag_system project."""

import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load local .env if present (production should use real environment vars).
load_dotenv(BASE_DIR / ".env", override=False)


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "django-insecure-change-me",
)

DEBUG = os.getenv("DJANGO_DEBUG", "false").strip().lower() in {"1", "true", "yes", "on"}

ALLOWED_HOSTS = [
    h.strip()
    for h in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if h.strip()
]

CSRF_TRUSTED_ORIGINS = [
    o.strip()
    for o in os.getenv("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",")
    if o.strip()
]


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rag_core",
    "rag_collections",
    "rag_chat",
    "rag_analytics",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "rag_system.middleware.ApiKeyMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "rag_system.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "rag_system.wsgi.application"


# Database
# Use Postgres everywhere for consistency.
# - In production (Heroku, etc.), set DATABASE_URL.
# - In local dev, use docker-compose Postgres and keep DATABASE_URL pointing to it.

DATABASES = {
    "default": dj_database_url.config(
        default=os.getenv("DATABASE_URL", "postgres://rag:rag@localhost:5432/rag"),
        conn_max_age=int(os.getenv("DB_CONN_MAX_AGE", "60")),
    )
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Common reverse-proxy / PaaS defaults
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# API key required for /api/* (UI uses server-side /chat/* proxies so keys never hit browsers).
RAG_API_KEY = os.getenv("RAG_API_KEY", "").strip()

# Maximum characters accepted in a single chat query.
RAG_MAX_QUERY_LENGTH = int(os.getenv("RAG_MAX_QUERY_LENGTH", "2000"))

# Django REST Framework
REST_FRAMEWORK = {
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        # Applies to all DRF views. Override per-view with throttle_classes/scope.
        "anon": os.getenv("RAG_THROTTLE_RATE", "60/hour"),
    },
    # Trust one upstream proxy hop (Heroku router, nginx, etc.) when
    # determining the real client IP for throttle keys.
    "NUM_PROXIES": int(os.getenv("RAG_NUM_PROXIES", "1")),
}
