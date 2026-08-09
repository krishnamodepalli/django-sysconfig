"""
Tests for the configuration registry.

Covers:
- Singleton identity
- app_label validation (ImproperlyConfigured)
- Field name validation (ImproperlyConfigured)
- Section class name -> snake_case normalisation
- Field path assignment (dot notation, no slashes)
- DB row creation on registration
- AppConfigDefinition.get_field() lookup
- get_sections() sort order
"""

import pytest
from django.core.exceptions import ImproperlyConfigured

from django_sysconfig.frontend_models import StringFrontendModel
from django_sysconfig.models import ConfigValue
from django_sysconfig.registry import (
    AppConfigDefinition,
    ConfigRegistry,
    Field,
    Section,
    config_registry,
)

# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------


class TestRegistrySingleton:

    def test_same_instance(self):
        assert ConfigRegistry() is ConfigRegistry()

    def test_global_matches_direct_instantiation(self):
        assert config_registry is ConfigRegistry()


# ---------------------------------------------------------------------------
# app_label validation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "bad_label",
    [
        "MyApp",  # PascalCase
        "myApp",  # camelCase
        "my-app",  # hyphen
        "my app",  # space
        "123app",  # starts with digit
        "MYAPP",  # uppercase
    ],
)
class TestAppLabelValidation:

    def test_raises_improperly_configured(self, bad_label):
        with pytest.raises(ImproperlyConfigured):
            config_registry.register(bad_label, type("Cfg", (), {}))


# ---------------------------------------------------------------------------
# Field name validation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "bad_name",
    [
        "MyField",  # PascalCase
        "myField",  # camelCase
        "my-field",  # hyphen
        "my field",  # space
        "123field",  # starts with digit
        "FIELD",  # uppercase
    ],
)
class TestFieldNameValidation:

    def test_raises_improperly_configured(self, bad_name):
        with pytest.raises(ImproperlyConfigured):
            type("BadSection", (Section,), {bad_name: Field(StringFrontendModel)})


# ---------------------------------------------------------------------------
# Section name normalisation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "class_name, expected_key",
    [
        ("General", "general"),
        ("PaymentSettings", "payment_settings"),
        ("APIConfig", "api_config"),
        ("HTTPSRedirect", "https_redirect"),
        ("AdvancedOptions", "advanced_options"),
    ],
)
class TestSectionNormalisation:

    def test_section_key_is_snake_case(self, class_name, expected_key):
        SectionCls = type(class_name, (Section,), {"label": "", "sort_order": 0})
        ConfigCls = type("Cfg", (), {class_name: SectionCls})
        config_def = AppConfigDefinition("dummy_app", ConfigCls)
        assert expected_key in config_def.sections


# ---------------------------------------------------------------------------
# Field path assignment
# ---------------------------------------------------------------------------


class TestFieldPaths:

    def test_field_paths_use_dot_notation(self):
        config_def = config_registry.get_config("testapp")
        for section_key, section in config_def.sections.items():
            for field_name, field in section.get_fields().items():
                assert field.path == f"{section_key}.{field_name}"

    def test_field_path_contains_no_slashes(self):
        config_def = config_registry.get_config("testapp")
        for _, section in config_def.sections.items():
            for _, field in section.get_fields().items():
                assert "/" not in field.path

    def test_multi_word_section_field_path(self):
        class PaymentSettings(Section):
            api_key = Field(StringFrontendModel, label="API Key")

        Cfg = type("Cfg", (), {"PaymentSettings": PaymentSettings})
        config_def = AppConfigDefinition("dummy_app", Cfg)
        field = config_def.sections["payment_settings"].get_fields()["api_key"]
        assert field.path == "payment_settings.api_key"


# ---------------------------------------------------------------------------
# DB row creation
# ---------------------------------------------------------------------------


class TestDBRowCreation:

    def test_rows_created_for_all_fields(self):
        # testapp: 6 fields in General + 3 in Advanced
        assert ConfigValue.objects.filter(app_label="testapp").count() == 9

    def test_row_path_uses_dot_notation(self):
        for row in ConfigValue.objects.filter(app_label="testapp"):
            assert "." in row.path
            assert "/" not in row.path

    def test_existing_row_not_overwritten_on_re_register(self):
        row = ConfigValue.objects.get(app_label="testapp", path="general.site_name")
        row.value = "Custom Value"
        row.save()

        from tests.conftest import make_test_config

        config_registry._ensure_db_records(
            "testapp",
            AppConfigDefinition("testapp", make_test_config()),
        )

        row.refresh_from_db()
        assert row.value == "Custom Value"


# ---------------------------------------------------------------------------
# AppConfigDefinition.get_field() lookup
# ---------------------------------------------------------------------------


class TestGetField:

    def test_returns_correct_field(self):
        config_def = config_registry.get_config("testapp")
        field = config_def.get_field("general.site_name")
        assert field is not None
        assert field.name == "site_name"

    def test_returns_none_for_unknown_section(self):
        config_def = config_registry.get_config("testapp")
        assert config_def.get_field("unknown.site_name") is None

    def test_returns_none_for_unknown_field(self):
        config_def = config_registry.get_config("testapp")
        assert config_def.get_field("general.unknown_field") is None

    def test_resolves_after_section_normalisation(self):
        class PaymentSettings(Section):
            api_key = Field(StringFrontendModel, label="API Key")

        Cfg = type("Cfg", (), {"PaymentSettings": PaymentSettings})
        config_registry.register("payments", Cfg)
        config_def = config_registry.get_config("payments")
        field = config_def.get_field("payment_settings.api_key")
        assert field is not None
        assert field.name == "api_key"

    def test_get_config_returns_none_for_unknown_app(self):
        assert config_registry.get_config("nonexistent") is None


# ---------------------------------------------------------------------------
# get_sections() sort order
# ---------------------------------------------------------------------------


class TestSectionSortOrder:

    def test_sections_ordered_by_sort_order(self):
        config_def = config_registry.get_config("testapp")
        orders = [section.sort_order for _, section in config_def.get_sections()]
        assert orders == sorted(orders)

    def test_custom_sort_order_respected(self):
        class Beta(Section):
            sort_order = 20
            value = Field(StringFrontendModel)

        class Alpha(Section):
            sort_order = 10
            value = Field(StringFrontendModel)

        Cfg = type("Cfg", (), {"Beta": Beta, "Alpha": Alpha})
        config_def = AppConfigDefinition("dummy_app", Cfg)
        keys = [key for key, _ in config_def.get_sections()]
        assert keys == ["alpha", "beta"]


# ---------------------------------------------------------------------------
# get_fields() immutability
# ---------------------------------------------------------------------------


class TestGetFieldsImmutability:

    def test_mutating_returned_dict_does_not_affect_registry(self):
        config_def = config_registry.get_config("testapp")
        section = config_def.sections["general"]

        fields = section.get_fields()
        fields["injected"] = Field(StringFrontendModel)

        assert "injected" not in section.get_fields()

    def test_returns_new_dict_each_call(self):
        config_def = config_registry.get_config("testapp")
        section = config_def.sections["general"]

        assert section.get_fields() is not section.get_fields()
