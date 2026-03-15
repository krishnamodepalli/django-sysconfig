# Why django-sysconfig?

There are several ways to manage runtime configuration in a Django project. Here's how `django-sysconfig` compares to the most common alternatives — and when each approach makes sense.

---

## vs. `settings.py` / environment variables

**Environment variables** are the right choice for infrastructure-level settings: `DATABASE_URL`, `SECRET_KEY`, `ALLOWED_HOSTS`, third-party API keys baked in at deploy time. These values are environment-specific, never change at runtime, and are well-handled by tools like `django-environ` or `python-decouple`.

**`django-sysconfig` is not a replacement for `settings.py`.** It's complementary. Use environment variables for deployment configuration. Use `django-sysconfig` for operational configuration — settings that non-engineers need to change without a redeploy.

| | `settings.py` / env vars | `django-sysconfig` |
|---|---|---|
| Changed by | Engineers, at deploy time | Staff users, at any time |
| Requires redeploy | Yes | No |
| Type safety | Manual | Built-in |
| Admin UI | No | Yes |
| Validation | Manual | Built-in |
| Audit trail | Via deploy logs | Via `on_save` callbacks |

---

## vs. `django-constance`

[`django-constance`](https://github.com/jazzband/django-constance) is a popular library for dynamic Django settings. It covers similar ground: database-backed values, a Django admin UI, and caching.

**Where `django-sysconfig` is different:**

- **Structure.** `django-constance` uses a flat namespace — all settings live at the top level. `django-sysconfig` organises settings into apps and sections, which scales better as a project grows and makes it easier for staff to find the right setting.
- **Schema location.** `django-constance` defines configuration in `settings.py` itself (`CONSTANCE_CONFIG = {...}`). `django-sysconfig` puts the schema in `sysconfig.py` files alongside the app that owns the settings — closer to where the code that uses them lives.
- **Validators.** `django-sysconfig` ships with 20 built-in validators and a clean interface for writing custom ones. `django-constance` leaves validation largely to you.
- **`on_save` callbacks.** `django-sysconfig` has first-class support for reacting to value changes. `django-constance` doesn't.
- **Encryption.** `django-sysconfig` provides a `SecretFrontendModel` with Fernet encryption out of the box.

**When `django-constance` might be a better fit:**

- You want a very simple, minimal setup with almost no concepts to learn.
- Your project is small and a flat namespace is fine.
- You need Redis or database backends for constance specifically (constance supports multiple storage backends).

---

## vs. `django-dynamic-preferences`

[`django-dynamic-preferences`](https://github.com/agateblue/django-dynamic-preferences) is a more fully-featured preferences system that supports per-user and per-site preferences in addition to global ones. It uses a registry-based approach similar to `django-sysconfig`.

**Where `django-sysconfig` is different:**

- **Scope.** `django-dynamic-preferences` solves a broader problem: per-user preferences, per-instance settings, and global config. `django-sysconfig` is focused on global system configuration only. If you need per-user preferences, `django-dynamic-preferences` is probably the right tool.
- **Simplicity.** `django-sysconfig` has fewer concepts and a smaller API surface area.
- **Encryption.** `django-sysconfig` has built-in encrypted secret fields.

**When `django-dynamic-preferences` might be a better fit:**

- You need per-user or per-site configuration, not just global settings.
- You need the full feature set of a mature, battle-tested library.

---

## vs. a custom key-value model

Many projects just add a `Setting` model with `key` and `value` fields. This works, but you end up rebuilding the same things over and over:

- Type coercion (parsing `"100"` as an integer)
- Validation (checking that an email address is actually an email address)
- Caching (to avoid a DB query on every request)
- Admin UI (registering a `ModelAdmin` class)
- Documentation (remembering what `"smtp_port"` is for)
- Defaults (what happens when there's no row for a key yet)

`django-sysconfig` gives you all of that with a few lines of code and a `sysconfig.py` file.

---

## Summary

| | `django-sysconfig` | `django-constance` | `django-dynamic-preferences` | Custom model |
|---|:---:|:---:|:---:|:---:|
| Structured schema | ✅ | ❌ flat | ✅ | ❌ |
| Schema in app code | ✅ | ❌ settings.py | ✅ | ❌ |
| Built-in validators | ✅ 20 | ❌ | ✅ | ❌ |
| `on_save` callbacks | ✅ | ❌ | ❌ | ❌ |
| Encryption at rest | ✅ | ❌ | ❌ | ❌ |
| Admin UI | ✅ | ✅ | ✅ | manual |
| Caching | ✅ | ✅ | ✅ | manual |
| Per-user preferences | ❌ | ❌ | ✅ | manual |
| Multiple storage backends | ❌ | ✅ | ✅ | — |

`django-sysconfig` is the right fit if you want **structured, typed, validated global configuration** that staff members can edit through an admin UI — with minimal boilerplate and a design that scales as your project grows.
