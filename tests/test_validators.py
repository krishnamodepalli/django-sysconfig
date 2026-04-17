"""
Tests for all validators in django_sysconfig.validators.

These are pure unit tests — no DB, no registry, no cache.
"""

import pytest

from django_sysconfig.validators import (
    ChoiceValidator,
    DomainValidator,
    EmailValidator,
    HostnameValidator,
    IPAddressValidator,
    IPv4Validator,
    IPv6Validator,
    JsonValidator,
    MaxLengthValidator,
    MinLengthValidator,
    NonNegativeValidator,
    NotBlankValidator,
    NotEmptyValidator,
    PathValidator,
    PortValidator,
    PositiveValidator,
    RangeValidator,
    RegexValidator,
    SlugValidator,
    UrlValidator,
    ValidationError,
)

# Mark this whole file as "no_db"
pytestmark = pytest.mark.no_db

# ---------------------------------------------------------------------------
# NotEmptyValidator
# ---------------------------------------------------------------------------


class TestNotEmptyValidator:
    def setup_method(self):
        self.validator = NotEmptyValidator("The value provided is Empty")

    def test_none_is_empty(self):
        with pytest.raises(ValidationError):
            self.validator(None)

    def test_empty_string_is_empty(self):
        with pytest.raises(ValidationError):
            self.validator("")

    def test_empty_list_is_empty(self):
        with pytest.raises(ValidationError):
            self.validator([])

    def test_empty_dict_is_empty(self):
        with pytest.raises(ValidationError):
            self.validator({})

    def test_zero_is_not_empty(self):
        self.validator(0)

    def test_int_is_not_empty(self):
        self.validator(1)
        self.validator(2)
        self.validator(-1)

    def test_float_is_not_empty(self):
        self.validator(1.0)
        self.validator(-1.0)

    def test_bool_is_not_empty(self):
        self.validator(True)
        self.validator(False)


# ---------------------------------------------------------------------------
# NotBlankValidator
# ---------------------------------------------------------------------------


class TestNotBlankValidator:
    def setup_method(self):
        self.validator = NotBlankValidator()

    def test_empty_string_is_blank(self):
        with pytest.raises(ValidationError):
            self.validator("")

    def test_none_is_not_blank(self):
        self.validator(None)

    def test_empty_list_is_not_blank(self):
        self.validator([])

    def test_empty_dict_is_not_blank(self):
        self.validator({})

    def test_zero_is_not_blank(self):
        self.validator(0)

    def test_int_is_not_blank(self):
        self.validator(1)
        self.validator(2)
        self.validator(-1)

    def test_float_is_not_blank(self):
        self.validator(1.0)
        self.validator(-1.0)

    def test_bool_is_not_blank(self):
        self.validator(True)
        self.validator(False)


# ---------------------------------------------------------------------------
# MinLengthValidator
# ---------------------------------------------------------------------------


class TestMinLengthValidator:
    def setup_method(self):
        self.validator = MinLengthValidator(4)

    def test_min_length_must_be_more_than_one(self):
        with pytest.raises(ValidationError):
            MinLengthValidator(0)
        with pytest.raises(ValidationError):
            MinLengthValidator(-2)

    def test_does_not_validate_int(self):
        self.validator(1)
        self.validator(-100)

    def test_does_not_validate_float(self):
        self.validator(1.0)
        self.validator(-10.0)

    def test_none_skips_validation(self):
        self.validator(None)

    def test_string_length(self):
        self.validator("hello")

        with pytest.raises(ValidationError):
            self.validator("hi")


# ---------------------------------------------------------------------------
# MaxLengthValidator
# ---------------------------------------------------------------------------


class TestMaxLengthValidator:
    def setup_method(self):
        self.validator = MaxLengthValidator(5)

    def test_max_length_must_be_more_than_one(self):
        with pytest.raises(ValidationError):
            MaxLengthValidator(0)
        with pytest.raises(ValidationError):
            MaxLengthValidator(-2)

    def test_does_not_validate_int(self):
        self.validator(1)
        self.validator(-100)

    def test_does_not_validate_float(self):
        self.validator(1.0)
        self.validator(-10.0)

    def test_none_skips_validation(self):
        self.validator(None)

    def test_string_length(self):
        self.validator("hello")
        self.validator("hi")

        with pytest.raises(ValidationError):
            self.validator("hello world")


