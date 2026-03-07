"""
Configuration Accessor

A clean, unified API for reading and writing configuration values.
Uses dot notation for paths: `app.section.field`

Usage:
    from django_sysconfig.accessor import config

    # Get a value (auto-casted to the correct type)
    max_todos = config.get('todo.general.max_todos_per_user')  # Returns int
    enabled = config.get('todo.general.allow_public_todos')    # Returns bool

    # Set a value
    config.set('todo.general.max_todos_per_user', 200)

    # Get with default (if field doesn't exist)
    value = config.get('todo.general.unknown_field', default=10)

    # Get all configs for an app
    all_todo = config.all('todo')

    # Get a section
    general = config.section('todo.general')
"""

from typing import Any

from .cache import config_cache
from .exceptions import (
    AppNotFoundError,
    ConfigValueError,
    FieldNotFoundError,
    InvalidPathError,
)
from .models import ConfigValue
from .registry import Field, config_registry

# Sentinel to distinguish between "no default provided" and an explicit default=None
_MISSING = object()


class ConfigAccessor:
    """
    Configuration accessor using dot notation paths.

    All paths follow the format: `app.section.field`
    Examples:
        - todo.general.max_todos_per_user
        - core.site.site_name
        - core.api.rate_limit
    """

    def _parse_path(self, path: str) -> tuple[str, str, str]:
        """
        Parse a dot-notation path into (app_label, section, field).

        Args:
            path: Full path like 'todo.general.max_todos_per_user'

        Returns:
            Tuple of (app_label, section, field)

        Raises:
            InvalidPathError: If path doesn't have exactly 3 parts
        """
        parts = path.split(".")
        if len(parts) != 3:
            raise InvalidPathError(
                path,
                f"Invalid path '{path}'. Expected format: app.section.field",
            )
        return parts[0], parts[1], parts[2]

    def _parse_app_section(self, path: str) -> tuple[str, str]:
        """
        Parse a path into (app_label, section).

        Args:
            path: Path like 'todo.general'

        Returns:
            Tuple of (app_label, section)

        Raises:
            InvalidPathError: If path doesn't have exactly 2 parts
        """
        parts = path.split(".")
        if len(parts) != 2:
            raise InvalidPathError(
                path,
                f"Invalid path '{path}'. Expected format: app.section",
            )
        return parts[0], parts[1]

    def _get_field(self, app_label: str, section: str, field: str) -> Field:
        """
        Get the field definition.

        Raises:
            AppNotFoundError: If app has no registered config
            FieldNotFoundError: If field doesn't exist
        """
        config_def = config_registry.get_config(app_label)
        if not config_def:
            raise AppNotFoundError(app_label)

        # Registry uses slash notation internally
        registry_path = f"{section}/{field}"
        field_def = config_def.get_field(registry_path)
        if not field_def:
            raise FieldNotFoundError(f"{app_label}.{section}.{field}")

        return field_def

    def _to_db_path(self, section: str, field: str) -> str:
        """Convert section and field to database path (dot notation)."""
        return f"{section}.{field}"

    def _deserialize(self, field: Field, raw_value: str | None) -> Any:
        """Deserialize a raw database value using the field's frontend model."""
        if raw_value is None:
            return field.default

        # Special handling for SecretFrontendModel - decrypt the value
        from .frontend_models import SecretFrontendModel

        if field.frontend_model is SecretFrontendModel:
            return SecretFrontendModel.decrypt_value(raw_value)

        frontend_model = field.get_frontend_model_instance(raw_value)
        return frontend_model.get_value(raw_value)

    def _serialize(self, field: Field, value: Any) -> str | None:
        """Serialize a value for database storage using the field's frontend model."""
        frontend_model = field.get_frontend_model_instance(value)
        return frontend_model.serialize_value(value)

    def get(self, path: str, default: Any = _MISSING) -> Any:
        """
        Get a configuration value.

        The value is automatically cast to the appropriate type based on
        the FrontendModel defined for this field.

        Args:
            path: Full path like 'todo.general.max_todos_per_user'
            default: Fallback if field doesn't exist (overrides field default).
                     Pass any value including None to suppress exceptions.

        Returns:
            The typed configuration value

        Raises:
            InvalidPathError: If path format is invalid
            AppNotFoundError: If app has no registered config (only if no default)
            FieldNotFoundError: If field doesn't exist (only if no default)
        """
        try:
            app_label, section, field_name = self._parse_path(path)
            field = self._get_field(app_label, section, field_name)
        except (InvalidPathError, AppNotFoundError, FieldNotFoundError):
            if default is not _MISSING:
                return default
            raise

        # First check cache
        cached_value = config_cache.get(path)
        if cached_value is not config_cache.NOT_FOUND:
            # Cache hit - deserialize the raw value
            return self._deserialize(field, cached_value)

        # Cache miss - query database
        db_path = self._to_db_path(section, field_name)

        try:
            config_value = ConfigValue.objects.get(
                app_label=app_label,
                path=db_path,
            )
            # Cache the raw database value
            config_cache.set(path, config_value.value)
            return self._deserialize(field, config_value.value)
        except ConfigValue.DoesNotExist:
            # No DB value - use default and cache it
            if field.default is not None:
                # Serialize and cache the default value
                frontend_model = field.get_frontend_model_instance()
                serialized_default = frontend_model.serialize_value(field.default)
                config_cache.set(path, serialized_default)
                return field.default
            # No default - cache None to avoid repeated DB queries
            config_cache.set(path, None)
            return default

    def set(self, path: str, value: Any) -> None:
        """
        Set a configuration value.

        The value is automatically serialized based on the FrontendModel
        defined for this field.

        Args:
            path: Full path like 'todo.general.max_todos_per_user'
            value: The value to set

        Raises:
            InvalidPathError: If path format is invalid
            AppNotFoundError: If app has no registered config
            FieldNotFoundError: If field doesn't exist
            ConfigValueError: If value cannot be serialized
        """
        app_label, section, field_name = self._parse_path(path)
        field = self._get_field(app_label, section, field_name)

        try:
            serialized = self._serialize(field, value)
        except Exception as e:
            raise ConfigValueError(path, value, str(e)) from e

        db_path = self._to_db_path(section, field_name)

        # Get old value before saving (for on_save callback)
        old_value = None
        if field.on_save:
            try:
                existing = ConfigValue.objects.get(app_label=app_label, path=db_path)
                old_value = self._deserialize(field, existing.value)
            except ConfigValue.DoesNotExist:
                old_value = field.default

        # Save to database
        ConfigValue.objects.update_or_create(
            app_label=app_label,
            path=db_path,
            defaults={"value": serialized},
        )

        # Invalidate cache after successful DB save
        config_cache.invalidate(path)

        # Cache the new value immediately to avoid cache miss on next read
        config_cache.set(path, serialized)

        # Call on_save callback if defined
        if field.on_save:
            field.on_save(path, value, old_value)

    def set_many(self, values: dict[str, Any]) -> int:
        """
        Set multiple configuration values at once.

        Args:
            values: Dict mapping full paths to values

        Returns:
            Number of values set

        Raises:
            InvalidPathError, AppNotFoundError, FieldNotFoundError, ConfigValueError
        """
        count = 0
        for path, value in values.items():
            self.set(path, value)
            count += 1
        return count

    def all(self, app_label: str) -> dict[str, dict[str, Any]]:
        """
        Get all configuration values for an app.

        Args:
            app_label: The app label (e.g., 'todo')

        Returns:
            Nested dict: {section: {field: typed_value, ...}, ...}

        Raises:
            AppNotFoundError: If app has no registered config
        """
        config_def = config_registry.get_config(app_label)
        if not config_def:
            raise AppNotFoundError(app_label)

        # Fetch all stored values
        stored = {
            cv.path: cv.value for cv in ConfigValue.objects.filter(app_label=app_label)
        }

        result = {}
        for section_name, section_class in config_def.get_sections():
            section_key = section_name.lower()
            section_data = {}

            for field_name, field in section_class.get_fields().items():
                db_path = self._to_db_path(section_key, field_name)
                raw_value = stored.get(db_path)
                section_data[field_name] = self._deserialize(field, raw_value)

            result[section_key] = section_data

        return result

    def section(self, path: str) -> dict[str, Any]:
        """
        Get all configuration values for a specific section.

        Args:
            path: Path like 'todo.general'

        Returns:
            Dict: {field: typed_value, ...}

        Raises:
            InvalidPathError: If path format is invalid
            AppNotFoundError: If app has no registered config
        """
        app_label, section = self._parse_app_section(path)
        all_config = self.all(app_label)
        return all_config.get(section.lower(), {})

    def exists(self, path: str) -> bool:
        """
        Check if a configuration path exists (is registered).

        Args:
            path: Full path like 'todo.general.max_todos_per_user'

        Returns:
            True if the field is registered, False otherwise
        """
        try:
            app_label, section, field_name = self._parse_path(path)
            self._get_field(app_label, section, field_name)
            return True
        except (InvalidPathError, AppNotFoundError, FieldNotFoundError):
            return False

    def is_set(self, path: str) -> bool:
        """
        Check if a configuration value has been explicitly set in the database.

        Args:
            path: Full path like 'todo.general.max_todos_per_user'

        Returns:
            True if value exists in database, False if using default
        """
        try:
            app_label, section, field_name = self._parse_path(path)
        except InvalidPathError:
            return False

        db_path = self._to_db_path(section, field_name)
        return ConfigValue.objects.filter(
            app_label=app_label,
            path=db_path,
        ).exists()


# Global config accessor instance
config = ConfigAccessor()
