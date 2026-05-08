from typing import Any

from django.db import transaction

# We must defer importing registry/models/config until runtime
# to prevent AppRegistryNotReady since this is exported in __init__.py


def _resolve_config_path(key: str) -> str:
    """
    Resolve a keyword argument key to a full app.section.field path.
    If the key contains '__', it is treated as replacing '.'.
    Otherwise, it searches the registry for a unique field with that name.
    """
    if "__" in key:
        return key.replace("__", ".")

    from .registry import config_registry

    # Search for a short name
    matches = []
    for app_label, app_config in config_registry.get_all_configs().items():
        for section_key, section_class in app_config.get_sections():
            if key in section_class.get_fields():
                matches.append(f"{app_label}.{section_key}.{key}")

    if not matches:
        raise ValueError(f"Configuration key '{key}' not found in registry.")
    if len(matches) > 1:
        raise ValueError(
            f"Configuration key '{key}' is ambiguous. Found in: {', '.join(matches)}. "
            f"Use the full path with '__' (e.g. {matches[0].replace('.', '__')})."
        )
    return matches[0]


class override_sysconfig:
    """
    Decorator and context manager to temporarily override configuration values.

    Changes are persisted to the database and cache. Original values
    are restored when exiting the context.

    Usage as a context manager:
        with override_sysconfig(ENABLE_BETA_FEATURES=True, MAX_RETRIES=5):
            assert config.get('testapp.general.enabled') is True

    Usage as a decorator:
        @override_sysconfig(ENABLE_BETA_FEATURES=True)
        def test_beta_logic():
            pass
    """

    def __init__(self, **kwargs: Any):
        self.overrides = {}
        for k, v in kwargs.items():
            self.overrides[_resolve_config_path(k)] = v
        self.saved_state = {}

    def __enter__(self) -> "override_sysconfig":
        self._save_and_apply()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self._restore()

    def __call__(self, test_func: Any) -> Any:
        from functools import wraps

        @wraps(test_func)
        def inner(*args: Any, **kwargs: Any) -> Any:
            with self:
                return test_func(*args, **kwargs)

        return inner

    def _save_and_apply(self) -> None:
        from .accessor import config
        from .cache import config_cache
        from .models import ConfigValue

        for path, _ in self.overrides.items():
            # Check if there is an existing DB record for the field
            app_label = path.split(".")[0]
            db_path = ".".join(path.split(".")[1:])

            if ConfigValue.objects.filter(app_label=app_label, path=db_path).exists():
                self.saved_state[path] = config.get(path)
            else:
                self.saved_state[path] = config_cache.NOT_FOUND

        with transaction.atomic():
            for path, new_value in self.overrides.items():
                config.set(path, new_value)
                # In testing, transactions might not commit immediately, so we
                # manually invalidate the cache to ensure the next .get() sees the new value in DB
                config_cache.invalidate(path)

    def _restore(self) -> None:
        from .accessor import config
        from .cache import config_cache
        from .models import ConfigValue

        with transaction.atomic():
            for path, original_value in self.saved_state.items():
                if original_value is config_cache.NOT_FOUND:
                    # Reset to field default via delete since it didn't exist in DB before override
                    app_label = path.split(".")[0]
                    db_path = ".".join(path.split(".")[1:])
                    ConfigValue.objects.filter(
                        app_label=app_label, path=db_path
                    ).delete()
                    config_cache.invalidate(path)
                else:
                    config.set(path, original_value)
                    config_cache.invalidate(path)
