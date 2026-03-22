"""
Tests for snake_case normalisation of app labels, section names, and field names.

These are pure schema-level tests — no DB access required.
All normalisation happens at class definition / registration time.

Covers:
- Field names normalised at definition time via SectionMeta
- field.name and _fields dict both use the normalised key
- Section names normalised at registration time
- App labels normalised at registration time
- get_config() normalises the lookup input
- field.path uses fully normalised segments
- Idempotency — already-normalised names are unchanged
- Edge cases — consecutive caps (SMS, API, XML, S3)
"""

import pytest

from django_sysconfig.frontend_models import IntegerFrontendModel, StringFrontendModel
from django_sysconfig.registry import (
    AppConfigDefinition,
    ConfigRegistry,
    Field,
    Section,
)

pytestmark = pytest.mark.no_db


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_registry() -> ConfigRegistry:
    """Return a fresh isolated registry for each test."""
    r = ConfigRegistry.__new__(ConfigRegistry)
    r._configs = {}
    return r


# ---------------------------------------------------------------------------
# Field name normalisation
# ---------------------------------------------------------------------------


class TestFieldNormalisation:
    """Field names are normalised to snake_case by SectionMeta at definition time."""

    def test_camel_case_field_name(self):
        class MySection(Section):
            siteURL = Field(StringFrontendModel, label="Site URL")

        assert "site_url" in MySection._fields
        assert MySection._fields["site_url"].name == "site_url"

    def test_pascal_case_field_name(self):
        class MySection(Section):
            MaxItems = Field(IntegerFrontendModel, label="Max Items")

        assert "max_items" in MySection._fields
        assert MySection._fields["max_items"].name == "max_items"

    def test_already_snake_case_field_name(self):
        class MySection(Section):
            site_name = Field(StringFrontendModel, label="Site Name")

        assert "site_name" in MySection._fields
        assert MySection._fields["site_name"].name == "site_name"

    def test_original_attribute_name_not_in_fields(self):
        class MySection(Section):
            siteURL = Field(StringFrontendModel, label="Site URL")

        assert "siteURL" not in MySection._fields

    def test_multiple_fields_all_normalised(self):
        class MySection(Section):
            siteURL = Field(StringFrontendModel, label="Site URL")
            MaxItems = Field(IntegerFrontendModel, label="Max Items")
            already_normalised = Field(StringFrontendModel, label="Already")

        assert set(MySection._fields.keys()) == {
            "site_url",
            "max_items",
            "already_normalised",
        }

    def test_field_name_attribute_matches_dict_key(self):
        class MySection(Section):
            siteURL = Field(StringFrontendModel, label="Site URL")

        field = MySection._fields["site_url"]
        assert field.name == "site_url"

    def test_get_fields_returns_normalised_keys(self):
        class MySection(Section):
            siteURL = Field(StringFrontendModel, label="Site URL")
            MaxItems = Field(IntegerFrontendModel, label="Max Items")

        fields = MySection.get_fields()
        assert "site_url" in fields
        assert "max_items" in fields
        assert "siteURL" not in fields
        assert "MaxItems" not in fields


# ---------------------------------------------------------------------------
# Section name normalisation
# ---------------------------------------------------------------------------


