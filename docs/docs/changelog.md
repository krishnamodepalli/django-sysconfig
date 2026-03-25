# Changelog

All notable changes to `django-sysconfig` are documented here.

This project follows [Semantic Versioning](https://semver.org/): `MAJOR.MINOR.PATCH`.

- **MAJOR** — breaking changes to the public API
- **MINOR** — new features, backwards compatible
- **PATCH** — bug fixes, backwards compatible

---

<!--
    INSTRUCTIONS FOR MAINTAINER:
    Add a new section for each release above the previous ones.
    Use the format below. Keep the Unreleased section at the top.
    Move items from Unreleased to a versioned section when you cut a release.
-->

## [Unreleased]

### Added
- *(nothing yet)*

### Changed
- *(nothing yet)*

### Fixed
- *(nothing yet)*

---

## [0.1.0] — Initial release

### Added

- `ConfigRegistry` — global in-memory schema store, populated via `@register_config(...)` decorator
- `Section` and `Field` base classes for defining configuration schemas in `sysconfig.py` files
- Autodiscovery via `django.utils.module_loading.autodiscover_modules("sysconfig")`
- `ConfigAccessor` with `get`, `set`, `set_many`, `all`, `section`, `exists`, and `is_set` methods
- Seven built-in field types: `StringFrontendModel`, `TextareaFrontendModel`, `IntegerFrontendModel`, `DecimalFrontendModel`, `BooleanFrontendModel`, `SelectFrontendModel`, `SecretFrontendModel`
- Fernet encryption at rest for `SecretFrontendModel` fields, keyed from `SECRET_KEY`
- 20 built-in validators: `NotEmptyValidator`, `NotBlankValidator`, `MinLengthValidator`, `MaxLengthValidator`, `RegexValidator`, `SlugValidator`, `JsonValidator`, `RangeValidator`, `PositiveValidator`, `NonNegativeValidator`, `PortValidator`, `EmailValidator`, `UrlValidator`, `IPv4Validator`, `IPv6Validator`, `IPAddressValidator`, `HostnameValidator`, `DomainValidator`, `ChoiceValidator`, `PathValidator`
- `on_save` callback support on `Field` definitions
- Django cache framework integration with explicit cache invalidation on write
- `ConfigAppListView` and `ConfigAppDetailView` staff-only admin views
- Django admin index page banner linking to the config UI
- `ConfigValue` database model for storing serialized values
- Full exception hierarchy: `ConfigError`, `InvalidPathError`, `AppNotFoundError`, `FieldNotFoundError`, `ConfigValueError`
- `validate_value()` helper for running validators outside of `config.set(...)`

---

[Unreleased]: https://github.com/krishnamodepalli/django-sysconfig/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/krishnamodepalli/django-sysconfig/releases/tag/v0.1.0
