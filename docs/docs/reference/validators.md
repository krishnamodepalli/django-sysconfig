# Validators Reference

Validators run before a value is saved — whether through the admin UI or via `config.set(...)`. If any validator fails, the value is not written and a `ConfigValueError` is raised.

All validators live in `django_sysconfig.validators`.

---

## Using validators

Pass a list of validator instances to the `validators` parameter of a `Field`:

```python
from django_sysconfig.validators import NotEmptyValidator, EmailValidator

sender = Field(
    StringFrontendModel,
    label="Sender Address",
    validators=[NotEmptyValidator(), EmailValidator()],
)
```

Validators are run in order. All validators run even if an earlier one fails, so the user sees all errors at once.

---

## Overriding the error message

Every validator accepts an optional `message` argument to override the default error text:

```python
from django_sysconfig.validators import RangeValidator

max_items = Field(
    IntegerFrontendModel,
    label="Max Items",
    validators=[
        RangeValidator(
            min_value=1,
            max_value=100,
            message="Max items must be between 1 and 100.",
        )
    ],
)
```

---

## Presence validators

### `NotEmptyValidator()`

The value must not be `None`, an empty string `""`, an empty list `[]`, or an empty dict `{}`.

**Alias:** `Required` (same class, different name)

```python
from django_sysconfig.validators import NotEmptyValidator, Required  # same thing

Field(StringFrontendModel, validators=[NotEmptyValidator()])
```

---

### `NotBlankValidator()`

The string value must not consist entirely of whitespace. `None` is allowed (use `NotEmptyValidator` if you also want to reject `None`).

```python
site_name = Field(StringFrontendModel, validators=[NotBlankValidator()])
```

---

## String length validators

### `MinLengthValidator(min_length)`

The string must be at least `min_length` characters long.

```python
from django_sysconfig.validators import MinLengthValidator

password_min = Field(IntegerFrontendModel, validators=[MinLengthValidator(8)])
```

---

### `MaxLengthValidator(max_length)`

The string must be at most `max_length` characters long.

```python
from django_sysconfig.validators import MaxLengthValidator

slug = Field(StringFrontendModel, validators=[MaxLengthValidator(50)])
```

---

## Pattern validators

### `RegexValidator(pattern, flags=0, inverse=False)`

The value must match the given regex pattern. Set `inverse=True` to require that the value does *not* match.

```python
from django_sysconfig.validators import RegexValidator

# Must start with "sk_"
api_key = Field(StringFrontendModel, validators=[RegexValidator(r"^sk_")])

# Must NOT contain spaces
no_spaces = Field(StringFrontendModel, validators=[RegexValidator(r"\s", inverse=True)])
```

---

### `SlugValidator()`

The value must contain only letters, digits, hyphens (`-`), and underscores (`_`). No spaces or special characters.

```python
from django_sysconfig.validators import SlugValidator

url_slug = Field(StringFrontendModel, validators=[SlugValidator()])
```

---

### `JsonValidator()`

The value must be a valid JSON string.

```python
from django_sysconfig.validators import JsonValidator

extra_metadata = Field(TextareaFrontendModel, validators=[JsonValidator()])
```

---

## Numeric validators

### `RangeValidator(min_value=None, max_value=None)`

The number must fall within the given inclusive range. Either bound can be omitted.

```python
from django_sysconfig.validators import RangeValidator
from decimal import Decimal

# Integer range
items = Field(IntegerFrontendModel, validators=[RangeValidator(min_value=1, max_value=1000)])

# Decimal range
tax = Field(DecimalFrontendModel, validators=[RangeValidator(min_value=Decimal("0"), max_value=Decimal("1"))])

# Only a lower bound
port = Field(IntegerFrontendModel, validators=[RangeValidator(min_value=1)])
```

---

### `PositiveValidator()`

The number must be greater than zero.

```python
from django_sysconfig.validators import PositiveValidator

price = Field(DecimalFrontendModel, validators=[PositiveValidator()])
```

---

### `NonNegativeValidator()`

The number must be zero or greater.

```python
from django_sysconfig.validators import NonNegativeValidator

trial_days = Field(IntegerFrontendModel, validators=[NonNegativeValidator()])
```

---

### `PortValidator()`

The integer must be a valid TCP/UDP port number: between 1 and 65535 inclusive.

```python
from django_sysconfig.validators import PortValidator

smtp_port = Field(IntegerFrontendModel, validators=[PortValidator()])
```

---

## Network / format validators

### `EmailValidator()`

The value must be a valid email address.

```python
from django_sysconfig.validators import EmailValidator

sender = Field(StringFrontendModel, validators=[EmailValidator()])
```

---

### `UrlValidator(schemes=None)`

The value must be a valid URL. Defaults to allowing `http`, `https`, and `ftp` schemes. Pass a list to restrict which schemes are accepted.

```python
from django_sysconfig.validators import UrlValidator

# Allow http and https only
webhook_url = Field(StringFrontendModel, validators=[UrlValidator(schemes=["http", "https"])])
```

---

### `IPv4Validator()`

The value must be a valid IPv4 address (e.g. `"192.168.1.1"`).

---

### `IPv6Validator()`

The value must be a valid IPv6 address (e.g. `"::1"`).

---

### `IPAddressValidator(version=None)`

The value must be a valid IP address. Set `version=4` or `version=6` to restrict to a specific version. Leave as `None` (default) to accept both.

```python
from django_sysconfig.validators import IPAddressValidator

ip = Field(StringFrontendModel, validators=[IPAddressValidator()])           # IPv4 or IPv6
ipv4_only = Field(StringFrontendModel, validators=[IPAddressValidator(version=4)])
```

---

### `HostnameValidator()`

The value must be a valid RFC 1123 hostname (e.g. `"my-server"`, `"db.internal"`).

---

### `DomainValidator()`

The value must be a valid domain name, up to 253 characters (e.g. `"example.com"`, `"sub.domain.org"`).

---

## Other validators

### `ChoiceValidator(choices)`

The value must be one of the items in `choices`. Always use this alongside `SelectFrontendModel`.

```python
from django_sysconfig.validators import ChoiceValidator

mode = Field(
    SelectFrontendModel,
    choices=[("html", "HTML"), ("text", "Plain Text")],
    validators=[ChoiceValidator(["html", "text"])],
)
```

---

### `PathValidator(must_be_absolute=False)`

The value must look like a valid file system path. Set `must_be_absolute=True` to require an absolute path (starting with `/` on Unix or a drive letter on Windows).

```python
from django_sysconfig.validators import PathValidator

upload_dir = Field(StringFrontendModel, validators=[PathValidator(must_be_absolute=True)])
```

---

## Writing custom validators

See [Extending: Custom Validators](../extending/custom-validators.md).
