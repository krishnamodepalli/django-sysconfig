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
    """Return a fresh isolated registry instance that does not touch the singleton."""

    class _IsolatedRegistry(ConfigRegistry):
        _instance = None  # own singleton slot, separate from ConfigRegistry._instance

    r = _IsolatedRegistry()
    r._configs = {}
    return r


# ---------------------------------------------------------------------------
# Field name normalisation
# ---------------------------------------------------------------------------


class TestFieldNormalisation:
    """Field names are normalised to snake_case by SectionMeta at definition time."""

    @pytest.mark.parametrize(
        "attr_name, expected_key",
        [
            ("siteURL", "site_url"),
            ("MaxItems", "max_items"),
            ("already_normalised", "already_normalised"),
        ],
    )
    def test_field_name_normalised_to_snake_case(self, attr_name, expected_key):
        MySection = type(
            "MySection",
            (Section,),
            {attr_name: Field(StringFrontendModel, label="Test")},
        )

        assert expected_key in MySection._fields
        assert MySection._fields[expected_key].name == expected_key
        assert attr_name not in MySection._fields or attr_name == expected_key

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

    def test_get_fields_returns_normalised_keys(self):
        class MySection(Section):
            siteURL = Field(StringFrontendModel, label="Site URL")
            MaxItems = Field(IntegerFrontendModel, label="Max Items")

        fields = MySection.get_fields()
        assert set(fields.keys()) == {"site_url", "max_items"}


# ---------------------------------------------------------------------------
# Section name normalisation
# ---------------------------------------------------------------------------


class TestSectionNormalisation:
    """Section class names are normalised to snake_case at AppConfigDefinition init."""

    @pytest.mark.parametrize(
        "class_name, expected_key",
        [
            ("PaymentSettings", "payment_settings"),
            ("General", "general"),
            ("SMS", "sms"),
            ("APIKeys", "api_keys"),
        ],
    )
    def test_section_name_normalised_to_snake_case(self, class_name, expected_key):
        SectionClass = type(
            class_name,
            (Section,),
            {
                "label": class_name,
                "site_name": Field(StringFrontendModel, label="Site Name"),
            },
        )
        config_def = AppConfigDefinition(
            "myapp", type("MyConfig", (), {class_name: SectionClass})
        )

        assert expected_key in config_def.sections
        assert class_name not in config_def.sections or class_name == expected_key

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

    @pytest.mark.parametrize(
        "app_label, expected",
        [
            ("MyApp", "my_app"),
            ("myApp", "my_app"),
            ("my_app", "my_app"),
        ],
    )
    def test_app_label_normalised_to_snake_case(self, app_label, expected):
        config_def = AppConfigDefinition(app_label, type("C", (), {}))
        assert config_def.app_label == expected

    @pytest.mark.parametrize("lookup", ["MyApp", "myApp", "my_app"])
    def test_registry_normalises_on_register_and_lookup(self, lookup):
        class MyConfig:
            class General(Section):
                label = "General"
                site_name = Field(StringFrontendModel, label="Site Name")

        r = make_registry()
        r.register("MyApp", MyConfig)

        assert "my_app" in r._configs
        assert "MyApp" not in r._configs
        assert r.get_config(lookup) is not None

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

    @pytest.mark.parametrize(
        "section_name, field_attr, expected_path",
        [
            ("PaymentSettings", "siteURL", "payment_settings/site_url"),
            ("General", "site_name", "general/site_name"),
        ],
    )
    def test_field_path_uses_normalised_segments(
        self, section_name, field_attr, expected_path
    ):
        section_key, field_key = expected_path.split("/")
        SectionClass = type(
            section_name,
            (Section,),
            {
                "label": section_name,
                field_attr: Field(StringFrontendModel, label="Test"),
            },
        )
        config_def = AppConfigDefinition(
            "myapp", type("MyConfig", (), {section_name: SectionClass})
        )

        field = config_def.sections[section_key].get_fields()[field_key]
        assert field.path == expected_path

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
