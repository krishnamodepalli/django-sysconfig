---
title: Installation
description: Add django-sysconfig to your Django project.
---

# Installation

## Requirements

- Python **3.11** or higher
- Django **4.2** or higher
- A supported database: PostgreSQL, MySQL, or SQLite

## Install

```bash
pip install django-sysconfig
```

## Add to INSTALLED_APPS

```python
# settings.py
INSTALLED_APPS = [
    "django_sysconfig",  # ← must be first
    "django.contrib.admin",
    ...
]
```

:::warning Why must it be first?
Django loads admin templates from apps in `INSTALLED_APPS` order. `django-sysconfig` overrides the admin index template to add the **System Configuration** button. If it's not listed before `django.contrib.admin`, the standard admin templates load first and the button won't appear.
:::

## Wire up the URLs

Add the config UI routes to your root `urls.py`. The config path **must come before** `path("admin/", ...)`:

```python
# urls.py
from django.urls import path, include
from django.contrib import admin

urlpatterns = [
    path("admin/config/", include("django_sysconfig.urls")),  # ← before admin/
    path("admin/", admin.site.urls),
]
```

Django matches URL patterns in order. Placing the config URL first ensures `/admin/config/` is routed correctly rather than being caught by the admin's catch-all.

## Run migrations

`django-sysconfig` needs one database table to store configuration values:

```bash
python manage.py migrate
```

## Verify

Start your dev server and visit `/admin/config/`:

```bash
python manage.py runserver
```

You should see the django-sysconfig App List view — empty for now, since no apps have registered any config yet.

---

Ready to define your first config schema? Head to [Quick Start](/quickstart).
