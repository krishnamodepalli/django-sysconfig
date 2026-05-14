# Field Types Reference

Field types (called `FrontendModel` classes internally) control three things: the Python type returned by `config.get(...)`, how values are serialized to and from the database, and the UI widget rendered in the admin.

The recommended way to define fields is using the `django_sysconfig.fields` module.

---

## Overview

| Helper                   | FrontendModel Class      | Python type | Admin widget           |
| ------------------------ | ------------------------ | ----------- | ---------------------- |
| `fields.String`          | `StringFrontendModel`    | `str`       | Text input             |
| `fields.Textarea`        | `TextareaFrontendModel`  | `str`       | Textarea               |
| `fields.Integer`         | `IntegerFrontendModel`   | `int`       | Number input           |
| `fields.Decimal`         | `DecimalFrontendModel`   | `Decimal`   | Number input with step |
| `fields.Boolean`         | `BooleanFrontendModel`   | `bool`      | Checkbox               |
| `fields.Select`          | `SelectFrontendModel`    | `str`       | Dropdown select        |
| `fields.Secret`          | `SecretFrontendModel`    | `str`       | Password input (masked)|

---

## fields.String

A single-line text input. Returns a `str`.

```python
from django_sysconfig import fields

site_name = fields.String(
    label="Site Name",
    default="My App",
)
```

**Reading:**
```python
config.get("myapp.general.site_name")  # str → "My App"
```

**Use for:** names, addresses, URLs, short text values, anything that fits comfortably on one line.

---

## fields.Textarea

A multi-line text area. Returns a `str`. Useful for longer text like descriptions, templates, or snippets.

```python
from django_sysconfig import fields

welcome_message = fields.Textarea(
    label="Welcome Message",
    comment="Shown on the dashboard. HTML is allowed.",
    default="Welcome to our platform.",
)
```

**Reading:**
```python
config.get("myapp.general.welcome_message")  # str (may contain newlines)
```

**Use for:** descriptions, HTML snippets, multi-line templates, legal disclaimers.

---

## fields.Integer

A number input. Returns a Python `int`.

```python
from django_sysconfig import fields, validators

max_items = fields.Integer(
    label="Max Items Per User",
    default=100,
    validators=[validators.RangeValidator(min_value=1, max_value=10_000)],
)
```

**Reading:**
```python
config.get("myapp.general.max_items")  # int → 100
```

**Use for:** limits, counts, timeouts (in seconds), port numbers, pagination sizes.

---

## fields.Decimal

A number input with configurable step precision. Returns a Python `Decimal`.

```python
from decimal import Decimal
from django_sysconfig import fields, validators

tax_rate = fields.Decimal(
    label="Tax Rate",
    comment="As a decimal. For example, 0.20 represents 20%.",
    default=Decimal("0.20"),
    step="0.001",   # controls the HTML input step attribute
    validators=[validators.RangeValidator(min_value=Decimal("0"), max_value=Decimal("1"))],
)
```

**Reading:**
```python
config.get("billing.pricing.tax_rate")  # Decimal → Decimal("0.20")
```

The `step` kwarg is passed through to the HTML `<input step="...">` attribute. It controls the increment buttons and validation in the browser, but does not affect how the value is stored or returned.

**Use for:** tax rates, percentages, prices, exchange rates, any value where floating-point precision matters.

::: info Why `Decimal` and not `float`?
Floating-point arithmetic is imprecise for financial calculations. `Decimal("0.1") + Decimal("0.2")` is exactly `Decimal("0.3")`. `0.1 + 0.2` in Python floats is `0.30000000000000004`.
:::

---

## fields.Boolean

A toggle button. Returns a Python `bool`.

```python
from django_sysconfig import fields

maintenance_mode = fields.Boolean(
    label="Maintenance Mode",
    comment="When enabled, the site returns 503 to all visitors.",
    default=False,
)
```

**Reading:**
```python
config.get("myapp.general.maintenance_mode")  # bool → False
```

Stored as `"true"` (True) or `"false"` (False) in the database.

**Use for:** feature flags, toggles, enable/disable switches.

---

## fields.Select

A dropdown select. Returns a `str` — the *value* of the selected choice (not the display label).

Requires a `choices` kwarg: a list of `(value, display_label)` tuples.

```python
from django_sysconfig import fields, validators

environment = fields.Select(
    label="Environment",
    default="production",
    choices=[
        ("development", "Development"),
        ("staging", "Staging"),
        ("production", "Production"),
    ],
    validators=[validators.ChoiceValidator(["development", "staging", "production"])],
)
```

**Reading:**
```python
config.get("myapp.general.environment")  # str → "production"
```

::: tip
Always pair a select field with a `ChoiceValidator`. This ensures the stored value is always one of your valid choices, even if someone sets it programmatically via `config.set(...)`.
:::

**Use for:** mode selection, theme selection, log level, any enumerated value.

---

## fields.Secret

A password-style input. Stores the value **encrypted at rest** using Fernet symmetric encryption. Returns a plaintext `str` when read.

```python
from django_sysconfig import fields

api_key = fields.Secret(
    label="Third-Party API Key",
    comment="Stored encrypted. Never displayed after saving.",
)
```

**Reading:**
```python
config.get("integrations.service.api_key")  # str → "sk_live_abc123..."
# Decryption is transparent — you always get the plaintext value
```

**Admin UI behavior:**
- The input is always rendered as an empty password field.
- Leaving the input blank on save preserves the existing encrypted value.
- The decrypted value is **never** sent to the browser.

For details on the encryption scheme and key rotation, see the [Encryption guide](../guides/encryption.md).

**Use for:** API keys, passwords, tokens, webhook secrets, any credential.

---

## Using multiple field types together

```python
from decimal import Decimal
from django_sysconfig import register_config, Section, fields, validators

@register_config("email")
class EmailConfig:
    class Smtp(Section):
        label = "SMTP Settings"

        host = fields.String(label="Host", default="smtp.example.com")
        port = fields.Integer(label="Port", default=587, validators=[validators.PortValidator()])
        use_tls = fields.Boolean(label="Use TLS", default=True)
        username = fields.String(label="Username", default="")
        password = fields.Secret(label="Password")
        timeout = fields.Decimal(
            label="Timeout (seconds)",
            default=Decimal("30.0"),
            step="0.5",
        )
```
