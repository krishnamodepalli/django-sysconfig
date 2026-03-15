# Quick Start

Get `django-sysconfig` running in your project in under five minutes.

---

## 1. Install

```bash
pip install django-sysconfig
```

---

## 2. Add to INSTALLED_APPS

```python
# settings.py
INSTALLED_APPS = [
    ...
    "django_sysconfig",
]
```

---

## 3. Run migrations

`django-sysconfig` needs one database table to store configuration values.

```bash
python manage.py migrate
```

---

## 4. Wire up the admin UI (optional but recommended)

```python
# urls.py
from django.urls import include, path
from django.contrib import admin

urlpatterns = [
    # Must come BEFORE the default admin path
    path("admin/config/", include("django_sysconfig.urls")),
    path("admin/", admin.site.urls),
]
```

> **Why before `admin/`?**
> Django matches URL patterns in order. Placing the config URL first ensures `/admin/config/` is handled by `django-sysconfig` rather than being caught by the admin's catch-all.

---

## 5. Define your first config schema

Create a `sysconfig.py` file inside any installed Django app:

```python
# myapp/sysconfig.py
from django_sysconfig.registry import register_config, Section, Field
from django_sysconfig.frontend_models import (
    StringFrontendModel,
    IntegerFrontendModel,
    BooleanFrontendModel,
)
from django_sysconfig.validators import NotEmptyValidator, RangeValidator

@register_config("myapp")
class MyAppConfig:
    class General(Section):
        label = "General Settings"
        sort_order = 10

        site_name = Field(
            StringFrontendModel,
            label="Site Name",
            comment="The public-facing name of your site.",
            default="My App",
            validators=[NotEmptyValidator()],
        )

        max_items = Field(
            IntegerFrontendModel,
            label="Max Items Per User",
            default=100,
            validators=[RangeValidator(min_value=1, max_value=10_000)],
        )

        maintenance_mode = Field(
            BooleanFrontendModel,
            label="Maintenance Mode",
            default=False,
        )
```

Django's auto-discovery picks this file up on startup — no further registration needed.

---

## 6. Read values in your application code

```python
from django_sysconfig.accessor import config

site_name   = config.get("myapp.general.site_name")        # str  → "My App"
max_items   = config.get("myapp.general.max_items")        # int  → 100
maintenance = config.get("myapp.general.maintenance_mode") # bool → False
```

Values are **typed** — `max_items` is an `int`, not the string `"100"`. Caching is handled automatically.

---

## 7. Edit values in the admin UI

Start your dev server, log in with a staff account, and visit `/admin/config/`. You'll see your app listed with all its sections and fields.

<!-- SCREENSHOT: Admin config list showing "myapp" with "General Settings" section -->
<!-- GIF: Editing the "Site Name" field and saving -->

---

## You're done!

From here, explore:

- [Getting Started](../getting-started) — a real-world walkthrough with multiple apps and sections
- [Field Types](../reference/field-types) — all seven field types with examples
- [Validators](../reference/validators) — all 20 built-in validators
- [Accessor API](../reference/accessor-api) — every method on the `config` object
