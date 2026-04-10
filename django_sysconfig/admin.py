from django.contrib import admin

from .models import ConfigValue

# Constants for value preview display
FERNET_TOKEN_PREFIX = "gAAAAA"  # All Fernet tokens start with this
SECRET_VALUE_MIN_LENGTH = 50  # Values longer than this are likely encrypted
PREVIEW_MAX_LENGTH = 100  # Maximum length for value preview


@admin.register(ConfigValue)
class ConfigValueAdmin(admin.ModelAdmin):
    """Basic admin for ConfigValue model - mainly for debugging purposes."""

    list_display = ("app_label", "path", "value_preview")
    list_filter = ("app_label",)
    search_fields = ("app_label", "path")
    ordering = ("app_label", "path")
    readonly_fields = ("app_label", "path", "value_preview")

    def value_preview(self, obj):
        """Show value preview, masking secrets."""
        if not obj.value:
            return "(empty)"
        # Mask potentially encrypted/secret values (they start with 'gAAAAA' for Fernet)
        if (
            obj.value.startswith(FERNET_TOKEN_PREFIX)
            or len(obj.value) > SECRET_VALUE_MIN_LENGTH
        ):
            return "*** (encrypted/secret value hidden) ***"
        # Truncate long values
        if len(obj.value) > PREVIEW_MAX_LENGTH:
            return obj.value[:PREVIEW_MAX_LENGTH] + "..."
        return obj.value

    value_preview.short_description = "Value"
