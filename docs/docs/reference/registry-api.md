# Registry API Reference

The `ConfigRegistry` is an in-memory store that holds the entire configuration schema after Django starts up. It's populated by `@register_config(...)` decorators during autodiscovery and is read-only at runtime.

You rarely need to interact with the registry directly — the `config` accessor handles everything for normal use. But if you're building developer tooling, writing management commands, or creating custom extensions, direct registry access is available.

---

## Importing the registry

```python
from django_sysconfig.registry import registry
```

This is the global singleton `ConfigRegistry` instance used by `django-sysconfig` internally.

---

## `@register_config(app_label)`

The decorator that registers a config class with the global registry. Used in your `sysconfig.py` files.

```python
from django_sysconfig.registry import register_config, Section, Field

@register_config("myapp")
class MyAppConfig:
    class General(Section):
        label = "General"
        site_name = Field(StringFrontendModel, label="Site Name", default="My App")
```

**Arguments:**

| Argument    | Type  | Description                                           |
| ----------- | ----- | ----------------------------------------------------- |
| `app_label` | `str` | The label under which this config is registered. Becomes the first segment of all paths in this config class. |

The decorator runs at import time (when the `sysconfig.py` module is loaded during autodiscovery). It:
1. Introspects the decorated class for `Section` subclasses and their `Field` attributes.
2. Registers the resolved schema with `registry`.
3. Creates `ConfigValue` database rows for all fields that have a `default` (via `get_or_create`).

---

## `Section`

Base class for section definitions. Subclass it inside your config class to define a section.

```python
from django_sysconfig.registry import Section

class General(Section):
    label = "General Settings"
    sort_order = 10
```

**Class attributes:**

| Attribute    | Type  | Default | Description                                           |
| ------------ | ----- | ------- | ----------------------------------------------------- |
| `label`      | `str` | `""`    | Heading shown in the admin UI                         |
| `sort_order` | `int` | `0`     | Display order among sections (lower = first)          |

---

## `Field(...)`

Defines a single configurable value. Assign `Field(...)` instances as class attributes on a `Section` subclass.

```python
from django_sysconfig.registry import Field

site_name = Field(
    StringFrontendModel,
    label="Site Name",
    comment="Shown in the browser tab.",
    default="My App",
    sort_order=10,
    validators=[NotEmptyValidator()],
    on_save=my_callback,
)
```

**Arguments:**

| Parameter        | Type                      | Required | Description                                                 |
| ---------------- | ------------------------- | -------- | ----------------------------------------------------------- |
| `frontend_model` | `type[BaseFrontendModel]` | Yes      | The field type class                                        |
| `label`          | `str`                     | No       | Human-readable label (shown in the admin UI)                |
| `comment`        | `str`                     | No       | Help text; HTML is allowed                                  |
| `default`        | `Any`                     | No       | Value used when no DB record exists                         |
| `sort_order`     | `int`                     | No       | Display order within the section (lower = first)            |
| `validators`     | `list[BaseValidator]`     | No       | Validators run before saving                                |
| `on_save`        | `Callable`                | No       | Callback fired after a successful write                     |
| `**kwargs`       | —                         | No       | Passed through to the `frontend_model` (e.g. `choices`, `step`) |

---

## Registry introspection

These methods are available on the `registry` singleton for tooling and introspection:

### `registry.get_apps()`

Returns a list of all registered app labels.

```python
from django_sysconfig.registry import registry

registry.get_apps()
# ["billing", "myapp", "notifications"]
```

---

### `registry.get_sections(app_label)`

Returns the sections registered for a given app, as an ordered list.

```python
registry.get_sections("billing")
# [<Section: general>, <Section: pricing>]
```

---

### `registry.get_fields(app_label, section_name)`

Returns the fields registered for a given section.

```python
registry.get_fields("billing", "pricing")
# [<Field: tax_rate>, <Field: free_tier_limit>, <Field: trial_days>]
```

---

### `registry.get_field(path)`

Returns the `Field` definition for a given dot-notation path.

```python
field = registry.get_field("billing.pricing.tax_rate")
field.label    # "Tax Rate"
field.default  # Decimal("0.20")
```

**Raises:** `InvalidPathError`, `AppNotFoundError`, `FieldNotFoundError`.

---

## Writing a management command that inspects the schema

```python
from django.core.management.base import BaseCommand
from django_sysconfig.registry import registry

class Command(BaseCommand):
    help = "List all registered configuration fields"

    def handle(self, *args, **kwargs):
        for app_label in registry.get_apps():
            self.stdout.write(f"\n[{app_label}]")
            for section in registry.get_sections(app_label):
                self.stdout.write(f"  {section.label}")
                for field in registry.get_fields(app_label, section.__name__.lower()):
                    self.stdout.write(f"    {field.label} (default: {field.default!r})")
```
