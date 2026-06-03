# Admin UI Guide

`django-sysconfig` ships with a built-in staff interface for browsing and editing all registered configuration. It's designed to feel like a natural extension of the Django admin.

## Setup

If you haven't wired up the admin UI yet, add these two lines to your `urls.py`:

```python
# urls.py
from django.urls import include, path
from django.contrib import admin

urlpatterns = [
    path("admin/config/", include("django_sysconfig.urls")),  # ← before admin/
    path("admin/", admin.site.urls),
]
```

::: warning
The config path must come *before* `path("admin/", ...)`. Django matches patterns in order, and the default admin would otherwise swallow the `/admin/config/` URL.
:::

## Access control

Both views require `request.user.is_staff = True`. Non-staff users who visit `/admin/config/` are redirected to the login page, exactly like the Django admin.

There is no finer-grained permission system built in — any staff member can read and edit any configuration value. If you need field-level or app-level restrictions, you can extend the existing views and add more permissions to it (or open an issue to discuss your use case).

## The app list view

**URL:** `/admin/config/`

<!-- SCREENSHOT: App list view showing three registered apps: "billing", "myapp", "notifications" -->

The app list view shows every Django app that has registered configuration (i.e., has a `sysconfig.py` with a `@register_config(...)` decorator). Apps are listed alphabetically by label.

From here, click any app to navigate to its detail view.

:::tip
The Django admin index page is extended with a **"System Configuration"** banner that links directly to this page, so staff members don't need to know the URL.
:::

<!-- SCREENSHOT: Django admin index page showing the "System Configuration" banner at the top -->

## The app detail view

**URL:** `/admin/config/<app_label>/`

<!-- SCREENSHOT: App detail view for "billing" showing "General" and "Pricing" sections with fields -->

This is where values are edited. The detail view renders all sections and fields for the selected app.

### How the form works

- Sections appear as collapsible groups, ordered by their `sort_order`.
- Each field is rendered with its `label`, its current value (or default), and its `comment` as help text below the input.
- The form shows all sections at once. Submitting saves the fields that are changed on the page.

<!-- GIF: Opening an app detail view, changing a value, and saving -->

### Field rendering

Each field type renders a different input:

| Field type            | UI widget                     |
| --------------------- | ----------------------------- |
| `StringFrontendModel` | Single-line text input        |
| `TextareaFrontendModel` | Multi-line textarea         |
| `IntegerFrontendModel` | Number input                 |
| `DecimalFrontendModel` | Number input with step       |
| `BooleanFrontendModel` | Checkbox                     |
| `SelectFrontendModel` | Dropdown `<select>`           |
| `SecretFrontendModel` | Password input (masked)       |

### Secret fields

Secret fields (`SecretFrontendModel`) are always displayed as an empty password input, even if a value has been saved. The actual stored value is never sent to the browser.

To update a secret field: type the new value and save. To leave it unchanged: do not touch that input and save — the existing value is preserved. There will be a dot (beside the label) representing if a value is changed or not, so that no values are not changed accidentally.

<!-- SCREENSHOT: A secret field showing a masked/empty password input with a "saved" indicator -->

### Validation errors

If any field fails validation, the form is re-rendered with error messages inline. No values are saved until all fields pass validation.

<!-- SCREENSHOT: A form with a validation error shown below an email field -->

## Navigating back to Django admin

The detail view includes a breadcrumb back to both the app list and the Django admin index. The `Back to Admin` link in the top bar takes you to `/admin/`.

## Tips for staff users

- **Changes take effect immediately.** There's no "publish" or "activate" step. As soon as you hit Save, the new values are live (the cache is invalidated and the database is updated).
- **Secret fields are write-only.** If you need to inspect a stored value, use [config `get`](/cli/management-command#get) from the terminal.
