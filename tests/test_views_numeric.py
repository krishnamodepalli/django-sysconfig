"""Invalid numeric form submissions report an error and preserve the stored value."""

from types import SimpleNamespace

import pytest
from django.contrib.messages import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.urls import include, path

from django_sysconfig.models import ConfigValue
from django_sysconfig.views import ConfigAppDetailView

urlpatterns = [path("config/", include("django_sysconfig.urls"))]


@pytest.mark.parametrize(
    "field,raw,message",
    [
        ("max_items", "3.14", "Enter a valid integer."),
        ("price", "not-a-decimal", "Enter a valid decimal number."),
    ],
)
def test_invalid_numeric_submission_preserves_value(rf, settings, field, raw, message):
    """Exercise the real view, parser and database for integer and decimal input."""
    settings.ROOT_URLCONF = __name__
    row = ConfigValue.objects.get(app_label="testapp", path=f"general.{field}")
    original = row.value
    input_name = f"config_general_{field}"
    request = rf.post(
        "/config/testapp/", {"changed_fields": input_name, input_name: raw}
    )
    request.user = SimpleNamespace(is_authenticated=True, is_staff=True)
    request.session = {}
    request._messages = FallbackStorage(request)

    response = ConfigAppDetailView.as_view()(request, app_label="testapp")

    assert response.status_code == 302
    assert response.url == "/config/testapp/"
    assert [str(item) for item in get_messages(request)] == [message]
    row.refresh_from_db()
    assert row.value == original
