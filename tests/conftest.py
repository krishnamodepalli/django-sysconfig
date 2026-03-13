"""
Shared pytest fixtures for django-sysconfig tests.
"""

import pytest
from django.core.cache import cache as django_cache

from django_sysconfig.frontend_models import (
    BooleanFrontendModel,
    IntegerFrontendModel,
    SecretFrontendModel,
    StringFrontendModel,
)
from django_sysconfig.registry import Field, Section, config_registry, register_config
from django_sysconfig.validators import NotEmptyValidator, RangeValidator


@pytest.fixture(autouse=True)
def clean_state():
    """
    Ensure the registry and cache are isolated for every test.

    Runs before and after each test regardless of whether the test
    uses the registry — prevents singleton state from leaking across tests.
    """
    config_registry.clear()
    django_cache.clear()
    yield
    config_registry.clear()
    django_cache.clear()


@pytest.fixture
def registered_config(clean_state):
    """
    Register a realistic test config under the 'testapp' label.

    Yields the config class itself so tests can reference field metadata.
    Registry and cache cleanup is handled by clean_state (autouse).
    """

    @register_config("testapp")
    class TestAppConfig:
        class General(Section):
            label = "General Settings"
            sort_order = 10

            site_name = Field(
                StringFrontendModel,
                label="Site Name",
                default="Test Site",
            )
            max_items = Field(
                IntegerFrontendModel,
                label="Max Items",
                default=100,
                validators=[RangeValidator(min_value=1, max_value=9999)],
            )
            enabled = Field(
                BooleanFrontendModel,
                label="Enabled",
                default=True,
            )

        class Secrets(Section):
            label = "Secret Settings"
            sort_order = 20

            api_key = Field(
                SecretFrontendModel,
                label="API Key",
                validators=[NotEmptyValidator()],
            )

    yield TestAppConfig
