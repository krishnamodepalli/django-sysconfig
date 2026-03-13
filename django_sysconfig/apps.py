from django.apps import AppConfig
from django.utils.module_loading import autodiscover_modules


class ConfigAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_sysconfig"
    verbose_name = "System Configuration"

    def ready(self):
        # Auto-discover sysconfig.py files in all installed apps
        autodiscover_modules("sysconfig")

        # Sync default values to DB after migrations, not during app init
        from django.db.models.signals import post_migrate

        post_migrate.connect(self._sync_defaults, sender=self)

    def _sync_defaults(self, **kwargs):
        from .registry import config_registry

        for app_label, config_def in config_registry._configs.items():
            config_registry._ensure_db_records(app_label, config_def)
