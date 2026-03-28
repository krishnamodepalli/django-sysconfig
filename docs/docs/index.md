# django-sysconfig

**Schema-driven, database-backed runtime configuration for Django.**

Define typed configuration fields in code. Store their values in the database. Let your team manage everything through a clean admin UI — without ever touching `settings.py`.

![django-sysconfig demo](https://github.com/krishnamodepalli/django-sysconfig/releases/download/v0.3.0/django-sysconfig.gif)

## Why django-sysconfig?

Some settings belong in `settings.py`. Others — feature flags, rate limits, API keys, maintenance mode — need to change at runtime, often by someone who isn't an engineer. `django-sysconfig` gives those settings a proper home: a typed schema in code, values in the database, and a clean staff UI to manage them.

## What you get out of the box

- **Typed fields** — string, integer, decimal, boolean, select, textarea, and encrypted secret
- **Code-driven schema** — your config structure lives in `sysconfig.py` files; only values go in the database
- **Dot-notation accessor** — `config.get("myapp.general.site_name")` returns the right Python type, automatically
- **Built-in caching** — values are cached via Django's cache framework and invalidated on every write
- **Encryption at rest** — secret fields use Fernet symmetric encryption, keyed from your `SECRET_KEY`
- **20 built-in validators** — email, URL, IP, hostname, range, regex, slug, JSON, port, and more
- **Auto-discovery** — drop a `sysconfig.py` in any installed app and it's picked up on startup
- **Admin UI** — staff-only views for browsing and editing configuration, per app and section
- **`on_save` callbacks** — react to value changes with custom logic
- **Management commands** — `config [get | set | reset | export | import]`. [See more](/cli/management-command)

## Get started

New here? Head to the [Quick Start](/quickstart) to have `django-sysconfig` running in under five minutes.

Want the full picture first? Read the [Introduction](/introduction) to understand the design philosophy and how everything fits together.

## Requirements

| Dependency     | Minimum version |
| -------------- | --------------- |
| Python         | 3.11            |
| Django         | 4.2             |
| `cryptography` | 41.0            |

## Installation

```bash
pip install django-sysconfig
```

See the full [Installation guide](/installation) for `INSTALLED_APPS` setup, URL configuration, and migrations.
