# django-sysconfig

[![PyPI version](https://img.shields.io/pypi/v/django-sysconfig?label=PyPI&color=blue&logo=pypi&logoColor=white)](https://pypi.org/project/django-sysconfig/)
[![Python versions](https://img.shields.io/pypi/pyversions/django-sysconfig)](https://pypi.org/project/django-sysconfig/)
[![CI](https://github.com/krishnamodepalli/django-sysconfig/actions/workflows/ci.yml/badge.svg)](https://github.com/krishnamodepalli/django-sysconfig/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/krishnamodepalli/django-sysconfig)](https://github.com/krishnamodepalli/django-sysconfig/blob/master/LICENSE)

**Schema-driven, database-backed runtime configuration for Django.**

Define typed config fields in code. Store values in the database. Edit everything live through a built-in admin UI — without touching `settings.py`.

![django-sysconfig demo](https://github.com/krishnamodepalli/django-sysconfig/releases/download/v0.3.0/django-sysconfig.gif)

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

Staff can toggle `maintenance_mode` at `/admin/config/` — no code change, no redeploy.

---

## Documentation

Full guides, API reference, and examples are in the docs.

- [Quick Start](https://krishnamodepalli.github.io/django-sysconfig/quickstart/) — up and running in 5 minutes
- [Installation](https://krishnamodepalli.github.io/django-sysconfig/installation/) — full setup guide

---

## Contributing

See [CONTRIBUTING.md](https://github.com/krishnamodepalli/django-sysconfig/blob/master/CONTRIBUTING.md). Issues and pull requests are welcome.

---

## Security

Please do not open a public issue for security vulnerabilities. Report them privately via [GitHub Security Advisories](https://github.com/krishnamodepalli/django-sysconfig/security/advisories/new).
