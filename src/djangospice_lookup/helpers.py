
from typing import Any
from django.http import HttpRequest

from .definition import LookupDefinition


def clean_values(values: list[str]) -> list[str]:
    """
    Remove empty values and normalize whitespace.
    """

    return [
        value.strip()
        for value in values
        if value.strip()
    ]


def positive_int(value: str | None,*,default: int | None) -> int | None:
    """
    Parse a positive integer.

    Invalid or non-positive values fall back to ``default``.
    """

    if value in (None, ""):
        return default

    try:
        value = int(value)
    except (TypeError, ValueError):
        return default

    if value < 1:
        return default

    return value



def get_dependencies(request: HttpRequest, definition: LookupDefinition) -> dict[str, Any]:
    """
    Extract values for declared lookup dependencies.

    Only dependencies declared by ``definition.depends_on``
    are accepted.

    """

    dependencies: dict[str, Any] = {}

    for dependency in definition.dependencies:
        path = dependency.path

        values = request.GET.getlist(
            path,
        )

        values = clean_values(
            values,
        )

        if not values:
            continue

        dependencies[path] = (
            values[0]
            if len(values) == 1
            else values
        )

    return dependencies





