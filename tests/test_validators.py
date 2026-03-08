from django.test import SimpleTestCase as TestCase

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


class NotEmptyValidatorTestCase(TestCase):
    def setUp(self):
        message = "The value provided is Empty"
        self.validator = NotEmptyValidator(message)

    def test_none_is_empty(self):
        with self.assertRaises(ValidationError):
            self.validator(None)

    def test_empty_string_is_empty(self):
        with self.assertRaises(ValidationError):
            self.validator("")

    def test_empty_list_is_empty(self):
        with self.assertRaises(ValidationError):
            self.validator([])

    def test_empty_dict_is_empty(self):
        with self.assertRaises(ValidationError):
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


class NotBlankValidatorTestCase(TestCase):
    def setUp(self):
        self.validator = NotBlankValidator()

    def test_empty_string_is_blank(self):
        with self.assertRaises(ValidationError):
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


class MinLengthValidatorTestCase(TestCase):
    def setUp(self):
        self.validator = MinLengthValidator(4)

    def test_min_length_must_be_more_than_one(self):
        with self.assertRaises(ValidationError):
            _ = MinLengthValidator(0)
        with self.assertRaises(ValidationError):
            _ = MinLengthValidator(-2)

    def test_do_not_care_min_length_for_int(self):
        self.validator(1)
        self.validator(-100)

    def test_do_not_care_min_length_for_float(self):
        self.validator(1.0)
        self.validator(-10.0)

    def test_none_skips_validation(self):
        self.validator(None)  # must not raise

    def test_string_length(self):
        self.validator("hello")

        with self.assertRaises(ValidationError):
            self.validator("hi")


class MaxLengthValidatorTestCase(TestCase):
    def setUp(self):
        self.validator = MaxLengthValidator(5)

    def test_max_length_must_be_more_than_one(self):
        with self.assertRaises(ValidationError):
            _ = MaxLengthValidator(0)
        with self.assertRaises(ValidationError):
            _ = MaxLengthValidator(-2)

    def test_do_not_care_max_length_for_int(self):
        self.validator(1)
        self.validator(-100)

    def test_do_not_care_max_length_for_float(self):
        self.validator(1.0)
        self.validator(-10.0)

    def test_none_skips_validation(self):
        self.validator(None)  # must not raise

    def test_string_length(self):
        self.validator("hello")
        self.validator("hi")

        with self.assertRaises(ValidationError):
            self.validator("hello world")


class RegexValidatorTestCase(TestCase):
    def setUp(self):
        self.validator = RegexValidator(r"^[a-z]+$")

    def test_none_skips_validation(self):
        self.validator(None)  # must not raise

    def test_non_string_fails_validation(self):
        with self.assertRaises(ValidationError):
            self.validator(123)
        with self.assertRaises(ValidationError):
            self.validator([])

    def test_matching_pattern(self):
        self.validator("hello")
        self.validator("abc")

    def test_non_matching_pattern(self):
        with self.assertRaises(ValidationError):
            self.validator("Hello")
        with self.assertRaises(ValidationError):
            self.validator("hello123")

    def test_inverse_validator(self):
        inverse_validator = RegexValidator(r"^[a-z]+$", inverse=True)
        inverse_validator("Hello")
        inverse_validator("hello123")

        with self.assertRaises(ValidationError):
            inverse_validator("hello")


class RangeValidatorTestCase(TestCase):
    def setUp(self):
        self.validator = RangeValidator(min_value=1, max_value=10)

    def test_none_skips_validation(self):
        self.validator(None)  # must not raise

    def test_valid_range(self):
        self.validator(1)
        self.validator(5)
        self.validator(10)

    def test_below_minimum(self):
        with self.assertRaises(ValidationError):
            self.validator(0)
        with self.assertRaises(ValidationError):
            self.validator(-1)

    def test_above_maximum(self):
        with self.assertRaises(ValidationError):
            self.validator(11)
        with self.assertRaises(ValidationError):
            self.validator(100)

    def test_min_only(self):
        min_validator = RangeValidator(min_value=5)
        min_validator(5)
        min_validator(100)

        with self.assertRaises(ValidationError):
            min_validator(4)

    def test_max_only(self):
        max_validator = RangeValidator(max_value=10)
        max_validator(10)
        max_validator(-100)

        with self.assertRaises(ValidationError):
            max_validator(11)

    def test_float_values(self):
        self.validator(1.5)
        self.validator(9.9)

        with self.assertRaises(ValidationError):
            self.validator(0.5)
        with self.assertRaises(ValidationError):
            self.validator(10.5)

    def test_string_numbers(self):
        self.validator("5")
        self.validator("1")

        with self.assertRaises(ValidationError):
            self.validator("0")

    def test_invalid_number(self):
        with self.assertRaises(ValidationError):
            self.validator("not a number")


