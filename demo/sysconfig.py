"""
Demo configuration for manual testing of django-sysconfig.

Registers a variety of field types and validators so the config admin UI
can be explored end-to-end during local development.

This file is auto-discovered by django_sysconfig on startup.
"""

from django_sysconfig.frontend_models import (
    BooleanFrontendModel,
    DecimalFrontendModel,
    IntegerFrontendModel,
    SecretFrontendModel,
    SelectFrontendModel,
    StringFrontendModel,
    TextareaFrontendModel,
)
from django_sysconfig.registry import Field, Section, register_config
from django_sysconfig.validators import (
    EmailValidator,
    MaxLengthValidator,
    MinLengthValidator,
    NotEmptyValidator,
    PortValidator,
    PositiveValidator,
    RangeValidator,
    UrlValidator,
)


@register_config("demo")
class DemoConfig:
    class General(Section):
        label = "General Settings"
        sort_order = 10

        site_name = Field(
            StringFrontendModel,
            label="Site Name",
            comment="The public name of the site shown in the browser tab.",
            default="My Django Site",
            validators=[NotEmptyValidator(), MaxLengthValidator(100)],
        )

        site_description = Field(
            TextareaFrontendModel,
            label="Site Description",
            comment="A short description used in meta tags.",
            default="A Django-powered website.",
            validators=[MaxLengthValidator(500)],
        )

        maintenance_mode = Field(
            BooleanFrontendModel,
            label="Maintenance Mode",
            comment="When enabled, visitors see a maintenance page.",
            default=False,
        )

        items_per_page = Field(
            IntegerFrontendModel,
            label="Items Per Page",
            comment="Number of items to show per page in list views.",
            default=20,
            validators=[RangeValidator(min_value=5, max_value=200)],
        )

    class Email(Section):
        label = "Email Settings"
        sort_order = 20

        sender_address = Field(
            StringFrontendModel,
            label="Sender Email Address",
            comment="The From address used for all outgoing emails.",
            default="noreply@example.com",
            validators=[NotEmptyValidator(), EmailValidator()],
        )

        smtp_host = Field(
            StringFrontendModel,
            label="SMTP Host",
            comment="Hostname of your SMTP server.",
            default="smtp.example.com",
            validators=[NotEmptyValidator()],
        )

        smtp_port = Field(
            IntegerFrontendModel,
            label="SMTP Port",
            comment="Port your SMTP server listens on (usually 25, 465, or 587).",
            default=587,
            validators=[PortValidator()],
        )

        smtp_password = Field(
            SecretFrontendModel,
            label="SMTP Password",
            comment="Stored encrypted at rest. Leave blank to keep the current value.",
        )

    class Api(Section):
        label = "API Settings"
        sort_order = 30

        api_base_url = Field(
            StringFrontendModel,
            label="API Base URL",
            comment="Base URL for outgoing API requests.",
            default="https://api.example.com",
            validators=[NotEmptyValidator(), UrlValidator()],
        )

        api_key = Field(
            SecretFrontendModel,
            label="API Key",
            comment="Third-party API key. Stored encrypted.",
        )

        request_timeout = Field(
            DecimalFrontendModel,
            label="Request Timeout (seconds)",
            comment="Maximum seconds to wait for an API response.",
            default="30.0",
            validators=[PositiveValidator()],
        )

        log_level = Field(
            SelectFrontendModel,
            label="Log Level",
            comment="Verbosity of API request logging.",
            default="WARNING",
            choices=[
                ("DEBUG", "Debug"),
                ("INFO", "Info"),
                ("WARNING", "Warning"),
                ("ERROR", "Error"),
            ],
        )

    class Advanced(Section):
        label = "Advanced"
        sort_order = 40

        cache_ttl = Field(
            IntegerFrontendModel,
            label="Cache TTL (seconds)",
            comment="How long to cache API responses. Set to 0 to disable.",
            default=300,
            validators=[RangeValidator(min_value=0, max_value=86400)],
        )

        allowed_origins = Field(
            TextareaFrontendModel,
            label="Allowed CORS Origins",
            comment="One origin per line, e.g. https://example.com",
            default="http://localhost:3000",
        )

        feature_flag_notes = Field(
            TextareaFrontendModel,
            label="Internal Notes",
            comment="Free-form notes for the development team. Not used by the app.",
        )
