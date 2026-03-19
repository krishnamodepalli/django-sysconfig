# Reading and Writing Values

The `config` accessor is the single object your application code uses to interact with configuration. Import it once and use it anywhere.

```python
from django_sysconfig.accessor import config
```

All paths use **dot notation** with exactly three parts: `app_label.section.field`.

## Reading values

### `config.get(path, default=...)`

This **lazy loads** the value.

Returns the value for the given path. If the field has no saved value in the database, the field's defined default is returned. You can also supply a fallback for unregistered paths.

```python
# Returns the saved value, or the field's default if none is saved
site_name = config.get("myapp.general.site_name")   # str
max_items = config.get("myapp.general.max_items")   # int
live_mode = config.get("billing.general.live_mode") # bool
tax_rate  = config.get("billing.pricing.tax_rate")  # Decimal

# Supply a fallback for unknown/unregistered paths (no exception raised)
value = config.get("myapp.general.unknown_field", default=42)
```

Values are **typed** — you get the correct Python type back without any casting. An `IntegerFrontendModel` field always returns an `int`. A `BooleanFrontendModel` field always returns a `bool`. A `DecimalFrontendModel` field always returns a `Decimal`.

Reads are served from the cache when available, so repeated calls in the same request are fast.

### `config.all(app_label)`

This **eager loads** all the sections and fields in the specified app. Returns all configuration values for an entire app, as a nested dictionary keyed by section, then field name.

:::warning
The returned dictionary includes **plaintext (decrypted) values for all secret fields**. Avoid logging, serializing, or exposing this output — treat it with the same care as raw credentials.
:::

```python
billing_config = config.all("billing")
# {
#   "general": {
#     "live_mode": False,
#   },
#   "pricing": {
#     "tax_rate": Decimal("0.20"),
#     "free_tier_limit": 10,
#     "trial_days": 14,
#   }
# }
```

### `config.section(path)`

This **eager loads** all the fields in the specified section path. Returns all configuration values for a single section, as a flat dictionary keyed by field name.

:::warning
The returned dictionary includes **plaintext (decrypted) values for all secret fields**. Avoid logging, serializing, or exposing this output — treat it with the same care as raw credentials.
:::

```python
pricing = config.section("billing.pricing")
# {
#   "tax_rate": Decimal("0.20"),
#   "free_tier_limit": 10,
#   "trial_days": 14,
# }
```

### `config.exists(path)`

Returns `True` if the path is registered in the schema (i.e., a field with that path exists in code). Does not check the database.

```python
config.exists("myapp.general.site_name")   # True
config.exists("myapp.general.no_such_key") # False
```

### `config.is_set(path)`

Returns `True` if the field has a value explicitly saved in the database — that is, the value has been changed from (or confirmed as) the default at some point.

```python
config.is_set("myapp.general.site_name")    # False on a fresh install
# ... after saving a value via the admin UI or config.set(...) ...
config.is_set("myapp.general.site_name")    # True
```

This is useful for "onboarding" flows where you want to detect whether a required configuration step has been completed.

## Writing values

### `config.set(path, value)`

Saves a single value to the database, invalidates the cache, and fires the `on_save` callback if one is defined.

```python
config.set("myapp.general.site_name", "Acme Corp")
config.set("myapp.general.max_items", 500)
config.set("billing.general.live_mode", True)
config.set("billing.pricing.tax_rate", Decimal("0.15"))
```

The value is validated against the field's validators before being saved. If validation fails, a `ConfigValueError` is raised and nothing is written.

### `config.set_many(values)`

Saves multiple values atomically in a single database transaction. All cache invalidations happen after the transaction commits. All `on_save` callbacks fire after the write was successful, one per changed field.

```python
config.set_many({
    "myapp.general.site_name": "Acme Corp",
    "myapp.general.max_items": 500,
    "billing.pricing.tax_rate": Decimal("0.15"),
})
```

If any value fails validation, the entire transaction is rolled back and no values are saved.

## Exceptions

All exceptions inherit from `ConfigError`, so you can catch the base class if you want to handle any config-related error in one place.

| Exception          | Raised when                                                     |
| ------------------ | --------------------------------------------------------------- |
| `ConfigError`      | Base class for all config exceptions                            |
| `InvalidPathError` | The path doesn't have exactly three dot-separated parts         |
| `AppNotFoundError` | No configuration is registered for the given app label          |
| `FieldNotFoundError` | The section or field doesn't exist in the registered schema   |
| `ConfigValueError` | A value fails validation, or can't be serialized for the field type |

```python
from django_sysconfig.exceptions import ConfigError, FieldNotFoundError

try:
    value = config.get("myapp.general.nonexistent")
except FieldNotFoundError:
    # handle missing field
    value = "fallback"
except ConfigError:
    # handle any other config error
    value = "fallback"
```

## Practical patterns

### Feature flags

```python
# Check a boolean flag before running a code path
if config.get("myapp.features.new_checkout"):
    return new_checkout_flow(request)
else:
    return legacy_checkout_flow(request)
```

### Maintenance mode middleware

```python
class MaintenanceModeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if config.get("myapp.general.maintenance_mode"):
            return HttpResponse("Down for maintenance.", status=503)
        return self.get_response(request)
```

### Reading config in a Django management command

```python
from django.core.management.base import BaseCommand
from django_sysconfig.accessor import config

class Command(BaseCommand):
    help = "Send weekly digest emails"

    def handle(self, *args, **kwargs):
        sender = config.get("notifications.email.sender_address")
        # ...
```

### Using `config.all()` or `config.section()` in a template context processor

```python
def sysconfig_context(request):
    return {"site_config": config.section("myapp.general")}
```

Then in your template:

```html
<title>{{ site_config.site_name }}</title>
```
