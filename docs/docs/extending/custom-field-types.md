# Custom Field Types

The seven built-in field types cover most use cases, but you can create your own by subclassing `BaseFrontendModel`. A custom field type lets you define exactly how a value is serialized to the database, deserialized back to Python, and rendered in the admin UI.

---

## When to write a custom field type

Consider writing a custom field type when:

- You need a Python type that isn't covered by the built-in types (e.g. `datetime`, a custom dataclass, a list of values)
- You want a specialized UI widget in the admin
- You need custom serialization logic (e.g. storing a value as JSON)
- You want to reuse the same serialization + deserialization + UI widget pattern across many fields

---

## The `BaseFrontendModel` interface

```python
from django_sysconfig.frontend_models import BaseFrontendModel

class BaseFrontendModel:
    def serialize(self, value) -> str:
        """Convert a Python value to a string for database storage."""
        raise NotImplementedError

    def deserialize(self, raw: str):
        """Convert a stored string back to the correct Python type."""
        raise NotImplementedError

    def render(self, name: str, value, attrs: dict) -> str:
        """Return an HTML string for the admin UI input widget."""
        raise NotImplementedError
```

You must implement all three methods.

---

## Example: a `DateFrontendModel`

This custom type stores a `datetime.date` value as an ISO 8601 string (`YYYY-MM-DD`) and renders a date picker in the admin.

```python
import datetime
from django_sysconfig.frontend_models import BaseFrontendModel

class DateFrontendModel(BaseFrontendModel):
    def serialize(self, value: datetime.date) -> str:
        if isinstance(value, str):
            return value  # already serialized
        return value.isoformat()  # e.g. "2024-06-01"

    def deserialize(self, raw: str) -> datetime.date:
        if not raw:
            return None
        return datetime.date.fromisoformat(raw)

    def render(self, name: str, value, attrs: dict) -> str:
        # value here is the raw string from the database (or empty string)
        html_value = value if value else ""
        return f'<input type="date" name="{name}" value="{html_value}">'
```

---

## Using your custom field type

Once defined, use it exactly like any built-in type:

```python
import datetime
from myapp.field_types import DateFrontendModel
from django_sysconfig.registry import register_config, Section, Field

@register_config("events")
class EventsConfig:
    class Schedule(Section):
        label = "Schedule"

        launch_date = Field(
            DateFrontendModel,
            label="Launch Date",
            comment="The public launch date for the product.",
            default=datetime.date(2025, 1, 1),
        )
```

```python
from django_sysconfig.accessor import config
import datetime

launch = config.get("events.schedule.launch_date")
# datetime.date(2025, 1, 1)

config.set("events.schedule.launch_date", datetime.date(2025, 6, 15))
```

---

## Example: a `JsonFrontendModel`

For storing arbitrary JSON-serializable data (lists, dicts):

```python
import json
from django_sysconfig.frontend_models import BaseFrontendModel

class JsonFrontendModel(BaseFrontendModel):
    def serialize(self, value) -> str:
        if isinstance(value, str):
            return value  # assume already serialized
        return json.dumps(value)

    def deserialize(self, raw: str):
        if not raw:
            return None
        return json.loads(raw)

    def render(self, name: str, value, attrs: dict) -> str:
        # Pretty-print JSON in the textarea for readability
        if value:
            try:
                pretty = json.dumps(json.loads(value), indent=2)
            except (ValueError, TypeError):
                pretty = value
        else:
            pretty = ""
        return f'<textarea name="{name}" rows="10" cols="60">{pretty}</textarea>'
```

Usage:

```python
allowed_origins = Field(
    JsonFrontendModel,
    label="Allowed Origins",
    comment='JSON list, e.g. <code>["https://example.com"]</code>',
    default=["https://example.com"],
)
```

```python
origins = config.get("security.cors.allowed_origins")
# ["https://example.com"]
```

---

## Tips for writing robust custom field types

### Handle already-serialized inputs in `serialize`

The `serialize` method may receive either the Python type or a string (if the value was previously deserialized and re-submitted). Add a type guard:

```python
def serialize(self, value) -> str:
    if isinstance(value, str):
        return value
    return my_custom_encoding(value)
```

### Return `None` for empty/missing values in `deserialize`

If `raw` is an empty string or `None` (which can happen for fields without a default), return `None`:

```python
def deserialize(self, raw: str):
    if not raw:
        return None
    return my_custom_decoding(raw)
```

### Sanitize HTML in `render`

If your `render` method echoes user-supplied values into HTML attributes, escape them:

```python
from django.utils.html import escape

def render(self, name: str, value, attrs: dict) -> str:
    safe_value = escape(value or "")
    return f'<input type="text" name="{name}" value="{safe_value}">'
```
