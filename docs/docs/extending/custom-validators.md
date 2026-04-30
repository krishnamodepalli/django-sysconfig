# Custom Validators

The 20 built-in validators cover the most common cases, but you can write your own by subclassing `BaseValidator`. A custom validator is just a callable class that inspects a value and returns a list of error strings.

---

## The `BaseValidator` interface

```python
from django_sysconfig.validators import BaseValidator

class BaseValidator:
    default_message = "This value is not valid."

    def __init__(self, message: str = None):
        self.message = message or self.default_message

    def __call__(self, value) -> list[str]:
        """
        Validate the value. Return a list of error strings.
        Return an empty list if the value is valid.
        """
        raise NotImplementedError
```

Your validator must implement `__call__` and return:
- `[]` — an empty list if the value is valid
- `["Error message here."]` — a list with one or more strings if the value is invalid

---

## A simple example

A validator that requires the value to start with a specific prefix:

```python
from django_sysconfig.validators import BaseValidator

class StartsWithValidator(BaseValidator):
    default_message = "Value must start with '{prefix}'."

    def __init__(self, prefix: str, message: str = None):
        self.prefix = prefix
        super().__init__(message=message or self.default_message.format(prefix=prefix))

    def __call__(self, value) -> list[str]:
        if value and not str(value).startswith(self.prefix):
            return [self.message]
        return []
```

Usage:

```python
stripe_key = Field(
    StringFrontendModel,
    label="Stripe Secret Key",
    validators=[StartsWithValidator("sk_")],
)
```

---

## Reusing built-in validators

You can compose your custom validator from existing built-in ones:

```python
from django_sysconfig.validators import BaseValidator, UrlValidator
from myapp.validators import StartsWithValidator  # defined earlier

class HttpsUrlValidator(BaseValidator):
    """Must be a valid URL that uses the https scheme."""

    def __init__(self, message: str = None):
        super().__init__(message=message)
        self._url_validator = UrlValidator(schemes=["https"])

    def __call__(self, value) -> list[str]:
        return self._url_validator(value)
```

Or, more directly, just compose a list of validators on the field itself:

```python
webhook_url = Field(
    StringFrontendModel,
    label="Webhook URL",
    validators=[
        NotEmptyValidator(),
        UrlValidator(schemes=["https"]),
    ],
)
```

---

## Tips

### Don't validate `None` unless intentional

Most validators should return `[]` (valid) when the value is `None` or empty — let `NotEmptyValidator` handle the "required" concern. This keeps validators single-purpose and composable.

```python
def __call__(self, value) -> list[str]:
    if not value:
        return []  # not my concern — use NotEmptyValidator separately
    # ... actual validation
```

### Return multiple errors when appropriate

If your validator checks multiple conditions, return all failures at once — don't short-circuit after the first. Users appreciate seeing all the issues in one save.

### Keep error messages user-friendly

Error messages are shown in the admin UI. Write them for a staff member, not a developer. "Must be a valid email address" is better than "EmailValidator constraint failed".