# ---------------------------------------------------------------------------
# RegexValidator
# ---------------------------------------------------------------------------


class TestRegexValidator:
    def setup_method(self):
        self.validator = RegexValidator(r"^[a-z]+$")

    def test_none_skips_validation(self):
        self.validator(None)

    def test_non_string_fails_validation(self):
        with pytest.raises(ValidationError):
            self.validator(123)
        with pytest.raises(ValidationError):
            self.validator([])

    def test_matching_pattern(self):
        self.validator("hello")
        self.validator("abc")

    def test_non_matching_pattern(self):
        with pytest.raises(ValidationError):
            self.validator("Hello")
        with pytest.raises(ValidationError):
            self.validator("hello123")

    def test_inverse_validator(self):
        inverse_validator = RegexValidator(r"^[a-z]+$", inverse=True)
        inverse_validator("Hello")
        inverse_validator("hello123")

        with pytest.raises(ValidationError):
            inverse_validator("hello")


# ---------------------------------------------------------------------------
# RangeValidator
# ---------------------------------------------------------------------------


class TestRangeValidator:
    def setup_method(self):
        self.validator = RangeValidator(min_value=1, max_value=10)

    def test_none_skips_validation(self):
        self.validator(None)

    def test_valid_range(self):
        self.validator(1)
        self.validator(5)
        self.validator(10)

    def test_below_minimum(self):
        with pytest.raises(ValidationError):
            self.validator(0)
        with pytest.raises(ValidationError):
            self.validator(-1)

    def test_above_maximum(self):
        with pytest.raises(ValidationError):
            self.validator(11)
        with pytest.raises(ValidationError):
            self.validator(100)

    def test_min_only(self):
        min_validator = RangeValidator(min_value=5)
        min_validator(5)
        min_validator(100)

        with pytest.raises(ValidationError):
            min_validator(4)

    def test_max_only(self):
        max_validator = RangeValidator(max_value=10)
        max_validator(10)
        max_validator(-100)

        with pytest.raises(ValidationError):
            max_validator(11)

    def test_float_values(self):
        self.validator(1.5)
        self.validator(9.9)

        with pytest.raises(ValidationError):
            self.validator(0.5)
        with pytest.raises(ValidationError):
            self.validator(10.5)

    def test_string_numbers(self):
        self.validator("5")
        self.validator("1")

        with pytest.raises(ValidationError):
            self.validator("0")

    def test_invalid_number(self):
        with pytest.raises(ValidationError):
            self.validator("not a number")


# ---------------------------------------------------------------------------
# PositiveValidator
# ---------------------------------------------------------------------------


class TestPositiveValidator:
    def setup_method(self):
        self.validator = PositiveValidator()

    def test_none_skips_validation(self):
        self.validator(None)

    def test_positive_numbers(self):
        self.validator(1)
        self.validator(100)
        self.validator(0.1)

    def test_zero_is_not_positive(self):
        with pytest.raises(ValidationError):
            self.validator(0)

    def test_negative_numbers(self):
        with pytest.raises(ValidationError):
            self.validator(-1)
        with pytest.raises(ValidationError):
            self.validator(-0.1)

    def test_string_numbers(self):
        self.validator("1")
        self.validator("100")

        with pytest.raises(ValidationError):
            self.validator("0")
        with pytest.raises(ValidationError):
            self.validator("-1")

    def test_invalid_number(self):
        with pytest.raises(ValidationError):
            self.validator("not a number")


# ---------------------------------------------------------------------------
# NonNegativeValidator
# ---------------------------------------------------------------------------


class TestNonNegativeValidator:
    def setup_method(self):
        self.validator = NonNegativeValidator()

    def test_none_skips_validation(self):
        self.validator(None)

    def test_positive_numbers(self):
        self.validator(1)
        self.validator(100)
        self.validator(0.1)

    def test_zero_is_non_negative(self):
        self.validator(0)

    def test_negative_numbers(self):
        with pytest.raises(ValidationError):
            self.validator(-1)
        with pytest.raises(ValidationError):
            self.validator(-0.1)

    def test_string_numbers(self):
        self.validator("0")
        self.validator("1")

        with pytest.raises(ValidationError):
            self.validator("-1")

    def test_invalid_number(self):
        with pytest.raises(ValidationError):
            self.validator("not a number")


