"""
Typed field shorthands for django-sysconfig.

Instead of importing and passing a FrontendModel class explicitly:

    from django_sysconfig.registry import Field
    from django_sysconfig.frontend_models import StringFrontendModel

    site_name = Field(StringFrontendModel, label="Site Name")

You can use the shorthands here:

    from django_sysconfig import fields

    site_name = fields.String(label="Site Name")

Each shorthand is a partial of Field with the frontend_model pre-filled.
All keyword arguments accepted by Field are supported.
"""

from functools import partial

from .frontend_models import (
    BooleanFrontendModel,
    DecimalFrontendModel,
    IntegerFrontendModel,
    SecretFrontendModel,
    SelectFrontendModel,
    StringFrontendModel,
    TextareaFrontendModel,
)
from .registry import Field

__all__ = [
    "String",
    "Textarea",
    "Integer",
    "Decimal",
    "Boolean",
    "Select",
    "Secret",
]

String = partial(Field, StringFrontendModel)
Textarea = partial(Field, TextareaFrontendModel)
Integer = partial(Field, IntegerFrontendModel)
Decimal = partial(Field, DecimalFrontendModel)
Boolean = partial(Field, BooleanFrontendModel)
Select = partial(Field, SelectFrontendModel)
Secret = partial(Field, SecretFrontendModel)
