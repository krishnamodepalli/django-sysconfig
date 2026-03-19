# django-sysconfig

**A Magento-style system configuration app for Django.**

Define typed, structured configuration fields in code. Store their values in the database. Let your team manage everything through a clean admin UI — without ever touching `settings.py`.

<!-- SCREENSHOT: Hero image of the admin UI config list view -->
<!-- GIF: Short clip showing editing a config value in the admin UI and the change taking effect live -->

## Why django-sysconfig?

Most Django projects eventually hit the same wall: some settings need to change at runtime, without a redeploy. Environment variables don't cut it. A freeform key-value table in the database feels like a hack. And custom admin pages take time to build.

`django-sysconfig` gives you a better answer. Your configuration *schema* — the fields, their types, their defaults, their validation rules — lives in code, right next to the app that owns it. The *values* live in the database, editable through a built-in staff UI. Your application code reads values with a single, typed accessor call.

It's the configuration workflow that Magento figured out years ago, brought to Django.

## What you get out of the box

- **Typed fields** — string, integer, decimal, boolean, select, textarea, and encrypted secret
- **Code-driven schema** — your config structure lives in `sysconfig.py` files; only values go in the database
- **Dot-notation accessor** — `config.get("myapp.general.site_name")` returns the right Python type, automatically
- **Built-in caching** — values are cached via Django's cache framework and invalidated on every write
- **Encryption at rest** — secret fields use Fernet symmetric encryption, keyed from your `SECRET_KEY`
- **20 built-in validators** — email, URL, IP, hostname, range, regex, slug, JSON, port, and more
- **Auto-discovery** — drop a `sysconfig.py` in any installed app and it's picked up on startup
- **Admin UI** — staff-only views for browsing and editing configuration, per app and section
- **`on_save` callbacks** — react to value changes with custom logic

## A quick taste

Define your config schema in `myapp/sysconfig.py`:

```python
from django_sysconfig.registry import register_config, Section, Field
from django_sysconfig.frontend_models import StringFrontendModel, BooleanFrontendModel
from django_sysconfig.validators import NotEmptyValidator

@register_config("myapp")
class MyAppConfig:
    class General(Section):         # becomes `general` in the database reference
        label = "General Settings"

        site_name = Field(
            StringFrontendModel,
            label="Site Name",
            default="My App",
            validators=[NotEmptyValidator()],
        )

        maintenance_mode = Field(
            BooleanFrontendModel,
            label="Maintenance Mode",
            default=False,
        )

    class AdminUser(Section):       # becomes `admin_user`
        label = "Admin User Settings"

        allow_beta_features_access = Field(
            BooleanFrontendModel,
            label="Allow Beta Features Access",
            default=False,
        )
```

Read values anywhere in your project:

```python
from django_sysconfig.accessor import config

name = config.get("myapp.general.site_name")       # "My App"
down = config.get("myapp.general.maintenance_mode") # False
beta_access = config.get("myapp.admin_user.allow_beta_features_access") # False
```

That's it. No migrations to write, no admin classes to register, no serialization to handle yourself.

## Get started

New here? Head to the [Quick Start](/quickstart) to have `django-sysconfig` running in under five minutes.

Want the full picture first? Read the [Introduction](/introduction) to understand the design philosophy and how everything fits together.

## Requirements

| Dependency     | Minimum version |
| -------------- | --------------- |
| Python         | 3.11            |
| Django         | 4.2             |
| `cryptography` | 41.0            |

## Installation

```bash
pip install django-sysconfig
```

```python
# settings.py
INSTALLED_APPS = [
    ...
    "django_sysconfig",
]
```

```python
# project/urls.py
urlpatterns = [
    # Must come BEFORE the default admin path
    path("admin/config/", include("django_sysconfig.urls")),
    path("admin/", admin.site.urls),
]
```

```bash
python manage.py migrate
```
