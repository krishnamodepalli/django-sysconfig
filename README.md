# django-sysconfig

[![PyPI version](https://img.shields.io/pypi/v/django-sysconfig?label=PyPI&color=blue&logo=pypi&logoColor=white)](https://pypi.org/project/django-sysconfig/)
[![Python versions](https://img.shields.io/pypi/pyversions/django-sysconfig)](https://pypi.org/project/django-sysconfig/)
[![CI](https://github.com/krishnamodepalli/django-sysconfig/actions/workflows/ci.yml/badge.svg)](https://github.com/krishnamodepalli/django-sysconfig/actions/workflows/ci.yml)
[![Release](https://github.com/krishnamodepalli/django-sysconfig/actions/workflows/release.yml/badge.svg)](https://github.com/krishnamodepalli/django-sysconfig/actions/workflows/release.yml)
[![License](https://img.shields.io/github/license/krishnamodepalli/django-sysconfig)](https://github.com/krishnamodepalli/django-sysconfig/blob/master/LICENSE)
[![Demo](https://img.shields.io/badge/demo-live-brightgreen?style=flat&logo=django&logoColor=white)](https://djangosysconfig.pythonanywhere.com)

**Runtime configuration for Django.** Define typed config fields in code, store values in the database, edit everything through a built-in admin UI — without touching `settings.py`.
<!-- GIF: hero clip showing sysconfig.py → admin UI → config.get() returning live value -->

---

## Why django-sysconfig?

Some settings belong in `settings.py`. Others — feature flags, rate limits, API keys, email addresses — need to change at runtime without a redeploy, often by someone who isn't an engineer.

`django-sysconfig` gives those settings a proper home: a typed schema in code, values in the database, and a clean staff UI to manage them.

---

## Install

```bash
pip install django-sysconfig
```

```python
# settings.py
INSTALLED_APPS = [
    "django_sysconfig",   # add at the top
    ...
]
```

```bash
python manage.py migrate
```

---

## Quick example

```python
# myapp/sysconfig.py
from django_sysconfig.registry import register_config, Section, Field
from django_sysconfig.frontend_models import BooleanFrontendModel, IntegerFrontendModel
from django_sysconfig.validators import RangeValidator

@register_config("myapp")
class MyAppConfig:
    class General(Section):
        label = "General"

        maintenance_mode = Field(BooleanFrontendModel, label="Maintenance Mode", default=False)
        max_items = Field(IntegerFrontendModel, label="Max Items", default=100,
                          validators=[RangeValidator(min_value=1, max_value=10_000)])
```

```python
# anywhere in your project
from django_sysconfig.accessor import config

if config.get("myapp.general.maintenance_mode"):
    return HttpResponse("Down for maintenance.", status=503)
```

Staff can change `maintenance_mode` through `/admin/config/` — no code change, no redeploy.

---

## What's included

- **7 field types** — string, integer, decimal, boolean, select, textarea, encrypted secret
- **20 built-in validators** — email, URL, IP, hostname, port, range, regex, slug, JSON, and more
- **Auto-discovery** — drop a `sysconfig.py` in any installed app, it's picked up on startup
- **Typed accessor** — `config.get(...)` always returns the correct Python type
- **Caching** — values are cached via Django's cache framework, invalidated on every write
- **Encryption at rest** — secret fields use Fernet symmetric encryption
- **on_save callbacks** — react to value changes with custom logic
- **Management commands** — `config get`, `config set`, `config import`, `config export`

---

## Requirements

| | Minimum |
|---|---|
| Python | 3.11 |
| Django | 4.2 |
| `cryptography` | 41.0 |

---

## Documentation

**[krishnamodepalli.github.io/django-sysconfig](https://krishnamodepalli.github.io/django-sysconfig/)**

---

## Contributing

See [CONTRIBUTING.md](https://github.com/krishnamodepalli/django-sysconfig/blob/develop/CONTRIBUTING.md). Issues and pull requests are welcome.
