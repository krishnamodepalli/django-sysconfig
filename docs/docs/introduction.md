---
title: Introduction
---

# Introduction

## What is django-sysconfig?

`django-sysconfig` is a Django app that gives your project a structured, database-backed configuration system — complete with typed fields, validation, caching, encryption, and a built-in admin UI.

Think of it as a first-class home for all the settings in your app that need to be **editable at runtime** by non-developers: things like feature flags, email sender addresses, rate limits, third-party API keys, or a maintenance mode toggle.

## The core idea: schema in code, values in the database

**Your schema lives in code.** You define fields — their types, labels, defaults, validation rules — in a `sysconfig.py` file inside your Django app. This is versioned, reviewable, and self-documenting. It's the single source of truth for *what* can be configured.

**Your values live in the database.** When a staff member changes a value through the admin UI (or when your code calls `config.set(...)`), only the value is written to the database. The schema never changes.

**Your application reads values through a typed accessor.** `config.get("myapp.general.site_name")` returns a Python `str`. `config.get("myapp.general.max_items")` returns a Python `int`. No parsing, no casting, no surprises.

## Key concepts

### App label

Every configuration block is registered under an **app label** — typically the same as the Django app it belongs to. This becomes the first segment of every config path: `myapp.general.site_name`.

### Section

A **section** is a logical grouping of related fields within an app. Sections have a label (shown as a heading in the admin UI) and a `sort_order` that controls display order. In code, they're inner classes inside your config class.

### Field

A **field** defines a single configurable value. It has a type (the `frontend_model`), a label, an optional comment, a default value, optional validators, and an optional `on_save` callback.

### Accessor

The **accessor** (`config`) is the object you import in your application code to read and write configuration values. It handles caching, type conversion, and path validation transparently.

### Frontend model

The **frontend model** is the type system. It specifies how a value is serialized to the database, deserialized back to Python, and rendered in the admin UI. `django-sysconfig` ships with seven built-in types; you can write your own.

## Caching

This app uses [Django cache framework](https://docs.djangoproject.com/en/4.2/topics/cache/#django-s-cache-framework) for caching. We recommend configuring `RedisCache` or `PyMemCache` instead of `LocMemCache`. [See the caching guide](/guides/caching).

## How autodiscovery works

When Django starts up, `django-sysconfig`'s `AppConfig.ready()` method calls Django's `autodiscover_modules("sysconfig")`. This imports every `sysconfig.py` file from every installed app. Each `@register_config(...)` decorator runs, registering the config class with the global `ConfigRegistry`.

You don't wire anything up manually. Drop a `sysconfig.py` in your app, and it's discovered automatically.

## A note on what goes in the database

Only **values** are stored in the database — nothing about the schema itself. When you add a new field with a default, `django-sysconfig` creates a database row for it on startup (via `get_or_create`), but only if no row already exists for that path. Existing values are never overwritten by a schema change.

This means:

- Removing a field from code leaves an orphaned row in the database (which is harmless but can be cleaned up manually).
- Adding a field with a default makes it immediately available without any data migration.
- Renaming a field effectively creates a new field; the old database row is abandoned.

## Next steps

- [Quick Start](/quickstart) — get up and running in five minutes
- [Getting Started](/getting-started) — a thorough walkthrough of a real-world setup
- [How It Works](/how-it-works) — a deeper look at the internals
