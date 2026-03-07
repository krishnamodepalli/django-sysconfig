"""
Validators for configuration fields.

Validators are used to ensure configuration values meet specific requirements
before being saved to the database.
"""

import re
from abc import ABC, abstractmethod
from decimal import Decimal, InvalidOperation
from typing import Any


class ValidationError(Exception):
    """Raised when a configuration value fails validation."""

    def __init__(self, message: str, field_label: str = ""):
        self.message = message
        self.field_label = field_label
        super().__init__(message)

    def __str__(self):
        if self.field_label:
            return f"{self.field_label}: {self.message}"
        return self.message


class BaseValidator(ABC):
    """Abstract base class for all validators."""

    # Error message template - subclasses should override
    message: str = "Invalid value."

    def __init__(self, message: str | None = None):
        """
        Initialize the validator.

        Args:
            message: Custom error message (overrides default)
        """
        if message is not None:
            self.message = message

    @abstractmethod
    def __call__(self, value: Any) -> None:
        """
        Validate the value.

        Args:
            value: The value to validate

        Raises:
            ValidationError: If validation fails
        """
        pass

    def _fail(self, message: str | None = None):
        """Raise a ValidationError with the given or default message."""
        raise ValidationError(message or self.message)


# ============================================================================
# Required / Presence Validators
# ============================================================================


class NotEmptyValidator(BaseValidator):
    """Validates that a value is not empty (None, empty string, etc.)."""

    message = "This field is required."

    def __call__(self, value: Any) -> None:
        # First sanitize the given value
        if isinstance(value, (str | int | float | bool)):
            value = str(value)

        if value is None:
            self._fail()
        if isinstance(value, str) and value.strip() == "":
            self._fail()
        if isinstance(value, list | dict) and len(value) == 0:
            self._fail()


class NotBlankValidator(BaseValidator):
    """Validates that a string value is not blank (whitespace only)."""

    message = "This field cannot be blank."

    def __call__(self, value: Any) -> None:
        if value is None:
            return  # None is allowed, use NotEmptyValidator for required
        if isinstance(value, str) and value.strip() == "":
            self._fail()


# ============================================================================
# String Validators
# ============================================================================


class MinLengthValidator(BaseValidator):
    """Validates that a string has at least a minimum length."""

    def __init__(self, min_length: int, message: str | None = None):
        if min_length <= 0:
            raise ValidationError("`min_length` cannot be 0 or less")

        self.min_length = min_length
        super().__init__(message or f"Must be at least {min_length} characters.")

    def __call__(self, value: Any) -> None:
        if value is None:
            self._fail("This field is required.")
        if isinstance(value, str) and len(value) < self.min_length:
            self._fail()


class MaxLengthValidator(BaseValidator):
    """Validates that a string does not exceed a maximum length."""

    def __init__(self, max_length: int, message: str | None = None):
        if max_length <= 0:
            raise ValidationError("`max_length` cannot be 0 or less")

        self.max_length = max_length
        super().__init__(message or f"Must be at most {max_length} characters.")

    def __call__(self, value: Any) -> None:
        if value is None:
            self._fail("This field is required.")
        if isinstance(value, str) and len(value) > self.max_length:
            self._fail()


class RegexValidator(BaseValidator):
    """Validates that a string matches a regular expression pattern."""

    def __init__(
        self,
        pattern: str,
        message: str | None = None,
        flags: int = 0,
        inverse: bool = False,
    ):
        """
        Args:
            pattern: The regex pattern to match
            message: Custom error message
            flags: Regex flags (e.g., re.IGNORECASE)
            inverse: If True, validation fails when pattern matches
        """
        self.pattern = re.compile(pattern, flags)
        self.inverse = inverse
        super().__init__(message or "Value does not match the required pattern.")

    def __call__(self, value: Any) -> None:
        if value is None:
            self._fail("This field is required.")
        if not isinstance(value, str):
            self._fail("Value must be a string.")
            return

        matches = self.pattern.search(value) is not None
        if self.inverse and matches:
            self._fail()
        elif not self.inverse and not matches:
            self._fail()


