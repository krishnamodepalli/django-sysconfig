---
title: Installation
description: Get django-sysconfig running in under five minutes.
---

# Installation

Get django-sysconfig running in under five minutes.

:::tip
We recommend using a virtual environment to isolate your project dependencies.
:::

## Requirements

- Python **3.11** or higher
- Django **4.2** or higher
- A supported database: PostgreSQL, MySQL, or SQLite

## Install via pip

```bash
pip install django-sysconfig
```

## Add to INSTALLED_APPS

```python
# settings.py
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "django_sysconfig",  # ← Add this
]
```

## Configure URLs

Include the `django-sysconfig` URLs in your root `urls.py` file. It's recommended to mount them under `admin/config/`.

```python
# urls.py
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("admin/config/", include("django_sysconfig.urls")), # ← Add this
]
```

## Run Migrations

```bash
python manage.py migrate
```

## Create a Superuser

To access the config UI, you'll need to be a staff member.

```bash
python manage.py createsuperuser
```

## Verify

Start the dev server and open [http://127.0.0.1:8000/admin/config/](http://127.0.0.1:8000/admin/config/):

```bash
python manage.py runserver
```

You should see the django-sysconfig App List view. 🎉

---

Ready to configure your first app? Head over to [Configuration](../configuration/) next.
