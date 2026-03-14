---
title: Configuration
description: How to define configuration for your Django app.
---

# Configuration

To add configuration to your app, create a `sysconfig.py` file in your Django app directory.

## Basic Usage

Use `@register_config`, `Section`, and `Field` to define your schema.

```python
# myapp/sysconfig.py
from django_sysconfig.registry import register_config, Section, Field
from django_sysconfig.frontend_models import StringFrontendModel, IntegerFrontendModel
from django_sysconfig.validators import NotEmptyValidator, RangeValidator

@register_config("myapp")
class MyAppConfig:
    class General(Section):
        label = "General Settings"
        sort_order = 10

        site_name = Field(
            StringFrontendModel,
            label="Site Name",
            default="My App",
            validators=[NotEmptyValidator()],
        )

        max_items = Field(
            IntegerFrontendModel,
            label="Max Items",
            default=100,
            validators=[RangeValidator(min_value=1, max_value=9999)],
        )
```

## Using the Accessor

You can access configuration values anywhere in your code using the global `config` object.

```python
from django_sysconfig.accessor import config

# Get a value
site_name = config.get("myapp.general.site_name")

# Get a value with a fallback
unknown = config.get("myapp.general.unknown", default="fallback")

# Update a value
config.set("myapp.general.site_name", "New Site Name")

# Check if a config exists
if config.exists("myapp.general.site_name"):
    ...
```

## Available Frontend Models

Frontend models handle the rendering and data conversion for fields.

| Class | Python type |
|---|---|
| `StringFrontendModel` | `str` |
| `TextareaFrontendModel` | `str` |
| `IntegerFrontendModel` | `int` |
| `DecimalFrontendModel` | `Decimal` |
| `BooleanFrontendModel` | `bool` |
| `SelectFrontendModel` | `str` |
| `SecretFrontendModel` | `str` (encrypted) |

## Validators

django-sysconfig includes 20+ built-in validators, including:
`NotEmptyValidator`, `NotBlankValidator`, `MinLengthValidator`, `MaxLengthValidator`, `RegexValidator`, `RangeValidator`, `EmailValidator`, `UrlValidator`, `IPv4Validator`, `IPv6Validator`, `JsonValidator`, `PathValidator`, etc.

---

That's it! You now have a typed, managed configuration system for your Django app.
