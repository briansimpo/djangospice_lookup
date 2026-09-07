from typing import Any
from django.conf import settings
from django.utils.module_loading import import_string


def setting(name: str, default: Any) -> Any:
    return getattr(
        settings,
        name,
        default,
    )


def resolve_callable(value: Any) -> Any | None:
    if value is None:
        return None

    if isinstance(value, str):
        value = import_string(value)

    if not callable(value):
        raise TypeError(
            "Configured callable must be callable "
            "or a dotted Python path."
        )

    return value


def positive_int(name: str, value: Any) -> int:
    try:
        value = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"{name} must be a positive integer."
        ) from exc

    if value <= 0:
        raise ValueError(
            f"{name} must be a positive integer."
        )

    return value


def non_empty_string(name: str, value: Any) -> str:
    if not isinstance(value, str):
        raise TypeError(
            f"{name} must be a string."
        )

    value = value.strip()

    if not value:
        raise ValueError(
            f"{name} cannot be empty."
        )

    return value


def algorithms(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        value = (value,)

    try:
        value = tuple(value)
    except TypeError as exc:
        raise TypeError(
            "DJANGOSPICE_LOOKUP_JWT_ALGORITHMS "
            "must be an iterable of strings."
        ) from exc

    if not value:
        raise ValueError(
            "At least one JWT algorithm must be configured."
        )

    result: list[str] = []

    for algorithm in value:
        if not isinstance(algorithm, str):
            raise TypeError(
                "JWT algorithms must be strings."
            )

        algorithm = algorithm.strip()

        if not algorithm:
            raise ValueError(
                "JWT algorithms cannot contain empty values."
            )

        result.append(algorithm)

    return tuple(result)

