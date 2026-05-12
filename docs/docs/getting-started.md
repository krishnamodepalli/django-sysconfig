# Getting Started

This guide walks through a realistic setup: two Django apps, each with their own configuration, using several field types, validators, and the admin UI. By the end, you'll have a solid mental model for how `django-sysconfig` fits into a real project.

If you want the shortest possible path to working code, start with [Quick Start](quickstart.md) instead.

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

## Step 1: Install and configure

If you haven't done this yet, follow the [Quick Start](quickstart.md) steps first. Come back here once migrations have run and the admin URL is wired up.

## Step 2: Define config for the `notifications` app

```python
# notifications/sysconfig.py
from django_sysconfig import register_config, Section, fields, validators

@register_config("notifications")
class NotificationsConfig:
    class Email(Section):
        label = "Email Settings"
        sort_order = 10

        sender_address = fields.String(
            label="Sender Address",
            comment="The From: address on all outgoing emails.",
            default="no-reply@example.com",
            validators=[validators.NotEmptyValidator(), validators.EmailValidator()],
        )
        format = fields.Select(
            label="Email Format",
            default="html",
            choices=[("html", "HTML"), ("text", "Plain Text")],
            validators=[validators.ChoiceValidator(["html", "text"])],
        )

    class Sms(Section):
        label = "SMS Settings"
        sort_order = 20

        enabled = fields.Boolean(label="Enable SMS Notifications", default=False)
        twilio_api_key = fields.Secret(
            label="Twilio API Key",
            comment="Stored encrypted. Never displayed after saving.",
        )
```

This is the new and **recommended** way of creating configuration with the fields. The below is an example of old way of creating fields, which is still supported. This is how you will use any custom Fields created by yourself.

```python
maintenance_mode = Field(BooleanFrontendModel, label="Maintenance Mode", default=False)
```

A few things to notice:

- **Multiple sections** — `Email` and `Sms` are separate sections within the same app. They'll appear as distinct groupings in the admin UI.
- **`Select`** requires a `choices` kwarg — a list of `(value, label)` tuples, same as Django's own choice fields.
- **`Secret`** encrypts the value at rest. The admin UI will never display the stored value after it's been saved.

## Step 3: Define config for the `billing` app

```python
# billing/sysconfig.py
from django_sysconfig.registry import register_config, Section, fields, validators

@register_config("billing")
class BillingConfig:
    class General(Section):
        label = "General"
        sort_order = 10

        live_mode = fields.Field(
            BooleanFrontendModel,
            label="Live Mode",
            comment="When disabled, all charges are simulated.",
            default=False,
        )

    class Pricing(Section):
        label = "Pricing"
        sort_order = 20

        tax_rate = fields.Field(
            DecimalFrontendModel,
            label="Tax Rate",
            comment="As a decimal, e.g. 0.20 for 20%.",
            default=0.20,
            step="0.001",
            validators=[validators.RangeValidator(min_value=Decimal("0"), max_value=Decimal("1"))],
        )

        free_tier_limit = fields.Field(
            IntegerFrontendModel,
            label="Free Tier Item Limit",
            default=10,
            validators=[validators.PositiveValidator()],
        )

        trial_days = fields.Field(
            IntegerFrontendModel,
            label="Trial Period (days)",
            default=14,
            validators=[validators.NonNegativeValidator()],
        )
```

## Step 4: Restart and verify

Restart your dev server. On startup, Django autodiscovers both `sysconfig.py` files and registers them. Visit `/admin/config/` — you should see both `notifications` and `billing` listed.

<!-- SCREENSHOT: Admin config list view showing "billing" and "notifications" apps -->

Click into `notifications`. You'll see the `Email Settings` and `SMS Settings` sections, with all their fields pre-populated with default values.

<!-- SCREENSHOT: notifications app detail view with Email Settings section expanded -->

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

## What's next?

You now have a fully working multi-app configuration setup. Explore deeper topics:

- [Defining Configuration](/guides/defining-config) — section options, field options, and design tips
- [Admin UI Guide](/guides/admin-ui) — walkthrough of the staff interface
- [Encryption Guide](/guides/encryption) — how secret fields work and how to handle key rotation
- [on_save Callbacks](/guides/on-save-callbacks) — react to value changes with custom logic
- [Management Commands](/cli/management-command) — inspect and edit config from the terminal
