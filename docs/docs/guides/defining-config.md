# Defining Configuration

Your configuration schema lives in `sysconfig.py` files — one per Django app that needs configurable settings. This guide covers everything about defining apps, sections, and fields, plus advice on designing a schema that stays clean as your project grows.

## The basic structure

```python
# myapp/sysconfig.py
from django_sysconfig import register_config, Section, fields

@register_config("myapp")
class MyAppConfig:
    class General(Section):
        label = "General Settings"

        site_name = fields.String(
            label="Site Name",
            default="My App",
        )
```

Three pieces:

1. **`@register_config("app_label")`** — registers the class under the given label. Must be `snake_case`. The label becomes the first segment of every config path in this app (`myapp.general.site_name`).
2. **Inner class extending `Section`** — a logical grouping of related fields. The class name is automatically converted to `snake_case` and becomes the second path segment (`PaymentSettings` → `myapp.payment_settings.*`).
3. **Field assignments** — individual configurable values using `fields.<Type>`. The attribute name must be `snake_case`. It becomes the third path segment (`myapp.general.site_name`).

### Fields vs. the Field Class

Under the hood, every field in `django-sysconfig` is an instance of the `Field` class. The `fields` module provides pre-configured shorthands for all built-in types:

- `fields.String(...)` is shorthand for `Field(StringFrontendModel, ...)`
- `fields.Integer(...)` is shorthand for `Field(IntegerFrontendModel, ...)`
- ...and so on.

Using the `fields` module is the recommended way to define your schema as it is more concise and avoids importing multiple `FrontendModel` classes.

## Section options

| Attribute    | Type  | Default | Description                                                  |
| ------------ | ----- | ------- | ------------------------------------------------------------ |
| `label`      | `str` | —       | Heading shown in the admin UI                                |
| `sort_order` | `int` | `0`     | Display order among sections in this app (lower = first)     |

```python
class Advanced(Section):
    label = "Advanced Settings"
    sort_order = 99
```

## Field options

| Parameter        | Type                     | Required | Description                                                         |
| ---------------- | ------------------------ | -------- | ------------------------------------------------------------------- |
| `frontend_model` | `type[BaseFrontendModel]`| Yes      | The field type class — determines Python type and UI widget. [Full list of field types](/reference/field-types#overview)  |
| `label`          | `str`                    | No       | Human-readable label shown in the admin UI                          |
| `comment`        | `str`                    | No       | Help text below the input; HTML is allowed                          |
| `default`        | `Any`                    | No       | Defulat value for the config.                                       |
| `sort_order`     | `int`                    | No       | Display order within the section (lower = first)                    |
| `validators`     | `list[BaseValidator]`    | No       | List of validators run before saving                                |
| `on_save`        | `Callable`               | No       | Callback invoked after a value is written to the database           |
| `**kwargs`       | —                        | No       | Extra arguments passed through to the frontend model (e.g. `choices`, `step`) |

## A complete example

```python
from django_sysconfig import register_config, Section, fields, validators

@register_config("store")
class StoreConfig:
    class General(Section):
        label = "General"
        sort_order = 10

        store_name = fields.String(
            label="Store Name",
            default="My Store",
            validators=[validators.NotEmptyValidator()],
        )

        store_description = fields.Textarea(
            label="Store Description",
            comment="Shown on the About page. HTML allowed.",
            default="",
            sort_order=20,
        )

        currency = fields.Select(
            label="Currency",
            default="usd",
            choices=[("usd", "USD"), ("eur", "EUR"), ("gbp", "GBP")],
            validators=[validators.ChoiceValidator(["usd", "eur", "gbp"])],
            sort_order=30,
        )

    class Email(Section):
        label = "Email"
        sort_order = 20

        sender = fields.String(
            label="Sender Address",
            default="shop@example.com",
            validators=[validators.NotEmptyValidator(), validators.EmailValidator()],
        )

    class Payments(Section):
        label = "Payments"
        sort_order = 30

        live_mode = fields.Boolean(
            label="Live Mode",
            comment="<strong>Warning:</strong> enabling this processes real charges.",
            default=False,
        )

        tax_rate = fields.Decimal(
            label="Tax Rate",
            default="0.20",
            step="0.01",
            validators=[validators.RangeValidator(min_value=Decimal("0"), max_value=Decimal("1"))],
        )

        stripe_secret_key = fields.Secret(
            label="Stripe Secret Key",
            comment="Stored encrypted. Starts with <code>sk_</code>.",
        )
```

## Designing your schema

### One `sysconfig.py` per app

Each Django app should own its own configuration. Don't put all configuration for an entire project in a single file. The app label in `@register_config` groups fields in the admin UI and forms the first segment of every path.

### Section boundaries

A section is a visual and semantic grouping. Good sections:
- Have a clear, single concern ("Email Settings", "Payments", "Feature Flags")
- Contain 3–10 fields; fewer than 3 might not need their own section, more than 10 might need splitting

### Field naming

Field attribute names become path segments. Use `snake_case`. Keep names descriptive but concise — they appear in code as `config.get("myapp.section.field_name")`.

Avoid generic names like `value`, `data`, or `config` that mean nothing in isolation.

### Always set a `default`

Fields without a `default` will return `None` from `config.get(...)` until a value is explicitly saved to the database. This is usually fine for secret fields (which have no sensible default), but for most other fields, a `default` makes your app's behavior predictable on a fresh install.

### Use `comment` liberally

The `comment` field is shown below the input in the admin UI. Use it to explain:
- What the value is used for
- What format is expected (e.g., "As a decimal, e.g. 0.20 for 20%")
- Any side effects of changing the value
- Links to external documentation

HTML is allowed in `comment`, so you can use `<code>`, `<strong>`, and links.

### Sort order

Both sections and fields accept a `sort_order` integer. Lower numbers appear first. If you don't specify `sort_order`, fields appear in the order Python sees them (which is definition order in Python 3.7+). Being explicit with `sort_order` makes your schema easier to reorganize later without changing the visual order in the admin UI.

## What happens on startup

When your `sysconfig.py` is imported:

1. The `@register_config(...)` decorator registers the class with the global `ConfigRegistry`.
2. For every field that has a `default`, a `ConfigValue` database row is created using `get_or_create`. If a row already exists (from a previous run), it's left untouched.
3. Every field will have a one-one mapping in the DB row and is created on the app start or restart.

This means it's safe to add new fields with defaults between deployments — they'll be available immediately on the next startup, with no manual data migration needed.
