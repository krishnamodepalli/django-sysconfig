# Reading and Writing Values

The `config` accessor is the single object your application code uses to interact with configuration. Import it once and use it anywhere.

```python
from django_sysconfig.accessor import config
```

All methods accept a path in one of two forms:

- **String path** — dot notation with exactly three parts: `"app_label.section.field"`
- **Field reference** — a `Field` instance obtained directly from your config class (see [Typed Field API](#typed-field-api))

## Reading values

### `config.get(path, default=...)`

This **lazy loads** the value.

Returns the value for the given path. If the field has no saved value in the database, the field's defined default is returned. If the field has no default either, `default` is returned.

Invalid paths and unknown apps or fields always raise an exception — `default` does not suppress them.

```python
# Returns the saved value, or the field's default if none is saved
site_name = config.get("myapp.general.site_name")   # str
max_items = config.get("myapp.general.max_items")   # int
live_mode = config.get("billing.general.live_mode") # bool
tax_rate  = config.get("billing.pricing.tax_rate")  # Decimal

# Fallback for a registered field that has no saved value and no field default
value = config.get("myapp.general.some_field", default=42)

# Field reference — fully typed, IDE-navigable
from myapp.sysconfig import MyAppConfig
max_items = config.get(MyAppConfig.General.max_items)
```

Values are **typed** — you get the correct Python type back without any casting. An `IntegerFrontendModel` field always returns an `int`. A `BooleanFrontendModel` field always returns a `bool`. A `DecimalFrontendModel` field always returns a `Decimal`.

Reads are served from the cache when available, so repeated calls in the same request are fast.

### `config.all(app)`

This **eager loads** all the sections and fields in the specified app. Returns all configuration values for an entire app, as a nested dictionary keyed by section, then field name.

Accepts either an app label string or an `AppConfigDefinition` instance.

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

### `config.section(section)`

This **eager loads** all the fields in the specified section. Returns all configuration values for a single section, as a flat dictionary keyed by field name.

Accepts either a two-part string path (`"app.section"`) or a `Section` subclass directly.

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

Returns `True` if the path is registered in the schema (i.e., a field with that path exists in code). Does not check the database. Accepts a string path or a `Field` instance.

```python
config.exists("myapp.general.site_name")          # True
config.exists("myapp.general.no_such_key")        # False
config.exists(MyAppConfig.General.site_name)      # True
```

### `config.is_set(path)`

Returns `True` if the field has a value other than empty string or `NULL` in the database. Accepts a string path or a `Field` instance.

```python
config.is_set("myapp.general.site_name")    # False if a default is not set. True if set.
# ... after saving a value via the admin UI or config.set(...) ...
config.is_set("myapp.general.site_name")    # True
config.is_set(MyAppConfig.General.site_name) # same, via Field reference
```

This is useful for "onboarding" flows where you want to detect whether a required configuration step has been completed.

## Writing values

### `config.set(path, value)`

Saves a single value to the database, updates the cache, and fires the `on_save` callback if one is defined. Accepts a string path or a `Field` instance.

```python
config.set("myapp.general.site_name", "Acme Corp")
config.set("myapp.general.max_items", 500)
config.set("billing.general.live_mode", True)
config.set("billing.pricing.tax_rate", Decimal("0.15"))

# Field reference
config.set(MyAppConfig.General.max_items, 500)
```

The value is validated against the field's validators before being saved. If validation fails, a `ConfigValidationError` is raised and nothing is written.

### `config.set_many(values)`

Saves multiple values atomically in a single database transaction. All cache invalidations happen after the transaction commits. All `on_save` callbacks fire after the write was successful, one per changed field.

Keys can be string paths or `Field` instances — they can be mixed in the same call.

```python
config.set_many({
    "myapp.general.site_name": "Acme Corp",
    "myapp.general.max_items": 500,
    "billing.pricing.tax_rate": Decimal("0.15"),
})

# Mixed — string and Field keys together
config.set_many({
    MyAppConfig.General.site_name: "Acme Corp",
    "billing.pricing.tax_rate": Decimal("0.15"),
})
```

If any value fails validation, the entire transaction is rolled back and no values are saved.

:::tip
You can also read and write values directly from the terminal using the
[`config` management command](/cli/management-command).
:::

## Typed Field API

Every accessor method accepts a `Field` instance in place of a string path. This lets you reference config fields through your config class directly, giving you autocomplete, go-to-definition, and safe renames in any IDE.

### Getting a Field reference

Import your config class and access the field as a class attribute:

```python
from myapp.sysconfig import MyAppConfig

field = MyAppConfig.General.max_items  # Field instance
```

After registration, every `Field` carries these runtime attributes set by the registry:

| Attribute       | Example value                  | Description                        |
| --------------- | ------------------------------ | ---------------------------------- |
| `full_path`     | `"myapp.general.max_items"`    | Full three-part path               |
| `_app_label`    | `"myapp"`                      | App label                          |
| `_section_name` | `"general"`                    | Section key (snake_case)           |
| `name`          | `"max_items"`                  | Field name                         |
| `path`          | `"general.max_items"`          | Two-part path used in the database |

### Using Field references

```python
from myapp.sysconfig import MyAppConfig

# All methods accept Field in place of a string path
value    = config.get(MyAppConfig.General.max_items)
config.set(MyAppConfig.General.max_items, 500)
is_set   = config.is_set(MyAppConfig.General.max_items)
exists   = config.exists(MyAppConfig.General.max_items)

# set_many accepts mixed keys
config.set_many({
    MyAppConfig.General.max_items: 500,
    MyAppConfig.General.site_name: "Acme Corp",
})
```

String paths and Field references share the same cache key, so a read via one form is immediately visible to the other with no extra DB round-trip.

### String path vs Field reference

| | String path | Field reference |
|---|---|---|
| **IDE support** | None | Autocomplete, go-to-definition, safe rename |
| **Typo safety** | Fails at runtime | Fails at import time |
| **Cold cache** (DB hit) | ~175 µs | ~175 µs |
| **Warm cache** (cache hit) | ~6 µs | ~5 µs |

Performance is negligible in both cases — choose Field references for the IDE and type-safety benefits, not for speed.

## Exceptions

All exceptions inherit from `ConfigError`, so you can catch the base class if you want to handle any config-related error in one place.

| Exception          | Raised when                                                     |
| ------------------ | --------------------------------------------------------------- |
| `ConfigError`      | Base class for all config exceptions                            |
| `InvalidPathError` | The path doesn't have exactly three dot-separated parts         |
| `AppNotFoundError` | No configuration is registered for the given app label          |
| `FieldNotFoundError` | The section or field doesn't exist in the registered schema   |
| `ConfigValidationError` | A value fails one or more field validators                  |
| `ConfigValueError` | A value can't be serialized for the given field type                |

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