class PositiveValidatorTestCase(TestCase):
    def setUp(self):
        self.validator = PositiveValidator()

    def test_none_skips_validation(self):
        self.validator(None)  # must not raise

    def test_positive_numbers(self):
        self.validator(1)
        self.validator(100)
        self.validator(0.1)

    def test_zero_is_not_positive(self):
        with self.assertRaises(ValidationError):
            self.validator(0)

    def test_negative_numbers(self):
        with self.assertRaises(ValidationError):
            self.validator(-1)
        with self.assertRaises(ValidationError):
            self.validator(-0.1)

    def test_string_numbers(self):
        self.validator("1")
        self.validator("100")

        with self.assertRaises(ValidationError):
            self.validator("0")
        with self.assertRaises(ValidationError):
            self.validator("-1")

    def test_invalid_number(self):
        with self.assertRaises(ValidationError):
            self.validator("not a number")


class NonNegativeValidatorTestCase(TestCase):
    def setUp(self):
        self.validator = NonNegativeValidator()

    def test_none_skips_validation(self):
        self.validator(None)  # must not raise

    def test_positive_numbers(self):
        self.validator(1)
        self.validator(100)
        self.validator(0.1)

    def test_zero_is_non_negative(self):
        self.validator(0)

    def test_negative_numbers(self):
        with self.assertRaises(ValidationError):
            self.validator(-1)
        with self.assertRaises(ValidationError):
            self.validator(-0.1)

    def test_string_numbers(self):
        self.validator("0")
        self.validator("1")

        with self.assertRaises(ValidationError):
            self.validator("-1")

    def test_invalid_number(self):
        with self.assertRaises(ValidationError):
            self.validator("not a number")


class EmailValidatorTestCase(TestCase):
    def setUp(self):
        self.validator = EmailValidator()

    def test_none_skips_validation(self):
        self.validator(None)  # must not raise

    def test_empty_string_skips_validation(self):
        self.validator("")  # must not raise

    def test_valid_emails(self):
        self.validator("test@example.com")
        self.validator("user.name@example.co.uk")
        self.validator("user+tag@example.com")
        self.validator("user_name@example-domain.com")

    def test_invalid_emails(self):
        with self.assertRaises(ValidationError):
            self.validator("notanemail")
        with self.assertRaises(ValidationError):
            self.validator("@example.com")
        with self.assertRaises(ValidationError):
            self.validator("user@")
        with self.assertRaises(ValidationError):
            self.validator("user@example")

    def test_non_string(self):
        with self.assertRaises(ValidationError):
            self.validator(123)


class UrlValidatorTestCase(TestCase):
    def setUp(self):
        self.validator = UrlValidator()

    def test_none_skips_validation(self):
        self.validator(None)  # must not raise

    def test_empty_string_skips_validation(self):
        self.validator("")  # must not raise

    def test_valid_urls(self):
        self.validator("http://example.com")
        self.validator("https://example.com/path")
        self.validator("ftp://example.com")
        self.validator("http://localhost:8000")
        self.validator("https://192.168.1.1:8080/path")

    def test_invalid_urls(self):
        with self.assertRaises(ValidationError):
            self.validator("not a url")
        with self.assertRaises(ValidationError):
            self.validator("example.com")
        with self.assertRaises(ValidationError):
            self.validator("http://")

    def test_custom_schemes(self):
        custom_validator = UrlValidator(schemes=["http"])
        custom_validator("http://example.com")

        with self.assertRaises(ValidationError):
            custom_validator("https://example.com")

    def test_non_string(self):
        with self.assertRaises(ValidationError):
            self.validator(123)


