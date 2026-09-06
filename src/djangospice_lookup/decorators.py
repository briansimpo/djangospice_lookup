from __future__ import annotations

from typing import Any

from django.db import models

from .definition import LookupDefinition
from .exceptions import LookupConfigurationError
from .registry import lookup_registry


def register_lookup(model: type[models.Model], **kwargs: Any) -> LookupDefinition:
    """
    Register a Django model as a lookup.

    The lookup identity is derived from:

        model._meta.app_label
        model._meta.model_name
    """

    if not isinstance(model, type) or not issubclass(
        model,
        models.Model,
    ):
        raise LookupConfigurationError(
            "register_lookup() requires a Django model class."
        )

    definition = LookupDefinition(
        model=model,
        **kwargs,
    )

    return lookup_registry.register(
        definition,
    )