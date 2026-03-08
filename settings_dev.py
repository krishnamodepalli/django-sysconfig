"""
Development settings for django-sysconfig.

This file is NOT for running tests — use tests/settings.py for that (pytest handles it).
This file is for spinning up a local Django project to manually explore
and test the admin UI / views while developing the library.

Setup:
    1. pip install -e ".[dev]"
    2. DJANGO_SETTINGS_MODULE=settings_dev .venv/bin/django-admin migrate
    3. DJANGO_SETTINGS_MODULE=settings_dev .venv/bin/django-admin createsuperuser
    4. DJANGO_SETTINGS_MODULE=settings_dev .venv/bin/django-admin runserver

    Then visit http://127.0.0.1:8000/admin/config/
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

SECRET_KEY = "dev-only-insecure-key-do-not-use-in-production"

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
    # Local demo app for manual dev testing (not packaged)
    "demo",
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

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

STATIC_URL = "/static/"

USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
