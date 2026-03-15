---
title: Quick Start
description: Learn what django-sysconfig is and why it exists.
---

# Quick Start

## Installation & Setup

1. Straight forward installation with pip.

```bash
pip3 install django-sysconfig
```

2. Add the `django_sysconfig` to the `INSTALLED_APPS` array in `settings.py`

```python
# settings.py

INSTALLED_APPS = [
    'django_sysconfig',     # Add it at the top

    'django.contrib.auth',
    # rest of the apps
]
```

3. Migrate after adding the app to `INSTALLED_APPS`.

```bash
python3 manage.py makemigrations
python3 manage.py migrate
```

4. Include `django-sysconfig` URLs in your root `urls.py`. It is recommended that it is added before `/admin/` route.

```python
# urls.py
from django.urls import path, include

urlpatterns = [
    path("admin/config/", include("django_sysconfig.urls")), # ← Add this
    path("admin/", admin.site.urls),
]
```


## Usage

### Define the schema

In your app, create a `sysconfig.py` file and define you schema

```python
# myapp/sysconfig.py

from django_sysconfig.registry import register_config, Section, Field
from django_sysconfig.frontend_models import StringFrontendModel, SecretFrontendModel
from django_sysconfig.validators import NotEmptyValidator

@register_config("myapp")
class MyAppConfig:
    class Stripe(Section):
        label = "Stripe Settings"
        sort_order = 10

        public_key = Field(
            StringFrontendModel,
            label="Site Name",
            default="My App",
            validators=[NotEmptyValidator()],
        )

        secret_key = Field(
            SecretFrontendModel,
            label="Max Items",
            default=100,
            validators=[NotEmptyValidator()]
        )
```

### Accessing

In any part of you application, just get a configuration like

```python
from django_sysconfig.accessor import config
import stripe

stripe.api_key = config.get('myapp.stripe.secret_key')
```
