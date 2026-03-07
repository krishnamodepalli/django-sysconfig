# AGENTS.md — django-sysconfig

This file gives GitHub Copilot CLI (and other AI agents) full context about this repository so they can work effectively without prior session history.

---

## What this project is

**`django-sysconfig`** is a reusable Django app that provides a Magento-style system configuration system. It lets you define typed, structured configuration fields in code (`sysconfig.py` files per-app), store their values in the database, and manage them through a built-in Django admin UI.

- **PyPI package name:** `django-sysconfig`
- **Python import name:** `django_sysconfig`
- **Minimum Python:** 3.11
- **Minimum Django:** 4.2
- **License:** MIT

---

## Repository layout

```
django-sysconfig/
├── django_sysconfig/          # The installable Django app
│   ├── __init__.py            # Lazy-imports config accessor; exports exceptions
│   ├── apps.py                # AppConfig (name="django_sysconfig")
│   ├── models.py              # ConfigValue model (app_label, path, value)
│   ├── registry.py            # Field, Section, AppConfigDefinition, ConfigRegistry, @register_config
│   ├── accessor.py            # ConfigAccessor class + global `config` singleton (dot-notation API)
│   ├── cache.py               # ConfigCache singleton (wraps Django cache framework)
│   ├── encryption.py          # Fernet encryption/decryption (key derived from SECRET_KEY)
│   ├── frontend_models.py     # BaseFrontendModel + 7 concrete types (see below)
│   ├── validators.py          # BaseValidator + 20 concrete validators (see below)
│   ├── exceptions.py          # ConfigError hierarchy
│   ├── helpers.py             # Re-exports accessor + exceptions for convenience
│   ├── admin.py               # ConfigValueAdmin (read-only, masks secrets)
│   ├── views.py               # ConfigAppListView, ConfigAppDetailView (staff-only)
│   ├── urls.py                # app_name="django_sysconfig"; two routes
│   ├── migrations/
│   │   └── 0001_initial.py
│   └── templates/
│       ├── admin/index.html               # Extends Django admin index with config banner
│       └── django_sysconfig/
│           ├── app_list.html
│           ├── app_config.html
│           └── frontend_models/
│               ├── boolean.html
│               ├── decimal.html
│               ├── integer.html
│               ├── secret.html
│               ├── select.html
│               ├── string.html
│               └── textarea.html
├── tests/
│   ├── __init__.py
│   ├── settings.py            # Minimal Django settings for pytest-django
│   └── test_validators.py     # Tests for all validators
├── pyproject.toml             # hatchling build; dependencies; pytest config
├── README.md
├── LICENSE                    # MIT
└── .gitignore
```

---

## Core concepts

### Configuration flow