# ============================================================================
# Numeric Validators
# ============================================================================


class RangeValidator(BaseValidator):
    """Validates that a numeric value is within a specified range."""

    def __init__(
        self,
        min_value: int | float | Decimal | None = None,
        max_value: int | float | Decimal | None = None,
        message: str | None = None,
    ):
        """
        Args:
            min_value: Minimum allowed value (inclusive)
            max_value: Maximum allowed value (inclusive)
            message: Custom error message
        """
        self.min_value = min_value
        self.max_value = max_value

        if message is None:
            if min_value is not None and max_value is not None:
                message = f"Must be between {min_value} and {max_value}."
            elif min_value is not None:
                message = f"Must be at least {min_value}."
            elif max_value is not None:
                message = f"Must be at most {max_value}."
            else:
                message = "Invalid value."

        super().__init__(message)

    def __call__(self, value: Any) -> None:
        if value is None:
            self._fail("This field is required.")

        try:
            num_value = Decimal(str(value))
        except (ValueError, TypeError, InvalidOperation):
            self._fail("Must be a valid number.")
            return

        if self.min_value is not None and num_value < Decimal(str(self.min_value)):
            self._fail()
        if self.max_value is not None and num_value > Decimal(str(self.max_value)):
            self._fail()


class PositiveValidator(BaseValidator):
    """Validates that a numeric value is positive (> 0)."""

    message = "Must be a positive number."

    def __call__(self, value: Any) -> None:
        if value is None:
            self._fail("This field is required.")
        try:
            if Decimal(str(value)) <= 0:
                self._fail()
        except (ValueError, TypeError, InvalidOperation):
            self._fail("Must be a valid number.")


class NonNegativeValidator(BaseValidator):
    """Validates that a numeric value is non-negative (>= 0)."""

    message = "Must be zero or a positive number."

    def __call__(self, value: Any) -> None:
        if value is None:
            self._fail("This field is required.")
        try:
            if Decimal(str(value)) < 0:
                self._fail()
        except (ValueError, TypeError, InvalidOperation):
            self._fail("Must be a valid number.")


# ============================================================================
# Format Validators (URL, Email, IP, etc.)
# ============================================================================


class EmailValidator(BaseValidator):
    """Validates that a value is a valid email address."""

    message = "Enter a valid email address."

    # Basic email pattern - covers most cases
    EMAIL_PATTERN = re.compile(
        r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
        re.IGNORECASE,
    )

    def __call__(self, value: Any) -> None:
        if value is None:
            self._fail("This field is required.")
        if value == "":
            self._fail("This field cannot be empty.")
        if not isinstance(value, str):
            self._fail()
            return
        if not self.EMAIL_PATTERN.match(value):
            self._fail()


class UrlValidator(BaseValidator):
    """Validates that a value is a valid URL."""

    message = "Enter a valid URL."

    # URL pattern supporting http, https, ftp
    URL_PATTERN = re.compile(
        r"^(https?|ftp)://"  # Scheme
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,63}\.?|"  # Domain
        r"localhost|"  # localhost
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # or IPv4
        r"(?::\d+)?"  # Optional port
        r"(?:/?|[/?]\S+)$",  # Path
        re.IGNORECASE,
    )

    def __init__(self, schemes: list[str] | None = None, message: str | None = None):
        """
        Args:
            schemes: Allowed URL schemes (default: ['http', 'https', 'ftp'])
            message: Custom error message
        """
        self.schemes = schemes or ["http", "https", "ftp"]
        super().__init__(message)

    def __call__(self, value: Any) -> None:
        if value is None:
            self._fail("This field is required.")
        if value == "":
            self._fail("This field cannot be empty.")
        if not isinstance(value, str):
            self._fail()
            return
        if not self.URL_PATTERN.match(value):
            self._fail()

        # Check scheme
        scheme = value.split("://")[0].lower()
        if scheme not in self.schemes:
            self._fail(f"URL scheme must be one of: {', '.join(self.schemes)}")