class TestSectionNormalisation:
    """Section class names are normalised to snake_case at AppConfigDefinition init."""

    def test_multi_word_pascal_case_section(self):
        class MyConfig:
            class PaymentSettings(Section):
                label = "Payment Settings"
                site_name = Field(StringFrontendModel, label="Site Name")

        config_def = AppConfigDefinition("myapp", MyConfig)
        assert "payment_settings" in config_def.sections
        assert "PaymentSettings" not in config_def.sections

    def test_single_word_section(self):
        class MyConfig:
            class General(Section):
                label = "General"
                site_name = Field(StringFrontendModel, label="Site Name")

        config_def = AppConfigDefinition("myapp", MyConfig)
        assert "general" in config_def.sections

    def test_all_caps_section(self):
        class MyConfig:
            class SMS(Section):
                label = "SMS"
                site_name = Field(StringFrontendModel, label="Site Name")

        config_def = AppConfigDefinition("myapp", MyConfig)
        assert "sms" in config_def.sections

    def test_mixed_caps_section(self):
        class MyConfig:
            class APIKeys(Section):
                label = "API Keys"
                site_name = Field(StringFrontendModel, label="Site Name")

        config_def = AppConfigDefinition("myapp", MyConfig)
        assert "api_keys" in config_def.sections

    def test_multiple_sections_all_normalised(self):
        class MyConfig:
            class PaymentSettings(Section):
                label = "Payment"
                site_name = Field(StringFrontendModel, label="Site Name")

            class EmailNotifications(Section):
                label = "Email"
                site_name = Field(StringFrontendModel, label="Site Name")

            class General(Section):
                label = "General"
                site_name = Field(StringFrontendModel, label="Site Name")

        config_def = AppConfigDefinition("myapp", MyConfig)
        assert set(config_def.sections.keys()) == {
            "payment_settings",
            "email_notifications",
            "general",
        }

    def test_get_sections_returns_normalised_keys(self):
        class MyConfig:
            class PaymentSettings(Section):
                label = "Payment"
                sort_order = 10
                site_name = Field(StringFrontendModel, label="Site Name")

        config_def = AppConfigDefinition("myapp", MyConfig)
        section_keys = [key for key, _ in config_def.get_sections()]
        assert "payment_settings" in section_keys
        assert "PaymentSettings" not in section_keys


# ---------------------------------------------------------------------------
# App label normalisation
# ---------------------------------------------------------------------------


class TestAppLabelNormalisation:
    """App labels are normalised to snake_case at registration time."""

    def test_pascal_case_app_label(self):
        class MyConfig:
            class General(Section):
                label = "General"
                site_name = Field(StringFrontendModel, label="Site Name")

        config_def = AppConfigDefinition("MyApp", MyConfig)
        assert config_def.app_label == "my_app"

    def test_camel_case_app_label(self):
        config_def = AppConfigDefinition("myApp", type("C", (), {}))
        assert config_def.app_label == "my_app"

    def test_already_snake_case_app_label(self):
        config_def = AppConfigDefinition("my_app", type("C", (), {}))
        assert config_def.app_label == "my_app"

    def test_registry_stores_under_normalised_label(self):
        class MyConfig:
            class General(Section):
                label = "General"
                site_name = Field(StringFrontendModel, label="Site Name")

        r = make_registry()
        r.register("MyApp", MyConfig)
        assert "my_app" in r._configs
        assert "MyApp" not in r._configs

    def test_get_config_finds_by_normalised_label(self):
        class MyConfig:
            class General(Section):
                label = "General"
                site_name = Field(StringFrontendModel, label="Site Name")

        r = make_registry()
        r.register("MyApp", MyConfig)
        assert r.get_config("my_app") is not None

    def test_get_config_normalises_lookup_input(self):
        class MyConfig:
            class General(Section):
                label = "General"
                site_name = Field(StringFrontendModel, label="Site Name")

        r = make_registry()
        r.register("MyApp", MyConfig)

        # All of these should find the same config
        assert r.get_config("MyApp") is not None
        assert r.get_config("myApp") is not None
        assert r.get_config("my_app") is not None

    def test_get_registered_apps_returns_normalised_labels(self):
        class MyConfig:
            class General(Section):
                label = "General"
                site_name = Field(StringFrontendModel, label="Site Name")

        r = make_registry()
        r.register("MyApp", MyConfig)
        assert "my_app" in r.get_registered_apps()
        assert "MyApp" not in r.get_registered_apps()


# ---------------------------------------------------------------------------
# Field path normalisation
# ---------------------------------------------------------------------------


