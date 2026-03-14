---
title: Introduction
description: Learn what django-sysconfig is and why it exists.
---

# Introduction

Welcome to the **django-sysconfig** documentation. django-sysconfig is a reusable <abbr title="A high-level Python web framework that encourages rapid development and clean, pragmatic design.">Django</abbr> application that provides a Magento-style system configuration system.

:::note
This documentation is built by a custom static site generator included in this repo. Run `npm run build` to compile these Markdown files into a deployable `dist/` folder.
:::

## What is django-sysconfig?

django-sysconfig lets you define typed, structured configuration fields in code (`sysconfig.py` files per-app), store their values in the database, and manage them through a built-in Django admin UI.

### Key Features

- **Typed Configuration** — define fields as int, bool, Decimal, str, etc.
- **Magento-style Registry** — use `@register_config`, `Section`, and `Field`.
- **Admin UI** — beautiful staff-only UI for managing configuration.
- **Cache-first Access** — high performance with Django's cache framework.
- **Encrypted Secrets** — store sensitive values (like API keys) encrypted at rest.
- **Extensible Validators** — 20+ built-in validators, or add your own.

## Core Concepts

### Configuration Flow

1. An app defines its config schema in `sysconfig.py` using `@register_config`, `Section`, and `Field`.
2. On Django startup, `ConfigAppConfig.ready()` calls `autodiscover_modules("sysconfig")`.
3. `@register_config` registers the config class and creates `ConfigValue` DB rows for fields with defaults.
4. At runtime, `config.get("app.section.field")` reads from cache → DB → field default.
5. `config.set("app.section.field", value)` validates, serializes, writes to DB, and invalidates the cache.

## Path Format

All paths use **dot notation with exactly 3 parts:** `app_label.section.field`

Examples:
- `todo.general.max_todos_per_user`
- `core.site.site_name`

---

Ready to get started? Head over to [Installation](/installation/) next.
