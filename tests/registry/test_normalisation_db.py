"""
Tests for snake_case normalisation at the database level.

Verifies that ConfigValue rows are created and looked up using normalised
snake_case keys — not the original PascalCase or camelCase names.

Covers:
- DB rows created with normalised app_label
- DB rows created with normalised section.field path
- No rows created with collapsed / un-normalised keys
- config.get() works with the canonical normalised path
- config.set() writes to the normalised DB path
- config.exists() returns True for normalised paths only
"""

import pytest

from django_sysconfig.frontend_models import IntegerFrontendModel, StringFrontendModel
from django_sysconfig.models import ConfigValue
from django_sysconfig.registry import Field, Section

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

NORM_APP = "norm_test_app"  # expected normalised form used in DB and accessor paths
RAW_APP = (
    "NormTestApp"  # un-normalised label passed to register() to exercise normalisation
)


def make_normalisation_config():
    """Config with un-normalised PascalCase section and camelCase field names."""

    class NormTestConfig:
        class PaymentSettings(Section):
            label = "Payment Settings"
            sort_order = 10

            siteURL = Field(
                StringFrontendModel, label="Site URL", default="https://example.com"
            )
            maxItems = Field(IntegerFrontendModel, label="Max Items", default=50)

    return NormTestConfig


# ---------------------------------------------------------------------------
# DB row creation
# ---------------------------------------------------------------------------


class TestDbRowNormalisation:

    @pytest.fixture(autouse=True)
    def register_norm_config(self, db):
        """Register the normalisation test config fresh for each test."""
        from django_sysconfig.registry import config_registry

        config_registry.clear()
        from django.core.cache import cache

        cache.clear()

        norm_config = make_normalisation_config()
        config_registry.register(RAW_APP, norm_config)

        yield
        assert ConfigValue.objects.filter(app_label=NORM_APP).exists()

    def test_db_row_created_with_normalised_section_field_path(self):
        assert ConfigValue.objects.filter(
            app_label=NORM_APP,
            path="payment_settings.site_url",
        ).exists()

    def test_db_row_created_for_all_fields(self):
        paths = ConfigValue.objects.filter(app_label=NORM_APP).values_list(
            "path", flat=True
        )
        assert "payment_settings.site_url" in paths
        assert "payment_settings.max_items" in paths

    def test_no_row_created_with_collapsed_section_name(self):
        # "paymentsettings" is what .lower() would produce — must not exist
        assert not ConfigValue.objects.filter(
            app_label=NORM_APP,
            path__startswith="paymentsettings.",
        ).exists()

    def test_no_row_created_with_original_field_name(self):
        # "siteURL" and "maxItems" must not appear in DB paths
        assert not ConfigValue.objects.filter(
            app_label=NORM_APP,
            path__contains="siteURL",
        ).exists()
        assert not ConfigValue.objects.filter(
            app_label=NORM_APP,
            path__contains="maxItems",
        ).exists()

    def test_db_row_value_matches_field_default(self):
        row = ConfigValue.objects.get(
            app_label=NORM_APP,
            path="payment_settings.site_url",
        )
        assert row.value == "https://example.com"


# ---------------------------------------------------------------------------
# Accessor integration
# ---------------------------------------------------------------------------


class TestAccessorWithNormalisedPaths:

    @pytest.fixture(autouse=True)
    def register_norm_config(self, db):
        from django.core.cache import cache

        from django_sysconfig.registry import config_registry

        config_registry.clear()
        cache.clear()

        norm_config = make_normalisation_config()
        config_registry.register(RAW_APP, norm_config)

        yield
        from django_sysconfig.accessor import config

        value = config.get(f"{NORM_APP}.payment_settings.site_url")
        assert value == "https://example.com"

    def test_config_get_integer_with_normalised_path(self):
        from django_sysconfig.accessor import config

        value = config.get(f"{NORM_APP}.payment_settings.max_items")
        assert value == 50
        assert isinstance(value, int)

    def test_config_set_writes_to_normalised_db_path(self):
        from django_sysconfig.accessor import config

        config.set(f"{NORM_APP}.payment_settings.max_items", 99)

        row = ConfigValue.objects.get(
            app_label=NORM_APP,
            path="payment_settings.max_items",
        )
        assert row.value == "99"

    def test_config_exists_returns_true_for_normalised_path(self):
        from django_sysconfig.accessor import config

        assert config.exists(f"{NORM_APP}.payment_settings.site_url") is True
        assert config.exists(f"{NORM_APP}.payment_settings.max_items") is True

    def test_config_exists_returns_false_for_original_path(self):
        from django_sysconfig.accessor import config

        # Original un-normalised paths must not resolve
        assert config.exists(f"{NORM_APP}.PaymentSettings.siteURL") is False
        assert config.exists(f"{NORM_APP}.paymentsettings.siteURL") is False
