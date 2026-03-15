# Exceptions Reference

All `django-sysconfig` exceptions inherit from `ConfigError`, so you can catch them at any granularity you need.

```python
from django_sysconfig.exceptions import (
    ConfigError,
    InvalidPathError,
    AppNotFoundError,
    FieldNotFoundError,
    ConfigValueError,
)
```

---

## Exception hierarchy

```
ConfigError
├── InvalidPathError
├── AppNotFoundError
├── FieldNotFoundError
└── ConfigValueError
```

---

## `ConfigError`

**Base class** for all `django-sysconfig` exceptions. Catch this to handle any config-related exception in one place.

```python
from django_sysconfig.exceptions import ConfigError

try:
    value = config.get("some.path.here")
except ConfigError as e:
    # Something went wrong — path invalid, app not found, field not found, etc.
    value = "fallback"
```

---

## `InvalidPathError`

Raised when the path passed to any accessor method doesn't have exactly three dot-separated parts.

**Triggers:**
- `config.get("myapp.site_name")` — only two parts
- `config.get("myapp.general.site.name")` — four parts
- `config.get("")` — empty string
- `config.get("myapp")` — one part

```python
from django_sysconfig.exceptions import InvalidPathError

try:
    config.get("myapp.general")  # missing field segment
except InvalidPathError as e:
    print(e)  # "Path must have exactly three dot-separated parts: 'myapp.general'"
```

---

## `AppNotFoundError`

Raised when the first segment of the path (the app label) has no registered configuration. This usually means there's no `sysconfig.py` file in that app, or the file doesn't use `@register_config(...)`, or the app isn't in `INSTALLED_APPS`.

**Triggers:**
- `config.get("nonexistent_app.general.field")`
- `config.all("nonexistent_app")`

```python
from django_sysconfig.exceptions import AppNotFoundError

try:
    config.get("typo_in_appname.general.site_name")
except AppNotFoundError as e:
    print(e)  # "No config registered for app: 'typo_in_appname'"
```

**Common cause:** You defined a `sysconfig.py` but the app isn't in `INSTALLED_APPS`, so it was never autodiscovered.

---

## `FieldNotFoundError`

Raised when the app is registered but the section or field doesn't exist in the schema.

**Triggers:**
- `config.get("myapp.general.nonexistent_field")` — field doesn't exist
- `config.get("myapp.nonexistent_section.field")` — section doesn't exist

```python
from django_sysconfig.exceptions import FieldNotFoundError

try:
    config.get("myapp.general.old_field_name")  # field was renamed
except FieldNotFoundError as e:
    print(e)  # "Field not found: 'myapp.general.old_field_name'"
```

**Common cause:** A field was renamed or removed from the schema, but the old path is still referenced somewhere in the codebase.

---

## `ConfigValueError`

Raised when a value can't be saved — either because it fails validation, or because it can't be serialized for the given field type.

**Triggers:**
- `config.set("myapp.general.max_items", -1)` — if a `PositiveValidator` is on the field
- `config.set("notifications.email.sender", "not-an-email")` — if `EmailValidator` is on the field
- `config.set("myapp.general.max_items", "not-a-number")` — wrong type for `IntegerFrontendModel`

```python
from django_sysconfig.exceptions import ConfigValueError

try:
    config.set("myapp.general.max_items", -5)
except ConfigValueError as e:
    print(e)  # "Max Items Per User: Value must be greater than zero."
```

The error message includes the field label (if available) and the specific validation failure, making it suitable to display directly to users.

---

## Catching exceptions in practice

### In views — user-facing error handling

```python
from django_sysconfig.exceptions import ConfigError

def my_view(request):
    try:
        limit = config.get("myapp.general.item_limit")
    except ConfigError:
        limit = 10  # safe fallback
    ...
```

### In management commands — fail loudly

```python
from django_sysconfig.exceptions import ConfigValueError

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        try:
            config.set("billing.general.live_mode", True)
        except ConfigValueError as e:
            raise CommandError(f"Failed to update config: {e}")
```

### In tests — assert specific exceptions

```python
import pytest
from django_sysconfig.exceptions import FieldNotFoundError

def test_get_nonexistent_field():
    with pytest.raises(FieldNotFoundError):
        config.get("myapp.general.this_does_not_exist")
```
