"""
Frontend Models Module

FrontendModels handle the rendering of configuration inputs and extraction
of values from form submissions. Each FrontendModel corresponds to a specific
input type (string, integer, boolean, etc.).

These classes bind configuration fields to their input components and handle:
- Rendering the appropriate HTML input element via Django templates
- Extracting and converting values from POST requests
"""

from abc import ABC, abstractmethod
from decimal import Decimal, InvalidOperation
from typing import Any

from django.template.loader import render_to_string


class BaseFrontendModel(ABC):
    """
    Abstract base class for all frontend models.

    Each frontend model is responsible for rendering an input component
    and extracting the submitted value from the request.
    """

    template_name: str = "config/frontend_models/base.html"

    def __init__(self, field, current_value: Any = None):
        """
        Initialize the frontend model.

        Args:
            field: The Field instance this frontend model is rendering
            current_value: The current value from the database (or default)
        """
        self.field = field
        self.current_value = current_value

    def get_context(self) -> dict:
        """Get the template context for rendering."""
        return {
            "field": self.field,
            "value": self.current_value,
            "input_name": self.get_input_name(),
            "input_id": self.get_input_id(),
        }

    def get_input_name(self) -> str:
        """Get the HTML input name attribute."""
        return f"config_{self.field.path.replace('/', '_')}"

    def get_input_id(self) -> str:
        """Get the HTML input id attribute."""
        return f"id_{self.get_input_name()}"

    def render(self) -> str:
        """Render the input component as HTML."""
        return render_to_string(self.template_name, self.get_context())

    @abstractmethod
    def get_value(self, raw_value: str | None) -> Any:
        """
        Convert the raw form value to the appropriate Python type.

        Args:
            raw_value: The raw string value from the form submission

        Returns:
            The converted value in the appropriate type
        """
        pass

    def serialize_value(self, value: Any) -> str | None:
        """
        Serialize a value for storage in the database.

        Args:
            value: The Python value to serialize

        Returns:
            String representation for database storage, or None
        """
        if value is None:
            return None
        return str(value)


class StringFrontendModel(BaseFrontendModel):
    """Frontend model for text/string inputs."""

    template_name = "config/frontend_models/string.html"

    def get_value(self, raw_value: str | None) -> str | None:
        if raw_value is None or raw_value == "":
            return None
        return str(raw_value)


class TextareaFrontendModel(BaseFrontendModel):
    """Frontend model for multi-line text inputs."""

    template_name = "config/frontend_models/textarea.html"

    def get_value(self, raw_value: str | None) -> str | None:
        if raw_value is None or raw_value == "":
            return None
        return str(raw_value)


class IntegerFrontendModel(BaseFrontendModel):
    """Frontend model for integer number inputs."""

    template_name = "config/frontend_models/integer.html"

    def get_value(self, raw_value: str | None) -> int | None:
        if raw_value is None or raw_value == "":
            return None
        try:
            return int(raw_value)
        except (ValueError, TypeError):
            return None

    def serialize_value(self, value: Any) -> str | None:
        if value is None:
            return None
        return str(int(value))


class DecimalFrontendModel(BaseFrontendModel):
    """Frontend model for decimal number inputs."""

    template_name = "config/frontend_models/decimal.html"

    def get_context(self) -> dict:
        context = super().get_context()
        # Allow customizing decimal places via field extra
        context["step"] = self.field.extra.get("step", "0.01")
        return context

    def get_value(self, raw_value: str | None) -> Decimal | None:
        if raw_value is None or raw_value == "":
            return None
        try:
            return Decimal(raw_value)
        except (InvalidOperation, TypeError):
            return None

    def serialize_value(self, value: Any) -> str | None:
        if value is None:
            return None
        return str(Decimal(value))


