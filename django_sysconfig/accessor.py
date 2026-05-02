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

from collections.abc import Callable
from typing import Any

from .cache import config_cache
from .exceptions import (
    AppNotFoundError,
    ConfigValidationError,
    ConfigValueError,
    FieldNotFoundError,
    InvalidPathError,
)
from .models import ConfigValue
from .registry import Field, config_registry


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
        if len(parts) != 3 or any(not part for part in parts):
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
        if len(parts) != 2 or any(not part for part in parts):
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

        registry_path = f"{section}.{field}"
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

    def get(self, path: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        The value is automatically cast to the appropriate type based on
        the FrontendModel defined for this field.

        Args:
            path: Full path like 'todo.general.max_todos_per_user'
            default: Fallback returned when the field is registered but has no
                     value in the database and no field-level default defined.
                     Invalid paths and unknown apps/fields always raise — they
                     are never silently swallowed.

        Returns:
            The typed configuration value

        Raises:
            InvalidPathError: If path format is invalid (always raised)
            AppNotFoundError: If app has no registered config (always raised)
            FieldNotFoundError: If field doesn't exist (always raised)
        """
        app_label, section, field_name = self._parse_path(path)
        field = self._get_field(app_label, section, field_name)

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
            # No DB value - use field default if available
            if field.default is not None:
                # Serialize and cache the default value
                frontend_model = field.get_frontend_model_instance()
                serialized_default = frontend_model.serialize_value(field.default)
                config_cache.set(path, serialized_default)
                return field.default
            # Field has no default - return caller's fallback (None by default)
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
        from django.db import transaction

        with transaction.atomic():
            cache_refresh, callbacks = self._set_value_internal(path, value)
            transaction.on_commit(cache_refresh)
            transaction.on_commit(callbacks)

    def set_many(
        self, values: dict[str, Any], skip_on_save_callbacks: bool = False
    ) -> int:
        """
        Set multiple configuration values at once.

        All writes are performed within a single transaction. If any write fails,
        the entire batch is rolled back. on_save callbacks are fired sequentially
        only after the transaction commits successfully.

        Args:
            values (dict[str, Any]): Dict mapping full paths to values.
            skip_on_save_callbacks (bool): If True, on_save callbacks are suppressed
                for all fields in this batch. Useful for bulk imports or environment
                cloning where side effects are undesirable. Defaults to False.

        Returns:
            int: Number of values set.

        Raises:
            InvalidPathError: If any path format is invalid.
            AppNotFoundError: If any app has no registered config.
            FieldNotFoundError: If any field does not exist.
            ConfigValueError: If any value cannot be serialized.
            ConfigValidationError: If any value fails field validation.
        """
        from django.db import transaction

        with transaction.atomic():
            callbacks_to_register = []

            for path, value in values.items():
                cache_refresh_callback, on_save_callback = self._set_value_internal(
                    path, value
                )
                transaction.on_commit(cache_refresh_callback)

                if not skip_on_save_callbacks:
                    callbacks_to_register.append(on_save_callback)

            for callback in callbacks_to_register:
                transaction.on_commit(callback)

        return len(values)

    def _set_value_internal(
        self, path: str, value: Any
    ) -> tuple[Callable[[], None], Callable[[], None]]:
        """
        Internal implementation of setting a configuration value.

        Performs validation, serialization, and database write. Returns two
        callbacks intended to be registered with transaction.on_commit:
          - on_commit_cache_refresh: repopulates the cache
          - on_commit_callback: dispatches the field's on_save hook if defined

        Both callbacks must only be executed after the transaction commits
        successfully to ensure cache always reflects durable DB state.
        """
        app_label, section, field_name = self._parse_path(path)
        field = self._get_field(app_label, section, field_name)

        # Run field validators before doing anything else.
        if field.validators:
            from .validators import validate_value

            field_label = field.label or field_name
            errors = validate_value(value, field.validators, field_label)
            if errors:
                raise ConfigValidationError(path, errors)

        try:
            serialized = self._serialize(field, value)
        except Exception as e:
            raise ConfigValueError(path, value, str(e)) from e

        db_path = self._to_db_path(section, field_name)

        # Fetch old value before the write so on_save receives the previous state.
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

        def on_commit_cache_refresh():
            # Cache the new value immediately to avoid cache miss on next read
            config_cache.set(path, serialized)

        def on_commit_callback():
            # Dispatch on_save hook if the field defines one.
            if field.on_save:
                field.on_save(path, value, old_value)

        return on_commit_cache_refresh, on_commit_callback

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
        for section_key, section_class in config_def.get_sections():
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
        return all_config.get(section, {})

    def exists(self, path: str) -> bool:
        """
        Check if a configuration path exists (is registered).

        Args:
            path: Full path like 'todo.general.max_todos_per_user'

        Returns:
            True if the field is registered, False otherwise

        Raises:
            InvalidPathError: If ``path`` is not a valid three-segment path.
                A malformed path is a programmer error, not a "not found"
                condition, and is left to propagate so callers can catch
                bad path strings early.
        """
        try:
            app_label, section, field_name = self._parse_path(path)

            # This ensures the config exists in the registry singleton object
            self._get_field(app_label, section, field_name)

            return True
        except (AppNotFoundError, FieldNotFoundError):
            return False

    def is_set(self, path: str) -> bool:
        """
        Check if a configuration value has been explicitly set in the database.

        Args:
            path: Full path like 'todo.general.max_todos_per_user'

        Returns:
            True if value exists in database with a non-empty value, False if using default
        """
        if not self.exists(path):
            return False

        app_label, section, field_name = self._parse_path(path)
        db_path = self._to_db_path(section, field_name)

        try:
            config_value = ConfigValue.objects.get(
                app_label=app_label,
                path=db_path,
            )
            # Check if value is not None and not empty string
            return config_value.value is not None and config_value.value != ""
        except ConfigValue.DoesNotExist:
            return False

    def reset(self, path: str) -> None:
        """
        Reset a configuration value to its field default.

        Sets the DB row back to the field's default value using the standard
        set() path — handles serialization, cache refresh, and on_save dispatch.

        Args:
            path: Full path like 'todo.general.max_todos_per_user'

        Raises:
            InvalidPathError: If path format is invalid
            AppNotFoundError: If app has no registered config
            FieldNotFoundError: If field doesn't exist
        """
        app_label, section, field_name = self._parse_path(path)
        field = self._get_field(app_label, section, field_name)

        self.set(path, field.default)


# Global config accessor instance
config = ConfigAccessor()