class IPv4Validator(BaseValidator):
    """Validates that a value is a valid IPv4 address."""

    message = "Enter a valid IPv4 address."

    IPV4_PATTERN = re.compile(
        r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
        r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
    )

    def __call__(self, value: Any) -> None:
        if value is None:
            self._fail("This field is required.")
        if value == "":
            self._fail("This field cannot be empty.")
        if not isinstance(value, str):
            self._fail()
            return
        if not self.IPV4_PATTERN.match(value):
            self._fail()


class IPv6Validator(BaseValidator):
    """Validates that a value is a valid IPv6 address."""

    message = "Enter a valid IPv6 address."

    def __call__(self, value: Any) -> None:
        if value is None:
            self._fail("This field is required.")
        if value == "":
            self._fail("This field cannot be empty.")
        if not isinstance(value, str):
            self._fail()
            return

        # Use Python's ipaddress module for proper IPv6 validation
        import ipaddress

        try:
            ipaddress.IPv6Address(value)
        except ipaddress.AddressValueError:
            self._fail()


class IPAddressValidator(BaseValidator):
    """Validates that a value is a valid IP address (IPv4 or IPv6)."""

    message = "Enter a valid IP address."

    def __init__(self, version: int | None = None, message: str | None = None):
        """
        Args:
            version: IP version (4 or 6). None allows both.
            message: Custom error message
        """
        self.version = version
        super().__init__(message)

    def __call__(self, value: Any) -> None:
        if value is None:
            self._fail("This field is required.")
        if value == "":
            self._fail("This field cannot be empty.")
        if not isinstance(value, str):
            self._fail()
            return

        import ipaddress

        try:
            ip = ipaddress.ip_address(value)
            if self.version == 4 and ip.version != 4:
                self._fail("Enter a valid IPv4 address.")
            elif self.version == 6 and ip.version != 6:
                self._fail("Enter a valid IPv6 address.")
        except ValueError:
            self._fail()


class HostnameValidator(BaseValidator):
    """Validates that a value is a valid hostname."""

    message = "Enter a valid hostname."

    # RFC 1123 compliant hostname pattern
    HOSTNAME_PATTERN = re.compile(
        r"^"  # Start of string
        r"(?=.{1,253}$)"  # Total length of hostname must be 1–253 characters
        r"(?:"
        r"[a-zA-Z0-9]"  # Label must start with a letter or digit
        r"(?:[a-zA-Z0-9-]{0,61}"  # Optional middle characters (letters, digits, hyphens)
        r"[a-zA-Z0-9])?"  # Label must end with a letter or digit if longer than 1 char
        r"\."  # Dot separator for labels
        r")*"  # Repeat for all intermediate labels (zero or more)
        r"[a-zA-Z0-9]"  # Last label must start with a letter or digit
        r"(?:[a-zA-Z0-9-]{0,61}"  # Optional middle characters for last label
        r"[a-zA-Z0-9])?"  # Last label must end with a letter or digit if longer than 1 char
        r"$",  # End of string
        re.IGNORECASE,  # Case-insensitive
    )

    def __call__(self, value: Any) -> None:
        if value is None:
            self._fail("This field is required.")
        if value == "":
            self._fail("This field cannot be empty.")
        if not isinstance(value, str):
            self._fail()
            return
        if not self.HOSTNAME_PATTERN.match(value):
            self._fail()


# ============================================================================
# Choice / Enum Validators
# ============================================================================