class BooleanFrontendModel(BaseFrontendModel):
    """Frontend model for boolean checkbox inputs."""

    template_name = "config/frontend_models/boolean.html"

    def get_context(self) -> dict:
        context = super().get_context()
        # Convert value to boolean for template
        context["checked"] = self._to_bool(self.current_value)
        return context

    def _to_bool(self, value: Any) -> bool:
        """Convert various value representations to boolean."""
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ("true", "1", "yes", "on")
        return bool(value)

    def get_value(self, raw_value: str | None) -> bool:
        """
        Convert raw form value to boolean.

        Checkbox behavior:
        - If checkbox is checked, browser sends a value (usually "on" or the value attribute)
        - If checkbox is unchecked, browser doesn't send the field at all (None)
        - We also handle explicit "false" string for API/form compatibility
        """
        if raw_value is None or raw_value == "":
            return False
        # Explicitly handle "false" string (for API/form submissions)
        if isinstance(raw_value, str) and raw_value.lower() == "false":
            return False
        # Any other non-empty value means True
        return True

    def serialize_value(self, value: Any) -> str:
        return "true" if value else "false"


class SelectFrontendModel(BaseFrontendModel):
    """Frontend model for dropdown select inputs."""

    template_name = "config/frontend_models/select.html"

    def get_context(self) -> dict:
        context = super().get_context()
        # Choices should be provided via field.extra['choices']
        # Format: [('value', 'Label'), ...]
        context["choices"] = self.field.extra.get("choices", [])
        return context

    def get_value(self, raw_value: str | None) -> str | None:
        if raw_value is None or raw_value == "":
            return None
        return str(raw_value)


class SecretFrontendModel(BaseFrontendModel):
    """
    Frontend model for sensitive/secret values like API keys.

    - Renders as a password input (masked)
    - Encrypts value before storing in database
    - Decrypts value when retrieved
    - Shows placeholder when value exists, never displays actual value
    """

    template_name = "config/frontend_models/secret.html"

    # Placeholder shown when a secret value exists
    SECRET_PLACEHOLDER = "••••••••••••••••••••••••"

    def get_context(self) -> dict:
        context = super().get_context()
        # Never send the actual value to the template
        # Just indicate whether a value exists
        context["has_value"] = (
            self.current_value is not None and self.current_value != ""
        )
        context["placeholder"] = self.SECRET_PLACEHOLDER
        # Remove the actual value from context
        context["value"] = ""
        return context

    def get_value(self, raw_value: str | None) -> str | None:
        """
        Get the decrypted value.

        Note: This is called when reading from the form submission.
        The raw_value here is the plaintext entered by the user.
        """
        if raw_value is None or raw_value == "":
            return None
        return str(raw_value)

    def serialize_value(self, value: Any) -> str | None:
        """
        Encrypt the value before storing in the database.
        """
        if value is None or value == "":
            return None

        from .encryption import encrypt

        return encrypt(str(value))

    @staticmethod
    def decrypt_value(encrypted_value: str | None) -> str | None:
        """
        Decrypt a value retrieved from the database.

        This is a static method that can be called by the accessor
        to decrypt stored values.
        """
        if encrypted_value is None or encrypted_value == "":
            return None

        from .encryption import safe_decrypt

        return safe_decrypt(encrypted_value) or None


# Registry mapping frontend_model names to their classes
FRONTEND_MODEL_REGISTRY: dict[str, type[BaseFrontendModel]] = {
    "string": StringFrontendModel,
    "text": StringFrontendModel,
    "textarea": TextareaFrontendModel,
    "integer": IntegerFrontendModel,
    "int": IntegerFrontendModel,
    "decimal": DecimalFrontendModel,
    "float": DecimalFrontendModel,
    "boolean": BooleanFrontendModel,
    "bool": BooleanFrontendModel,
    "select": SelectFrontendModel,
    "dropdown": SelectFrontendModel,
    "secret": SecretFrontendModel,
    "password": SecretFrontendModel,
}


def get_frontend_model(
    frontend_model_name: str,
    field,
    current_value: Any = None,
) -> BaseFrontendModel:
    """
    Factory function to get the appropriate frontend model instance.

    Args:
        frontend_model_name: The name of the frontend model type
        field: The Field instance
        current_value: The current value from the database

    Returns:
        An instance of the appropriate BaseFrontendModel subclass
    """
    model_class = FRONTEND_MODEL_REGISTRY.get(
        frontend_model_name.lower(),
        StringFrontendModel,  # Default to string
    )
    return model_class(field, current_value)
