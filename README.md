# django-sysconfig

A **Magento-style system configuration app for Django**. Define typed, structured configuration fields in code, store their values in the database, and manage everything through a built-in admin UI — without touching `settings.py`.

---

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Defining Configuration](#defining-configuration)
  - [Field options](#field-options)
  - [Section options](#section-options)
- [Field Types](#field-types)
- [Reading and Writing Values](#reading-and-writing-values)
- [Validators](#validators)
- [on\_save Callback](#on_save-callback)
- [Encryption](#encryption)
- [Admin UI](#admin-ui)
- [How It Works](#how-it-works)
- [License](#license)

---

## Features

- **Typed fields** — string, integer, decimal, boolean, select, textarea, and encrypted secret types
- **Code-driven schema** — configuration structure lives in `sysconfig.py` files; only values are stored in the database
- **Dot-notation accessor** — `config.get("myapp.general.site_name")` returns the correct Python type automatically
- **Caching** — values are cached via Django's cache framework and invalidated on every write
- **Encryption at rest** — secret fields use Fernet (AES-128-CBC + HMAC), key derived from `SECRET_KEY`
- **20 built-in validators** — email, URL, IP, hostname, range, regex, slug, JSON, port, and more
- **Auto-discovery** — `sysconfig.py` files are found and loaded automatically on Django startup
- **Admin UI** — built-in staff-only views for browsing and editing configuration per app and section
- **on\_save callbacks** — react to value changes with custom logic (cache busting, webhooks, etc.)

---

## Requirements

- Python ≥ 3.11
- Django ≥ 4.2
- `cryptography` ≥ 41.0

---

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

Run migrations:

```bash
python manage.py migrate
```

Optionally, wire up the admin UI:

```python
# urls.py
from django.urls import include, path

urlpatterns = [
    ...
    path("admin/config/", include("django_sysconfig.urls")),
]
```

---

## Quick Start

**1. Define your config schema** in `myapp/sysconfig.py`:

```python
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
            comment="The public-facing name of the site.",
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

**2. Read values anywhere in your project:**

```python
from django_sysconfig.accessor import config

site_name = config.get("myapp.general.site_name")       # "My App"
max_items = config.get("myapp.general.max_items")       # 100
maintenance = config.get("myapp.general.maintenance_mode")  # False
```

---

## Defining Configuration

Create a `sysconfig.py` file inside any installed Django app. Decorate a class with `@register_config("<app_label>")` and nest `Section` subclasses containing `Field` instances.

```python
from django_sysconfig.registry import register_config, Section, Field
from django_sysconfig.frontend_models import StringFrontendModel, SelectFrontendModel
from django_sysconfig.validators import NotEmptyValidator, ChoiceValidator

@register_config("notifications")
class NotificationsConfig:
    class Email(Section):
        label = "Email Settings"
        sort_order = 10

        sender_address = Field(
            StringFrontendModel,
            label="Sender Address",
            default="no-reply@example.com",
            validators=[NotEmptyValidator()],
        )

        format = Field(
            SelectFrontendModel,
            label="Email Format",
            default="html",
            choices=[("html", "HTML"), ("text", "Plain Text")],
            validators=[ChoiceValidator(["html", "text"])],
        )

    class Sms(Section):
        label = "SMS Settings"
        sort_order = 20

        enabled = Field(
            BooleanFrontendModel,
            label="Enable SMS",
            default=False,
        )
```

### Field options

| Parameter | Type | Description |
|---|---|---|
| `frontend_model` | `type[BaseFrontendModel]` | The field type class (required) |
| `label` | `str` | Human-readable label shown in the admin UI |
| `comment` | `str` | Help text shown below the input; HTML is allowed |
| `default` | `Any` | Default value when no DB record exists |
| `sort_order` | `int` | Display order within the section (lower = first) |
| `validators` | `list[BaseValidator]` | Validators run before saving |
| `on_save` | `Callable` | Callback invoked after a value is saved |
| `**kwargs` | | Extra args passed to the frontend model (e.g., `choices`) |

### Section options

| Attribute | Type | Description |
|---|---|---|
| `label` | `str` | Section heading shown in the admin UI |
| `sort_order` | `int` | Display order among sections (lower = first) |

---

## Field Types

| Class | Python type | Description |
|---|---|---|
| `StringFrontendModel` | `str` | Single-line text input |
| `TextareaFrontendModel` | `str` | Multi-line text area |
| `IntegerFrontendModel` | `int` | Integer number input |
| `DecimalFrontendModel` | `Decimal` | Decimal number input (accepts `step` kwarg) |
| `BooleanFrontendModel` | `bool` | Checkbox |
| `SelectFrontendModel` | `str` | Dropdown select (requires `choices` kwarg) |
| `SecretFrontendModel` | `str` | Password input — encrypted at rest (see [Encryption](#encryption)) |

**Select field choices format:**

```python
Field(
    SelectFrontendModel,
    label="Environment",
    default="production",
    choices=[
        ("development", "Development"),
        ("staging", "Staging"),
        ("production", "Production"),
    ],
)
```

**Decimal field with custom step:**

```python
Field(
    DecimalFrontendModel,
    label="Tax Rate",
    default=Decimal("0.20"),
    step="0.001",   # passed through to the HTML input
)
```

---

## Reading and Writing Values

All paths use dot notation with exactly three parts: `app_label.section.field`.

```python
from django_sysconfig.accessor import config

# --- Reading ---

# Returns the typed value; falls back to the field's default if not set in DB
config.get("myapp.general.site_name")           # str
config.get("myapp.general.max_items")           # int
config.get("myapp.general.maintenance_mode")    # bool

# Supply a fallback for unknown/unregistered paths (no exception raised)
config.get("myapp.general.unknown", default=42)

# All values for an entire app  →  {section: {field: value, ...}, ...}
config.all("myapp")

# All values for one section  →  {field: value, ...}
config.section("myapp.general")

# Check if a path is registered in code
config.exists("myapp.general.site_name")        # True / False

# Check if a value has been explicitly saved to the database
config.is_set("myapp.general.site_name")        # True / False

# --- Writing ---

config.set("myapp.general.site_name", "Acme Corp")
config.set("myapp.general.max_items", 500)
config.set("myapp.general.maintenance_mode", True)

# Save multiple values atomically
config.set_many({
    "myapp.general.site_name": "Acme Corp",
    "myapp.general.max_items": 500,
})
```

### Exceptions

| Exception | Raised when |
|---|---|
| `InvalidPathError` | Path does not have exactly three dot-separated parts |
| `AppNotFoundError` | No config is registered for the given app label |
| `FieldNotFoundError` | The field does not exist in the registered schema |
| `ConfigValueError` | A value cannot be serialized for the given field type |

All inherit from `ConfigError`.

---

## Validators

Import validators from `django_sysconfig.validators` and pass them as a list to the `validators` parameter on a `Field`.

```python
from django_sysconfig.validators import NotEmptyValidator, EmailValidator, RangeValidator

Field(StringFrontendModel, validators=[NotEmptyValidator(), EmailValidator()])
```

All validators accept an optional `message` argument to override the default error message.

### Presence

| Validator | Description |
|---|---|
| `NotEmptyValidator()` | Value must not be `None`, empty string, empty list, or empty dict. Alias: `Required` |
| `NotBlankValidator()` | String value must not be whitespace-only (`None` is allowed) |

### String length

| Validator | Description |
|---|---|
| `MinLengthValidator(min_length)` | String must be at least `min_length` characters |
| `MaxLengthValidator(max_length)` | String must be at most `max_length` characters |

### Pattern

| Validator | Description |
|---|---|
| `RegexValidator(pattern, flags=0, inverse=False)` | Value must match (or not match, if `inverse=True`) the given regex pattern |
| `SlugValidator()` | Value must contain only letters, digits, hyphens, and underscores |
| `JsonValidator()` | Value must be a valid JSON string |

### Numeric

| Validator | Description |
|---|---|
| `RangeValidator(min_value=None, max_value=None)` | Number must fall within the given range (both bounds inclusive, either optional) |
| `PositiveValidator()` | Number must be greater than zero |
| `NonNegativeValidator()` | Number must be zero or greater |
| `PortValidator()` | Integer must be a valid port number (1–65535) |

### Network / format

| Validator | Description |
|---|---|
| `EmailValidator()` | Must be a valid email address |
| `UrlValidator(schemes=None)` | Must be a valid URL; `schemes` defaults to `["http", "https", "ftp"]` |
| `IPv4Validator()` | Must be a valid IPv4 address |
| `IPv6Validator()` | Must be a valid IPv6 address |
| `IPAddressValidator(version=None)` | Must be a valid IP address; `version` can be `4`, `6`, or `None` (both) |
| `HostnameValidator()` | Must be a valid RFC 1123 hostname |
| `DomainValidator()` | Must be a valid domain name (max 253 characters) |

### Other

| Validator | Description |
|---|---|
| `ChoiceValidator(choices)` | Value must be one of the items in `choices` |
| `PathValidator(must_be_absolute=False)` | Value must look like a valid file path; optionally require an absolute path |

### Running validators manually

```python
from django_sysconfig.validators import validate_value, NotEmptyValidator, EmailValidator

errors = validate_value(
    "not-an-email",
    [NotEmptyValidator(), EmailValidator()],
    field_label="Sender Address",
)
# ["Sender Address: Enter a valid email address."]
```

---

## on\_save Callback

Attach a callback to any field to react when its value changes. The callback receives the full dot-notation path, the new value, and the old value.

```python
def on_maintenance_mode_change(path: str, new_value: bool, old_value: bool) -> None:
    if new_value and not old_value:
        # Notify ops team, clear caches, etc.
        pass

maintenance_mode = Field(
    BooleanFrontendModel,
    label="Maintenance Mode",
    default=False,
    on_save=on_maintenance_mode_change,
)
```

The callback is fired **after** the value has been successfully written to the database and the cache has been updated.

---

## Encryption

Fields using `SecretFrontendModel` are **encrypted at rest**. Values are encrypted with [Fernet](https://cryptography.io/en/latest/fernet/) (AES-128-CBC + HMAC-SHA256) using a key derived from Django's `SECRET_KEY` via SHA-256.

- The encrypted value is stored as a Fernet token in the database.
- The admin UI always masks the value — it is never displayed.
- Values are decrypted transparently when read via `config.get(...)`.
- Rotating `SECRET_KEY` will make existing encrypted values unreadable; re-save them after rotation.

```python
from django_sysconfig.frontend_models import SecretFrontendModel

api_key = Field(
    SecretFrontendModel,
    label="API Key",
    comment="Your third-party API key. Stored encrypted.",
)
```

---

## Admin UI

The admin UI is a pair of staff-only class-based views:

| URL | View | Description |
|---|---|---|
| `/admin/config/` | `ConfigAppListView` | Lists all apps that have registered configuration |
| `/admin/config/<app_label>/` | `ConfigAppDetailView` | Renders and saves all fields for an app |

The Django admin index page is extended with a banner linking to the config UI.

Both views require the user to be a **staff member** (`is_staff=True`).

---

## How It Works

1. **Discovery** — On startup, `AppConfig.ready()` calls `autodiscover_modules("sysconfig")`, which imports `sysconfig.py` from every installed app.
2. **Registration** — `@register_config("app_label")` registers the class with the global `ConfigRegistry`. For every field that has a default, a `ConfigValue` database row is created via `get_or_create` (existing values are never overwritten).
3. **Reading** — `config.get("app.section.field")` checks the cache first. On a miss, it queries the database. The raw string is deserialized by the field's `FrontendModel` into the correct Python type (int, bool, Decimal, etc.).
4. **Writing** — `config.set(...)` serializes the value, writes it to the database, invalidates the cache entry, and then calls the `on_save` callback if one is defined.
5. **Caching** — The cache layer wraps Django's standard cache framework. Entries have no expiry and are invalidated explicitly on every write.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to set up your local development environment, run tests, and submit a pull request.

---

## License

MIT
