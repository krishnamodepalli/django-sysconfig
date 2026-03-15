# Getting Started

This guide walks through a realistic setup: two Django apps, each with their own configuration, using several field types, validators, and the admin UI. By the end, you'll have a solid mental model for how `django-sysconfig` fits into a real project.

If you want the shortest possible path to working code, start with [Quick Start](quickstart.md) instead.

---

## Project structure

Suppose you have a Django project with two apps:

```
myproject/
├── myproject/
│   ├── settings.py
│   └── urls.py
├── notifications/
│   ├── models.py
│   └── sysconfig.py     ← we'll create this
├── billing/
│   ├── models.py
│   └── sysconfig.py     ← and this
```

---

## Step 1: Install and configure

If you haven't done this yet, follow the [Quick Start](quickstart.md) steps 1–4 first. Come back here once migrations have run and the admin URL is wired up.

---

## Step 2: Define config for the `notifications` app

```python
# notifications/sysconfig.py
from django_sysconfig.registry import register_config, Section, Field
from django_sysconfig.frontend_models import (
    StringFrontendModel,
    BooleanFrontendModel,
    SelectFrontendModel,
    SecretFrontendModel,
)
from django_sysconfig.validators import (
    NotEmptyValidator,
    EmailValidator,
    ChoiceValidator,
)

@register_config("notifications")
class NotificationsConfig:
    class Email(Section):
        label = "Email Settings"
        sort_order = 10

        sender_address = Field(
            StringFrontendModel,
            label="Sender Address",
            comment="The From: address on all outgoing emails.",
            default="no-reply@example.com",
            validators=[NotEmptyValidator(), EmailValidator()],
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
            label="Enable SMS Notifications",
            default=False,
        )

        api_key = Field(
            SecretFrontendModel,
            label="SMS Provider API Key",
            comment="Stored encrypted. Never displayed after saving.",
        )
```

A few things to notice:

- **Multiple sections** — `Email` and `Sms` are separate sections within the same app. They'll appear as distinct groupings in the admin UI.
- **`SelectFrontendModel`** requires a `choices` kwarg — a list of `(value, label)` tuples, same as Django's own choice fields.
- **`SecretFrontendModel`** encrypts the value at rest. The admin UI will never display the stored value after it's been saved.

---

## Step 3: Define config for the `billing` app

```python
# billing/sysconfig.py
from decimal import Decimal
from django_sysconfig.registry import register_config, Section, Field
from django_sysconfig.frontend_models import (
    BooleanFrontendModel,
    DecimalFrontendModel,
    IntegerFrontendModel,
)
from django_sysconfig.validators import (
    RangeValidator,
    NonNegativeValidator,
    PositiveValidator,
)

@register_config("billing")
class BillingConfig:
    class General(Section):
        label = "General"
        sort_order = 10

        live_mode = Field(
            BooleanFrontendModel,
            label="Live Mode",
            comment="When disabled, all charges are simulated.",
            default=False,
        )

    class Pricing(Section):
        label = "Pricing"
        sort_order = 20

        tax_rate = Field(
            DecimalFrontendModel,
            label="Tax Rate",
            comment="As a decimal, e.g. 0.20 for 20%.",
            default=Decimal("0.20"),
            step="0.001",
            validators=[RangeValidator(min_value=Decimal("0"), max_value=Decimal("1"))],
        )

        free_tier_limit = Field(
            IntegerFrontendModel,
            label="Free Tier Item Limit",
            default=10,
            validators=[PositiveValidator()],
        )

        trial_days = Field(
            IntegerFrontendModel,
            label="Trial Period (days)",
            default=14,
            validators=[NonNegativeValidator()],
        )
```

---

## Step 4: Restart and verify

Restart your dev server. On startup, Django autodiscovers both `sysconfig.py` files and registers them. Visit `/admin/config/` — you should see both `notifications` and `billing` listed.

<!-- SCREENSHOT: Admin config list view showing "billing" and "notifications" apps -->

Click into `notifications`. You'll see the `Email Settings` and `SMS Settings` sections, with all their fields pre-populated with default values.

<!-- SCREENSHOT: notifications app detail view with Email Settings section expanded -->

---

## Step 5: Read values in your application code

```python
# notifications/tasks.py
from django_sysconfig.accessor import config

def send_email(to_address, subject, body):
    sender = config.get("notifications.email.sender_address")
    fmt    = config.get("notifications.email.format")
    # ... your email logic
```

```python
# billing/views.py
from django_sysconfig.accessor import config

def checkout(request):
    if not config.get("billing.general.live_mode"):
        # simulate the charge
        return simulate_charge(request)

    tax_rate = config.get("billing.pricing.tax_rate")  # Decimal
    # ... real charge logic
```

---

## Step 6: Write values programmatically

You can also set values from code — useful for tests, management commands, or initial data setup:

```python
from django_sysconfig.accessor import config

# Single value
config.set("notifications.email.sender_address", "hello@myapp.com")

# Multiple values atomically
config.set_many({
    "billing.general.live_mode": True,
    "billing.pricing.tax_rate": Decimal("0.15"),
    "billing.pricing.trial_days": 30,
})
```

`set_many` writes all values in a single database transaction and invalidates all affected cache entries.

---

## What's next?

You now have a fully working multi-app configuration setup. Explore deeper topics:

- [Defining Configuration](guides/defining-config.md) — section options, field options, and design tips
- [Admin UI Guide](guides/admin-ui.md) — walkthrough of the staff interface
- [Encryption Guide](guides/encryption.md) — how secret fields work and how to handle key rotation
- [Field Types Reference](reference/field-types.md) — all seven types in detail
- [Validators Reference](reference/validators.md) — all 20 validators with usage examples
