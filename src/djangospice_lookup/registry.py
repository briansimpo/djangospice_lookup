from __future__ import annotations

from threading import RLock

from .definition import LookupDefinition
from .exceptions import LookupConfigurationError
from .identifier import LookupIdentifier


class LookupRegistry:
    """
    Registry of explicitly exposed model lookups.
    """

    def __init__(self) -> None:
        self._definitions: dict[
            tuple[str, str],
            LookupDefinition,
        ] = {}
        self._lock = RLock()

    def register(self, definition: LookupDefinition) -> LookupDefinition:
        key = definition.key

        with self._lock:
            if key in self._definitions:
                existing = self._definitions[key]

                raise LookupConfigurationError(
                    f"Lookup '{definition.identifier}' is already "
                    f"registered for "
                    f"{existing.model._meta.label}."
                )

            self._definitions[key] = definition

        return definition

    def get(self, app_name: str, name: str) -> LookupDefinition:
        identifier = LookupIdentifier(
            app_name,
            name,
        )

        with self._lock:
            try:
                return self._definitions[identifier.key]
            except KeyError as exc:
                raise LookupConfigurationError(
                    f"Unknown lookup: {identifier}."
                ) from exc

    def has(self, app_name: str, name: str) -> bool:
        identifier = LookupIdentifier(
            app_name,
            name,
        )

        with self._lock:
            return identifier.key in self._definitions

    def unregister(self, app_name: str, name: str) -> None:
        identifier = LookupIdentifier(
            app_name,
            name,
        )

        with self._lock:
            self._definitions.pop(
                identifier.key,
                None,
            )

    def all(self) -> tuple[LookupDefinition, ...]:
        with self._lock:
            return tuple(self._definitions.values())

    def clear(self) -> None:
        with self._lock:
            self._definitions.clear()


lookup_registry = LookupRegistry()