class ChoiceValidator(BaseValidator):
    """Validates that a value is one of the allowed choices."""

    def __init__(self, choices: list[Any], message: str | None = None):
        """
        Args:
            choices: List of allowed values
            message: Custom error message
        """
        self.choices = choices
        super().__init__(
            message or f"Must be one of: {', '.join(str(c) for c in choices)}"
        )

    def __call__(self, value: Any) -> None:
        if value is None:
            self._fail()
        if value not in self.choices:
            self._fail()


# ============================================================================
# Special Validators
# ============================================================================


class SlugValidator(BaseValidator):
    """Validates that a value is a valid slug (letters, numbers, hyphens, underscores)."""

    message = "Enter a valid slug (letters, numbers, hyphens, underscores only)."

    SLUG_PATTERN = re.compile(r"^[-a-zA-Z0-9_]+$")

    def __call__(self, value: Any) -> None:
        if value is None:
            self._fail("This field is required.")
        if value == "":
            self._fail("This field cannot be empty.")
        if not isinstance(value, str):
            self._fail()
            return
        if not self.SLUG_PATTERN.match(value):
            self._fail()


class JsonValidator(BaseValidator):
    """Validates that a value is valid JSON."""

    message = "Enter valid JSON."

    def __call__(self, value: Any) -> None:
        if value is None:
            self._fail("This field is required.")
        if value == "":
            self._fail("This field cannot be empty.")
        if not isinstance(value, str):
            return  # Already parsed

        import json

        try:
            json.loads(value)
        except json.JSONDecodeError:
            self._fail()


class PathValidator(BaseValidator):
    """Validates that a value looks like a valid file path."""

    message = "Enter a valid file path."

    def __init__(self, must_be_absolute: bool = False, message: str | None = None):
        """
        Args:
            must_be_absolute: If True, path must be absolute
            message: Custom error message
        """
        self.must_be_absolute = must_be_absolute
        super().__init__(message)

    def __call__(self, value: Any) -> None:
        if value is None:
            self._fail("This field is required.")
        if value == "":
            self._fail("This field cannot be empty.")
        if not isinstance(value, str):
            self._fail()
            return

        import os

        if self.must_be_absolute and not os.path.isabs(value):
            self._fail("Path must be absolute.")

        # Check for invalid characters (basic check)
        invalid_chars = ["\x00"]  # Null byte
        for char in invalid_chars:
            if char in value:
                self._fail()


class PortValidator(BaseValidator):
    """Validates that a value is a valid port number (1-65535)."""

    message = "Enter a valid port number (1-65535)."

    def __call__(self, value: Any) -> None:
        if value is None:
            self._fail("This field is required.")
        if value == "":
            self._fail("This field cannot be empty.")

        try:
            port = int(value)
            if port < 1 or port > 65535:
                self._fail()
        except (ValueError, TypeError):
            self._fail()


class DomainValidator(BaseValidator):
    """Validates that a value is a valid domain name."""

    message = "Enter a valid domain name."

    DOMAIN_PATTERN = re.compile(
        r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*"
        r"[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$"
    )

    def __call__(self, value: Any) -> None:
        if value is None:
            self._fail("This field is required.")
        if value == "":
            self._fail("This field cannot be empty.")
        if not isinstance(value, str):
            self._fail()
            return
        if len(value) > 253:
            self._fail()
        if not self.DOMAIN_PATTERN.match(value):
            self._fail()


# ============================================================================
# Convenience Aliases
# ============================================================================

# Alias for backward compatibility and clarity
Required = NotEmptyValidator


# ============================================================================
# Utility function to run validators
# ============================================================================


def validate_value(
    value: Any,
    validators: list[BaseValidator],
    field_label: str = "",
) -> list[str]:
    """
    Run all validators against a value.

    Args:
        value: The value to validate
        validators: List of validators to run
        field_label: Label for error messages

    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    for validator in validators:
        try:
            validator(value)
        except ValidationError as e:
            e.field_label = field_label
            errors.append(str(e))
    return errors
