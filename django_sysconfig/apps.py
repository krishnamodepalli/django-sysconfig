from django.apps import AppConfig
from django.utils.module_loading import autodiscover_modules


class ConfigAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_sysconfig"
    verbose_name = "System Configuration"

    def ready(self):
        # Auto-discover sysconfig.py files in all installed apps
        autodiscover_modules("sysconfig")
