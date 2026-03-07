"""
Custom exceptions for the config app.
"""


class ConfigError(Exception):
    """Base exception for all config-related errors."""

    pass


class ConfigNotFoundError(ConfigError):
    """Raised when a configuration path does not exist."""

    def __init__(self, path: str, message: str | None = None):
        self.path = path
        self.message = message or f"Configuration not found: {path}"
        super().__init__(self.message)


class AppNotFoundError(ConfigError):
    """Raised when an app has no registered configuration."""

    def __init__(self, app_label: str, message: str | None = None):
        self.app_label = app_label
        self.message = message or f"No configuration registered for app: {app_label}"
        super().__init__(self.message)


class SectionNotFoundError(ConfigError):
    """Raised when a section does not exist in an app's configuration."""

    def __init__(self, app_label: str, section: str, message: str | None = None):
        self.app_label = app_label
        self.section = section
        self.message = message or f"Section '{section}' not found in app: {app_label}"
        super().__init__(self.message)


class FieldNotFoundError(ConfigError):
    """Raised when a field does not exist in a section."""

    def __init__(self, path: str, message: str | None = None):
        self.path = path
        self.message = message or f"Field not found: {path}"
        super().__init__(self.message)


class InvalidPathError(ConfigError):
    """Raised when a configuration path is malformed."""

    def __init__(self, path: str, message: str | None = None):
        self.path = path
        self.message = (
            message
            or f"Invalid configuration path: {path}. Expected format: app.section.field"
        )
        super().__init__(self.message)


class ConfigValueError(ConfigError):
    """Raised when a configuration value is invalid."""

    def __init__(self, path: str, value, message: str | None = None):
        self.path = path
        self.value = value
        self.message = message or f"Invalid value for {path}: {value}"
        super().__init__(self.message)