class TestFieldPathNormalisation:
    """field.path uses fully normalised snake_case segments."""

    def test_field_path_uses_normalised_section_and_field(self):
        class MyConfig:
            class PaymentSettings(Section):
                label = "Payment"
                siteURL = Field(StringFrontendModel, label="Site URL")

        config_def = AppConfigDefinition("MyApp", MyConfig)
        section = config_def.sections["payment_settings"]
        field = section.get_fields()["site_url"]
        assert field.path == "payment_settings/site_url"

    def test_field_path_already_normalised(self):
        class MyConfig:
            class General(Section):
                label = "General"
                site_name = Field(StringFrontendModel, label="Site Name")

        config_def = AppConfigDefinition("myapp", MyConfig)
        section = config_def.sections["general"]
        field = section.get_fields()["site_name"]
        assert field.path == "general/site_name"

    def test_get_field_finds_by_normalised_path(self):
        class MyConfig:
            class PaymentSettings(Section):
                label = "Payment"
                siteURL = Field(StringFrontendModel, label="Site URL")

        config_def = AppConfigDefinition("MyApp", MyConfig)
        field = config_def.get_field("payment_settings/site_url")
        assert field is not None
        assert field.name == "site_url"

    def test_get_field_returns_none_for_original_path(self):
        class MyConfig:
            class PaymentSettings(Section):
                label = "Payment"
                siteURL = Field(StringFrontendModel, label="Site URL")

        config_def = AppConfigDefinition("MyApp", MyConfig)
        # Original un-normalised path should not be found
        assert config_def.get_field("PaymentSettings/siteURL") is None


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------


class TestIdempotency:
    """Normalising already-normalised names produces the same result."""

    def test_snake_case_app_label_unchanged(self):
        config_def = AppConfigDefinition("my_app", type("C", (), {}))
        assert config_def.app_label == "my_app"

    def test_snake_case_section_unchanged(self):
        class MyConfig:
            class general(Section):
                label = "General"
                site_name = Field(StringFrontendModel, label="Site Name")

        config_def = AppConfigDefinition("myapp", MyConfig)
        assert "general" in config_def.sections

    def test_snake_case_field_unchanged(self):
        class MySection(Section):
            site_name = Field(StringFrontendModel, label="Site Name")

        assert "site_name" in MySection._fields
        assert MySection._fields["site_name"].name == "site_name"

    def test_register_twice_with_same_label(self):
        class MyConfig:
            class General(Section):
                label = "General"
                site_name = Field(StringFrontendModel, label="Site Name")

        r = make_registry()
        r.register("my_app", MyConfig)
        r.register("my_app", MyConfig)
        # Should still be one entry, not two
        assert len(r._configs) == 1


# ---------------------------------------------------------------------------
# Edge cases — consecutive caps
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Consecutive uppercase sequences are handled correctly."""

    def test_all_caps_single_word(self):
        class MyConfig:
            class SMS(Section):
                label = "SMS"
                enabled = Field(StringFrontendModel, label="Enabled")

        config_def = AppConfigDefinition("myapp", MyConfig)
        assert "sms" in config_def.sections

    def test_caps_prefix_then_word(self):
        class MyConfig:
            class APIKeys(Section):
                label = "API Keys"
                enabled = Field(StringFrontendModel, label="Enabled")

        config_def = AppConfigDefinition("myapp", MyConfig)
        assert "api_keys" in config_def.sections

    def test_digit_after_caps(self):
        class MyConfig:
            class S3Config(Section):
                label = "S3 Config"
                enabled = Field(StringFrontendModel, label="Enabled")

        config_def = AppConfigDefinition("myapp", MyConfig)
        assert "s3_config" in config_def.sections

    def test_xml_parser_section(self):
        class MyConfig:
            class XMLParser(Section):
                label = "XML Parser"
                enabled = Field(StringFrontendModel, label="Enabled")

        config_def = AppConfigDefinition("myapp", MyConfig)
        assert "xml_parser" in config_def.sections

    def test_consecutive_caps_field_name(self):
        class MySection(Section):
            parseHTTPSUrl = Field(StringFrontendModel, label="HTTPS URL")

        assert "parse_https_url" in MySection._fields

    def test_all_caps_field_name(self):
        class MySection(Section):
            URL = Field(StringFrontendModel, label="URL")

        assert "url" in MySection._fields
