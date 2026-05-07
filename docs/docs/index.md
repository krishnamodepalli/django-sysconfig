---
layout: home
title: django-sysconfig
description: Schema-driven, database-backed runtime configuration for Django. Define typed fields in code, store values in the database, manage through a clean admin UI.

hero:
  name: django-sysconfig
  text: Runtime config for Django
  tagline: Define typed fields in code. Store values in the database. Let your team manage everything through a clean admin UI — without touching settings.py.
  actions:
    - theme: brand
      text: Quick Start
      link: /quickstart
    - theme: alt
      text: Introduction
      link: /introduction
    - theme: alt
      text: GitHub
      link: https://github.com/krishnamodepalli/django-sysconfig

features:
  - title: Typed Fields
    icon: 🔤
    details: String, integer, decimal, boolean, select, textarea, and encrypted secret — each returns the correct Python type from config.get().
  - title: Code-driven schema
    icon: 📐
    details: Your config structure lives in sysconfig.py files. Only the values go in the database. Schema changes are code reviews, not migration scripts.
  - title: Three part configuration path
    icon: 🎯
    details: The part configuration path allows structured config tree which makes scaling seamless and structuring easy.
  - title: Built-in caching
    icon: ⚡
    details: Values are cached via Django's cache framework and invalidated on every write — via transaction.on_commit() to stay consistent.
  - title: Encryption at rest
    icon: 🔒
    details: Secret fields use Fernet symmetric encryption, keyed from your SECRET_KEY. Encrypted in the DB, transparent on read.
  - title: 20+ validators
    icon: ✅
    details: Email, URL, IP, hostname, range, regex, slug, JSON, port, and more — all composable, all with custom error messages.
  - title: Auto-discovery
    icon: 🔍
    details: Drop a sysconfig.py in any installed app and it's registered on startup. No manual wiring.
  - title: Admin UI
    icon: 🖥️
    details: Staff-only views for browsing and editing configuration per app and section. Works with your existing Django admin.
---

## Requirements

| Dependency     | Minimum version |
| -------------- | --------------- |
| Python         | 3.10            |
| Django         | 4.2             |
| `cryptography` | 41.0            |

## Installation

```bash
pip install django-sysconfig
```

See the full [Installation guide](/installation) for `INSTALLED_APPS` setup, URL configuration, and migrations.
