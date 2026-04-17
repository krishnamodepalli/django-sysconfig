import pytest

from django_sysconfig import override_sysconfig
from django_sysconfig.accessor import config
from django_sysconfig.models import ConfigValue
from django_sysconfig.registry import config_registry

pytestmark = pytest.mark.django_db


def test_override_sysconfig_decorator():
    @override_sysconfig(testapp__general__enabled=False)
    def inner_test():
        assert config.get("testapp.general.enabled") is False

    assert config.get("testapp.general.enabled") is True
    inner_test()
    assert config.get("testapp.general.enabled") is True


def test_override_sysconfig_context_manager():
    assert config.get("testapp.general.enabled") is True
    with override_sysconfig(testapp__general__enabled=False):
        assert config.get("testapp.general.enabled") is False
    assert config.get("testapp.general.enabled") is True


def test_override_sysconfig_short_name():
    # 'enabled' should resolve to 'testapp.general.enabled'
    # 'max_items' should resolve to 'testapp.general.max_items'
    assert config.get("testapp.general.max_items") == 10
    with override_sysconfig(max_items=50):
        assert config.get("testapp.general.max_items") == 50
    assert config.get("testapp.general.max_items") == 10


def test_override_sysconfig_creates_and_cleans_up():
    assert ConfigValue.objects.filter(path="general.enabled").count() == 1

    with override_sysconfig(testapp__general__enabled=False):
        assert (
            ConfigValue.objects.filter(path="general.enabled", value="false").count()
            == 1
        )

    assert ConfigValue.objects.filter(path="general.enabled", value="true").count() == 1


def test_reset_to_defaults():
    config.set("testapp.general.enabled", False)
    assert config.get("testapp.general.enabled") is False

    config_registry.reset_to_defaults()
    assert config.get("testapp.general.enabled") is True
    assert ConfigValue.objects.count() == 0
