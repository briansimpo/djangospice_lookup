from __future__ import annotations

from django.core.exceptions import FieldDoesNotExist
from django.db import models

from .exceptions import InvalidLookupSearch


SEARCHABLE_FIELD_TYPES = (
    models.CharField,
    models.TextField,
    models.EmailField,
    models.SlugField,
)


def get_default_search_fields(model: type[models.Model]) -> tuple[str, ...]:

    fields: list[str] = []

    for field in model._meta.get_fields():

        if not isinstance(
            field,
            SEARCHABLE_FIELD_TYPES,
        ):
            continue

        if field.primary_key:
            continue

        if not field.editable:
            continue

        fields.append(field.name)

    return tuple(fields)


def validate_search_fields(model: type[models.Model], fields: tuple[str, ...]) -> tuple[str, ...]:

    if not fields:
        return get_default_search_fields(
            model
        )

    validated: list[str] = []

    for path in fields:

        if not path:
            raise InvalidLookupSearch(
                "Search field cannot be empty."
            )

        current_model = model
        parts = path.split("__")

        for index, part in enumerate(parts):

            try:
                field = current_model._meta.get_field(
                    part
                )
            except FieldDoesNotExist as exc:
                raise InvalidLookupSearch(
                    f"'{path}' is not a valid search field "
                    f"on '{model._meta.label}'."
                ) from exc

            is_last = index == len(parts) - 1

            if field.is_relation:

                if is_last:
                    raise InvalidLookupSearch(
                        f"'{path}' ends on a relationship. "
                        "Search fields must resolve to "
                        "a concrete text field."
                    )

                current_model = field.related_model
                continue

            if not is_last:
                raise InvalidLookupSearch(
                    f"'{path}' cannot continue through "
                    f"non-relational field '{part}'."
                )

            if not isinstance(
                field,
                SEARCHABLE_FIELD_TYPES,
            ):
                raise InvalidLookupSearch(
                    f"'{path}' does not resolve to a "
                    "supported text field."
                )

        validated.append(path)

    return tuple(validated)