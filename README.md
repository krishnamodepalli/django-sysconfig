# django-sysconfig

A Magento-style system configuration app for Django. Define typed configuration fields in code, store values in the database, and manage them via a built-in admin UI.

## Features

- **Typed fields** — string, integer, decimal, boolean, select, textarea, and secret (encrypted) field types
- **Code-driven definitions** — configuration schema lives in `sysconfig.py` files, values live in the database
- **Admin UI** — built-in views for managing configuration per-app, per-section
- **Dot-notation accessor** — `config.get('myapp.general.some_setting')`
- **Caching** — uses Django's cache framework; invalidated automatically on save
- **Encryption** — secret fields are encrypted at rest using Fernet (AES-128-CBC + HMAC) with a key derived from `SECRET_KEY`
- **Validators** — `Required`, `NotEmpty`, `Email`, `Range`, `Choice`, and more
- **Auto-discovery** — `sysconfig.py` files are discovered automatically on Django startup

## Installation

```bash
pip install django-sysconfig
```

Add to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...
    "django_sysconfig",
]
```

Include the URLs (optional, for the admin UI):

```python
# urls.py
from django.urls import include, path

urlpatterns = [
    ...
    path("admin/config/", include("django_sysconfig.urls")),
]
```

Run migrations:

```bash
python manage.py migrate
```

## Defining Configuration

Create a `sysconfig.py` in any of your Django apps:

```python
# myapp/sysconfig.py
from django_sysconfig.registry import register_config, Section, Field
from django_sysconfig.frontend_models import StringFrontendModel, IntegerFrontendModel
from django_sysconfig.validators import Required, RangeValidator

@register_config("myapp")
class MyAppConfig:
    class General(Section):
        label = "General Settings"
        sort_order = 10

        site_name = Field(
            StringFrontendModel,
            label="Site Name",
            comment="The public name of the site.",
            default="My App",
            validators=[Required()],
        )

        max_items = Field(
            IntegerFrontendModel,
            label="Max Items Per User",
            default=100,
            validators=[RangeValidator(min_value=1, max_value=10000)],
        )
```

## Reading and Writing Values

```python
from django_sysconfig.accessor import config

# Get a value (auto-cast to the correct Python type)
site_name = config.get("myapp.general.site_name")   # str
max_items = config.get("myapp.general.max_items")   # int

# Get with fallback default (if field not registered)
value = config.get("myapp.general.unknown", default="fallback")

# Set a value
config.set("myapp.general.max_items", 200)

# Set multiple values at once
config.set_many({
    "myapp.general.site_name": "New Name",
    "myapp.general.max_items": 50,
})

# Get all values for an app
all_config = config.all("myapp")
# {"general": {"site_name": "New Name", "max_items": 50}}

# Get all values for a section
general = config.section("myapp.general")
# {"site_name": "New Name", "max_items": 50}
```

## Available Field Types

| Frontend Model | Python type | Description |
|---|---|---|
| `StringFrontendModel` | `str` | Single-line text input |
| `IntegerFrontendModel` | `int` | Integer input |
| `DecimalFrontendModel` | `Decimal` | Decimal number input |
| `BooleanFrontendModel` | `bool` | Checkbox |
| `TextAreaFrontendModel` | `str` | Multi-line text area |
| `SelectFrontendModel` | `str` | Dropdown (requires `choices` kwarg) |
| `SecretFrontendModel` | `str` | Encrypted text input |

## Available Validators

- `Required` / `NotEmptyValidator` — field must have a non-empty value
- `EmailValidator` — value must be a valid email address
- `RangeValidator(min_value, max_value)` — numeric range check
- `ChoiceValidator(choices)` — value must be one of the given choices
- `RegexValidator(pattern)` — value must match a regex

## on_save Callback

```python
def clear_cache(path, new_value, old_value):
    # called after the value is saved to the database
    pass

some_field = Field(
    StringFrontendModel,
    label="Some Field",
    default="",
    on_save=clear_cache,
)
```

## License

MIT
