"""
Configuration Registry Module

This module provides the core registration system for app configurations.
Configurations are defined in sysconfig.py files within each app and are
auto-discovered when Django starts.

Usage:
    # In your app's sysconfig.py
    from django_sysconfig.registry import register_config, Section, Field
    from django_sysconfig.frontend_models import StringFrontendModel, IntegerFrontendModel
    from django_sysconfig.validators import Required, EmailValidator, RangeValidator

    @register_config('myapp')
    class MyAppConfig:
        class General(Section):
            label = "General Settings"
            sort_order = 10

            some_setting = Field(
                StringFrontendModel,
                label='Some Setting',
                comment='Help text for this setting',
                default='default_value',
                validators=[Required()],
            )
"""

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

import django.db
from django.core.exceptions import ImproperlyConfigured

from .utils import is_snake_case, to_snake_case

if TYPE_CHECKING:
    from .frontend_models import BaseFrontendModel
    from .validators import BaseValidator


class Field:
    """
    Represents a configuration field.

    Metadata like label, comment, frontend_model, default are defined here
    in code and are NOT stored in the database. Only the actual value is
    stored in the ConfigValue model.
    """

    def __init__(
        self,
        frontend_model: "type[BaseFrontendModel]",
        label: str = "",
        comment: str = "",
        default: Any = None,
        sort_order: int = 0,
        validators: "list[BaseValidator] | None" = None,
        on_save: "Callable[[str, Any, Any], None] | None" = None,
        **kwargs,
    ):
        """
        Initialize a configuration field.

        Args:
            frontend_model: The FrontendModel class to use for rendering
                          (e.g., StringFrontendModel, IntegerFrontendModel)
            label: Human-readable label for the field
            comment: Help text/comment to assist in filling the config.
                    Supports HTML markup (e.g., <code>, <a>, <strong>).
            default: Default value if no value is stored in the database
            sort_order: Order in which to display this field within its section
            validators: List of validators to run before saving
                       (e.g., [Required(), EmailValidator()])
            on_save: Optional callback called when value is saved.
                    Signature: (path: str, new_value: Any, old_value: Any) -> None
            **kwargs: Additional arguments passed to the frontend model
                     (e.g., 'choices' for select fields)
        """
        self.frontend_model = frontend_model
        self.label = label
        self.comment = comment
        self.default = default
        self.sort_order = sort_order
        self.validators = validators or []
        self.on_save = on_save
        self.extra = kwargs

        # These will be set by the registry during registration
        self.name: str = ""
        self.path: str = ""
        self.full_path: str = ""
        self._section = ""
        self._app_label = ""

    @property
    def required(self) -> bool:
        """Check if this field has a NotEmptyValidator (i.e., is required)."""
        from .validators import NotEmptyValidator

        return any(isinstance(v, NotEmptyValidator) for v in self.validators)

    def get_frontend_model_instance(
        self, current_value: Any = None
    ) -> "BaseFrontendModel":
        """Create an instance of the frontend model for this field."""
        return self.frontend_model(self, current_value)

    def __repr__(self):
        model_name = getattr(self.frontend_model, "__name__", str(self.frontend_model))
        return f"Field(name={self.name!r}, frontend_model={model_name})"


class SectionMeta(type):
    """Metaclass for Section to collect Field instances."""

    def __new__(mcs, name, bases, namespace):
        fields = {}
        # Collect all Field instances from the class namespace
        for key, value in list(namespace.items()):
            if isinstance(value, Field):
                if not is_snake_case(key):
                    raise ImproperlyConfigured(
                        f"Field name '{key}' in section '{name}' must be snake_case "
                        f"(e.g. 'site_url', 'max_items')."
                    )
                value.name = key
                fields[key] = value

        namespace["_fields"] = fields
        return super().__new__(mcs, name, bases, namespace)


class Section(metaclass=SectionMeta):
    """
    Base class for configuration sections.

    Sections group related configuration fields together. Each section
    renders as a collapsible container in the admin UI.

    Attributes:
        label: Human-readable label for the section
        sort_order: Order in which to display this section (lower = first)
    """

    label: str = ""
    sort_order: int = 0
    _fields: dict[str, Field] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # Ensure each subclass has its own _fields dict
        cls._fields = {}
        for key, value in vars(cls).items():
            if isinstance(value, Field):
                if not is_snake_case(key):
                    raise ImproperlyConfigured(
                        f"Field name '{key}' in section '{cls.__name__}' must be snake_case "
                        f"(e.g. 'site_url', 'max_items')."
                    )
                value.name = key
                cls._fields[key] = value

    @classmethod
    def get_fields(cls) -> dict[str, Field]:
        """Return all fields in this section, sorted by sort_order."""
        return dict(sorted(cls._fields.items(), key=lambda x: (x[1].sort_order, x[0])))


