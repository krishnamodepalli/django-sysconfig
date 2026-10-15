"""
Tests for frontend model value parsing.
"""

from decimal import Decimal
from types import SimpleNamespace

import pytest

from django_sysconfig.frontend_models import DecimalFrontendModel, IntegerFrontendModel

pytestmark = pytest.mark.no_db


def make_field():
    return SimpleNamespace(path="general.value", extra={})


class TestIntegerFrontendModel:

    def test_parses_integer_strings(self):
        model = IntegerFrontendModel(make_field())

        assert model.get_value("42") == 42

    def test_blank_input_remains_none(self):
        model = IntegerFrontendModel(make_field())

        assert model.get_value("") is None
        assert model.get_value(None) is None

    def test_raises_for_invalid_non_empty_input(self):
        model = IntegerFrontendModel(make_field())

        with pytest.raises(ValueError, match="valid integer"):
            model.get_value("3.14")


class TestDecimalFrontendModel:

    def test_parses_decimal_strings(self):
        model = DecimalFrontendModel(make_field())

        assert model.get_value("19.99") == Decimal("19.99")

    def test_blank_input_remains_none(self):
        model = DecimalFrontendModel(make_field())

        assert model.get_value("") is None
        assert model.get_value(None) is None

    def test_raises_for_invalid_non_empty_input(self):
        model = DecimalFrontendModel(make_field())

        with pytest.raises(ValueError, match="valid decimal"):
            model.get_value("not-a-decimal")