# ---------------------------------------------------------------------------
# EmailValidator
# ---------------------------------------------------------------------------


class TestEmailValidator:
    def setup_method(self):
        self.validator = EmailValidator()

    def test_none_skips_validation(self):
        self.validator(None)

    def test_empty_string_skips_validation(self):
        self.validator("")

    def test_valid_emails(self):
        self.validator("test@example.com")
        self.validator("user.name@example.co.uk")
        self.validator("user+tag@example.com")
        self.validator("user_name@example-domain.com")

    def test_invalid_emails(self):
        with pytest.raises(ValidationError):
            self.validator("notanemail")
        with pytest.raises(ValidationError):
            self.validator("@example.com")
        with pytest.raises(ValidationError):
            self.validator("user@")
        with pytest.raises(ValidationError):
            self.validator("user@example")

    def test_non_string(self):
        with pytest.raises(ValidationError):
            self.validator(123)


# ---------------------------------------------------------------------------
# UrlValidator
# ---------------------------------------------------------------------------


class TestUrlValidator:
    def setup_method(self):
        self.validator = UrlValidator()

    def test_none_skips_validation(self):
        self.validator(None)

    def test_empty_string_skips_validation(self):
        self.validator("")

    def test_valid_http_url(self):
        self.validator("http://example.com")

    def test_valid_https_url(self):
        self.validator("https://example.com/path?foo=bar")

    def test_valid_ftp_url(self):
        self.validator("ftp://files.example.com")

    def test_valid_localhost_with_port(self):
        self.validator("http://localhost:8000")

    def test_valid_ipv4(self):
        self.validator("https://192.168.1.1:8080/path")

    def test_invalid_url_no_scheme(self):
        with pytest.raises(ValidationError):
            self.validator("example.com")

    def test_invalid_url_scheme_only(self):
        with pytest.raises(ValidationError):
            self.validator("http://")

    def test_invalid_url_plain_string(self):
        with pytest.raises(ValidationError):
            self.validator("not a url")

    def test_unsupported_scheme_raises(self):
        with pytest.raises(ValidationError):
            self.validator("ssh://example.com")

    def test_non_string_raises(self):
        with pytest.raises(ValidationError):
            self.validator(123)

    def test_custom_schemes_restricts_correctly(self):
        validator = UrlValidator(schemes=["https"])
        validator("https://example.com")
        with pytest.raises(ValidationError):
            validator("http://example.com")

    def test_custom_schemes_unknown_raises_at_init(self):
        with pytest.raises(ValueError):
            UrlValidator(schemes=["ssh"])

    def test_empty_schemes_raises_at_init(self):
        with pytest.raises(ValueError):
            UrlValidator(schemes=[])

    def test_custom_message(self):
        validator = UrlValidator(message="Bad URL.")
        with pytest.raises(ValidationError) as exc:
            validator("not-a-url")
        assert "Bad URL." in str(exc.value)


# ---------------------------------------------------------------------------
# IPv4Validator
# ---------------------------------------------------------------------------


class TestIPv4Validator:
    def setup_method(self):
        self.validator = IPv4Validator()

    def test_none_skips_validation(self):
        self.validator(None)

    def test_empty_string_skips_validation(self):
        self.validator("")

    def test_valid_ipv4(self):
        self.validator("192.168.1.1")
        self.validator("127.0.0.1")
        self.validator("0.0.0.0")
        self.validator("255.255.255.255")

    def test_invalid_ipv4(self):
        with pytest.raises(ValidationError):
            self.validator("256.1.1.1")
        with pytest.raises(ValidationError):
            self.validator("192.168.1")
        with pytest.raises(ValidationError):
            self.validator("192.168.1.1.1")
        with pytest.raises(ValidationError):
            self.validator("not an ip")

    def test_non_string(self):
        with pytest.raises(ValidationError):
            self.validator(123)


# ---------------------------------------------------------------------------
# IPv6Validator
# ---------------------------------------------------------------------------