class AppConfigDefinition:
    """
    Holds the parsed configuration definition for an app.

    This class is created by the registry when processing a config class
    decorated with @register_config.
    """

    def __init__(self, app_label: str, config_class: type):
        self.app_label = app_label
        self.config_class = config_class
        self.sections: dict[str, type[Section]] = {}

        # Extract sections from the config class
        for name in dir(config_class):
            if name.startswith("_"):
                continue
            attr = getattr(config_class, name)
            if (
                isinstance(attr, type)
                and issubclass(attr, Section)
                and attr is not Section
            ):
                # Set path for each field in the section
                section_key = to_snake_case(name)
                for field_name, field in attr.get_fields().items():
                    field._section = section_key
                    field._app_label = app_label
                    field.name = field_name
                    field.full_path = f"{app_label}.{section_key}.{field_name}"
                    field.path = f"{section_key}.{field_name}"
                self.sections[section_key] = attr

    def get_sections(self) -> list[tuple[str, type[Section]]]:
        """Return sections sorted by sort_order."""
        return sorted(
            self.sections.items(),
            key=lambda x: (x[1].sort_order, x[0]),
        )

    def get_field(self, path: str) -> Field | None:
        """Get a field by its path (e.g., 'general.max_todos')."""
        parts = path.split(".")
        if len(parts) != 2:
            return None

        section_key, field_name = parts
        section = self.sections.get(section_key)
        if section:
            return section.get_fields().get(field_name)
        return None


class ConfigRegistry:
    """
    Singleton registry that holds all registered app configurations.

    Configurations are registered via the @register_config decorator and
    are auto-discovered from sysconfig.py files in all installed apps.
    """

    _instance = None
    _configs: dict[str, AppConfigDefinition] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._configs = {}
        return cls._instance

    def register(self, app_label: str, config_class: type) -> None:
        """Register a configuration class for an app."""
        if not is_snake_case(app_label):
            raise ImproperlyConfigured(
                f"app_label '{app_label}' passed to @register_config must be snake_case "
                f"(e.g. 'my_app', 'user_preferences')."
            )
        config_def = AppConfigDefinition(app_label, config_class)
        self._configs[app_label] = config_def

        # Create DB records for all fields with default values
        self._ensure_db_records(app_label, config_def)

    def _ensure_db_records(
        self, app_label: str, config_def: AppConfigDefinition
    ) -> None:
        """
        Ensure database records exist for all config fields.

        Creates records with default values for fields that don't have
        a database entry yet.
        """
        try:
            from django.db import transaction

            from .models import ConfigValue

            with transaction.atomic():
                for section_key, section in config_def.get_sections():
                    for field_name, field in section.get_fields().items():
                        db_path = f"{section_key}.{field_name}"

                        # Serialize the default value
                        default_value = None
                        if field.default is not None:
                            frontend_model = field.get_frontend_model_instance()
                            default_value = frontend_model.serialize_value(
                                field.default
                            )

                        # Create only if doesn't exist (don't overwrite existing values)
                        ConfigValue.objects.get_or_create(
                            app_label=app_label,
                            path=db_path,
                            defaults={"value": default_value},
                        )
        except (
            django.db.utils.OperationalError,
            django.db.utils.ProgrammingError,
        ):
            # Silently ignore DB errors during startup (e.g., migrations not run yet)
            # This is expected during initial app loading before migrations are applied
            pass

    def get_config(self, app_label: str) -> AppConfigDefinition | None:
        """Get the configuration definition for an app."""
        return self._configs.get(app_label)

    def get_all_configs(self) -> dict[str, AppConfigDefinition]:
        """Get all registered configurations."""
        return self._configs.copy()

    def get_registered_apps(self) -> list[str]:
        """Get list of all apps with registered configurations."""
        return list(self._configs.keys())

    def clear(self) -> None:
        """Clear all registered configurations (useful for testing)."""
        self._configs.clear()


# Global registry instance
config_registry = ConfigRegistry()


def register_config(app_label: str):
    """
    Decorator to register a configuration class for an app.

    Usage:
        @register_config('myapp')
        class MyAppConfig:
            class General(Section):
                label = "General Settings"
                ...
    """

    def decorator(cls):
        config_registry.register(app_label, cls)
        return cls

    return decorator
