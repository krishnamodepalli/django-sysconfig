"""
Admin Views for Configuration Management

These views provide the admin interface for managing app configurations.
They are integrated into Django's admin site and require admin permissions.
"""

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views import View

from .accessor import config
from .models import ConfigValue
from .registry import config_registry
from .validators import validate_value


@method_decorator(staff_member_required, name="dispatch")
class ConfigAppListView(View):
    """
    View to list all apps that have registered configurations.
    """

    template_name = "django_sysconfig/app_list.html"

    def get(self, request):
        configs = config_registry.get_all_configs()

        # Build list of apps with their metadata
        apps = []
        for app_label, config_def in sorted(configs.items()):
            section_count = len(config_def.sections)
            field_count = sum(
                len(section.get_fields()) for section in config_def.sections.values()
            )
            apps.append(
                {
                    "app_label": app_label,
                    "section_count": section_count,
                    "field_count": field_count,
                }
            )

        context = {
            "title": "System Configuration",
            "apps": apps,
            "has_permission": True,
            "site_header": "Django administration",
            "site_title": "Django site admin",
        }
        return render(request, self.template_name, context)


@method_decorator(staff_member_required, name="dispatch")
class ConfigAppDetailView(View):
    """
    View to display and edit configurations for a specific app.

    Renders all sections and fields for the app, allowing admins to
    modify configuration values.
    """

    template_name = "django_sysconfig/app_config.html"

    def _validate_app_label(self, request, app_label):
        """
        Validate app_label and get config definition.

        Returns:
            Tuple of (sanitized_app_label, config_def) or (None, None) if invalid
        """
        # Validate app_label to prevent potential issues
        if not app_label or not isinstance(app_label, str) or not app_label.strip():
            messages.error(request, "Invalid app label.")
            return None, None

        app_label = app_label.strip()
        config_def = config_registry.get_config(app_label)
        if not config_def:
            messages.error(request, f"No configuration found for app: {app_label}")
            return None, None

        return app_label, config_def

    def get(self, request, app_label):
        app_label, config_def = self._validate_app_label(request, app_label)
        if not config_def:
            return redirect("config:app_list")

        sections_data = self._build_sections_data(app_label, config_def)

        context = {
            "title": f"Configuration: {app_label}",
            "app_label": app_label,
            "sections": sections_data,
            "has_permission": True,
            "site_header": "Django administration",
            "site_title": "Django site admin",
        }
        return render(request, self.template_name, context)

    def post(self, request, app_label):
        app_label, config_def = self._validate_app_label(request, app_label)
        if not config_def:
            return redirect("config:app_list")

        # Get the list of changed fields (optimization)
        changed_fields_str = request.POST.get("changed_fields", "").strip()
        changed_fields = (
            {f for f in changed_fields_str.split(",") if f}
            if changed_fields_str
            else set()
        )

        # If no fields were changed, skip saving entirely
        if not changed_fields:
            messages.info(request, "No changes to save.")
            return redirect("config:app_detail", app_label=app_label)

        # First pass: validate all changed fields using their validators
        validation_errors = []
        for section_name, section in config_def.get_sections():
            section_key = section_name.lower()
            for field_name, field in section.get_fields().items():
                input_name = f"config_{section_key}_{field_name}"

                # Only validate changed fields
                if input_name not in changed_fields:
                    continue

                # Skip if field has no validators
                if not field.validators:
                    continue

                # Get and process value
                processed_value = self._get_processed_value(request, field, input_name)

                # Skip validation for optional fields when value is None/empty
                # Required fields should still validate None/empty (and fail)
                if not field.required and (
                    processed_value is None or processed_value == ""
                ):
                    continue

                # Run all validators for this field
                field_label = field.label or field_name
                errors = validate_value(processed_value, field.validators, field_label)
                validation_errors.extend(errors)

        # If validation errors, show them and redirect back
        if validation_errors:
            for error in validation_errors:
                messages.error(request, error)
            return redirect("config:app_detail", app_label=app_label)

        # Process only changed fields
        saved_count = 0
        for section_name, section in config_def.get_sections():
            section_key = section_name.lower()
            for field_name, field in section.get_fields().items():
                input_name = f"config_{section_key}_{field_name}"

                # Skip if field wasn't changed
                if input_name not in changed_fields:
                    continue

                # Get and process value
                processed_value = self._get_processed_value(request, field, input_name)

                # Use the accessor to set the value (dot notation)
                full_path = f"{app_label}.{section_key}.{field_name}"
                config.set(full_path, processed_value)
                saved_count += 1

        if saved_count > 0:
            messages.success(
                request,
                f"Configuration saved successfully. ({saved_count} setting{'s' if saved_count != 1 else ''} updated)",
            )
        else:
            messages.info(request, "No changes to save.")

        return redirect("config:app_detail", app_label=app_label)

    def _get_processed_value(self, request, field, input_name: str):
        """
        Get and process a value from POST data.

        Args:
            request: The Django request object
            field: The Field instance
            input_name: The HTML input name

        Returns:
            The processed value in its appropriate Python type
        """
        raw_value = request.POST.get(input_name)
        frontend_model = field.get_frontend_model_instance()
        return frontend_model.get_value(raw_value)

    def _build_sections_data(self, app_label: str, config_def) -> list[dict]:
        """Build the sections data structure for the template."""
        # Fetch all stored values for this app
        stored_values = {
            cv.path: cv.value for cv in ConfigValue.objects.filter(app_label=app_label)
        }

        sections_data = []
        for section_name, section in config_def.get_sections():
            section_key = section_name.lower()
            fields_data = []

            for field_name, field in section.get_fields().items():
                # DB path uses dot notation
                db_path = f"{section_key}.{field_name}"

                # Get stored value or use default
                stored_value = stored_values.get(db_path)
                if stored_value is None:
                    current_value = field.default
                else:
                    current_value = stored_value

                # Get the frontend model and render the input
                frontend_model = field.get_frontend_model_instance(current_value)

                fields_data.append(
                    {
                        "name": field_name,
                        "field": field,
                        "rendered_input": frontend_model.render(),
                        "has_stored_value": stored_value is not None,
                    }
                )

            sections_data.append(
                {
                    "name": section_name,
                    "label": section.label or section_name,
                    "sort_order": section.sort_order,
                    "fields": fields_data,
                }
            )

        return sections_data