class TestIPv6Validator:
    def setup_method(self):
        self.validator = IPv6Validator()

    def test_none_skips_validation(self):
        self.validator(None)

    def test_empty_string_skips_validation(self):
        self.validator("")

    def test_valid_ipv6(self):
        self.validator("2001:0db8:85a3:0000:0000:8a2e:0370:7334")
        self.validator("2001:db8:85a3::8a2e:370:7334")
        self.validator("::1")
        self.validator("2001:db8::1")

    def test_invalid_ipv6(self):
        with pytest.raises(ValidationError):
            self.validator("192.168.1.1")
        with pytest.raises(ValidationError):
            self.validator("not an ip")
        with pytest.raises(ValidationError):
            self.validator("2001:db8::1::1")

    def test_non_string(self):
        with pytest.raises(ValidationError):
            self.validator(123)


# ---------------------------------------------------------------------------
# IPAddressValidator
# ---------------------------------------------------------------------------


class TestIPAddressValidator:
    def setup_method(self):
        self.validator = IPAddressValidator()

    def test_none_skips_validation(self):
        self.validator(None)

    def test_empty_string_skips_validation(self):
        self.validator("")

    def test_valid_ipv4(self):
        self.validator("192.168.1.1")
        self.validator("127.0.0.1")

    def test_valid_ipv6(self):
        self.validator("2001:db8::1")
        self.validator("::1")

    def test_invalid_ip(self):
        with pytest.raises(ValidationError):
            self.validator("not an ip")
        with pytest.raises(ValidationError):
            self.validator("256.1.1.1")

    def test_version_4_only(self):
        v4_validator = IPAddressValidator(version=4)
        v4_validator("192.168.1.1")

        with pytest.raises(ValidationError):
            v4_validator("2001:db8::1")

    def test_version_6_only(self):
        v6_validator = IPAddressValidator(version=6)
        v6_validator("2001:db8::1")

        with pytest.raises(ValidationError):
            v6_validator("192.168.1.1")

    def test_non_string(self):
        with pytest.raises(ValidationError):
            self.validator(123)


# ---------------------------------------------------------------------------
# HostnameValidator
# ---------------------------------------------------------------------------


class TestHostnameValidator:
    def setup_method(self):
        self.validator = HostnameValidator()

    def test_none_skips_validation(self):
        self.validator(None)

    def test_empty_string_skips_validation(self):
        self.validator("")

    def test_valid_hostnames(self):
        self.validator("example.com")
        self.validator("sub.example.com")
        self.validator("host-name.example.com")
        self.validator("localhost")

    def test_invalid_hostnames(self):
        with pytest.raises(ValidationError):
            self.validator("-example.com")
        with pytest.raises(ValidationError):
            self.validator("example..com")
        with pytest.raises(ValidationError):
            self.validator("example-.com")
        with pytest.raises(ValidationError):
            self.validator("example.com-")

    def test_non_string(self):
        with pytest.raises(ValidationError):
            self.validator(123)


# ---------------------------------------------------------------------------
# ChoiceValidator
# ---------------------------------------------------------------------------


class TestChoiceValidator:
    def setup_method(self):
        self.validator = ChoiceValidator(["option1", "option2", "option3"])

    def test_none_skips_validation(self):
        self.validator(None)

    def test_valid_choices(self):
        self.validator("option1")
        self.validator("option2")
        self.validator("option3")

    def test_invalid_choices(self):
        with pytest.raises(ValidationError):
            self.validator("option4")
        with pytest.raises(ValidationError):
            self.validator("invalid")

    def test_numeric_choices(self):
        numeric_validator = ChoiceValidator([1, 2, 3])
        numeric_validator(1)
        numeric_validator(2)

        with pytest.raises(ValidationError):
            numeric_validator(4)


# ---------------------------------------------------------------------------
# SlugValidator
# ---------------------------------------------------------------------------


class TestSlugValidator:
    def setup_method(self):
        self.validator = SlugValidator()

    def test_none_skips_validation(self):
        self.validator(None)

    def test_empty_string_skips_validation(self):
        self.validator("")

    def test_valid_slugs(self):
        self.validator("hello")
        self.validator("hello-world")
        self.validator("hello_world")
        self.validator("hello123")
        self.validator("123hello")

    def test_invalid_slugs(self):
        with pytest.raises(ValidationError):
            self.validator("hello world")
        with pytest.raises(ValidationError):
            self.validator("hello.world")
        with pytest.raises(ValidationError):
            self.validator("hello@world")

    def test_non_string(self):
        with pytest.raises(ValidationError):
            self.validator(123)