class IPv4ValidatorTestCase(TestCase):
    def setUp(self):
        self.validator = IPv4Validator()

    def test_none_skips_validation(self):
        self.validator(None)  # must not raise

    def test_empty_string_skips_validation(self):
        self.validator("")  # must not raise

    def test_valid_ipv4(self):
        self.validator("192.168.1.1")
        self.validator("127.0.0.1")
        self.validator("0.0.0.0")
        self.validator("255.255.255.255")

    def test_invalid_ipv4(self):
        with self.assertRaises(ValidationError):
            self.validator("256.1.1.1")
        with self.assertRaises(ValidationError):
            self.validator("192.168.1")
        with self.assertRaises(ValidationError):
            self.validator("192.168.1.1.1")
        with self.assertRaises(ValidationError):
            self.validator("not an ip")

    def test_non_string(self):
        with self.assertRaises(ValidationError):
            self.validator(123)


class IPv6ValidatorTestCase(TestCase):
    def setUp(self):
        self.validator = IPv6Validator()

    def test_none_skips_validation(self):
        self.validator(None)  # must not raise

    def test_empty_string_skips_validation(self):
        self.validator("")  # must not raise

    def test_valid_ipv6(self):
        self.validator("2001:0db8:85a3:0000:0000:8a2e:0370:7334")
        self.validator("2001:db8:85a3::8a2e:370:7334")
        self.validator("::1")
        self.validator("2001:db8::1")

    def test_invalid_ipv6(self):
        with self.assertRaises(ValidationError):
            self.validator("192.168.1.1")
        with self.assertRaises(ValidationError):
            self.validator("not an ip")
        with self.assertRaises(ValidationError):
            self.validator("2001:db8::1::1")

    def test_non_string(self):
        with self.assertRaises(ValidationError):
            self.validator(123)


class IPAddressValidatorTestCase(TestCase):
    def setUp(self):
        self.validator = IPAddressValidator()

    def test_none_skips_validation(self):
        self.validator(None)  # must not raise

    def test_empty_string_skips_validation(self):
        self.validator("")  # must not raise

    def test_valid_ipv4(self):
        self.validator("192.168.1.1")
        self.validator("127.0.0.1")

    def test_valid_ipv6(self):
        self.validator("2001:db8::1")
        self.validator("::1")

    def test_invalid_ip(self):
        with self.assertRaises(ValidationError):
            self.validator("not an ip")
        with self.assertRaises(ValidationError):
            self.validator("256.1.1.1")

    def test_version_4_only(self):
        v4_validator = IPAddressValidator(version=4)
        v4_validator("192.168.1.1")

        with self.assertRaises(ValidationError):
            v4_validator("2001:db8::1")

    def test_version_6_only(self):
        v6_validator = IPAddressValidator(version=6)
        v6_validator("2001:db8::1")

        with self.assertRaises(ValidationError):
            v6_validator("192.168.1.1")

    def test_non_string(self):
        with self.assertRaises(ValidationError):
            self.validator(123)


class HostnameValidatorTestCase(TestCase):
    def setUp(self):
        self.validator = HostnameValidator()

    def test_none_skips_validation(self):
        self.validator(None)  # must not raise

    def test_empty_string_skips_validation(self):
        self.validator("")  # must not raise

    def test_valid_hostnames(self):
        self.validator("example.com")
        self.validator("sub.example.com")
        self.validator("host-name.example.com")
        self.validator("localhost")

    def test_invalid_hostnames(self):
        with self.assertRaises(ValidationError):
            self.validator("-example.com")
        with self.assertRaises(ValidationError):
            self.validator("example..com")
        with self.assertRaises(ValidationError):
            self.validator("example-.com")
        with self.assertRaises(ValidationError):
            self.validator("example.com-")

    def test_non_string(self):
        with self.assertRaises(ValidationError):
            self.validator(123)


class ChoiceValidatorTestCase(TestCase):
    def setUp(self):
        self.validator = ChoiceValidator(["option1", "option2", "option3"])

    def test_none_skips_validation(self):
        self.validator(None)

    def test_valid_choices(self):
        self.validator("option1")
        self.validator("option2")
        self.validator("option3")

    def test_invalid_choices(self):
        with self.assertRaises(ValidationError):
            self.validator("option4")
        with self.assertRaises(ValidationError):
            self.validator("invalid")

    def test_numeric_choices(self):
        numeric_validator = ChoiceValidator([1, 2, 3])
        numeric_validator(1)
        numeric_validator(2)

        with self.assertRaises(ValidationError):
            numeric_validator(4)


