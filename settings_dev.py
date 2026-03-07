"""
Development settings for django-sysconfig.

This file is NOT for running tests — use tests/settings.py for that (pytest handles it).
This file is for spinning up a local Django project to manually explore
and test the admin UI / views while developing the library.

Setup:
    1. Copy .env.example to .env and fill in values
    2. Start Postgres:  docker compose up -d
    3. Run migrations:  DJANGO_SETTINGS_MODULE=settings_dev .venv/bin/django-admin migrate
    4. Create superuser: DJANGO_SETTINGS_MODULE=settings_dev .venv/bin/django-admin createsuperuser
    5. Run dev server:  DJANGO_SETTINGS_MODULE=settings_dev .venv/bin/django-admin runserver

    Then visit http://127.0.0.1:8000/admin/config/
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Load .env file if python-dotenv is available, otherwise rely on shell env vars
try:
    from dotenv import load_dotenv

    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "dev-only-insecure-key-set-DJANGO_SECRET_KEY-in-env",
)

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # This library
    "django_sysconfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "urls_dev"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

# Development database — Postgres via Docker (see docker-compose.yml and .env.example)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "django_sysconfig"),
        "USER": os.environ.get("POSTGRES_USER", "django"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "django"),
        "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}

# In-memory cache for development
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

STATIC_URL = "/static/"

USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