# ---------------------------------------------------------------------------
# JsonValidator
# ---------------------------------------------------------------------------


class TestJsonValidator:
    def setup_method(self):
        self.validator = JsonValidator()

    def test_none_skips_validation(self):
        self.validator(None)

    def test_empty_string_skips_validation(self):
        self.validator("")

    def test_valid_json(self):
        self.validator("{}")
        self.validator("[]")
        self.validator('{"key": "value"}')
        self.validator("[1, 2, 3]")
        self.validator('{"nested": {"key": "value"}}')

    def test_invalid_json(self):
        with pytest.raises(ValidationError):
            self.validator("{invalid}")
        with pytest.raises(ValidationError):
            self.validator('{"key": }')
        with pytest.raises(ValidationError):
            self.validator("not json")

    def test_non_string_already_parsed(self):
        self.validator({})
        self.validator([])
        self.validator({"key": "value"})


# ---------------------------------------------------------------------------
# PathValidator
# ---------------------------------------------------------------------------


class TestPathValidator:
    def setup_method(self):
        self.relative_validator = PathValidator()
        self.absolute_validator = PathValidator(must_be_absolute=True)

    def test_none_skips_validation(self):
        self.relative_validator(None)
        self.absolute_validator(None)

    def test_empty_string_skips_validation(self):
        self.relative_validator("")
        self.absolute_validator("")

    def test_valid_paths(self):
        self.relative_validator("/path/to/file")
        self.relative_validator("relative/path")
        self.relative_validator("./relative/path")

    def test_absolute_path_required(self):
        import os

        abs_path = os.path.abspath("/absolute/path")
        self.absolute_validator(abs_path)

        with pytest.raises(ValidationError):
            self.absolute_validator("relative/path")

    def test_invalid_paths(self):
        with pytest.raises(ValidationError):
            self.relative_validator("path\x00with/null")

    def test_non_string(self):
        with pytest.raises(ValidationError):
            self.relative_validator(123)
        with pytest.raises(ValidationError):
            self.absolute_validator(123)


# ---------------------------------------------------------------------------
# PortValidator
# ---------------------------------------------------------------------------


class TestPortValidator:
    def setup_method(self):
        self.validator = PortValidator()

    def test_none_skips_validation(self):
        self.validator(None)

    def test_empty_string_skips_validation(self):
        self.validator("")

    def test_valid_ports(self):
        self.validator(1)
        self.validator(8080)
        self.validator(65535)
        self.validator("80")
        self.validator("443")

    def test_invalid_ports(self):
        with pytest.raises(ValidationError):
            self.validator(0)
        with pytest.raises(ValidationError):
            self.validator(65536)
        with pytest.raises(ValidationError):
            self.validator(-1)
        with pytest.raises(ValidationError):
            self.validator("0")
        with pytest.raises(ValidationError):
            self.validator("65536")

    def test_non_numeric(self):
        with pytest.raises(ValidationError):
            self.validator("not a port")


# ---------------------------------------------------------------------------
# DomainValidator
# ---------------------------------------------------------------------------


class TestDomainValidator:
    def setup_method(self):
        self.validator = DomainValidator()

    def test_none_skips_validation(self):
        self.validator(None)

    def test_empty_string_skips_validation(self):
        self.validator("")

    def test_valid_domains(self):
        self.validator("example.com")
        self.validator("sub.example.com")
        self.validator("example.co.uk")
        self.validator("a" * 63 + ".com")

    def test_invalid_domains(self):
        with pytest.raises(ValidationError):
            self.validator("example..com")
        with pytest.raises(ValidationError):
            self.validator("-example.com")
        with pytest.raises(ValidationError):
            self.validator("example-.com")
        with pytest.raises(ValidationError):
            self.validator("a" * 64 + ".com")
        with pytest.raises(ValidationError):
            self.validator("a" * 254)

    def test_non_string(self):
        with pytest.raises(ValidationError):
            self.validator(123)