class SlugValidatorTestCase(TestCase):
    def setUp(self):
        self.validator = SlugValidator()

    def test_none_skips_validation(self):
        self.validator(None)  # must not raise

    def test_empty_string_skips_validation(self):
        self.validator("")  # must not raise

    def test_valid_slugs(self):
        self.validator("hello")
        self.validator("hello-world")
        self.validator("hello_world")
        self.validator("hello123")
        self.validator("123hello")

    def test_invalid_slugs(self):
        with self.assertRaises(ValidationError):
            self.validator("hello world")
        with self.assertRaises(ValidationError):
            self.validator("hello.world")
        with self.assertRaises(ValidationError):
            self.validator("hello@world")

    def test_non_string(self):
        with self.assertRaises(ValidationError):
            self.validator(123)


class JsonValidatorTestCase(TestCase):
    def setUp(self):
        self.validator = JsonValidator()

    def test_none_skips_validation(self):
        self.validator(None)  # must not raise

    def test_empty_string_skips_validation(self):
        self.validator("")  # must not raise

    def test_valid_json(self):
        self.validator("{}")
        self.validator("[]")
        self.validator('{"key": "value"}')
        self.validator("[1, 2, 3]")
        self.validator('{"nested": {"key": "value"}}')

    def test_invalid_json(self):
        with self.assertRaises(ValidationError):
            self.validator("{invalid}")
        with self.assertRaises(ValidationError):
            self.validator('{"key": }')
        with self.assertRaises(ValidationError):
            self.validator("not json")

    def test_non_string(self):
        # Non-strings are considered already parsed
        self.validator({})
        self.validator([])
        self.validator({"key": "value"})


class PathValidatorTestCase(TestCase):
    def setUp(self):
        self.relative_validator = PathValidator()
        self.absolute_validator = PathValidator(must_be_absolute=True)

    def test_none_skips_validation(self):
        self.relative_validator(None)  # must not raise
        self.absolute_validator(None)  # must not raise

    def test_empty_string_skips_validation(self):
        self.relative_validator("")  # must not raise
        self.absolute_validator("")  # must not raise

    def test_valid_paths(self):
        self.relative_validator("/path/to/file")
        self.relative_validator("relative/path")
        self.relative_validator("./relative/path")

    def test_absolute_path_required(self):
        self.absolute_validator("/absolute/path")

        with self.assertRaises(ValidationError):
            self.absolute_validator("relative/path")

    def test_invalid_paths(self):
        with self.assertRaises(ValidationError):
            self.relative_validator("path\x00with/null")

    def test_non_string(self):
        with self.assertRaises(ValidationError):
            self.relative_validator(123)
        with self.assertRaises(ValidationError):
            self.absolute_validator(123)


class PortValidatorTestCase(TestCase):
    def setUp(self):
        self.validator = PortValidator()

    def test_none_skips_validation(self):
        self.validator(None)  # must not raise

    def test_empty_string_skips_validation(self):
        self.validator("")  # must not raise

    def test_valid_ports(self):
        self.validator(1)
        self.validator(8080)
        self.validator(65535)
        self.validator("80")
        self.validator("443")

    def test_invalid_ports(self):
        with self.assertRaises(ValidationError):
            self.validator(0)
        with self.assertRaises(ValidationError):
            self.validator(65536)
        with self.assertRaises(ValidationError):
            self.validator(-1)
        with self.assertRaises(ValidationError):
            self.validator("0")
        with self.assertRaises(ValidationError):
            self.validator("65536")

    def test_non_numeric(self):
        with self.assertRaises(ValidationError):
            self.validator("not a port")


class DomainValidatorTestCase(TestCase):
    def setUp(self):
        self.validator = DomainValidator()

    def test_none_skips_validation(self):
        self.validator(None)  # must not raise

    def test_empty_string_skips_validation(self):
        self.validator("")  # must not raise

    def test_valid_domains(self):
        self.validator("example.com")
        self.validator("sub.example.com")
        self.validator("example.co.uk")
        self.validator("a" * 63 + ".com")  # Max label length

    def test_invalid_domains(self):
        with self.assertRaises(ValidationError):
            self.validator("example..com")
        with self.assertRaises(ValidationError):
            self.validator("-example.com")
        with self.assertRaises(ValidationError):
            self.validator("example-.com")
        with self.assertRaises(ValidationError):
            self.validator("a" * 64 + ".com")  # Label too long
        with self.assertRaises(ValidationError):
            self.validator("a" * 254)  # Total too long

    def test_non_string(self):
        with self.assertRaises(ValidationError):
            self.validator(123)
