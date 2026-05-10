# Config app - Magento-style configuration system for Django
#
# Usage:
#     from django_sysconfig.accessor import config
#     value = config.get('todo.general.max_todos_per_user')
#
# Note: Import `config` from `config.accessor` to avoid circular imports
# during Django app initialization.

from .exceptions import (
    AppNotFoundError,
    ConfigError,
    ConfigValidationError,
    ConfigValueError,
    FieldNotFoundError,
    InvalidPathError,
)

__all__ = [
    "config",
    "AppNotFoundError",
    "ConfigError",
    "ConfigValidationError",
    "ConfigValueError",
    "FieldNotFoundError",
    "InvalidPathError",
]

__version__ = "1.0.1"


def __getattr__(name: str):
    """Lazy import for config accessor to avoid circular imports."""
    if name == "config":
        from .accessor import config

        return config
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
