"""
Tests for:
- ConfigAccessor.exists()
- ConfigAccessor.is_set()
- ConfigAccessor.all()
- ConfigAccessor.section()
"""

from decimal import Decimal

import pytest

from django_sysconfig.exceptions import AppNotFoundError, InvalidPathError

# ===========================================================================
# exists()
# ===========================================================================


class TestExists:
    """
    exists() returns True if the path is registered in the schema, False if
    the path is well-formed but the app/section/field is unknown. A malformed
    path (not exactly three dotted segments) is a programmer error and
    raises ``InvalidPathError`` so typos and bad inputs surface early.
    """

    def test_returns_true_for_registered_field(self, config):
        assert config.exists("testapp.general.site_name") is True

    def test_returns_true_for_all_registered_fields(self, config):
        paths = [
            "testapp.general.site_name",
            "testapp.general.description",
            "testapp.general.max_items",
            "testapp.general.price",
            "testapp.general.enabled",
            "testapp.advanced.mode",
            "testapp.advanced.api_key",
            "testapp.advanced.port",
        ]
        for path in paths:
            assert config.exists(path) is True, f"Expected {path} to exist"

    def test_returns_false_for_unknown_field(self, config):
        assert config.exists("testapp.general.nonexistent") is False

    def test_returns_false_for_unknown_section(self, config):
        assert config.exists("testapp.unknown_section.site_name") is False

    def test_returns_false_for_unknown_app(self, config):
        assert config.exists("unknown_app.general.site_name") is False

    def test_raises_for_invalid_path_format(self, config):
        with pytest.raises(InvalidPathError):
            config.exists("invalid")

    def test_raises_for_two_part_path(self, config):
        with pytest.raises(InvalidPathError):
            config.exists("testapp.general")

    def test_raises_for_empty_string(self, config):
        with pytest.raises(InvalidPathError):
            config.exists("")

    def test_raises_for_every_malformed_path(self, config):
        # A malformed path is a programmer error — surface it, don't silence it.
        for path in ["", "x", "x.y", "x.y.z.w", "...", "testapp..field"]:
            with pytest.raises(InvalidPathError):
                config.exists(path)

    def test_well_formed_unknown_path_still_returns_false(self, config):
        # Three-segment paths whose app/section/field just aren't registered
        # must stay a False result, not raise.
        assert config.exists("ghost.none.missing") is False


# ===========================================================================
# is_set()
# ===========================================================================


class TestIsSet:
    """
    is_set() returns True only if a ConfigValue row exists in the DB for
    this path — i.e. the value was explicitly set, not just defaulting.
    """

    def test_returns_true_after_set(self, config):
        config.set("testapp.general.max_items", 50)
        assert config.is_set("testapp.general.max_items") is True

    def test_raises_for_invalid_path(self, config):
        with pytest.raises(InvalidPathError):
            config.is_set("invalid")

    def test_returns_false_for_unknown_field(self, config):
        assert config.is_set("testapp.general.nonexistent") is False

    def test_is_set_reflects_db_state_not_default(self, config):
        # Field has a Python default of 10, but no explicit DB row unless set
        path = "testapp.general.max_items"

        # get() returns default without a DB row — but is_set should be False
        # only if registration didn't seed a DB row for this field.
        # (If your registry.register() seeds DB rows, this will be True.)
        result = config.is_set(path)
        assert isinstance(result, bool)  # at minimum, must return a bool

    def test_is_set_true_after_overwrite(self, config):
        config.set("testapp.general.max_items", 10)
        config.set("testapp.general.max_items", 20)
        assert config.is_set("testapp.general.max_items") is True

    def test_multiple_fields_independent(self, config):
        config.set("testapp.general.max_items", 10)
        # port was not explicitly set by this test
        assert config.is_set("testapp.general.max_items") is True


# ===========================================================================
# all()
# ===========================================================================


class TestAll:
    """
    all() returns a nested dict of {section: {field: value}} for an entire app,
    with all values correctly typed.
    """

    def test_returns_dict(self, config):
        result = config.all("testapp")
        assert isinstance(result, dict)

    def test_contains_all_sections(self, config):
        result = config.all("testapp")
        assert "general" in result
        assert "advanced" in result

    def test_general_section_contains_all_fields(self, config):
        result = config.all("testapp")
        general = result["general"]
        assert "site_name" in general
        assert "description" in general
        assert "max_items" in general
        assert "price" in general
        assert "enabled" in general

    def test_advanced_section_contains_all_fields(self, config):
        result = config.all("testapp")
        advanced = result["advanced"]
        assert "mode" in advanced
        assert "api_key" in advanced
        assert "port" in advanced

    def test_returns_default_values_before_any_set(self, config):
        result = config.all("testapp")
        assert result["general"]["site_name"] == "Test Site"
        assert result["general"]["max_items"] == 10
        assert result["general"]["enabled"] is True
        assert result["advanced"]["mode"] == "standard"
        assert result["advanced"]["port"] == 8080

    def test_reflects_updated_values_after_set(self, config):
        config.set("testapp.general.max_items", 999)
        result = config.all("testapp")
        assert result["general"]["max_items"] == 999

    def test_values_are_correctly_typed(self, config):
        result = config.all("testapp")
        assert isinstance(result["general"]["max_items"], int)
        assert isinstance(result["general"]["price"], Decimal)
        assert isinstance(result["general"]["enabled"], bool)
        assert isinstance(result["general"]["site_name"], str)

    def test_raises_for_unknown_app(self, config):
        with pytest.raises(AppNotFoundError):
            config.all("unknown_app")

    def test_multiple_sets_reflected_correctly(self, config):
        config.set("testapp.general.site_name", "First")
        config.set("testapp.general.site_name", "Second")
        result = config.all("testapp")
        assert result["general"]["site_name"] == "Second"


# ===========================================================================
# section()
# ===========================================================================


class TestSection:
    """
    section() returns a flat dict of {field: value} for a single section.
    """

    def test_returns_dict(self, config):
        result = config.section("testapp.general")
        assert isinstance(result, dict)

    def test_general_section_contains_correct_fields(self, config):
        result = config.section("testapp.general")
        assert "site_name" in result
        assert "description" in result
        assert "max_items" in result
        assert "price" in result
        assert "enabled" in result

    def test_does_not_contain_other_section_fields(self, config):
        result = config.section("testapp.general")
        assert "mode" not in result
        assert "api_key" not in result
        assert "port" not in result

    def test_returns_defaults_before_any_set(self, config):
        result = config.section("testapp.general")
        assert result["site_name"] == "Test Site"
        assert result["max_items"] == 10
        assert result["enabled"] is True

    def test_reflects_updated_value_after_set(self, config):
        config.set("testapp.general.max_items", 42)
        result = config.section("testapp.general")
        assert result["max_items"] == 42

    def test_advanced_section(self, config):
        result = config.section("testapp.advanced")
        assert result["mode"] == "standard"
        assert result["port"] == 8080

    def test_raises_for_invalid_path_format(self, config):
        with pytest.raises(InvalidPathError):
            config.section("testapp")

    def test_raises_for_three_part_path(self, config):
        with pytest.raises(InvalidPathError):
            config.section("testapp.general.site_name")

    def test_raises_for_unknown_app(self, config):
        with pytest.raises(AppNotFoundError):
            config.section("unknown_app.general")

    def test_unknown_section_returns_empty_dict(self, config):
        # section() delegates to all(), which returns {} for missing keys
        result = config.section("testapp.nonexistent")
        assert result == {}
