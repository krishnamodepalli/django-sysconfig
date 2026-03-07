from django.db import models


class ConfigValue(models.Model):
    """
    Stores configuration values in the database.

    Only the actual values are stored here. Metadata like label, comment,
    frontend_model, default, sort_order are defined in code (via Field and
    Section classes in sysconfig.py files) and read dynamically at runtime.
    """

    app_label = models.CharField(
        max_length=100,
        help_text="The app this configuration belongs to",
    )
    path = models.CharField(
        max_length=255,
        help_text="Configuration path, e.g., 'general/max_todos_per_user'",
    )
    value = models.TextField(
        null=True,
        blank=True,
        help_text="The stored configuration value",
    )

    class Meta:
        unique_together = ("app_label", "path")
        verbose_name = "Configuration Value"
        verbose_name_plural = "Configuration Values"
        ordering = ["app_label", "path"]

    def __str__(self):
        return f"{self.app_label}/{self.path}"