1. An app defines its config schema in `sysconfig.py` using `@register_config`, `Section`, and `Field`.
2. On Django startup, `ConfigAppConfig.ready()` calls `autodiscover_modules("sysconfig")`, which imports all `sysconfig.py` files.
3. `@register_config` registers the config class with the global `ConfigRegistry` singleton and creates `ConfigValue` DB rows for fields with defaults (if they don't exist yet).
4. At runtime, `config.get("app.section.field")` reads from cache → DB → field default, deserializes the value via the field's `FrontendModel`, and returns the correct Python type.
5. `config.set("app.section.field", value)` validates, serializes, writes to DB, and invalidates the cache entry.

### Path format

All paths use **dot notation with exactly 3 parts:** `app_label.section.field`

Examples:
- `todo.general.max_todos_per_user`
- `core.site.site_name`
- `myapp.email.sender_address`

Internally the DB stores paths as `section.field` (2 parts) with `app_label` as a separate column.

### FrontendModel

Each `Field` has a `FrontendModel` class that handles:
- **Rendering** — `render()` → HTML string via Django templates
- **Deserializing** — `get_value(raw)` → Python type (int, bool, Decimal, str, etc.)
- **Serializing** — `serialize_value(value)` → str for DB storage

Available frontend models:
| Class | Python type | Template |
|---|---|---|
| `StringFrontendModel` | `str` | `string.html` |
| `TextareaFrontendModel` | `str` | `textarea.html` |
| `IntegerFrontendModel` | `int` | `integer.html` |
| `DecimalFrontendModel` | `Decimal` | `decimal.html` |
| `BooleanFrontendModel` | `bool` | `boolean.html` |
| `SelectFrontendModel` | `str` | `select.html` (requires `choices` kwarg) |
| `SecretFrontendModel` | `str` | `secret.html` (Fernet encrypted at rest) |

### Validators

All validators live in `django_sysconfig.validators` and inherit `BaseValidator`. The function `validate_value(value, validators, label)` runs a list of validators and returns a list of error strings.

Available validators:
`NotEmptyValidator`, `NotBlankValidator`, `MinLengthValidator`, `MaxLengthValidator`, `RegexValidator`, `RangeValidator`, `PositiveValidator`, `NonNegativeValidator`, `EmailValidator`, `UrlValidator`, `IPv4Validator`, `IPv6Validator`, `IPAddressValidator`, `HostnameValidator`, `ChoiceValidator`, `SlugValidator`, `JsonValidator`, `PathValidator`, `PortValidator`, `DomainValidator`

### Encryption

`SecretFrontendModel` uses `django_sysconfig.encryption` which derives a Fernet key from `settings.SECRET_KEY` via SHA-256. Encrypted values are stored as Fernet tokens (start with `gAAAAA`). The admin masks these values.

---

## How to define configuration (consumer usage)

```python
# myapp/sysconfig.py
from django_sysconfig.registry import register_config, Section, Field
from django_sysconfig.frontend_models import StringFrontendModel, IntegerFrontendModel, BooleanFrontendModel
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

---

## How to use the accessor

```python
from django_sysconfig.accessor import config

config.get("myapp.general.site_name")          # str
config.get("myapp.general.max_items")          # int
config.get("myapp.general.unknown", default=0) # fallback if not registered
config.set("myapp.general.max_items", 200)
config.set_many({"myapp.general.site_name": "New", "myapp.general.max_items": 50})
config.all("myapp")       # {"general": {"site_name": ..., "max_items": ...}}
config.section("myapp.general")  # {"site_name": ..., "max_items": ...}
config.exists("myapp.general.site_name")  # bool
config.is_set("myapp.general.site_name")  # bool (has DB value, not just default)
```

---

## URLs / Admin UI setup

```python
# project/urls.py
path("admin/config/", include("django_sysconfig.urls")),
```

Routes:
- `""` → `ConfigAppListView` (lists all registered apps)
- `"<app_label>/"` → `ConfigAppDetailView` (GET renders form, POST saves changed fields)

Both views require `@staff_member_required`. The admin `index.html` template extends Django's admin index with a banner linking to the config UI.

---

## Running tests

```bash
pip install -e ".[dev]"
pytest
```

Tests use `pytest-django` with `tests/settings.py` (in-memory SQLite, `locmem` cache).

---

## Known areas for improvement

The following are known gaps and potential improvements to work on:

- **Test coverage** — only `test_validators.py` exists; need tests for `registry.py`, `accessor.py`, `cache.py`, `encryption.py`, `views.py`, `frontend_models.py`
- **Management command** — a `sync_config` or `list_config` management command would be useful
- **Read-the-docs / Sphinx docs** — no documentation site yet
- **`on_save` callback** — exists on `Field` but not covered by tests
- **`CHANGELOG.md`** — not yet created
- **GitHub Actions CI** — no `.github/workflows/` directory yet; needs a CI pipeline (lint + test on multiple Python/Django versions)
- **PyPI publish workflow** — needs a release GitHub Actions workflow
- **`conftest.py`** — tests currently have no shared fixtures; a `conftest.py` with a registered test config would reduce boilerplate
- **Type stubs / `py.typed` marker** — not yet added for PEP 561 compliance

---

## Commit message convention

This project uses **Conventional Commits** (https://www.conventionalcommits.org/).

Format: `<type>(<scope>): <short description>`

Common types:
- `feat` — a new feature
- `fix` — a bug fix
- `docs` — documentation changes only
- `test` — adding or updating tests
- `refactor` — code changes that neither fix a bug nor add a feature
- `chore` — build process, tooling, dependency updates
- `ci` — CI/CD workflow changes
- `perf` — performance improvements
- `style` — formatting changes (no logic change)

Scope is optional but encouraged (e.g., `feat(registry):`, `fix(accessor):`, `test(validators):`).

The initial bootstrap commit uses the type `pilot` to mark the point where AI-assisted development began.

---

## AI context

Copilot session notes and discussion summaries are stored in `.copilot/` at the repository root. This directory is **gitignored** and never committed. It exists only on the local machine and is used to carry context across Copilot CLI sessions.

The primary context file is `.copilot/context.md`.
